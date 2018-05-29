// TODO: use addmod8

#include <Adafruit_GPS.h>
#include <Adafruit_LSM9DS1.h>
#include <Adafruit_Sensor.h>
#include <ArduinoSort.h>
#include <AP_Declination.h>
#include <Bounce2.h>
#include <elapsedMillis.h>
#include <FastLED.h>
#include <RH_RF95.h>
#include <SD.h>
#include <SPI.h>
#include <TimeLib.h>
#include <TinyPacks.h>
#include <Wire.h>

// Pins 0 and 1 are used for Serial1 (GPS)
#define RFM95_INT          3   // already wired for us
#define RFM95_RST          4   // already wired for us
#define LED_DATA_PIN       5   // orange
#define RFM95_CS           8   // already wired for us
#define VBAT_PIN           9   // already wired for us  // A7
#define SDCARD_CS_PIN      10
#define LSM9DS1_CSAG       11
#define LSM9DS1_CSM        12
#define RED_LED_PIN        13  // already wired for us
#define SPI_MISO_PIN       22  // shared between Radio+Sensors+SD
#define SPI_MOSI_PIN       23  // shared between Radio+Sensors+SD
#define SPI_SCK_PIN        24  // shared between Radio+Sensors+SD

#define LED_CHIPSET        NEOPIXEL
#define DEFAULT_BRIGHTNESS 100  // TODO: read from SD (maybe this should be on the volume knob)
#define FRAMES_PER_SECOND  30  // TODO: bump this to 120

// TODO: read from SD card
const int max_peer_distance = 6000; // meters. peers this far away and further will be the minimum brightness
const int peer_led_time = 500; // ms. time to display the peer when multiple peers are the same direction
const int msPerPattern = 1 * 60 * 1000; // 1 minute  // TODO: tune this/read from SD card

const int numLEDs = 16;
CRGB leds[numLEDs];  // led[0] = magnetic north

const int numPeers = 4;  // TODO: this should be the max. read from the SD card instead
int my_peer_id = 0;  // TODO: read from the SD card instead
int my_network_id = 0;  // TODO: read from the SD card instead

/* Radio */

#define RF95_FREQ 915.0  // todo: read this from sd? 915.0 or 868.0MHz
#define RF95_POWER 23    // todo: read this from sd? 5-23dBm

RH_RF95 rf95(RFM95_CS, RFM95_INT);

void setupRadio() {
  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, HIGH);

  delay(100);  // give the radio time to wake up

  // manual reset
  digitalWrite(RFM95_RST, LOW);
  delay(10);
  digitalWrite(RFM95_RST, HIGH);
  delay(10);

  // Defaults after init are 434.0MHz, modulation GFSK_Rb250Fd250, +13dbM
  if (!rf95.init()) {
    Serial.println("LoRa radio init failed");
    while (1);
  }
  Serial.println("LoRa radio init OK!");

  // TODO: read from the SD card
  if (!rf95.setFrequency(RF95_FREQ)) {
    Serial.println("setFrequency failed");
    while (1);
  }
  Serial.print("Set Freq to: "); Serial.println(RF95_FREQ);

  // Defaults after init are 434.0MHz, 13dBm, Bw = 125 kHz, Cr = 4/5, Sf = 128chips/symbol, CRC on

  // The default transmitter power is 13dBm, using PA_BOOST.
  // If you are using RFM95/96/97/98 modules which uses the PA_BOOST transmitter pin, then
  // you can set transmitter powers from 5 to 23 dBm:
  // TODO: read from the SD card
  rf95.setTxPower(RF95_POWER, false);
}

PackWriter writer;

uint8_t radio_tx_buf[RH_RF95_MAX_MESSAGE_LEN];  // keep this off the stack

long peer_gps_updated_at[numPeers];
int peer_hue[numPeers];  // TODO: this is only 0-255, so use byte instead?
long peer_gps_latitude[numPeers];
long peer_gps_longitude[numPeers];

