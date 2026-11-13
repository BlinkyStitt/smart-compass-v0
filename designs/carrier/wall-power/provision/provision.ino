#include <Wire.h>
#include <SparkFun_STUSB4500.h>

STUSB4500 sink;

bool hasWallProfile() {
  return sink.getPdoNumber() == 2 &&
         sink.getVoltage(2) == 20.0f && sink.getCurrent(2) == 3.0f &&
         sink.getConfigOkGpio() == 2 && sink.getPowerAbove5vOnly() == 1 &&
         sink.getReqSrcCurrent() == 0;
}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  if (!sink.begin(0x28)) {
    Serial.println("No STUSB4500 at 0x28");
    return;
  }
  Serial.println(hasWallProfile() ? "Verified 20 V / 3 A NVM" :
                 "Send W to write the 20 V / 3 A NVM, or V to verify");
}

void loop() {
  const int command = Serial.read();
  if (command == 'V') {
    sink.read();
    Serial.println(hasWallProfile() ? "Verified 20 V / 3 A NVM" : "FAIL: wrong NVM");
  } else if (command == 'W') {
    sink.setPdoNumber(2);
    sink.setVoltage(2, 20.0f);
    sink.setCurrent(2, 3.0f);
    sink.setConfigOkGpio(2);
    sink.setPowerAbove5vOnly(1);
    sink.setReqSrcCurrent(0);
    sink.write();
    Serial.println("Power-cycle the target and send V to verify NVM");
  }
}
