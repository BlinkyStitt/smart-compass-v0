// TODO: use addmod8

#include <AP_Declination.h>
#include <Adafruit_GPS.h>
#include <Adafruit_LSM9DS1.h>
#include <Adafruit_Sensor.h>
#include <ArduinoSort.h>
#include <Bounce2.h>
#include <FastLED.h>
#include <RH_RF95.h>
#include <SD.h>
#include <SPI.h>
#include <elapsedMillis.h>
// TODO: fork TimeLib to include ms
#include <TimeLib.h>
#include <Wire.h>

#include "smart_compass.pb.h"
#include <pb_decode.h>
#include <pb_encode.h>

// Pins 0 and 1 are used for Serial1 (GPS)
#define RFM95_INT 3    // already wired for us
#define RFM95_RST 4    // already wired for us
#define LED_DATA_PIN 5 // orange
#define RFM95_CS 8     // already wired for us
#define VBAT_PIN 9     // already wired for us  // A7
#define SDCARD_CS_PIN 10
#define LSM9DS1_CSAG 11
#define LSM9DS1_CSM 12
#define RED_LED_PIN 13  // already wired for us
#define SPI_MISO_PIN 22 // shared between Radio+Sensors+SD
#define SPI_MOSI_PIN 23 // shared between Radio+Sensors+SD
#define SPI_SCK_PIN 24  // shared between Radio+Sensors+SD

#define LED_CHIPSET NEOPIXEL
#define DEFAULT_BRIGHTNESS 100 // TODO: read from SD (maybe this should be on the volume knob)
#define FRAMES_PER_SECOND 30  // TODO: bump this to 120

// TODO: read from SD card
const int broadcast_time_ms = 250;  // TODO: 1 second is way too long. that ends up being
const int max_peer_distance = 5000;     // meters. peers this far away and further will be the minimum brightness
const int peer_led_time = 500;          // ms. time to display the peer when multiple peers are the same direction
const int msPerPattern = 1 * 60 * 1000; // 1 minute  // TODO: tune this/read from SD card

const int numLEDs = 16;
CRGB leds[numLEDs]; // led[0] = magnetic north

const int numPeers = 4; // TODO: this should be the max. read from the SD card instead

SmartCompassMessage compass_messages[numPeers] = {SmartCompassMessage_init_default};

int my_network_id, my_peer_id, my_hue, my_saturation;

/* Radio */

#define RF95_FREQ 915.0 // todo: read this from sd? 915.0 or 868.0MHz
#define RF95_POWER 20   // todo: read this from sd? 5-23dBm

RH_RF95 rf95(RFM95_CS, RFM95_INT);

void setupRadio() {
  Serial.print("Setting up Radio... ");

  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, HIGH);

  delay(100); // give the radio time to wake up

  // manual reset
  digitalWrite(RFM95_RST, LOW);
  delay(10);
  digitalWrite(RFM95_RST, HIGH);
  delay(10);

  // Defaults after init are 434.0MHz, modulation GFSK_Rb250Fd250, +13dbM
  if (!rf95.init()) {
    Serial.println("failed! Cannot proceed!");
    while (1)
      ;
  }

  // TODO: read frequency the SD card
  if (!rf95.setFrequency(RF95_FREQ)) {
    Serial.println("setFrequency failed! Cannot proceed!");
    while (1)
      ;
  }
  Serial.print("Freq: ");
  Serial.print(RF95_FREQ);

  // Defaults after init are 434.0MHz, 13dBm, Bw = 125 kHz, Cr = 4/5, Sf = 128chips/symbol, CRC on

  // The default transmitter power is 13dBm, using PA_BOOST.
  // If you are using RFM95/96/97/98 modules which uses the PA_BOOST transmitter pin, then you can set transmitter
  // powers from 5 to 23 dBm:
  // TODO: read power from the SD card
  rf95.setTxPower(RF95_POWER, false);

  Serial.println(" done.");
}

