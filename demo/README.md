# Amulet lighting preview

Run `just demo` from the repository root. The app starts with a posed mannequin
wearing the pendant on the night-time playa, with spiral rainbow. Use
**Presentation** to choose the worn night scene, a night pendant close-up, or
isolated design inspection. It needs Godot 4 with Forward+
and Metal on macOS:

```sh
brew install --cask godot
just cad
just demo
```

![Night mannequin presentation](../hardware/enclosure/exports/night-mannequin.png)

The saved FreeCAD model now uses the selected black LED centre finish on one
250 mm sheet of 3 mm nominal black LED acrylic. The demo compares that coating with a full-mirror coating on
the same mechanical assembly. Both have a black masked outer rim.

The capture command generates the canonical rainbow loops and three glow-material
rainbows with moving dark regions. Use the app to
inspect other patterns, lighting, coating finishes, and exploded assembly.

## Ring material versions

Use **Ring material** to select Glow PETG or Silver PETG. The view, pattern and
common geometry stay the same. Glow uses pale, matte material with green stored
emission. Silver uses a grey/silver surface, neutral RGB absorption and no
phosphor emission. Direct rings and reflections share the selected response.
Both models keep the 2.0 mm outside wall. Optical coefficients are assumptions;
production samples must establish actual transmission and diffusion.

[Glow model GLB](../hardware/enclosure/exports/amulet.glb) ·
[Silver model GLB](../hardware/enclosure/exports/amulet-silver.glb)

[Glow rainbow MP4](../hardware/enclosure/exports/infinity-rainbow.mp4) ·
[Glow rainbow GIF](../hardware/enclosure/exports/infinity-rainbow.gif) ·
[Silver rainbow MP4](../hardware/enclosure/exports/infinity-rainbow-silver.mp4) ·
[Silver rainbow GIF](../hardware/enclosure/exports/infinity-rainbow-silver.gif)

## Rainbow loop

The flat Fibonacci aperture faces use a broad luminous centre with soft edges.
The former steep Gaussian spots gave a false rounded lens appearance. The
continuous black acrylic cover and the original stencil still define the face.
This diffusion profile is qualitative; it is not measured photometry.

Each sixteen-second loop shows a pendant close-up at a fixed 0.46 m distance.
The camera follows a closed figure eight and crosses the centre head on twice.
The pointing-hand side stops at +20° to keep the finger clear of the display;
the other side reaches −50°. Elevation ranges from −20° to +20°. The mannequin
and a curved 3D playa panorama stay fixed in world space. A ground plane
continues beneath the wearer. Both designs use the same scenery and camera.
The mannequin stays visible behind the pendant. The separate full-body view
shows the complete pose at 3.5 m. Position, velocity and LED state join at the
loop boundary. All 494 LEDs show a moving spatial gradient, with two eight-second
colour cycles per camera loop. The movie check tracks the spatial rainbow
phase across the Fibonacci board and outside ring through the changing views.
The check first normalizes each observed RGB channel range to remove the fixed
material tint and phosphor offset; it does not use time to fit that normalization.
Each surface must complete two turns; uniform colour cycling or a frozen ring fails. Emission scale stays at 2, exposure at 1, and
assumed ring diffusion at 0.65.

The featureless mannequin is approximately 1.85 m tall. Its backward lean,
raised hand, pointing hand and plain backward cap give the oversized pendant a
Flavor Flav inspired wearing pose. The 250 mm pendant retains its CAD size.
The black 10 mm webbing and neck loop illustrate wearing context. The mannequin
and straps are display geometry; they are not extra print jobs or proof of fit.

The [night backdrop](assets/playa-night.png) is a generated illustration of dark
desert, distant camp lights and stars. Subtle amber and blue spotlights make the
wearer's pose visible. These lights and the existing sky reflections are
assumptions, not a measured reconstruction of the background or LED brightness.

Every assembled rainbow frame includes the stationary mannequin and curved 3D playa background.
Use **Design inspection** to examine the rear hardware or exploded assembly.

## Controls

- **Presentation** selects the worn night scene, worn night close-up, or
  design inspection. Reset restores the framing for that presentation.
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

## Rainbows with moving dark regions

Both viewers append **Rainbow • dark sectors**, **Rainbow • dark spirals**,
and **Rainbow • dark diagonals** to their menus. Existing menu IDs and the default
spiral rainbow stay the same. Each new style multiplies
the existing rainbow by a continuous mask. No random, frame-count, or stored
pattern state enters the calculation.

