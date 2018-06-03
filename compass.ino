
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

const int max_compass_points = max_peers + 1;
CHSV compass_points[num_LEDs][max_compass_points];
int next_compass_point[num_LEDs] = {0};

void updateCompassPoints() {
  // clear past compass points
  // TODO: this isn't very efficient since it recalculates everything every time
  for (int i = 0; i < num_LEDs; i++) {
    next_compass_point[i] = 0; // TODO: is this the right syntax?
  }

  // compass points go COUNTER-clockwise to match LEDs!
  // add north
  compass_points[0][next_compass_point[0]] = CHSV(0, 255, 255);
  next_compass_point[0]++;

  // add east (TODO: remove this when done debugging)
  compass_points[12][next_compass_point[12]] = CHSV(64, 255, 255);
  next_compass_point[12]++;

  // add south (TODO: remove this when done debugging)
  compass_points[8][next_compass_point[8]] = CHSV(128, 255, 255);
  next_compass_point[8]++;

  // add west (TODO: remove this when done debugging)
  compass_points[4][next_compass_point[4]] = CHSV(192, 255, 255);
  next_compass_point[4]++;

  for (int i = 0; i < num_peers; i++) {
    if (!compass_messages[i].saturation) {
      // skip the peer if we don't have any color data for them
      continue;
    }
    if (i == my_peer_id) {
      // don't show yourself
      continue;
    }

    float peer_distance; // meters
    float magnetic_bearing = course_to(compass_messages[my_peer_id].latitude, compass_messages[my_peer_id].longitude,
                                       compass_messages[i].latitude, compass_messages[i].longitude, &peer_distance);

    if (peer_distance < 10) {
      // TODO: what should we do for really close peers?
      continue;
    }

    // TODO: double check that this is looping the correct way around the LED
    // circle 0 -> 360 should go clockwise, but the lights are wired counter-clockwise
    // TODO: i don't think mod is needed here
    int compass_point_id = map(magnetic_bearing, 0, 360, num_LEDs, 0) % num_LEDs;

    // convert distance to brightness. the closer, the brighter
    // TODO: scurve instead of linear? use fastLED helpers
    // TODO: tune this
    int peer_brightness = map(min(max_peer_distance, peer_distance), 0, max_peer_distance, 10, 255);

    compass_points[compass_point_id][next_compass_point[compass_point_id]] =
        CHSV(compass_messages[i].hue, compass_messages[i].saturation, peer_brightness);
    next_compass_point[compass_point_id]++;
  }

  /*
  // TODO: this is broken
  for (int i = 0; i < num_LEDs; i++) {
    // TODO: sort every time? i feel like there is a smarter way to insert. it
  probably doesn't matter
    // TODO: i think this is broken
    sortArray(compass_points[i], next_compass_point[i], firstIsBrighter);
  }
  */
}