void radioTransmit(int pid) {
  if (timeStatus() == timeNotSet) {
    Serial.println("Time not set! Skipping transmission.");
    return;
  }

  // TODO: should we transmit peer data even if we don't have local time set?
  // maybe set time from a peer?
  Serial.print("My time to transmit (");
  Serial.print(now());
  Serial.println(")... ");

  // TODO: what if this is really slow? we should transmit 1 peer per loop so
  // that we run updateLights/Sensors/etc.
  if (!compass_messages[pid].hue) {
    // if we don't have any info for this peer, skip sending anything
    // TODO: this blocks us from being able to use pure red
    Serial.print("No peer data to transmit for ");
    Serial.println(pid);
    return;
  }

  Serial.print("Message: ");

  Serial.print("n=");
  Serial.print(compass_messages[pid].network_id);

  Serial.print(" txp=");
  Serial.print(compass_messages[pid].tx_peer_id);

  Serial.print(" p=");
  Serial.print(compass_messages[pid].peer_id);

  unsigned long time_now = now_millis();
  compass_messages[pid].tx_time = time_now;

  Serial.print(" now=");
  Serial.print(time_now);

  Serial.print(" t=");
  Serial.print(compass_messages[pid].last_updated_at);

  Serial.print(" lat=");
  Serial.print(compass_messages[pid].latitude);

  Serial.print(" lon=");
  Serial.print(compass_messages[pid].longitude);

  Serial.print(" EOM. ");

  static uint8_t radio_buf[RH_RF95_MAX_MESSAGE_LEN];

  // Create a stream that will write to our buffer
  // TODO: I think this should be static or global
  pb_ostream_t stream = pb_ostream_from_buffer(radio_buf, sizeof(radio_buf));

  if (!pb_encode(&stream, SmartCompassMessage_fields, &compass_messages[pid])) {
    Serial.println("ERROR ENCODING!");
    return;
  }

  // sending will wait for any previous send with waitPacketSent(), but we want to dither LEDs
  Serial.print("sending... ");
  rf95.send((uint8_t *)radio_buf, stream.bytes_written);
  while (rf95.mode() == RH_RF95_MODE_TX) {
    FastLED.delay(1);
  }
  Serial.println("done.");

  // Serial.print("Sent packed message: ");
  // Serial.println((char*)radio_buf);
}

void radioReceive() {
  // i had separate buffers for tx and for rx, but that doesn't seem necessary
  static uint8_t radio_buf[RH_RF95_MAX_MESSAGE_LEN]; // TODO: keep this off the stack
  static uint8_t radio_buf_len;
  static SmartCompassMessage message = SmartCompassMessage_init_default;

  // Serial.println("Checking for reply...");
  if (rf95.available()) {
    // radio_buf_len = sizeof(radio_buf);  // TODO: protobuf uses size_t, but radio uses uint8_t
    radio_buf_len = RH_RF95_MAX_MESSAGE_LEN; // reset this to max length otherwise it won't receive the full message!

    // Should be a reply message for us now
    if (rf95.recv(radio_buf, &radio_buf_len)) {
      Serial.print("RSSI: ");
      Serial.println(rf95.lastRssi(), DEC);

      pb_istream_t stream = pb_istream_from_buffer(radio_buf, radio_buf_len);
      if (!pb_decode(&stream, SmartCompassMessage_fields, &message)) {
        Serial.print("Decoding failed: ");
        Serial.println(PB_GET_ERROR(&stream));
        return;
      }

      if (message.network_id != my_network_id) {
        Serial.print("Message is for another network: ");
        Serial.println(message.network_id);
        return;
      }

      if (message.tx_peer_id == my_peer_id) {
        Serial.print("ERROR! Peer id collision! ");
        Serial.println(my_peer_id);
        return;
      }

      if (message.peer_id == my_peer_id) {
        Serial.println("Ignoring stats about myself.");
        return;
      }

      if (message.last_updated_at < compass_messages[message.peer_id].last_updated_at) {
        Serial.println("Ignoring old message.");
        return;
      }

      compass_messages[message.peer_id].last_updated_at = message.last_updated_at;
      compass_messages[message.peer_id].hue = message.hue;
      compass_messages[message.peer_id].saturation = message.saturation;
      compass_messages[message.peer_id].latitude = message.latitude;
      compass_messages[message.peer_id].longitude = message.longitude;

      Serial.print("Message for peer #");
      Serial.print(message.peer_id);
      Serial.print(" from #");
      Serial.print(message.tx_peer_id);
      Serial.print(": t=");
      Serial.print(message.tx_time);
      Serial.print(" h=");
      Serial.print(message.hue);
      Serial.print(" s=");
      Serial.print(message.saturation);
      Serial.print(" lat=");
      Serial.print(message.latitude);
      Serial.print(" lon=");
      Serial.println(message.longitude);

      // TODO: move the rest of this from TinyPack to protobuf
      /*
      if (timeStatus() != timeSet) {
        // TODO: set time from peer's time (use ms)
      }
      */
    } else {
      Serial.println("Receive failed");
    }
  }
}

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

