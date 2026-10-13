# Amulet lighting preview

Run `just demo` from the repository root. The demo starts at 0.6 m, facing the
front, with indoor light and spiral rainbow. It needs Godot 4 with Forward+
and Metal on macOS:

```sh
brew install --cask godot
just cad
just demo
```

The saved FreeCAD model now uses the selected clear-centre finish on one
250 mm sheet of 0.060 inch clear acrylic. The demo compares that coating with a full-mirror coating on
the same mechanical assembly. Both have a black masked outer rim.

![Indoor front comparison](../hardware/enclosure/exports/demo-front-indoor.png)

Columns: selected clear centre, alternative full mirror coating. Top row: LEDs on. Bottom row: LEDs off. The view, pattern time, brightness,
exposure and environment match within each comparison.

[Watch the twelve-second Godot finish comparison](../hardware/enclosure/exports/lighting-demo.mp4).
Each finish gets the same six-second pattern segment, indoor light and moving
side-to-front camera path.
The [52-second Godot demo](../hardware/enclosure/exports/amulet-demo.mp4) also
shows a front-hemisphere sweep and all four lighting presets. All demo movie and GIF
frames come from Godot, including their animated LEDs and mirror reflections.

## Looping animations

[Explode and reassemble (GIF)](../hardware/enclosure/exports/exploded.gif) ·
[Full-resolution video](../hardware/enclosure/exports/exploded.mp4)

The preview shows pale green glow PETG in daylight and applies an assumed green bias to LED output. It does not simulate stored afterglow.
Three modeled black PET shields cover the exposed upper LED edges at the rings. The preview shows their geometry; it does not prove tape adhesion or the absence of light leaks in an assembled sample.

The 24-second exploded loop separates the current assembly, pauses with its
layers apart, then brings it back together. It keeps the front sheet and each
large printed circle whole. The centre module, paired printed rings and LED rows,
and rear electronics move as groups. The camera stays on the front side.
Parts, camera and moving rainbow return to their starting states at the loop
boundary. These are diagram positions, not removal paths or service clearances.
The separated front coating shows environment reflection; the infinity cavity
returns when the mirrors come back together.

[Spiral rainbow](../hardware/enclosure/exports/infinity-rainbow.gif) ·
[Ocean gradient](../hardware/enclosure/exports/infinity-ocean.gif) ·
[Sunset gradient](../hardware/enclosure/exports/infinity-sunset.gif)

Each sixteen-second loop moves from a 65° side view through the front, across to
the other side and back. Camera position, velocity and LED state join at the
loop boundary. All 494 LEDs show a moving spatial gradient, with two eight-second
colour cycles per camera sweep. Emission scale stays at 2: no pulsing, blackout
intervals or abrupt colour changes. Each loop shows the centre and all three
rings, with night light, a 0.46 m distance, fixed exposure 1, and assumed printed-ring
diffusion 0.65. These are illustration settings, not measurements.

The twenty-four-second `turntable.gif` now uses a ±70° front sweep, with two complete
rainbow cycles and no rear dwell. It also loops without a camera or colour jump.

## Controls

- Drag to orbit. Right-drag to pan. Use the wheel to change distance. Press `R`
  to reset the view.
- Use Front, ¾, Edge and Rear for fixed angles. Distance buttons select 0.3,
  0.5, 1, 2, 5 or 10 m. The status shows distance from the orbit target, angles,
  pattern time, frame rate and central diffusion.
- Select spiral rainbow, rotating spokes, radial waves, solid R/G/B, white or
  a single-pixel chase, ocean gradient or sunset gradient through all 494 LEDs. Pause stops pattern time. The four
  switches control the circle, halo, inward ring and outward ring separately.
- Select night, indoor, overcast or bright sun. Ambient intensity and light
  direction remain adjustable. Exposure stays at 1 unless you move its slider.
- Adjust front reflectance and transmission. Moving either control reduces
  the other when needed to keep their sum at or below 1.
- Adjust glow-ring transmission, glow-ring diffusion and centre diffusion. These
  are assumptions, not measured material values. Scroll the control panel to
  reach the view controls.

Changing the finish preserves camera position, time, light, brightness and
exposure. For a stationary comparison, pause first.

## What the image means

`hardware/enclosure/exports/amulet.glb` is the only generated scene asset.
`scene.json` holds part names, exact native bounds, dimensions, mirror planes,
494 emitting positions and directions, assumptions, and current mass estimates.
The exporter tessellates the saved assembled FreeCAD model in metres, with X
right, Y up and Z toward the front. It never uses print-bed STL translations.
Godot loads the GLB at runtime through `GLTFDocument`.

