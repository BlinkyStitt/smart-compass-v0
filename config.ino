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

  Serial.println("Loading config... ");

  const char *filename = "/config.ini";

  IniFile ini(filename);

  if (!ini.open()) {
    // TODO: block here once the sd card is actually wired up
    /*
    Serial.println(" does not exist. Cannot proceed!");
    while (1)
      ;
    */
  }

  /*
  // TODO: block here once the sd card is actually wired up
  // Check the file is valid. This can be used to warn if any lines are longer than the buffer.
  if (!ini.validate(buffer, buffer_len)) {
    Serial.print(ini.getFilename());
    Serial.print(" not valid. Cannot proceed!");
    printErrorMessage(ini.getError());
    while (1)
      ;
  }
  */

  /*
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
    Serial.print("network_id: ");
    Serial.println(buffer);
  } else {
    Serial.print("Could not read 'my_network_id' from section 'global', error was ");
    printErrorMessage(ini.getError());
    while (1)
      ;
  }

  if (ini.getValue("global", "my_peer_id", buffer, buffer_len, my_peer_id)) {
    Serial.print("peer_id: ");
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
  */
  num_peers = 4;
  my_network_id = 1;
  my_peer_id = 1;
  my_hue = 140;
  my_saturation = 110;

  // load args that have defaults
  Serial.print("broadcast_time_ms: ");
  if (false && ini.getValue("global", "broadcast_time_ms", buffer, buffer_len, broadcast_time_ms)) {
    Serial.println(buffer);
  } else {
    Serial.print("(default) ");
    broadcast_time_ms = 250; // TODO: tune this.
    // peers will be updated at most broadcast_time_ms * num_peers * num_peers
    Serial.println(broadcast_time_ms);
  }

  Serial.print("default_brightness: ");
  if (false && ini.getValue("global", "default_brightness", buffer, buffer_len, default_brightness)) {
    Serial.println(buffer);
  } else {
    Serial.print("(default) ");
    default_brightness = 60;
    Serial.println(default_brightness);
  }

  Serial.print("frames_per_second: ");
  if (false && ini.getValue("global", "frames_per_second", buffer, buffer_len, frames_per_second)) {
    Serial.println(buffer);
  } else {
    Serial.print("(default) ");
    frames_per_second = 30;
    Serial.println(frames_per_second);
  }

  // TODO: rename this. peers at this distance or further are the dimmest
  Serial.print("max_peer_distance: ");
  if (false && ini.getValue("global", "max_peer_distance", buffer, buffer_len, max_peer_distance)) {
    Serial.println(buffer);
  } else {
    Serial.print("(default) ");
    max_peer_distance = 5000;
    Serial.println(max_peer_distance);
  }

  Serial.print("ms_per_light_pattern: ");
  if (false && ini.getValue("global", "ms_per_light_pattern", buffer, buffer_len, ms_per_light_pattern)) {
    Serial.println(buffer);
  } else {
    Serial.print("(default) ");
    ms_per_light_pattern = 10 * 60 * 1000;
    Serial.println(ms_per_light_pattern);
  }

  Serial.print("peer_led_ms: ");
  // time to display the peer when multiple peers are the same direction
  if (false && ini.getValue("global", "peer_led_ms", buffer, buffer_len, peer_led_ms)) {
    Serial.println(buffer);
  } else {
    Serial.print("(default) ");
    peer_led_ms = 500;
    Serial.println(peer_led_ms);
  }

  Serial.print("radio_power: ");
  // 5-23 dBm
  // TODO: whats the difference in power?
  if (false && ini.getValue("global", "radio_power", buffer, buffer_len, radio_power)) {
    Serial.println(buffer);
  } else {
    Serial.print("(default) ");
    radio_power = 13;
    Serial.println(radio_power);
  }

  Serial.print("time_zone_offset: ");
  if (false && ini.getValue("global", "time_zone_offset", buffer, buffer_len, time_zone_offset)) {
    Serial.println(buffer);
  } else {
    Serial.print("(default) ");
    time_zone_offset = -7;
    Serial.println(time_zone_offset);
  }

  Serial.print("flashlight_density: ");
  if (false && ini.getValue("global", "flashlight_density", buffer, buffer_len, flashlight_density)) {
    Serial.println(buffer);
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

  gps_log_filename += my_network_id;
  gps_log_filename += "-" + my_peer_id;
  gps_log_filename += ".log";

  // everyone will be in sync on the patterns, but their color will be diffferent
  // TODO: except that would only be true if they get plugged in at the exact same time. maybe sync this over the radio?
  // TODO: or tie it more directly to the current time (and sync that)
  g_hue = my_hue;
}