/* GPS */

#define gpsSerial Serial1
Adafruit_GPS GPS(&gpsSerial);

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
  //GPS.sendCommand(PMTK_SET_NMEA_UPDATE_100_MILLIHERTZ); // Once every 10 seconds
  GPS.sendCommand(PMTK_SET_NMEA_UPDATE_1HZ); // Once every second

  // Position fix update rate commands.
  //GPS.sendCommand(PMTK_API_SET_FIX_CTL_100_MILLIHERTZ); // Once every 10 seconds
  GPS.sendCommand(PMTK_API_SET_FIX_CTL_1HZ); // Once every second

  // Request updates on antenna status, comment out to keep quiet
  //GPS.sendCommand(PGCMD_ANTENNA);

  // Ask for firmware version
  // TODO: why is this println instead of sendCommand?
  // TODO: how do we display the response?
  //gpsSerial.println(PMTK_Q_RELEASE);

  // TODO: wait until we get a GPS fix and then set the clock?

  Serial.println("done.");
}

/* SD */

String gps_log_filename = "";
File logFile;

void setupSD() {
  Serial.print("Setting up SD... ");

  pinMode(SDCARD_CS_PIN, OUTPUT);

  if (!SD.begin(SDCARD_CS_PIN)) {
    Serial.println("failed! Cannot proceed!");
    while (1)
      ;
  }

  Serial.println("done.");

  gps_log_filename += my_network_id;
  gps_log_filename += "-" + my_peer_id;
  gps_log_filename += ".log";

  // open the file. note that only one file can be open at a time, so you have to close this one before opening another.
  logFile = SD.open("test.txt", FILE_WRITE);

  // if the file opened okay, write to it:
  // TODO: delete this once I've tried it out
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

  Serial.println("done.");
}

/* lights */

void setupLights() {
  Serial.print("Setting up lights... ");

  pinMode(LED_DATA_PIN, OUTPUT);

  // TODO: FastLED.setMaxPowerInVoltsAndMilliamps( VOLTS, MAX_MA);

  FastLED.addLeds<LED_CHIPSET, LED_DATA_PIN>(leds, numLEDs).setCorrection(TypicalSMD5050);
  FastLED.setBrightness(DEFAULT_BRIGHTNESS); // TODO: read this from the SD card
  FastLED.clear();
  FastLED.show();

  Serial.println("done.");
}

/* interrupts - https://gist.github.com/nonsintetic/ad13e70f164801325f5f552f84306d6f */

uint32_t sampleRate = 50; // how many times per second the TC5_Handler() gets called

void TC5_Handler(void) {
  // YOUR CODE HERE

  // check GPS for data. do this here so that a slow framerate doesn't slow reading from GPS
  char c = GPS.read();

  // END OF YOUR CODE
  TC5->COUNT16.INTFLAG.bit.MC0 = 1; // don't change this, it's part of the timer code
}

/*
 *  TIMER SPECIFIC FUNCTIONS FOLLOW
 *  you shouldn't change these unless you know what you're doing
 */

