# BlackPill perimeter carrier

Use the selected WeAct V3.1 F411 board with U3 and P1/P2/P3 header parts absent.
Fit fixed wires to the selected PCB pads. Preserve the existing circuit and
firmware pin assignments. The carrier uses the original functional PCB outline
and all through-holes, plus nominal bounds for every other source model body.
The module remains one purchased part. Its source boxes are clearance inputs;
do not use their volumes to estimate mass or count them as separate BOM parts.

Use source datum [26.4034996033, 10.3894996643] mm from the PCB lower-left and
turn it 90 degrees in both designs. PCB bottom Z is 6 mm in Wide and 8 mm in
Narrow. Transform the PCB, all pads and all source bounds together.

The nominal assembly PCB thickness is 1.6 mm from the manufacturer release
notes. The original CAD PCB is about 1.49144 mm thick. These are different
source values, not a guaranteed supplied range. The carrier captures the edge
in a 1.85 mm slot. It does not squeeze components or depend on clamp force.
The nominal 1.6 mm board has 0.25 mm vertical play. Inspect the supplied board
and check the fit before assembly. Keep physical retention unmeasured until
the qualification procedure has run.

The four source-coordinate retainer stations are [9.5, -4.2],
[31, 24.97899933], [43.3, -4.2] and [43.3, 24.97899933] mm. The staggered
left retainers clear the narrow boost module without moving either PCB or
reducing its loaded space.

Four M2 nuts fit in the integral rear bosses. Insert the nut at [31, 24.97899933] mm along source −X. Insert the other
three along source +X through their 9 mm entries. The reversed entry keeps
the complete lowering path clear of the next boss. The longer entries clear the 3.9 mm radius bosses
while each nut is lowered into its slot. Insert all nuts
before fitting the carrier or electronics. Each boss has a 1.35 mm pocket roof
and 0.85 mm bottom skin target. The separate carrier sits at Z = 4.1 mm. Its
side lips and unused far end support the actual PCB face. The native check
requires at least 80 mm² nominal bearing area; this is a design target, not a
published force rating. The open centre leaves space below the components.

Fit four printed edge retainers. At stations 0/1, use M2 × 12 screws finished
to 8.75 mm in Wide or 10.75 mm in Narrow. At stations 2/3, fit the sense bridge over the retainer and the discharge
bridge over it. Use M2 × 25 screws finished to 19.7 mm in Wide or 21.7 mm
in Narrow. Deburr and check each finished screw.
The nominal tip extends 0.4 mm beyond the complete nut. The retainers seat on
hard stops. Their 0.8 mm edge overlap captures the board with 0.25 mm nominal
side clearance. Do not tighten them against the PCB or components.

Support and remove both bridges and their fixed looms first. Disconnect or
desolder its external leads. Remove all four retainers and screws for straight
board insertion/removal.
The component check covers a continuous 20 mm vertical motion before wiring
and case installation. It does not permit removing this board through fitted
optics or without disconnecting its wires. Battery access remains a separate
operation; the mounted electronics stay in place during a cell swap.

The 12 mm loaded-height reference keeps room for the module and fixed wiring.
The selected sense bridge and RC loom occupy part of that space. The native
check cuts only their complete modeled spaces from the remaining reference.
It keeps every original source body and verifies that no cut removes any
source body space previously reserved. It also checks all added parts and
assembly references directly against all 130 nominal source body boxes.
The source models above 0.05 mm from PCB top lie between Y = 4.70846 and
15.79880 mm. The 1.2 mm edge relief is a conservative nominal source space.
The underside reference reserves 1 mm below the active PCB area and stops at
X = 49.75 mm, before the unused end bearing. Do not add underside wiring at
that bearing. All selected header pads lie at X ≤ 36.957 mm. Final joints,
routes and strain relief remain open design work.

