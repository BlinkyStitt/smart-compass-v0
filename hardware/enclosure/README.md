# Round compass pendant

Open [smart-compass.FCStd](smart-compass.FCStd) in FreeCAD. The native document contains the parameter sheet, editable sketches and solid features, and separate manufactured parts. The first model uses **236 mm outside diameter × 54 mm depth**, before projecting buttons, screw heads, and necklace fittings.

This is a provisional assembly. It is suitable for design review. Measure the installed parts before you manufacture it. Physical checks remain deferred in [design-v2.md](../../design-v2.md).

![Exploded assembly](exports/exploded.png)

## Model and exports

| File | Use |
| --- | --- |
| `smart-compass.FCStd` | Native master; its `Parameters` sheet owns dimensions after the first build. |
| `Build.FCMacro` | Rebuild all dependent geometry and exports from saved spreadsheet values. |
| `parameters.json` | Initial seed only. It does not override an existing native master. |
| `fibonacci256-layout.json` | Published 256-point pixel map, with source attribution. |
| `exports/smart-compass.step` | Assembly for another CAD program. |
| `exports/*.stl` | Separate printed parts, in assembled coordinates and millimetres. Move each part onto the print bed in the slicer. |
| `exports/wood-fibonacci-mask.svg` | Nominal laser paths: outer outline, six bolt holes, 256 circle cells, and sixteen ring windows. |
| `exports/front-acrylic.svg` | Nominal laser paths for one front diffuser panel. |
| `exports/circle-alignment-overlay.svg` | Print at 100%; check the 166 mm circle, 100 mm scale line, and every LED centre. Use A3 or a tiled print at 100%; disable fit-to-page. Do not laser-cut this inspection overlay. |
| `exports/assembly-section.svg` | Actual solid section at Y=0 with overall diameter and depth dimensions. |
| `exports/front.png`, `assembly.png`, `exploded.png`, `electronics.png` | Native FreeCAD views. These are geometry previews, not optical simulations. |

## Light stack

Body coordinates are X right, Y top, and Z toward the viewer. The rear surface is Z=0. The dimensions below describe the initial seed.

| Part or surface | Z position, mm |
| --- | --- |
| Rear plate | 0–3 |
| Battery envelope | 4.5–28.5 |
| Controller/sensor PCB lower faces | 7 |
| Ring floor | 30–32 |
| Wrapped strip bodies, 10 mm wide | 32–42 |
| Circle edge seat | 36–37.4 |
| Circle PCB | 37.4–39 |
| Circle LED package references | 39–42 |
| Circle light baffle; rim feet extend down to PCB | 42.2–45 (feet: 39–42.2) |
| Laser-cut wood | 45–48 |
| Acrylic diffuser | 48–51 |
| Front bezel | 51–54 |

The circle has one opening per pixel. The openings follow the actual published Fibonacci point arrangement. The generator divides the surface into Voronoi cells and leaves a nominal 1.6 mm wood web between cells. The wood remains one connected part. A matching printed baffle separates the light below the wood. It starts 0.2 mm above the nominal LED package tops. Each unit can use a different cell outline later, while preserving pixel centres and the bolt pattern.

The source map gives 8-bit XY coordinates, not measured millimetres. The model sets the outermost LED centre radius to **79.5 mm**. Scale, mirror settings, and rotation remain adjustable. **TODO: SC-ENCLOSURE — Check the alignment overlay against the actual circle before cutting the mask.** No ideal golden-angle spiral substitutes for the published map.

The rings use cylindrical supports. Ordinary strip bends around those supports, with LEDs facing inward. The wood provides eight broad windows per ring. Start with white reflective channel surfaces; reflector shape and ring diffusion still need optical work. The first model focuses on the circle. It does not claim to isolate each ring pixel or prove the proposed light path.

| Ring | Pixels | Nominal strip length | Pitch-line diameter, with 3 mm seam gap | Front window diameters |
| --- | --- | --- | --- | --- |
| Inner | 72 | 600.0 mm | 191.9 mm | 177–189 mm |
| Outer | 80 | 666.7 mm | 213.2 mm | 199–211 mm |

