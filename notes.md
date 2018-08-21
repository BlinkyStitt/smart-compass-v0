
Compile protobuf:

    ../libraries/nanopb-0.3.9.1-macosx-x86/generator-bin/protoc --nanopb_out=. smart-compass.proto

Generate shared network key:

    openssl rand 16 >security.key

TODO:
- make sure SmartCompassLocationMessage_size < RH_RF95_MAX_MESSAGE_LEN
- database saving is broken
- make peer locations and saved locations use the same code but just with different arrays
- is max_compass_points big enough? what about when we include saved locations?
- color-blind friendly colors from test-lights.ino. i can't tell what any of the current pin_colors are. red, yellow, blue, white.
- document max_points_per_color. its not a very descriptive name. it groups up saved locations by color and then only shows the nearest X
- move max_points_per_color to the SD?
- actually solder something on pin 6 so we can get a decent random?
- put LED_FADE_RATE on SD
- do we want to log anything else on start?
- what rate should we read GPS data at? the flora example does 1Hz but we don't want to suck too much power
- what table size?
- make sure course_to actualy works. and confirm distance is in meters
- lots left to write in compass.ino

TODO v2:
- IniFile doesn't support unsigned ints, but most of our variables should be unsigned
- how is clang-format deciding to order includes? they aren't alphabetical
- is 128 bit blake2s hashing secure enough?
- Full message signing is crashing: "Message: n=73-8C-76-2C-83-AA-53-18-58-EE-73-81-86-27-B6-2 h=0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0 txp=0 p=0 now=1529107392 ms=167426 t=1529107383 lat=377489183 lon=-1224411416 EOM. resetting... updating... .."
- try freertos if i start having timing issues
- use addmod8 for FastLED patterns
- move pins around for cleaner traces
- split this into 3 different sized arrays and use a union?
- disable ADC or other things to save battery?
- time_segments can get pretty big being 2 * num_peers ^ 2. thats fine for my small group but we might want something smarter for bigger groups

// TODO: if debug, EVERY_N_SECONDS(10) {
  // TODO: print if configured
  // TODO: print if the radio is sleeping
  // TODO: print if the gps has a fix
  // TODO: print number of saved gps points
  // TODO: print  broadcasting_peer_id and broadcasted_peer_id
  // TODO: print transmit errors
  // TODO: print memory/cpu stats
  // TODO: print other things
