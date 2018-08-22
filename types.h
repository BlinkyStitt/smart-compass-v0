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

typedef struct {
  int database_id;  // TODO: long?
  bool transmitted;
  uint32_t last_updated_at;
  int32_t latitude;
  int32_t longitude;
  float distance;
  float magnetic_bearing;

  // TODO: what type?
  int hue;
  int saturation;
} CompassPin;


// Record definition for the database table
// TODO: consistent naming with pins
typedef struct {
  uint32_t last_updated_at;
  int32_t latitude;
  int32_t longitude;

  // TODO: what type?
  int hue;
  int saturation;

} SavedLocationData;
