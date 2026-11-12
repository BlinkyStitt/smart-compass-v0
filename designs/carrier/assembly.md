# Rev A carrier assembly

Use the [routed KiCad board](carrier-a.kicad_pcb) with the 200 mm narrow
enclosure. The board is 1.2 mm thick with four 35 µm copper layers. Keep the
seven rear-cover mounts. The five stock boards plug into the low-profile
sockets from the fit model. Keep a separate mechanical restraint for each
board. Pull a connector by its housing and support the carrier near it.

Have the PCB assembler install the small surface-mount parts. Fit the socket
strips, harness headers and axial fuses after reflow. Use a jig to keep the
matching male pins straight when soldering them to the modules. The PowerBoost
uses its stock terminal-block and LBO header holes. Leave R20 and the factory
red LED in place. Use the stock Sparkle Motion barrel jack and screw clamps.
The LED board inputs, switch and cell contacts still need bench wiring. Make
these as subassemblies so final assembly is screw and plug work.

## Plugs

Pin order is the PCB pad order starting at pin 1. Read pad numbers in KiCad or
use the square pad for the JST headers. Label both ends of each lead before
installation. Use the [carrier parts and pad map](routed-components.json) for
part locations. Use the [stock module source records](../../hardware/enclosure/electrical-design.md)
for the module pins.

| Carrier | Header | Connections in pad order |
| --- | --- | --- |
| J1 | JST B4P-VH | Charger BAT, ground, charger SYS, charger TS sense |
| J2 | JST B3P-VH | Fused cell positive through S1 pole A, cell negative, holder thermistor |
| J3 | JST B5P-VH | Pololu VIN, VOUT, GND, A, OFF |
| J4 | JST B6P-VH | PowerBoost X2.2, X2.1, X1.2, X1.1, JP1.4 LBO, empty |
| J5 | JST B2B-XH-A | S1 pole B RUN contact, S1 pole B common |
| J6 | JST B2P-VH | Sparkle Motion 2.1 mm barrel plug center, sleeve |
| J7 | JST B5B-XH-A | Sparkle JP1.9, JP1.7, JP1.8, JP1.5, JP1.2 |
| J8 | JST B3B-XH-A | Fibonacci 5V, GND, DIN |
| J9 | JST B3B-XH-A | Inner ring 5V, GND, DIN |
| J10 | JST B3B-XH-A | Side ring A 5V, GND, DIN |
| J11 | JST B3B-XH-A | Side ring B 5V, GND, DIN |
| J12 | JST B6B-PH-K | Start pair, Mode pair, Action pair |

J8 through J11 have the same power, ground and data order. Labels identify the
four outputs. Keep the 1000 µF bulk capacitor at the Fibonacci end of J8. R8
drains this branch while J8 is seated. Keep all other USB ports for service and
isolate them from live wall or battery power.

Use precrimped 18 AWG for the cell power and charger SYS paths, 22 AWG for the
barrel feed and LED power, and 26 AWG for controls and LED data. Match the
terminal to each wire gauge. Where the VH contact range ends at 22 AWG, join
the short 22 AWG pigtail to a thinner control or thermistor lead in the
subassembly. Use one conductor per clamp on Sparkle Motion.

Keep the contact-adjacent 4 A fuse in the positive cell lead. Connect the fused
positive lead to S1 terminal 1 and J2.1 to terminal 2. Connect J5.1 to terminal
4 and J5.2 to terminal 5. Insulate unused S1 terminals 3 and 6. Check the
delivered switch with a continuity meter in both positions. The ground return
and thermistor stay in the holder harness. The battery positive contact is
isolated in OFF. Unplug wall USB before opening the case or changing the cell.

## Make the first harness against the actual case

- Leave 25 mm of slack at the cell, charger, switch, and LED clamp harness.
- Leave 20 mm at the barrel, boost, latch, and button harnesses.
- Leave 40 mm in each of the four front LED cables so the cover can open
  about 30 mm and leave 10 mm for access to the plugs.
- Route the power and return leads together. Form gentle U-bends in the
  available spaces. Use a removable soft tie to hold each fold. Keep bends out
  of the battery door path, cover rim, and fastener seats.

Measure the bent route between the actual lead exits and add the slack and
termination allowance before cutting. The model checks room for the mated
housings and the existing fold reservations. The charger harness needs its
own fitted fold and lead-exit check. Test finger access and the completed wires on the
first assembly. Check module retention and antenna behavior with the PCB in
place. Weigh the assembled prototype to capture the cost of the extra plugs
and charger.

## Verify the carrier

Open the board in KiCad 10. Run the DRC with the ground plane refilled.

```sh
kicad-cli pcb drc --refill-zones --exit-code-violations \
  designs/carrier/carrier-a.kicad_pcb
```

The board contains the editable copper. `pcb_placement.py` still makes the
stock socket and outline gauge. `route_board.py` adds the power and harness
connections and exports a Specctra placement from that gauge. Use the stock
footprint libraries from KiCad 10. Review routing after any changes to the
placement or connector map.

For the mechanical check, set `COMPASS_CARRIER_SOURCE` to the absolute
path to `designs/carrier` and set `COMPASS_CARRIER_OUTPUT` to a writable
directory. Run `RunRoutedFit.FCMacro` in FreeCAD. It records the mated plug, proposed USB module envelope
and battery motion checks in `routed-fit.json`.

Use the [wall power design](wall-power.md) before connecting the charger or a
cell. First power up the carrier through J1 SYS and GND on a current-limited
bench supply at 3.6 V with the battery and charger disconnected. Check SYS
at the latch plug and check for shorts. Install the latch and boost next.
Measure the 5 V rail before installing the other modules and LED loads.
