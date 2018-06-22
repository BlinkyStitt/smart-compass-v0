
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

  // add points for
  switch (compass_mode) {
  case COMPASS_FRIENDS:
    addCompassPointsForFriends();
    break;
  case COMPASS_PLACES:
    addCompassPointsForPlaces();
    break;
  }
}

void addCompassPointsForFriends() {
  float peer_distance; // meters
  float magnetic_bearing;  // degrees
  int compass_point_id = 0, peer_brightness = 0;

  for (int i = 0; i < num_peers; i++) {
    if (!compass_messages[i].saturation) {
      // skip the peer if we don't have any color data for them
      continue;
    }
    if (i == my_peer_id) {
      // don't show yourself (or maybe just show it on the status bar so you can see your own color?
      continue;
    }

    magnetic_bearing = course_to(compass_messages[my_peer_id].latitude, compass_messages[my_peer_id].longitude,
                                 compass_messages[i].latitude, compass_messages[i].longitude,
                                 &peer_distance);

    // convert distance to brightness. the closer, the brighter
    // TODO: scurve instead of linear? use fastLED helpers
    // TODO: tune this
    // TODO: if peer data is old, blink or something
    peer_brightness = map(constrain(peer_distance, min_peer_distance, max_peer_distance), 0, max_peer_distance, 30, 255);

    // TODO: double check that this is looping the correct way around the LED
    // circle 0 -> 360 should go clockwise, but the lights are wired counter-clockwise
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
      compass_point_id = map(magnetic_bearing, 0, 360, 0, outer_ring_size) % outer_ring_size;

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

void addCompassPointsForPlaces() {
  // TODO: write this
  // TODO: always show at least 1 light per color. if there are more than, show the closest X
}

void setPin(int pin_id, CHSV color, long latitude, long longitude) {
  // TODO: write this
  if (pin_id < 0) {
    DEBUG_PRINTLN("ERROR saving pin with invalid ID");
  }

  // TODO: search for a nearby pin. if it doesn't exist, increment num_pins
}
