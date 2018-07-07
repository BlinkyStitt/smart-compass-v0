// TODO: use addmod8

#define DEBUG
#include "bs_debug.h"
#define ARRAY_SIZE(array) ((sizeof(array)) / (sizeof(array[0])))

// TODO: how is clang-format deciding to order these? they aren't alphabetical
#include <AP_Declination.h>
#include <Adafruit_GPS.h>
#include <Adafruit_LSM9DS1.h>
#include <Adafruit_Sensor.h>
#include <EDB.h>
#include <FastLED.h>
#include <IniFile.h>
#include <RH_RF95.h>
#include <SD.h>
#include <SPI.h>
#include <Wire.h>
#include <elapsedMillis.h>
#include <pb_decode.h>
#include <pb_encode.h>

// it isn't legal for us to encrypt on amateur radio, but we need some sort of security so we sign our messages
#include <BLAKE2s.h>

#include "smart-compass.pb.h"
#include "types.h"

#define MAX_PINS 255

// TODO: put on SD?
#define LED_FADE_RATE 90

// Pins 0 and 1 are used for Serial1 (GPS)
#define RFM95_INT 3 // already wired for us
#define RFM95_RST 4 // already wired for us
#define LED_DATA 5
#define RFM95_CS 8      // already wired for us
#define VBAT_PIN 9      // already wired for us  // A7
#define SDCARD_CS 10    // TODO: moved to a different pin for cleaner traces
#define LSM9DS1_CSAG 11 // TODO: moved to a different pin for cleaner traces
#define LSM9DS1_CSM 12  // TODO: moved to a different pin for cleaner traces
#define RED_LED 13      // already wired for us
#define SPI_MISO 22     // shared between Radio+Sensors+SD
#define SPI_MOSI 23     // shared between Radio+Sensors+SD
#define SPI_SCK 24      // shared between Radio+Sensors+SD
#define gpsSerial Serial1

#define LED_CHIPSET NEOPIXEL

/* these variables are used by multiple ino files and I'm not sure the right place to put them */
// TODO: maybe pass these around as arguments instead of having them be global? at least rename them all to be prefixed
// with g_

// lights for compass ring
const int inner_ring_size = 16;
const int inner_ring_start = 0;
const int inner_ring_end = inner_ring_start + inner_ring_size; // TODO: use this instead of numLeds a lot of places

const int outer_ring_size = 24;
const int outer_ring_start = inner_ring_end;
const int outer_ring_end = outer_ring_start + outer_ring_size;

// TODO: add status bar lights
const int status_bar_size = 8;
const int status_bar_start = outer_ring_end;
const int status_bar_end = status_bar_start + status_bar_size;

// TODO: also add a 8 led strip for showing nearby peers

// TODO: split this into 3 different sized arrays and use a union?
const int num_LEDs = status_bar_end;
CRGB leds[num_LEDs];

// rotating "base color" used by some patterns
uint8_t g_hue = 0;

// the more peers, the longer it takes for peer data to update
const int max_peers = 4;

// setup messages for all possible peers
SmartCompassLocationMessage compass_messages[max_peers] = {SmartCompassLocationMessage_init_default};

#define NETWORK_KEY_SIZE 16

// these are set by config
int my_peer_id, my_hue, my_saturation, num_peers;
uint8_t my_network_key[NETWORK_KEY_SIZE];

// these are set by config or fallback to defaults
// TODO: making this unsigned makes IniConfig sad. they shouldn't ever be negative though!
int broadcast_time_s, default_brightness, flashlight_density, frames_per_second, gps_update_s, loop_delay_ms,
    min_peer_distance, max_peer_distance, ms_per_light_pattern, peer_led_ms, radio_power;

int time_zone_offset;

// it is not legal to encrypt in the US, but we can sign and hash for security
// TODO: make sure to update the protobuf, too!
#define NETWORK_HASH_SIZE 16
BLAKE2s blake2s;
uint8_t my_network_hash[NETWORK_HASH_SIZE]; // TODO: union type to access as hex?

