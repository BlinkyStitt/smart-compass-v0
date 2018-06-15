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
  // TODO: add a second, larger ring
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
