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
  CHSV color;
} CompassPin;


// Record definition for the database table
// TODO: consistent naming with pins
typedef struct {
  int location_id = -1;
  int next_track;
  int play_count;
  int32_t latitude;
  int32_t longitude;
  CHSV color;
} LocationData;
