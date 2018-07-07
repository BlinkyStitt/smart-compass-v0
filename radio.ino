/* Radio */

// TODO: there are lots more frequencies than this. pick a good one from the sd card and use constrain()
#define RADIO_FREQ 915.0

RH_RF95 rf95(RFM95_CS, RFM95_INT);

void setupRadio() {
  DEBUG_PRINT(F("Setting up Radio... "));

  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, HIGH);

  delay(100); // give the radio time to wake up

  // manual reset
  digitalWrite(RFM95_RST, LOW);
  delay(10);
  digitalWrite(RFM95_RST, HIGH);
  delay(10);

  // Defaults after init are 434.0MHz, modulation GFSK_Rb250Fd250, 13dBm, Bw = 125 kHz, Cr = 4/5, Sf = 128chips/symbol,
  // CRC on
  if (!rf95.init()) {
    DEBUG_PRINTLN(F("failed! Cannot proceed without Radio!"));
    while (1)
      ;
  }

  // we could read this from the SD card, but I think 868 requires a license
  // TODO: figure out what frequencies we can use
  if (!rf95.setFrequency(RADIO_FREQ)) {
    DEBUG_PRINTLN(F("setFrequency failed! Cannot proceed!"));
    while (1)
      ;
  }
  DEBUG_PRINT(F("Freq: "));
  DEBUG_PRINT(RADIO_FREQ);

  // The default transmitter power is 13dBm, using PA_BOOST.
  rf95.setTxPower(constrain(radio_power, 5, 23), false);

  DEBUG_PRINTLN(F(" done."));
}

void signSmartCompassLocationMessage(SmartCompassLocationMessage message, uint8_t *hash) {
  /*
  unsigned long start;
  unsigned long elapsed;
  start = micros();
  */

  // TODO: print the message here?

  // DEBUG_PRINT(F("resetting... "));
  blake2s.reset((void *)my_network_key, sizeof(my_network_key), NETWORK_HASH_SIZE);

  // TODO: this seems fragile. is there a dynamic way to include all elements EXCEPT for the hash?
  // DEBUG_PRINT(F("updating... "));
  blake2s.update((void *)message.network_hash, sizeof(message.network_hash));
  // DEBUG_PRINT(F("."));
  blake2s.update((void *)message.tx_peer_id, sizeof(message.tx_peer_id));
  // DEBUG_PRINT(F("."));

  /*
  // TODO: something is wrong about this. it crashed here
  blake2s.update((void *)message.tx_time, sizeof(message.tx_time));
  DEBUG_PRINT(F("."));
  blake2s.update((void *)message.tx_ms, sizeof(message.tx_ms));
  DEBUG_PRINT(F("."));
  blake2s.update((void *)message.peer_id, sizeof(message.peer_id));
  DEBUG_PRINT(F("."));
  blake2s.update((void *)message.last_updated_at, sizeof(message.last_updated_at));
  DEBUG_PRINT(F("."));
  blake2s.update((void *)message.hue, sizeof(message.hue));
  DEBUG_PRINT(F("."));
  blake2s.update((void *)message.saturation, sizeof(message.saturation));
  DEBUG_PRINT(F("."));
  blake2s.update((void *)message.latitude, sizeof(message.latitude));
  DEBUG_PRINT(F("."));
  blake2s.update((void *)message.longitude, sizeof(message.longitude));
  DEBUG_PRINT(F(". "));
  */

  // DEBUG_PRINT(F("finalizing... "));
  blake2s.finalize(hash, NETWORK_HASH_SIZE);

  // DEBUG_PRINT(F("done. "));

  /*
  elapsed = micros() - start;

  DEBUG_PRINT(elapsed / 1000.0);
  DEBUG_PRINT(F("us per op, "));
  DEBUG_PRINT((1000.0 * 1000000.0) / elapsed);
  DEBUG_PRINTLN(F(" ops per second"));
  */

  DEBUG_PRINT(F("Hash: "));
  DEBUG_HEX8(hash, NETWORK_HASH_SIZE, true);
}

