/* SD */

void setupSD() {
  Serial.print("Setting up SD... ");

  pinMode(SDCARD_CS_PIN, OUTPUT);

  if (!SD.begin(SDCARD_CS_PIN)) {
    Serial.println("failed! Cannot proceed without SD!");
    while (1)
      ;
  }

  Serial.println("done.");

  gps_log_filename += my_network_id;
  gps_log_filename += "-" + my_peer_id;
  gps_log_filename += ".log";

  // open the file. note that only one file can be open at a time, so you have to close this one before opening another.
  gpsLogFile = SD.open("test.txt", FILE_WRITE);

  // if the file opened okay, write to it:
  // TODO: delete this once I've tried it out
  if (gpsLogFile) {
    Serial.print("Writing to test.txt...");
    gpsLogFile.println("testing 1, 2, 3.");
    // close the file:
    gpsLogFile.close();
    Serial.println("done.");
  } else {
    // if the file didn't open, print an error:
    Serial.println("error opening test.txt");
  }

  Serial.println("done.");
}