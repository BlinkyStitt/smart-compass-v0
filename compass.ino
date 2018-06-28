
// https://forum.arduino.cc/index.php?topic=98147.msg736165#msg736165
int rad2deg(long rad) { return rad * 57296 / 1000; }

// https://forum.arduino.cc/index.php?topic=98147.msg736165#msg736165
int deg2rad(long deg) { return deg * 1000 / 57296; }

// http://forum.arduino.cc/index.php?topic=393511.msg3232854#msg3232854
// find the bearing and distance in meters from point 1 to 2, using the equirectangular approximation
// lat and lon are degrees*1.0e6, 10 cm precision
// TODO: I copied this from the internet. make sure it actually works
// TODO: what are the units of the distance? meters?
float course_to(long lat1, long lon1, long lat2, long lon2, float *distance) {
  float dlam, dphi, radius = 6371000.0;

  dphi = deg2rad(lat1 + lat2) * 0.5e-6; // average latitude in radians
  float cphi = cos(dphi);

  dphi = deg2rad(lat2 - lat1) * 1.0e-6; // differences in degrees (to radians)
  dlam = deg2rad(lon2 - lon1) * 1.0e-6;

  dlam *= cphi; // correct for latitude

  // calculate bearing and offset for true north -> magnetic north
  float magnetic_bearing = rad2deg(atan2(dlam, dphi)) + magnetic_declination;

  // wrap around
  if (magnetic_bearing < 0) {
    magnetic_bearing += 360.0;
  } else if (magnetic_bearing >= 360) {
    magnetic_bearing -= 360.0;
  }

  *distance = radius * sqrt(dphi * dphi + dlam * dlam);
  return magnetic_bearing;
}

// compare compass points
bool firstIsBrighter(CHSV first, CHSV second) { return first.value > second.value; }

// TODO: CHSV nearby_points[]

void updateCompassPoints(CompassMode compass_mode) {
  // clear past compass points
  // TODO: this isn't very efficient since it recalculates everything every time
  for (int i = 0; i < inner_ring_size; i++) {
    next_inner_compass_point[i] = 0;
  }
  for (int i = 0; i < outer_ring_size; i++) {
    next_outer_compass_point[i] = 0;
  }

  // compass points go COUNTER-clockwise to match LEDs!
  // add north to inner ring
  inner_compass_points[0][next_inner_compass_point[0]] = CHSV(0, 255, 255);
  next_inner_compass_point[0]++;

  // add north to outer ring
  outer_compass_points[0][next_outer_compass_point[0]] = CHSV(0, 255, 255);
  next_outer_compass_point[0]++;

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
    if (!compass_messages[i].hue) {
      // skip the peer if we don't have any color data for them
      continue;
    }
    if (i == my_peer_id) {
      // don't show yourself (or maybe just show it on the status bar so you can see your own color?
      continue;
    }

    magnetic_bearing = course_to(compass_messages[my_peer_id].latitude, compass_messages[my_peer_id].longitude,
                                 compass_messages[i].latitude, compass_messages[i].longitude, &peer_distance);

    // convert distance to brightness. the closer, the brighter
    // TODO: scurve instead of linear? use fastLED helpers
    // TODO: tune this
    // TODO: if peer data is old, blink or something
    peer_brightness = map(constrain(peer_distance, min_peer_distance, max_peer_distance), 0, max_peer_distance, 60, 255);

    // TODO: double check that this is looping the correct way around the LED
    // circle 0 -> 360 should go clockwise, but the outer ring lights are wired counter-clockwise
    if (peer_distance <= min_peer_distance) {
      // TODO: what should we do for really close peers? don't just hide them. add to a 8 led strip bar
    } else if (peer_distance <= max_peer_distance / 2) {
      // inner ring
      compass_point_id = map(magnetic_bearing, 0, 360, 0, inner_ring_size) % inner_ring_size;

      inner_compass_points[compass_point_id][next_inner_compass_point[compass_point_id]] =
          CHSV(compass_messages[i].hue, compass_messages[i].saturation, peer_brightness);

      next_inner_compass_point[compass_point_id]++;
    } else {
      // outer ring
      compass_point_id = map(magnetic_bearing, 0, 360, outer_ring_size, 0) % outer_ring_size;

      outer_compass_points[compass_point_id][next_outer_compass_point[compass_point_id]] =
          CHSV(compass_messages[i].hue, compass_messages[i].saturation, peer_brightness);

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

    int j;
    for (j = 0; j < num_colors; j++) {
      if (compass_pins[i].color == pin_colors[j]) {
        break;
      }
    }

    if (j == delete_pin_color_id or j >= num_colors) {
      // TODO: log something here? we didn't find a matching color
      continue;
    }

    if (points_per_color[j] >= max_points_per_color) {
      // this color has too many points on the compass already
      continue;
    }

    points_per_color[j]++;

    if (points_per_color[j] == max_points_per_color) {
      colors_left--;
    }

    // convert distance to brightness. the closer, the brighter
    // TODO: scurve instead of linear? use fastLED helpers
    // TODO: tune this. whats a good minimum on that will still work when batteries are low
    // TODO: if peer data is old, blink or something
    int peer_brightness =
        map(constrain(compass_pins[i].distance, min_peer_distance, max_peer_distance), 0, max_peer_distance, 60, 255);

    // TODO: double check that this is looping the correct way around the LED
    // circle 0 -> 360 should go clockwise, but the lights are wired counter-clockwise
    if (compass_pins[i].distance <= min_peer_distance) {
      // TODO: add to a 8 led strip bar
    } else if (compass_pins[i].distance <= max_peer_distance / 2) {
      // inner ring
      int compass_point_id = map(compass_pins[i].magnetic_bearing, 0, 360, 0, inner_ring_size) % inner_ring_size;

      inner_compass_points[compass_point_id][next_inner_compass_point[compass_point_id]] =
          CHSV(compass_pins[i].color.hue, compass_pins[i].color.saturation, peer_brightness);

      // TODO: check next_inner_compass_point for overflow
      next_inner_compass_point[compass_point_id]++;
    } else {
      // outer ring
      int compass_point_id = map(compass_pins[i].magnetic_bearing, 0, 360, 0, outer_ring_size) % outer_ring_size;

      outer_compass_points[compass_point_id][next_outer_compass_point[compass_point_id]] =
          CHSV(compass_pins[i].color.hue, compass_pins[i].color.saturation, peer_brightness);

      // TODO: check next_outer_compass_point for overflow
      next_outer_compass_point[compass_point_id]++;
    }

    // all colors have their maximum number of points left on the compass
    if (colors_left <= 0) {
      break;
    }
  }
}

// todo: this uses "SmartCompassPinMessages." Be consistent about naming
int getCompassPinId(long latitude, long longitude) {
  // TODO: loop over existing pins. if distance <10, return pin id. if none <10, increment and return last pin id
  // TODO: add something during updateLights that adds this pin color to the status bar
  return -1;
}

// todo: this uses "SmartCompassPinMessages." Be consistent about naming
void setCompassPin(int pin_id, CHSV color, long latitude, long longitude) {
  // TODO: write this
  if (pin_id < 0) {
    DEBUG_PRINTLN("ERROR saving pin with invalid ID");
  }

  // todo: do something to compass_pins

  // if pin changed, don't set compass_pins[pin_id].transmitted = false. we will do that once its finished being modified
}
