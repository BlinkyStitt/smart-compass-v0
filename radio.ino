/* Radio */

// TODO: there are lots more frequencies than this. pick a good one from the sd card and use constrain()
#define RADIO_FREQ 915.0

RH_RF95 rf95(RFM95_CS, RFM95_INT);

void setupRadio() {
  DEBUG_PRINT(F("Setting up Radio... "));

  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, HIGH);

  FastLED.delay(100); // give the radio time to wake up

  resetRadio(false);

  // setModemConfig()?

  DEBUG_PRINTLN(F(" done."));
}

void resetRadio(bool with_lights) {
  DEBUG_PRINTLN("Resetting the Radio...");

  // manual reset
  digitalWrite(RFM95_RST, LOW);
  FastLED.delay(10);

  if (with_lights) {
    // TODO: set a status light?
    updateLights(1);
  }

  digitalWrite(RFM95_RST, HIGH);
  FastLED.delay(10);

  if (with_lights) {
    updateLights(2);
  }

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
  DEBUG_PRINTLN(RADIO_FREQ);

  // The default transmitter power is 13dBm, using PA_BOOST.
  rf95.setTxPower(constrain(radio_power, 5, 23), false);
}

void signSmartCompassLocationMessage(SmartCompassLocationMessage *message, uint8_t *hash) {
  /*
  unsigned long start;
  unsigned long elapsed;
  start = micros();
  */

  // TODO: is this right? first variable is &, but sizeof isn't?

  DEBUG_PRINT(F("resetting... "));
  blake2s.reset(&my_network_key, sizeof(my_network_key), NETWORK_HASH_SIZE);

  // TODO: this seems fragile. is there a dynamic way to include all elements EXCEPT for the hash?
  DEBUG_PRINT(F("updating"));
  blake2s.update(&message->network_hash, sizeof(message->network_hash));
  DEBUG_PRINT(".");
  blake2s.update(&message->tx_peer_id, sizeof(message->tx_peer_id));
  DEBUG_PRINT(".");
  blake2s.update(&message->tx_time, sizeof(message->tx_time));
  DEBUG_PRINT(".");
  blake2s.update(&message->tx_ms, sizeof(message->tx_ms));
  DEBUG_PRINT(".");
  blake2s.update(&message->peer_id, sizeof(message->peer_id));
  DEBUG_PRINT(".");
  blake2s.update(&message->last_updated_at, sizeof(message->last_updated_at));
  DEBUG_PRINT(".");
  blake2s.update(&message->hue, sizeof(message->hue));
  DEBUG_PRINT(".");
  blake2s.update(&message->saturation, sizeof(message->saturation));
  DEBUG_PRINT(".");
  blake2s.update(&message->latitude, sizeof(message->latitude));
  DEBUG_PRINT(".");
  blake2s.update(&message->longitude, sizeof(message->longitude));
  DEBUG_PRINT(".");

  // TODO: is this right? should hash have a &?
  DEBUG_PRINTLN(F(" finalizing..."));
  blake2s.finalize(hash, NETWORK_HASH_SIZE);

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

void signSmartCompassPinMessage(SmartCompassPinMessage *message, uint8_t *hash) {
  /*
  unsigned long start;
  unsigned long elapsed;
  start = micros();
  */

  // TODO: print the message here?

  DEBUG_PRINT(F("resetting... "));
  blake2s.reset(&my_network_key, sizeof(my_network_key), NETWORK_HASH_SIZE);

  // TODO: this seems fragile. is there a dynamic way to include all elements EXCEPT for the hash?
  DEBUG_PRINT(F("updating"));
  blake2s.update(&message->network_hash, sizeof(message->network_hash));
  DEBUG_PRINT(".");
  blake2s.update(&message->tx_peer_id, sizeof(message->tx_peer_id));
  DEBUG_PRINT(".");
  blake2s.update(&message->last_updated_at, sizeof(message->last_updated_at));
  DEBUG_PRINT(".");
  blake2s.update(&message->latitude, sizeof(message->latitude));
  DEBUG_PRINT(".");
  blake2s.update(&message->longitude, sizeof(message->longitude));
  DEBUG_PRINT(F("."));
  blake2s.update(&message->hue, sizeof(message->hue));
  DEBUG_PRINT(".");

  DEBUG_PRINT(F(" finalizing... "));
  blake2s.finalize(hash, NETWORK_HASH_SIZE);

  DEBUG_PRINT(F("done. "));

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
void printSmartCompassLocationMessage(SmartCompassLocationMessage *message, bool print_hash = false, bool eol = false) {
  DEBUG_PRINT(F("Message: n="));
  DEBUG_HEX8(message->network_hash, NETWORK_HASH_SIZE, false);

  if (print_hash) {
    DEBUG_PRINT(F(" h="));
    DEBUG_HEX8(message->message_hash, NETWORK_HASH_SIZE, false);
  }

  // TODO: tx_time and last_updated_at are usually going to be very close. transmit age of message instead of tx_time

  DEBUG_PRINT(F(" txp="));
  DEBUG_PRINT(message->tx_peer_id);
  DEBUG_PRINT(F(" p="));
  DEBUG_PRINT(message->peer_id);
  DEBUG_PRINT(F(" now="));
  DEBUG_PRINT(message->tx_time);
  DEBUG_PRINT(F(" ms="));
  DEBUG_PRINT(message->tx_ms);
  DEBUG_PRINT(F(" t="));
  DEBUG_PRINT(message->last_updated_at);
  DEBUG_PRINT(F(" lat="));
  DEBUG_PRINT(message->latitude);
  DEBUG_PRINT(F(" lon="));
  DEBUG_PRINT(message->longitude);

  DEBUG_PRINT(F(" EOM. "));

  if (eol) {
    DEBUG_PRINTLN();
  }
}

void printSmartCompassPinMessage(SmartCompassPinMessage *message, bool print_hash = false, bool eol = false) {
  DEBUG_PRINT(F("Message: n="));
  DEBUG_HEX8(message->network_hash, NETWORK_HASH_SIZE, false);

  if (print_hash) {
    DEBUG_PRINT(F(" h="));
    DEBUG_HEX8(message->message_hash, NETWORK_HASH_SIZE, false);
  }

  // TODO: should we include tx_time here?
  DEBUG_PRINT(F(" txp="));
  DEBUG_PRINT(message->tx_peer_id);
  DEBUG_PRINT(F(" t="));
  DEBUG_PRINT(message->last_updated_at);
  DEBUG_PRINT(F(" lat="));
  DEBUG_PRINT(message->latitude);
  DEBUG_PRINT(F(" lon="));
  DEBUG_PRINT(message->longitude);
  DEBUG_PRINT(F(" hue="));
  DEBUG_PRINT(message->hue);

  DEBUG_PRINT(F(" EOM. "));

  if (eol) {
    DEBUG_PRINTLN();
  }
}

#else
void printSmartCompassLocationMessage(SmartCompassLocationMessage *message, bool print_hash = false, bool eol = false) {}
void printSmartCompassPinMessage(SmartCompassPinMessage *message, bool print_hash = false, bool eol = false) {}
#endif

inline void radioSleep() {
  // TODO: it doesn't seem to be waking up from sleep right. transmit keeps getting stuck
  //rf95.sleep();
}

void radioTransmit(const int pid) {
  static unsigned long wait_until = 0;
  static bool reset_wait_until = true;

  // TODO: what if time_now wraps?
  static unsigned long time_now = 0;

  updateLights(3); // we update lights here because checking the time can be slow

  getGPSTime(&time_now);

  updateLights(4); // we update lights here because sending can be slow

  // if tx_compass_location is false, we transmit a pin id instead of a friend location. i don't love this pattern
  // TODO: what happens when we want to tx other things?
  bool tx_compass_location = true;
  int tx_pin_id = -1;

  // TODO: i distabled this while testing to send out a ton of transmission really fast
  if (time_now - last_transmitted[pid] < broadcast_time_s) {
    // we already transmitted for this peer recently. don't broadcast it again

    // TODO: a crash might be related to this. i'm not sure though. now i'm thinking there is probably more than one
    /*
    // check if there are any pins to transmit
    for (int i = next_compass_pin - 1; i >= 0; i--) {
      // checking against hue like this stops us from using true red (which is good since that's already used for north)
      // TODO: but then how should we broadcast that a pin should be deleted?
      if (!compass_pins[i].transmitted and compass_pins[i].database_id > 0) {
        tx_compass_location = false; // set to false to enable transmitting of compass_pins instead of friend locations
        tx_pin_id = i;
        break;
      }
    }
    */
    updateLights(5); // we update lights here because sending can be slow

    if (tx_compass_location) {
      // we don't have any queued messages and we already transmitted peer updates
      // put the radio to sleep to save power
      // TODO: this takes a finite amount of time to wake. not sure how long tho...
      radioSleep();
      updateLights(6); // we update lights here because sending can be slow
      return;
    }
  }

  if (tx_compass_location and (pid == 0)) {
    // if we are broadcasting the first peer, delay a little bit in case GPS is out of sync and a nearby peer isn't listening yet

    if (reset_wait_until) {
      // TODO: make this 10% of our transmit time?
      wait_until = millis() + 200;
      reset_wait_until = false;
      return;
    }

    if (millis() < wait_until) {
      return;
    }

    reset_wait_until = true;
  }

  // TODO: if the message is 10 minutes old or older, set message hue to 0 and return instead of transmitting

  DEBUG_PRINT(F("Time to transmit data from "));
  DEBUG_PRINT(my_peer_id);
  DEBUG_PRINT(" about ");
  DEBUG_PRINT(pid);
  DEBUG_PRINTLN("...");

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

  // TODO: lets try turning off the lights here and seeing if we can get it to crash.
  // turn off all lights
  // TODO: this is jarring to look at. instead, fade all to black? or set brightness to 10%?
  // TODO: and make sure to set the brightness back to the approriate level for the battery charge when done transmitting
  // TODO: or maybe we should instead be calling setPower
  //fill_solid(leds, num_LEDs, CRGB::Black);
  //FastLED.show();
  //TODO? FastLED.setMaxPowerInVoltsAndMilliamps(checkBatteryVoltage(), 10);

  // create a buffer for the radio
  uint8_t radio_buf[RH_RF95_MAX_MESSAGE_LEN];

  // Create a protobuf stream that will write to our buffer
  pb_ostream_t ostream = pb_ostream_from_buffer(radio_buf, sizeof(radio_buf));

  updateLights(7); // we update lights here because sending can be slow

  // TODO: i think this is wrong and this is causing a crash during send, but now that i've seen a crash just sending a bunch of As i don't know
  if (tx_compass_location) {
    encodeCompassMessage(&ostream, &compass_messages[pid], time_now);
  } else {
    encodePinMessage(&ostream, &compass_pins[tx_pin_id], time_now);
  }

  // we used to update lights here because encoding can be slow, but we want minimal time between encode and tx

  if (!ostream.bytes_written) {
    DEBUG_PRINTLN(F("Skipping transmit."));
    return;
  }

  // sending will wait for any previous send with waitPacketSent(), but we want to dither LEDs so wait now
  DEBUG_PRINT(F("Sending "));
  DEBUG_PRINT(ostream.bytes_written);
  DEBUG_PRINTLN(F(" bytes... "));

  DEBUG_PRINT(F("TX #"));
  DEBUG_PRINTLN(g_packets_sent);

  // TODO: this crashes seemingly randomly before finishing transmission. i think its a coincidence or the bug is above here
  // maybe the bug is the buffer getting stomped on somehow and the radio not liking an invalid send?
  // TODO: disabled send and it kept working for >14 minutes without crashing. bug is here
  rf95.send(radio_buf, ostream.bytes_written);

  g_packets_sent++;

  unsigned long abort_time = millis() + 250; // TODO: tune this

  while (rf95.mode() == RH_RF95_MODE_TX) {

    // TODO: we are crashing while transmitting. abort_time isn't helping this crash (but it does fix a different one!)
    // TODO: this must be a power issue involving something in updateLights. Current theory is checking the orientation breaks the radio
    updateLights(9); // we update lights here because sending can be slow

    FastLED.delay(loop_delay_ms);

     // BUG FIX! we got stuck transmitting here. i noticed because power usage stayed at +100mA
     if (millis() > abort_time) {
       DEBUG_PRINTLN(F("ERR! transmit got stuck!"));
       abort_time = 0;

       // does this work?
       resetRadio(true);
       break;
     }
   }

  if (abort_time == 0) {
    DEBUG_PRINTLN(F("Transmit ERR. "));
  } else {
    DEBUG_PRINTLN(F("Transmit done. "));
  }

  // TODO: increase led power limits after decreasing them above

  if (tx_compass_location) {
    last_transmitted[pid] = time_now;

    DEBUG_PRINTLN(F("Last transmit time updated."));
  } else {
    compass_pins[tx_pin_id].transmitted = true;

    DEBUG_PRINTLN(F("Pin marked as transmitted."));
  }

  updateLights(10);  // we update lights here because sending can be slow

  return;
}

// sign compass_message and send it to protobuf output stream
// returns the number of bytes written to the buffer
// TODO: something about this is broken but i don't know if its in the crypto or in the pb_encode
void encodeCompassMessage(pb_ostream_t *ostream, SmartCompassLocationMessage *compass_message, unsigned long time_now) {
  // TODO: checking hue like this means no-one can pick true red as their hue
  if (!compass_message->hue or (compass_message->peer_id == my_peer_id and !GPS.fix)) {
    // if we don't have any info for this peer, skip sending anything
    // if the peer is ourselves, don't broadcast unless we have a GPS fix (otherwise we would send 0, 0

    // don't retry
    last_transmitted[compass_message->peer_id] = time_now;

    DEBUG_PRINT(F("No peer data to transmit for #"));
    DEBUG_PRINTLN(compass_message->peer_id);

    // TODO: if half of the network is on, this might cause excessive sleeps, but let's test
    radioSleep();

    return;
  }

  DEBUG_PRINT(F("Encoding compass location message for #"));
  DEBUG_PRINT(compass_message->peer_id);
  DEBUG_PRINTLN(F("... "));

  compass_message->tx_time = time_now;
  compass_message->tx_ms = network_ms;

  printSmartCompassLocationMessage(compass_message, false, true);
  signSmartCompassLocationMessage(compass_message, compass_message->message_hash);

  updateLights(11); // we update lights here because encoding can be slow

  if (!pb_encode(ostream, SmartCompassLocationMessage_fields, compass_message)) {
    DEBUG_PRINTLN(F("ERROR ENCODING!"));
    return;
  }

  DEBUG_PRINTLN(F("Encoding done."));

  // second print to make sure nothing got corrupted
  printSmartCompassLocationMessage(compass_message, true, true);
}

// copy compass_pin values into pin_message_tx, sign it, and then send pin_message_tx to protobuf output stream
// returns the number of bytes written to the buffer
// TODO: something about this is broken
void encodePinMessage(pb_ostream_t *ostream, CompassPin *compass_pin, unsigned long time_now) {
  if (compass_pin->hue == 0) {
    return;
  }

  DEBUG_PRINTLN(F("Encoding compass pin..."));

  // pin_message_tx's network_hash and tx_peer_id are already setup by config.ino
  pin_message_tx.last_updated_at = compass_pin->last_updated_at;
  pin_message_tx.latitude = compass_pin->latitude;
  pin_message_tx.longitude = compass_pin->longitude;
  pin_message_tx.hue = compass_pin->hue;
  pin_message_tx.saturation = compass_pin->saturation;

  printSmartCompassPinMessage(&pin_message_tx, false, true);

  // TODO: i think this is wrong.
  signSmartCompassPinMessage(&pin_message_tx, pin_message_tx.message_hash);

  updateLights(12); // we update lights here because encoding can be slow

  if (!pb_encode(ostream, SmartCompassPinMessage_fields, &pin_message_tx)) {
    DEBUG_PRINTLN(F("ERROR ENCODING!"));
    return;
  }

  DEBUG_PRINTLN(F("Encoding done."));

  // second print to make sure nothing got corrupted
  printSmartCompassPinMessage(&pin_message_tx, true, true);
}

// TODO: return a boolean and then radioTransmit could do `if (radioReceive()) { abort tx and wait for next loop }`
// TODO: I've had it crash here!
void radioReceive() {
  if (!rf95.available()) {
    // no packets to process
    return;
  }

  uint8_t radio_buf[RH_RF95_MAX_MESSAGE_LEN];
  uint8_t radio_buf_len = RH_RF95_MAX_MESSAGE_LEN;  // start this at max length so it will read the full message

  DEBUG_PRINT(F("Receiving... "));

  // Should be a reply message for us now
  if (!rf95.recv(radio_buf, &radio_buf_len)) {
    DEBUG_PRINTLN(F("FAILED!"));
    return;
  }

  DEBUG_PRINTLN(F("DONE!"));

  DEBUG_PRINT(F("RSSI: "));
  // TODO: what is the scale for this?
  DEBUG_PRINTLN2(rf95.lastRssi(), DEC);

  updateLights(13); // we update lights here because receiving can be slow

  pb_istream_t stream = pb_istream_from_buffer(radio_buf, radio_buf_len);

  if (pb_decode(&stream, SmartCompassLocationMessage_fields, &location_message_rx)) {
    updateLights(14); // we update lights here because decoding can be slow

    receiveLocationMessage(&location_message_rx);
  } else {
    // TODO: re-enable this once other things are working
    /*
    DEBUG_PRINT(F("Decoding as location message failed: "));
    DEBUG_PRINTLN(PB_GET_ERROR(&stream));

    // TODO: only do this on a certain error type?
    // TODO: can we simply re-use the stream? do we need to reset or something?
    stream = pb_istream_from_buffer(radio_buf, radio_buf_len);
    if (pb_decode(&stream, SmartCompassPinMessage_fields, &pin_message_rx)) {
      updateLights(15); // we update lights here because decoding can be slow

       receivePinMessage(&pin_message_rx);
    } else {
      DEBUG_PRINT(F("Decoding as pin message failed: "));
      DEBUG_PRINTLN(PB_GET_ERROR(&stream));
    }

    return;
    */
  }
}

void receiveLocationMessage(SmartCompassLocationMessage *message) {
  if (memcmp(&message->network_hash, &my_network_hash, NETWORK_HASH_SIZE) != 0) {
    DEBUG_PRINT(F("Location message is for another network: "));
    DEBUG_HEX8(message->network_hash, NETWORK_HASH_SIZE, false);
    DEBUG_PRINT(F(" != "));
    DEBUG_HEX8(my_network_hash, NETWORK_HASH_SIZE, true);

    // TODO: log this to the SD? I doubt we will ever actually see this, but metrics are good, right?
    // TODO: flash lights on the status bar?
    return;
  }

  DEBUG_PRINTLN(F("Checking hash..."));
  uint8_t calculated_hash[NETWORK_HASH_SIZE];
  signSmartCompassLocationMessage(message, calculated_hash);

  if (memcmp(&calculated_hash, &message->message_hash, NETWORK_HASH_SIZE) != 0) {
    DEBUG_PRINTLN(F("Message has an invalid hash!"));
    // TODO: log this to the SD? I doubt we will ever actually see this, but security is a good idea, right?
    // TODO: flash lights on the status bar?
    return;
  }
  printSmartCompassLocationMessage(message, true, true);

  // do this check as quick as possible so that the delay checking network_ms is as small as possible
  if (message->tx_peer_id < my_peer_id) {
    // if tx_peer_id is smaller than our id, use their network_ms
    // TODO: more complicated systems could be designed for syncing network_ms, but this is quick and easy
    if (abs(message->tx_ms - network_ms) >= g_network_offset) {
      // TODO: flash lights on the status bar if there is a large difference?
      DEBUG_PRINT(F("Updating network_ms! "));
      DEBUG_PRINT(network_ms);
      DEBUG_PRINT(F(" -> "));

      // TODO: do something to tweak g_network_offset to be based on seen offset?

      network_ms = message->tx_ms + g_network_offset;

      DEBUG_PRINTLN(network_ms);
    } else {
      DEBUG_PRINT(F("Leaving network_ms alone! Times in sync "));

      DEBUG_PRINT(network_ms);
      DEBUG_PRINT(F(" !-> "));

      DEBUG_PRINT(message->tx_ms);
      DEBUG_PRINT(F(" + "));
      DEBUG_PRINTLN(g_network_offset);
    }
  } else if (message->tx_peer_id == my_peer_id) {
    // TODO: flash lights on the status bar?
    DEBUG_PRINT(F("ERROR! Peer id collision!"));
    DEBUG_PRINTLN(my_peer_id);
    return;
  } else if (message->tx_peer_id >= num_peers) {
    DEBUG_PRINT(F("ERROR! Peer num mismatch!"));
    DEBUG_PRINT(message->tx_peer_id);
    DEBUG_PRINT(F(" >= "));
    DEBUG_PRINTLN(num_peers);
    return;
  } else {
    DEBUG_PRINT(F("Leaving network_ms alone! TX peer is junior. "));
    DEBUG_PRINT(network_ms);
    DEBUG_PRINT(F(" !-> "));

    DEBUG_PRINT(message->tx_ms);
    DEBUG_PRINT(F(" + "));
    DEBUG_PRINTLN(g_network_offset);
  }

  if (message->peer_id >= num_peers) {
    DEBUG_PRINT(F("ERROR! Peer num mismatch!"));
    DEBUG_PRINT(message->peer_id);
    DEBUG_PRINT(F(" >= "));
    DEBUG_PRINTLN(num_peers);
    return;
  }


  if (message->peer_id == my_peer_id) {
    DEBUG_PRINTLN(F("Ignoring stats about myself."));
    // TODO: instead of ignoring, track how old my info is on all peers. if it is old, maybe there was some interference
    return;
  }

  if (message->last_updated_at < compass_messages[message->peer_id].last_updated_at) {
    // TODO: flash lights on the status bar?
    DEBUG_PRINTLN(F("Ignoring old message."));
    return;
  }

  // TODO: if message is older than 10 minutes, ignore it

  for (int i = message->num_pins + 1; i < next_compass_pin; i++) {
    // this peer hasn't heard some pins. re-transmit them
    // TODO: this won't work well once we have 255 pins, but I think that will be okay for now
    compass_pins[i].transmitted = false;
  }

  // TODO: do we care about saving tx times? we will change them when we re-broadcast
  // compass_messages[message->peer_id].tx_time = message->tx_time;
  // compass_messages[message->peer_id].tx_ms = message->tx_ms;

  compass_messages[message->peer_id].last_updated_at = message->last_updated_at;
  compass_messages[message->peer_id].hue = message->hue;
  compass_messages[message->peer_id].saturation = message->saturation;
  compass_messages[message->peer_id].latitude = message->latitude;
  compass_messages[message->peer_id].longitude = message->longitude;
  compass_messages[message->peer_id].num_pins = message->num_pins;

  DEBUG_PRINT(F("Saving location for peer "));
  DEBUG_PRINT(message->peer_id);
  DEBUG_PRINT(F("; last_updated_at: "));
  DEBUG_PRINT(compass_messages[message->peer_id].last_updated_at);

  DEBUG_PRINT(F("; hue: "));
  DEBUG_PRINT(compass_messages[message->peer_id].hue);
  DEBUG_PRINT(F("; saturation: "));
  DEBUG_PRINT(compass_messages[message->peer_id].saturation);
  DEBUG_PRINT(F("; latitude: "));
  DEBUG_PRINT(compass_messages[message->peer_id].latitude);
  DEBUG_PRINT(F("; longitude: "));
  DEBUG_PRINT(compass_messages[message->peer_id].longitude);
  DEBUG_PRINT(F("; num_pins: "));
  DEBUG_PRINTLN(compass_messages[message->peer_id].num_pins);

}

void receivePinMessage(SmartCompassPinMessage *message) {
  static uint8_t calculated_hash[NETWORK_HASH_SIZE];

  if (memcmp(&message->network_hash, &my_network_hash, NETWORK_HASH_SIZE) != 0) {
    DEBUG_PRINT(F("Pin message is for another network: "));
    DEBUG_HEX8(message->network_hash, NETWORK_HASH_SIZE, false);
    DEBUG_PRINT(F(" != "));
    DEBUG_HEX8(my_network_hash, NETWORK_HASH_SIZE, true);

    // TODO: log this to the SD? I doubt we will ever actually see this, but metrics are good, right?
    // TODO: flash lights on the status bar?
    return;
  }

  DEBUG_PRINTLN(F("Received message for our network. Checking signature..."));
  signSmartCompassPinMessage(message, calculated_hash);

  if (memcmp(&calculated_hash, &message->message_hash, NETWORK_HASH_SIZE) != 0) {
    DEBUG_PRINTLN(F("Message hash an invalid hash!"));
    // TODO: log this to the SD? I doubt we will ever actually see this, but security is a good idea, right?
    // TODO: flash lights on the status bar?
    return;
  }

  printSmartCompassPinMessage(message, true, true);

  if (message->tx_peer_id == my_peer_id) {
    // TODO: flash lights on the status bar?
    DEBUG_PRINT(F("ERROR! Peer id collision! "));
    DEBUG_PRINTLN(my_peer_id);
    return;
  }

  // getCompassPinId gets an existing pin id or get a new pin id and increments our pin counter
  int compass_pin_id = getCompassPinId(GPS.latitude_fixed, GPS.longitude_fixed);

  if (compass_pin_id == -1) {
    // TODO: remove this once getCompassPinId is actually implemented
    return;
  }

  if (message->last_updated_at < compass_pins[compass_pin_id].last_updated_at) {
    // TODO: flash lights on the status bar?
    DEBUG_PRINTLN(F("Heard old message-> Queuing transmission."));
    compass_pins[compass_pin_id].transmitted = false;
    return;
  }

  if (message->last_updated_at == compass_pins[compass_pin_id].last_updated_at and
      message->hue == compass_pins[compass_pin_id].hue) {
    // TODO: flash lights on the status bar?
    DEBUG_PRINTLN(F("Heard re-broadcast of existing message-> Skipping."));
    return;
  }

  compass_pins[compass_pin_id].last_updated_at = message->last_updated_at;

  compass_pins[compass_pin_id].latitude = message->latitude;
  compass_pins[compass_pin_id].longitude = message->longitude;

  if (GPS.fix) {
    compass_pins[compass_pin_id].magnetic_bearing =
        course_to(GPS.latitude_fixed, GPS.longitude_fixed, message->latitude, message->longitude,
                  &compass_pins[compass_pin_id].distance);
  } else {
    compass_pins[compass_pin_id].magnetic_bearing = 0;
    compass_pins[compass_pin_id].distance = -1;
  }

  compass_pins[compass_pin_id].hue = message->hue;
  compass_pins[compass_pin_id].saturation = message->saturation;

  // send this when it is our time to transmit
  compass_pins[compass_pin_id].transmitted = false;
}
