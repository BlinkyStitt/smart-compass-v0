// TODO: use addmod8

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
#define SDCARD_CS_PIN 10
#define LSM9DS1_CSAG 11
#define LSM9DS1_CSM 12
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
int broadcast_time_ms, default_brightness, flashlight_density, frames_per_second, max_peer_distance, ms_per_light_pattern,
  peer_led_ms, radio_power;

int time_zone_offset;

// offset between true and magnetic north
float magnetic_declination = 0.0;

// connect to the GPS
Adafruit_GPS GPS(&gpsSerial);

// save GPS data to SD card
String gps_log_filename = ""; // this is filled in during setupSD
File gps_log_file;

// keep us from transmitting to often
bool should_transmit[max_peers] = {true};

// TODO: this will probably change when I move from the breadboard to the PCB. give them better names (portrait, landscape?)
enum Orientation: byte {
  ORIENTED_UP, ORIENTED_DOWN, ORIENTED_USB_UP, ORIENTED_USB_DOWN, ORIENTED_SPI_UP, ORIENTED_SPI_DOWN
};

bool sensor_setup, sd_setup = false;

void setup() {
  Serial.begin(115200);

  // TODO: wait for serial while debugging?

  delay(1000);

  Serial.println("Setting up...");
  randomSeed(analogRead(6));

  // configuration depends on SD card so do it first
  setupSD();

  setupConfig();

  // do more setup now that we have our configuration
  setupGPS();
  setupRadio();
  setupSensor();
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

  gpsReceive();

  updateLights();

  // TODO: fastled EVERY_N_SECONDS helper doesn't work for us. maybe if we passed variables

  if (timeStatus() == timeNotSet) {
    // TODO: set time from peer?
    //radioReceive();
  } else {
    // if it's our time to transmit, radioTransmit(), else wait for radioReceive()
    // TODO: should there be downtime when no one is transmitting or receiving?

    time_segment_id = (nowMillis() / broadcast_time_ms) % time_segments;
    broadcasting_peer_id = time_segment_id / num_peers;
    broadcasted_peer_id = time_segment_id % num_peers;

    if (broadcasting_peer_id == my_peer_id) {
      if (should_transmit[broadcasted_peer_id]) {
        radioTransmit(broadcasted_peer_id);
        should_transmit[broadcasted_peer_id] = false;
      } else {
        // it's our time to transmit, but we already did
      }
    } else {
      // reset should_transmit to true
      for (int i = 0; i < num_peers; i++) {
        should_transmit[i] = true;
      }
      radioReceive();
    }
  }

  // delay to handle dithering
  // don't sleep too long or you get in the way of radios. keep this less < framerate
  FastLED.delay(10);
}
