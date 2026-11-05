# Sparkle source-hole mounts and fixed input

Use the selected Sparkle Motion Rev D at all four source mounting holes.
The nominal hole centres are [2.54, 2.54], [48.26, 30.48], [2.54, 30.48] and
[48.26, 2.54] mm. Their nominal diameter is 2.5 mm. The local fixture datum is
the mounting-grid centre [25.4, 16.51] mm, viewed from the component side.
It differs from the PCB outline centre by 0.0635 mm in Y. Use this datum for
the board, terminals, holes and component reservations together.

Use PCB bottom Z = 6 mm and a 180-degree turn in Wide. Use Z = 8 mm and no
turn in Narrow. Each fixture uses four selected M2 × 8 cap screws finished to
6.8 mm and four selected M2 nuts, with no PCB washers. The nominal tip extends
0.43 mm past the nut. The integral posts have a 3.1 mm lower radius and a
1.95 mm bearing radius. Their narrow neck extends 2.1 mm below the PCB to
clear the reserved underside parts. Insert nuts before the board and screws.

Remove only **X7**, the stock barrel jack, to expose its input holes. Preserve
the pads, traces, **D2** diode and **PTC1**. Connect the paired fixed 22 AWG
input wires to X7.PWR and X7.GND. Leave X7.GNDBREAK open. Do not feed the LED
output rail instead. The original source model remains unchanged in the
repository. Its identified DCJACK_2MM_PTH body, index159, selects the connector
removal; the factory checks the source bytes, body volume and bounds.

The top reservation retains the full 15 mm loaded height. The lower reservation
extends 2.1 mm below the PCB. Both include the USB connector's 0.986 mm nominal
overhang with a 1 mm target. These are conservative design spaces, not measured
part tolerances. Only screw clearance regions are removed. Input joint and wire
spaces still need explicit fitted geometry before harness acceptance. Count
the purchased module once; the two reservations are not additional parts.

Run `SparkleMountCheck.FCMacro` in FreeCAD with `SC_CAD_DIR` set to this
directory. Set `SC_SPARKLE_CHECK_RESULT` to a new result path. Require its named
PASS and unchanged source hashes. It checks the four bearings, complete nut
insertion paths, screw engagement, selected electrical pad bores, the full
source bounds and every retained source body's clearance to all eight hardware
parts. Negative cases reject missing parts, floating posts and short screws.

These component checks do not prove case fit, solder dimensions, strain relief,
wire retention, vibration, temperatures or physical qualification. Inspect the
supplied revision, finished holes, wire fit and reworked pads before assembly.
Keep all unexecuted physical qualification procedures unmeasured.