// Configures the TC to generate output events at the sample frequency.
// Configures the TC in Frequency Generation mode, with an event output once
// each time the audio sample frequency period expires.
void tcConfigure(int sampleRate) {
  // Enable GCLK for TCC2 and TC5 (timer counter input clock)
  GCLK->CLKCTRL.reg = (uint16_t)(GCLK_CLKCTRL_CLKEN | GCLK_CLKCTRL_GEN_GCLK0 | GCLK_CLKCTRL_ID(GCM_TC4_TC5));
  while (GCLK->STATUS.bit.SYNCBUSY)
    ;

  tcReset(); // reset TC5

  // Set Timer counter Mode to 16 bits
  TC5->COUNT16.CTRLA.reg |= TC_CTRLA_MODE_COUNT16;
  // Set TC5 mode as match frequency
  TC5->COUNT16.CTRLA.reg |= TC_CTRLA_WAVEGEN_MFRQ;
  // set prescaler and enable TC5
  TC5->COUNT16.CTRLA.reg |= TC_CTRLA_PRESCALER_DIV1 | TC_CTRLA_ENABLE;
  // set TC5 timer counter based off of the system clock and the user defined
  // sample rate or waveform
  TC5->COUNT16.CC[0].reg = (uint16_t)(SystemCoreClock / sampleRate - 1);
  while (tcIsSyncing())
    ;

  // Configure interrupt request
  NVIC_DisableIRQ(TC5_IRQn);
  NVIC_ClearPendingIRQ(TC5_IRQn);
  NVIC_SetPriority(TC5_IRQn, 0);
  NVIC_EnableIRQ(TC5_IRQn);

  // Enable the TC5 interrupt request
  TC5->COUNT16.INTENSET.bit.MC0 = 1;
  while (tcIsSyncing())
    ; // wait until TC5 is done syncing
}

// Function that is used to check if TC5 is done syncing
// returns true when it is done syncing
bool tcIsSyncing() { return TC5->COUNT16.STATUS.reg & TC_STATUS_SYNCBUSY; }

// This function enables TC5 and waits for it to be ready
void tcStartCounter() {
  TC5->COUNT16.CTRLA.reg |= TC_CTRLA_ENABLE; // set the CTRLA register
  while (tcIsSyncing())
    ; // wait until snyc'd
}

// Reset TC5
void tcReset() {
  TC5->COUNT16.CTRLA.reg = TC_CTRLA_SWRST;
  while (tcIsSyncing())
    ;
  while (TC5->COUNT16.CTRLA.bit.SWRST)
    ;
}

// disable TC5
void tcDisable() {
  TC5->COUNT16.CTRLA.reg &= ~TC_CTRLA_ENABLE;
  while (tcIsSyncing())
    ;
}

/* Setup */

void setup() {
  // TODO: cut this into multiple functions
  Serial.begin(115200);

  delay(1000);

  Serial.println("Setting up...");
  randomSeed(analogRead(5));

  // setupSD();  // do this first to get our configuration

  // TODO: read SD card here to configure things
  my_network_id = 0;
  my_peer_id = random(1, numPeers); // TODO: don't use 0 since it seems to be the default when we have trouble parsing
  my_hue = 128;
  my_saturation = 50;

  Serial.print("My peer id: ");
  Serial.println(my_peer_id);

  // initialize compass messages
  for (int i = 0; i < numPeers; i++) {
    compass_messages[i].network_id = my_network_id;
    compass_messages[i].tx_peer_id = my_peer_id;
    compass_messages[i].peer_id = i;

    // hue, latitude, longitude are set for remote peers when a message for this peer is received
    // latitude, longitude for my_peer_id are set when GPS data is received
  }

  compass_messages[my_peer_id].hue = my_hue;
  compass_messages[my_peer_id].saturation = my_saturation;

  // do more setup now that we have our configuration
  setupGPS();

  setupRadio();

  // TODO: enable once it is connected
  setupSensor();

  setupLights();

  // TODO: set gHue? to myPeerHue?

  tcConfigure(sampleRate); // configure the timer to run at <sampleRate>Hertz
  tcStartCounter();        // starts the timer

  Serial.println("Starting...");
}

