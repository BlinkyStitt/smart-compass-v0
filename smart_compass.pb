syntax = "proto2";

/* TODO: int32 is bigger than we need for most of these */

message SmartCompass {
  required int32  network_id = 1;
  required int32  peer_id = 2;
  required int32 time = 3;

  message GPS {
    required int32   id = 1;
    required int32   time_diff = 2;
    required int32   hue = 3;
    required int32   latitude = 4;
    required int32   longitude = 5;
  }

  repeated GPS gps = 4;
}