// offset between true and magnetic north
float g_magnetic_declination = 0.0;

// connect to the GPS
Adafruit_GPS GPS(&gpsSerial);

// save GPS data to SD card
String gps_log_filename = ""; // TODO: everyone says not to use String, but it seems fine and is way simpler
File my_file;

// keep us from transmitting too often
// TODO: i think our loop check has a bug. this used to just be a boolean, but that had a bug. it should have worked tho
long last_transmitted[max_peers] = {0};

bool config_setup, sd_setup, sensor_setup = false;

// todo: make compasslocationmessages work like this
CompassPin compass_pins[MAX_PINS] = {0, false, 0, 0, 0, 0, 0, {0, 0, 0}};

int distance_sorted_compass_pin_ids[MAX_PINS];
int next_compass_pin = 0;

SmartCompassPinMessage pin_message_rx = SmartCompassPinMessage_init_default;
SmartCompassPinMessage pin_message_tx = SmartCompassPinMessage_init_default;

const int max_compass_points = max_peers + 1; // TODO: is this enough? what about when we include saved locations?

// compass points go COUNTER-clockwise to match LEDs!
CHSV inner_compass_points[inner_ring_size][max_compass_points];
int next_inner_compass_point[inner_ring_size] = {0};

CHSV outer_compass_points[outer_ring_size][max_compass_points];
int next_outer_compass_point[outer_ring_size] = {0};

elapsedMillis network_ms = 0;

CHSV pin_colors[] = {
    // {h, s, v},
    // TODO: color-blind friendly colors from test-lights.ino. i can't tell what any of these are. red, yellow, blue,
    // white
    {160, 71, 255},  // CRGB::RoyalBlue
    {0, 255, 255},   // Red for disabling, not for actual red pins!
    {213, 255, 255}, // CRGB::Purple
    {234, 59, 255},  // CRGB::HotPink;
    {23, 255, 255},  // CRGB::DarkOrange;
    {52, 219, 255},  // CRGB::Gold;
    {104, 171, 255}, // CRGB::SeaGreen; // TODO: this one doesn't look great at full value
    {128, 255, 255}  // CRGB::Aqua;
};
int last_pin_color_id = 0;
const int delete_pin_color_id = 1;

const int max_points_per_color = 3; // TODO: put this on the SD?

void setupSPI() {
  // https://github.com/ImprobableStudios/Feather_TFT_LoRa_Sniffer/blob/9a8012ba316a652da669fe097c4b76c98bbaf35c/Feather_TFT_LoRa_Sniffer.ino#L222
  // The RFM95 has a pulldown on this pin, so the radio
  // is technically always selected unless you set the pin low.
  // this will cause other SPI devices to fail to function as
  // expected because CS (active-low) will be selected for
  // the RFM95 at the same time.
  digitalWrite(RFM95_CS, HIGH);

  digitalWrite(SDCARD_CS, HIGH);

  digitalWrite(LSM9DS1_CSM, HIGH);
  digitalWrite(LSM9DS1_CSAG, HIGH);

  // give everything time to wake up
  delay(200);

  SPI.begin();
}

void setup() {
#ifdef DEBUG
  Serial.begin(115200);

  delay(5000);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB
  }
#else
  delay(5000); // todo: tune this. don't get locked out if something crashes
