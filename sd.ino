/* SD */

void setupSD() {
  Serial.print("Setting up SD... ");

  pinMode(SDCARD_CS_PIN, OUTPUT);

  if (!SD.begin(SDCARD_CS_PIN)) {
    /*
    // TODO: enable this once it is wired up
    Serial.println("failed! Cannot proceed without SD!");
    while (1)
      ;
    */
    Serial.println("failed! Using debug defaults!");
    return;
  }

  Serial.println("done.");
}