void signSmartCompassPinMessage(SmartCompassPinMessage message, uint8_t *hash) {
  /*
  unsigned long start;
  unsigned long elapsed;
  start = micros();
  */

  // TODO: print the message here?

  // DEBUG_PRINT(F("resetting... "));
  blake2s.reset((void *)my_network_key, sizeof(my_network_key), NETWORK_HASH_SIZE);

  // TODO: this seems fragile. is there a dynamic way to include all elements EXCEPT for the hash?
  // DEBUG_PRINT(F("updating... "));
  blake2s.update((void *)message.network_hash, sizeof(message.network_hash));
  // DEBUG_PRINT(F("."));
  blake2s.update((void *)message.tx_peer_id, sizeof(message.tx_peer_id));
  // DEBUG_PRINT(F("."));

  /*
  // TODO: something is wrong about this. it crashed here for signSmartCompassLocationMessage
  blake2s.update((void *)message.last_updated_at, sizeof(message.last_updated_at));
  DEBUG_PRINT(F("."));
  blake2s.update((void *)message.latitude, sizeof(message.latitude));
  DEBUG_PRINT(F("."));
  blake2s.update((void *)message.longitude, sizeof(message.longitude));
  DEBUG_PRINT(F(". "));
  blake2s.update((void *)message.hue, sizeof(message.hue));
  DEBUG_PRINT(F("."));
  */

  // DEBUG_PRINT(F("finalizing... "));
  blake2s.finalize(hash, NETWORK_HASH_SIZE);

  // DEBUG_PRINT(F("done. "));

  /*
  elapsed = micros() - start;

  DEBUG_PRINT(elapsed / 1000.0);
  DEBUG_PRINT(F("us per op, "));
  DEBUG_PRINT((1000.0 * 1000000.0) / elapsed);
  DEBUG_PRINTLN(F(" ops per second"));
  */

  DEBUG_PRINT(F("Hash: "));
  DEBUG_HEX8(hash, NETWORK_HASH_SIZE, true);
}

#ifdef DEBUG
void printSmartCompassLocationMessage(SmartCompassLocationMessage message, bool print_hash = false, bool eol = false) {
  DEBUG_PRINT(F("Message: n="));
  DEBUG_HEX8(message.network_hash, NETWORK_HASH_SIZE, false);

  if (print_hash) {
    DEBUG_PRINT(F(" h="));
    DEBUG_HEX8(message.message_hash, NETWORK_HASH_SIZE, false);
  }

  DEBUG_PRINT(F(" txp="));
  DEBUG_PRINT(message.tx_peer_id);
  DEBUG_PRINT(F(" p="));
  DEBUG_PRINT(message.peer_id);
  DEBUG_PRINT(F(" now="));
  DEBUG_PRINT(message.tx_time);
  DEBUG_PRINT(F(" ms="));
  DEBUG_PRINT(message.tx_ms);
  DEBUG_PRINT(F(" t="));
  DEBUG_PRINT(message.last_updated_at);
  DEBUG_PRINT(F(" lat="));
  DEBUG_PRINT(message.latitude);
  DEBUG_PRINT(F(" lon="));
  DEBUG_PRINT(message.longitude);

  DEBUG_PRINT(F(" EOM. "));

  if (eol) {
    DEBUG_PRINTLN();
  }
}

void printSmartCompassPinMessage(SmartCompassPinMessage message, bool print_hash = false, bool eol = false) {
  DEBUG_PRINT(F("Message: n="));
  DEBUG_HEX8(message.network_hash, NETWORK_HASH_SIZE, false);

  if (print_hash) {
    DEBUG_PRINT(F(" h="));
    DEBUG_HEX8(message.message_hash, NETWORK_HASH_SIZE, false);
  }

  DEBUG_PRINT(F(" txp="));
  DEBUG_PRINT(message.tx_peer_id);
  DEBUG_PRINT(F(" t="));
  DEBUG_PRINT(message.last_updated_at);
  DEBUG_PRINT(F(" lat="));
  DEBUG_PRINT(message.latitude);
  DEBUG_PRINT(F(" lon="));
  DEBUG_PRINT(message.longitude);
  DEBUG_PRINT(F(" hue="));
  DEBUG_PRINT(message.hue);

  DEBUG_PRINT(F(" EOM. "));

  if (eol) {
    DEBUG_PRINTLN();
  }
}

