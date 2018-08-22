/* light patterns */

void flashlight() {
  static int turn_on_id = 0;

  // TODO: tune this
  // rotate the LEDs slowly
  EVERY_N_SECONDS(60) {
    turn_on_id++;

    if (turn_on_id >= flashlight_density) {
      turn_on_id = 0;
    }
  }

  // smoothly transition from other patterns
  // TODO: would be nice to call fade on just the status bar here
  fadeToBlackBy(leds, num_LEDs, LED_FADE_RATE);

  for (int i = inner_ring_start; i < outer_ring_end; i++) {
    if (i % flashlight_density == turn_on_id) {
      // TODO: slowly turn on (at LED_FADE_RATE?) instead of jumping to full brightness?
      leds[i] = CRGB::White;
    }
  }
}

// https://gist.github.com/kriegsman
void sinelon() {
  // a colored dot sweeping back and forth, with fading trails
  fadeToBlackBy(leds, num_LEDs, LED_FADE_RATE);

  int pos = beatsin16(13, 0, num_LEDs);
  leds[pos] += CHSV(g_hue, 255, 192);
}

// TODO: circle with multiple colors
// TODO: do inner and outer ring at the same time
// TODO: this is wrong
void circle() {
  int ms_per_led = 3 * 1000 / frames_per_second; // 3 frames
  int pos = (network_ms / ms_per_led) % (outer_ring_end - inner_ring_start) + inner_ring_start;

  // fade everything
  fadeToBlackBy(leds, num_LEDs, LED_FADE_RATE);

  // todo: what saturation and value
  leds[pos] = CHSV(g_hue, 255, 255);
}

// This function draws rainbows with an ever-changing, widely-varying set of parameters.
// https://gist.github.com/kriegsman/964de772d64c502760e5
void pride() {
  static uint16_t sPseudotime = 0;
  static uint16_t sLastMillis = 0;
  static uint16_t sHue16 = 0;

  // TODO: figure out what all these numbers do and make it look good on two concentric rings
  uint8_t sat8 = beatsin88(87, 220, 250);
  uint8_t brightdepth = beatsin88(341, 96, 224);
  uint16_t brightnessthetainc16 = beatsin88(203, (25 * 256), (40 * 256));
  uint8_t msmultiplier = beatsin88(147, 23, 60);

  uint16_t hue16 = sHue16; // g_hue * 256;
  uint16_t hueinc16 = beatsin88(113, 1, 3000);

  uint16_t ms = network_ms; // this should keep everyone's lights looking the same
  uint16_t deltams = ms - sLastMillis;
  sLastMillis = ms;
  sPseudotime += deltams * msmultiplier;
  sHue16 += deltams * beatsin88(400, 5, 9);
  uint16_t brightnesstheta16 = sPseudotime;

  for (uint16_t i = 0; i < num_LEDs; i++) {
    hue16 += hueinc16;
    uint8_t hue8 = hue16 / 256;

    brightnesstheta16 += brightnessthetainc16;
    uint16_t b16 = sin16(brightnesstheta16) + 32768;

    uint16_t bri16 = (uint32_t)((uint32_t)b16 * (uint32_t)b16) / 65536;
    uint8_t bri8 = (uint32_t)(((uint32_t)bri16) * brightdepth) / 65536;
    bri8 += (255 - brightdepth);

    CRGB newcolor = CHSV(hue8, sat8, bri8);

    uint16_t pixelnumber = i;
    pixelnumber = (num_LEDs - 1) - pixelnumber;

    nblend(leds[pixelnumber], newcolor, 64);
  }
}
