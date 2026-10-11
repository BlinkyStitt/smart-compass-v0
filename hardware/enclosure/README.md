# Round compass pendant

Open [smart-compass.FCStd](smart-compass.FCStd) in FreeCAD. The editable model now uses **250 mm outside diameter × 45 mm depth**, before projecting controls, screw heads, and necklace fittings. The inner strip faces the Fibonacci circle. The outer strip faces radially outward, so its light is visible when you look at the pendant edge.

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
| `exports/*.stl` | One connected printed part per file, translated onto Z=0. Four quarters form each optical deck, lower barrel, rear support, and outer bezel. Board mounts and seam straps have separate files. |
| `exports/parts.json` | Generated STL list, solid volumes, and optical dimensions. Volume is not slicer mass or finished pendant mass. |
| `exports/wood-fibonacci-mask.svg` | Nominal laser paths: 166 mm outline and 256 circle cells. No ring windows. |
| `exports/front-acrylic.svg` | Nominal central diffuser outline. |
| `exports/front-mirror.svg`, `rear-mirror.svg` | Nominal annular acrylic outlines. The rear mirror includes a top wire notch. |
| `exports/edge-diffuser.svg` | Flat cutting template for the wrapped PET side band. Use a knife or a process approved for the selected sheet. |
| `exports/circle-alignment-overlay.svg` | Print at 100%. Check the 166 mm outline, 100 mm scale, and LED centres. The 196 mm sheet fits A4. Disable fit-to-page. Do not laser-cut this inspection overlay. |
| `exports/assembly-section.svg` | Actual solid section at Y=0 with diameter and depth dimensions. |
| `exports/front.png`, `assembly.png`, `exploded.png`, `electronics.png`, `edge.png` | Native CAD views. These show geometry, not simulated light. |

## Light stack and ring directions

Body coordinates are X right, Y top, and Z toward the front viewer. Rear Z=0. The table describes the current seed.

| Part or surface | Z position, mm |
| --- | --- |
| Open rear support | 0–1.6 |
| Battery envelope | 3.1–27.1 |
| Controller/sensor PCB lower faces | 5.6 |
| Thin annular optical floor | 27.65–29 |
| Rear mirror; reflecting surface at its front | 29–30.5 |
| Wrapped strip bodies, 10 mm wide | 31.1–41.1 |
| Circle edge seat | 30.6–32 |
| Circle PCB | 32–33.6 |
| Circle LED packages | 33.6–36.6 |
| Circle baffle; three rim feet extend to PCB | 36.8–39.7; feet 33.6–36.8 |
| Circle wood | 39.7–41.7 |
| Central diffuser and separate two-way mirror annulus | 41.7–43.2 |
| Outer bezel and central retainer | 43.2–45 |
| Wrapped edge diffuser | 30.5–43.2 |

The circle has one opening per pixel. Its inset Voronoi cells follow the published Fibonacci map, with a nominal 1.6 mm wood web. A matching opaque baffle separates the light below the wood. The wood sits directly behind the central diffuser. Neither part extends across the mirror gap.

The published map gives 8-bit XY values, not measured millimetres. The model sets the outermost LED centre radius to **79.5 mm**. Scale, mirror settings, and rotation remain editable. **TODO: SC-ENCLOSURE — Check the alignment overlay against the actual circle before cutting the mask.**

| Ring | Direction | Pixels | Nominal strip length | Pitch-line diameter, including 3 mm seam gap |
| --- | --- | --- | --- | --- |
| Inner | Radially inward toward the circle | 84 | 700.0 mm | 223.8 mm |
| Outer | Radially outward toward the edge diffuser | 90 | 750.0 mm | 239.7 mm |

Both strips use **120 LED/m**. Each carrier supports the strip's back. Ordinary strip wraps around the cylindrical carrier in its normal bend plane. Do not bend it sideways to make a front-facing flat ring. Both seams start at the top, with independent rear lead exits and slack for service. Pixel positions include the one seam gap; they do not distribute that gap between every LED.

