#include <RTCZero.h>

// Pins 0 and 1 are used for Serial1 (GPS)
#define RFM95_INT 3 // already wired for us
#define RFM95_RST 4 // already wired for us
#define LED_DATA 5
#define RFM95_CS 8 // already wired for us
#define VBAT_PIN 9 // already wired for us  // A7
#define SDCARD_CS 10
#define LSM9DS1_CSAG 11
#define LSM9DS1_CSM 12
#define RED_LED 13  // already wired for us
#define SPI_MISO 22 // shared between Radio+Sensors+SD
#define SPI_MOSI 23 // shared between Radio+Sensors+SD
#define SPI_SCK 24  // shared between Radio+Sensors+SD

// the gps has it's own rtc. just use GPS.seconds
RTCZero rtc;

/* Setup */

void setupRTC() {
  rtc.begin(); // initialize RTC

  rtc.setEpoch(1451606400); // Jan 1, 2016
}

void setup() {
  // TODO: cut this into multiple functions
  Serial.begin(19200);
  while (!Serial) {  // TODO: remove this when done debugging otherwise it won't start without the usb plugged in
    delay(1);
  }

  Serial.println("Setting up...");

  // disable the radio
  pinMode(RFM95_CS, INPUT_PULLUP);

  setupRTC();

  Serial.println("Starting...");
}

/* Loop */

void loop() {
  Serial.print("Unix

  time = ");
  Serial.println(rtc.getY2kEpoch());

  Serial.print("Seconds since Jan 1 2000 = ");
  Serial.println(rtc.getY2kEpoch());

  // Print date...
  Serial.print(rtc.getDay());
  Serial.print("/");
  Serial.print(rtc.getMonth());
  Serial.print("/");
  Serial.print(rtc.getYear());
  Serial.print("\t");

  // ...and time
  print2digits(rtc.getHours());
  Serial.print(":");
  print2digits(rtc.getMinutes());
  Serial.print(":");
  print2digits(rtc.getSeconds());

  Serial.println();

  delay(1000);
}

void print2digits(int number) {
  if (number < 10) {
    Serial.print("0");
  }
  Serial.print(number);
}
