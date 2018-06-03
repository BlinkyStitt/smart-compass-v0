/* lights */

void setupLights() {
  Serial.print("Setting up lights... ");

  pinMode(LED_DATA_PIN, OUTPUT);

  // https://learn.adafruit.com/adafruit-feather-m0-basic-proto/power-management
  // While you can get 500mA from it, you can't do it continuously from 5V as it will overheat the regulator.
  FastLED.setMaxPowerInVoltsAndMilliamps(3.3, 500);

  FastLED.addLeds<LED_CHIPSET, LED_DATA_PIN>(leds, num_LEDs).setCorrection(TypicalSMD5050);
  FastLED.setBrightness(default_brightness); // TODO: read this from the SD card
  FastLED.clear();
  FastLED.show();

  Serial.println("done.");
}

void updateLightsForCompass() {
  updateCompassPoints();

  // cycle through the colors for each light
  for (int i = 0; i < num_LEDs; i++) {
    if (next_compass_point[i] == 0) {
      // no colors on this light. turn it off
      leds[i] = CRGB::Black;
      // Serial.print("No color for light #"); Serial.println(i);
      continue;
    } else {
      int j = 0;
      if (next_compass_point[i] > 1) {
        // there are one or more colors that want to shine on this one light. give each 500ms
        // TODO: instead give the closer peers (brighter compass points) more time?
        // TODO: use a static variable for this and increment it every 500ms instead?
        j = map(((millis() / peer_led_ms) % num_peers), 0, num_peers, 0, next_compass_point[i]);
      }

      // Serial.print("Displaying 1 of "); Serial.print(next_compass_point[i]);
      // Serial.print(" colors for light #"); Serial.println(i);

      leds[i] = compass_points[i][j];
    }
  }
}

void updateLightsForHanging() {
  // do awesome patterns
  static int num_light_patterns = 1; // TODO: how should this work? this seems fragile. make a list of functions instead

  // we use the actual time in ms instead of elapsed_ms so that all the compasses are in near perfect sync
  // ms since 1970 divided into 1 minute chunks
  int pattern_id = (nowMillis() / ms_per_light_pattern) % num_light_patterns;

  // TODO: more patterns
  switch (pattern_id) {
  case 0:
    sinelon(); // TODO: pride doesn't look very good with only 16 lights
    break;
  }
}

// non-blocking lights are a lot harder than lights using delay! good luck!
void updateLightsForLoading() {
  // TODO: what pattern? just loop instead of sinelon?
  sinelon();
}

void updateLightsForClock() {
  // TODO: turn the time into a watch face. use hour() and minute() and seconds()
  int hour_id, minute_id, second_id;

  // note that the lights are wired counter-clockwise!
  // TODO: timezone from lat/long? at least read it from the SD card
  int timezone_adjusted_hour = hour() - 8;
  if (timezone_adjusted_hour < 0) {
    timezone_adjusted_hour += 12;
  } else {
    timezone_adjusted_hour %= 12;
  }

  hour_id = map(timezone_adjusted_hour, 0, 12, 16, 0);
  minute_id = map(minute(), 0, 60, 16, 0);
  second_id = map(second(), 0, 60, 16, 0);

  // TODO: I'm not sure what color the noon marker should be. and i'm not sure i like how i'm handling overlapping
  for (int i = 0; i < num_LEDs; i++) {
    if (i == second_id) {
      leds[i] = CRGB::Red;
    } else if (i == minute_id) {
      leds[i] = CRGB::Yellow;
    } else if (i == hour_id) {
      leds[i] = CRGB::Blue;
    } else {
      // TODO: dim quickly instead?
      leds[i] = CRGB::Black;
    }
  }
}

void updateLights() {
  // update the led array every frame
  EVERY_N_MILLISECONDS(1000 / frames_per_second) {
    // TODO: do something based on battery level. maybe decrease overall brightness in a loop to make it blink slowly
    switch (checkBattery()) {
    case 0:
      // battery critical!
      break;
    case 1:
      // battery low
      break;
    case 2:
      // battery ok
      break;
    case 3:
      // battery fully charged
      break;
    }

    switch (checkOrientation()) {
    case ORIENTED_UP:
      // show the compass if possible
      if (GPS.fix) {
        updateLightsForCompass();
      } else {
        updateLightsForLoading();
      }
      break;
    case ORIENTED_DOWN:
      flashlight();
      break;
    case ORIENTED_USB_UP:
    case ORIENTED_SPI_UP:
    case ORIENTED_SPI_DOWN:
      // pretty patterns
      // TODO: different things for the different SPI tilts? maybe use that to toggle what the compass shows? need some sort of debounce
      updateLightsForHanging();
      break;
    case ORIENTED_USB_DOWN:
      // show the time
      // TODO: usb up is showing this, too
      if (timeStatus() == timeSet) {
        updateLightsForClock();
      } else {
        updateLightsForLoading();
      }
      break;
    }

    // debugging lights
    for (int i = 0; i < num_LEDs; i++) {
      if (leds[i]) {
        // TODO: better logging?
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
  EVERY_N_MILLISECONDS(3 * 1000 / frames_per_second) { g_hue++; }
}
