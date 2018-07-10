/* GPS */

void setupGPS() {
  DEBUG_PRINT(F("Setting up GPS... "));

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

  // TODO: what update rate should we use?
  // Set the update rate
  // different commands to set the update rate from once a second (1 Hz) to 10
  // times a second (10Hz) Note that these only control the rate at which the
  // position is echoed, to actually speed up the position fix you must also
  // send one of the position fix rate commands below too. For the parsing code
  // to work nicely and have time to sort thru the data, and print it out we
  // don't suggest using anything higher than 1 Hz
  // GPS.sendCommand(PMTK_SET_NMEA_UPDATE_100_MILLIHERTZ); // Once every 10 seconds
  GPS.sendCommand(PMTK_SET_NMEA_UPDATE_1HZ); // Once every second

  // Position fix update rate commands.
  // GPS.sendCommand(PMTK_API_SET_FIX_CTL_100_MILLIHERTZ); // Once every 10 seconds
  GPS.sendCommand(PMTK_API_SET_FIX_CTL_1HZ); // Once every second

  // Request updates on antenna status, comment out to keep quiet
  // GPS.sendCommand(PGCMD_ANTENNA);

  // Ask for firmware version
  // TODO: why is this println instead of sendCommand?
  // TODO: how do we display the response?
  // gpsSerial.println(PMTK_Q_RELEASE);

  // TODO: wait until we get a GPS fix and then set the clock?

  DEBUG_PRINTLN(F("done."));
}

unsigned long getGPSTime() {
  // 2018 "epoch"
  // TODO: this jumps around a bit since it is updated when gps parsing happens. i liked the internal rtc, but it was
  // slow to use
  unsigned long t = (GPS.year - 2018);

  t = (t * 12) + GPS.month;

  // not every month has 31 days, but thats fine. we just don't want to roll back last_updated_at
  t = (t * 31) + GPS.day;

  t = (t * 24) + GPS.hour;

  t = (t * 60) + GPS.minute;

  t = (t * 60) + GPS.seconds;

  // according to the docs, the GPS has an RTC so if you have a fix with the battery, you'll always be able to check the
  // time i can't find where in the code this is handled though. i only see the time set when a message is parsed so i
  // think that's when it happens and they just use the rtc to improve cold start
  return t;
}

