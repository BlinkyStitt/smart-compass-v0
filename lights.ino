/* lights */

int saved_pin_id = -1; // when a pin is modified, this is updated to match the id. once configuration is complete, this
                       // pin_id is broadcast to peers and

// TODO: i don't love this pattern
CompassMode next_compass_mode = COMPASS_FRIENDS;

void setupLights() {
  DEBUG_PRINT("Setting up lights... ");

  pinMode(LED_DATA, OUTPUT);
  pinMode(RED_LED, OUTPUT);

  digitalWrite(RED_LED, LOW);

  // TODO: seed fastled random?

  // https://learn.adafruit.com/adafruit-feather-m0-basic-proto/power-management
  // "While you can get 500mA from it, you can't do it continuously from 5V as it will overheat the regulator."
  // TODO: include radio_power instead of hard coding 120 (it is 120mA when radio_power=20)
  // TODO: we won't use the radio at full power and SD at full power at the same time. so tune this
  // TODO: maybe run it without lights to see max power draw and subtract that from 500
  // leave some room for the radio and gps and SD and mcu (TODO: and 100mA for charger?)
  FastLED.setMaxPowerInVoltsAndMilliamps(3.3, 500 - 120 - 25 - 100 - 50);

  FastLED.addLeds<LED_CHIPSET, LED_DATA>(leds, num_LEDs).setCorrection(TypicalSMD5050);
  FastLED.setBrightness(default_brightness);
  FastLED.clear();
  FastLED.show();

  DEBUG_PRINTLN("done.");
}

void updateLightsForCompass(CompassMode compass_mode) {
  static unsigned long now_ms = 0;

  // show the compass if we know our own GPS location and have SD to show saved locations
  if (!GPS.fix or !sd_setup) {
    DEBUG_PRINTLN(F("Compass not ready!"));
    updateLightsForLoading();
    return;
  }

  now_ms = millis();

  // calculate distance to friends or saved places
  updateCompassPoints(compass_mode);

  // fade all lights
  fadeToBlackBy(leds, num_LEDs, LED_FADE_RATE);

  // cycle through the colors for each light
  // TODO: dry this up
  for (int i = 0; i < inner_ring_size; i++) {
    //    DEBUG_PRINT(F("inner ring "));
    //    DEBUG_PRINTLN(i);

    if (next_inner_compass_point[i] == 0) {
      // no lights for this inner compass point

      // lights from other patterns will quickly fade to black
      leds[inner_ring_start + i].fadeToBlackBy(90);

      continue;
    }

    if (next_inner_compass_point[i] > max_compass_points) {
      // TODO: what is going on?
      DEBUG_PRINT(F("ERROR! INVALID next_outer_compass_point for "));
      DEBUG_PRINT(i);
      DEBUG_PRINT(F(": "));
      DEBUG_PRINTLN(next_outer_compass_point[i]);
      continue;
    }

    int j = 0;
    if (next_inner_compass_point[i] > 1) {
      // there are one or more colors that want to shine on this one light. give each 500ms
      // TODO: use a static variable for this and increment it every 500ms instead? or use FastLED beat helper?
      // we don't use network_ms here so that the lights don't jump around
      // TODO: this is wrong
      j = (now_ms / peer_led_ms) % next_inner_compass_point[i];
    }

    //     DEBUG_PRINT("Displaying ");
    //     DEBUG_PRINT(j + 1);
    //     DEBUG_PRINT(" of ");
    //     DEBUG_PRINT(next_inner_compass_point[i]);
    //     DEBUG_PRINT(" colors for inner light #");
    //     DEBUG_PRINTLN(i);

    leds[inner_ring_start + i] = inner_compass_points[i][j];
  }
  // TODO: this is broken. i think the bug is somewhere in the setting of outer_compass_points
  for (int i = 0; i < outer_ring_size; i++) {
    //    DEBUG_PRINT(F("outer ring "));
    //    DEBUG_PRINTLN(i);

    if (next_outer_compass_point[i] == 0) {
      // no lights for this outer compass point

      // lights from other patterns will quickly fade to black
      leds[outer_ring_start + i].fadeToBlackBy(90);

      continue;
    }

    if (next_outer_compass_point[i] > max_compass_points) {
      // TODO: what is going on?
      DEBUG_PRINT(F("ERROR! INVALID next_outer_compass_point for "));
      DEBUG_PRINT(i);
      DEBUG_PRINT(F(": "));
      DEBUG_PRINTLN(next_outer_compass_point[i]);
      continue;
    }

    int j = 0;
    if (next_outer_compass_point[i] > 1) {
      // there are one or more colors that want to shine on this one light. give each 500ms
      // TODO: use a static variable for this and increment it every 500ms instead? or use FastLED beat helper?
      // we don't use network_ms here so that the lights don't jump around
      // TODO: this is wrong
      j = (now_ms / peer_led_ms) % next_outer_compass_point[i];
    }

    //     DEBUG_PRINT("Displaying ");
    //     DEBUG_PRINT(j + 1);
    //     DEBUG_PRINT(" of ");
    //     DEBUG_PRINT(next_outer_compass_point[i]);
    //     DEBUG_PRINT(" colors for outer light #");
    //     DEBUG_PRINTLN(i);

    leds[outer_ring_start + i] = outer_compass_points[i][j];
  }
}

