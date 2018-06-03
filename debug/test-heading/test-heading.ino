#include <Adafruit_LSM9DS1.h>
#include <Adafruit_Sensor.h>
#include <MadgwickAHRS.h>
#include <MahonyAHRS.h>

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

// Offsets in uTesla applied to raw x/y/z values
float mag_offsets[3] = { 25.36F, 18.13F, 3.23F };

// Soft iron error compensation matrix
float mag_softiron_matrix[3][3] = { { 0.998, 0.034, -0.006 },
                                    { 0.034, 0.980, 0.004 },
                                    { -0.006, 0.004, 1.024 } };

float mag_field_strength = 42.73F;

/* Sensors */

sensors_event_t accel, mag, gyro, temp;

Adafruit_LSM9DS1 lsm = Adafruit_LSM9DS1(LSM9DS1_CSAG, LSM9DS1_CSM);

//Mahony orientation_filter;
Madgwick orientation_filter;  // more accurate, but more resources (and so more power)

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

  orientation_filter.begin(100);
}

void sensorReceive() {
  lsm.read();
  lsm.getEvent(&accel, &mag, &gyro, &temp);

  // Apply mag offset compensation (base values in gauss. offsets in uTesla)
  float x = mag.magnetic.x - mag_offsets[0] / 100;
  float y = mag.magnetic.y - mag_offsets[1] / 100;
  float z = mag.magnetic.z - mag_offsets[2] / 100;

  // Apply mag soft iron error compensation
  float mx = x * mag_softiron_matrix[0][0] + y * mag_softiron_matrix[0][1] + z * mag_softiron_matrix[0][2];
  float my = x * mag_softiron_matrix[1][0] + y * mag_softiron_matrix[1][1] + z * mag_softiron_matrix[1][2];
  float mz = x * mag_softiron_matrix[2][0] + y * mag_softiron_matrix[2][1] + z * mag_softiron_matrix[2][2];

  // TODO: make sure gyro.gyro.* is in degrees/s and not radians/s
  orientation_filter.update(gyro.gyro.x, gyro.gyro.y, gyro.gyro.z,
                            accel.acceleration.x, accel.acceleration.y, accel.acceleration.z,
                            mx, my, mz);

  /*
  // print the heading, pitch and roll
  float roll = orientation_filter.getRoll();
  float pitch = orientation_filter.getPitch();
  float heading = orientation_filter.getYaw();
  Serial.print("Orientation: ");
  Serial.print(heading);
  Serial.print(" ");
  Serial.print(pitch);
  Serial.print(" ");
  Serial.println(roll);
  */

  // TODO: this is giving a value between 12-13. supposedly this is for the chip to use and not really an environ sensor
  /*
  Serial.print("temp: ");
  Serial.print(temp.temperature);
  */

  /*
  // debugging sensors
  Serial.print("accel (m/s^2): ");
  Serial.print(accel.acceleration.x);
  Serial.print("x ");
  Serial.print(accel.acceleration.y);
  Serial.print("y ");
  Serial.print(accel.acceleration.z);
  Serial.print("z ");
  Serial.print("; mag (gauss): ");
  Serial.print(mx);
  Serial.print("x ");
  Serial.print(my);
  Serial.print("y ");
  Serial.print(mz);
  Serial.print("z ");
  Serial.print("; gyro (dps): ");
  Serial.print(gx);
  Serial.print("x ");
  Serial.print(gy);
  Serial.print("y ");
  Serial.print(gz);
  Serial.println("z");
  */
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

  // print the heading, pitch and roll
  float roll = orientation_filter.getRoll();
  float pitch = orientation_filter.getPitch();
  float heading = orientation_filter.getYaw();
  Serial.print("Orientation: ");
  Serial.print(heading);
  Serial.print(" ");
  Serial.print(pitch);
  Serial.print(" ");
  Serial.println(roll);

  delay(10);
}
