# Wireless mesh smart compass

Libraries:
- Adafruit_GPS from https://github.com/WyseNynja/Adafruit_GPS
- AP_Declination from https://github.com/WyseNynja/ardupilot
- Adafruit_LSM9DS1
- Adafruit_Sensor
- elapsedMillis
- FastLED
- nanopb-0.3.9.1
- RadioHead
- SD
- SPI
- Time

Each node has:
- sd card
- 9-DOF Accel/Magnetometer/Gyro+Temp
- gps (https://learn.adafruit.com/adafruit-ultimate-gps-featherwing/arduino-library)
- lora radio (https://learn.adafruit.com/adafruit-feather-32u4-radio-with-lora-radio-module?view=all#using-with-arduino-ide)
- rgb led ring

It uses the 9-dof/gyro as a switch.
- hanging upright => pretty patterns
- flat upright => smart compass
- hanging upside down => clock
- flat upside down => off

It reads configuration off the SD card. Things such as the color to broadcast, the network id, the frequency to use, the total number of nodes, and probably more.

It uses the GPS to get lat/long and the time (is there a library for getting time zone from lat/long?).

It uses the radio to broadcast its GPS location to other nodes. Nodes all work on the same RF frequency. They are synchronised so each transmits in a particular time slot. There are 4 nodes in the mesh. Each timing cycle is 8,192ms and so it takes around 8 to 32 seconds to send data through the mesh. This timing needs to be tuned.

Each node stores all the values of all other nodes (color/lat/long/time).  When a node is ready to transmit, it sends all the values. Newer values replace older and propagate through the mesh. If this is too much data, cut it into chunks.

APC220 modules have open air ranges of up to 1000m. Trees and metal (eg a shed) can greatly decrease this though, to as low as 50m. I'm not sure what the feather lora module ranges are, but it should be even better.

The lights around the compass can display the direction to the other nodes, the closest bathrooms, our camp, or the man. Press a button to change modes of what is displayed. Hold a button to add a bathroom/home/misc to the SD card. Once saved, this will be relayed to other nodes.

TODO:
 - all the examples i've seen have a send an ack, but which node should ack?
 