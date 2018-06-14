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

void updateLightsForCompass() {
  updateCompassPoints();

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

void updateLightsForClock() {
  // turn the time into a watch face with just an hour hand

  // TODO: do we care about gpsMs? we only have 16 lights of output
  int adjusted_seconds = second();  // + (gpsMs % 1000) / 1000;

  int adjusted_minute = minute() + adjusted_seconds / 60.0;

  // we include the minute_led_ids here in case of fractional timezones. we will likely drop the minute_led_id
  int adjusted_hour = hour() + time_zone_offset + adjusted_minute / 60.0;

  if (adjusted_hour < 0) {
    adjusted_hour += 12;
  } else if (adjusted_hour >= 12) {
    adjusted_hour -= 12;
  }

  DEBUG_PRINT("time: ");
  DEBUG_PRINT(adjusted_hour);
  DEBUG_PRINT(":");
  DEBUG_PRINT(adjusted_minute);
  DEBUG_PRINT(":");
  DEBUG_PRINTLN(adjusted_seconds);

  // TODO: make sure this loops the right way once it is wired.
  //int hour_led_id = map(adjusted_hour, 0, 12, 16, 0) % 16;
  int hour_led_id;
  switch (adjusted_hour) {
  case 0:
    hour_led_id = 0;
    break;
  case 1:
    hour_led_id = 15;
    break;
  case 2:
    hour_led_id = 13;
    break;
  case 3:
    hour_led_id = 12;
    break;
  case 4:
    hour_led_id = 11;
    break;
  case 5:
    hour_led_id = 9;
    break;
  case 6:
    hour_led_id = 8;
    break;
  case 7:
    hour_led_id = 7;
    break;
  case 8:
    hour_led_id = 5;
    break;
  case 9:
    hour_led_id = 4;
    break;
  case 10:
    hour_led_id = 3;
    break;
  case 11:
    hour_led_id = 1;
    break;
  }

  int minute_led_id = map(adjusted_minute, 0, 60, 16, 0) % 16;
  int second_led_id = map(adjusted_seconds, 0, 60, 16, 0) % 16;

  /*
  DEBUG_PRINT("led_ids hour ,minute, second: ");
  DEBUG_PRINT(hour_led_id);
  DEBUG_PRINT(" ");
  DEBUG_PRINT(minute_led_id);
  DEBUG_PRINT(" ");
  DEBUG_PRINTLN(second_led_id);
  */

  // TODO: I'm not sure what color the noon marker should be or if we even need one
  // TODO: what colors should the leds be?
  // TODO: i'm not sure i like how i'm handling overlapping
  // TODO: blink instead of full brightness?
  for (int i = 0; i < num_LEDs; i++) {
    if (i == second_led_id) {
      leds[i] = CRGB::Blue;
    } else if (i == minute_led_id) {
      leds[i] = CRGB::Yellow;
    } else if (i == hour_led_id) {
      leds[i] = CRGB::Red;
    }
    // everything starts at least a little dimmed
    // lights that aren't part of the current time will quickly fade to black
    // this makes for a smooth transition from other patterns
    leds[i].fadeToBlackBy(90);
  }
}

byte last_orientation = ORIENTED_PORTRAIT;
byte current_orientation;

void updateLights() {
  // update the led array every frame
  EVERY_N_MILLISECONDS(1000 / frames_per_second) {
    // decrease overall brightness if battery is low
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

    current_orientation = getOrientation();
    switch (current_orientation) {
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
    case ORIENTED_USB_DOWN:
      // TODO: config for bathroom
      //break;
    case ORIENTED_USB_UP:
      // TODO: config for home
      //break;
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