#else
void printSmartCompassLocationMessage(SmartCompassLocationMessage message, bool print_hash = false, bool eol = false) {}
void printSmartCompassPinMessage(SmartCompassPinMessage message, bool print_hash = false, bool eol = false) {}
#endif

void radioTransmit(const int pid) {
  static uint8_t radio_buf[RH_RF95_MAX_MESSAGE_LEN];

  updateLights(); // we update lights here because checking the time can be slow

  unsigned long time_now = getGPSTime();

  updateLights(); // we update lights here because sending can be slow

  // TODO: tie this 2 second limit to update interval
  // TODO: what if time_now wraps?
  bool tx_compass_location =
      true; // if this is false, we transmit a pin id instead of a friend location. i don't love this pattern
  int tx_pin_id = -1;
  // TODO: don't hard code 2. calculate based on peer update time
  if (time_now - last_transmitted[pid] < 2) {
    // we already transmitted for this peer recently. don't broadcast it again

    // check if there are any pins to transmit
    for (int i = next_compass_pin - 1; i >= 0; i--) {
      // checking against hue like this stops us from using true red (which is good since that's already used for north)
      if (!compass_pins[i].transmitted and compass_pins[i].color.hue) {
        tx_compass_location = false; // set to false to enable transmitting of compass_pins instead of friend locations
        tx_pin_id = i;
        break;
      }
    }

    updateLights(); // we update lights here because sending can be slow

    if (tx_compass_location) {
      // we don't have any queued messages and we already transmitted peer updates
      // put the radio to sleep to save power
      // TODO: this takes a finite amount of time to wake. not sure how long tho...
      rf95.sleep();
      updateLights(); // we update lights here because sending can be slow
      return;
    }
  }

  DEBUG_PRINTLN(F("My time to transmit..."));

  /*
  // TODO: this is causing it to hang. does my module not have this? do I need to configure another pin?
  // http://www.airspayce.com/mikem/arduino/RadioHead/classRHGenericDriver.html#ac577b932ba8b042b8170b24d513635c7
  if (rf95.isChannelActive()) {
    DEBUG_PRINTLN("Channel is active. Delaying transmission");
    // TODO: exponential backoff? how long? FastLED's random?
    // TODO: how long should we wait? the upstream method waits 100-1000ms
    wait_for_congestion = time_now + random(100, 500);
    return;
  }
  */

  if (rf95.available()) {
    DEBUG_PRINTLN(F("Missed a peer message! Parsing before transmitting."));
    radioReceive();
    // TODO: do something with the lights? could be cool to add a circle in my_hue to whatever pattern is currently
    // playing
    return; // we will try broadcasting next loop
  }

  // Create a protobuf stream that will write to our buffer
  pb_ostream_t ostream = pb_ostream_from_buffer(radio_buf, sizeof(radio_buf));

  updateLights(); // we update lights here because sending can be slow

  if (tx_compass_location) {
    encodeCompassMessage(&ostream, compass_messages[pid], time_now);
  } else {
    encodePinMessage(&ostream, compass_pins[tx_pin_id], time_now);
  }

  // TODO: bytes_written seems to always be 0, even with a successful encode
  if (!ostream.bytes_written) {
    DEBUG_PRINTLN("Skipping transmit.");
    return;
  }

  updateLights(); // we update lights here because encoding can be slow

  // sending will wait for any previous send with waitPacketSent(), but we want to dither LEDs so wait now
  // TODO: time it (tho it seems fast enough)
  DEBUG_PRINT(F("Sending "));
  DEBUG_PRINT(ostream.bytes_written);
  DEBUG_PRINTLN(F(" bytes... "));
  rf95.send(radio_buf, ostream.bytes_written);
  while (rf95.mode() == RH_RF95_MODE_TX) {
    updateLights(); // we update lights here because sending can be slow
    FastLED.delay(loop_delay_ms);
  }

  // TODO: it is sometimes crashing here or inside the above while loop :'(

  DEBUG_PRINT(F("Transmit done. "));

  if (tx_compass_location) {
    last_transmitted[pid] = time_now;
  } else {
    compass_pins[tx_pin_id].transmitted = true;
  }

  DEBUG_PRINTLN(F("Time updated."));

  updateLights(); // we update lights here because sending can be slow

  return;
}

