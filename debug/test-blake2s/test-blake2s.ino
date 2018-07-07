#include <BLAKE2s.h>

#include "smart-compass.pb.h"

// Pins 0 and 1 are used for Serial1 (GPS)
#define RFM95_INT 3 // already wired for us
#define RFM95_RST 4 // already wired for us
#define LED_DATA 5
#define RFM95_CS 8 // already wired for us
#define VBAT_PIN 9 // already wired for us  // A7
#define SDCARD_CS 10
#define LSM9DS1_CSAG 11
#define LSM9DS1_CSM 12
#define RED_LED 13  // already wired for us
#define SPI_MISO 22 // shared between Radio+Sensors+SD
#define SPI_MOSI 23 // shared between Radio+Sensors+SD
#define SPI_SCK 24  // shared between Radio+Sensors+SD

#define HASH_SIZE 64

// a real app would read this from config
uint8_t my_network_key[] = "thisisatest";  // [MAX_KEY_SIZE];  // TODO: read this from the SD card

BLAKE2s blake2s;

byte hash[HASH_SIZE];

SmartCompassLocationMessage compass_message = SmartCompassLocationMessage_init_default;

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

  Serial.println("Starting...");
}

/* Crypto */

void signSmartCompassLocationMessage() {
  unsigned long start;
  unsigned long elapsed;
  start = micros();

  blake2s.reset((void *)my_network_key, sizeof(my_network_key), HASH_SIZE);

  // TODO: this seems fragile. is there a dynamic way to include all elements EXCEPT for the hash?
  blake2s.update((void *)compass_message.network_hash, sizeof(compass_message.network_hash));
  blake2s.update((void *)compass_message.tx_peer_id, sizeof(compass_message.tx_peer_id));
  blake2s.update((void *)compass_message.tx_time, sizeof(compass_message.tx_time));
  blake2s.update((void *)compass_message.tx_ms, sizeof(compass_message.tx_ms));
  blake2s.update((void *)compass_message.peer_id, sizeof(compass_message.peer_id));
  blake2s.update((void *)compass_message.last_updated_at, sizeof(compass_message.last_updated_at));
  blake2s.update((void *)compass_message.hue, sizeof(compass_message.hue));
  blake2s.update((void *)compass_message.saturation, sizeof(compass_message.saturation));
  blake2s.update((void *)compass_message.latitude, sizeof(compass_message.latitude));
  blake2s.update((void *)compass_message.longitude, sizeof(compass_message.longitude));

  blake2s.finalize(hash, HASH_SIZE);

  elapsed = micros() - start;

  Serial.print(elapsed / 1000.0);
  Serial.print("us per op, ");
  Serial.print((1000.0 * 1000000.0) / elapsed);
  Serial.println(" ops per second");
}


/* Loop */

void loop() {
  // TODO: stop using globals!
  signSmartCompassLocationMessage();
}
