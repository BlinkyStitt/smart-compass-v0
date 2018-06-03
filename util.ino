
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

unsigned long nowMillis() {
  if (timeStatus() != timeSet) {
    return millis();
  }

  // TODO: include some sort of offset to make sure this is in sync with remote peers
  // TODO: this wraps around, but I think thats fine because it will wrap the same for everyone
  return now() * 1000 + (gps_ms % 1000);
}