void radioTransmit() {
  // even if we don't have our own peer data, we want
  Serial.println("Transmitting..."); // Send a message to other smart compasses in the mesh

  // Pack
  // TODO: versioning? https://github.com/nanopb/nanopb ?
  // TODO: time this. if it takes a long time, add a FastLED.delay(2) for some dithering time
  writer.setBuffer(radio_tx_buf, RH_RF95_MAX_MESSAGE_LEN);
  writer.openMap();
    writer.putString("n");  // network id
    writer.putInteger(my_network_id);  // TODO: read network id from SD card. whats a reasonable max length?

    writer.putString("p");  // peer id
    writer.putInteger(my_peer_id);  // TODO: read peer id from SD card. integer from 0-255 to map to a palette (rainbow spectrum by default)

    int time_now = now();  // seconds precision is fine
    writer.putString("t");
    writer.putInteger(time_now);

    writer.putString("g");
    writer.openList();
      for (int pid = 0; pid < numPeers; pid++) {
        if (! peer_hue[pid]) {
          // if we don't have any info for this peer, skip sending anything
          break;
        }

        writer.openList();
          // TODO: write peer info // TODO: do this way more efficiently
          writer.putInteger(pid);  // TODO: read peer id from SD card
          writer.putInteger(time_now - peer_gps_updated_at[pid]);  // seconds since gps was last updated
          writer.putInteger(peer_hue[pid]);  // int from 0-255
          writer.putInteger(peer_gps_latitude[pid]);
          writer.putInteger(peer_gps_longitude[pid]);
        writer.close();
      }
    writer.close();
  writer.close();

  Serial.println("Sending...");
  // sending will wait for any previous send with waitPacketSent()
  FastLED.delay(10);  // TODO: get rid of this delay when the above prints are gone?
  rf95.send((uint8_t *)radio_tx_buf, writer.getOffset());

  // We don't actually need to block until the transmitter is no longer transmitting since we won't transmit again for a while
  // also, send will do its own waiting if it needs to
  /*
  Serial.println("Waiting for packet to complete...");
  FastLED.delay(10);
  rf95.waitPacketSent();  // TODO: this might get in the way. maybe right something that waits with FastLED.delay?
  */
}

PackReader reader;

uint8_t radio_rx_buf[RH_RF95_MAX_MESSAGE_LEN];  // keep this off the stack
uint8_t radio_rx_buf_len = 0;  // this will be set when its received

void radioReceive() {
  Serial.println("Checking for reply...");
  if (rf95.available()) {
    // Should be a reply message for us now
    if (rf95.recv(radio_rx_buf, &radio_rx_buf_len)) {
      Serial.print("RSSI: ");
      Serial.println(rf95.lastRssi(), DEC);

      reader.setBuffer(radio_rx_buf, radio_rx_buf_len);
      reader.next();
      if(!reader.openMap()) {
        Serial.print("Received someone else's message");
        // TODO: do something fun with the lights?
        return;
      }

      int tx_network_id, tx_peer_id, tx_peer_time;

      Serial.print("Message:");
      while (reader.next()) {
        if (reader.match("n")) {
          tx_network_id = reader.getBoolean();

          Serial.print(" ");
          Serial.print(tx_network_id);

          if (tx_network_id != my_network_id) {
            break;
          }
        } else if (reader.match("p")) {
          tx_peer_id = reader.getInteger();

          Serial.print(" ");
          Serial.print(tx_peer_id);

          if (tx_peer_id == my_peer_id) {
            Serial.println("peer ID collision!");
            break;
          }
        } else if (reader.match("t")) {
          tx_peer_time = reader.getInteger();

          Serial.print(" ");
          Serial.print(tx_peer_time);
        } else if (reader.match("g")) {
          if (reader.openList()) {
            while (reader.next()) {
              if (reader.openList()) {
                int pid = reader.getInteger();

                // ignore own stats from other peers
                if (pid != my_peer_id) {
                  // TODO: if this data is older than our local data, ignore it
                  // TODO: subtracting here seems backwards
                  int tx_peer_gps_updated_at = tx_peer_time - reader.getInteger();  // seconds since gps was last updated

                  // if the received time is newer than our record...
                  if (tx_peer_gps_updated_at > peer_gps_updated_at[pid]) {
                    // update our record
                    peer_hue[pid] = reader.getInteger();  // int from 0-255
                    peer_gps_latitude[pid] = reader.getInteger();
                    peer_gps_longitude[pid] = reader.getInteger();
                  }
                }

                // TODO: i'm pretty sure it's fine if we close without reading the other values in the case pid == my_peer_id
                reader.close();
              }
            }
            reader.close();
          }
        } else {
          Serial.print("Skipping unknown key");
          reader.next();
        }
      }

      reader.close();
    } else {
      Serial.println("Receive failed");
    }
  }
}

