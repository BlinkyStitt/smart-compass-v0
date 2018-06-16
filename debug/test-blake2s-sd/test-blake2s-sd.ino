#define DEBUG
#include "debug.h"

#include <BLAKE2s.h>
#include <SD.h>
#include <SPI.h>

// Pins 0 and 1 are used for Serial1 (GPS)
#define RFM95_INT 3 // already wired for us
#define RFM95_RST 4 // already wired for us
#define LED_DATA_PIN 5
#define RFM95_CS 8 // already wired for us
#define VBAT_PIN 9 // already wired for us  // A7
#define SDCARD_CS_PIN 10
#define LSM9DS1_CSAG 11
#define LSM9DS1_CSM 12
#define RED_LED_PIN 13  // already wired for us
#define SPI_MISO_PIN 22 // shared between Radio+Sensors+SD
#define SPI_MOSI_PIN 23 // shared between Radio+Sensors+SD
#define SPI_SCK_PIN 24  // shared between Radio+Sensors+SD

#define HASH_SIZE 64
#define NETWORK_KEY_SIZE 64
uint8_t my_network_key[NETWORK_KEY_SIZE];

#define NETWORK_HASH_SIZE 4
uint8_t my_network_hash[NETWORK_HASH_SIZE];

BLAKE2s blake2s;

byte hash[HASH_SIZE];

File my_file;

bool sd_setup = false;

/* Setup */

void setup() {
  // TODO: cut this into multiple functions
  Serial.begin(19200);
  while (!Serial) {  // TODO: remove this when done debugging otherwise it won't start without the usb plugged in
    delay(1);
  }

  Serial.println("Setting up...");

  // make sure radio doesn't get in the way
  digitalWrite(RFM95_CS, HIGH);

  setupSD();
  setupSecurity();

  Serial.println("Success!");
}

/* Crypto */

void networkIdFromKey(uint8_t* network_key, uint8_t* network_hash) {
  Serial.println(F("Generating network id from key..."));

  Serial.println("resetting...");
  blake2s.reset(sizeof(network_hash));

  Serial.println("updating...");
  blake2s.update((void *)network_key, sizeof(network_key));

  Serial.println("finalizing...");
  blake2s.finalize(network_hash, sizeof(network_hash));

  Serial.println("done!");
}

void setupSecurity() {
  // TODO: open security.key and store in my_network_key

  my_file = SD.open(F("security.key"));

  Serial.print(F("Opening security.key... "));
  if (!my_file) {
    // if the file didn't open, print an error:
    Serial.println(F("failed!"));
    return;
  }
  Serial.println(F("open."));

  // read the key into a variable
  my_file.read(my_network_key, NETWORK_KEY_SIZE);

  Serial.println("my_network_key set!");

  // close the file:
  my_file.close();

  // this will override whatever they set
  // TODO: not sure about the types here..
  networkIdFromKey(my_network_key, my_network_hash);
  Serial.print(F("key-based my_network_hash: "));

  for (int i = 0; i < NETWORK_HASH_SIZE; i++) {
    Serial.print(my_network_hash[i], HEX);
    Serial.print("-");
  }
  Serial.println();

  // TODO: convert my_network_hash to my_network_int
}


/* Loop */

void loop() { }