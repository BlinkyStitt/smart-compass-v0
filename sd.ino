/* SD */

void setupSD() {
  DEBUG_PRINT("Setting up SD... ");

  if (!SD.begin(SDCARD_CS_PIN)) {
    DEBUG_PRINTLN("failed! No SD!");
    return;
  }

  sd_setup = true;

  DEBUG_PRINTLN("done.");
}