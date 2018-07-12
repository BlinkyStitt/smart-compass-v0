// Based on https://www.arduino.cc/en/Tutorial/Genuino101CurieIMUGyro

#include <Adafruit_LSM9DS1.h>
#include <Adafruit_Sensor.h>

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

/* Sensors */

sensors_event_t accel, mag, gyro, temp;

Adafruit_LSM9DS1 lsm = Adafruit_LSM9DS1(LSM9DS1_CSAG, LSM9DS1_CSM);

void setupSensor() {
  pinMode(LSM9DS1_CSM, OUTPUT);
  pinMode(LSM9DS1_CSAG, OUTPUT);

  if(!lsm.begin()) {
    Serial.print(F("Ooops, no LSM9DS1 detected ... Check your wiring!"));
    while(1);
  }

  // TODO: tune these

  // Set the accelerometer range
  lsm.setupAccel(lsm.LSM9DS1_ACCELRANGE_2G);
  //lsm.setupAccel(lsm.LSM9DS1_ACCELRANGE_4G);
  //lsm.setupAccel(lsm.LSM9DS1_ACCELRANGE_8G);
  //lsm.setupAccel(lsm.LSM9DS1_ACCELRANGE_16G);

  // Set the magnetometer sensitivity
  lsm.setupMag(lsm.LSM9DS1_MAGGAIN_4GAUSS);
  //lsm.setupMag(lsm.LSM9DS1_MAGGAIN_8GAUSS);
  //lsm.setupMag(lsm.LSM9DS1_MAGGAIN_12GAUSS);
  //lsm.setupMag(lsm.LSM9DS1_MAGGAIN_16GAUSS);

  // Setup the gyroscope
  lsm.setupGyro(lsm.LSM9DS1_GYROSCALE_245DPS);
  //lsm.setupGyro(lsm.LSM9DS1_GYROSCALE_500DPS);
  //lsm.setupGyro(lsm.LSM9DS1_GYROSCALE_2000DPS);
}

void sensorReceive() {
  lsm.read();
  lsm.getEvent(&accel, &mag, &gyro, &temp);
}

/* Setup */

void setup() {
  // TODO: cut this into multiple functions
  Serial.begin(19200);
  while (!Serial) {  // TODO: remove this when done debugging otherwise it won't start without the usb plugged in
    delay(1);
  }

  Serial.println("Setting up...");

  // disable the radio
  pinMode(RFM95_CS, INPUT_PULLUP);

  setupSensor();

  Serial.println("Starting...");
}

/* Loop */

String lastOrientation, currentOrientation;

void loop() {
  sensorReceive();

  // read accelerometer:
  int x = accel.acceleration.x;
  int y = accel.acceleration.y;
  int z = accel.acceleration.z;

  // calculate the absolute values, to determine the largest
  int absX = abs(x);
  int absY = abs(y);
  int absZ = abs(z);

  if ( (absZ > absX) && (absZ > absY)) {
    // base orientation on Z
    if (z > 0) {
      currentOrientation = "up";
    } else {
      currentOrientation = "down";
    }
  } else if ( (absY > absX) && (absY > absZ)) {
    // base orientation on Y
    if (y > 0) {
      currentOrientation = "usb down";
    } else {
      currentOrientation = "usb up";
    }
  } else {
    // base orientation on X
    if (x < 0) {
      currentOrientation = "upside-down portrait";
    } else {
      currentOrientation = "portrait";
    }
  }

  // if the orientation has changed, print out a description:
  // TODO: make sure the orientation stays here for a moment?
  if (currentOrientation != lastOrientation) {
    Serial.println(currentOrientation);
    lastOrientation = currentOrientation;
  }

  delay(50);
}