`demo/patterns.gd` takes mapped XY positions in metres and elapsed seconds `t`.
Let `a = atan2(x,y)/(2*pi)` (clockwise from the top). Let `q = (x,y)/0.0795`
for Fibonacci pixels, or `q = normalize(x,y)` for each ring or side row.
Let `r = length(q)`. Thus all mounted rings use unit radius; strip seams and
directions remain in geometry metadata. Wire order and LED counts do not enter
these formulas. Zero coordinates give finite colours, with angle and `q` zero.

| Menu style | Mask phase `p` | Motion of the dark regions |
| --- | --- | --- |
| Dark sectors | `2*a - t/8` | Two sectors rotate clockwise, one turn in 16 s. |
| Dark spirals | `3*a - 2*r + t/8` | Three winding bands rotate counterclockwise, one turn in 24 s; at a fixed angle they move outward by one normalized radius in 16 s. |
| Dark diagonals | `0.75*(q.x + q.y) - t/8` | Bands travel towards upper right at `(1/12,1/12)` normalized units/s. |

All phases repeat modulo 1. Each mask and its RGB output repeat after 8 s.
For all three styles, set `d = abs(fract(p+0.5)-0.5)` and
`u = clamp((d-0.18)/0.08,0,1)`. The mask is `u*u*(3-2*u)`.
Each period has a **0.36-phase exact-black plateau**, two **0.08-phase smooth
edges**, and a **0.48-phase fully lit plateau**. Each edge passes a fixed LED
in **0.64 s** at the default speed, above the 250 ms minimum. The mask and its
first derivative join continuously at black, full light, and repeat boundaries.
Integer angular coefficients prevent a seam at the top of a ring.

The RGB field is `rainbow(fract(a+2*r-t/8))*mask`, with alpha 1. The rainbow
interpolates between the six linear RGB vertices, without gamma conversion.
Brightness, material response, and stored glow remain downstream. These scalar
operations can use Rust `no_std` and `libm`: `sqrt`, `atan2`, floor-based positive
fraction, clamp, cubic interpolation, and six-sector RGB interpolation. Retain
the constants and the fixed geometry/time RGB values in `pattern_checks.gd`
when porting; do not move mounting transforms into a pattern.

The shared checks sample every mapped LED at **1/64 s** intervals over `[0,8)`.
They compare each real viewer adapter with the shared function. They check RGB
bounds, exact black, full light, motion through every LED, partly lit output in
every row, temporal continuity, cycle joins, the angular seam, origin, ring
normalization, frame-step independence, and fixed Rust parity values. Each row
prints its cycle-average summed-RGB reduction against the original full rainbow
at equal brightness. This is an **LED-output proxy**, not measured electrical
power. The viewer does not simulate firmware current limits. Black LEDs still
consume idle current. Numerical smoothness does not prove physical flicker
performance or battery life.

Reference reductions with the tracked layouts, identical times and brightness
(percent of summed linear RGB, not current):

| Layout / output (LED count) | Sectors | Spirals | Diagonals |
| --- | ---: | ---: | ---: |
| 250 mm / Circle (256) | 44.032% | 43.989% | 43.968% |
| 250 mm / Halo (64) | 43.987% | 43.987% | 44.160% |
| 250 mm / Inner (84) | 43.990% | 43.990% | 44.159% |
| 250 mm / Outer (90) | 43.991% | 43.991% | 44.159% |
| 200 mm / Fibonacci (256) | 44.032% | 43.989% | 43.968% |
| 200 mm / Inner (70) | 43.988% | 43.988% | 44.159% |
| 200 mm / Side row 0 (70) | 43.988% | 43.988% | 44.159% |
| 200 mm / Side row 1 (70) | 43.988% | 43.988% | 44.159% |

For a renderer-independent adapter check, use an absolute metadata path:

```sh
godot --headless --path demo --script res://check_patterns.gd -- "$PWD/hardware/enclosure/exports/scene.json"
```

For visual inspection, select each new style in both viewers. Watch the circle
and every ring or side row for at least one eight-second cycle. Check the top
seam, pause/resume, and each output switch. In the main viewer, compare Glow
PETG and Silver PETG with equal brightness and exposure. Stored glow can remain
visible where LED intent is black; pause freezes the pattern while glow charging
and decay continue. The stacked viewer retains its fixed illustrative charge.
Keep this visual evidence separate from numerical and physical-device checks.

## What the image means

`hardware/enclosure/exports/amulet.glb` and `amulet-silver.glb` contain the
generated CAD assembly. `mannequin.gd` adds the display-only wearer and webbing
at runtime. `scene.json` holds CAD part names, exact native bounds, dimensions, mirror planes,
494 emitting positions and directions, assumptions, and current mass estimates.
The exporter tessellates the saved assembled FreeCAD model in metres, with X
right, Y up and Z toward the front. It never uses print-bed STL translations.
Godot loads the GLB at runtime through `GLTFDocument`.