#endif

  DEBUG_PRINTLN("Setting up...");

  // TODO: disable ADC?

  // Configure SPI pins for everything BEFORE trying to do anything with them individually
  setupSPI();

  randomSeed(analogRead(6));

  // configuration depends on SD card so do it first
  setupSD();

  setupConfig();

  // do more setup now that we have our configuration
  if (config_setup) {
    setupGPS();
    setupRadio();
    setupSensor();
  }

  setupLights();

  // open the SD card
  my_file = SD.open(gps_log_filename, FILE_WRITE);

  // if the file opened okay, write to it:
  if (!my_file) {
    // if the file didn't open, print an error and abort
    DEBUG_PRINT(F("error opening gps log: "));
    DEBUG_PRINTLN(gps_log_filename);
  } else {
    DEBUG_PRINT(F("Logging start to "));
    DEBUG_PRINTLN(gps_log_filename);

    // add a blank line each time we start
    my_file.println("");

    // TODO: do we want to log anything else?

    // close the file:
    my_file.close();
  }

  // configure the timer that reads GPS data to run at <sampleRate>Hertz
  // TODO: what rate should we read at? the flora example does 1Hz!
  tcConfigure(10);
  tcStartCounter();

  checkBattery();

  DEBUG_PRINTLN(F("Starting..."));
}

/*
 * this stuff was in its own .ino files, but something was broken about it
 * i think i fixed it by moving the struct definitions to types.h, but I'm not sure how best to move db_file and db defs
 */

// TODO: what table size?
#define TABLE_SIZE 4096 * 2

// The max number of records that should be created = (TABLE_SIZE - sizeof(EDB_Header)) / sizeof(LogEvent).
// If you try to insert more, operations will return EDB_OUT_OF_RANGE for all records outside the usable range.

const char *db_name = "compass.db";
File db_file;

// The read and write handlers for using the SD Library
// Also blinks the led while writing/reading
// database entries start at 1!
inline void writer(unsigned long address, const byte *data, unsigned int recsize) {
  digitalWrite(RED_LED, HIGH);
  db_file.seek(address);
  db_file.write(data, recsize);
  db_file.flush();
  digitalWrite(RED_LED, LOW);
}

inline void reader(unsigned long address, byte *data, unsigned int recsize) {
  digitalWrite(RED_LED, HIGH);
  db_file.seek(address);
  db_file.read(data, recsize);
  digitalWrite(RED_LED, LOW);
}

// Create an EDB object with the appropriate write and read handlers
// NOTE! These handlers do NOT open or close the database file!
EDB db(&writer, &reader);

/*
 * END things that should be moved into their own ino files
 */

void loop() {
  // TODO: num_peers * num_peers can get pretty big!
  // each peer needs enough time to broadcast data for every other peer
  static unsigned int time_segments = num_peers * num_peers;
  static unsigned int time_segment_id, broadcasting_peer_id, broadcasted_peer_id;

  if (config_setup) {
    gpsReceive();

    updateLights();

    if (GPS.fix) {
      // if it's our time to transmit, radioTransmit(), else wait for radioReceive()
      // TODO: should there be downtime when no one is transmitting or receiving?

      // TODO: i don't think this is working right.
      // TODO: should we be including millis in this somehow? time segment length would be better then, but I'm not sure
      // it matters
      // TODO: change this to broadcast_time_ms if we can figure out a reliable way to include millis
      // TODO: only calculate this every 100ms or something like that?
      time_segment_id = (getGPSTime() / broadcast_time_s) % time_segments;

      broadcasting_peer_id = time_segment_id / num_peers;
      broadcasted_peer_id = time_segment_id % num_peers;

      /*
      // this is going to be too verbose
      DEBUG_PRINT(broadcasting_peer_id);
      DEBUG_PRINT(" -> ");
      DEBUG_PRINTLN(broadcasted_peer_id);
      */

      if (broadcasting_peer_id == my_peer_id) {
        radioTransmit(broadcasted_peer_id); // this will noop if we have transmitted recently
      } else {
        // TODO: have known down time so we can sleep longer?
        radioReceive();
      }
    } else {
      // we don't know what time it is. listen and we might hear the time from a peer
      radioReceive();
    }

    // TODO: this seems excessive, but maybe it will keep framerate smoother
    updateLights();
  } else {
    // without config, we can't do anything with radios or saved GPS locations. just do the lights
    updateLights();
  }

  // don't sleep too long or you get in the way of radios. keep this less < framerate
  FastLED.delay(loop_delay_ms);
}
