/* lights */

void setupLights() {
  Serial.print("Setting up lights... ");

  pinMode(LED_DATA_PIN, OUTPUT);

  // TODO: seed fastled random?

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
    if (next_compass_point[i] > 0) {
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
    // everything starts at least a little dimmed
    leds[i].fadeToBlackBy(90);
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
  // turn the time into a watch face with just an hour hand

  // TODO: do we care about gpsMs? we only have 16 lights of output
  int adjusted_seconds = second();  // + (gpsMs % 1000) / 1000;

  int adjusted_minute = minute() + adjusted_seconds / 60.0;

  // we include the minutes here in case of fractional timezones. we will likely drop the minute
  int adjusted_hour = hour() + time_zone_offset + adjusted_minute / 60.0;

  if (adjusted_hour < 0) {
    adjusted_hour += 12;
  } else if (adjusted_hour >= 12) {
    adjusted_hour -= 12;
  }

  Serial.print("time: ");
  Serial.print(adjusted_hour);
  Serial.print(":");
  Serial.print(adjusted_minute);
  Serial.print(":");
  Serial.println(adjusted_seconds);

  // TODO: make sure this loops the right way once it is wired.
  // TODO: why do I need % 16?
  int hour_id = map(adjusted_hour, 0, 12, 16, 0) % 16;
  int minute_id = map(adjusted_minute, 0, 60, 16, 0) % 16;
  int second_id = map(adjusted_seconds, 0, 60, 16, 0) % 16;

  Serial.print("{hour,minute,second}_id: ");
  Serial.print(hour_id);
  Serial.print(" ");
  Serial.print(minute_id);
  Serial.print(" ");
  Serial.println(second_id);

  // TODO: I'm not sure what color the noon marker should be or if we even need one
  // TODO: what colors should the leds be?
  // TODO: i'm not sure i like how i'm handling overlapping
  // TODO: blink instead of full brightness? at least use HSV to lower the brightness
  for (int i = 0; i < num_LEDs; i++) {
    if (i == second_id) {
      leds[i] = CRGB::Blue;
    } else if (i == minute_id) {
      leds[i] = CRGB::Yellow;
    } else if (i == hour_id) {
      leds[i] = CRGB::Red;
    }
    // everything starts at least a little dimmed
    // lights that aren't part of the current time will quickly fade to black
    // this makes for a smooth transition from other patterns
    leds[i].fadeToBlackBy(90);
  }
}

void updateLights() {
  // update the led array every frame
  EVERY_N_MILLISECONDS(1000 / frames_per_second) {
    // decrease overall brightness if battery is low
    switch (checkBattery()) {
    case 0:
      // battery critical!
      // TODO: use map_float(quadwave8(millis()), 0, 256, 0.3, 0.5);
      FastLED.setBrightness(default_brightness * .5);
      break;
    case 1:
      // battery low
      FastLED.setBrightness(default_brightness * .75);
      break;
    case 2:
      // battery ok
      FastLED.setBrightness(default_brightness * .90);
      break;
    case 3:
      // battery fully charged
      FastLED.setBrightness(default_brightness);
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
