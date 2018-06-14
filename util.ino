
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
