
// https://forum.arduino.cc/index.php?topic=98147.msg736165#msg736165
int rad2deg(const long rad) { return rad * 57296 / 1000; }

// https://forum.arduino.cc/index.php?topic=98147.msg736165#msg736165
int deg2rad(const long deg) { return deg * 1000 / 57296; }

// http://forum.arduino.cc/index.php?topic=393511.msg3232854#msg3232854
// find the bearing and distance in meters from point 1 to 2, using the equirectangular approximation
// lat and lon are degrees*1.0e6, 10 cm precision
// TODO: i'm pretty sure that these units are wrong. without dividing distance, it said they were 100m away from eachother
float course_to(const long lat1, const long lon1, const long lat2, const long lon2, float *distance) {
  float dlam, dphi, radius = 6371000.0;

  dphi = deg2rad(lat1 + lat2) * 0.5e-6; // average latitude in radians
  float cphi = cos(dphi);

  dphi = deg2rad(lat2 - lat1) * 1.0e-6; // differences in degrees (to radians)
  dlam = deg2rad(lon2 - lon1) * 1.0e-6;

  dlam *= cphi; // correct for latitude

  // calculate bearing and offset for true north -> magnetic north
  float magnetic_bearing = rad2deg(atan2(dlam, dphi)) + g_magnetic_declination;

  // wrap around
  if (magnetic_bearing < 0) {
    magnetic_bearing += 360.0;
  } else if (magnetic_bearing >= 360) {
    magnetic_bearing -= 360.0;
  }

  // TODO: not sure about units here
  *distance = radius * sqrt(dphi * dphi + dlam * dlam) / 100;
  return magnetic_bearing;
}

// compare compass points
bool firstIsBrighter(CHSV first, CHSV second) { return first.value > second.value; }

void updateCompassPoints(CompassMode compass_mode) {
  // clear past compass points
  // TODO: this isn't very efficient since it recalculates everything every time, but it works
  for (int i = 0; i < inner_ring_size; i++) {
    next_inner_compass_point[i] = 0;
  }
  for (int i = 0; i < outer_ring_size; i++) {
    next_outer_compass_point[i] = 0;
  }
  next_status_bar_id = 0;

  // compass points go COUNTER-clockwise to match LEDs!
  // add north to inner ring
  inner_compass_points[0][next_inner_compass_point[0]].hue = 0;
  inner_compass_points[0][next_inner_compass_point[0]].saturation = 255;
  inner_compass_points[0][next_inner_compass_point[0]].value = 255;
  next_inner_compass_point[0]++;

  // add north to outer ring
  outer_compass_points[0][next_outer_compass_point[0]].hue = 0;
  outer_compass_points[0][next_outer_compass_point[0]].saturation = 255;
  outer_compass_points[0][next_outer_compass_point[0]].value = 255;
  next_outer_compass_point[0]++;

  // add low battery indicator to the status bar
  switch (checkBattery()) {
  case BATTERY_DEAD:
  case BATTERY_LOW:
    status_bar[next_status_bar_id].hue = 0;
    status_bar[next_status_bar_id].saturation = 255;
    status_bar[next_status_bar_id].value = 64; // TODO: how bright?
    next_status_bar_id++;
    break;
  }

  // TODO: make sure we don't overflow next_status_bar_id (do that in add_color_to_leds helper)
  status_bar[next_status_bar_id].hue = compass_messages[my_peer_id].hue;
  status_bar[next_status_bar_id].saturation = compass_messages[my_peer_id].saturation;
  status_bar[next_status_bar_id].value = 128;

  // TODO: this is very verbose
  /*
  DEBUG_PRINT(F("Adding status light for self @ "));
  DEBUG_PRINT(compass_messages[my_peer_id].latitude);
  DEBUG_PRINT(", ");
  DEBUG_PRINT(compass_messages[my_peer_id].longitude);
  DEBUG_PRINT(F("; Hue: "));
  DEBUG_PRINT(status_bar[next_status_bar_id].hue);
  DEBUG_PRINT(F("; Saturation: "));
  DEBUG_PRINT(status_bar[next_status_bar_id].saturation);
  DEBUG_PRINT(F("; Value: "));
  DEBUG_PRINTLN(status_bar[next_status_bar_id].value);
  */

  next_status_bar_id++;

  // add points to the compass
  // TODO: sort compass_pins
  // TODO: pass compass_pins (compass_locations/saved_locations) to addCompassPoints function
  switch (compass_mode) {
  case COMPASS_FRIENDS:
    addCompassPointsForFriends();
    break;
  case COMPASS_PLACES:
    addCompassPointsForPlaces();
    break;
  }
}

