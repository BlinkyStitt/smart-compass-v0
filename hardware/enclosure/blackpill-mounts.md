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

Fit four printed edge retainers and four M2 × 12 screws. Finish the under-head
screw length to 8.75 mm in Wide or 10.75 mm in Narrow, then deburr and check it.
The nominal tip extends 0.4 mm beyond the complete nut. The retainers seat on
hard stops. Their 0.8 mm edge overlap captures the board with 0.25 mm nominal
side clearance. Do not tighten them against the PCB or components.

Remove all four retainers and screws for straight board insertion/removal.
The component check covers a continuous 20 mm vertical motion before wiring
and case installation. It does not permit removing this board through fitted
optics or without disconnecting its wires. Battery access remains a separate
operation; the mounted electronics stay in place during a cell swap.

The 12 mm loaded-height reference keeps room for the module and later wiring.
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
