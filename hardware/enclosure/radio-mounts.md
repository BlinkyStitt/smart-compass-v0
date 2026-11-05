# Radio edge carrier

Use Adafruit 3072 RFM95W with JP1, JP2, JP3 and optional X1 antenna connector
parts uninstalled. Fit the selected fixed wires directly to their source pads.
Leave JP1.1–JP1.5 and JP3.3 EN without external leads. Use JP2.1 ANT for the
existing 78 mm internal wire. Preserve all existing circuit and firmware pins.

[Adafruit's downloads](https://learn.adafruit.com/adafruit-rfm69hcw-and-rfm96-rfm95-rfm98-lora-packet-padio-breakouts/downloads)
state that the RFM69 and RFM9X use the same schematic and board layout. Thus
the source U1 RFM69 label does not select a different product. The original
Eagle files, revision, hashes and attribution remain in
[sources/rfm-lora](sources/rfm-lora/README.md).

The actual source outline is 25.4 × 29.21 mm, with three rounded corners and
15 through-pads. It has no mechanical mounting holes. Use the outline centre
[12.7, 14.605] mm from its lower-left as the assembly datum. The Eagle X origin
is 0.254 mm; remove that offset once for the PCB and every pad. Wide uses a
180-degree rotation and PCB bottom Z = 6 mm. Narrow uses 0 degrees and Z =
8 mm. The fixture does not choose global board positions or an antenna route.
Transform those together in the full generator and check the installed fit.

Fit three M2 nuts into integral rear bosses before fitting the carrier or
electronics. Each entry is 9 mm long. The [23.8, −4.2] mm station uses source
−X to clear the Wide vent mount. The other two use source +X. Boss pocket roof and bottom skin
targets are 1.35 and 0.85 mm. The separate carrier bears at Z = 4.1 mm. It
supports the long PCB edges and the unused far end, after source X = 24 mm.
Do not add wires or solder to unused X1 pads or the bearing lands.

The carrier has three loose retainers in a triangle at source [5, 33.41],
[20.4, 33.41] and [23.8, −4.2] mm. The lower post clears the full Narrow door
latch space. The complete perimeter lips and end stops still support and
capture the PCB. This arrangement does not establish retention force.
Each retainer seats on a hard stop and
captures 0.6 mm of the PCB edge. The 1.85 mm slot leaves 0.25 mm play for the
1.6 mm nominal PCB. The 0.25 mm side gap and all printed dimensions are assembly
targets. They are not guaranteed tolerances of a supplied board or print.

Use three M2 × 12 screws, finished under the head to 8.75 mm in Wide or
10.75 mm in Narrow. Deburr and inspect the ends. Nominal tip projection is
0.4 mm beyond the complete nut. Tighten onto the hard stops; do not squeeze
the PCB. Remove all three retainers and screws for straight board insertion.
The component check covers a continuous 20 mm vertical motion before wiring
and case installation. It does not prove removal through fitted optics.

The full source outline replaces the old generic 25.4 × 32 mm padded box.
Adafruit lists approximately 29 × 25 × 4 mm for the product. This design
keeps an 8 mm top-of-assembly target from PCB bottom and a separate 2.1 mm
underboard wiring space. Nine populated source footprints, including their
pads and drawing lines, stay within the capture lands. Their nominal XY
bounds extend to Y = 28.494 mm; the upper land starts at 28.61 mm. These are
source-layout checks. They do not give maximum supplied component dimensions.
Inspect the actual board, regulator variant, tin shield and solder before fit.
[Adafruit product and revision history](https://www.adafruit.com/product/3072).

The full generator joins the two actual antenna saddles to this removable
carrier with a 6 mm wide, 3 mm thick spine at Z = 4.1 mm. The spine starts
0.25 mm beyond the PCB edge toward the antenna run. It does not cross the
underboard wiring space. Place the first tie station 13.5 mm after the bend
and the second at 50 mm. These stations clear the retainers. Check the complete
carrier, wire, all other products and withdrawal path in the full assembly.
The component check alone does not establish those installed results.

The reference spaces exclude only the documented 3.2 mm radius ANT launch
neighbourhood and the source-supported edge/end bearing lands. The ANT drill
stays 1 mm. This local exception does not establish RF performance or permit
other wires to cross components. Final joints, routes, insulation and strain
relief need complete installed checks. No PCB or reference volume establishes
module mass; count the purchased radio once in the BOM.

Run `RadioMountCheck.FCMacro` with `SC_CAD_DIR` set to this directory and
`SC_RADIO_CHECK_RESULT` set to a new result path. Require its named PASS and
unchanged source hashes. It checks all 15 pad bores, nine footprint spaces,
actual PCB bearing, nut paths, screw engagement, six capture translations,
six rigid rocking rotations at ±2 degrees, and assembly motion.
It rejects missing parts, floating carriers, unseated retainers, short screws
and insertion with a retainer fitted. Physical fit, retention, joints,
vibration, heat and radio operation remain unmeasured.