// todo: this shows "SmartCompassLocationMessages." Be consistent about naming
// todo: DRY this up with compass locations
void addCompassPointsForFriends() {
  float peer_distance;    // meters
  float magnetic_bearing; // degrees
  int compass_point_id = 0, peer_brightness = 0;

  for (int i = 0; i < num_peers; i++) {
    if (compass_messages[i].hue == 0) {
      // skip the peer if we don't have any color data for them
      continue;
    }
    if (i == my_peer_id) {
      // don't show yourself on the compass ring.
      continue;
    }

    // TODO: if the message is older than 10 minutes, set hue to 0 and continue

    magnetic_bearing = course_to(compass_messages[my_peer_id].latitude, compass_messages[my_peer_id].longitude,
                                 compass_messages[i].latitude, compass_messages[i].longitude, &peer_distance);

    // convert distance to brightness. the closer, the brighter
    // TODO: scurve instead of linear? use fastLED helpers
    // TODO: tune this
    // TODO: if peer data is old, blink or something
    peer_brightness = map(constrain(peer_distance, min_peer_distance, max_peer_distance), 0, max_peer_distance, 128, 255);

    // TODO: this is SUPER verbose
    /*
    DEBUG_PRINT(F("Adding compass point for "));
    DEBUG_PRINT(i);
    DEBUG_PRINT(F(" @ "));
    DEBUG_PRINT(compass_messages[i].latitude);
    DEBUG_PRINT(F(", "));
    DEBUG_PRINT(compass_messages[i].longitude);
    DEBUG_PRINT(F(" Bearing: "));
    DEBUG_PRINT(magnetic_bearing);
    DEBUG_PRINT(F("; Distance: "));
    DEBUG_PRINT(peer_distance);
    DEBUG_PRINT(F("; Hue: "));
    DEBUG_PRINT(compass_messages[i].hue);
    DEBUG_PRINT(F("; Saturation: "));
    DEBUG_PRINT(compass_messages[i].saturation);
    DEBUG_PRINT(F("; Brightness: "));
    DEBUG_PRINTLN(peer_brightness);
    */

    // circle 0 -> 360 should go clockwise, but the outer ring lights are wired counter-clockwise
    if (peer_distance <= min_peer_distance) {
      // close peer! add to status bar

      // check that next_outer_compass_point[compass_point_id] is a safe value
      if (next_status_bar_id >= status_bar_size) {
        // TODO: how should we handle too many nearby peers?
        DEBUG_PRINTLN("TOO MANY STATUSES!");
        continue;
      }

      status_bar[next_status_bar_id].hue = compass_messages[i].hue;
      status_bar[next_status_bar_id].saturation = compass_messages[i].saturation;
      status_bar[next_status_bar_id].value = peer_brightness;

      next_status_bar_id++;
    } else if (peer_distance <= max_peer_distance / 2) {
      // inner ring
      compass_point_id = map(magnetic_bearing, 0, 360, 0, inner_ring_size) % inner_ring_size;

      // check that next_inner_compass_point[compass_point_id] is a safe value
      if (next_inner_compass_point[compass_point_id] >= max_compass_points) {
        // TODO: how should we handle too many peers?
        DEBUG_PRINTLN("TOO MANY INNER POINTS!");
        continue;
      }

      inner_compass_points[compass_point_id][next_inner_compass_point[compass_point_id]].hue = compass_messages[i].hue;
      inner_compass_points[compass_point_id][next_inner_compass_point[compass_point_id]].saturation = compass_messages[i].saturation;
      inner_compass_points[compass_point_id][next_inner_compass_point[compass_point_id]].value = peer_brightness;

      next_inner_compass_point[compass_point_id]++;
    } else {
      // outer ring
      compass_point_id = map(magnetic_bearing, 0, 360, outer_ring_size, 0) % outer_ring_size;

      // check that next_outer_compass_point[compass_point_id] is a safe value
      if (next_outer_compass_point[compass_point_id] >= max_compass_points) {
        // TODO: how should we handle too many peers?
        DEBUG_PRINTLN("TOO MANY OUTER POINTS!");
        continue;
      }

      outer_compass_points[compass_point_id][next_outer_compass_point[compass_point_id]].hue = compass_messages[i].hue;
      outer_compass_points[compass_point_id][next_outer_compass_point[compass_point_id]].saturation = compass_messages[i].saturation;
      outer_compass_points[compass_point_id][next_outer_compass_point[compass_point_id]].value = peer_brightness;

      next_outer_compass_point[compass_point_id]++;
    }
  }

  /*
  // TODO: this is broken
  for (int i = 0; i < num_LEDs; i++) {
    // TODO: sort every time? i feel like there is a smarter way to insert. it probably doesn't matter
    sortArray(compass_points[i], next_compass_point[i], firstIsBrighter);
  }
  */
}

