/* lights */

void setupLights() {
  DEBUG_PRINT("Setting up lights... ");

  pinMode(LED_DATA_PIN, OUTPUT);
  pinMode(RED_LED_PIN, OUTPUT);

  // TODO: seed fastled random?

  // https://learn.adafruit.com/adafruit-feather-m0-basic-proto/power-management
  // While you can get 500mA from it, you can't do it continuously from 5V as it will overheat the regulator.
  FastLED.setMaxPowerInVoltsAndMilliamps(3.3, 500);

  FastLED.addLeds<LED_CHIPSET, LED_DATA_PIN>(leds, num_LEDs).setCorrection(TypicalSMD5050);
  FastLED.setBrightness(default_brightness); // TODO: read this from the SD card
  FastLED.clear();
  FastLED.show();

  DEBUG_PRINTLN("done.");
}

void updateLightsForCompass(CompassMode compass_mode) {
  // show the compass if we know our own GPS location
  if (!GPS.fix) {
    updateLightsForLoading();
    return;
  }

  updateCompassPoints(compass_mode);

  // cycle through the colors for each light
  for (int i = 0; i < num_LEDs; i++) {
    if (next_compass_point[i] > 0) {
      int j = 0;
      if (next_compass_point[i] > 1) {
        // there are one or more colors that want to shine on this one light. give each 500ms
        // TODO: instead give the closer peers (brighter compass points) more time?
        // TODO: use a static variable for this and increment it every 500ms instead? or use FastLED beat helper?
        // TODO: use nowMillis() here?
        j = map(((millis() / peer_led_ms) % num_peers), 0, num_peers, 0, next_compass_point[i]);
      }

      // DEBUG_PRINT("Displaying 1 of "); DEBUG_PRINT(next_compass_point[i]);
      // DEBUG_PRINT(" colors for light #"); DEBUG_PRINTLN(i);

      leds[i] = compass_points[i][j];
    }
    // everything starts at least a little dimmed. lights from other patterns will quickly fade to black
    leds[i].fadeToBlackBy(90);
  }
}

void updateLightsForHanging() {
  // do awesome patterns
  static int num_light_patterns = 1; // TODO: how should this work? this seems fragile. make a list of functions instead

  // TODO: use gps time (synced with peers) to have the same light pattern as them
  int pattern_id = (millis() / ms_per_light_pattern) % num_light_patterns;

  // TODO: more patterns
  switch (pattern_id) {
  case 0:
    pride(); // TODO: pride doesn't look very good with only 16 lights
    break;
  }
}

// non-blocking lights are a lot harder than lights using delay! good luck!
void updateLightsForLoading() {
  // TODO: what pattern? just loop instead of sinelon?
  circle();
}

void updateLightsForConfiguring(CompassMode compass_mode, CompassMode configure_mode, Orientation last_orientation, Orientation current_orientation) {
  static elapsedMillis configure_ms = 0;

  CompassMode next_compass_mode = compass_mode;  // this will change to configure_mode after configure_ms reaches a threshold

  // TODO: finish writing this
  return;

  if (!GPS.fix) {
    updateLightsForLoading();
    return;
  }

  if (last_orientation != current_orientation) {
    // reset the timer if the orientation just changed
    configure_ms = 0;
  }

  if (compass_mode == configure_mode) {
    // TODO: update lights. fill up the circle using configure_ms over 5 seconds
  } else {
    // TODO: drain lights?
  }

  if (configure_ms > 5000 + 100) {
    // TODO: add glitter to show that its done

    // TODO: having this overlapping with long or short hold is kinda weird. buttons would probably be better
    if (compass_mode == configure_mode) {
      // if we are already configured for this mode and they've held it for 5 seconds, change mode to default
      next_compass_mode = COMPASS_FRIENDS;
    } else {
      // if the current compass mode does not match the mode we are configuring, change to that mode
      next_compass_mode = configure_mode;
    }

    if (configure_ms > 10000 + 100) {
      // TODO: add a different glitter effect to show we are saving/deleting a pin
      switch(configure_mode) {
      case COMPASS_BATHROOM:
        updateBathroomPin();
        break;
      case COMPASS_HOME:
        updateHomePin();
        break;
      }
    }
  }

  return;
}

void updateLights() {
  static Orientation last_orientation = ORIENTED_PORTRAIT;
  static Orientation current_orientation;
  static CompassMode compass_mode = COMPASS_FRIENDS;
  static CompassMode next_compass_mode = COMPASS_FRIENDS;

  // decrease overall brightness if battery is low
  // TODO: how often should we do this?
  EVERY_N_SECONDS(120) {
    switch (checkBattery()) {
    case BATTERY_DEAD:
      // TODO: use map_float(quadwave8(millis()), 0, 256, 0.3, 0.5);
      FastLED.setBrightness(default_brightness * .5);
      break;
    case BATTERY_LOW:
      FastLED.setBrightness(default_brightness * .75);
      break;
    case BATTERY_OK:
      FastLED.setBrightness(default_brightness * .90);
      break;
    case BATTERY_FULL:
      FastLED.setBrightness(default_brightness);
      break;
    }
  }

  // update the led array every frame
  EVERY_N_MILLISECONDS(1000 / frames_per_second) {
    current_orientation = getOrientation();
    switch (current_orientation) {
    case ORIENTED_UP:
      compass_mode = next_compass_mode;  // TODO: is this right?
      updateLightsForCompass(compass_mode);
      break;
    case ORIENTED_DOWN:
      flashlight();
      break;
    case ORIENTED_USB_DOWN:
      updateLightsForConfiguring(compass_mode, COMPASS_BATHROOM, last_orientation, current_orientation);
      break;
    case ORIENTED_USB_UP:
      updateLightsForConfiguring(compass_mode, COMPASS_HOME, last_orientation, current_orientation);
      break;
    case ORIENTED_PORTRAIT:
      // pretty patterns
      // TODO: different things for the different USB tilts? maybe use that to toggle what the compass shows? need some sort of debounce
      updateLightsForHanging();
      break;
    case ORIENTED_PORTRAIT_UPSIDE_DOWN:
      // show the time
      // TODO: usb up is showing this, too
      if (timeStatus() == timeSet) {
        updateLightsForClock();
      } else {
        updateLightsForLoading();
      }
      break;
    }

    last_orientation = current_orientation;

    #ifdef DEBUG
      // debugging lights
      int network_ms_wrapped = network_ms % 10000;
      if (network_ms_wrapped < 1000) {
        DEBUG_PRINT(F(" "));

        if (network_ms_wrapped < 100) {
          DEBUG_PRINT(F(" "));

          if (network_ms_wrapped < 10) {
            DEBUG_PRINT(F(" "));
          }
        }
      }
      DEBUG_PRINT(network_ms_wrapped);

      DEBUG_PRINT(F(": "));
      for (int i = 0; i < num_LEDs; i++) {
        if (leds[i]) {
          // TODO: better logging?
          DEBUG_PRINT(F("X"));
        } else {
          DEBUG_PRINT(F("O"));
        }
      }
      DEBUG_PRINTLN();
    #endif

    // display the colors
    FastLED.show();

    // set g_hue based on shared timer
    g_hue = network_ms / (3 * 1000 / frames_per_second);
  }
}
