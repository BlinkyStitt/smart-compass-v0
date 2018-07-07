/* SD */

void setupSD() {
  DEBUG_PRINT(F("Setting up SD... "));

  if (!SD.begin(SDCARD_CS)) {
    DEBUG_PRINTLN(F("failed! No SD!"));
    return;
  }

  sd_setup = true;

  DEBUG_PRINTLN(F("done."));
}