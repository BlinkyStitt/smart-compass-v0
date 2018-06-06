/* GPS */

elapsedMillis gps_ms = 0; // TODO: do we want this seperate from elapsed_ms? This should wrap around at 1000ms.

void setupGPS() {
  Serial.print("Setting up GPS... ");

  // 9600 NMEA is the default baud rate for Adafruit MTK GPS's
  GPS.begin(9600);
  gpsSerial.begin(9600);

  // TODO: which output mode should we use?
  // uncomment this line to turn on RMC (recommended minimum) and GGA (fix data) including altitude
  GPS.sendCommand(PMTK_SET_NMEA_OUTPUT_RMCGGA);
  // uncomment this line to turn on only the "minimum recommended" data
  // GPS.sendCommand(PMTK_SET_NMEA_OUTPUT_RMCONLY);
  // For parsing data, we don't suggest using anything but either RMC only or
  // RMC+GGA since the parser doesn't care about other sentences at this time

  // Set the update rate
  // different commands to set the update rate from once a second (1 Hz) to 10
  // times a second (10Hz) Note that these only control the rate at which the
  // position is echoed, to actually speed up the position fix you must also
  // send one of the position fix rate commands below too. For the parsing code
  // to work nicely and have time to sort thru the data, and print it out we
  // don't suggest using anything higher than 1 Hz
  GPS.sendCommand(PMTK_SET_NMEA_UPDATE_100_MILLIHERTZ); // Once every 10 seconds
  // GPS.sendCommand(PMTK_SET_NMEA_UPDATE_1HZ); // Once every second

  // Position fix update rate commands.
  GPS.sendCommand(PMTK_API_SET_FIX_CTL_100_MILLIHERTZ); // Once every 10 seconds
  GPS.sendCommand(PMTK_API_SET_FIX_CTL_1HZ); // Once every second

  // Request updates on antenna status, comment out to keep quiet
  // GPS.sendCommand(PGCMD_ANTENNA);

  // Ask for firmware version
  // TODO: why is this println instead of sendCommand?
  // TODO: how do we display the response?
  // gpsSerial.println(PMTK_Q_RELEASE);

  // TODO: wait until we get a GPS fix and then set the clock?

  Serial.println("done.");
}

long last_gps_update = 0;

void gpsReceive() {
  static AP_Declination declination_calculator;

  // limit updates to at most every 3 seconds
  if (last_gps_update and (millis() - last_gps_update < 3000)) {
    return;
  }

  // if no new sentence is received... (updates at most every 100 mHz thanks to PMTK_SET_NMEA_UPDATE_*)
  if (!GPS.newNMEAreceived()) {
    // exit
    return;
  }

  // we have a new sentence! we can check the checksum, parse it...
  // a tricky thing here is if we print the NMEA sentence, or data
  // we end up not listening and catching other sentences!
  // so be very wary if using OUTPUT_ALLDATA and trying to print out data
  // Serial.println(GPS.lastNMEA());   // this also sets the newNMEAreceived()
  // flag to false

  if (!GPS.parse(GPS.lastNMEA())) { // this also sets the newNMEAreceived() flag to false
    // we can fail to parse a sentence in which case we should just wait for another
    return;
  }

  if (!GPS.fix) {
    // TODO: clear my compass_message?
    return;
  }
  last_gps_update = millis();

  // TODO: do we have time before GPS.fix?
  // set the time to match the GPS if it isn't set or has drifted
  // TODO: should we just do this every time
  if ((second() - GPS.seconds > 2) || (timeStatus() == timeNotSet)) {
    Serial.print(second());
    Serial.print(" vs ");
    Serial.print(GPS.seconds);
    setTime(GPS.hour, GPS.minute, GPS.seconds, GPS.day, GPS.month, GPS.year);
    Serial.print("; Now: ");
    Serial.println(now());
  }

  // TODO: should we only do this if there is more drift?
  // TODO: this bounces around wildly. figure out some way to sync multiple clocks from a GPS fix and radio
  gps_ms = GPS.milliseconds;

  compass_messages[my_peer_id].last_updated_at = now();  // TODO: seconds or milliseconds?

  compass_messages[my_peer_id].latitude = GPS.latitude_fixed;
  compass_messages[my_peer_id].longitude = GPS.longitude_fixed;

  /*
  // hard code salesforce tower while debugging
  compass_messages[my_peer_id].latitude = 37789900;
  compass_messages[my_peer_id].longitude = -122396900;
  */

  // TODO: do we really need to do this every time? how expensive is this?
  // calculate magnetic declination in software. the gps chip and library
  // support it with GPS.magvariation but the Ultimate GPS module we are using
  // is configured to store log data instead of calculate it
  magnetic_declination = declination_calculator.get_declination(GPS.latitudeDegrees, GPS.longitudeDegrees);

  /*
  Serial.print("Fix: "); Serial.print((int)GPS.fix);
  Serial.print(" quality: "); Serial.println((int)GPS.fixquality);

  Serial.print("Satellites: "); Serial.println((int)GPS.satellites);

  Serial.print("Location 1: ");
  Serial.print(GPS.latitude, 4); Serial.print(GPS.lat);
  Serial.print(", ");
  Serial.print(GPS.longitude, 4); Serial.println(GPS.lon);
  */

  Serial.print("Location: ");
  Serial.print(GPS.latitudeDegrees, 4);
  Serial.print(", ");
  Serial.println(GPS.longitudeDegrees, 4);

  /*
  Serial.print("Location 3: ");
  Serial.print(GPS.latitude_fixed);
  Serial.print(", ");
  Serial.println(GPS.longitude_fixed);

  Serial.print("Speed (knots): "); Serial.println(GPS.speed);
  Serial.print("Angle: "); Serial.println(GPS.angle);
  Serial.print("Altitude: "); Serial.println(GPS.altitude);

  //Serial.print("GPS Mag variation: "); Serial.println(GPS.magvariation, 4);
  Serial.print("Software Mag variation: "); Serial.println(magnetic_declination,
  4);
  */

  // save to the SD card
  gps_log_file = SD.open(gps_log_filename, FILE_WRITE);

  // if the file opened okay, write to it:
  if (!gps_log_file) {
    // if the file didn't open, print an error and abort
    // Serial.println("error opening gps log");
    return;
  }

  Serial.print("Logging GPS data...");
  // TODO: only log if it is has changed by more than a couple meters

  gps_log_file.print(compass_messages[my_peer_id].last_updated_at);
  gps_log_file.print(",");
  gps_log_file.print(GPS.latitudeDegrees, 4);
  gps_log_file.print(",");
  gps_log_file.print(GPS.longitudeDegrees, 4);
  gps_log_file.print(",");
  gps_log_file.print(GPS.speed);
  gps_log_file.print(",");
  gps_log_file.print(GPS.angle);
  gps_log_file.println(";");

  // TODO: do we want to log anything else?

  // TODO: what happens if we lose power before closing/flushing?

  // close the file:
  gps_log_file.close();
}