Run `BlackPillMountCheck.FCMacro` with `SC_CAD_DIR` set to this directory and
`SC_BLACKPILL_CHECK_RESULT` set to a new result path. Require its named PASS and
unchanged input hashes. The check includes all source body boxes, 21 pad bores,
actual bearing faces, nut paths, screw engagement, capture and vertical motion.
It tests capture with both source thickness values. Those test cases do not
establish a tolerance range. Physical dimensions, retention, vibration, joints,
temperature and wearing acceptance remain unmeasured.


## Fixed battery-sense loom

The bridge adds one printed part above the BlackPill. It uses the two far
retainers and their existing nuts. Its 1.35 mm floor starts 5.5 mm above PCB
bottom. The feet seat on both retainer tops. The two bridges share the longer screws. They keep the same
0.4 mm nominal projection through the nuts. The native check requires complete
foot bearing, full nut engagement and no solid intersections. This is a
component study; complete installed wiring and case acceptance remain open.

Fit the two selected 100 kohm MRS16 resistors parallel to source X. Their
centres are [20, 5.5] and [20, 10.5] mm, 8.7 mm above PCB bottom. Finish each
insulated assembly within a 12 × 3.5 × 3.5 mm space. R_SENSE_TOP pin1 exits at
[14, 5.5], pin2 at [26, 5.5]. R_SENSE_BOTTOM pin1 exits at [26, 10.5], pin2
at [14, 10.5]. Keep the selected B, SENSE and GND connections. Do not install
a separate sense PCB. The MRS16 source gives a 3.6 mm maximum body length and
1.6 mm maximum diameter. Its 0.5 mm lead diameter and 125 mg mass are nominal.
Its 29 mm minimum lead length and 5 mm minimum mounting pitch support the
specified trim. These values do not establish a supplied lead maximum.

Lay the KEMET C315C104K5R5TA beside the resistors. In source coordinates, its
maximum body spans X = 28..31.14 mm and Y = 7.095..10.905 mm. Its centre is
8.7 mm above PCB bottom. Form the two leads towards +X to a 5 mm joint pitch
at X = 34.14 mm, then trim them at X = 37.14 mm. Pin1 uses Y = 6.5 mm for
SENSE; pin2 uses Y = 11.5 mm for GND. The source permits a 1.76..3.32 mm
initial pitch and a 0.485..0.61 mm lead diameter. At the smallest pitch, the
specified lead path uses about 6.41 mm of the 7 mm minimum stock length.
Support the body during forming. Do not put a bend at the body seal. The
geometric allowance does not establish a qualified lead-forming process.

Make separate fixed lap joints to insulated 26 AWG signal wire. Keep each
capacitor joint inside X = 34.14..40 mm and a 3.5 mm outside-diameter gauge.
Use TE Raychem RNF-100-1/8-0-SP sleeves. Recover and inspect them before
installation near PETG. The source states a 95 C minimum shrink temperature
and 121 C full-recovery temperature. The TE A2 drawing, 29-May-2025, gives
3.2 mm minimum expanded ID, 1.6 mm maximum recovered ID and 0.50 ± 0.10 mm
fully recovered wall. The product page lists a wider wall tolerance. Neither
value is an installed joint OD limit. The finished 3.5 mm space is an assembly
gauge target, not a manufacturer guarantee. Verify sleeve coverage, insulation
and joint workmanship on the supplied parts. Do not shrink tubing in the case.

Use seven separate Alpha Wire LC134 BK088 square-knot spot ties through the
bridge slots: two on each resistor assembly, one on the capacitor body, and
one on each capacitor joint. Cut 70 mm blanks. Place the knots and short tails
in the modeled side spaces. Seat the ties without crushing a body, sleeve or
joint. The model reserves 1.7 mm width and 0.5 mm thickness around each loop,
plus its attached 4 × 2.2 × 2 mm knot space. These are finished assembly
spaces. They do not predict knot shape, tension or retention. Gauge the
assembled loom and keep loose wire away from components and screw tips.
The selected Alpha specification gives 0.060 ± 0.006 inch width and
0.014 ± 0.003 inch thickness. Its 25 lb minimum tape breaking strength is not
an installed knot or component-retention rating. Use the current product
specification; the older catalog gives different nominal thickness/strength.

