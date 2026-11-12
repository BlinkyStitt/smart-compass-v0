# Plug-in carrier for the narrow compass

Rev A has a [routed carrier PCB](carrier-a.kicad_pcb), a
[plug and harness assembly guide](assembly.md), and a
[USB-C power and charging design](wall-power.md). The charger is a separate
assembly that plugs into the carrier. The [sealed pigtail](dust-sealing.md)
uses a downward cable gland in the lower rear cover. The compact charger,
pigtail head and complete enclosure seals still need physical verification.

The original fit model uses a single 1.2 mm carrier board. The
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

## Harness slack and assembly

The fit report lists the installed slack allowance for each of the 13 off-board
cables. Allow 20–25 mm on local leads and 40 mm on the four LED cables that cross
to the front. These lengths stay in the finished harness. Measure the route
between the actual connector exits with its ordinary bends, then add the
service allowance and the wire inside each connector. Make the first cables
against the fitted hardware before setting the final cut list.

Lift the rear cover straight back and support it about 30 mm off the case. The LED leads
have a further 10 mm of handling allowance to reach their plugs. Unplug those
leads before taking the cover away. Keep some play at each connector and
support the lead near its exit. Lay the excess into the blue service-fold
spaces in the CAD as separate flat U-bends. Keep the wires free to slide against
each other through the turn and use a removable soft tie to keep each fold in
its space. Keep the door, cover rim, screw seats, and LED board clear.

The slots use the largest specified individual wire diameter for each cable
and at least three times that diameter for the wire centreline bend radius. Use the
larger bend radius if the selected cable or connector requires one. Check the
actual lead exits and the opened and closed assembly with the first set of
cables. [Wire support and bend-radius reference](https://standards.nasa.gov/sites/default/files/standards/NASA/A/4/nasa-std-87394a_w_change_4_0.pdf)

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

## Qualify the prototype

Use the Rev A assembly and power guides for the bench build. Measure current
and temperature at the contacts, copper, and LED circuits. Check the positions of the GPS and radio antennas with the
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
