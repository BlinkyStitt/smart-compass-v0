/* SD */

void setupSD() {
  Serial.print("Setting up SD... ");

  if (!SD.begin(SDCARD_CS_PIN)) {
    Serial.println("failed! No SD!");
    return;
  }

  sd_setup = true;

  Serial.println("done.");
}