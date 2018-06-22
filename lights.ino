/* lights */

int saved_pin_id = -1; // when a pin is modified, this is updated to match the id. once configuration is complete, this pin_id is broadcast to peers and

// TODO: i don't love this pattern
CompassMode next_compass_mode = COMPASS_FRIENDS;

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
  // show the compass if we know our own GPS location and have SD to show saved locations
  if (!GPS.fix or !sd_setup) {
    updateLightsForLoading();
    return;
  }

  // calculate distance to friends or saved places
  updateCompassPoints(compass_mode);

  // cycle through the colors for each light
  // TODO: dry this up
  for (int i = 0; i < inner_ring_size; i++) {
    if (next_inner_compass_point[i] > 0) {
      int j = 0;
      if (next_inner_compass_point[i] > 1) {
        // there are one or more colors that want to shine on this one light. give each 500ms
        // TODO: instead give the closer peers (brighter compass points) more time?
        // TODO: use a static variable for this and increment it every 500ms instead? or use FastLED beat helper?
        // we don't use network_ms here so that the lights don't jump around
        j = map(((millis() / peer_led_ms) % num_peers), 0, num_peers, 0, next_inner_compass_point[i]);
      }

      // DEBUG_PRINT("Displaying 1 of "); DEBUG_PRINT(next_compass_point[i]);
      // DEBUG_PRINT(" colors for light #"); DEBUG_PRINTLN(i);

      leds[i] = inner_compass_points[i][j];
    } else {
      // lights from other patterns will quickly fade to black
      leds[i].fadeToBlackBy(90);
    }
  }
}

void updateLightsForHanging() {
  // do awesome patterns
  static int num_light_patterns = 1; // TODO: how should this work? this seems fragile. make a list of functions instead

  // TODO: use network_ms (synced with peers) so everyone has the same light pattern
  int pattern_id = (network_ms / ms_per_light_pattern) % num_light_patterns;

  // TODO: more patterns
  switch (pattern_id) {
  case 0:
    pride(); // TODO: pride doesn't look very good with only 16 lights
    break;
  }
}

// non-blocking lights are a lot harder than lights using delay! good luck!
void updateLightsForLoading() {
  // TODO: have 3 lights chasing each other in a circle. red for sd_setup, green for config_setup, blue for sd_setup
  // TODO: if none of them are setup, do something special

  if (sd_setup and config_setup and sd_setup) {
    // setup was successful. show standard loading lights
    circle();
    return;
  }

  pride();
  return;
}

void updateLightsForConfiguring(const CompassMode compass_mode, CompassMode configure_mode, Orientation last_orientation, Orientation current_orientation) {
  static elapsedMillis configure_ms = 0;
  static CHSV fill_color;
  static int pin_id = -1, num_fill = 0;

  // we need a GPS fix and SD/
  if (!GPS.fix or !sd_setup) {
    updateLightsForLoading();
    return;
  }

  if (last_orientation != current_orientation) {
    // reset the timer if the orientation just changed
    configure_ms = 0;
    pin_id = -1;
  }

  switch(configure_mode) {
  case COMPASS_PLACES:
    fill_color = CHSV(240, 255, 128); // blue
    break;
  case COMPASS_FRIENDS:
    fill_color = CHSV(0, 255, 128);  // red
    break;
  }

  if (configure_ms < 5000) {
    // fill up the inner circle of lights over 5 seconds
    num_fill = constrain(map(configure_ms, 0, 5000, 0, inner_ring_size), 0, inner_ring_size);
    fill_solid(leds, inner_ring_start + num_fill, fill_color);
  } else {
    // the compass has been held in configure mode for 5 seconds and the inner ring has filled completely
    next_compass_mode = configure_mode; // TODO: pass by reference instead of globals?

    if (configure_mode != COMPASS_PLACES) {
      // only COMPASS_PLACES lets you save locations
      // don't do anything with the outer ring. just leave the inner filled
      fill_solid(leds, inner_ring_end, fill_color);
    } else {
      // keep the inner ring filled and fill up the outer circle of lights over 5 seconds
      num_fill = constrain(map(configure_ms, 5000, 10000, 0, outer_ring_size), 0, outer_ring_size);
      fill_solid(leds, outer_ring_start + num_fill, fill_color);

      if (configure_ms > 10000) {
        // TODO: rotate through different fill_colors with a small pallet (exclude red since that is north)

        if (pin_id != -1) {
          // TODO: set pin_id to either match the nearest pin or return the id of an unset pin
          // pin_id = ...;

          saved_pin_id = pin_id;
        }

        setPin(pin_id, fill_color, GPS.latitude_fixed, GPS.longitude_fixed);
      }
    }
  }

  return;
}

void updateLights() {
  static Orientation last_orientation = ORIENTED_PORTRAIT;
  static Orientation current_orientation;
  static CompassMode compass_mode = COMPASS_FRIENDS;

  // decrease overall brightness if battery is low
  // TODO: how often should we do this?
  EVERY_N_SECONDS(120) {
    switch (checkBattery()) {
    case BATTERY_DEAD:
      // TODO: use map_float(quadwave8(millis()), 0, 256, 0.3, 0.5);
      // TODO: maybe add a red led to a strip of 8 LEDs?
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
      // if we did any configuring, next_compass_mode will be set to the desired compass_moe
      compass_mode = next_compass_mode;
      // if we did a long time of configuring, we have a new lat/long saved. queue it from broadcast
      // we didn't broadcast it when it was saved because it might have a non-standard color that takes some extra time to configure
      if (saved_pin_id > 0) {
        queueBroadcastPin(saved_pin_id);

        // clear saved_pin_id now that the message is queued
        saved_pin_id = -1;
      }

      updateLightsForCompass(compass_mode);
      break;
    case ORIENTED_DOWN:
      flashlight();
      break;
    case ORIENTED_USB_DOWN:
      updateLightsForConfiguring(compass_mode, COMPASS_PLACES, last_orientation, current_orientation);
      break;
    case ORIENTED_USB_UP:
      updateLightsForConfiguring(compass_mode, COMPASS_FRIENDS, last_orientation, current_orientation);
      break;
    case ORIENTED_PORTRAIT:
      // pretty patterns
      // TODO: different things for the different USB tilts? maybe use that to toggle what the compass shows? need some sort of debounce
      updateLightsForHanging();
      break;
    case ORIENTED_PORTRAIT_UPSIDE_DOWN:
      // show the time
      // TODO: usb up is showing this, too. check orientations
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
