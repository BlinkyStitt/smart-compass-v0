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
  Serial.print("Setting up sensors...");

  pinMode(LSM9DS1_CSAG, OUTPUT);
  pinMode(LSM9DS1_CSM, OUTPUT);

  // TODO: if lsm is broken, always display the compass?
  if (!lsm.begin()) {
    Serial.print(F("Oops, no LSM9DS1 detected... Check your wiring!"));
    while (1)
      ;
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

  Serial.println("done.");
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

static Orientation checkOrientation() {
  static Orientation currentOrientation;

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
      return ORIENTED_UP;
    }
    return ORIENTED_DOWN;
  }

  if ( (absY > absX) && (absY > absZ)) {
    // base orientation on Y
    if (y > 0) {
      return ORIENTED_USB_UP;
    }
    return  ORIENTED_USB_DOWN;
  }

  // base orientation on X
  if (x < 0) {
    return ORIENTED_SPI_UP;
  }

  return ORIENTED_SPI_DOWN;
}
