/* Config */

// from https://github.com/stevemarple/IniFile/blob/master/examples/IniFileExample/IniFileExample.ino
void printErrorMessage(uint8_t e, bool eol = true) {
  Serial.print("Config Error: ");

  switch (e) {
  case IniFile::errorNoError:
    Serial.print("no error");
    break;
  case IniFile::errorFileNotFound:
    Serial.print("file not found");
    break;
  case IniFile::errorFileNotOpen:
    Serial.print("file not open");
    break;
  case IniFile::errorBufferTooSmall:
    Serial.print("buffer too small");
    break;
  case IniFile::errorSeekError:
    Serial.print("seek error");
    break;
  case IniFile::errorSectionNotFound:
    Serial.print("section not found");
    break;
  case IniFile::errorKeyNotFound:
    Serial.print("key not found");
    break;
  case IniFile::errorEndOfFile:
    Serial.print("end of file");
    break;
  case IniFile::errorUnknownError:
    Serial.print("unknown error");
    break;
  default:
    Serial.print("unknown error value");
    break;
  }
  if (eol) {
    Serial.println();
  }
}

void setupConfig() {
  const size_t buffer_len = 80;
  char buffer[buffer_len];
  const char *filename = "/config.ini";

  // create this even if sd isn't setup so that the if/else below is simpler
  IniFile ini(filename);

  if (!sd_setup) {
    Serial.println("SD not setup. Skipping dynamic config!");
  } else {
    Serial.println("Loading config... ");

    if (!ini.open()) {
      // TODO: default to just pretty lights since we don't have a network id or home locations
      Serial.println(" does not exist. Cannot proceed!");
      while (1)
        ;
    }

    if (!ini.validate(buffer, buffer_len)) {
      // TODO: default to just pretty lights since we don't have a network id or home locations
      Serial.print(ini.getFilename());
      Serial.print(" not valid. Cannot proceed!");
      printErrorMessage(ini.getError());
      while (1)
        ;
    }

    // load required args
    if (ini.getValue("global", "num_peers", buffer, buffer_len, num_peers)) {
      Serial.print("num_peers: ");
      Serial.println(buffer);
    } else {
      Serial.print("Could not read 'num_peers' from section 'global', error was ");
      printErrorMessage(ini.getError());
      while (1)
        ;
    }

    if (ini.getValue("global", "my_network_id", buffer, buffer_len, my_network_id)) {
      Serial.print("my_network_id: ");
      Serial.println(buffer);
    } else {
      Serial.print("Could not read 'my_network_id' from section 'global', error was ");
      printErrorMessage(ini.getError());
      while (1)
        ;
    }

    if (ini.getValue("global", "my_peer_id", buffer, buffer_len, my_peer_id)) {
      Serial.print("my_peer_id: ");
      Serial.println(buffer);
    } else {
      Serial.print("Could not read 'my_peer_id' from section 'global', error was ");
      printErrorMessage(ini.getError());
      while (1)
        ;
    }

    if (ini.getValue("global", "my_hue", buffer, buffer_len, my_hue)) {
      Serial.print("my_hue: ");
      Serial.println(buffer);
    } else {
      Serial.print("Could not read 'my_hue' from section 'global', error was ");
      printErrorMessage(ini.getError());
      while (1)
        ;
    }

    if (ini.getValue("global", "my_saturation", buffer, buffer_len, my_saturation)) {
      Serial.print("my_saturation: ");
      Serial.println(buffer);
    } else {
      Serial.print("Could not read 'my_saturation' from section 'global', error was ");
      printErrorMessage(ini.getError());
      while (1)
        ;
    }

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

  Serial.print("broadcast_time_s: ");
  if (! broadcast_time_s) {
    Serial.print("(default) ");
    broadcast_time_s = 2;
    Serial.println(broadcast_time_s);
  }

  Serial.print("default_brightness: ");
  if (! default_brightness) {
    Serial.print("(default) ");
    default_brightness = 60;  // TODO: increase this when done debugging
    Serial.println(default_brightness);
  }

  Serial.print("frames_per_second: ");
  if (! frames_per_second) {
    Serial.print("(default) ");
    frames_per_second = 30;
    Serial.println(frames_per_second);
  }

  // TODO: rename this. peers at this distance or further are the dimmest
  Serial.print("max_peer_distance: ");
  if (! max_peer_distance) {
    Serial.print("(default) ");
    max_peer_distance = 5000;
    Serial.println(max_peer_distance);
  }

  Serial.print("ms_per_light_pattern: ");
  if (! ms_per_light_pattern) {
    Serial.print("(default) ");
    ms_per_light_pattern = 10 * 60 * 1000;
  }
  Serial.println(ms_per_light_pattern);

  Serial.print("peer_led_ms: ");
  // time to display the peer when multiple peers are the same direction
  if (! peer_led_ms) {
    Serial.print("(default) ");
    peer_led_ms = 500;
  }
  Serial.println(peer_led_ms);

  Serial.print("radio_power: ");
  // 5-23 dBm
  // TODO: whats the difference in power?
  if (! radio_power) {
    Serial.print("(default) ");
    radio_power = 13;
  }
  Serial.println(radio_power);

  Serial.print("time_zone_offset: ");
  if (time_zone_offset) {
    ;
  } else {
    Serial.print("(default) ");
    time_zone_offset = -8;
  }
  Serial.println(time_zone_offset);

  Serial.print("flashlight_density: ");
  if (flashlight_density) {
    Serial.println(flashlight_density);
  } else {
    Serial.print("(default) ");
    flashlight_density = 2;
    Serial.println(flashlight_density);
  }

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
    gps_log_filename = gps_log_filename + "-0.log";
  } else {
    gps_log_filename = gps_log_filename + "-";
    gps_log_filename = gps_log_filename + my_peer_id;
    gps_log_filename = gps_log_filename + ".log";
  }

  Serial.print("gps_log_filename: ");
  Serial.println(gps_log_filename);

  // everyone will be in sync on the patterns, but their color will be diffferent
  // TODO: except that would only be true if they get plugged in at the exact same time. maybe sync this over the radio?
  // TODO: or tie it more directly to the current time (and sync that)
  g_hue = my_hue;
}
