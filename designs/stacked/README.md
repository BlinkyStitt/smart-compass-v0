# Compact stacked Fibonacci concept

The pattern menu also offers **Rainbow • dark sectors**, **Rainbow • dark
spirals**, and **Rainbow • dark diagonals**. Both viewers use the same
position/time functions. The [shared pattern guide](../../demo/README.md#rainbows-with-moving-dark-regions)
defines the equations, directions, eight-second repeat, 0.36-phase black width,
0.08-phase edge width, 640 ms edge duration, and Rust parity checks. Every ring,
including each outside row, uses its mounted XY angle and unit radius. The side
switch still controls both outside rows. Pause freezes pattern time. This viewer
keeps its existing fixed illustrative glow charge.

`preview-check` runs shared numerical checks through this viewer's real adapter,
including per-row cycle-average RGB comparisons at 1/64 s intervals. To run only
these calculations without CAD import or a GPU, prepare the shared scripts and
use an absolute metadata path:

```sh
python3 -c 'import sys; sys.path.insert(0,"designs/stacked"); import run; run.prepare_preview()'
godot --headless --path designs/stacked/.build/preview --script res://check_patterns.gd -- "$PWD/designs/stacked/exports/scene.json"
```

Inspect all three styles in the interactive preview, including each side row,
the top seam, pause/resume, and the output switches. Compare Glow and Silver in
the main viewer as described in the shared guide. Report numerical results as
LED-output proxies. Preview images and smooth equations cannot prove electrical
savings, battery runtime, or physical flicker performance. Black LEDs consume
idle current; stored glow can obscure dark LED intent.

This is the second enclosure design. The original 250 mm design and its exports
stay in `hardware/enclosure`. This concept is 200 mm wide and 57.6 mm deep. It
uses the original 166 mm Fibonacci256, the original Evil Genius Labs stencil,
a 3 mm coated black LED acrylic rear mirror, a full-face 14 mm mirror cavity,
a 70-LED inward ring,
and two 70-LED outside strips behind one continuous 20 mm side diffuser. The GPS footprint rotates 90 degrees; all
component envelopes keep their original dimensions.

From front to back: front two-way mirror, empty cavity with inward ring, rear
coated black LED acrylic coupling mirror, 1 mm air gap, original stencil, LED
board, electronics
and internal battery, removable rear. The body and cavity frame form one printed
part. The separate front bezel uses six M2 × 6 countersunk screws and captive
M2 nuts with side insertion; the rear cover remains independent. The rear coating transmits the cell light
into the cavity and reflects returning light. Both coatings face the cavity.
The inward ring has 6.17 mm nominal clearance from the full 166 mm source.
Both mirror sheets are 187 mm in diameter; the front opening is 179 mm.
The strip loops move outward by 5.31 mm from the 190 mm design. The shell
keeps its 9 mm radial envelope; the board support, mirror seats, rear posts,
front screws and suspension slots follow the larger body. The original board
and electronics stay at their existing positions.
The 20 mm side band spans Z=14 to 34 mm. Its two 10 mm strips sit side by side
across the case depth, with LED rows at Z=19 and 29 mm. The case stays
200 mm wide and 57.6 mm deep. One side-band switch controls both rows; the
preview blends their emitted light through the full sleeve and blends stored
afterglow without tripling it. The outside sleeve has its own broad axial scatter
profile; the inner mirror ring keeps its narrow profile. The outside model
conserves each row's integrated source light as it spreads. Its assumed maximum
RMS scatter scale is 7.5 mm, scaled by the diffusion control. This is an
unmeasured material assumption, not a prediction for the printed sleeve.
The outside rows form one 140-LED side chain. The CAD keeps the board clips
inside that chain; actual jumper routing and fastening still need physical checks.

## Build and view

Use the same installed FreeCAD, Godot 4 Forward+/Metal and FFmpeg tools as the
first design. Run from the repository root:

```sh
python3 designs/stacked/run.py test
python3 designs/stacked/run.py build
python3 designs/stacked/run.py check
python3 designs/stacked/run.py preview-check
python3 designs/stacked/run.py preview
```

Edit `parameters.json`, then rebuild. All mirror and black acrylic coefficients come
from `hardware/enclosure/acrylic-optics.json`, shared with the first design. The saved CAD spreadsheet records the
inputs; the JSON owns regeneration. The build checks native solid collisions,
original stencil volume, runtime GLB meshes, pixel identities, bounded mirror
transport against an independent unfolded-ray calculation, and movie timing.
It publishes all checked outputs together and records source/export hashes.
The commit-time staged check is `python3 designs/stacked/run.py check --staged`.
The original `just` commands still operate on the first design.

Open [the native FreeCAD model](exports/stacked-fibonacci.FCStd) or
[the assembled STEP](exports/stacked-fibonacci.step).

## Compare the separate renders

Open matching files in two windows. Each design has its own files; no image
combines both designs. The first design remains at its original paths.

| View | Compact design | First design |
| --- | --- | --- |
| Full pose | [Night mannequin](exports/night-mannequin.png) | [Night mannequin](../../hardware/enclosure/exports/night-mannequin.png) |
| Rainbow | [MP4](exports/infinity-rainbow.mp4) · [GIF](exports/infinity-rainbow.gif) | [MP4](../../hardware/enclosure/exports/infinity-rainbow.mp4) · [GIF](../../hardware/enclosure/exports/infinity-rainbow.gif) |

Additional separate stills show [front](exports/night-front.png),
[angled](exports/night-angled.png), [side](exports/night-side.png),
[inner ring off](exports/night-inner-off.png), [all LEDs off](exports/night-leds-off.png)
and [exploded layers](exports/exploded.png).

The playa backdrop, body pose, camp lights, world camera positions, source
brightness, exposure, 38-degree field of view, gradient formulas and 16-second camera sequence match the first
design. The final webbing segments meet the compact rear anchors. The compact
pendant keeps its actual size; the camera does not enlarge it to fill the frame.
`exports/comparison.json` records the settings and shared asset hashes.

The preview provides separate cell, inward-ring and side-band switches, five
patterns, mirror reflection/transmission controls, orbit/zoom and exploded view.
At a head-on angle the repeated cell images overlap. Angled views show the depth
and shifted copies; the circular wall clips rays that leave the cavity.

## Evidence boundary

This is CAD and a qualitative optical preview, not a print-service release.
The digital model passes solid collision checks. Component envelopes, shelf
fastening, wiring, vents, suspension and actual supplied revisions still need
physical checks. No thermal, electrical, brightness, strength or assembly claim
follows from these renders.

The outer clear acrylic mirror uses nominal 70% reflection and 30% transmission
from [Two Way Mirrors](https://www.twowaymirrors.com/acrylic/). The inner mirror
combines the black cover and rear mirror in one 3 mm nominal sheet. Its coating
faces the cavity. No separate clear rear mirror or black filter remains.

The coated black sheet uses an **engineering estimate**, requested by Bryan:
70% reflection, 9% transmission and 21% absorption from the cavity. From the
black substrate side, the estimate is 10% reflection, 9% transmission and 81%
absorption. [Chemcast Black LED acrylic](https://www.tapplastics.com/product/plastics/cut_to_size_plastic/black_led_sheet/668)
has about 29% transmission without a coating. Combining that with the clear
mirror specification and clear acrylic's roughly 92% transmission gives
0.30 × 0.29 / 0.92 = 9.46%, rounded to 9%. This assumes a similar coating;
no published measurement establishes the custom coated black sheet.

The first cell image passes both mirrors: 0.09 × 0.30 = 2.7% before other losses.
The black-mirror value already includes substrate absorption; applying 29%
again would count it twice. The inner ring bypasses the black substrate. The
source brightness stays fixed. The case is 200 mm wide and 57.6 mm deep, with
1 mm between the original stencil and coated black sheet. The default mirror gap is 14 mm. The continuous outside band is 20 mm.

A mirror coating does not diffuse the LEDs. Scattering remains a qualitative
flat central profile with soft falloff because the black-sheet supplier gives no haze or
angular scatter data. Thin-sheet transport omits refraction and substrate
ghosting. Glow colour and stored emission also remain estimates. CAD and the
preview do not establish physical fit, brightness, optical flatness or thermal
performance.

The original stencil, attribution and source remain in
`hardware/enclosure/vendor/evilgeniuslabs-fibonacci256`. The compact model uses
the exact source contours and volume, including the open perimeter cells.


## Depth and mirror-gap input

Set `mirror_gap` in `parameters.json` in millimetres, then rebuild. The front
mirror, cavity, frame, bezel and total body depth follow that value. The board
and electronics do not move when you change the gap. With the lowered Z28 PCB,
12, 14, 16 and 20 mm gaps give 55.6, 57.6, 59.6 and 63.6 mm body depths.
The default 14 mm allows 2 mm clearance at each side of the 10 mm inner strip.
A 20 mm gap is an appearance choice, not an optical optimum proven by data.

The Radio and BatterySense shelves now sit at Z8 instead of Z27. Their XY
footprints do not overlap the other electronics. The original 20 mm battery
and SparkleMotion end at Z23, leaving 5 mm below the PCB. All board clips and
support posts derive their height from `circle_back_z`. Moving this battery
into the outer rim cannot lower the full-face mirror stack at 200 mm diameter.


The capture uploads the current LED colour field before each saved frame.
Both designs load `demo/patterns.gd` for their eight-second rainbow cycle.
The GPU check disables automatic updates and checks actual central cell RGB
at a fixed camera angle. Both captures use the same closed figure-eight camera path, crossing the
centre head on twice. The pointing-hand side stops at +20°; the clear side
reaches −50°, with −20° to +20° elevation. The mannequin and curved 3D playa remain fixed in world space;
only the camera moves. The movie check registers the actual CAD source locations
through those views and requires two spatial rainbow turns on both the Fibonacci
board and outside ring. A frozen ring, slow hue drift, wrong direction or uniform
colour cycling fails.