// sign compass_message and send it to protobuf output stream
// returns the number of bytes written to the buffer
// TODO: should compass_message be passed by reference, too?
void encodeCompassMessage(pb_ostream_t *ostream, SmartCompassLocationMessage compass_message, unsigned long time_now) {
  // TODO: checking hue like this means no-one can pick true red as their hue
  if (!compass_message.hue or (compass_message.peer_id == my_peer_id and !GPS.fix)) {
    // if we don't have any info for this peer, skip sending anything
    // if the peer is ourselves, don't broadcast unless we have a GPS fix (otherwise we would send 0, 0

    // don't retry
    last_transmitted[compass_message.peer_id] = time_now;

    DEBUG_PRINT(F("No peer data to transmit for #"));
    DEBUG_PRINTLN(compass_message.peer_id);

    return;
  }

  DEBUG_PRINT(F("Encoding compass location message for #"));
  DEBUG_PRINT(compass_message.peer_id);
  DEBUG_PRINTLN(F("... "));

  compass_message.tx_time = time_now;
  compass_message.tx_ms = network_ms;

  printSmartCompassLocationMessage(compass_message, false, true);
  signSmartCompassLocationMessage(compass_message, compass_message.message_hash);

  updateLights(); // we update lights here because encoding can be slow

  if (!pb_encode(ostream, SmartCompassLocationMessage_fields, &compass_message)) {
    DEBUG_PRINTLN(F("ERROR ENCODING!"));
    return;
  }

  DEBUG_PRINTLN(F("Encoding done."));
}

// copy compass_pin values into pin_message_tx, sign it, and then send pin_message_tx to protobuf output stream
// returns the number of bytes written to the buffer
// TODO: should compass_pin be passed by reference, too?
void encodePinMessage(pb_ostream_t *ostream, CompassPin compass_pin, unsigned long time_now) {
  if (compass_pin.color.hue == 0) {
    return;
  }

  DEBUG_PRINTLN(F("Encoding compass pin..."));

  // pin_message_tx's network_hash and tx_peer_id are already setup by config.ino
  pin_message_tx.last_updated_at = compass_pin.last_updated_at;
  pin_message_tx.latitude = compass_pin.latitude;
  pin_message_tx.longitude = compass_pin.longitude;
  pin_message_tx.hue = compass_pin.color.hue;
  pin_message_tx.saturation = compass_pin.color.saturation;

  printSmartCompassPinMessage(pin_message_tx, false, true);
  signSmartCompassPinMessage(pin_message_tx, pin_message_tx.message_hash);

  updateLights(); // we update lights here because encoding can be slow

  if (!pb_encode(ostream, SmartCompassPinMessage_fields, &pin_message_tx)) {
    DEBUG_PRINTLN(F("ERROR ENCODING!"));
    return;
  }

  DEBUG_PRINTLN(F("Encoding done."));
}

