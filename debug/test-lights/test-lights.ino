// make sure the lights are wired correctly

#define DEBUG
#include "bs_debug.h"
#define ARRAY_SIZE(array) ((sizeof(array))/(sizeof(array[0])))

#include <FastLED.h>
#include <IniFile.h>
#include <RH_RF95.h>
#include <SPI.h>

#ifdef DEBUG
// debug-only includes
#include <RunningAverage.h>

#endif

#define MAX_PINS 255

// Pins 0 and 1 are used for Serial1 (GPS)
#define RFM95_INT 3 // already wired for us
#define RFM95_RST 4 // already wired for us
#define LED_DATA 5
#define RFM95_CS 8       // already wired for us
#define VBAT_PIN 9       // already wired for us  // A7
#define SDCARD_CS 10 // TODO: moved to a different pin for cleaner traces
#define LSM9DS1_CSAG 11  // TODO: moved to a different pin for cleaner traces
#define LSM9DS1_CSM 12   // TODO: moved to a different pin for cleaner traces
#define RED_LED 13   // already wired for us
#define SPI_MISO 22  // shared between Radio+Sensors+SD
#define SPI_MOSI 23  // shared between Radio+Sensors+SD
#define SPI_SCK 24   // shared between Radio+Sensors+SD
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

const int status_bar_size = 8;
const int status_bar_start = outer_ring_end;
const int status_bar_end = status_bar_start + status_bar_size;

// TODO: split this into 3 different sized arrays and use a union?
const int num_LEDs = status_bar_end;
CRGB leds[num_LEDs];

const int default_brightness = 128; // TODO: what should we test with?

CHSV colors[] = {
  // TODO: find more color-blind friendly colors
  // {h, s, v},

  {0, 255, 255},  // CRGB::Red for North

  // saved pin colors
  {23, 255, 255},  // CRGB::DarkOrange;
  {52, 219, 255},  // CRGB::Gold;
  // TODO: need a green
  //{104, 171, 255},  // CRGB::SeaGreen; // TODO: this one doesn't look great at full value at full value
  //{128, 255, 255},  // CRGB::Aqua;  // TODO: this doesn't look good to bryan
  {160, 71, 255},  // CRGB::RoyalBlue
  {213, 255, 255},  // CRGB::Purple
  //{234, 59, 255},  // CRGB::HotPink;    // TODO: this doesn't look good to bryan

  {0, 0, 0}  // CRGB::Black;
};

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

void setupLights() {
  DEBUG_PRINT("Setting up lights... ");

  pinMode(LED_DATA, OUTPUT);
  pinMode(RED_LED, OUTPUT);

  // TODO: seed fastled random?

  // https://learn.adafruit.com/adafruit-feather-m0-basic-proto/power-management
  // "While you can get 500mA from it, you can't do it continuously from 5V as it will overheat the regulator."
  FastLED.setMaxPowerInVoltsAndMilliamps(3.3, 500);

  FastLED.addLeds<LED_CHIPSET, LED_DATA>(leds, num_LEDs).setCorrection(TypicalSMD5050);
  FastLED.setBrightness(default_brightness); // TODO: read this from the SD card
  FastLED.clear();
  FastLED.show();

  DEBUG_PRINTLN("done.");
}

void setup() {
  Serial.begin(115200);

  delay(1000);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB
  }

  DEBUG_PRINTLN("Setting up...");

  // Configure SPI pins for everything BEFORE trying to do anything with them individually
  setupSPI();

  setupLights();

  DEBUG_PRINTLN(F("Starting with color #0..."));
}

void loop() {
  static int color_id = 0;

  // TODO: do something neat that will make it obvious that the lights are wired properly
  // TODO: (one red, two green, three blue repeating clockwise?)
  // TODO: test different battery levels and dimming distant peers
  fill_solid(leds, num_LEDs, colors[color_id]);

  // don't sleep too long or you get in the way of radios. keep this less < framerate
  // delayToDither(10);
  FastLED.delay(10);

  EVERY_N_SECONDS(2) {
    color_id++;
    if (color_id >= ARRAY_SIZE(colors)) {
      color_id = 0;
    }
    DEBUG_PRINT(F("Color #"));
    DEBUG_PRINTLN(color_id);
  }
}
