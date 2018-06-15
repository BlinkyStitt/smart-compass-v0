/* Config */

#ifdef DEBUG
  // from https://github.com/stevemarple/IniFile/blob/master/examples/IniFileExample/IniFileExample.ino
  void printErrorMessage(uint8_t e, bool eol = true) {
    DEBUG_PRINT(F("Config Error: "));

    switch (e) {
    case IniFile::errorNoError:
      DEBUG_PRINT(F("no error"));
      break;
    case IniFile::errorFileNotFound:
      DEBUG_PRINT(F("file not found"));
      break;
    case IniFile::errorFileNotOpen:
      DEBUG_PRINT(F("file not open"));
      break;
    case IniFile::errorBufferTooSmall:
      DEBUG_PRINT(F("buffer too small"));
      break;
    case IniFile::errorSeekError:
      DEBUG_PRINT(F("seek error"));
      break;
    case IniFile::errorSectionNotFound:
      DEBUG_PRINT(F("section not found"));
      break;
    case IniFile::errorKeyNotFound:
      DEBUG_PRINT(F("key not found"));
      break;
    case IniFile::errorEndOfFile:
      DEBUG_PRINT(F("end of file"));
      break;
    case IniFile::errorUnknownError:
      DEBUG_PRINT(F("unknown error"));
      break;
    default:
      DEBUG_PRINT(F("unknown error value"));
      break;
    }
    if (eol) {
      DEBUG_PRINTLN();
    }
  }
#else
  void printErrorMessage(uint8_t e, bool eol = true) {}
#endif

bool loadRequired(IniFile ini, char* buffer, size_t buffer_len) {
  // load required args
  if (ini.getValue("global", "num_peers", buffer, buffer_len, num_peers)) {
    DEBUG_PRINT(F("num_peers: "));
    DEBUG_PRINTLN(buffer);
  } else {
    DEBUG_PRINT(F("Could not read 'num_peers' from section 'global', error was "));
    printErrorMessage(ini.getError());
    return false;
  }

  if (ini.getValue("global", "my_network_id", buffer, buffer_len, my_network_id)) {
    DEBUG_PRINT(F("my_network_id: "));
    DEBUG_PRINTLN(buffer);
  } else {
    DEBUG_PRINT(F("Could not read 'my_network_id' from section 'global', error was "));
    printErrorMessage(ini.getError());
    return false;
  }

  if (ini.getValue("global", "my_peer_id", buffer, buffer_len, my_peer_id)) {
    DEBUG_PRINT(F("my_peer_id: "));
    DEBUG_PRINTLN(buffer);
  } else {
    DEBUG_PRINT(F("Could not read 'my_peer_id' from section 'global', error was "));
    printErrorMessage(ini.getError());
    return false;
  }

  if (ini.getValue("global", "my_hue", buffer, buffer_len, my_hue)) {
    DEBUG_PRINT(F("my_hue: "));
    DEBUG_PRINTLN(buffer);
  } else {
    DEBUG_PRINT(F("Could not read 'my_hue' from section 'global', error was "));
    printErrorMessage(ini.getError());
    return false;
  }

  if (ini.getValue("global", "my_saturation", buffer, buffer_len, my_saturation)) {
    DEBUG_PRINT(F("my_saturation: "));
    DEBUG_PRINTLN(buffer);
  } else {
    DEBUG_PRINT(F("Could not read 'my_saturation' from section 'global', error was "));
    printErrorMessage(ini.getError());
    return false;
  }

  return true;
}

void loadOptional(IniFile ini, char* buffer, size_t buffer_len) {
  // load args that have defaults
  // TODO: gps_interval_s?
  ini.getValue("global", "broadcast_time_s", buffer, buffer_len, broadcast_time_s);
  ini.getValue("global", "default_brightness", buffer, buffer_len, default_brightness);
  ini.getValue("global", "frames_per_second", buffer, buffer_len, frames_per_second);
  ini.getValue("global", "max_peer_distance", buffer, buffer_len, max_peer_distance);
  ini.getValue("global", "ms_per_light_pattern", buffer, buffer_len, ms_per_light_pattern);
  ini.getValue("global", "peer_led_ms", buffer, buffer_len, peer_led_ms);
  ini.getValue("global", "radio_power", buffer, buffer_len, radio_power);
  ini.getValue("global", "time_zone_offset", buffer, buffer_len, time_zone_offset);
  ini.getValue("global", "flashlight_density", buffer, buffer_len, flashlight_density);
}