void gpsReceive() {
  static AP_Declination declination_calculator;
  static long last_gps_update = 0;
  static int last_logged_latitude = 0;
  static int last_logged_longitude = 0;
  static const int min_update_interval = broadcast_time_s * num_peers * 1000; // TODO: tune this

  // limit updates
  /*
  // TODO: enable this?
  if (last_gps_update and (millis() - last_gps_update < min_update_interval)) {
    return;
  }
  */

  // if no new sentence is received... (updates at most every 100 mHz thanks to PMTK_SET_NMEA_UPDATE_*)
  if (!GPS.newNMEAreceived()) {
    // exit
    return;
  }

  if (!GPS.parse(GPS.lastNMEA())) { // this also sets the newNMEAreceived() flag to false
    // we can fail to parse a sentence in which case we should just wait for another
    return;
  }

  if (!GPS.fix) {
    // TODO: clear my compass_message?
    return;
  }

  // we used to update an rtc here, but the GPS time seems to work better. setting the rtc is slow

  //updateLights();

  last_gps_update = millis();

  compass_messages[my_peer_id].last_updated_at = getGPSTime(); // TODO: this is seconds. should we use milliseconds?

  // A value in decimal degrees to 5 decimal places is precise to 1.1132 meter at the equator
  // Accuracy to 5 decimal places with commercial GPS units can only be achieved with differential correction.
  // so lets divide by 1000 to get to ~11 meter accuracy (TODO: round?)
  compass_messages[my_peer_id].latitude = GPS.latitude_fixed;
  compass_messages[my_peer_id].longitude = GPS.longitude_fixed;

  updateLights();

  // compare lat/long with less precision so we don't log all the time
  // TODO: what units is this? 30 meters?
  if ((abs(last_logged_latitude - compass_messages[my_peer_id].latitude) < 3000) and (abs(last_logged_longitude - compass_messages[my_peer_id].longitude) < 3000)) {
    // don't bother saving if the points haven't changed much
    return;
  }

  // everything under this only happens if the location has changed by 30 meters

  updateLights();

  DEBUG_PRINT("last_logged_latitude=");
  DEBUG_PRINTLN(last_logged_latitude);
  DEBUG_PRINT("last_logged_longitude=");
  DEBUG_PRINTLN(last_logged_longitude);

  last_logged_latitude = compass_messages[my_peer_id].latitude;
  last_logged_longitude = compass_messages[my_peer_id].longitude;

  /*
  // hard code salesforce tower while debugging
  // TODO: enable this by setting config on the SD card
  compass_messages[my_peer_id].latitude = 37789900;
  compass_messages[my_peer_id].longitude = -122396900;
  */

  /*
  DEBUG_PRINT("Fix: "); DEBUG_PRINT((int)GPS.fix);
  DEBUG_PRINT(" quality: "); DEBUG_PRINTLN((int)GPS.fixquality);

  DEBUG_PRINT("Satellites: "); DEBUG_PRINTLN((int)GPS.satellites);

  DEBUG_PRINT("Location 1: ");
  DEBUG_PRINT(GPS.latitude, 4); DEBUG_PRINT(GPS.lat);
  DEBUG_PRINT(", ");
  DEBUG_PRINT(GPS.longitude, 4); DEBUG_PRINTLN(GPS.lon);
  */

  DEBUG_PRINT(F("Location: "));
  DEBUG_PRINT2(GPS.latitudeDegrees, 4);
  DEBUG_PRINT(F(", "));
  DEBUG_PRINTLN2(GPS.longitudeDegrees, 4);

  /*
  DEBUG_PRINT("Location 3: ");
  DEBUG_PRINT(GPS.latitude_fixed);
  DEBUG_PRINT(", ");
  DEBUG_PRINTLN(GPS.longitude_fixed);

  DEBUG_PRINT("Speed (knots): "); DEBUG_PRINTLN(GPS.speed);
  DEBUG_PRINT("Angle: "); DEBUG_PRINTLN(GPS.angle);
  DEBUG_PRINT("Altitude: "); DEBUG_PRINTLN(GPS.altitude);

  //DEBUG_PRINT("GPS Mag variation: "); DEBUG_PRINTLN(GPS.magvariation, 4);
  DEBUG_PRINT("Software Mag variation: "); DEBUG_PRINTLN(g_magnetic_declination,
  4);
  */

  // update lights here because logging to GPS can be slow
  updateLights();

  // calculate magnetic declination in software. the gps chip and library
  // support it with GPS.magvariation but the Ultimate GPS module we are using
  // is configured to store log data instead of calculate declination
  g_magnetic_declination = declination_calculator.get_declination(GPS.latitudeDegrees, GPS.longitudeDegrees);

  // update lights here because logging to GPS can be slow
  updateLights();

  // open the SD card
  my_file = SD.open(gps_log_filename, FILE_WRITE);
  updateLights();

  // if the file opened okay, write to it:
  if (!my_file) {
    // if the file didn't open, print an error and abort
    DEBUG_PRINT(F("error opening gps log: "));
    DEBUG_PRINTLN(gps_log_filename);
    return;
  }
  updateLights();

  DEBUG_PRINT(F("Logging GPS data... "));
  DEBUG_PRINTLN(gps_log_filename);
  updateLights();

  my_file.print(compass_messages[my_peer_id].last_updated_at);
  my_file.print(",");
  updateLights();

  my_file.print(GPS.latitudeDegrees, 4);
  my_file.print(",");
  updateLights();

  my_file.print(GPS.longitudeDegrees, 4);
  my_file.print(",");
  updateLights();

  my_file.print(GPS.speed);
  my_file.print(",");
  updateLights();

  my_file.print(GPS.angle);
  my_file.println(";");

  // TODO: do we want to log anything else?

  // update lights here because logging to GPS can be slow
  updateLights();

  // close the file:
  my_file.close();

  // update lights here because logging to GPS can be slow
  updateLights();

  DEBUG_PRINTLN(F("Logging done."));

  // TODO: sort compass_pins
}
