# Round compass pendant

Open [smart-compass.FCStd](smart-compass.FCStd) in FreeCAD. The editable model now uses **250 mm outside diameter × 35 mm body depth**, down from 45 mm. Rear vent guards add 2.85 mm; modeled depth is **37.85 mm** before screw heads and necklace fittings. A removable **PETG rear** uses a **1 mm skin**, **1.6 mm wide × 2 mm high ribs**, thicker clamp lands, and integral mounts. Remove it to show the electronics. Clear filament will normally look translucent; opaque PETG also works. The inner strip faces the Fibonacci circle. A 64-pixel circle halo faces outward into the mirror gap. One outer LED row sits at the center of the broad black LED-diffusing acrylic side wall. The front border also stays black acrylic.

Two separate pockets now fit conservative **Adafruit 328 pack envelopes, 50.5 × 60.5 × 7.9 mm each**. A separate power-board envelope fits beside them. Connect only one pack at a time. These packs do not establish six-hour bright runtime; see [sourced battery options and energy limits](battery-options.md). Sparkle retains 1 mm nominal component clearance below the circle. The mirror keeps its 11.2 mm separation.

The infinity mirror occupies the annular gap around the circle. The circle keeps its shaped wood mask and central acrylic diffuser. Dimensions remain provisional. Physical checks stay deferred in [design-v2.md](../../design-v2.md).

![Exploded assembly](exports/exploded.png)

## Model and exports

| File | Use |
| --- | --- |
| `smart-compass.FCStd` | Native master. Its `Parameters` sheet owns dimensions after the first build. |
| `Build.FCMacro` | Rebuild geometry and exports from saved spreadsheet values. |
| `parameters.json` | Initial seed; it does not override saved sheet values. |
| `fibonacci256-layout.json` | Published indexed pixel map, with source attribution. |
| `exports/smart-compass.step` | Assembly in millimetres for another CAD program. |
| `exports/*.stl` | One connected printed part per file, translated onto Z=0. Four quarters form each optical deck, lower barrel and rear. Rear quarters include their ribs, board mounts, battery pockets and hatch posts. Necklace brackets and seam straps have separate files. |
| `exports/parts.json` | Generated STL list, solid volumes, and optical dimensions. Volume is not slicer mass or finished pendant mass. |
| `exports/wood-fibonacci-mask.svg` | Nominal laser paths: 166 mm outline and 256 circle cells. No ring windows. |
| `exports/front-acrylic.svg` | Nominal central diffuser outline. |
| `exports/outer-black-acrylic.svg` | One-piece opaque black outer front border: outer/inner circles and six M3 clearance holes. |
| `exports/front-mirror.svg`, `rear-mirror.svg` | Nominal annular acrylic outlines. The rear mirror includes a top wire notch. |
| `exports/edge-diffuser.svg` | Nominal flat forming reference for the black acrylic curved side wall; allow for forming and trim after forming. |
| `exports/circle-alignment-overlay.svg` | Print at 100%. Check the 166 mm outline, 100 mm scale, and LED centres. The 196 mm sheet fits A4. Disable fit-to-page. Do not laser-cut this inspection overlay. |
| `exports/assembly-section.svg` | Actual solid section at Y=0 with diameter and depth dimensions. |
| `exports/front.png`, `assembly.png`, `exploded.png`, `electronics.png`, `edge.png`, `rear.png` | Native CAD views. These show geometry, not simulated light. |

## Light stack and ring directions

Body coordinates are X right, Y top, and Z toward the front viewer. Rear Z=0. The table describes the current seed.

