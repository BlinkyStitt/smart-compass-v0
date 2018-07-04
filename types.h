// http://playground.arduino.cc/Code/Enum

enum Orientation : byte {
  ORIENTED_UP,
  ORIENTED_DOWN,
  ORIENTED_USB_UP,
  ORIENTED_USB_DOWN,
  ORIENTED_PORTRAIT_UPSIDE_DOWN,
  ORIENTED_PORTRAIT
};

enum BatteryStatus : byte {
  BATTERY_DEAD,
  BATTERY_LOW,
  BATTERY_OK,
  BATTERY_FULL
};

enum CompassMode : byte {
  COMPASS_FRIENDS,
  COMPASS_PLACES
};
