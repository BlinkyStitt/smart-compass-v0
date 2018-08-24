/* Sensors */

sensors_event_t accel, mag, gyro, temp;
Adafruit_LSM9DS1 lsm = Adafruit_LSM9DS1(LSM9DS1_CSAG, LSM9DS1_CSM); // SPI

/*
// TODO: load these from the SD card
// Offsets in uTesla applied to raw x/y/z values
float mag_offsets[3] = { 25.36F, 18.13F, 3.23F };

// Soft iron error compensation matrix
float mag_softiron_matrix[3][3] = { { 0.998, 0.034, -0.006 },
                                    { 0.034, 0.980, 0.004 },
                                    { -0.006, 0.004, 1.024 } };

float mag_field_strength = 42.73F;
*/

void setupSensor() {
  DEBUG_PRINT(F("Setting up sensors..."));

  if (!lsm.begin()) {
    DEBUG_PRINTLN(F("Oops, no LSM9DS1 detected... Check your wiring!"));
    return;
  }

  // TODO: allow setting these on the SD card?

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

  // TODO: is this enough? if we need it faster than this, move sensorReceive to timer.ino
  //  orientation_filter.begin(100);

  sensor_setup = true;

  DEBUG_PRINTLN("done.");
}

void sensorReceive() {
  static unsigned long next_update = 0;

  // TODO: this should be a global since we are using multiple places now
  static int goal_fps = 1000.0 / frames_per_second;

  // limit our refresh rate
  if (millis() < next_update) {
    return;
  }

  // TODO: this might be our culprit for the last of the crashes! if we wake up the sensor and it draws power while the
  // TODO: lights are bright and the radio is drawing full power?
  if (rf95.mode() == RH_RF95_MODE_TX) {
    return;
  }

  // TODO: is this the right mode? its the only one that had rx in it
  if (rf95.mode() == RH_RF95_MODE_RXCONTINUOUS) {
    return;
  }

  // 20ms * 2 delay time. more delay = less battery drain
  next_update = millis() + goal_fps * 2;

  lsm.read();
  lsm.getEvent(&accel, &mag, &gyro, &temp);
}

void getOrientation(Orientation *o) {
  // DEBUG_PRINT(F("Orientation: "));

  if (!sensor_setup) {
    DEBUG_PRINTLN(F("UP (no sensor)"));
    *o = ORIENTED_UP;
    return;
  }

  sensorReceive();

  // read accelerometer:
  int x = accel.acceleration.x;
  int y = accel.acceleration.y;
  int z = accel.acceleration.z;

  // calculate the absolute values, to determine the largest
  int absX = abs(x);
  int absY = abs(y);
  int absZ = abs(z);

  // the lights are now on the back of the device! what was up is now down

  if ((absZ > absX) && (absZ > absY)) {
    // base orientation on Z
    if (z > 0) {
      //    DEBUG_PRINTLN(F("DOWN"));
      *o = ORIENTED_DOWN;
      return;
    }
    //      DEBUG_PRINTLN(F("UP"));
    *o = ORIENTED_UP;
    return;
  }

  if ((absY > absX) && (absY > absZ)) {
    // base orientation on Y
    if (y > 0) {
      //      DEBUG_PRINTLN(F("USB_DOWN"));
      *o = ORIENTED_USB_DOWN;
      return;
    }
    //    DEBUG_PRINTLN(F("USB_UP"));
    *o = ORIENTED_USB_UP;
    return;
  }

  // base orientation on X
  if (x < 0) {
    //    DEBUG_PRINTLN(F("UPSIDE_DOWN"));
    *o = ORIENTED_PORTRAIT_UPSIDE_DOWN;
    return;
  }

  //  DEBUG_PRINTLN(F("PORTRAIT"));
  *o = ORIENTED_PORTRAIT;
  return;
}