/* Loop */

elapsedMillis elapsedMs = 0; // todo: do we care if this overflows?
elapsedMillis gpsMs = 0;     // TODO: do we want this seperate from elapsedMs? This
                             // should wrap around at 1000ms.
float magneticDeclination = 0.0;

uint8_t gHue = 0; // rotating "base color" used by some patterns
bool should_transmit[numPeers] = {true};

void loop() {
  // TODO: numPeers * numPeers can get pretty big! maybe
  static unsigned int time_segments = numPeers * numPeers; // each peer needs enough time to broadcast every other peer
  static unsigned int time_segment_id, broadcasting_peer_id, broadcasted_peer_id;

  updateLights();

  // TODO: only do this every 10 seconds
  // TODO: fastled EVERY_N_SECONDS helper doesn't work for us. maybe if we passed variables
  gpsReceive();

  if (timeStatus() == timeNotSet) {
    radioReceive();
  } else {
    // if it's our time to transmit, radioTransmit(), else wait for radioReceive()
    // TODO: should there be downtime when no one is transmitting or receiving?

    time_segment_id = (now_millis() / broadcast_time_ms) % time_segments;
    broadcasting_peer_id = time_segment_id / numPeers;
    broadcasted_peer_id = time_segment_id % numPeers;

    /*
    Serial.print("broadcasting_peer_id / broadcasted_peer_id: ");
    Serial.print(broadcasting_peer_id);
    Serial.print(" / ");
    Serial.println(broadcasted_peer_id);
    */

    if (broadcasting_peer_id == my_peer_id) {
      if (should_transmit[broadcasted_peer_id]) {
        radioTransmit(broadcasted_peer_id);
        should_transmit[broadcasted_peer_id] = false;
      } else {
        // TODO: it's our time to transmit, but we already did. what should we do?
      }
    } else {
      for (int i = 0; i < numPeers; i++) {
        should_transmit[i] = true;
      }
      radioReceive();
    }
  }

  // TODO: don't do this. this delays too long. and gets in the way of the radio tx/rx
  //delayToSyncFrameRate(FRAMES_PER_SECOND);
  FastLED.delay(10);  // don't sleep too long or you get in the way of radios
}

void sensorReceive() {
  lsm.read();
  lsm.getEvent(&accel, &mag, &gyro, &temp);

  // TODO: this is giving a value between 12-13
  /*
  Serial.print("temp: ");
  Serial.print(temp.temperature);
  */

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
}

void gpsReceive() {
  static AP_Declination declinationCalculator;

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
    return;
  }

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
  gpsMs = GPS.milliseconds;

  compass_messages[my_peer_id].last_updated_at = now_millis();
  compass_messages[my_peer_id].latitude = GPS.latitude_fixed;
  compass_messages[my_peer_id].longitude = GPS.longitude_fixed;

  // TODO: do we really need to do this every time? how expensive is this?
  // calculate magnetic declination in software. the gps chip and library
  // support it with GPS.magvariation but the Ultimate GPS module we are using
  // is configured to store log data instead of calculate it
  magneticDeclination = declinationCalculator.get_declination(GPS.latitudeDegrees, GPS.longitudeDegrees);

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

  // TODO: only do this when we need it?
  //Serial.print("GPS Mag variation: "); Serial.println(GPS.magvariation, 4);
  Serial.print("Software Mag variation: "); Serial.println(magneticDeclination,
  4);
  */

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
}

// https://forum.arduino.cc/index.php?topic=98147.msg736165#msg736165
int rad2deg(long rad) { return rad * 57296 / 1000; }

// https://forum.arduino.cc/index.php?topic=98147.msg736165#msg736165
int deg2rad(long deg) { return deg * 1000 / 57296; }