/* Sensors */

sensors_event_t accel, mag, gyro, temp;

Adafruit_LSM9DS1 lsm = Adafruit_LSM9DS1();  // i2c
// TODO: spi is lower power, but more wires
//Adafruit_LSM9DS1 lsm = Adafruit_LSM9DS1(LSM9DS1_XGCS, LSM9DS1_MCS);  // SPI

void setupSensor() {
//  pinMode(LSM9DS1_MCS, OUTPUT);
//  pinMode(LSM9DS1_XGCS, OUTPUT);

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

  Serial.println("lsm setup!");
}

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
  GPS.sendCommand(PMTK_SET_NMEA_UPDATE_100_MILLIHERTZ);   // Once every 10 seconds

  // Position fix update rate commands.
  GPS.sendCommand(PMTK_API_SET_FIX_CTL_100_MILLIHERTZ);   // Once every 10 seconds

  // Request updates on antenna status, comment out to keep quiet
  GPS.sendCommand(PGCMD_ANTENNA);

  // Ask for firmware version
  // TODO: why is this println instead of sendCommand? // TODO: how do we display the response?
  gpsSerial.println(PMTK_Q_RELEASE);

  // TODO: wait until we get a GPS fix and then set the clock?
}

/* SD */

String gps_log_filename = "";
File logFile;

void setupSD() {
  pinMode(SDCARD_CS_PIN, OUTPUT);

  if (!SD.begin(SDCARD_CS_PIN)) {
    Serial.println("SD initialization failed!");
    while(1);
  }
  Serial.println("SD initialization done.");

  // TODO: read SD card here to configure things
  my_peer_id = 0;  // TODO: read from SD
  my_network_id = 0; // TODO: read from SD card

  peer_hue[my_peer_id] = 0;  // TODO: read form SD card

  gps_log_filename += my_network_id;
  gps_log_filename += "-" + my_peer_id;
  gps_log_filename += ".log";

  // open the file. note that only one file can be open at a time,
  // so you have to close this one before opening another.
  logFile = SD.open("test.txt", FILE_WRITE);

  // TODO: delete this once I've tried it out
  // if the file opened okay, write to it:
  if (logFile) {
    Serial.print("Writing to test.txt...");
    logFile.println("testing 1, 2, 3.");
	// close the file:
    logFile.close();
    Serial.println("done.");
  } else {
    // if the file didn't open, print an error:
    Serial.println("error opening test.txt");
  }
}

/* lights */

void setupLights() {
  Serial.println("Setting up lights...");

  // TODO: do things with FastLED here
  // TODO: clock select pin for FastLED to OUTPUT like we do for the SDCARD?
  // TODO: FastLED.setMaxPowerInVoltsAndMilliamps( VOLTS, MAX_MA);
  FastLED.addLeds<LED_CHIPSET, LED_DATA_PIN>(leds, numLEDs).setCorrection(TypicalSMD5050);
  FastLED.setBrightness(DEFAULT_BRIGHTNESS);  // TODO: read this from the SD card
  FastLED.clear();
  FastLED.show();

  Serial.println("done");
}

/* Setup */

void setup() {
  // TODO: cut this into multiple functions
  Serial.begin(115200);
  while (!Serial) {  // TODO: remove this when done debugging otherwise it won't start without the usb plugged in
    delay(1);
  }

  /*
  // TODO: enable once it is connected
  setupSD();  // do this first to get our configuration
  */

  // do more setup now that we have our configuration
  setupGPS();
  setupRadio();

  // TODO: enable once it is connected
  //setupSensor();

  //setupLights();

  // TODO: set gHue? to myPeerHue?

  Serial.println("Starting...");
}

/* Loop */

elapsedMillis elapsedMs = 0;    // todo: do we care if this overflows?
elapsedMillis gpsMs = 0;  // TODO: do we want this seperate from elapsedMs? This should wrap around at 1000ms.
float magneticDeclination = 0.0;

