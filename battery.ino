void checkBattery(BatteryStatus *b) {
  float measuredvbat = analogRead(VBAT_PIN);
  measuredvbat *= 2;    // we divided by 2, so multiply back
  measuredvbat *= 3.3;  // Multiply by 3.3V, our reference voltage
  measuredvbat /= 1024; // convert to voltage

  DEBUG_PRINT(F("VBat: "));
  DEBUG_PRINTLN(measuredvbat);

  //DEBUG_PRINT(F("Battery: "));
  if (measuredvbat < 3.3) {
    //DEBUG_PRINTLN(F("DEAD"));
    *b = BATTERY_DEAD;
    return;
  }

  if (measuredvbat < 3.7) {
    //DEBUG_PRINTLN(F("LOW"));
    *b = BATTERY_LOW;
    return;
  }

  if (measuredvbat < 4.1) {
    //DEBUG_PRINTLN(F("OK"));
    *b = BATTERY_OK;
    return;
  }

  //DEBUG_PRINTLN(F("FULL"));
  *b = BATTERY_FULL;
  return;
}