// http://forum.arduino.cc/index.php?topic=393511.msg3232854#msg3232854
// find the bearing and distance in meters from point 1 to 2, using the equirectangular approximation
// lat and lon are degrees*1.0e6, 10 cm precision
// TODO: I copied this from the internet. make sure it actually works
// TODO: what are the units of the distance? meters?
float course_to(long lat1, long lon1, long lat2, long lon2, float *distance) {
  float dlam, dphi, radius = 6371000.0;

  dphi = deg2rad(lat1 + lat2) * 0.5e-6; // average latitude in radians
  float cphi = cos(dphi);

  dphi = deg2rad(lat2 - lat1) * 1.0e-6; // differences in degrees (to radians)
  dlam = deg2rad(lon2 - lon1) * 1.0e-6;

  dlam *= cphi; // correct for latitude

  // calculate bearing and offset for true north -> magnetic north
  float magneticBearing = rad2deg(atan2(dlam, dphi)) + magneticDeclination;

  // wrap around
  if (magneticBearing < 0) {
    magneticBearing += 360.0;
  } else if (magneticBearing >= 360) {
    magneticBearing -= 360.0;
  }

  *distance = radius * sqrt(dphi * dphi + dlam * dlam);
  return magneticBearing;
}

float check_battery() {
  // TODO: do something with this
  float measuredvbat = analogRead(VBAT_PIN);
  measuredvbat *= 2;    // we divided by 2, so multiply back
  measuredvbat *= 3.3;  // Multiply by 3.3V, our reference voltage
  measuredvbat /= 1024; // convert to voltage

  Serial.print("VBat: ");
  Serial.println(measuredvbat);

  // return 0-3; dead, low, okay, full
  return measuredvbat;
}

// compare compass points
bool firstIsBrighter(CHSV first, CHSV second) { return first.value > second.value; }

const int maxCompassPoints = numPeers + 1;
CHSV compassPoints[numLEDs][maxCompassPoints];
int nextCompassPoint[numLEDs] = {0};

