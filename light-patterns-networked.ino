// just hammering out some ideas. no real structure yet

// time based pattern spread out across everyone's LEDs
// TODO: change this so that location shift and color shift are different values
// todo: this is kind of a cheater way to circle. maybe track the 3 bars separately so it doesn't look like it stutters
// when the color changes
void networkedLights() {
  static const int network_LEDs = num_LEDs * num_peers;
  static const int peer_shift = my_peer_id * num_LEDs;
  static const int ms_per_led = 4 * 1000 / frames_per_second;   // 4 frames
  static int shift;

  fadeToBlackBy(leds, num_LEDs, LED_FADE_RATE);
  //fadeLightBy(leds, num_LEDs, LED_FADE_RATE);

  // shift the pattern based on peer id and then shift more slowly over time
  shift = peer_shift + network_ms / ms_per_led;

  // i is our local ids for lights
  for (int i = 0; i < num_LEDs; i++) {
    int network_i = (i + shift) % network_LEDs;

    // light up every Nth light. the others will dim
    if (network_i % 5 == 0) {
      // TODO: use a color pallet?
      // TODO: this spreads the whole rainbow across all 4. do we want to change color slower than that?
      // TODO: do something with saturation, too?
      int color_value = map(network_i, 0, network_LEDs - 1, 0, 255);
      // TODO: cycle brightness instead of doing fixed full so that the flicker is less
      // TODO: or blend?
      leds[i] = CHSV(color_value, 230, 230);
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
