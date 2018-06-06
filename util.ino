
int checkBattery() {
  // TODO: do something with this
  float measuredvbat = analogRead(VBAT_PIN);
  measuredvbat *= 2;    // we divided by 2, so multiply back
  measuredvbat *= 3.3;  // Multiply by 3.3V, our reference voltage
  measuredvbat /= 1024; // convert to voltage

  /*
  Serial.print("VBat: ");
  Serial.println(measuredvbat);
  */

  // return 0-3; dead, low, okay, full

  if (measuredvbat < 3.3) {
    return 0;
  }

  if (measuredvbat < 3.7) {
    return 1;
  }

  if (measuredvbat < 4.1) {
    return 2;
  }

  return 3;
}

static void delayToDither(uint8_t ms_target_delay) {
  static long ms_prev = 0;

  long ms_cur = millis();

  // TODO: i'm not sure about the min here. i think it should protect us from the clock wrapping around
  int delay_needed = min(ms_prev + ms_target_delay - ms_cur, ms_target_delay);

  if (delay_needed > 0) {
    FastLED.delay(delay_needed);
  }

  ms_prev = ms_cur;
}

unsigned long nowMillis() {
  if (timeStatus() != timeSet) {
    return millis();
  }

  // TODO: include some sort of offset to make sure this is in sync with remote peers
  // TODO: this wraps around, but I think that's fine because it will wrap the same for everyone
  // TODO: there is a LOT of jitter here
  return now() * 1000 + (gps_ms % 1000);
}

// Thanks to DanRoad at https://www.reddit.com/r/arduino/comments/4vbzi0/i_made_a_prime_number_generator_using_an/d5zlsoa/
// https://gist.github.com/anonymous/bf0495a592e7e923e74ef3374acad103#file-best-ino
long nextPrime(long p) {
  while (!isPrime(++p)) continue;
  return p;
}

bool isPrime(long p) {
  if ( (p < 2) || (p % 2 == 0 && p != 2) || (p % 3 == 0 && p != 3) ) return false;

  for (long k = 6; (k-1)*(k-1) <= p; k += 6) {
    if (p % (k+1) == 0 || p % (k-1) == 0) return false;
  }

  return true;
}
// END https://gist.github.com/anonymous/bf0495a592e7e923e74ef3374acad103#file-best-ino