void updateCompassPoints() {
  // clear past compass points
  // TODO: this isn't very efficient since it recalculates everything every time
  for (int i = 0; i < numLEDs; i++) {
    nextCompassPoint[i] = 0; // TODO: is this the right syntax?
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
    if (!compass_messages[i].saturation) {
      // skip the peer if we don't have any color data for them
      continue;
    }
    if (i == my_peer_id) {
      // don't show yourself
      continue;
    }

    float peer_distance; // meters
    float magneticBearing = course_to(compass_messages[my_peer_id].latitude, compass_messages[my_peer_id].longitude,
                                      compass_messages[i].latitude, compass_messages[i].longitude, &peer_distance);

    if (peer_distance < 10) {
      // TODO: what should we do for really close peers?
      continue;
    }

    // TODO: double check that this is looping the correct way around the LED
    // circle 0 -> 360 should go clockwise, but it looks like the lights are wired counter-clockwise
    int compassPointId = map(magneticBearing, 0, 360, numLEDs, 0);

    // convert distance to brightness. the closer, the brighter
    // TODO: scurve instead of linear?
    // TODO: tune this
    int peer_brightness = map(min(max_peer_distance, peer_distance), 0, max_peer_distance, 10, 255);

    compassPoints[compassPointId][nextCompassPoint[compassPointId]] =
        CHSV(compass_messages[i].hue, compass_messages[i].saturation, peer_brightness);
    nextCompassPoint[compassPointId]++;
  }

  /*
  // TODO: this is broken
  for (int i = 0; i < numLEDs; i++) {
    // TODO: sort every time? i feel like there is a smarter way to insert. it
  probably doesn't matter
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
      // Serial.print("No color for light #"); Serial.println(i);
      continue;
    } else {
      int j = 0;
      if (nextCompassPoint[i] > 1) {
        // there are one or more colors that want to shine on this one light. give each 500ms
        // TODO: instead give the closer peers (brighter compass points) more time?
        j = map(((elapsedMs / peer_led_time) % numPeers), 0, numPeers, 0, nextCompassPoint[i]);
      }

      // Serial.print("Displaying 1 of "); Serial.print(nextCompassPoint[i]);
      // Serial.print(" colors for light #"); Serial.println(i);

      leds[i] = compassPoints[i][j];
    }
  }
}

unsigned long now_millis() {
  if (timeStatus() != timeSet) {
    return millis();
  }

  // TODO: include some sort of offset to make sure this is in sync with remote peers
  // TODO: this wraps around, but I think thats fine because it will wrap the same for everyone
  return now() * 1000 + (gpsMs % 1000);
}

void updateLightsForHanging() {
  // do awesome patterns
  int numLightPatterns = 1; // TODO: how should this work? this seems fragile. make a list of functions instead

  // we use the actual time in ms instead of elapsedMs so that all the compasses are in near perfect sync
  // ms since 1970 divided into 1 minute chunks
  int patternId = now_millis() / msPerPattern % numLightPatterns;

  // TODO: more patterns
  switch (patternId) {
  case 0:
    pride();
    break;
  }
}

// https://gist.github.com/kriegsman
void sinelon() {
  // a colored dot sweeping back and forth, with fading trails
  fadeToBlackBy(leds, numLEDs, 28);
  int pos = beatsin16(13, 0, numLEDs);
  leds[pos] += CHSV(gHue, 255, 192);
}

// This function draws rainbows with an ever-changing, widely-varying set of parameters.
// https://gist.github.com/kriegsman/964de772d64c502760e5
void pride() {
  static uint16_t sPseudotime = 0;
  static uint16_t sLastMillis = 0;
  static uint16_t sHue16 = 0;

  uint8_t sat8 = beatsin88(87, 220, 250);
  uint8_t brightdepth = beatsin88(341, 96, 224);
  uint16_t brightnessthetainc16 = beatsin88(203, (25 * 256), (40 * 256));
  uint8_t msmultiplier = beatsin88(147, 23, 60);

  uint16_t hue16 = sHue16; // gHue * 256;
  uint16_t hueinc16 = beatsin88(113, 1, 3000);

  uint16_t ms = now_millis();
  uint16_t deltams = ms - sLastMillis;
  sLastMillis = ms;
  sPseudotime += deltams * msmultiplier;
  sHue16 += deltams * beatsin88(400, 5, 9);
  uint16_t brightnesstheta16 = sPseudotime;

  for (uint16_t i = 0; i < numLEDs; i++) {
    hue16 += hueinc16;
    uint8_t hue8 = hue16 / 256;

    brightnesstheta16 += brightnessthetainc16;
    uint16_t b16 = sin16(brightnesstheta16) + 32768;

    uint16_t bri16 = (uint32_t)((uint32_t)b16 * (uint32_t)b16) / 65536;
    uint8_t bri8 = (uint32_t)(((uint32_t)bri16) * brightdepth) / 65536;
    bri8 += (255 - brightdepth);

    CRGB newcolor = CHSV(hue8, sat8, bri8);

    uint16_t pixelnumber = i;
    pixelnumber = (numLEDs - 1) - pixelnumber;

    nblend(leds[pixelnumber], newcolor, 64);
  }
}

// non-blocking lights are a lot harder than lights using delay! good luck!
void updateLightsForLoading() {
  // TODO: what pattern? sinelon is boring
  sinelon();
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
  // update the led array every frame
  EVERY_N_MILLISECONDS(1000 / FRAMES_PER_SECOND) {
    sensorReceive();

    // TODO: check_battery and do something if it is low. maybe decrease overall brightness in a loop to make it blink
    // slowly

    // TODO: uncomment this once the sensor is hooked up update lights based on the sensor and GPS data

    if (sensorFaceDown()) {
      FastLED.clear();
    } else if (!GPS.fix) {
      updateLightsForLoading();
    } else {
      if (sensorHanging()) {
        updateLightsForHanging();
      } else {
        updateLightsForCompass();
      }
    }

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

  // cycle the "base color" through the rainbow every 3 frames
  EVERY_N_MILLISECONDS(3 * 1000 / FRAMES_PER_SECOND) { gHue++; }
}
