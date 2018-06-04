/* Radio */

#define RADIO_FREQ 915.0

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

  // Defaults after init are 434.0MHz, modulation GFSK_Rb250Fd250, 13dBm, Bw = 125 kHz, Cr = 4/5, Sf = 128chips/symbol,
  // CRC on
  if (!rf95.init()) {
    Serial.println("failed! Cannot proceed without Radio!");
    while (1)
      ;
  }

  // we could read this from the SD card, but I think 868 requires a license
  if (!rf95.setFrequency(RADIO_FREQ)) {
    Serial.println("setFrequency failed! Cannot proceed!");
    while (1)
      ;
  }
  Serial.print("Freq: ");
  Serial.print(RADIO_FREQ);

  // The default transmitter power is 13dBm, using PA_BOOST.
  rf95.setTxPower(radio_power, false);

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
    Serial.print("No peer data to transmit for #");
    Serial.println(pid);
    return;
  }

  // TODO: what to do if the message is really old?

  Serial.print("Message: ");

  Serial.print("n=");
  Serial.print(compass_messages[pid].network_id);

  Serial.print(" txp=");
  Serial.print(compass_messages[pid].tx_peer_id);

  Serial.print(" p=");
  Serial.print(compass_messages[pid].peer_id);

  unsigned long time_now = now();
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
  pb_ostream_t stream = pb_ostream_from_buffer(radio_buf, sizeof(radio_buf));
  // TODO: max size (SmartCompassMessage_size) is only 64 bytes. we could combine 3 of them into one packet

  if (!pb_encode(&stream, SmartCompassMessage_fields, &compass_messages[pid])) {
    Serial.println("ERROR ENCODING!");
    return;
  }

  // sending will wait for any previous send with waitPacketSent(), but we want to dither LEDs
  Serial.print("sending... ");
  rf95.send((uint8_t *)radio_buf, stream.bytes_written);
  while (rf95.mode() == RH_RF95_MODE_TX) {
    FastLED.delay(2);
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

      /*
      if (timeStatus() != timeSet) {
        // TODO: set time from peer's time? except they use an overflowed ms count
      }
      */
    } else {
      Serial.println("Receive failed");
    }
  }
}
