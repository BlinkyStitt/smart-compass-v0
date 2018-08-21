#define DEBUG
//#define DEBUG_SERIAL_WAIT
#include "bs_debug.h"
#define ARRAY_SIZE(array) ((sizeof(array)) / (sizeof(array[0])))

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

#define MAX_PINS 12

#define LED_FADE_RATE 77

// Pins 0 and 1 are used for Serial1 (GPS)
#define RFM95_INT 3 // already wired for us
#define RFM95_RST 4 // already wired for us
#define LED_DATA 5
#define FLOATING_PIN 6
#define RFM95_CS 8      // already wired for us
#define VBAT_PIN 9      // already wired for us  // A7
#define SDCARD_CS 10
#define LSM9DS1_CSAG 11
#define LSM9DS1_CSM 12
#define RED_LED 13      // already wired for us
#define SPI_MISO 22     // shared between Radio+Sensors+SD
#define SPI_MOSI 23     // shared between Radio+Sensors+SD
#define SPI_SCK 24      // shared between Radio+Sensors+SD

#define gpsSerial Serial1

#define LED_CHIPSET NEOPIXEL

// lights for compass ring
const int inner_ring_size = 16;
const int inner_ring_start = 0;
const int inner_ring_end = inner_ring_start + inner_ring_size;

const int outer_ring_size = 24;
const int outer_ring_start = inner_ring_end;
const int outer_ring_end = outer_ring_start + outer_ring_size;

const int status_bar_size = 8;
const int status_bar_start = outer_ring_end;
const int status_bar_end = status_bar_start + status_bar_size;

const int num_LEDs = status_bar_end;
CRGB leds[num_LEDs];

// rotating "base color" used by some patterns
uint8_t g_hue = 0;

// the more peers, the longer it takes for peer data to update
const int max_peers = 4;

// setup messages for all possible peers
// TODO: pointers here? i think this is geting corrupted
SmartCompassLocationMessage compass_messages[max_peers] = {SmartCompassLocationMessage_init_default};

#define NETWORK_KEY_SIZE 16

// these are set by config
int my_peer_id, my_hue, my_saturation, num_peers;
uint8_t my_network_key[NETWORK_KEY_SIZE];

// these are set by config or fallback to defaults
int broadcast_time_s, default_brightness, flashlight_density, frames_per_second, gps_update_s, loop_delay_ms,
    min_peer_distance, max_peer_distance, ms_per_light_pattern, peer_led_ms, radio_power;

int time_zone_offset;

// it is not legal to encrypt in the US, but we can sign and hash for security
#define NETWORK_HASH_SIZE 16
BLAKE2s blake2s;
uint8_t my_network_hash[NETWORK_HASH_SIZE];

// offset between true and magnetic north
float g_magnetic_declination = 0.0;

// connect to the GPS
Adafruit_GPS GPS(&gpsSerial);

// save GPS data to SD card
// TODO: don't use String. use char array instead
String gps_log_filename = "";
File g_file;

// keep us from transmitting too often
long last_transmitted[max_peers] = {0};

bool config_setup, sd_setup, sensor_setup = false;

// TODO: these are getting overridden! i don't think these are declared how i need. i should be using pointers
CompassPin compass_pins[MAX_PINS];

int distance_sorted_compass_pin_ids[MAX_PINS];
int next_compass_pin = 0;

SmartCompassPinMessage pin_message_rx = SmartCompassPinMessage_init_default;
SmartCompassPinMessage pin_message_tx = SmartCompassPinMessage_init_default;

const int max_compass_points = max_peers + 1;

// inner compass points go COUNTER-clockwise to match LEDs!
// TODO: this is wrong! this is not claiming the memory like i expected it to and setting this is breaking compass_pins
CHSV inner_compass_points[inner_ring_size][max_compass_points];
int next_inner_compass_point[inner_ring_size];

// TODO: initialize this?
CHSV outer_compass_points[outer_ring_size][max_compass_points];
int next_outer_compass_point[outer_ring_size];

// TODO: initialize this?
CHSV status_bar[status_bar_size];
int next_status_bar_id = 0;

elapsedMillis network_ms = 0;

CHSV pin_colors[] = {
    // {h, s, v},
    // white
    {HUE_BLUE, 255, 255},
    {HUE_RED, 255, 255},   // Red for disabling, not for actual red pins!
    {HUE_YELLOW, 255, 255},
    {HUE_BLUE, 255, 255},
    {HUE_PINK, 128, 255},
};
int last_pin_color_id = 0;
const int delete_pin_color_id = 1;

