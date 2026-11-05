# Rear control component study

The selected controls are C&K 7201SYZQE and PTS645SL70-2 LFS. The active
part/source record is [electrical-design.json](electrical-design.json).
[control_fixture.py](control_fixture.py) makes their specified mounting parts.
The complete enclosure generators must place and check these parts before
publication. A component-study result does not complete that integration.

## Source dimensions and assembly settings

The [7000 drawing](https://www.ckswitches.com/media/1394/7000toggle.pdf)
(MI 10/02/26, DPDT drawing) gives the nominal 11.43 ×12.70 ×8.89 mm body,
6.35 mm threaded bushing diameter, 8.89 mm bushing height and 10.67 mm
actuator length. The six solder lugs use 4.83 mm column and 4.70 mm row
spacing. The actuator has a nominal 25° throw and 2.92 mm diameter.
These nominal outlines do not establish supplied-part tolerances.

Use the **open C&K 700201201 hex nut** and **700303202 lockwasher**.
The [hardware drawing](https://www.ckswitches.com/media/1960/switchhardware.pdf)
gives nominal nut flats of .307 inch and thickness .062 inch, and washer
outer diameter .402 inch and thickness .018 inch. The model converts those
imperial dimensions directly. It represents the toothed washer by an annulus;
it does not prove tooth compression or clamp torque. Do not substitute the
blind dress nut 709901201. Count only the installed hardware; supplied unused
nuts/rings are spares. Supplied fit and retention remain unmeasured.

The [PTS645 drawing](https://www.ckswitches.com/media/1471/pts645.pdf)
(MI 10/02/26, pages 1, 2, 5 and 7) defines the direct 7 ±0.1 mm actuator
height. The source's mechanical-characteristics table has inconsistent
option/height entries. This study does not use those entries as force/travel
bounds. Connect START pins **1 and 3**; pins 1/2 are internally common,
as are pins 3/4. Insulate the unused duplicate pins.

The START mounting datum is Z3.65 mm. The nominal body front is Z0.20 mm;
the actuator tip is Z−3.45 to −3.25 mm. The separate 0.8 mm bezel has its
outside face at Z−0.60 mm. Use the stock actuator directly, without a printed
plunger. Two compression collars bridge Z2.00 to Z3.65 mm. The 1.5 mm
backplate, M2 washers and nuts complete the stack. Finish two M2×10 screws
to **7.95 mm under the head**, then verify the actual stack and projection.
These are fabrication targets, not achieved measurements.

The separate U guard has 26 mm between its walls and a recessed **O** cue.
Its 20 mm rear projection shields the toggle. Two M2×8 screws, finished to
**7.20 mm under the head**, clamp its 3 mm flanges to full 2 mm rear-panel
lands. Recesses admit the heads and driver without intersecting a guard wall.
Install the switch by continuity so the lever toward O connects terminals
2–3 and 5–6. Check orientation and rotation retention physically.

## Native checks and print orientation

Run `RearControlsCheck.FCMacro` in an isolated FreeCAD process with
`SC_CAD_DIR` set to this directory and `SC_CONTROL_CHECK_RESULT` set to a
new result file. Require **REAR CONTROLS COMPONENT CHECK PASS**. An exit
code alone is insufficient. The record includes input hashes and tool version.

The fixtures exercise both guard orientations. Checks require one valid solid
per printed part, no component/panel interference, full-height bearing under
each mount, and positive clearance for a 24 mm finger approach. A thin
obstruction must fail. Native checks also compare the pruned exact-distance
query with all-obstacle distances on positive and touching fixtures.

Print the separate guard with its attachment face on the bed: the crossbar
starts on the bed and supports both walls. Print the bezel face-down, the
backplate flat and the collars flat. The rear panel has no integral 20 mm rear
guard projection. Complete assembly, slicer, material and installed service
checks still belong to each enclosure's publication contract.

Physical fit, print strength, tightening, fatigue, finger reach, operating
force and electrical switching are **unmeasured**. These component fixtures
are not an installed-enclosure or safe-to-wear result.
