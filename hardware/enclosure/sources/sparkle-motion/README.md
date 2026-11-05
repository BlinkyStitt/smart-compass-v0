# Original Sparkle Motion Rev D source layout

The Rev D Eagle board and schematic are original Adafruit files. The index
records their pinned revision, original names, SHA-256 values and byte counts.
The upstream attribution and CC-BY-SA-3.0 license remain in upstream-README.md
and license.txt. The earlier A/D connectivity extract remains unchanged.

The selected fixed input uses X7.PWR and X7.GND after removal of the stock X7
barrel jack. X7.GNDBREAK is also a ground pad but remains open. Keep D2 and PTC1.
The input path stays X7.PWR → D2 → PTC1 → board rail. Do not use an output power
clamp as a substitute input. The barrel-jack removal changes the connector;
it does not establish voltage-drop, leakage, fault or thermal limits.

The nominal X7 holes are 0.9 mm drills. Check actual finished holes and selected
wire fit. The source pad positions do not prove finished solder dimensions,
wire retention, supplied-board identity or physical qualification.