uint8_t gHue = 0; // rotating "base color" used by some patterns

void loop() {
  // only do this every 10 seconds
  //EVERY_N_SECONDS( 10 ) { gpsReceive(); }  // TODO: this fastled helper doesn't work for us. maybe if we passed variables
  gpsReceive();

  // TODO: if its our time to transmit, radioTransmit(), else wait for radioReceive()

  // TODO: check_battery and blink if low

  // TODO: uncomment this once the lights are hooked up
  //updateLights();

  // using FastLED's delay allows for dithering
  FastLED.delay(1000/FRAMES_PER_SECOND);

  // do some periodic updates
  EVERY_N_MILLISECONDS( 10 ) { gHue--; } // slowly cycle the "base color" through the rainbow
}

void sensorReceive() {
  lsm.read();
  lsm.getEvent(&accel, &mag, &gyro, &temp);
}

AP_Declination declinationCalculator;

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
  // TODO: should we just do this every time
  if ((second() != GPS.seconds) || (year() != GPS.year)) {
    setTime(GPS.hour, GPS.minute, GPS.seconds, GPS.day, GPS.month, GPS.year);
  }

  // TODO: should we only do this if there is more drift?
  gpsMs = GPS.milliseconds;

  peer_gps_updated_at[my_peer_id] = now();

  peer_gps_longitude[my_peer_id] = GPS.longitude_fixed;
  peer_gps_latitude[my_peer_id] = GPS.latitude_fixed;

  Serial.print("Now: "); Serial.println(peer_gps_updated_at[my_peer_id]);

  Serial.print("Fix: "); Serial.print((int)GPS.fix);
  Serial.print(" quality: "); Serial.println((int)GPS.fixquality);

  Serial.print("Location: ");
  // TODO: find the docs for the format of this. i think it's ddmm.mmmm
  Serial.print(GPS.latitude, 4); Serial.print(GPS.lat);
  Serial.print(", ");
  // TODO: find the docs for the format of this. i think it's dddmm.mmmm
  Serial.print(GPS.longitude, 4); Serial.println(GPS.lon);

  Serial.print("Speed (knots): "); Serial.println(GPS.speed);
  Serial.print("Angle: "); Serial.println(GPS.angle);
  Serial.print("Altitude: "); Serial.println(GPS.altitude);
  Serial.print("Satellites: "); Serial.println((int)GPS.satellites);

  // TODO: only do this when we need it?
  // calculate magnetic declination in software. the gps chip and library support it with GPS.magvariation
  // but the Ultimate GPS module we are using is configured to store log data instead of calculate it
  Serial.print("GPS Mag variation: "); Serial.println(GPS.magvariation, 4);
  magneticDeclination = declinationCalculator.get_declination(GPS.latitude / 100.0, GPS.longitude / 100.0);  // NOTICE that this is latitude, NOT latitude_fixed
  Serial.print("Software Mag variation: "); Serial.println(magneticDeclination, 4);

  /*
  // TODO: uncomment this once the SD card is setup
  // save to the SD card
  logFile = SD.open(gps_log_filename, FILE_WRITE);

  // if the file opened okay, write to it:
  if (! logFile) {
    // if the file didn't open, print an error and abort
    Serial.println("error opening gps log");
    return;
  }

  Serial.print("Logging GPS data...");
  // TODO: only log if it is has changed by more than a couple meters

  logFile.print(peer_gps_updated_at[my_peer_id]);
  logFile.print(",");
  logFile.print(GPS.latitude, 4); logFile.print(GPS.lat);
  logFile.print(",");
  logFile.print(GPS.longitude, 4); logFile.println(GPS.lon);
  logFile.print(",");
  logFile.print(GPS.speed);
  logFile.print(",");
  logFile.print(GPS.angle);
  logFile.println(";");

  // TODO: do we want to log anything else?

  // TODO: what happens if we lose power before closing/flushing?

  // close the file:
  logFile.close();
  */

  Serial.println("done.\n");
}

// https://forum.arduino.cc/index.php?topic=98147.msg736165#msg736165
int rad2deg(long rad) {
  return rad * 57296 / 1000;
}

