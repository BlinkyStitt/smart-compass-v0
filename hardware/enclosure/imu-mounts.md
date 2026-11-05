# Classic IMU source-hole mounting

This is an IMU component study. It replaces the proposed oversized PCB rails
with mounting posts at the classic Rev A board's four actual mounting holes.
Both installed designs still need integration. It does not close the
`fitted-harness` error or establish physical acceptance.

The selected [classic Rev A sources](sources/lsm9ds1-classic/README.md) define
an unscaled33.02 x20.32 mm outline with2.54 mm corner radii. Four2.5 mm holes
lie at2.54/2.54,30.48/2.54,30.48/17.78 and2.54/17.78 mm. The factory reads
the outline, hole pattern and all through-pad drills from the original Eagle
file. It retains the separate40 x28 x12 mm loaded engineering reservation.
That reservation includes fixed leads. It is not a measured component maximum.

Use four **SSCF-M2-8-A2 DIN912 cap screws**, finished to6.8 mm under the
head, and four **NUT203M2-B DIN934 M2 A4 nuts** from the existing hardware
record. The3.8 mm cap head fits the source's4.032 mm component-keepout disc.
Do not put a standard5 mm DIN125 washer on this PCB: it exceeds that keepout.
The nominal radial head-to-keepout gap is0.116 mm. These are source/assembly
positions, not manufactured clearance measurements.

The two designs place the PCB bottom at6 mm and9 mm respectively. Narrow
rotates the same source board90 degrees; it does not scale the board. Integral
posts use3.1 mm lower pods and1.95 mm upper bearing radii. The lower pods hold
replaceable M2 nuts in side-entry pockets. A1.4 mm nominal roof remains above
the pocket. The nut lies4.8 mm below the PCB bottom. The specified screw
engages the full1.6 mm nut and leaves0.4 mm nominal tip projection.

The source PCB mounting annuli must bear on the printed posts. They do not
rely on the larger loaded reservation for support. Install the nuts before
the PCB and gauge the clamp stack. Deburr screw ends and verify retention.
Use fixed soldered leads at the selected header pads; leave the supplied male
headers uninstalled. Route leads above the PCB and trim soldered tails before
assembly. Inspect joints and strain relief. Magnetic disturbance, print fit,
retention, joint quality and supplied-board tolerances remain unmeasured.

The native source footprint is a nominal PCB model with1.6 mm thickness. The
component/lead reservation stays a separate reference. It has clearance channels
at the selected header pads and the manufacturer's mounting keepouts. Do not
count that reference as another board or as extra component mass.

Run the pure tests with `python3 -m unittest discover -s hardware/enclosure -p
'test_imu_mount.py'`. Run `ImuMountCheck.FCMacro` in FreeCAD with
`SC_CAD_DIR` set to this directory and `SC_IMU_CHECK_RESULT` set to a new result
path outside Git. Require **IMU MOUNT COMPONENT CHECK PASS** and matching source
hashes. Exit zero alone does not prove a pass.

The native check covers both orientations, nine physical products plus one
reference, a connected rear/post interface, closed interference, PCB-annulus
bearing and screw projection. Missing board/hardware/reference inputs and
posts lowered clear of the PCB must fail. Complete enclosure clearance,
wire cuts/strain relief and physical qualification remain separate work.

The captive-nut slot has8mm entry length and clears the nut corners, not only
the flats. Before fitting boards or screws, lower each nut into the open end
of its slot and slide it under the pocket roof. The native check sweeps the
actual outer nut profile through both motions against the rear interface.
Supplied nut dimensions, print fit and insertion force remain unmeasured.