The board's 256 positions and pixel order come from [Evil Genius Labs' existing
Fibonacci256 Pixelblaze map](https://www.evilgeniuslabs.org/fibonacci256#pixelblaze-map).
The local coordinate table matches all 256 published entries. The native stencil
uses the original EGL STL from the supplied Thingiverse archive. Its 2 mm
thickness and volume match the original STL. All LED centres clear its walls;
actual board registration still needs a physical check.

The cavity shader follows rays between Z=23.5 and Z=34.7 mm. It intersects the
finite annular cavity, central obstruction and cylindrical diffuser boundaries.
The opaque LED strips/carriers terminate rays at these boundaries. Each mirror
reflection reduces the remaining contribution. The shader stops below 0.1%,
after 32 reflections, at an opaque boundary, or when a ray exits the cavity.
The front coating reflects the environment. The cavity does not use screen-space
reflections. The direct printed rings, circle cells and reflected rings use one LED
colour texture, in the CAD pixel order.

The first three patterns use the formulas in `design-v2.md`, in linear RGB.
Each circle cell uses its CAD aperture and LED position. A flat central
profile with soft falloff approximates the centre diffuser. One shared ring model spreads each LED
across neighbouring angles and height for both direct and reflected light. The
axial profile keeps a 5 mm central LED band and uses a smooth Gaussian tail.
Its maximum scatter scale is an unmeasured 3 mm assumption (about 2.0 mm at
the default diffusion). This leaves darker valleys between mirror copies and
makes the tunnel appear deeper at the fixed 11.2 mm mirror gap. Direct rings
use the same profile. The previous 8 mm scatter scale blended the copies
together. Mirror reflectance, transmission, exposure and glow decay remain
unchanged. Production samples must establish the actual axial spread. It
uses a continuous surface with gentle LED peaks, without rectangular package
masks. Sampling wraps around the whole ring, including the electrical strip joint. Mirror attenuation still reduces successive reflected copies. The glow PETG uses thickness-dependent RGB absorption, a small prompt green emission from blue light, and two stored green emission components. Both direct and reflected rings read the same charge texture. In live playback, LED and ambient light charge the material; disabling LEDs or reducing their brightness leaves the stored light to fade. Use **Precharge glow (illustration)** to set a charged starting state or **Clear stored glow** to remove stored emission. Pausing stops the pattern while charging and decay continue.

The model follows the qualitative [Prusa Ultraglow description](https://prusament.com/materials/prusament-petg-ultraglow/): light charges the pigment and its green emission fades after excitation stops. Charging weights favour blue over green and red. Assumed charge time constants are 6 and 60 seconds; dark decay time constants are 45 and 900 seconds. Initial charges are 0.35 and 0.20. These values, RGB absorption, surface grain, layer contrast and emission brightness need calibration against production-wall samples.

It treats the glow PETG as a transmitting, emitting surface backed by an opaque strip. These are design
approximations; the demo does not model volumetric scattering,
refraction, polarisation, coating angle response, measured spectral response, real
luminance or camera adaptation. It does not simulate firmware power limits.

Default optical assumptions:

| Control | Value |
| --- | ---: |
| Coated black front, cavity reflectance / transmission (estimate) | 0.70 / 0.09 |
| Rear mirror reflectance / transmission | 0.70 / 0.30 |
| Black LED centre surface reflectance / transmission | 0.039 / 0.29 |
| Glow-ring transmission | 0.40 |
| Glow-ring diffusion / centre diffusion | 0.65 / 0.65 |
| LED emission scale / exposure | 2.0 / 1.0 |

The shared `hardware/enclosure/acrylic-optics.json` records values and their sources.
[Two Way Mirrors](https://www.twowaymirrors.com/acrylic/) publishes nominal 70% reflection
and 30% transmission for its finished mirror sheet. The rear mirror uses this
model; transmitted rear light leaves the cavity. These are supplier values, not
independent measurements of the selected assembly.

The first design retains its custom one-piece black front. Its coated annulus
uses an **engineering estimate**, requested by Bryan: cavity-side reflection
70%, transmission 9%, absorption 21%; reverse-side reflection 10%, transmission
9%, absorption 81%. These values describe the complete coated black sheet.
They are not a measured specification for this custom coating.

[TAP/Chemcast](https://www.tapplastics.com/product/plastics/cut_to_size_plastic/black_led_sheet/668)
publishes approximately 29% transmission for uncoated Black LED acrylic. Clear
acrylic transmits about 92%, per the [PERSPEX Design Guide](https://www.perspex.co.uk/Perspex/media/General/technical-library/PDFs/Perspex-Design-Guide.pdf).
Assuming a similar mirror coating, 0.30 × 0.29 / 0.92 = 9.46%; the model rounds
that to 9%. The uncoated centre keeps 29% transmission. Its 3.9% surface
reflection is a Fresnel estimate using PMMA index 1.49, not a black-sheet
measurement. Reverse reflection of the coated sheet rounds to 10% after a
surface reflection plus a coating return through the black substrate twice.

Both designs share this coated-black-sheet estimate. The narrow design uses
it for its combined black cover/rear mirror, with clear 70/30 acrylic in front.
The complete-sheet coefficients include acrylic absorption: do not apply an
extra 29% or 92% factor. Scattering, spectral and assembled response remain
unmeasured.

The four light presets use relative scene intensities, not measured lux. The
CAD display transparency has no role in these values. Keep brightness,
coating, diffusion, fit, strength, dust and thermal tests in the existing
`SC-ENCLOSURE` physical TODOs.

## Selected mechanical assembly

The [enclosure guide](../hardware/enclosure/README.md) explains the 17 printed
parts, one-piece black LED acrylic front, assembly order, print settings and separate
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
named GLB mesh, compares imported bounds with CAD, checks full mannequin framing
and the fixed-distance figure eight with hand clearance at every saved view, exercises presentation, finish and optical
controls, and checks shared patterns and fixed exposure. On the GPU, 105 ray
cases compare the actual cavity tracing code with an independent unfolded-mirror
reference. The cases include spacing, attenuation, cutoff, the reflection limit,
centre obstruction and edge/rear rays. Rendered channels allow 0.009 absolute
error for framebuffer quantisation. GPU diffuser checks also verify smooth
inter-LED light, gentle peaks, continuity at the former package-mask edge, and
the same surface profile on all three rings.

`just cad` rebuilds the native model, validates CAD, slices all printed parts and
fit samples, exports the GLB and metadata, checks the demo, and captures the
matching rainbow movies and GIFs. It decodes every output. FreeCAD supplies
geometry and static engineering views; Godot renders the demo movies. The
freshness manifest includes demo sources and outputs. The staged commit hook
checks the same inventory. A stale or missing asset prevents `just demo` and
an ordinary direct Godot launch.

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

## Black LED acrylic and original stencil

The physical stencil now comes from Jason Coon's original EGL STL, at the
original 2 mm STL thickness. See the [source attribution](../hardware/enclosure/vendor/evilgeniuslabs-fibonacci256/SOURCE.md).
The 256 preview regions partition LED light only. The original native walls
clip every region; these regions are not an extra printed part. A flat central
profile gives each cell a broad face with a soft falloff at its edge.
This approximates the source photographs; it is not measured scattering.

One black LED acrylic sheet covers the front. Its assumed visible transmission
is 0.29, based on the supplier's approximate figure. We have no RGB spectrum
for our actual stock. The centre light crosses it once. Cavity light also
crosses the black substrate once after the mirror film. External film
reflection crosses it twice. The internal mirror reflectance stays unchanged.
The full-mirror centre comparison includes both film and black-sheet losses.
Surface roughness, cell diffusion, phosphor charging and decay remain
unmeasured assumptions. The manufacturer glow test used UV; RGB LEDs will
charge this material differently. Approve diffusion and afterglow from samples.

The amber camp light now sits behind the wearer. A fixed-camera comparison
identified the former front light as the source of the large right-side glare.
The blue rim light is also lower. Camera sweep, exposure and LED brightness
stay fixed.


Both enclosure previews load `patterns.gd` for the same spatial rainbow and
eight-second colour cycle. Captures upload LED colours before saving each frame.
The media check compares central LED colours at equal camera poses and different
phases. It also samples identical phases to distinguish colour motion from
codec and render noise.


Regenerate all Wide loops with `just cad`, then all Narrow loops with
`python3 designs/stacked/run.py build`, then publish with
`python3 site/build.py --output /path/to/compass-pages`. Each design owns its
`infinity-rainbow-dark-{sectors,spirals,diagonals}.mp4` exports. These use the
same 384-frame, 24 fps, 1280 × 720 figure eight and worn night scene as the
canonical rainbow, covering two eight-second cycles. Only glow PETG is captured
for the dark variants. No extra silver variants or GIFs are generated.

The masked movie check registers CAD board and outside-ring positions through
the moving camera and compares observed brightness to each documented mask,
allowing fixed stored glow, then checks the loop join. Canonical rotation
validation remains strict and separate. Source checks still establish exact
black intent and coverage of every ring/side row. Inspect saved loops for mask
shape, wearer context and transitions; this is optical evidence only.
