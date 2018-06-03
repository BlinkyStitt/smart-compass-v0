#include <Adafruit_LSM9DS1.h>
#include <Adafruit_Sensor.h>

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

  setupSensor();
}

/* Loop */

void loop() {
  sensorReceive();

  // Print the sensor data
  // thanks to https://github.com/PaulStoffregen/MotionCal/issues/8
  // TODO: how are these scaled? 100, 900, 16?
  Serial.print("Raw:");
  Serial.print((int)round(accel.acceleration.x * 1000));
  Serial.print(',');
  Serial.print((int)round(accel.acceleration.y * 1000));
  Serial.print(',');
  Serial.print((int)round(accel.acceleration.z * 1000));
  Serial.print(',');
  Serial.print((int)round(gyro.gyro.x * 1000));
  Serial.print(',');
  Serial.print((int)round(gyro.gyro.y * 1000));
  Serial.print(',');
  Serial.print((int)round(gyro.gyro.z * 1000));
  Serial.print(',');
  Serial.print((int)round(mag.magnetic.x * 1000));
  Serial.print(',');
  Serial.print((int)round(mag.magnetic.y * 1000));
  Serial.print(',');
  Serial.print((int)round(mag.magnetic.z * 1000));
  Serial.println();

  delay(50);
}