void setupConfig() {
  const size_t buffer_len = 80;
  char buffer[buffer_len];

  const char *filename = "/config.ini";

  // create this even if sd isn't setup so that the if/else below is simpler
  IniFile ini(filename);

  if (!sd_setup) {
    DEBUG_PRINTLN(F("SD not setup. Skipping dynamic config!"));
  } else {
    DEBUG_PRINTLN(F("Loading config... "));

    if (!ini.open()) {
      DEBUG_PRINTLN(F(" does not exist. Cannot proceed with config!"));
    } else {
      if (!ini.validate(buffer, buffer_len)) {
        // TODO: default to just pretty lights since we don't have a network id or home locations
        DEBUG_PRINT(ini.getFilename());
        DEBUG_PRINT(F(" not valid. Cannot proceed with config!"));
        printErrorMessage(ini.getError());
      } else {
        if (loadRequired(ini, buffer, buffer_len)) {
          loadOptional(ini, buffer, buffer_len);

          config_setup = true;
        }
      }

      ini.close();
    }
  }

  DEBUG_PRINT(F("broadcast_time_s: "));
  if (! broadcast_time_s) {
    DEBUG_PRINT(F("(default) "));
    broadcast_time_s = 2;
  }
  DEBUG_PRINTLN(broadcast_time_s);

  DEBUG_PRINT(F("default_brightness: "));
  if (! default_brightness) {
    DEBUG_PRINT(F("(default) "));
    default_brightness = 60;  // TODO: increase this when done debugging
  }
  DEBUG_PRINTLN(default_brightness);

  DEBUG_PRINT(F("frames_per_second: "));
  if (! frames_per_second) {
    DEBUG_PRINT(F("(default) "));
    frames_per_second = 30;
  }
  DEBUG_PRINTLN(frames_per_second);

  DEBUG_PRINT(F("max_peer_distance: "));
  if (! max_peer_distance) {
    DEBUG_PRINT(F("(default) "));
    max_peer_distance = 5000;
  }
  DEBUG_PRINTLN(max_peer_distance);

  DEBUG_PRINT(F("ms_per_light_pattern: "));
  if (! ms_per_light_pattern) {
    DEBUG_PRINT(F("(default) "));
    ms_per_light_pattern = 10 * 60 * 1000;
  }
  DEBUG_PRINTLN(ms_per_light_pattern);

  DEBUG_PRINT(F("peer_led_ms: "));
  // time to display the peer when multiple peers are the same direction
  if (! peer_led_ms) {
    DEBUG_PRINT(F("(default) "));
    peer_led_ms = 500;
  }
  DEBUG_PRINTLN(peer_led_ms);

  DEBUG_PRINT(F("radio_power: "));
  // 5-23 dBm
  // TODO: whats the difference in power?
  if (! radio_power) {
    DEBUG_PRINT(F("(default) "));
    radio_power = 13;
  }
  DEBUG_PRINTLN(radio_power);

  DEBUG_PRINT(F("time_zone_offset: "));
  if (!time_zone_offset) {
    DEBUG_PRINT(F("(default) "));
    time_zone_offset = -8;
  }
  DEBUG_PRINTLN(time_zone_offset);

  DEBUG_PRINT(F("flashlight_density: "));
  if (flashlight_density) {
    DEBUG_PRINT(F("(default) "));
    flashlight_density = 2;
  }
  DEBUG_PRINTLN(flashlight_density);

  // initialize compass messages
  for (int i = 0; i < num_peers; i++) {
    compass_messages[i].network_id = my_network_id;
    compass_messages[i].tx_peer_id = my_peer_id;
    compass_messages[i].peer_id = i;

    // hue, latitude, longitude are set for remote peers when a message for this peer is received
    // latitude, longitude for my_peer_id are set when GPS data is received
  }

  compass_messages[my_peer_id].hue = my_hue;
  compass_messages[my_peer_id].saturation = my_saturation;

  // TODO: there has to be a better way to concatenate ints into strings
  gps_log_filename = my_network_id;
  if (! my_peer_id) {
    gps_log_filename = gps_log_filename + F("-0.log");
  } else {
    gps_log_filename = gps_log_filename + F("-");
    gps_log_filename = gps_log_filename + my_peer_id;
    gps_log_filename = gps_log_filename + F(".log");
  }

  DEBUG_PRINT(F("gps_log_filename: "));
  DEBUG_PRINTLN(gps_log_filename);

  setupSecurity();
}

void networkIdFromKey(uint8_t* network_key, uint8_t* network_id) {
  blake2s.reset(sizeof(network_id));

  blake2s.update(network_key, sizeof(network_key));

  blake2s.finalize(network_id, sizeof(network_id));
}

void setupSecurity() {
  // TODO: open security.key and store in my_network_key

  my_file = SD.open(F("security.key"));

  DEBUG_PRINT(F("Opening security.key... "));
  if (!my_file) {
    // if the file didn't open, print an error:
    DEBUG_PRINTLN(F("failed!"));
    return;
  }
  DEBUG_PRINTLN(F("open."));

  my_file.read(my_network_key, sizeof(my_network_key));

  // close the file:
  my_file.close();

  // this will override whatever they set
  // TODO: not sure about the types here..
  networkIdFromKey(my_network_key, (uint8_t*) my_network_id);
  DEBUG_PRINT(F("key-based my_network_id: "));
  DEBUG_PRINTLN(my_network_id);
}

