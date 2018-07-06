// just hammering out some ideas. no real structure yet

// time based pattern spread out across everyone's LEDs
// TODO: change this so that location shift and color shift are different values
void networkedLights() {
  static const int network_LEDs = num_LEDs * num_peers;
  static const int peer_shift = my_peer_id * num_LEDs;
  static const int ms_per_led = 4 * 1000 / frames_per_second;
  static int shift;

  fadeToBlackBy(leds, num_LEDs, LED_FADE_RATE);

  // shift the pattern based on peer id and then shift more slowly over time
  shift = (peer_shift + network_ms / ms_per_led) % network_LEDs;

  // i is our local ids for lights
  for (int i = 0; i < num_LEDs; i++) {
    int shifted_i = i + shift;

    // light up every Nth light. the others will dim
    if (shifted_i % 5 == 0) {
      // TODO: use a color pallet?
      // TODO: shift the color more?
      int color_value = map((i + shift) % network_LEDs, 0, network_LEDs, 0, 255);
      leds[i] = CHSV(color_value, 255, 255);
    }
  }
}

/*
// stretched rainbow pattern where the start is moved around
void networkedLights2() {
  static const int network_LEDs = num_LEDs * num_peers;


  // chunk the time up such that every led gets an equal amount of time as the origin?
  origin_id = network_ms / (origin_frames * 1000/frames_per_second) % network_LEDs;

  ...
}

// r, g, and b heading down the length at different speeds. use blending

// r, g, and b heading down the length at the same speed

// breathing in sync, but with different colors

// pattern with only half the lights on

// TODO: if battery low add a red light to the status bar. if battery dead, add 2 read lights on the status bar
*/