| Part or surface | Z position, mm |
| --- | --- |
| PETG rear skin; clamp/seal lands; ribs | 0–1; 0–2; 1–3 |
| Four rear vent guards | -2.85–0 |
| Rear service cover and gasket | -1.70–0 |
| Two separate battery envelopes; reserved fit/strap tops | 3.5–11.4; 13.9 |
| Controller/sensor PCB lower faces | 6 |
| Sparkle component envelope top; clearance below circle | 21; 1 |
| Thin annular optical floor | 17.65–19 |
| Rear mirror; reflecting surface at its front | 19–20.5 |
| Halo and inward strip bodies, 10 mm wide | 21.1–31.1 |
| Outside strip body, centered at Z=17.6 | 12.6–22.6 |
| Circle edge seat, sloping underside | 18.5–22 |
| Circle PCB | 22–23.6 |
| Circle LED packages | 23.6–26.6 |
| Circle baffle; three rim feet extend to PCB | 26.8–29.7; feet 23.6–26.8 |
| Circle wood | 29.7–31.7 |
| Central diffuser and separate two-way mirror annulus | 31.7–33.2 |
| Black acrylic outer front border and printed circle snap rim | 33.2–35; tongues reach 27.2 |
| Black acrylic curved side wall | 2–33.2 |

The circle has one opening per pixel. Its inset Voronoi cells follow the published Fibonacci map, with a nominal 1.6 mm wood web. A matching opaque baffle separates the light below the wood. The wood sits directly behind the central diffuser. Neither part extends across the mirror gap.

The **outermost front border is opaque black acrylic**, without mirror film. It is one sheet ring: **250 mm outside diameter, 221 mm inside diameter, 14.5 mm radial width**, and **1.8 mm nominal thickness**. Six **3.4 mm clearance holes** on a **233 mm bolt circle** match the body bolts. Measure the supplied sheet and set `Parameters.front_bezel_thickness` before rebuilding. This part has no printed quarter seams or splice straps. It captures the mirror's outer edge and the side diffuser's front lip. The mirror remains in the separate 25 mm gap around the circle.

The published map gives 8-bit XY values, not measured millimetres. The model sets the outermost LED centre radius to **79.5 mm**. Scale, mirror settings, and rotation remain editable. **TODO: SC-ENCLOSURE — Check the alignment overlay against the actual circle before cutting the mask.**

| Ring | Direction | Pixels | Nominal strip length | Pitch-line diameter, including 3 mm seam gap |
| --- | --- | --- | --- | --- |
| Circle halo | Radially outward from the circle into the mirror | 64 | 533.3 mm | 170.7 mm |
| Inner | Radially inward toward the circle | 84 | 700.0 mm | 223.8 mm |
| Outer | Radially outward toward the edge diffuser | 90 | 750.0 mm | 239.7 mm |

All three strips use **120 LED/m**. Each carrier supports the strip's back. Ordinary strip wraps around the cylindrical carrier in its normal bend plane. Do not bend it sideways to make a front-facing flat ring. All seams start at the top, with independent rear lead exits and slack for service. Pixel positions include the one seam gap; they do not distribute that gap between every LED.

The inward LED faces sit about **26.7 mm outside the circle edge**. The circle halo LED faces sit at radius **87.5 mm**, about **22.2 mm** from the inward LED faces. Each ring has a separate carrier and lead path.

