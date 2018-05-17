#include <Adafruit_GPS.h>
#include <elapsedMillis.h>
#include <FastLED.h>
#include <RH_RF95.h>
#include <SoftwareSerial.h>
#include <SPI.h>

// todo: read this from sd?
#define RF95_FREQ 915.0  // or 868
#define RF95_POWER 23

#define VBATPIN A9

/* for feather m0
#define RFM95_CS 8
#define RFM95_RST 4
#define RFM95_INT 3
*/

/* Feather m0 w/wing */
#define RFM95_RST     11   // "A"
#define RFM95_CS      10   // "B"
#define RFM95_INT     6    // "D"

// Singleton instance of the radio driver
RH_RF95 rf95(RFM95_CS, RFM95_INT);

// TODO: what Serial are we actually using? I think Serial1 might be connected to the
#define gpsSerial Serial1
Adafruit_GPS GPS(&gpsSerial);

Adafruit_LSM9DS1 lsm = Adafruit_LSM9DS1();  // i2c sensor  // TODO: do we have these pins available? if not hardware and software spi are available

void setupSD() {
}

// Interrupt is called once a millisecond, looks for any new GPS data, and stores it. then looks for any
SIGNAL(TIMER0_COMPA_vect) {
  // if you want to debug, this is a good time to do it!
  // TODO: how does this work? where does this go?
  char c = GPS.read();

  lsm.getEvent(&accel, &mag, &gyro, &temp);
}

void setupGPS() {
  // 9600 NMEA is the default baud rate for Adafruit MTK GPS's- some use 4800
  GPS.begin(9600);
  gpsSerial.begin(9600);

  // uncomment this line to turn on RMC (recommended minimum) and GGA (fix data) including altitude
  GPS.sendCommand(PMTK_SET_NMEA_OUTPUT_RMCGGA);
  // uncomment this line to turn on only the "minimum recommended" data
  //GPS.sendCommand(PMTK_SET_NMEA_OUTPUT_RMCONLY);
  // For parsing data, we don't suggest using anything but either RMC only or RMC+GGA since
  // the parser doesn't care about other sentences at this time

  // Set the update rate
  GPS.sendCommand(PMTK_SET_NMEA_UPDATE_1HZ);   // 1 Hz update rate
  // For the parsing code to work nicely and have time to sort thru the data, and
  // print it out we don't suggest using anything higher than 1 Hz

  // Request updates on antenna status, comment out to keep quiet
  GPS.sendCommand(PGCMD_ANTENNA);

  // Ask for firmware version
  gpsSerial.println(PMTK_Q_RELEASE);
}

void setupRadio() {
  // TODO: i think there is a PULLUP option here
  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, HIGH);

  // manual reset
  digitalWrite(RFM95_RST, LOW);
  delay(10);
  digitalWrite(RFM95_RST, HIGH);
  delay(10);

  // Defaults after init are 434.0MHz, modulation GFSK_Rb250Fd250, +13dbM
  if (!rf95.setFrequency(RF95_FREQ)) {
    Serial.println("setFrequency failed");
    while (1);
  }
  // TODO: read from the SD card
  Serial.print("Set Freq to: "); Serial.println(RF95_FREQ);

  // Defaults after init are 434.0MHz, 13dBm, Bw = 125 kHz, Cr = 4/5, Sf = 128chips/symbol, CRC on

  // The default transmitter power is 13dBm, using PA_BOOST.
  // If you are using RFM95/96/97/98 modules which uses the PA_BOOST transmitter pin, then
  // you can set transmitter powers from 5 to 23 dBm:
  // TODO: read from the SD card
  rf95.setTxPower(RF95_POWER, false);
}

sensors_event_t accel, mag, gyro, temp;

void setupOrientation() {

  if(!lsm.begin()) {
    /* There was a problem detecting the LSM9DS1 ... check your connections */
    Serial.print(F("Ooops, no LSM9DS1 detected ... Check your wiring!"));
    while(1);
  }

  // 1.) Set the accelerometer range
  lsm.setupAccel(lsm.LSM9DS1_ACCELRANGE_2G);
  //lsm.setupAccel(lsm.LSM9DS1_ACCELRANGE_4G);
  //lsm.setupAccel(lsm.LSM9DS1_ACCELRANGE_8G);
  //lsm.setupAccel(lsm.LSM9DS1_ACCELRANGE_16G);

  // 2.) Set the magnetometer sensitivity
  lsm.setupMag(lsm.LSM9DS1_MAGGAIN_4GAUSS);
  //lsm.setupMag(lsm.LSM9DS1_MAGGAIN_8GAUSS);
  //lsm.setupMag(lsm.LSM9DS1_MAGGAIN_12GAUSS);
  //lsm.setupMag(lsm.LSM9DS1_MAGGAIN_16GAUSS);

  // 3.) Setup the gyroscope
  lsm.setupGyro(lsm.LSM9DS1_GYROSCALE_245DPS);
  //lsm.setupGyro(lsm.LSM9DS1_GYROSCALE_500DPS);
  //lsm.setupGyro(lsm.LSM9DS1_GYROSCALE_2000DPS);
}

void setupLights() {
  // TODO: do things with FastLED here
}

