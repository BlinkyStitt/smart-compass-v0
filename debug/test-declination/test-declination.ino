// TODO: use addmod8

#include <Adafruit_GPS.h>
#include <ArduinoSort.h>
#include <AP_Declination.h>
// TODO: rewrite this to use rtczero
#include <TimeLib.h>

/* GPS */

#define gpsSerial Serial1
Adafruit_GPS GPS(&gpsSerial);

void setupGPS() {
  // 9600 NMEA is the default baud rate for Adafruit MTK GPS's
  GPS.begin(9600);
  gpsSerial.begin(9600);

  // uncomment this line to turn on RMC (recommended minimum) and GGA (fix data) including altitude
  GPS.sendCommand(PMTK_SET_NMEA_OUTPUT_RMCGGA);
  // uncomment this line to turn on only the "minimum recommended" data
  //GPS.sendCommand(PMTK_SET_NMEA_OUTPUT_RMCONLY);
  // For parsing data, we don't suggest using anything but either RMC only or RMC+GGA since
  // the parser doesn't care about other sentences at this time

  // Set the update rate
  // different commands to set the update rate from once a second (1 Hz) to 10 times a second (10Hz)
  // Note that these only control the rate at which the position is echoed, to actually speed up the
  // position fix you must also send one of the position fix rate commands below too.
  // For the parsing code to work nicely and have time to sort thru the data, and
  // print it out we don't suggest using anything higher than 1 Hz
  GPS.sendCommand(PMTK_SET_NMEA_UPDATE_1HZ);   // Once every 10 seconds

  // Position fix update rate commands.
  GPS.sendCommand(PMTK_API_SET_FIX_CTL_1HZ);   // Once every 10 seconds

  // Request updates on antenna status, comment out to keep quiet
  GPS.sendCommand(PGCMD_ANTENNA);

  // Ask for firmware version
  // TODO: why is this println instead of sendCommand? // TODO: how do we display the response?
  gpsSerial.println(PMTK_Q_RELEASE);

  // TODO: wait until we get a GPS fix and then set the clock?
}

/* Setup */

void setup() {
  // TODO: cut this into multiple functions
  Serial.begin(115200);
  while (!Serial) {  // TODO: remove this when done debugging otherwise it won't start without the usb plugged in
    delay(1);
  }

  // do more setup now that we have our configuration
  setupGPS();

  Serial.println("Starting...");
}

/* Loop */

AP_Declination declinationCalculator;

void loop() {
  // http://www.geomag.nrcan.gc.ca/calc/mdcal-r-en.php?date=2018-05-29&latitude=0&latitude_direction=1&longitude=0&longitude_direction=-1
  Serial.print("0, 0; 4° 58.02' West:"); Serial.println(declinationCalculator.get_declination(0.0, 0.0));

  // http://www.geomag.nrcan.gc.ca/calc/mdcal-r-en.php?date=2018-05-29&latitude=40.9107&latitude_direction=1&longitude=119.0560&longitude_direction=1
  Serial.print("BRC; 13° 31.50' East: "); Serial.println(declinationCalculator.get_declination(40.9107, -119.0560));

  // http://www.geomag.nrcan.gc.ca/calc/mdcal-r-en.php?date=2018-05-29&latitude=45&latitude_direction=1&longitude=90&longitude_direction=1
  Serial.print("45, 90; 2° 31.80' West: "); Serial.println(declinationCalculator.get_declination(45.0, 90.0));

  // http://www.geomag.nrcan.gc.ca/calc/mdcal-r-en.php?date=2018-05-29&latitude=45&latitude_direction=-1&longitude=90&longitude_direction=1
  Serial.print("-45, 90; 41° 13.56' West: "); Serial.println(declinationCalculator.get_declination(-45.0, 90.0));

  // http://www.geomag.nrcan.gc.ca/calc/mdcal-r-en.php?date=2018-05-29&latitude=45&latitude_direction=-1&longitude=90&longitude_direction=-1
  Serial.print("-45, -90; 21° 19.62' East: "); Serial.println(declinationCalculator.get_declination(-45.0, -90.0));

  Serial.print("37.756144, -122.432568; 13° 29.52' East: "); Serial.println(declinationCalculator.get_declination(37.756144, -122.432568));

  Serial.print("Waiting for fix");
  while (!GPS.fix) {
    delay(10000);
    Serial.print(".");
    gpsReceive();
  }
  Serial.println("done.");

  Serial.print("Current GPS: "); Serial.println(declinationCalculator.get_declination(GPS.latitudeDegrees, GPS.longitudeDegrees));

  Serial.println("Done");

  while(1) {
    delay(1000);
  }
}

void gpsReceive() {
  char c = GPS.read();

  // if no new sentence is received... (updates at most every 100 mHz thanks to PMTK_SET_NMEA_UPDATE_*)
  if (!GPS.newNMEAreceived()) {
    // exit
    return;
  }

  // we have a new sentence! we can check the checksum, parse it...
  // a tricky thing here is if we print the NMEA sentence, or data
  // we end up not listening and catching other sentences!
  // so be very wary if using OUTPUT_ALLDATA and trying to print out data
  //Serial.println(GPS.lastNMEA());   // this also sets the newNMEAreceived() flag to false

  if (!GPS.parse(GPS.lastNMEA())) {  // this also sets the newNMEAreceived() flag to false
    return;  // we can fail to parse a sentence in which case we should just wait for another
  }

  if (!GPS.fix) {
    return;
  }

  // set the time to match the GPS if it doesn't already match
  // we check the year just in case it is turned on right when a minute starts // TODO: check if setTime has been called instead?
  if ((second() != GPS.seconds) || (year() != GPS.year)) {
    setTime(GPS.hour, GPS.minute, GPS.seconds, GPS.day, GPS.month, GPS.year);
  }

  Serial.print("Now: "); Serial.println(rtc.getY2kEpoch());

  Serial.print("Fix: "); Serial.print((int)GPS.fix);
  Serial.print(" quality: "); Serial.println((int)GPS.fixquality);

  Serial.print("Location 1: ");
  Serial.print(GPS.latitude, 5); Serial.print(GPS.lat);
  Serial.print(", ");
  Serial.print(GPS.longitude, 5); Serial.println(GPS.lon);

  Serial.print("Location 2: ");
  Serial.print(GPS.latitudeDegrees, 5);
  Serial.print(", ");
  Serial.println(GPS.longitudeDegrees, 5);

  Serial.print("Location 3: ");
  Serial.print(GPS.latitude_fixed);
  Serial.print(", ");
  Serial.println(GPS.longitude_fixed);

  Serial.print("Speed (knots): "); Serial.println(GPS.speed);
  Serial.print("Angle: "); Serial.println(GPS.angle);
  Serial.print("Altitude: "); Serial.println(GPS.altitude);
  Serial.print("Satellites: "); Serial.println((int)GPS.satellites);

  Serial.println("done.\n");
}
