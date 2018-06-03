/* Sensors */

sensors_event_t accel, mag, gyro, temp;
Adafruit_LSM9DS1 lsm = Adafruit_LSM9DS1(LSM9DS1_CSAG, LSM9DS1_CSM); // SPI

void setupSensor() {
  Serial.print("Setting up sensors...");

  pinMode(LSM9DS1_CSAG, OUTPUT);
  pinMode(LSM9DS1_CSM, OUTPUT);

  // TODO: if lsm is broken, always display the compass?
  if (!lsm.begin()) {
    Serial.print(F("Oops, no LSM9DS1 detected... Check your wiring!"));
    while (1)
      ;
  }

  // TODO: tune these

  // Set the accelerometer range
  lsm.setupAccel(lsm.LSM9DS1_ACCELRANGE_2G);
  // lsm.setupAccel(lsm.LSM9DS1_ACCELRANGE_4G);
  // lsm.setupAccel(lsm.LSM9DS1_ACCELRANGE_8G);
  // lsm.setupAccel(lsm.LSM9DS1_ACCELRANGE_16G);

  // Set the magnetometer sensitivity
  lsm.setupMag(lsm.LSM9DS1_MAGGAIN_4GAUSS);
  // lsm.setupMag(lsm.LSM9DS1_MAGGAIN_8GAUSS);
  // lsm.setupMag(lsm.LSM9DS1_MAGGAIN_12GAUSS);
  // lsm.setupMag(lsm.LSM9DS1_MAGGAIN_16GAUSS);

  // Setup the gyroscope
  lsm.setupGyro(lsm.LSM9DS1_GYROSCALE_245DPS);
  // lsm.setupGyro(lsm.LSM9DS1_GYROSCALE_500DPS);
  // lsm.setupGyro(lsm.LSM9DS1_GYROSCALE_2000DPS);

  Serial.println("done.");
}

void sensorReceive() {
  lsm.read();
  lsm.getEvent(&accel, &mag, &gyro, &temp);

  // TODO: this is giving a value between 12-13
  /*
  Serial.print("temp: ");
  Serial.print(temp.temperature);
  */

  /*
  // debugging sensors
  Serial.print("mag: ");
  Serial.print(mag.magnetic.x);
  Serial.print("x ");
  Serial.print(mag.magnetic.y);
  Serial.print("y ");
  Serial.print(mag.magnetic.z);
  Serial.print("z ");
  Serial.print("; gyro: ");
  Serial.print(gyro.gyro.x);
  Serial.print("x ");
  Serial.print(gyro.gyro.y);
  Serial.print("y ");
  Serial.print(gyro.gyro.z);
  Serial.println("z");
  */
}

bool sensorFaceDown() {
  // TODO: actually do something with the sensors
  return false;
}

bool sensorHanging() {
  // TODO: actually do something with the sensors
  return false;
}

bool sensorLevel() {
  // TODO: actually do something with the sensors
  return true;
}