const int max_points_per_color = 3;

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
  debug_serial(115200, 5000);

  DEBUG_PRINTLN("Setting up...");

  for (int i = 0; i < MAX_PINS; i++) {
    compass_pins[i].database_id = -1;
  }

  for (int i = 0; i < inner_ring_size; i++) {
    next_inner_compass_point[i] = 0;

    for (int j = 0; j < max_compass_points; j++) {
      inner_compass_points[i][j].hue = 128;
      inner_compass_points[i][j].saturation = 128;
      inner_compass_points[i][j].value = 128;
    }
  }

  for (int i = 0; i < outer_ring_size; i++) {
    next_outer_compass_point[i] = 0;

    for (int j = 0; j < max_compass_points; j++) {
      outer_compass_points[i][j].hue = 128;
      outer_compass_points[i][j].saturation = 128;
      outer_compass_points[i][j].value = 128;
    }
  }

  // TODO: something else is

  /*
  for (int i = 0; i < MAX_PINS; i++) {
    DEBUG_PRINTLN(compass_pins[i].database_id);
  }

  for (int i = 0; i < inner_ring_size; i++) {
    for (int j = 0; j < max_compass_points; j++) {
      DEBUG_PRINTLN(inner_compass_points[i][j].hue);
    }
  }

  for (int i = 0; i < outer_ring_size; i++) {
    for (int j = 0; j < max_compass_points; j++) {
      DEBUG_PRINTLN(outer_compass_points[i][j].hue);
    }
  }
  */

  // Configure SPI pins for everything BEFORE trying to do anything with them individually
  setupSPI();

  checkBattery();

  randomSeed(analogRead(FLOATING_PIN));

  // configuration depends on SD card so do it first
  setupSD();

  setupConfig();

  setupLights();

  // do more setup now that we have our configuration
  if (config_setup) {
    setupGPS();
    setupRadio();
  }

  setupSensor();

  // open the SD card
  g_file = SD.open(gps_log_filename, FILE_WRITE);

  // if the file opened okay, write to it:
  if (!g_file) {
    // if the file didn't open, print an error and abort
    DEBUG_PRINT(F("error opening gps log: "));
    DEBUG_PRINTLN(gps_log_filename);
  } else {
    DEBUG_PRINT(F("Logging start to "));
    DEBUG_PRINTLN(gps_log_filename);

    // add a blank line each time we start
    g_file.println("");

    // close the file:
    g_file.close();
  }

  // TODO: load saved locations

  // configure the timer that reads GPS data to run at <sampleRate>Hertz
  tcConfigure(10);
  tcStartCounter();

  if (sd_setup) {
    loadCompassPins();
  }

  DEBUG_PRINTLN(F("Starting..."));
}

/*
 * this stuff was in its own .ino files, but something was broken about it
 * i think i fixed it by moving the struct definitions to types.h, but I'm not sure how best to move g_file and db defs
 */

#define TABLE_SIZE 4096 * 2

// The max number of records that should be created = (TABLE_SIZE - sizeof(EDB_Header)) / sizeof(LogEvent).
// If you try to insert more, operations will return EDB_OUT_OF_RANGE for all records outside the usable range.

const char *db_name = "compass.db";

// The read and write handlers for using the SD Library
// Also blinks the led while writing/reading
// database entries start at 1!
inline void writer(unsigned long address, const byte *data, unsigned int recsize) {
  digitalWrite(RED_LED, HIGH);
  g_file.seek(address);
  g_file.write(data, recsize);
  g_file.flush();
  digitalWrite(RED_LED, LOW);
}

inline void reader(unsigned long address, byte *data, unsigned int recsize) {
  digitalWrite(RED_LED, HIGH);
  g_file.seek(address);
  g_file.read(data, recsize);
  digitalWrite(RED_LED, LOW);
}

// Create an EDB object with the appropriate write and read handlers
// NOTE! These handlers do NOT open or close the database file!
EDB db(&writer, &reader);

/*
 * END things that should be moved into their own ino files
 */

void loop() {
  // each peer needs enough time to broadcast data for every other peer. then we double it so we can spend half the time sleeping
  static const unsigned int time_segments = num_peers * num_peers * 2;
  static unsigned int time_segment_id, broadcasting_peer_id, broadcasted_peer_id;

  if (config_setup) {
    gpsReceive();

    updateLights();

    if (GPS.fix) {
      time_segment_id = (getGPSTime() / broadcast_time_s) % time_segments;

      broadcasting_peer_id = time_segment_id / (num_peers * 2);
      broadcasted_peer_id = time_segment_id % num_peers;

      if (broadcasting_peer_id == my_peer_id) {
        radioTransmit(broadcasted_peer_id); // this will sleep the radio if we've already transmitted for this segment
      } else if (broadcasting_peer_id >= num_peers) {
        // spend 1/2 the time with the radio sleeping
        radioSleep();
      } else {
        radioReceive();
      }
    } else {
      // even if we don't have a GPS fix, we can still update peer locations
      // this will take more power since the GPS will be searching for a fix and the radio will be on
      radioReceive();
    }

    // transmitting can be slow. update lights again just in case
    updateLights();
  } else {
    // without config, we can't do anything with radios or saved GPS locations. just do the lights
    updateLights();
  }

  // don't sleep too long or you get in the way of radios. keep this less < framerate
  FastLED.delay(loop_delay_ms);
}
