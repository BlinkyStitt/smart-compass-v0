# Wall-power boards

| Board | KiCad layout | KiCad schematic | Finished board |
| --- | --- | --- | --- |
| Internal charger | [Charger PCB](charger.kicad_pcb) | [Charger schematic](charger.kicad_sch) | 24 × 26 mm, 1.60 mm thick |
| Rev A 5 V external pigtail | [Pigtail PCB](usb-pigtail.kicad_pcb) | [Pigtail schematic](usb-pigtail.kicad_sch) | 28 × 31 mm, **1.20 ± 0.10 mm** thick |
| 60 W USB-C head | [Head PCB](usb-pd60.kicad_pcb) | [Head schematic](usb-pd60.kicad_sch) | 28 × 31 mm, **1.20 ± 0.10 mm** thick |
| LED power selector | [Selector PCB](led-power.kicad_pcb) | [Selector schematic](led-power.kicad_sch) | 28 × 28 mm, 1.60 mm thick |

Build the 60 W head, selector and existing charger together. Use the
[60 W BOM](bom-pd60.csv) and [assembly guide](../wall-power-pd60.md).
The 5 V pigtail is the earlier option. The 60 W head requires the
programmed STUSB4500 profile. Use the keyed connectors in the assembly
guide to prevent mixing the two pigtail assemblies.

Use KiCad 10. Each board has four copper layers. Specify 35 µm finished
outer copper and at least 35 µm on In2.Cu, which carries the power trunks.
Specify 0.13 mm minimum track, 0.20 mm minimum copper clearance and
0.30 mm copper-to-edge clearance. Use plated slots at the USB receptacle
and nonplated locator and mounting holes. Fill and copper-cap the vias
under the soldered exposed pads, and the other vias placed in SMD pads,
to prevent solder loss. The fabrication drill files do not specify
via fill. Tell the assembler which vias are in pads.

Use the [charger and 5 V pigtail BOM](bom.csv) for those assemblies.
Reflow the boards and solder the wires at the bench. Fit the USB shell
stakes per the assembly house's mixed SMT and through-hole process.
Check capacitor substitutions at DC bias. The charger needs at least
10 µF effective at BAT and SYS. Use the [assembly and bench guide](../wall-power.md)
for wiring, mounting and commissioning.

## Verify or export the boards

From this directory, with KiCad's footprint libraries installed, run the
following for each name in the table. Use a writable output directory.
Use KiCad's Python interpreter for the scripts that import `pcbnew`.

```sh
board=usb-pd60  # or led-power, charger, usb-pigtail
kicad-cli pcb drc --refill-zones --severity-all --exit-code-violations --schematic-parity \
  -o "$output/$board-drc.rpt" "$board.kicad_pcb"
kicad-cli sch export netlist --format kicadxml \
  -o "$output/$board.xml" "$board.kicad_sch"
python verify_netlist.py "$board.kicad_pcb" "$output/$board.xml"
kicad-cli pcb export gerbers --layers F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts \
  -o "$output/$board/" "$board.kicad_pcb"
kicad-cli pcb export drill --excellon-separate-th -o "$output/$board/" "$board.kicad_pcb"
kicad-cli pcb export pos --format csv --units mm --smd-only \
  -o "$output/$board/placement.csv" "$board.kicad_pcb"
```

The committed PCB files own the final routes. [Board source](board_design.py)
generates the footprints, pin maps and fixed power copper for a new route.
[Schematic source](schematic.py) generates the KiCad connection drawings
from those pin maps. The netlist comparison checks each footprint, reference
and connected pad. The first assembled pair still needs the bench checks.