// https://forum.arduino.cc/index.php?topic=98147.msg736165#msg736165
int deg2rad(long deg) {
  return deg * 1000 / 57296;
}

// http://forum.arduino.cc/index.php?topic=393511.msg3232854#msg3232854
// find the bearing and distance in meters from point 1 to 2,
// using the equirectangular approximation
// lat and lon are degrees*1.0e6, 10 cm precision
// TODO: I copied this from the internet. make sure it actually works
// TODO: what are the units of the distance?
float course_to(long lat1, long lon1, long lat2, long lon2, float* distance) {
	float dlam, dphi, radius=6371000.0;

	dphi = deg2rad(lat1+lat2) * 0.5e-6; // average latitude in radians
	float cphi = cos(dphi);

	dphi = deg2rad(lat2-lat1) * 1.0e-6; // differences in degrees (to radians)
	dlam = deg2rad(lon2-lon1) * 1.0e-6;

	dlam *= cphi;  //correct for latitude

	float bearing = rad2deg(atan2(dlam,dphi)) + magneticDeclination;
	if (bearing < 0) bearing = bearing + 360.0;

  // offset bearing for true north -> magnetic north

	*distance = radius * sqrt(dphi * dphi + dlam * dlam);
	return bearing;
}

float check_battery() {
    // TODO: do something with this
    float measuredvbat = analogRead(VBAT_PIN);
    measuredvbat *= 2;    // we divided by 2, so multiply back
    measuredvbat *= 3.3;  // Multiply by 3.3V, our reference voltage
    measuredvbat /= 1024; // convert to voltage
    Serial.print("VBat: " ); Serial.println(measuredvbat);

    // return 0-3; dead, low, okay, full
    return measuredvbat;
}

// compare compass points
bool firstIsBrighter(CHSV first, CHSV second) {
  return first.value > second.value;
}

// this is not very efficient
const int maxCompassPoints = numPeers + 1;
CHSV compassPoints[numLEDs][maxCompassPoints];
int nextCompassPoint[numLEDs] = {0};

void updateCompassPoints() {
  // clear past compass points
  // TODO: this isn't very efficient since it recalculates everything every time
  for (int i = 0; i < numLEDs; i++) {
    nextCompassPoint[i] = 0;  // TODO: is this the right syntax?
  }

  // add north
  compassPoints[0][nextCompassPoint[0]] = CHSV(0, 255, 255);
  nextCompassPoint[0]++;

  // add west (TODO: remove this when done debugging)
  compassPoints[4][nextCompassPoint[4]] = CHSV(64, 255, 255);
  nextCompassPoint[4]++;

  // add south (TODO: remove this when done debugging)
  compassPoints[8][nextCompassPoint[8]] = CHSV(128, 255, 255);
  nextCompassPoint[8]++;

  // add east (TODO: remove this when done debugging)
  compassPoints[12][nextCompassPoint[12]] = CHSV(192, 255, 255);
  nextCompassPoint[12]++;

  for (int i = 0; i < numPeers; i++) {
    if (! peer_hue[i]) {
      // skip the peer if we don't have any gps data for them
      continue;
    }
    if (i == my_peer_id) {
      // don't show yourself
      continue;
    }

    float peer_distance;  // TODO: units? I'm guessing it is meters
    float magneticBearing = course_to(
      peer_gps_latitude[my_peer_id], peer_gps_longitude[my_peer_id],
      peer_gps_latitude[i], peer_gps_longitude[i],
      &peer_distance
    );

    // TODO: double check that this is looping the correct way around the LED circle
    int compassPointId = map(magneticBearing, 0, 360, numLEDs, 0);

    if (peer_distance < 10) {
      // TODO: what should we do for really close peers?
      continue;
    }

    // convert distance to brightness. the closer, the brighter //TODO: scurve instead of linear?
    // TODO: tune this
    int peer_brightness = map(min(max_peer_distance, peer_distance), 0, max_peer_distance, 255, 10);

    compassPoints[compassPointId][nextCompassPoint[compassPointId]] = CHSV(peer_hue[i], 255, peer_brightness);
    nextCompassPoint[compassPointId]++;
  }

  /*
  // TODO: this is broken
  for (int i = 0; i < numLEDs; i++) {
    // TODO: sort every time? i feel like there is a smarter way to insert. it probably doesn't matter
    // TODO: i think this is broken
    sortArray(compassPoints[i], nextCompassPoint[i], firstIsBrighter);
  }
  */
}

