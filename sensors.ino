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
  lsm.read();
  lsm.getEvent(&accel, &mag, &gyro, &temp);

  /*
  // Apply mag offset compensation (base values in gauss. offsets in uTesla)
  float x = mag.magnetic.x - mag_offsets[0] / 100;
  float y = mag.magnetic.y - mag_offsets[1] / 100;
  float z = mag.magnetic.z - mag_offsets[2] / 100;

  // Apply mag soft iron error compensation
  float mx = x * mag_softiron_matrix[0][0] + y * mag_softiron_matrix[0][1] + z * mag_softiron_matrix[0][2];
  float my = x * mag_softiron_matrix[1][0] + y * mag_softiron_matrix[1][1] + z * mag_softiron_matrix[1][2];
  float mz = x * mag_softiron_matrix[2][0] + y * mag_softiron_matrix[2][1] + z * mag_softiron_matrix[2][2];

  // TODO: not sure about this one. i think its actually in dps
  // The filter library expects gyro data in degrees/s, but adafruit sensor
  // uses rad/s so we need to convert them first (or adapt the filter lib
  // where they are being converted)
  float gx = gyro.gyro.x;  // * 57.2958F;
  float gy = gyro.gyro.y; // * 57.2958F;
  float gz = gyro.gyro.z; // * 57.2958F;

  orientation_filter.update(gx, gy, gz,
                            accel.acceleration.x, accel.acceleration.y, accel.acceleration.z,
                            mx, my, mz);
  */

  /*
  // print the heading, pitch and roll
  float roll = orientation_filter.getRoll();
  float pitch = orientation_filter.getPitch();
  float heading = orientation_filter.getYaw();
  DEBUG_PRINT("Orientation: ");
  DEBUG_PRINT(heading);
  DEBUG_PRINT(" ");
  DEBUG_PRINT(pitch);
  DEBUG_PRINT(" ");
  DEBUG_PRINTLN(roll);
  */

  // TODO: this is giving a value between 12-13. supposedly this is for the chip to use and not really an environ sensor
  /*
  DEBUG_PRINT("temp: ");
  DEBUG_PRINT(temp.temperature);
  */

  /*
  // debugging sensors
  DEBUG_PRINT("accel (m/s^2): ");
  DEBUG_PRINT(accel.acceleration.x);
  DEBUG_PRINT("x ");
  DEBUG_PRINT(accel.acceleration.y);
  DEBUG_PRINT("y ");
  DEBUG_PRINT(accel.acceleration.z);
  DEBUG_PRINT("z ");
  DEBUG_PRINT("; mag (gauss): ");
  DEBUG_PRINT(mx);
  DEBUG_PRINT("x ");
  DEBUG_PRINT(my);
  DEBUG_PRINT("y ");
  DEBUG_PRINT(mz);
  DEBUG_PRINT("z ");
  DEBUG_PRINT("; gyro (dps): ");
  DEBUG_PRINT(gx);
  DEBUG_PRINT("x ");
  DEBUG_PRINT(gy);
  DEBUG_PRINT("y ");
  DEBUG_PRINT(gz);
  DEBUG_PRINTLN("z");
  */
}

static Orientation getOrientation() {
//  DEBUG_PRINT(F("Orientation: "));

  if (!sensor_setup) {
//    DEBUG_PRINTLN(F("UP (no sensor)"));
    return ORIENTED_UP;
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

  if ((absZ > absX) && (absZ > absY)) {
    // base orientation on Z
    if (z > 0) {
//      DEBUG_PRINTLN(F("UP"));
      return ORIENTED_UP;
    }
//    DEBUG_PRINTLN(F("DOWN"));
    return ORIENTED_DOWN;
  }

  if ((absY > absX) && (absY > absZ)) {
    // base orientation on Y
    if (y > 0) {
//      DEBUG_PRINTLN(F("USB_DOWN"));
      return ORIENTED_USB_DOWN;
    }
//    DEBUG_PRINTLN(F("USB_UP"));
    return ORIENTED_USB_UP;
  }

  // base orientation on X
  if (x < 0) {
//    DEBUG_PRINTLN(F("UPSIDE_DOWN"));
    return ORIENTED_PORTRAIT_UPSIDE_DOWN;
  }

//  DEBUG_PRINTLN(F("PORTRAIT"));
  return ORIENTED_PORTRAIT;
}