The inner LED package faces sit about **26.7 mm outside the circle edge**. The central retainer and outer bezel leave an unobstructed **22.5 mm radial mirror view**, from radius 88 to 110.5 mm. The rear acrylic carries full mirror film on its front surface; the partly reflective front annulus faces rearward. Their reflecting surfaces have **11.2 mm separation**. The 10 mm strip sits between them with 0.6 mm clearance at each end. Keep these faces parallel and keep the visible annulus free of wood, opaque radial ribs, and diffusing film. The circle boundary separates the mirror light from the shaped cells. If the selected mirror puts its reflective coating on another surface, update the surface separation and fit dimensions. This follows the [two-mirror arrangement described by Adafruit](https://learn.adafruit.com/make-it-glow-neopixel-and-led-diffusion-tips-tricks/infinity-mirrors); it does not prove the effect with the selected materials.

The outer LED packages point outward through a **12.7 mm tall edge band**. The opaque barrel stops below this band. The nominal 0.5 mm translucent PET sheet wraps at 123.5 mm inside radius; its upper and lower edges meet the bezel and barrel lips. Secure its top seam with removable clear tape. The model leaves about 1.5 mm between the LED package fronts and the sheet. No printed outer wall blocks the radial light path.

**TODO: SC-RING-GEOMETRY — Measure strip cut intervals, length, width, thickness/coating, LED package depth, bend limits, pad clearance, and fitted seam gap. Replace the provisional 84/90 counts and fitted diameters. Keep at least 20 mm of clear mirror view when changing them. Record each output's part, protocol, order, timing, seam, and index direction.** Mirror transmission, flatness, edge diffusion, and light leakage remain deferred optical checks.

## Low mass and home printing

The current printed solid volume is **214.6 cm³**, compared with **389.2 cm³** in the previous model: about **45% less**. This compares CAD solids only, with no infill, support, adhesive, sheet, fastener, board, or battery mass included. The model reduces wall thickness and removes broad solid panels. It uses a **1.35 mm barrel and strip walls**, **1.6 mm open rear support**, **1.8 mm bezels**, **2 mm wood**, and **1.5 mm front acrylic/mirrors**. The battery cradle has an open centre. Rear ribs and mounting pads carry the boards and battery; the rear is not a closed cover. Add only a thin removable fabric or foam chest guard after checking ventilation and wire clearance.

The optical deck and lower barrel print as separate levels. Each level, the rear support, and the outer bezel split into four quarters. The deck prints floor-down; a 45-degree underside supports the circle seat. The baffle exports face-down with its rim feet up. Their butt seams use separate bonded splice straps; the barrel straps follow the inner wall. Assemble and bond each set on a flat surface. Keep adhesive off optics, strip pads, bolt holes, and the removable rear joint. The whole rear support still separates from the frame for service. These are provisional bonded joints; the CAD does not establish suspension strength.

The generator checks every exported STL against a **220 × 220 mm bed**, including 5 mm margin on each side. Each file contains one connected part and starts on the print bed. Keep the exported orientation on the bed. Use local supports at the service-port roofs if the slicer requires them. The centre baffle and retainer fit without splitting. The one-piece laser-cut optical sheets remain larger than some print beds; they are not printed parts.

Start with a 0.4 mm nozzle and 0.2 mm layers. The 1.35 mm wall target is approximately three extrusion paths for a common 0.45 mm line width. Check actual paths in the slicer; nozzle diameter alone does not define wall width. Use extra perimeters around necklace eyes, screw posts, and joints. Thin skins need continuous paths, not a low infill setting that removes them. The provisional print basis follows [Prusa's wall guidance](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135). Choose an opaque material that suits the measured temperature. Physical print, joint, and load checks remain deferred.

## Electronics, battery, and suspension

The rear holds Sparkle Motion, BlackPill, GPS, an IMU breakout, an RF95 carrier, and a small battery-divider board. Sparkle uses published Rev D hole positions. Other boards use open-ended rails and straps, without invented PCB holes. Bond their feet to the matching rear pads after checking supplied boards. Component boxes are clearance references, not detailed board models.

Sparkle USB/power access is on the right. The radio passage is on the left. Two control holes sit near the upper rim; the lower opening reserves the physical power switch. Remove the rear support for BlackPill programming and reset. GPS angle, antenna attachment, connector access, and cable retention remain open fit work. Keep paired LED supply/return wiring away from the IMU.

The battery placeholder remains **154 × 74 × 24 mm**. It represents an insulated pack, with two 10 mm hook-and-loop straps. It does not select cells, topology, protection, charger, or regulator. Its 24 mm height limits further depth reduction. Sparkle powers BlackPill; PA4 senses the protected/switched battery through the separate divider specified in the design.

The target remains **six hours of bright animated patterns**. Measure average input watts with all services and the intended patterns/current caps, then multiply by six hours and add reserve/aging. At the illustrative 5 V × 2.5 A load, six hours uses 75 Wh at the output, or 88.2 Wh at an assumed 85% efficiency. These are sizing examples, not measured consumption or a runtime claim. **TODO: SC-BATTERY-THRESHOLDS — Select the pack and power hardware, then set the sense circuit, voltage profile, final envelope, and mass.**

Two integral 6 mm necklace eyes remain at X=±82 mm, Y=62 mm. Six perimeter M3 bolts transfer load into the frame. The three central M2 screws retain the circle's optical stack independently. Keep loads off PCBs and wires. Use nonmagnetic hardware near the sensor. Eye strength, bonded seam strength, strap, print orientation, and full pendant mass remain physical validation tasks.

## Assembly sequence

1. Check the circle overlay. Measure sheet thickness and laser kerf. Apply kerf compensation once in CAM; the SVG paths have none.
2. Print the quarter parts, seam straps, baffle, central retainer, battery cradle, and individual board mounts. Inspect slicer paths, bed fit, holes, and contacts.
3. Bond the four quarters of each optical deck, lower barrel, rear support, and outer bezel as separate subassemblies, with their matching splice straps. The through-bolts clamp the deck to the barrel. Fit the sheets without force. Keep all service interfaces removable.
4. Bond the board mounts and cradle feet to the rear pads. Install boards, pad and strap the insulated battery, and provide wiring strain relief. Keep wire loops clear of the open back.
5. Fit the rear mirror annulus on the optical floor, reflective face forward. Align its top notch with the inner-ring lead exit. Install the inward-facing inner strip and outward-facing outer strip on their respective carrier backs. Route leads rearward through the top exits.
6. Install the circle on its edge seat. Fit the baffle with its three PCB rim feet. Check actual pads and packages before clamping; the CAD only avoids nominal LED bodies.
7. Place the circle wood, central diffuser, and separate front two-way annulus. Put the mirror film toward the cavity. Fit the central retainer with three M2 screws into the pilot bores; start near M2 × 8 mm and verify engagement without reaching the PCB.
8. Wrap the edge diffuser, align its top seam, and fit the outer bezel. Clamp the assembly with six M3 through-bolts and rear nuts. The nominal stack is 45 mm; start near M3 × 50 mm and select actual length for heads, washers, nuts, and thread engagement. Do not use torque to force fit.
9. Fit the necklace strap and any removable chest guard. Support the front assembly when you remove the rear bolts. Retain physical fit, optics, suspension, heat, magnetic, and runtime checks in the deferred acceptance list.

## Edit and rebuild

Use the Homebrew FreeCAD app at `/Applications/FreeCAD.app`, version **1.1.4** or a compatible later version. The model contains native spreadsheet, sketch, extrusion, primitive, and Boolean objects. It needs no persistent Python feature proxy.

1. Edit `Parameters` in `smart-compass.FCStd` and save.
2. Run `Build.FCMacro` from FreeCAD's Macro menu. Set `SC_CAD_DIR` to this directory only if the runner does not expose the macro file path.
3. Inspect the rebuilt assembly and generated outputs. The macro checks connected solids, all 256 cell openings, part/PCB/battery and LED-body collisions, and each radial light path. It rejects an obstructed mirror gap or an oversized print part.
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

**TODO: SC-ENCLOSURE — Measure component revisions, circle registration, rim contacts, battery, controls, strips, and sheet materials. Finish GPS angle, antenna strain relief, wiring retention, mirror flatness/retention, edge-sheet fit, and mounting transforms. Keep physical printing, assembly, load, optical, thermal, magnetic, and six-hour runtime evidence deferred. CAD checks do not establish those results.**