// todo: this shows "SmartCompassPinMessages." Be consistent about naming
// TODO: DRY this up. take the compass_pins array as an argument and then have one array for friends and one for
void addCompassPointsForPlaces() {
  // always show at least 1 light per color. if there are more than, show the closest X
  // and skip any pins that are Red. we use Red as a mark for deletion

  static const int num_colors = ARRAY_SIZE(pin_colors);

  // TODO: don't count red. those are ignored entirely
  int points_per_color[num_colors] = {0};
  int colors_left = num_colors;

  for (int i = 0; i < next_compass_pin; i++) {
    // TODO: instead of using compass_pins[i], use compass_pins[sorted_compass_pins[i]] (sort by distance)

    if (compass_pins[i].distance < 0) {
      // skip pins with invalid distances
      continue;
    }

    // find the pin_color_id for this compass_pin's color
    // TODO: why don't we just store that instead of the color? that would save this lookup
    int pin_color_id;
    for (pin_color_id = 0; pin_color_id < num_colors; pin_color_id++) {
      if (compass_pins[i].hue == pin_colors[pin_color_id].hue and
          compass_pins[i].saturation == pin_colors[pin_color_id].saturation) {
        // color match!
        break;
      }
    }

    if (pin_color_id == delete_pin_color_id or pin_color_id >= num_colors) {
      // TODO: log something here? we didn't find a matching color
      continue;
    }

    if (points_per_color[pin_color_id] >= max_points_per_color) {
      // this color has too many points on the compass already
      continue;
    }

    points_per_color[pin_color_id]++;

    if (points_per_color[pin_color_id] == max_points_per_color) {
      colors_left--;
    }

    // convert distance to brightness. the closer, the brighter
    // TODO: scurve instead of linear? use fastLED helpers?
    // TODO: tune this. whats a good minimum on that will still work when batteries are low
    // TODO: if peer data is old, blink or something?
    int peer_brightness =
        map(constrain(compass_pins[i].distance, min_peer_distance, max_peer_distance), 0, max_peer_distance, 128, 255);

    // TODO: distance is being calculated wrong. print lat, long, distance and bearing here for debug purposes

    // TODO: debug program to double check that this is looping the correct way around the LED
    // circle 0 -> 360 should go clockwise, but the lights are wired counter-clockwise
    if (compass_pins[i].distance <= min_peer_distance) {
      // use the status bar to show nearby peers

      if (next_status_bar_id >= status_bar_size) {
        // TODO: how should we handle too many nearby peers?
        DEBUG_PRINTLN("TOO MANY STATUSES!");
        continue;
      }

      status_bar[next_status_bar_id].hue = compass_pins[i].hue;
      status_bar[next_status_bar_id].saturation = compass_pins[i].saturation;
      status_bar[next_status_bar_id].value = peer_brightness;

      next_status_bar_id++;
    } else if (compass_pins[i].distance <= max_peer_distance / 2) {
      // inner ring
      int compass_point_id = map(compass_pins[i].magnetic_bearing, 0, 360, 0, inner_ring_size) % inner_ring_size;

      // check that next_inner_compass_point[compass_point_id] is a safe value
      if (next_inner_compass_point[compass_point_id] >= max_compass_points) {
        // TODO: how should we handle too many peers?
        DEBUG_PRINTLN("TOO MANY INNER POINTS!");
        continue;
      }

      inner_compass_points[compass_point_id][next_inner_compass_point[compass_point_id]].hue = compass_pins[i].hue;
      inner_compass_points[compass_point_id][next_inner_compass_point[compass_point_id]].saturation = compass_pins[i].saturation;
      inner_compass_points[compass_point_id][next_inner_compass_point[compass_point_id]].value = peer_brightness;

      next_inner_compass_point[compass_point_id]++;
    } else {
      // outer ring
      int compass_point_id = map(compass_pins[i].magnetic_bearing, 0, 360, 0, outer_ring_size) % outer_ring_size;

      // check that next_outer_compass_point[compass_point_id] is a safe value
      if (next_outer_compass_point[compass_point_id] >= max_compass_points) {
        // TODO: how should we handle too many peers?
        DEBUG_PRINTLN("TOO MANY OUTER POINTS!");
        continue;
      }

      outer_compass_points[compass_point_id][next_outer_compass_point[compass_point_id]].hue = compass_pins[i].hue;
      outer_compass_points[compass_point_id][next_outer_compass_point[compass_point_id]].saturation = compass_pins[i].saturation;
      outer_compass_points[compass_point_id][next_outer_compass_point[compass_point_id]].value = peer_brightness;

      next_outer_compass_point[compass_point_id]++;
    }

    // all colors have their maximum number of points left on the compass
    if (colors_left <= 0) {
      break;
    }
  }
}

