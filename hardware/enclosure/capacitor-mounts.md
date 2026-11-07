# Horizontal bulk-capacitor holder

## Selected narrow assembly

Use this guide with the [fixed loom assembly guide](harness-assembly.md).
The complete narrow generation owns `installed-fit-check.json`, `loom-check.json`
and `inventory.md`. These records are in `designs/stacked/exports/` in the
repository and `04-REFERENCE/` in the service ZIP. A component test alone does
not establish installed fit or physical acceptance. Any Wide fixture data below
is an inactive component-study reference.

Use `designs/stacked/fasteners.json` for its 52 named narrow titanium cap screws.
The service ZIP includes `04-REFERENCE/fasteners.json`. All other hardware keeps
its specified parts, materials and mass allowances. Gauge the actual stock,
finished length, thread/runout, head fit and full nut engagement. Physical fit,
retention and strength remain unmeasured.

This component fixture defines the selected can, lead shapes and holder.
The complete narrow generation supplies its installed joints, routing and
service checks. No physical thermal, fault, wearing or retention pass comes
from the nominal CAD.

Use Panasonic EEUFR1A102,1000uF10V+/-20%, FR-A. The retained original1September2025
sheet gives D10+/-0.5,L16+/-1.5, lead diameter0.6+/-0.05 and pitch5+/-0.5mm.
Its100kHz ratings are1.79Arms at+105C and28mohm maximum impedance at+20C.
Impedance at one frequency does not establish broadband ESR or installed heat.
The retained source index records original URLs, revisions and SHA-256 values.

Panasonic requires at least2mm free space above the pressure valve for a
6.3..16mm can. Its sleeve does not have a guaranteed insulating function.
Isolate the case and do not deform it, compress it or load its lead seal.
The selected holder leaves a2.5mm cylindrical valve reservation beyond the
maximum17.5mm body, with0.25mm maximum accepted axial motion. Inspect the
actual valve location and clearance. Leave the valve path free of wiring.

The can axis is Y atZ8.85mm. Set its lead-side face atY-5mm, pressure valve
toward+Y and negative stripe toward+X. P is the-X lead and N is the+X lead.
Verify the supplied markings before soldering. These are local fixture XY
coordinates; use the BulkCapacitor placement in the narrow parameters for the
case transform. Keep both lead axes at X = +/-2.5 mm. Form each lead from
Y = -5 mm/Z = 8.85 mm toward -Y, round the corner at Y = -12.6 mm with the
0.6 mm centreline-radius target, then rise to Z = 13.45 mm. The rounded
centreline target is about 11.94 mm, within the shorter lead's published
14 mm minimum stock. Support the body during forming; keep bends away from
the seal. These geometry targets do not qualify the forming process.

The selected lead/pitch variation occupies a 1.15 mm diameter gauge. The
horizontal lead channels retain 0.8 mm radius. Each added vertical joint
channel has 1.75 mm radius. Make the specified 3.5 mm coaxial split-strand lap
below each lead end. Keep every strand, recover the selected sleeve onto 2 mm
of intact wire jacket, and gauge the completed 3 mm outside diameter. Use the
actual C_OUT.P/C_OUT.N routes and finishes in the complete narrow records.
Empty clearance pockets do not establish solder or insulation quality.

Wide uses the two side posts atX+/-10/Y8.5mm. Narrow uses posts at
X0.5/Y-9.5 andX4.25/Y19mm. The latter clears the2.5mm valve reservation.
A1.35mm outer bridge joins its cover ear outside the valve path. Narrow's7mm
base strip clears the keeper hood; recut lead channels pass through the lead-side
post without reaching its screw bore. The two profiles share the can, shim,
hard-stop and source limits. Narrow uses the formed lead path above. The
profiles do not move the radio or controls.

The lower clamshell and two screw posts fuse into the actual rear panel. The
upper clamshell lifts off after removing two screws. Use selected
SSCF-M2-8-TI5 stock screws finished/deburred to 7.6 mm for Narrow and two
NUT203 M2-B A4 nuts. The inactive Wide component fixture uses its separate
6.6 mm finish target. Hard stops take the screw load. The nominal tip projection
is0.4mm. Gauge the actual stack and check full nut engagement.

Two nominal0.25mm polyester semicircular shims support the10.5mm maximum can
inside the11mm bore. Cut each representative shim17x6mm and trim/form it to
fit. Use selected RS PRO770-787 white polyester stock,0.25mm nominal. The source
does not give a thickness tolerance or an insulation certification. Gauge the
supplied film and finished fit. A smaller supplied can can need up to three
nominal layers per side; cut each layer to its own developed radius. Do not
force the lid closed or use the screws to compress the can. Reject a loose,
deformed or damaged can. Retention, film fit and lead-seal loads remain
unmeasured. The full BOM must account for the actual two-to-six shim pieces.

For physical qualification, record the actual can dimensions, film thickness,
layer count, finished screws, valve clearance and lead layout. Check that the
hard stops meet with no can deformation. Apply a5N axial handling test target
in both directions and record motion; reject motion above0.25mm. This5N target
is a prototype assembly test, not a published component rating. Inspect leads,
seal, can and insulation after testing. Keep the outcome unmeasured until the
built unit has evidence. Do not infer temperature or fault acceptance from it.

The native component check covers eight physical products plus three clearance
references and the integral rear material. It checks all closed intersections,
actual lower-shim support, connected rear geometry, complete hard-stop bearing,
full nut engagement and pressure-valve clearance. Missing parts, a thin valve
obstruction, floating hard stops and short screw engagement must fail.

Nut entries clear the corners. Wide lowers each nut into a9mm entry toward-Y;
Narrow uses a12mm entry at the lead-side post and9mm at the vent-side post,
both toward+X. Insert nuts before fitting the can, cover, other boards or
screws. The native check sweeps the outer nut profile through lowering and
sliding against the integral rear. The compact interior screw has a2.15mm
radius counterbore and raised seat. Its2.35mm ear leaves1.55mm nominal wall
above the0.8mm-radius lead channel. Both designs use3.9mm-radius nut pods with7.2mm X flats. The source-sized
nut pockets keep at least1.35mm nominal surrounding wall.
