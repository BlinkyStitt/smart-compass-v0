# Source-based PowerBoost mounting study

This component fixture uses the pinned Adafruit2030 Basic source PCB and two
Pololu2444 blocks. It does not release either enclosure or the fitted harness.
Supplied fit, soldering, retention, vibration and temperature are unmeasured.

The original Eagle board supplies both mounting holes, all through-pad drills,
the curved outline and the actual power pad coordinates. The mounting holes
are nominal2.5mm at(2.794,20.32) and(2.54,2.54), from the source board origin.
The module has two holes on one edge. Its component keepout radius is2.016mm.
Do not add a standard5mm DIN125 washer at the PCB: it exceeds this keepout.

Use two SSCF-M2-8-A2 screws, finish/deburr to6.8mm under the head, and two
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
to these joints. The full routes, joint insulation and strain relief remain
open work; the source-hole mount alone does not resolve them.

`BoostMountCheck.FCMacro` checks both nominal orientations, closed intersections,
connected posts, actual annulus support, full nut engagement and missing-part,
floating-post and short-engagement rejection. Its separate component reference
retains all earlier clearance outside the real terminal body and head keepouts.
Count the PCB/module once, two blocks and four fasteners in the eventual BOM;
do not add reference volume to the physical mass. Enclosure integration and
all physical acceptance remain separate checks.
