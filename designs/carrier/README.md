# Plug-in carrier for the narrow compass

This is a mechanical fit prototype for a single 1.2 mm carrier board. The
housing uses the narrow design's 58.6 mm optical stack and removable protected
cell. The board follows the cavity and sits beside the battery bay. Its seven
mounts are part of the ribbed rear cover. The rear cover also has holes for
three panel-mount buttons. The layout budgets 36 off-board conductors,
compared with 92 in the current fixed loom. It retains 14 prints
for the case, optics, cell bay and disconnect guard. Final restraints can add
parts.

Three Keystone 3153 insulating washers take the place of the printed
Fibonacci clips. The fit check includes movement around the screw shaft and
checks bearing and clearance to the LEDs and optics. Check clamping and
retention on the physical assembly. [Keystone catalog](https://beta.keyelco.com/userAssets/file/M70p144.pdf)

## Module interfaces

- The GPS FeatherWing, classic LSM9DS1, RFM95W, and BlackPill use complete
  low-profile header strips. The terminal schedule records each pin, its source
  pad, its nominal position, and its circuit assignment. Leave unassigned pins
  unconnected. The module-side male headers need one bench soldering operation.
- The Sparkle Motion uses a 2 × 3 header at JP3. Keep the original barrel
  jack and screw-terminal block. Use a center-positive power lead and a
  five-conductor lead for the LED terminal group. The CAD reserves space for
  each exit. Check the exact connectors and bend radii before routing.
- The PowerBoost has space for removable power leads. The original R20.2
  connection is shown in the terminal schedule only to identify the behavior
  that the new circuit must replace. The carrier needs a circuit that preserves
  physical disconnect and low-battery shutdown through stock module interfaces.

The socket reference is the [Mill-Max 315/415 and 335/435 mated stack](https://www.mill-max.com/sites/default/files/external/assets/2018-03/PR685%20-%20Super%20Low%20Profile%20sockets%20315%20-%20415.pdf).
The drawings give 3.94 mm between the boards. Check supplied hole sizes,
soldered pin insertion, and module retention on the physical gauge.

## Build a fit sample

From the repository root, set the destination to a new output folder on the
external drive and run FreeCAD. Confirm `fit-check.json` is present and the log
reports `CARRIER MECHANICAL FIT PASS`.

```sh
mkdir "$CARRIER_OUTPUT"
COMPASS_CARRIER_SOURCE="$PWD/designs/carrier" \
COMPASS_CARRIER_OUTPUT="$CARRIER_OUTPUT" \
/Applications/FreeCAD.app/Contents/Resources/bin/freecad "$PWD/designs/carrier/Run.FCMacro"
```

The macro generates an installed FreeCAD assembly, a STEP file, a printable
board outline and hole gauge, the rear panel, the terminal schedule, and a fit
report. It also writes an unrouted KiCad board with the checked outline and
socket positions. Print the gauge flat to check connector fit and access.
Use the terminal schedule to assign the remaining connectors before routing.

## Complete the carrier

Route and verify the board before sending it to a PCB assembler. Select keyed
harnesses and verify the current ratings of the contacts, copper, and external
LED circuits. Check the positions of the GPS and radio antennas with the
carrier installed. Add independent board retention so the sockets are not the
only restraints. Select the exact panel buttons and verify their mount and lead
exits. The charger and external-power circuit still need a routed design and
bench verification with and without the protected cell.

The report compares the old loom, removed prints, new rear cover, laminate and
copper budget. The remaining allowance must cover sockets, replacement leads,
new retention and panel hardware, and any changes to the power circuit. The
finished assembly must be weighed. The current fit model retains the seven-print
battery bay. To reach the original 9–12 print target, the battery contact mounts
and final retention still need to be simplified and verified.