void updateLightsForHanging() {
  // do awesome patterns
  static const int num_light_patterns =
      1; // TODO: how should this work? this seems fragile. make an array of functions instead

  // use network_ms (synced with peers) so everyone has the same light pattern
  int pattern_id = (network_ms / ms_per_light_pattern) % num_light_patterns;

  // TODO: more patterns
  switch (pattern_id) {
  case 0:
    networkedLights();
    break;
  case 1: // TODO: bump num_light_patterns so this will get picked
    pride();
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

  networkedLights();
  return;
}

void updateLightsForConfiguring(const CompassMode compass_mode, CompassMode configure_mode,
                                Orientation last_orientation, Orientation current_orientation) {
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

    switch (configure_mode) {
    case COMPASS_PLACES:
      last_pin_color_id = 0;
      break;
    case COMPASS_FRIENDS:
      last_pin_color_id = delete_pin_color_id; // use the color for deleting? TODO: or not? this might be confusing
      break;
    }

    fill_color = pin_colors[last_pin_color_id];
  }

  // fade all lights
  fadeToBlackBy(leds, num_LEDs, LED_FADE_RATE);

  if (configure_ms < 4000) {
    // fill up the inner circle of lights over 4 seconds
    num_fill = inner_ring_start + constrain(map(configure_ms, 0, 4000, 0, inner_ring_size), 0, inner_ring_size);
  } else {
    // the compass has been held in configure mode for 4 seconds and the inner ring has filled completely
    next_compass_mode = configure_mode; // TODO: pass by reference instead of globals?

    if (configure_mode != COMPASS_PLACES) {
      // only COMPASS_PLACES lets you save locations
      // don't do anything with the outer ring. just leave the inner filled
      num_fill = inner_ring_end;
    } else {
      // keep the inner ring filled and fill up the outer circle of lights over 4 seconds
      num_fill = outer_ring_start + constrain(map(configure_ms, 4000, 8000, 0, outer_ring_size), 0, outer_ring_size);

      if (configure_ms >= 8000) {
        // the outer ring is filled!

        if (pin_id != -1) {
          // set pin_id to either match the nearest pin or return the id of the next unset pin
          pin_id = getCompassPinId(GPS.latitude_fixed, GPS.longitude_fixed);

          compass_pins[pin_id].transmitted = true;
          saved_pin_id = pin_id;
        }

        if (configure_ms >= 10000) {
          // if the outer ring has been filled for 2 seconds, change the color
          last_pin_color_id++;

          if (last_pin_color_id >= ARRAY_SIZE(pin_colors)) {
            last_pin_color_id = 0;
          }

          fill_color = pin_colors[last_pin_color_id];

          configure_ms = 8000;  // reset timer
        }

        setCompassPin(pin_id, fill_color, GPS.latitude_fixed, GPS.longitude_fixed);
      }
    }
  }

  // TODO: dim everything otherwise the unfilled lights stay lit up and its confusing
  fill_solid(leds, num_fill, fill_color);

  return;
}

void updateLights() {
  static Orientation last_orientation = ORIENTED_PORTRAIT;
  static Orientation current_orientation;
  static CompassMode compass_mode = COMPASS_FRIENDS;
  static unsigned long last_frame = 0;

  // decrease overall brightness if battery is low
  // TODO: how often should we do this?
  EVERY_N_SECONDS(300) {
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
      // TODO: different light pattern instead?
      FastLED.setBrightness(default_brightness);
      break;
    }
  }

  // update the led array every frame
  // TODO: TUNE this
  EVERY_N_MILLISECONDS(1000 / frames_per_second) {
    current_orientation = getOrientation();
    switch (current_orientation) {
    case ORIENTED_UP:
      // if we did any configuring, next_compass_mode will be set to the desired compass_moe
      compass_mode = next_compass_mode;
      // if we did a long time of configuring, we have a new lat/long saved. queue it from broadcast
      // we didn't broadcast it when it was saved because it might have a non-standard color that takes some extra time
      // to configure
      if (saved_pin_id > 0) {
        DEBUG_PRINTLN(F("Queuing saved pin for transmission."));
        // set transmitted to false now. next time we transmit, this pin id will be shared with peers
        compass_pins[saved_pin_id].transmitted = false;

        // TODO: save to database

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
      // TODO: different things for the different USB tilts? maybe use that to toggle what the compass shows? need some
      // sort of debounce
      updateLightsForHanging();
      break;
    case ORIENTED_PORTRAIT_UPSIDE_DOWN:
      // show the time
      // TODO: usb up is showing this, too. check orientations
      updateLightsForClock();
      break;
    }

    last_orientation = current_orientation;

    // TODO: i doubt this is related to the crash at all, but i'm stumped    /*
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

        // TODO: print N  W  S  E
        // TODO: print 12 9  6  3
        // TODO: print lights on seperate rows
        DEBUG_PRINT(F(": "));
        for (int i = 0; i < num_LEDs; i++) {
          if (leds[i]) {
            // TODO: better logging?
            DEBUG_PRINT(F("X"));
          } else {
            DEBUG_PRINT(F("O"));
          }
        }

        DEBUG_PRINT(F(" | ms since last frame="));
        DEBUG_PRINTLN(millis() - last_frame);

        last_frame = millis();
    #endif

    // display the colors
    FastLED.show();

    // set g_hue based on shared timer
    g_hue = network_ms / (3 * 1000 / frames_per_second);
  }
}