The rear mirror carries full mirror film on its front surface; the partly reflective front annulus faces rearward. Their reflecting surfaces have **11.2 mm separation**. The two 10 mm cavity strips have 0.6 mm end clearance. The visible front annulus now spans radii **85.5–110.5 mm**, or **25 mm radial width**. Keep those faces parallel and free of wood, opaque radial supports, and diffuser film. This follows [Adafruit's two-mirror arrangement](https://learn.adafruit.com/make-it-glow-neopixel-and-led-diffusion-tips-tricks/infinity-mirrors); it does not prove the selected materials' effect.

The circle appears as an island. Its load travels through the hidden seat and annular floor behind the mirror. The halo carrier wall is nominally 1.21 mm thick. The front snap rim is **3 mm wide**, with outside radius 85 mm. A **0.5 mm radial gap** separates it from the front mirror. Three 6 mm long, nominal 0.6 mm snap tongues retain the face without visible screw bosses. The outward halo lights the island's edge and mirror repetitions. It does not put another strip on the circle's front. Snap fit, release force, light leakage, and the perceived floating effect require later physical checks.

The **curved outside wall is black LED-diffusing acrylic**, with no mirror film. It surrounds the body behind the black acrylic front border. Nominal dimensions are **246 mm inside diameter, 250 mm outside diameter, 2 mm wall thickness, and 31.2 mm height**. The outer LED row centers at **Z=17.6 mm**, about **1.0 mm behind the wall**. Its carrier continues across the optical floor's height, outside the floor radius. The structural barrel stays behind the LEDs. Keep a single top seam and seal it and both lips with removable clear tape.

Use a light-transmitting black diffuser grade so the LEDs remain visible through the dark wall. Ordinary opaque black acrylic would block them. [Adafruit's black LED-diffusion acrylic](https://www.adafruit.com/product/4594) is an example of this material type; its listed 2.6 mm thickness is not the selected 2 mm CAD stock. **The 2 mm thickness remains provisional.** Measure the chosen sheet and revise `edge_diffuser_radius` and `edge_diffuser_thickness` in the saved master before rebuilding. The wall must retain at least 0.5 mm LED clearance and fit beneath the front border.

Heat-form the wall to a cylindrical sleeve using the selected material supplier's process. Do not treat it as the former flexible PET wrap. `edge-diffuser.svg` gives a nominal **778.1 × 31.2 mm forming reference** at the wall's mid-thickness radius, with a 1 mm end gap. Allow for the actual forming process, then trim and fit the cooled sleeve; this is not a validated final blank size. Forming, seam retention, RGB transmission and full-height diffusion remain under `SC-ENCLOSURE`. CAD views show the unlit black surface, not simulated light.

**TODO: SC-RING-GEOMETRY — Measure cut intervals, length, width, coating/thickness, LED depth, bend limits, pads and fitted seams for the 64/84/90 strips. Replace provisional pitch diameters 170.7/223.8/239.7 mm. Keep at least 20 mm clear mirror view and center the outside row. Record each output's part, protocol, order, timing, seam and direction.**

## Low mass and home printing

The model uses thin printed supports and sheet optics. The generated [parts manifest](exports/parts.json) records solid volume; this is not slicer mass or finished pendant mass. The PETG rear uses a **1 mm continuous skin**, **1.6 × 2 mm ribs**, a **2 mm perimeter seal land**, and **2 mm clamp/control/vent lands**. Integral battery walls and board feet add local depth. The normal rear view is opaque; remove the cover to show the electronics. Clear PETG is an option for a translucent view, not optical clarity.

The deck, lower barrel and rear each split into four quarters. Rear ribs cross their butt seams; four **12 × 18 × 1 mm exterior lap straps** join the rear quarters. Their 1 mm projection stays within the existing vent-guard envelope. Bond and seal each subassembly on a flat jig. Keep the rear-to-frame joint removable. Board feet, battery pockets and hatch posts print with the rear, so these mounts need no acrylic adhesive joint.

The deck prints floor-down with a 45-degree circle-seat underside. Rear quarters print skin-down with ribs/mounts up. The baffle and circle rim export face-down with feet/tongues up; vent guards export roof-down. The black acrylic front border remains one sheet. Inspect any support needed for rail tie slots and battery strap slots.

The generator checks every exported STL against a **220 × 220 mm bed**, including 5 mm margin on each side. Each file contains one connected part and starts on the print bed. Keep the exported orientation on the bed. Check the snap beads, guard feet, screw pilots, and short internal wire passages in the slicer. The centre baffle and retainer fit without splitting. The one-piece laser-cut optical sheets remain larger than some print beds; they are not printed parts.

Start with a 0.4 mm nozzle and 0.2 mm layers. The 1.35 mm wall target is approximately three extrusion paths for a common 0.45 mm line width. Check actual paths in the slicer; nozzle diameter alone does not define wall width. Print necklace brackets flat with at least six perimeters and solid local fill around slots and both screws. Use extra perimeters around case posts and joints. Thin skins need continuous paths, not a low infill setting that removes them. The provisional print basis follows [Prusa's wall guidance](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135). Use PETG for the rear and suspension brackets, in clear or opaque filament. Select final material from measured temperatures; no heat or strength result is implied. Physical print, joint, and load checks remain deferred.

## Electronics, battery, and suspension

The removable printed rear holds Sparkle Motion, BlackPill, GPS, IMU, RF95, the divider, and a **23 × 45 × 10 mm power-board fit reference**. Sparkle stays at **(47,20) mm**; its component top at Z=21 leaves **1 mm below the circle**. The divider stays at (5,20). Sparkle uses published Rev D holes. Other boards use rails and straps. Their feet now merge into the rear skin and ribs. Component boxes remain provisional clearance references, and native checks include them.

The rear has a **249 mm outside diameter** and four sealed print seams. Six M3 bolts clamp its reinforced lands. The 38 × 18 mm service opening and M2 posts remain. Larger **16 × 8 mm rear clearances** surround the two **12 × 4 mm rounded webbing slots** in independent suspension brackets. Two covered 6.6 mm access holes reach the brackets' separate M3 anchors. Seal these holes after service. The rear carries electronics but does not carry necklace load.

The old two side pegs were Mode/Action actuator placeholders. The old rectangular side holes reserved USB/power, radio, physical switch, and ventilation. They are removed. The current model has:

- Rear Mode and Action controls at X=-35/+35, Y=100 mm, under 16 mm flexible covers. A third covered control at X=35, Y=-100 reserves the latching physical power switch. It is not a firmware power latch.
- One **38 × 18 mm rear service opening** centered at (48,54), covered by a **46 × 26 mm plate**, two M2 screws, and a nominal **0.35 mm compressed gasket**. Route a retained USB extension to it. The actual extension and switch remain measured-part work. Keep the cover closed during dusty use.
- An internal insulated RF antenna baseline. An external antenna would need a designed sealed feedthrough. Remove the full rear for BlackPill SWD/reset and board replacement.

All coordinates use the body frame above. Rear controls do not project from the side. Exact switch travel, flexible covers, connector access, GPS angle and antenna retention remain fit TODOs. Keep paired LED supply/return away from the IMU.

## Breathing and playa dust

The PETG rear has **four 6 mm vent holes** at X=±95, Y=±30 mm. Each uses a nominal **16 mm adhesive membrane patch**, with 5 mm radial overlap beyond the hole. Choose a particulate-blocking ePTFE part and its approved bonding surface. The 0.2 mm thickness is a placeholder, not a selected product.

Each separate **20 × 20 mm rear guard** stands 1.5 mm off the rear. It protects the patch and gives two turned air paths at its ends. Air still must cross the membrane. Bond the guard's two feet, leaving the other two sides open. The patches remain serviceable from those ends after guard removal. Do not substitute ordinary mesh and claim fine-dust exclusion.

Bond and seal all quarter seams. Use removable clear tape around the rear/side-sheet joint, diffuser lips/top seam and bolt penetrations. Seal the service cover and control-cover perimeters. Keep the optical cavity's wire exits closed with removable opaque sealant. Replace a damaged or clogged membrane.

These vents provide breathing and pressure equalization; they do not establish enough cooling for bright patterns. The Fibonacci manufacturer reports closed-enclosure heat problems. Measure heat with the intended current cap later. Sound pickup through the covered case also needs a check. The model has no tested dust or IP rating. [Burning Man dust/electrical guidance](https://burningman.org/black-rock-city/preparation/camping-tips/electrical-safety/), [membrane vent guidance](https://www.gore.com/products/protective-adhesive-vents-electronic-outdoor-enclosures).

The battery pockets hold two separate Adafruit 328 fit envelopes, with individual 10 mm straps, padding lands, lead exits and **2.5 mm top reserve**. A power board fits to their right. See [battery-options.md](battery-options.md) for dimensions, supplied-part differences, charger/boost limits, and the one-connected-pack policy. The six-hour bright-pattern target remains open; these internal packs cannot satisfy the current conservative idle-power model for six hours. Keep the power cap and final supply as explicit hardware decisions. Sparkle supplies BlackPill; PA4 measures the selected protected/switched battery before regulation.

## Durable, repairable necklace mounts

Two separate **5 mm PETG brackets** sit at the upper rear. Each has a **12 × 4 mm capsule slot** at **X=±82, Y=62 mm**, an **11 mm-radius slot pad**, and **14 mm-wide connecting webs**. Each bracket joins the nearest M3 body bolt and a second independent M3 screw at **X=±97, Y=48 mm**. The second connection uses an integral barrel boss and radial rib. Its **5.63 mm across-flat, 2.6 mm deep hex pocket** accepts an M3 nut. Fit the nut from the open front of the barrel before installing the deck. Use a washer under the independent screw; select length for 5 mm bracket, boss and full nut engagement, without projecting into the optics.

The load path is necklace → welded metal ring → replaceable **10 mm webbing loop** → PETG bracket → both screws and frame bearing seats → barrel/deck. The rear cover and boards are outside this path. Specify closed, deburred, nonmagnetic rings and sewn webbing loops; do not use glued loops or a split key ring as the load-bearing baseline. Select actual webbing, stitching and ring ratings before manufacture. Round and smooth the slot's print edges before threading. The rounded plan ends do not prove an abrasion-free printed surface.

The independent screw keeps each bracket attached when the six case bolts and rear are removed. Support the pendant during all service. To replace a damaged webbing loop, remove that bracket and exchange the loop. To replace a cracked bracket, support the frame, remove the rear and that side's main bolt/independent screw, and install a spare bracket without replacing the main shell. Keep two printed spare brackets, spare M3 screws/nuts and webbing loops. The nut pocket remains accessible after removing the optical deck; no buried insert requires destruction of the shell.

**TODO: SC-ENCLOSURE — Verify each complete attachment to a provisional 100 N static bench load for 60 seconds in its hanging and pull-out directions, then inspect skin, bracket, barrel boss, seams, hardware and webbing. Set final cyclic/snag/drop checks from measured assembled mass. Test off-body. These are acceptance targets, not a load rating. Check the full printed/bonded frame, replaceable hardware, magnetic effects, wear and repair access.**


## Assembly sequence

1. Measure the circle, strips, sheets and supplied battery/power parts. Set the master and rebuild. Cut the circle wood/diffuser, annular mirrors and black acrylic front border. Apply laser kerf once in CAM. Heat-form the side diffuser and trim after cooling.
2. Print deck, barrel and rear quarters, seam straps, baffle, circle rim, two suspension brackets, four vent guards and service cover. The rear quarters include the board mounts, pockets and hatch posts. Inspect pilots, slot bridges, ribs and continuous skin paths in the slicer.
3. Bond each set of quarters as a separate subassembly. Bond the rear's exterior lap straps, then seal all seams. Do not glue the rear to the barrel. Keep the deck removable from the barrel for captive-nut repair.
4. Fit two M3 nuts in the open-front barrel pockets. Fit webbing/rings to each bracket. Seat and secure the brackets with their separate M3 screws. Check washers, screw length and bracket-to-frame bearing surfaces.
5. Fit boards, individually padded packs and straps to the rear. Cap the disconnected spare connector. Retain wiring and the USB extension with enough service slack. Fit controls, vent patches, guards, hatch gasket and cover. Select a safe power source before connecting LEDs; the modeled small boost is not a final full-display supply.
6. Fit the rear mirror, inward strip and outward halo. Fit the outside strip centered in its broad diffuser. Route leads rearward and seal optical wire gaps.
7. Fit circle PCB, baffle, wood and central diffuser. Engage the three tested snap tongues. Fit the front two-way annulus and black acrylic outside wall/front border.
8. Fit the complete rear subassembly and six M3 through-bolts with washers. Select actual lengths and engagement. Seal lips, rear joint, quarter seams, webbing clearances, anchor access holes and fastener penetrations. Keep clearances sealed to the brackets without trapping webbing.
9. Support the pendant when opening it. Remove the six body bolts and lift the rear with its electronics; the two independent screws retain the brackets. Do not pull on wire slack. Physical fit, suspension, dust, optics, heat, magnetic and six-hour runtime checks remain deferred.

## Edit and rebuild

Use the Homebrew FreeCAD app at `/Applications/FreeCAD.app`, version **1.1.4** or a compatible later version. The model contains native spreadsheet, sketch, extrusion, primitive, and Boolean objects. It needs no persistent Python feature proxy.

1. Edit `Parameters` in `smart-compass.FCStd` and save.
2. Run `Build.FCMacro` from FreeCAD's Macro menu. Set `SC_CAD_DIR` to this directory only if the runner does not expose the macro file path.
3. Inspect the rebuilt assembly and generated outputs. The macro checks connected solids, all 256 cell openings, part/PCB/component-envelope/battery and LED-body collisions, necklace-to-frame contact, and each radial light path. It rejects an obstructed mirror gap or an oversized print part.
4. Keep the master and its generated exports together. Do not edit STL/SVG copies as a second dimensional source.

The macro closes the saved document and creates its replacement. Some native expressions update immediately; computed cells, ring positions, splitting, and exports require the rebuild. Fix a rejected layout rather than disabling checks.

For a headless build, use `/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd Build.FCMacro` with `SC_CAD_DIR` set. GUI builds also regenerate PNG views. Require `CAD BUILD PASS`; exit code alone does not prove a FreeCAD script succeeded.

Run `Check.FCMacro` to reopen and verify the saved model and exports. It tests a sheet expression without saving that test edit. Save and close any edited master first. Run host geometry checks with:

```sh
python3 -m unittest discover -s hardware/enclosure -p 'test_*.py' -v
```

## Sources and remaining measurements

- [Fibonacci256 specifications and map](https://www.evilgeniuslabs.org/fibonacci256): 166 mm circle, 1.6 mm PCB, indexed XY layout. Jason Coon / Evil Genius Labs supplied the map.
- [Adafruit Sparkle Motion Rev D PCB](https://github.com/adafruit/Adafruit-Sparkle-Motion-PCB): 50.8 × 33.147 mm outline and mounting holes.
- [Adafruit CAD parts, item 6100](https://github.com/adafruit/Adafruit_CAD_Parts/tree/main/6100%20Sparkle%20Motion): component-envelope reference.
- [WeAct V3.1 hardware](https://github.com/WeActStudio/WeActStudio.MiniSTM32F4x1/tree/master/Hardware): nominal BlackPill envelope.
- [FreeCAD 1.1.4](https://github.com/FreeCAD/FreeCAD/releases/tag/1.1.4): native model runtime.

**TODO: SC-ENCLOSURE — Measure component revisions, circle registration, rim contacts, battery, controls, strips, and sheet materials, including PETG skin/rib paths, rear seam bonds/seals, bracket/slot finish, webbing/rings and repair hardware, black acrylic stock thickness, side-wall forming and bolt clamping. Finish GPS angle, internal antenna strain relief, USB extension, wiring retention, snap fit, mirror flatness/retention, black side-wall seam retention, RGB transmission and full-height uniformity, membrane part/adhesive, rear seals and mounting transforms. Keep physical printing, assembly, load, dust, optical, thermal, magnetic, and six-hour runtime evidence deferred. CAD checks do not establish those results.**