void updateLightsForCompass() {
  updateCompassPoints();

  // cycle through the colors for each light
  for (int i = 0; i < numLEDs; i++) {
    if (nextCompassPoint[i] == 0) {
      // no colors on this light. turn it off
      leds[i] = CRGB::Black;
      //Serial.print("No color for light #"); Serial.println(i);
      continue;
    } else {
      int j = 0;
      if (nextCompassPoint[i] > 1) {
        // there are one or more colors that want to shine on this one light. give each 500ms
        // TODO: instead give the closer peers (brighter compass points) more time?
        j = map(((elapsedMs / peer_led_time) % numPeers), 0, numPeers, 0, nextCompassPoint[i]);
      }

      //Serial.print("Displaying 1 of "); Serial.print(nextCompassPoint[i]); Serial.print(" colors for light #"); Serial.println(i);

      leds[i] = compassPoints[i][j];
    }
  }
}

void updateLightsForHanging() {
  // do awesome patterns
  int numLightPatterns = 3;  // TODO: how should this work? this seems

  // we use the actual time in ms instead of elapsedMs so that all the compasses are in near perfect sync
  long now_ms = now() * 1000 + gpsMs % 1000;  // TODO: type?

  // ms since 1970 divided into 1 minute chunks
  int patternId = now_ms / msPerPattern % numLightPatterns;

  switch (patternId) {
    case 0:
      updateLightsPattern0(now_ms);
      break;
    case 1:
      updateLightsPattern1(now_ms);
      break;
    case 2:
      updateLightsPattern2(now_ms);
      break;
  }
}

/* non-blocking lights are a lot harder than lights using delay! good luck! */
void updateLightsForLoading() {
  // TODO: write this. spin lights and fadeAll
}

void updateLightsPattern0(long now_ms) {
  // TODO: write this and name it something descriptive
}

void updateLightsPattern1(long now_ms) {
  // TODO: write this and name it something descriptive
}

void updateLightsPattern2(long now_ms) {
  // TODO: write this and name it something descriptive
}

void fadeAll() {
  // Dim all leds by 12.5% (but don't ever turn them off)
  // TODO: tune this
  for(int i = 0; i < numLEDs; i++) {
    leds[i].fadeLightBy(.125 * 256);
    //leds[i].fadeToBlackBy(32);
  }
}

void disableLights() {
  for(int i = 0; i < numLEDs; i++) {
    leds[i] = CRGB::Black;
  }
}

bool sensorFaceDown() {
  // TODO: actually do something with the sensors
  return false;
}

bool sensorHanging() {
  // TODO: actually do something with the sensors
  return false;
}

void updateLights() {
  sensorReceive();

  /*
  // TODO: uncomment this once the sensor is hooked up
  // update lights based on the sensor and GPS data

  if (sensorFaceDown()) {
    disableLights();
  } else if (!GPS.fix) {
    updateLightsForLoading();
  } else {
    if (sensorHanging()) {
      updateLightsForHanging();
    } else {
      updateLightsForCompass();
    }
  }
  */
  updateLightsForCompass();

  // debugging sensors
  Serial.print("mag:  ");
    Serial.print(mag.magnetic.x); Serial.print("x ");
    Serial.print(mag.magnetic.y); Serial.print("y ");
    Serial.print(mag.magnetic.z); Serial.println("z ");

  Serial.print("gyro: ");
    Serial.print(gyro.gyro.x); Serial.print("x ");
    Serial.print(gyro.gyro.y); Serial.print("y ");
    Serial.print(gyro.gyro.z); Serial.println("z ");

  /*
  // TODO: this keep reading negative numbers...
  Serial.print("temp: "); Serial.println(temp.temperature);
  */

  // debugging lights
  for (int i = 0; i < numLEDs; i++) {
    if (leds[i]) {
      // TODO: better logging
      Serial.print("X");
    } else {
      Serial.print("O");
    }
  }
  Serial.println();

  // display the colors
  FastLED.show();
}
