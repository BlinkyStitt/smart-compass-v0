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

  static const unsigned int min_distance= 5;
  static const unsigned int max_distance = num_LEDs;  // num_LEDs + a few for fade rate
  static unsigned int distance = max_distance / 2;  // max(min_distance, max_distance / (1+nearby_peers));  // min 5, max numLEDs + a few for fade rate
  // TODO: change density based on how many peers are nearby?

  // todo: fade slower (32) for larger distances
  fadeToBlackBy(leds, num_LEDs, 32);

  // shift the pattern based on peer id and then shift more slowly over time
  shift = peer_shift + network_ms / ms_per_led;

  // i is our local ids for lights
  for (int i = 0; i < num_LEDs; i++) {
    int network_i = (i + shift) % network_LEDs;

    // light up every Nth light. the others will fade
    if (network_i % distance == 0) {
      // TODO: use a color pallet?
      // TODO: this spreads the whole rainbow across all 4. do we want to change color slower than that?
      // TODO: do something with saturation, too?

      // TODO: without the constrain, it sometimes crashed. it shouldn't be needed if i did the map right
      // TODO: i think maybe changing the type to byte would be a better fix since -1 or 256 should wrap
      int color_value = constrain(map(network_i, 0, network_LEDs - 1, 0, 255), 0, 255);

      // TODO: add or blend instead of set?
      leds[i] = CHSV(color_value, 230, 200);
    }
  }
}
