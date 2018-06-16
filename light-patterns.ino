/* light patterns */

void flashlight() {
  for (int i = 0; i < num_LEDs; i++) {
    if (i % flashlight_density == 0) {
      leds[i] = CRGB::White;
    } else {
      // smoothly transition from other patterns
      leds[i].fadeToBlackBy(90);
    }
  }
}

// https://gist.github.com/kriegsman
void sinelon() {
  // a colored dot sweeping back and forth, with fading trails
  fadeToBlackBy(leds, num_LEDs, 64);
  int pos = beatsin16(13, 0, num_LEDs);
  leds[pos] += CHSV(g_hue, 255, 192);
}

// TODO: circle with multiple colors
void circle() {
  int ms_per_led = 3 * 1000 / frames_per_second;  // 3 frames
  int pos = (millis() / ms_per_led) % num_LEDs;  // TODO: use now_millis so we stay in sync with others?

  fadeToBlackBy(leds, num_LEDs, 64);

  leds[pos] += CHSV(g_hue, 255, 192);

  pos++;
  if (pos >= num_LEDs) {
    pos = 0;
  }
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

  uint16_t ms = network_ms;  // this should keep everyone's lights looking the same
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