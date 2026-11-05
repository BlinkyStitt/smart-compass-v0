# Latch module and wire-clamp mount

This is a source-based component study. Both complete installed assemblies and
all harness routes still need integration. A component pass does not close the
`fitted-harness` error or establish physical acceptance.

Use the Pololu2808 LV module, PCB psw03a. The retained manufacturer STEP model
contains the actual nominal PCB and populated components. Its bounds are
15.24 x17.78 x2.966 mm. Keep the model height; do not round it down to the
older dimension diagram's1.016 mm PCB plus1.9 mm component height. The
[index](sources/latch-2808/index.json) records original URLs, revisions and
SHA-256 hashes. The STEP header names20June2017; the dimension drawing
names12January2016. The maker's pinout identifies the component-side view.

| Assembly terminal | Source PCB X/Y, mm | Use |
| --- | --- | --- |
| VIN |1.27/16.51 |18AWG switched cell feed |
| VOUT |13.97/16.51 |18AWG PowerBoost input feed |
| GND |1.27/8.89 |26AWG control return to negative star |
| A |13.97/3.81 |On-only START to ground |
| OFF |1.27/3.81 |PowerBoost R20.2 shutdown request |

A is the **lower** right control pad. B is above it, at13.97/6.35 mm.
Connecting START to B does not implement the selected on-only control.
The maker's ±0.1 mm tolerance applies to hole **location**. The1.02 mm
hole diameter is nominal. Do not turn location tolerance into a diameter bound.
[Maker pinout and dimensions](https://www.pololu.com/product/2808/resources).

Install two **CamdenBoss CTBP2054/4** four-position2.54 mm rising-clamp
terminal blocks on the PCB underside, with entries facing outward. One strip
covers VIN/VIN/GND/GND; the other covers VOUT/VOUT/GND/GND. Use the upper
VIN and VOUT positions for18AWG. Use the lower GND position on the VIN strip
for26AWG control return. Leave the other five clamps empty and insulated.
The boost input return goes directly to the negative star. It does not pass
through the latch ground trace. Leave B,ON and CTRL without external leads.

The CamdenBoss catalog gives26–18AWG acceptance,6A/150V UL,8A/130V IEC,
20mohm maximum contact resistance and0.1Nm screw torque. It gives nominal
body size10.62 x6.2 x8.5 mm,0.8 x0.5 mm pins and3.5±0.3 mm pin length.
Use a4.5 mm strip **assembly target**; the catalog does not publish that strip
length. Check full conductor capture and keep insulation outside the clamp.
Put one untinned stranded conductor in each used position. Supplied fit,
soldering, screw retention, fault withstand and enclosed heat remain unmeasured.
Do not force pins or enlarge plated holes.
[Catalog15A, printed page6, version1](https://www.camdenboss.com/media/1546/camblock-plus-catalogue-15a.pdf).

The printed carrier has a32 x22.75 x1.35 mm floor atZ2 mm, centred atX0/Y-0.625 mm.
Its Y edges are-12 and10.75 mm. The shorter unused edge leaves0.25 mm
clearance to the Narrow pull-ribbon anchor at the selected module position.
The posts, spine, PCB bearing and terminal clearance stay unchanged. The PCB bottom is
Z12.2 mm. This leaves0.35 mm nominal clearance below the8.5 mm terminal
bodies. A central spine supports the real PCB underside. Four separate clips
bear on the side edges, clear of the populated centre. Each lip retains a
0.66 mm² bearing target at the source's minimum edge position. This area is a
geometry target. It does not establish retention strength.

Four DIN912 M2x20 A2 stock screws, finished to17 mm under the head, fasten the
carrier and clips through full2 mm case lands. Use eight DIN125 M2 washers
and four DIN934 M2 A4 nuts. The nominal complete stack leaves0.284 mm screw
tip projection above the nut. Gauge the stack, deburr the cut ends and verify
retention before use. These screws remain installed during cell replacement.
The carrier introduces no guessed PCB mounting holes.

Run the pure tests with `python3 -m unittest discover -s hardware/enclosure -p
'test_latch_mount.py'`. Run `LatchMountCheck.FCMacro` in FreeCAD with
`SC_CAD_DIR` set to this directory and `SC_LATCH_CHECK_RESULT` set to a new
result path outside Git. Require **LATCH MOUNT COMPONENT CHECK PASS** and
matching source hashes. Exit zero alone does not prove a pass.

The native check covers all24 products, connected valid solids, closed
interference, actual source-PCB bearing and a cut2 mm rear interface. Missing
parts, a clamp pushed into its washer and a whole clamp stack lifted clear of
the PCB must fail. It does not include complete enclosure bearing, full
installed service motions, wire cut lists, joint insulation or physical tests.
