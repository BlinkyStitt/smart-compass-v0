int checkBattery() {
  // TODO: do something with this
  float measuredvbat = analogRead(VBAT_PIN);
  measuredvbat *= 2;    // we divided by 2, so multiply back
  measuredvbat *= 3.3;  // Multiply by 3.3V, our reference voltage
  measuredvbat /= 1024; // convert to voltage

  /*
  DEBUG_PRINT(F("VBat: "));
  DEBUG_PRINTLN(measuredvbat);
  */

  if (measuredvbat < 3.3) {
    return BATTERY_DEAD;
  }

  if (measuredvbat < 3.7) {
    return BATTERY_LOW;
  }

  if (measuredvbat < 4.1) {
    return BATTERY_OK;
  }

  return BATTERY_FULL;
}
