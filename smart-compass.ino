// TODO: use addmod8

#include "debug.h"

// TODO: how is clang-format deciding to order these? they aren't alphabetical
#include <AP_Declination.h>
#include <Adafruit_GPS.h>
#include <Adafruit_LSM9DS1.h>
#include <Adafruit_Sensor.h>
#include <ArduinoSort.h>
#include <Bounce2.h>
#include <FastLED.h>
#include <IniFile.h>
#include <RH_RF95.h>
#include <SD.h>
#include <SPI.h>
#include <elapsedMillis.h>
#include <pb_decode.h>
#include <pb_encode.h>
// TODO: fork TimeLib to include ms
#include <TimeLib.h>
#include <Wire.h>

#include "smart-compass.pb.h"

// Pins 0 and 1 are used for Serial1 (GPS)
#define RFM95_INT 3 // already wired for us
#define RFM95_RST 4 // already wired for us
#define LED_DATA_PIN 5
#define RFM95_CS 8 // already wired for us
#define VBAT_PIN 9 // already wired for us  // A7
#define SDCARD_CS_PIN 10  // TODO: moved to a different pin for cleaner traces
#define LSM9DS1_CSAG 11  // TODO: moved to a different pin for cleaner traces
#define LSM9DS1_CSM 12  // TODO: moved to a different pin for cleaner traces
#define RED_LED_PIN 13  // already wired for us
#define SPI_MISO_PIN 22 // shared between Radio+Sensors+SD
#define SPI_MOSI_PIN 23 // shared between Radio+Sensors+SD
#define SPI_SCK_PIN 24  // shared between Radio+Sensors+SD
#define gpsSerial Serial1

#define LED_CHIPSET NEOPIXEL

/* these variables are used by multiple ino files and I'm not sure the right place to put them */
// TODO: maybe pass these around as arguments instead of having them be global?

// lights for compass ring
const int num_LEDs = 16;
CRGB leds[num_LEDs];

// rotating "base color" used by some patterns
uint8_t g_hue = 0;

// the more peers, the longer it takes for peer data to update
const int max_peers = 4;

// setup messages for all possible peers
SmartCompassMessage compass_messages[max_peers] = {SmartCompassMessage_init_default};

// these are set by config
int my_network_id, my_peer_id, my_hue, my_saturation, num_peers;

// these are set by config or fallback to defaults
// TODO: making this unsigned makes IniConfig sad. they shouldn't ever be negative though!
int broadcast_time_s, default_brightness, flashlight_density, frames_per_second, gps_update_s, max_peer_distance, ms_per_light_pattern,
  peer_led_ms, radio_power;

int time_zone_offset;

// offset between true and magnetic north
float magnetic_declination = 0.0;

// connect to the GPS
Adafruit_GPS GPS(&gpsSerial);

// save GPS data to SD card
//const char gps_log_filename = "gps.log"; // TODO: fill in during setupConfig
String gps_log_filename = ""; // TODO: everyone says not to use String, but it seems fine
File gps_log_file;

// keep us from transmitting too often
long last_transmitted[max_peers] = {0};

// TODO: this will probably change when I move from the breadboard to the PCB. give them better names (portrait, landscape?)
enum Orientation: byte {
  ORIENTED_UP, ORIENTED_DOWN, ORIENTED_USB_UP, ORIENTED_USB_DOWN, ORIENTED_PORTRAIT_UPSIDE_DOWN, ORIENTED_PORTRAIT
};

bool config_setup, sd_setup, sensor_setup = false;

elapsedMillis network_ms = 0;

void setupSPI() {
  // https://github.com/ImprobableStudios/Feather_TFT_LoRa_Sniffer/blob/9a8012ba316a652da669fe097c4b76c98bbaf35c/Feather_TFT_LoRa_Sniffer.ino#L222
  // The RFM95 has a pulldown on this pin, so the radio
  // is technically always selected unless you set the pin low.
  // this will cause other SPI devices to fail to function as
  // expected because CS (active-low) will be selected for
  // the RFM95 at the same time.
  digitalWrite(RFM95_CS, HIGH);

  digitalWrite(SDCARD_CS_PIN, HIGH);

  digitalWrite(LSM9DS1_CSM, HIGH);
  digitalWrite(LSM9DS1_CSAG, HIGH);

  // TODO: configure SPI pins?

  delay(100); // give everything time to wake up

  SPI.begin();
}

void setup() {
  #ifdef DEBUG
    Serial.begin(115200);

    delay(1000);
    while (!Serial) {
      ; // wait for serial port to connect. Needed for native USB
    }
  #endif

  Serial.println("Setting up...");

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

  // configure the timer to run at <sampleRate>Hertz
  tcConfigure(100);
  tcStartCounter();

  Serial.println("Starting...");
}

void loop() {
  // TODO: num_peers * num_peers can get pretty big!
  // each peer needs enough time to broadcast data for every other peer
  static unsigned int time_segments = num_peers * num_peers;
  static unsigned int time_segment_id, broadcasting_peer_id, broadcasted_peer_id;

  if (config_setup) {
    gpsReceive();

    updateLights();

    if (timeStatus() == timeNotSet) {
      radioReceive();
    } else {
      // if it's our time to transmit, radioTransmit(), else wait for radioReceive()
      // TODO: should there be downtime when no one is transmitting or receiving?

      // TODO: should we be including millis in this somehow? time segment length would be better then, but I'm not sure it matters
      // TODO: change this to broadcast_time_ms if we can figure out a reliable way to include millis
      time_segment_id = (now() / broadcast_time_s) % time_segments;
      broadcasting_peer_id = time_segment_id / num_peers;
      broadcasted_peer_id = time_segment_id % num_peers;

      if (broadcasting_peer_id == my_peer_id) {
        radioTransmit(broadcasted_peer_id);  // this will noop if we have transmitted recently
      } else {
        // TODO: have known down time so we can sleep longer?
        radioReceive();
      }
    }
  } else {
    updateLights();
  }

  // don't sleep too long or you get in the way of radios. keep this less < framerate
  //delayToDither(10);
  FastLED.delay(10);
}
