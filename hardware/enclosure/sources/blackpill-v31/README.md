# Original BlackPill V3.1 pin facts

`ports.json` records functional coordinates and pin identities from the pinned
WeAct V3.1 manufacturer STEP and schematic. `index.json` identifies the original
files by URL, revision, SHA-256 and byte count. It also checks the local facts.
The original component models and drawings are not redistributed here. No
license is assigned to the publisher's files. Their source links remain in the
index. This pin record does not use the later contributed KiCad carrier map.

The recovery inspection read the original STEP in FreeCAD 1.1.4 and checked all
40 side-header holes. The X coordinates start at 1.397 mm and increase by
2.54 mm. Manufacturer P1 has Y = 18.009 mm; P2 has Y = 2.794 mm. The model has
0.9 mm nominal holes. The resulting 15.215 mm row spacing differs from the
15.24 mm spacing in the later carrier footprint. The carrier's 0.8 mm drill
describes a carrier PCB, not a finished hole on the module.

The original V3.1 schematic identifies P1.3 as 3.3 V, P1.2 as GND and P1.11 as
PA4. The selected input uses those exact pads. The optional U3 flash shares
PA4, PA5, PA6 and PA7. Keep U3 absent. The newer KiCad README's SPI2/PB12..PB15
description does not apply to the selected V3.1 schematic. The circuit nets and
firmware pin assignments remain unchanged.

The coordinate frame is the original STEP's PCB lower-left corner, viewed
from the component side. X runs along the long board axis. The module is not
placed in either case by this record. Apply one explicit assembly transform
to the board, pads and retained components together during integration.

The source STEP PCB is about 1.49144 mm thick; the release notes state a
1.6 mm nominal board since V2. These sources do not give a guaranteed thickness
tolerance. Keep that difference visible. Check the supplied board before
fitting. The nominal CAD hole diameter is not a guaranteed finished-hole
minimum or evidence of a finished solder joint. Fitted routing, wire retention,
supplied dimensions and physical qualification remain open.