The cavity shader follows rays between Z=25.5 and Z=36.7 mm. It intersects the
finite annular cavity, central obstruction and cylindrical diffuser boundaries.
The opaque LED strips/carriers terminate rays at these boundaries. Each mirror
reflection reduces the remaining contribution. The shader stops below 0.1%,
after 32 reflections, at an opaque boundary, or when a ray exits the cavity.
The front coating reflects the environment. The cavity does not use screen-space
reflections. The direct printed rings, circle cells and reflected rings use one LED
colour texture, in the CAD pixel order.

The first three patterns use the formulas in `design-v2.md`, in linear RGB.
Each circle cell uses its CAD aperture and LED position. A variable Gaussian
spread approximates the centre diffuser. One shared ring model spreads each LED
across neighbouring angles and height for both direct and reflected light. It
uses a continuous surface with gentle LED peaks, without rectangular package
masks. Mirror attenuation still reduces successive reflected copies. It treats the glow PETG as a
transmitting, emitting surface backed by an opaque strip. These are design
approximations; the demo does not model scattering through an acrylic volume,
refraction, polarisation, coating angle response, wavelength response, real
luminance or camera adaptation. It does not simulate firmware power limits.

Default optical assumptions:

| Control | Value |
| --- | ---: |
| Front mirror reflectance / transmission | 0.65 / 0.25 |
| Rear mirror reflectance | 0.94 |
| Clear centre reflectance / transmission | 0.04 / 0.80 |
| Glow-ring transmission | 0.40 |
| Glow-ring diffusion / centre diffusion | 0.65 / 0.65 |
| LED emission scale / exposure | 2.0 / 1.0 |

The four light presets use relative scene intensities, not measured lux. The
CAD display transparency has no role in these values. Keep brightness,
coating, diffusion, fit, strength, dust and thermal tests in the existing
`SC-ENCLOSURE` physical TODOs.

## Selected mechanical assembly

The [enclosure guide](../hardware/enclosure/README.md) explains the 16 printed
parts, one-piece clear-centre front, assembly order, print settings and separate
rear service screws. The [section](../hardware/enclosure/exports/assembly-section.svg)
comes from the actual saved solids. The old quarter panels, seam straps, centre
snap rim and separate front acrylic cut files have been removed.

The rear mirror and all three printed glow rings remain. Their reflecting gap stays at
11.2 mm. The outer LED row follows the centre of its shorter outside ring. `scene.json`
records the native LED faces, part bounds, selected finish and complete installed
mass estimates for the pendant, necklace and external-battery option.
The alternate coating changes no geometry, camera, light, brightness or time.

## Checks and reproducible outputs

```sh
just demo-check
just demo-benchmark
just cad-check
```

`just demo-check` checks freshness, metadata and LED directions, imports every
named GLB mesh, compares imported bounds with CAD, exercises finish and optical
controls, and checks shared patterns and fixed exposure. On the GPU, 105 ray
cases compare the actual cavity tracing code with an independent unfolded-mirror
reference. The cases include spacing, attenuation, cutoff, the reflection limit,
centre obstruction and edge/rear rays. Rendered channels allow 0.009 absolute
error for framebuffer quantisation. GPU diffuser checks also verify smooth
inter-LED light, gentle peaks, continuity at the former package-mask edge, and
the same surface profile on all three rings.

`just cad` rebuilds the native model, validates CAD, slices all printed parts and fit samples, exports the GLB and metadata,
checks the demo, and captures both finishes under all four lights with LEDs
on and off. It repeats front, 72° steep, edge and rear views. It combines the 64
matched renders into 16 labelled comparison sheets. It also creates the Godot
demo, comparison video, sweep GIF, three moving gradient GIFs, and exploded
GIF/video. It decodes every output. FreeCAD supplies geometry and static engineering views;
Godot is the sole demo video renderer. The freshness manifest includes the demo sources and
outputs. The staged commit hook checks the same inventory. A stale or missing
asset prevents `just demo` and an ordinary direct Godot launch.

The build runs in temporary storage and publishes only after all stages pass.
The internal `--build-validation` mode permits checking that temporary build
before its final manifest exists. Use `just demo` for normal launches.

`just demo-benchmark` measures the actual scene at 1280 × 720 with the control
panel, default indoor light and optics, and an animated spiral. It warms the
renderer, then records 300 frame intervals per finish. It reports the renderer,
driver, GPU, mean, 95th percentile and average frame rate. Run it with other
render jobs stopped. Results describe this preview on that machine, not a
physical amulet.

The runtime import and renderer follow the official Godot documentation:
[GLTFDocument](https://docs.godotengine.org/en/stable/classes/class_gltfdocument.html),
[Forward+ and Metal](https://docs.godotengine.org/en/stable/tutorials/rendering/renderers.html),
and [reflection limits](https://docs.godotengine.org/en/stable/tutorials/3d/environment_and_post_processing.html#screen-space-reflections-ssr).
