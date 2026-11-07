# Source-based PowerBoost mounting study

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

This component fixture uses the pinned Adafruit2030 Basic source PCB and two
Pololu2444 blocks. It does not release either enclosure or the fitted harness.
Supplied fit, soldering, retention, vibration and temperature are unmeasured.

The original Eagle board supplies both mounting holes, all through-pad drills,
the curved outline and the actual power pad coordinates. The mounting holes
are nominal2.5mm at(2.794,20.32) and(2.54,2.54), from the source board origin.
The module has two holes on one edge. Its component keepout radius is2.016mm.
Do not add a standard5mm DIN125 washer at the PCB: it exceeds this keepout.

Use two selected SSCF-M2-8-TI5 screws, finish/deburr to 6.8 mm under the
head, and two
NUT203 M2-B A4 nuts from the existing hardware inventory. Four source-hole
posts are not possible on this board. The two lower pods have3.1mm radii;
the final1.5mm post neck has1.95mm radius and bears on the actual PCB annulus.
The nut pocket roof is1.4mm at the selected PCB datum. Source component-side
heads have3.8mm nominal diameter. Finish/gauge the actual screw length and
check full nut engagement before installation. These are assembly targets.

The Wide PCB bottom is6mm, rotated90degrees. The Narrow PCB bottom is9mm,
rotated0degrees. Posts connect to the rear panel. The retained full loaded
reservation is30x45x14mm for Wide and45x30x14mm for Narrow, from the PCB bottom.
The1.6mm PCB thickness is nominal, not a supplied-board tolerance.

Each source terminal body has6.8mm depth and8.4mm height. Along the pin row,
the drawing gives3.5mm pitch and2.28mm from one outer pin to its body edge.
The two-pin body length is7.96mm. Reserve2.28mm at both ends, a conservative
8.06mm reservation that includes the0.1mm end asymmetry without assuming its
orientation. This is a nominal reservation, not a guaranteed dimensional bound.
Retain the maximum4mm published pin length: pins extend2.4mm below the nominal
PCB. The PCB has nominal1mm drills; the source pin diameter is nominal0.8mm.
The output block reaches X30.451mm beyond the29.21mm board outline.

Solder both blocks before mounting the PCB. Leave B1 JST and CN1 USB absent.
Leave all JP1 external connections open. Use one untinned18AWG input conductor
or22AWG output conductor per clamp and the selected5mm strip target. Route the
26AWG trip lead from the R20.2 collector after removing R20. Do not use the
other R20 pad. Fit and restrain the leads so a battery change applies no load
to these joints. Follow the actual route, joint insulation and boost-input
relief in the complete narrow loom. Its lacing captures W006 and the continuous
W044 negative conductor. The source-hole component check alone does not prove
that installed result or physical retention.

`BoostMountCheck.FCMacro` checks both nominal orientations, closed intersections,
connected posts, actual annulus support, full nut engagement and missing-part,
floating-post and short-engagement rejection. Its separate component reference
retains all earlier clearance outside the real terminal body and head keepouts.
Count the PCB/module once, two blocks and four fasteners in the installed BOM;
do not add reference volume to the physical mass. Enclosure integration and
all physical acceptance remain separate checks.

The captive-nut slot has8mm entry length and clears the nut corners, not only
the flats. Before fitting boards or screws, lower each nut into the open end
of its slot and slide it under the pocket roof. The native check sweeps the
actual outer nut profile through both motions against the rear interface.
Supplied nut dimensions, print fit and insertion force remain unmeasured.