void setup() {
  Serial.begin(115200);
  while (!Serial) {  // TODO: remove this when done debugging otherwise it won't start without the usb plugged in
    delay(1);
  }

  setupSD();
  setupGPS();
  setupRadio();
  setupOrientation();
  setupLights();

  /* setup interrupts */
  // the nice thing about this code is you can have a timer0 interrupt go off
  // every 1 millisecond, and read data from the GPS for you. that makes the
  // loop code a heck of a lot easier!
  // Timer0 is already used for millis() - we'll just interrupt somewhere
  // in the middle and call the "Compare A" function above
  // TODO: what does this mean? do we really need it done every ms?
  OCR0A = 0xAF;
  TIMSK0 |= _BV(OCIE0A);

}

uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];  // keep this off the stack
uint8_t len = sizeof(buf);  // 251

void loop() {
  gpsReceive();

  // TODO: if its our time to transmit, radioTransmit(), else wait for radioReceive()

  // TODO: check_battery and blink if low

  // TODO: update_leds();  (which will check orientation)

  // using FastLED's delay allows for dithering
  FastLED.delay(10);
}

// TODO: variables for storing GPS lat/long

void radioTransmit() {
  // TODO: if no local gps data, return here

  Serial.println("Transmitting..."); // Send a message to other smart compasses in the mesh

  // TODO: send GPS data (max length is RH_RF95_MAX_MESSAGE_LEN = 251)
  // TODO: what format should our message have? $NETWORK_ID $BROADCASTER_RGB_COLOR $BROADCASTER_TIME $BROADCASTER_LAT $BROADCASTER_LONG $NODE_N_RGB_COLOR $NODE_N_TIME_DIFF $NODE_N_LAT_DIFF $NODE_N_LONG_DIFF
  char radiopacket[20] = "Hello World        ";
  Serial.print("Sending "); Serial.println(radiopacket);
  radiopacket[19] = 0;  // TODO: what is this for? is this how messages end?

  Serial.println("Sending...");
  FastLED.delay(10);  // TODO: get rid of this delay when the above prints are gone
  rf95.send((uint8_t *)radiopacket, 20);

  Serial.println("Waiting for packet to complete...");
  FastLED.delay(10);
  rf95.waitPacketSent();  // TODO: this might get in the way. maybe right something that waits with FastLED.delay?
}

void radioReceive() {
  Serial.println("Checking for reply...");
  if (rf95.available()) {
    // Should be a reply message for us now
    if (rf95.recv(buf, &len)) {
      // TODO: check and make sure this message is actually for us
      Serial.print("Got reply: ");
      Serial.println((char*)buf);
      Serial.print("RSSI: ");
      Serial.println(rf95.lastRssi(), DEC);
    } else {
      Serial.println("Receive failed");
    }
  }
}

void gpsReceive() {
  // if no new sentence is received...
  if (!GPS.newNMEAreceived()) {
    // exit
    return;
  }

  // we have a new sentence! we can check the checksum, parse it...
  // a tricky thing here is if we print the NMEA sentence, or data
  // we end up not listening and catching other sentences!
  // so be very wary if using OUTPUT_ALLDATA and trying to print out data
  //Serial.println(GPS.lastNMEA());   // this also sets the newNMEAreceived() flag to false

  if (!GPS.parse(GPS.lastNMEA()))   // this also sets the newNMEAreceived() flag to false
    return;  // we can fail to parse a sentence in which case we should just wait for another
  }

  // TODO: rewrite everything under here to instead update our internal state and log to SD

  // if millis() or timer wraps around, we'll just reset it
  if (timer > millis())  timer = millis();

  // approximately every 2 seconds or so, print out the current stats
  if (millis() - timer > 2000) {
    timer = millis(); // reset the timer

    Serial.print("\nTime: ");
    Serial.print(GPS.hour, DEC); Serial.print(':');
    Serial.print(GPS.minute, DEC); Serial.print(':');
    Serial.print(GPS.seconds, DEC); Serial.print('.');
    Serial.println(GPS.milliseconds);
    Serial.print("Date: ");
    Serial.print(GPS.day, DEC); Serial.print('/');
    Serial.print(GPS.month, DEC); Serial.print("/20");
    Serial.println(GPS.year, DEC);
    Serial.print("Fix: "); Serial.print((int)GPS.fix);
    Serial.print(" quality: "); Serial.println((int)GPS.fixquality);
    if (GPS.fix) {
      Serial.print("Location: ");
      Serial.print(GPS.latitude, 4); Serial.print(GPS.lat);
      Serial.print(", ");
      Serial.print(GPS.longitude, 4); Serial.println(GPS.lon);

      Serial.print("Speed (knots): "); Serial.println(GPS.speed);
      Serial.print("Angle: "); Serial.println(GPS.angle);
      Serial.print("Altitude: "); Serial.println(GPS.altitude);
      Serial.print("Satellites: "); Serial.println((int)GPS.satellites);
    }

    // TODO: save to SD card
  }
}

float check_battery() {
    float measuredvbat = analogRead(VBATPIN);
    measuredvbat *= 2;    // we divided by 2, so multiply back
    measuredvbat *= 3.3;  // Multiply by 3.3V, our reference voltage
    measuredvbat /= 1024; // convert to voltage
    Serial.print("VBat: " ); Serial.println(measuredvbat);

    return measuredvbat;
}