void radioReceive() {
  // TODO: call updatelights somewhere in here if it takes too long
  static uint8_t radio_buf[RH_RF95_MAX_MESSAGE_LEN];
  static uint8_t radio_buf_len;
  static SmartCompassLocationMessage location_message_rx = SmartCompassLocationMessage_init_default;
  static SmartCompassPinMessage pin_message_rx = SmartCompassPinMessage_init_default;

  if (!rf95.available()) {
    // no packets to process
    return;
  }

  radio_buf_len = RH_RF95_MAX_MESSAGE_LEN; // reset this to max length otherwise it won't receive the full message!

  // Should be a reply message for us now
  if (!rf95.recv(radio_buf, &radio_buf_len)) {
    DEBUG_PRINTLN(F("Receive failed"));
    return;
  }

  updateLights(); // we update lights here because receiving can be slow

  DEBUG_PRINT(F("RSSI: "));
  DEBUG_PRINTLN2(rf95.lastRssi(), DEC);

  pb_istream_t stream = pb_istream_from_buffer(radio_buf, radio_buf_len);

  if (pb_decode(&stream, SmartCompassLocationMessage_fields, &location_message_rx)) {
    updateLights(); // we update lights here because decoding can be slow

    receiveLocationMessage(location_message_rx);
    return;
  } else {
    DEBUG_PRINT(F("Decoding as location message failed: "));
    DEBUG_PRINTLN(PB_GET_ERROR(&stream));

    // TODO: only do this on a certain error type?
    // TODO: can we simply re-use the stream? do we need to reset or something?
    stream = pb_istream_from_buffer(radio_buf, radio_buf_len);
    if (pb_decode(&stream, SmartCompassPinMessage_fields, &pin_message_rx)) {
      updateLights(); // we update lights here because decoding can be slow

      receivePinMessage(pin_message_rx); // TODO: write this
    } else {
      DEBUG_PRINT(F("Decoding as pin message failed: "));
      DEBUG_PRINTLN(PB_GET_ERROR(&stream));
    }

    return;
  }
}

void receiveLocationMessage(SmartCompassLocationMessage message) {
  static uint8_t calculated_hash[NETWORK_HASH_SIZE];

  if (memcmp(message.network_hash, my_network_hash, NETWORK_HASH_SIZE) != 0) {
    DEBUG_PRINTLN(F("Message is for another network."));
    // TODO: log this to the SD? I doubt we will ever actually see this, but metrics are good, right?
    // TODO: flash lights on the status bar?
    return;
  }

  signSmartCompassLocationMessage(message, calculated_hash);
  if (memcmp(calculated_hash, message.message_hash, NETWORK_HASH_SIZE) != 0) {
    DEBUG_PRINTLN(F("Message hash an invalid hash!"));
    // TODO: log this to the SD? I doubt we will ever actually see this, but security is a good idea, right?
    // TODO: flash lights on the status bar?
    return;
  }

  printSmartCompassLocationMessage(message, true, true);

  if (message.tx_peer_id == my_peer_id) {
    // TODO: flash lights on the status bar?
    DEBUG_PRINT(F("ERROR! Peer id collision!"));
    DEBUG_PRINTLN(my_peer_id);
    return;
  }

  if (message.peer_id == my_peer_id) {
    DEBUG_PRINTLN(F("Ignoring stats about myself."));
    // TODO: instead of ignoring, track how old my info is on all peers. if it is old, maybe there was some interference
    return;
  }

  if (message.last_updated_at < compass_messages[message.peer_id].last_updated_at) {
    // TODO: flash lights on the status bar?
    DEBUG_PRINTLN(F("Ignoring old message."));
    return;
  }

  /*
  // sync to the lowest peer id's time
  // TODO: make this work. somehow time got set to way in the future
  // TODO: only do this if there is drift?
  // TODO: make sure this works well for all cases
  //if (message.peer_id < my_peer_id) {
  if (timeStatus() == timeNotSet) {
    setTime(0, 0, 0, 0, 0, 0);
    adjustTime(message.tx_time);
  }
  */

  // TODO: simply accepting the lower peer's time seems like it could have issues, but how much would that really
  // matter?
  if (message.peer_id < my_peer_id) {
    // TODO: flash lights on the status bar if there is a large difference?
    DEBUG_PRINT(F("Updating network_ms! "));
    DEBUG_PRINT(network_ms);
    DEBUG_PRINT(F(" -> "));
    network_ms = message.tx_ms + 74; // TODO: tune this offset. probably save it as a global and set from config
  } else {
    DEBUG_PRINT(F("Leaving network_ms alone! "));
  }
  DEBUG_PRINTLN(network_ms);

  for (int i = message.num_pins + 1; i < next_compass_pin; i++) {
    // this peer hasn't heard some pins. re-transmit them
    // TODO: this won't work well once we have 255 pins, but I think that will be okay for now
    compass_pins[i].transmitted = false;
  }

  // TODO: do we care about saving tx times? we will change them when we re-broadcast
  // compass_messages[message.peer_id].tx_time = message.tx_time;
  // compass_messages[message.peer_id].tx_ms = message.tx_ms;

  compass_messages[message.peer_id].last_updated_at = message.last_updated_at;
  compass_messages[message.peer_id].hue = message.hue;
  compass_messages[message.peer_id].saturation = message.saturation;
  compass_messages[message.peer_id].latitude = message.latitude;
  compass_messages[message.peer_id].longitude = message.longitude;
  compass_messages[message.peer_id].num_pins = message.num_pins;
}