Both seams start at the top. **TODO: SC-RING-GEOMETRY — Replace the provisional counts, strip width/thickness, and fit dimensions with measurements.** Density remains 120 LED/m. A pitch-line diameter differs from the case diameter and window diameters.

## Electronics, battery, and mounting

The rear layout holds Sparkle Motion, BlackPill, GPS, an IMU breakout, an RF95 carrier, and a small battery-divider board. Sparkle uses its published Rev D mounting-hole positions. BlackPill and the provisional sensor boards use edge rails and retention straps. Their rails avoid invented PCB hole locations. Bond the rail feet and battery cradle to the rear plate after you confirm the layout. Keep adhesive off straps, holes, and connectors.

Sparkle USB/power access is on the right. The radio passage is on the left; its antenna attachment and cable strain relief depend on the selected antenna. Two nominal 8.2 mm control holes are at the upper left/right rim. The lower opening reserves space for the physical power switch. Board component boxes are clearance references, not detailed board models. The GPS mount is flat in this first assembly; its final antenna angle remains open. Remove the rear plate to reach BlackPill USB/SWD and reset. Check access with the actual cables before manufacture. The side opening also provides a provisional microphone sound path.

The battery pocket is **154 × 74 × 24 mm**. It represents an insulated pack, not bare cells, contacts, or a charger. Two 10 mm hook-and-loop straps retain it. This space could accommodate a suitable wrapped 18650 assembly or a LiPo pack; cell arrangement, protection, charger, regulator, connector, and actual fit remain unselected. The battery stays below the optical floor. Sparkle supplies BlackPill; PA4 senses the protected/switched battery through the separate divider specified in the design.

The required runtime is **six hours of bright animated patterns**. Do not size the pack from a maximum-white test or promise six hours from the placeholder volume. Measure average input power with the intended patterns and current limits. Use `required usable Wh = average input W × 6 h`; include reserve and aging when selecting rated capacity. If you measure regulated output power, divide by measured conversion efficiency first. For illustration only, a sustained 5 V × 2.5 A load uses 75 Wh at the output in six hours, or 88.2 Wh at an assumed 85% conversion efficiency. Neither number is a measured workload.

**TODO: SC-BATTERY-THRESHOLDS — Select the pack and its power hardware, then set the sense circuit and voltage profile.** Do not connect a multi-cell pack directly until its voltage matches Sparkle and all LED requirements. A regulated USB-only pack can power the device but does not expose cell voltage for PA4 sensing.

Two 6 mm necklace eyes form part of the rear plate. The six perimeter bolts transfer the necklace load into the frame. Keep load off all PCBs and wiring. Use a cord/strap and nonmagnetic hardware near the sensor. The eye shape, print orientation, material, and load capacity remain provisional. The model reserves no magnetic clasp. Add a soft chest pad after checking vent access. The integral eyes are inside the rim, so the front outline stays round.

## Assembly sequence

1. Check the 1:1 circle overlay. Measure wood/acrylic thickness and laser kerf with a coupon. Apply kerf compensation once in CAM; the SVG paths contain none.
2. Print the frame, rear plate, bezel, baffle, cradle, and board rails. Use opaque material for light separation. Line the ring channels with suitable white reflective material. Confirm thermal suitability before bright operation.
3. Bond the cradle and rail feet to the rear plate. Install boards with nonmagnetic screws or straps. Pad and strap the insulated battery. Route paired LED supply/return wires away from the IMU. Add strain relief to cables.
4. Install the circle on its perimeter seat. Three feet on the removable baffle hold the PCB rim down against its seat. The generator places them clear of the nominal LED package bodies. Check those contacts against actual solder pads and LED packages before wearable use. Do not clamp LEDs or solder pads. Connect the rear headers before closing the enclosure.
5. Install both strips on their cylindrical supports. Leave the top seam spaces clear for soldered leads. Do not bend ordinary strip sideways. Confirm lead routing before retaining it.
6. Stack the matching baffle, wood mask, and acrylic under the bezel. The wood sits directly behind the acrylic. Avoid screws through pixel openings.
7. Clamp the stack with six M3 through-bolts and rear nuts. The nominal stack is 54 mm; start bolt selection around M3 × 60 mm, then select actual length from the fitted head, washer, nut, and thread engagement. Use nonmagnetic hardware. Do not use bolt torque to force a bad fit.
8. Install the necklace strap through the rear eyes. Support the front stack when you remove the rear bolts for service. Complete the deferred fit, suspension, wiring, magnetic, thermal, and light checks before wearing or running bright.