Use separate taps on a continuous SENSE wire. Connect R_SENSE_TOP.2,
R_SENSE_BOTTOM.1, C_SENSE.1 and PA4 to that wire. Connect the two GND leads
to the fixed BlackPill return outside its PCB pad. Put one conductor through
each PCB hole. Final cut lengths, taps, strain relief and full installed
routes remain required; this component check does not supply those results.

Primary sources: [Vishay MRS16, 28724, 07-Mar-2016](https://www.vishay.com/docs/28724/mrs16m25.pdf),
[KEMET individual part sheet, generated 05-Nov-2026](https://search.kemet.com/component-documentation/download/specsheet/C315C104K5R5TA),
[TE RNF-100 part and A2 customer drawing](https://www.te.com/en/product-5052994073.html),
[Alpha LC134 specification, printed 13-May-2024](https://www.alphawire.com/products/accessories/fit-wire-management/lacing-tape/lc134),
and [Alpha lacing instructions, square knot figure2](https://www.alphawire.com/-/media/project/alphawire/alphawire/files/other/lacing-cord-installation-instructions.pdf?rev=4c0c10ce440d4bdfbef409fef7b4e7d7).
The part records retain the Vishay and KEMET original PDF hashes. Physical
fit, insulation resistance, vibration, retention and temperature remain
unmeasured. Do not count reference volumes as purchased parts or mass.

## Fixed discharge loom

Fit R_A, R_B, R_OUT, R_OFF, R_BOOST and R_LOAD on the second bridge.
Keep the selected circuit: each pin2 goes to GND. Connect pin1 of R_A to
S1.3, R_B to B, R_OUT to FIB_5V, R_OFF to LATCH_OFF, R_BOOST to BOOST_OUT
and R_LOAD to LOAD_5V. Keep the three output drains separate. An open
F_FIB must not isolate either the boost-output drain or the LOAD_5V drain.
R_OFF is 100 kohm; the other five are 1 kohm. All six are the selected
Vishay MRS16 1% 0.4 W axial parts. The source's power rating depends on
its stated temperature conditions; no enclosed thermal result is measured.

The second bridge has a 1.35 mm floor, 12.8..14.15 mm above PCB bottom.
Its two 7.3 mm columns sit on the first bridge at the existing far stations.
The source-coordinate resistor starts are:

| Part | Pin1 X | Y | Pin2 X |
| --- | ---: | ---: | ---: |
| R_A | 14 | 2.5 | 26 |
| R_B | 29 | 2.5 | 41 |
| R_OUT | 14 | 9 | 26 |
| R_OFF | 29 | 9 | 41 |
| R_BOOST | 14 | 15.5 | 26 |
| R_LOAD | 29 | 15.5 | 41 |

Each axis is 16 mm above PCB bottom. Transform these points with the same
BlackPill datum, 90-degree rotation and installed centre as the board.
Fit each resistor and its two separate lap joints in a 12 × 3.5 × 3.5 mm
gauge space. Use the same selected RNF-100 sleeves and external recovery
process as the RC loom. The 3.6 mm maximum body leaves 4.2 mm at each end
for formed lead and joint work. The 12 mm finished pitch exceeds the
published 5 mm minimum mounting pitch and uses less than each 29 mm minimum
stock lead. The 0.5 mm lead diameter and 125 mg mass remain nominal facts.

Use twelve separate LC134 spot ties, two per insulated assembly, at 3 and
9 mm from its pin1 end. Cut 70 mm blanks. Put each knot on the source −Y
side in the modeled space. The stock-section and knot-space conditions
remain the same as for the RC loom. The completed top is 18.25 mm above
PCB bottom, including ties. Gauge the joints, knots and tails before fitting.
Do not tighten the shared screws against the resistors, PCB or wires.

The native component check requires both complete column bearing faces,
seated screw heads, existing nut engagement, all original source body
spaces, all six resistors and assembly spaces, twelve ties and the new
bridge. It rejects a floating upper bridge and missing discharge parts.
Complete installed clearance, fixed external routing, insulation, heat and
retention remain separate checks. No physical test has run.
