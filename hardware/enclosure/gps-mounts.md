# GPS source-hole mounts

Use the selected Adafruit Ultimate GPS FeatherWing at its four MS1 outline
mounts. Do not use the GPS antenna's internal hole as a board mount. The right
holes are nominal 2.54 mm unplated holes. The left holes are nominal 2.5 mm
plated holes. The source datum is [25.4, 11.43] mm from the outline lower-left,
viewed from the component side. Keep the source X axis across the Wide case.
Turn the module 90 degrees in Narrow, where the long board axis runs up the case.

The factory extracts the actual PCB from the original 55-solid Adafruit STEP.
It retains the full 50.8 × 22.86 × 8 mm loaded reservation, turned with the PCB.
The conservative loaded space is a reference, not an additional purchased part
or a homogeneous mass estimate. The source component bodies overlap each
other and the PCB. Do not use their compound as a regular solid to subtract
a complementary empty-space reference. The conservative space keeps the
complete original loaded bound and avoids that unreliable Boolean operation.
Do not compute module mass from the sum of mixed-material CAD volumes.

Use four selected M2 × 8 cap screws finished to 6.8 mm and four selected M2
nuts. Use no PCB washers. The source model registers the PCB holes. The native
test also checks each original source body against all eight hardware parts.
The 2.016 mm radius around each screw head is an assembly clearance in
the conservative loaded space, not a published component keepout. Check actual
head/component clearance on the supplied board before tightening. Each integral post has a 3.1 mm lower radius and
a 1.95 mm bearing radius. The source PCB is 1.57 mm thick. The nominal screw
tip extends 0.43 mm past the nut. Check the supplied board and screw lengths
before assembly. Do not force a screw or clamp components against a post.

Insert the nuts before the board and screws. Each nut entry faces outward in
source Y, which becomes installed X in Narrow. The native test
checks the complete hex nut's horizontal insertion and vertical drop path.
The component study uses board bottom Z = 6 mm for Wide and 9 mm for Narrow.

Run `GpsMountCheck.FCMacro` in FreeCAD with `SC_CAD_DIR` set to this directory.
Set `SC_GPS_CHECK_RESULT` to a new result path. Require the named PASS marker
and unchanged input hashes. The test checks source bounds and solid count,
all four bearings, screw engagement, nut insertion, six selected electrical pad
bores, and interferences with a nominal rear interface. Its negative cases
reject missing parts, detached PCB bodies, floating posts and short screw
engagement.

This component test does not prove installed case clearance, fitted wires,
finished solder joints, retention, vibration or physical acceptance. The seven
physical qualification procedures remain unmeasured. Do not release assembly
exports on the strength of this component test alone.