// todo: be more consistent about naming
int getCompassPinId(long latitude, long longitude) {
  int compass_pin_id = -1;

  // TODO: loop over existing pins. if distance <10, return pin id. if none <10, increment and return next_compass_pin_id
  // TODO: this should be fast if we sort the pins by distance and do a smart search.

  return compass_pin_id;
}

// todo: this uses "SmartCompassPinMessages." Be consistent about naming
void setCompassPin(int pin_id, CHSV *color, long latitude, long longitude) {
  if (pin_id < 0) {
    DEBUG_PRINTLN("ERROR Setting compass_pins with a negative index!");
    return;
  }

  compass_pins[pin_id].hue = color->hue;
  compass_pins[pin_id].saturation = color->saturation;

  compass_pins[pin_id].latitude = latitude;
  compass_pins[pin_id].longitude = longitude;

  // TODO: not sure about this. maybe only set if we aren't given a time?
  compass_pins[pin_id].last_updated_at = getGPSTime();

  // TODO: sort an index of compass_pins by distance?
}

// TODO: make the naming of compass_pins and saved_locations consistent
void saveCompassPin(const int pin_id) {
  SavedLocationData saved_location_data;

  saved_location_data.last_updated_at = compass_pins[pin_id].last_updated_at;
  saved_location_data.latitude = compass_pins[pin_id].latitude;
  saved_location_data.longitude = compass_pins[pin_id].longitude;
  saved_location_data.hue = compass_pins[pin_id].hue;
  saved_location_data.saturation = compass_pins[pin_id].saturation;

  openDatabase();

  EDB_Status result;

  if (compass_pins[pin_id].database_id < 0) {
    result = db.appendRec(EDB_REC saved_location_data);

    if (result == EDB_OK) {
      compass_pins[pin_id].database_id = db.count();
    }
  } else {
    result = db.updateRec(compass_pins[pin_id].database_id, EDB_REC saved_location_data);
  }

  if (result != EDB_OK) {
    printError(result);
    // TODO: what should we do here?
  }
  Serial.println("DONE");

  closeDatabase();
}

void loadCompassPins() {
  openDatabase();

  EDB_Status result;
  SavedLocationData saved_location_data;

  for (int recno = 1; recno <= db.count(); recno++) {
    if (next_compass_pin >= MAX_PINS) {
      break;
    }

    result = db.readRec(recno, EDB_REC saved_location_data);

    if (result != EDB_OK) {
      printError(result);
      break;
    }

    compass_pins[next_compass_pin].database_id = recno;

    compass_pins[next_compass_pin].transmitted = false;
    compass_pins[next_compass_pin].last_updated_at = saved_location_data.last_updated_at;
    compass_pins[next_compass_pin].latitude = saved_location_data.latitude;
    compass_pins[next_compass_pin].longitude = saved_location_data.longitude;

    // TODO: what should we set these to? until we have a gps fix, we can't calculate them
    compass_pins[next_compass_pin].distance = 0;
    compass_pins[next_compass_pin].magnetic_bearing = 0;

    compass_pins[next_compass_pin].hue = saved_location_data.hue;
    compass_pins[next_compass_pin].saturation = saved_location_data.saturation;

    next_compass_pin++;
  }

  closeDatabase();
}