void receivePinMessage(SmartCompassPinMessage message) {
  static uint8_t calculated_hash[NETWORK_HASH_SIZE];

  if (memcmp(message.network_hash, my_network_hash, NETWORK_HASH_SIZE) != 0) {
    DEBUG_PRINTLN(F("Message is for another network."));
    // TODO: log this to the SD? I doubt we will ever actually see this, but metrics are good, right?
    // TODO: flash lights on the status bar?
    return;
  }

  signSmartCompassPinMessage(message, calculated_hash);
  if (memcmp(calculated_hash, message.message_hash, NETWORK_HASH_SIZE) != 0) {
    DEBUG_PRINTLN(F("Message hash an invalid hash!"));
    // TODO: log this to the SD? I doubt we will ever actually see this, but security is a good idea, right?
    // TODO: flash lights on the status bar?
    return;
  }

  printSmartCompassPinMessage(message, true, true);

  if (message.tx_peer_id == my_peer_id) {
    // TODO: flash lights on the status bar?
    DEBUG_PRINT(F("ERROR! Peer id collision! "));
    DEBUG_PRINTLN(my_peer_id);
    return;
  }

  // getCompassPinId gets an existing pin id or get a new pin id and increments our pin counter
  int compass_pin_id = getCompassPinId(GPS.latitude_fixed, GPS.longitude_fixed);

  if (message.last_updated_at < compass_pins[compass_pin_id].last_updated_at) {
    // TODO: flash lights on the status bar?
    DEBUG_PRINTLN(F("Heard old message. Queuing transmission."));
    compass_pins[compass_pin_id].transmitted = false;
    return;
  }

  if (message.last_updated_at == compass_pins[compass_pin_id].last_updated_at and
      message.hue == compass_pins[compass_pin_id].color.hue) {
    // TODO: flash lights on the status bar?
    DEBUG_PRINTLN(F("Heard re-broadcast of existing message."));
    return;
  }

  compass_pins[compass_pin_id].last_updated_at = message.last_updated_at;

  compass_pins[compass_pin_id].latitude = message.latitude;
  compass_pins[compass_pin_id].longitude = message.longitude;

  if (GPS.fix) {
    compass_pins[compass_pin_id].magnetic_bearing =
        course_to(GPS.latitude_fixed, GPS.longitude_fixed, message.latitude, message.longitude,
                  &compass_pins[compass_pin_id].distance);
  } else {
    compass_pins[compass_pin_id].magnetic_bearing = 0;
    compass_pins[compass_pin_id].distance = -1;
  }

  compass_pins[compass_pin_id].color.hue = message.hue;
  compass_pins[compass_pin_id].color.saturation = message.saturation;

  // send this when it is our time to transmit
  compass_pins[compass_pin_id].transmitted = false;
}