## Edit and rebuild

Use FreeCAD **1.1.4** or a compatible later version. The delivered model uses native spreadsheet, sketch, extrusion, primitive, and Boolean objects. It needs no persistent Python feature proxy.

1. Open `smart-compass.FCStd` and edit the `Parameters` sheet. Values use mm unless the row says otherwise. Save the document.
2. Run `Build.FCMacro` from FreeCAD's Macro menu. Set `SC_CAD_DIR` to this directory only if your macro runner does not provide the file path.
3. Inspect the rebuilt model. The macro checks solid validity, wood/frame connectivity, LED opening coverage, and intersections of the modeled manufactured parts and PCB/battery envelopes. It stops exports when a check fails.
4. Keep the master and its new exports together. Do not hand-edit an exported STL or SVG as a second source of dimensions.

The rebuild uses the saved spreadsheet, closes that document, and creates its replacement. Save before you run it. Some dimensions update through native expressions immediately; computed mask cells, ring radii, board positions, and exported contours require the macro. Layout changes can fail the collision check. Adjust the layout; do not disable checks to force an export.

For a headless build, run `FreeCADCmd Build.FCMacro` with `SC_CAD_DIR` set to this directory. GUI execution also produces PNG previews. FreeCAD must finish with `CAD BUILD PASS`; exit code alone does not prove that its Python script succeeded.

Run `Check.FCMacro` in FreeCAD to reopen and verify the saved model and exports. It also tests a spreadsheet expression without saving the test change. Save and close any edited master first.

Run the host mask checks with:

```sh
python3 -m unittest discover -s hardware/enclosure -p 'test_*.py' -v
```

## Sources and open fit work

- [Fibonacci256 specifications and Pixelblaze map](https://www.evilgeniuslabs.org/fibonacci256): circle diameter, PCB thickness, and indexed XY arrangement. Jason Coon / Evil Genius Labs supplied the published map.
- [Adafruit Sparkle Motion Rev D Eagle board](https://github.com/adafruit/Adafruit-Sparkle-Motion-PCB): 50.8 × 33.147 mm outline and hole centres. The model rotates the board 180 degrees to face the service opening.
- [Adafruit CAD parts, item 6100](https://github.com/adafruit/Adafruit_CAD_Parts/tree/main/6100%20Sparkle%20Motion): component-envelope reference.
- [WeAct MiniSTM32F4x1 V3.1 hardware](https://github.com/WeActStudio/WeActStudio.MiniSTM32F4x1/tree/master/Hardware): nominal BlackPill board envelope. The model does not redistribute the vendor STEP files.
- [Official FreeCAD releases](https://github.com/FreeCAD/FreeCAD/releases/tag/1.1.4): native CAD runtime used to build the model.

**TODO: SC-ENCLOSURE —** Measure board revisions, circle registration and hold-down, actual connector heights, antenna, controls, battery, and ring strips. Check circle retention, then finish antenna strain relief, GPS angle, wiring retention, and any required ring reflectors. Record mounting transforms. The current CAD does not prove connector access, magnetic isolation, load capacity, heat removal, optical performance, or six-hour runtime. Keep the physical validation work in the design's acceptance list; it is not part of this CAD delivery.
