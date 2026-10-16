# Compact stacked Fibonacci concept

This is the second enclosure design. The original 250 mm design and its exports
stay in `hardware/enclosure`. This concept is 190 mm wide and 72.6 mm deep. It
uses the original 166 mm Fibonacci256, the original Evil Genius Labs stencil,
a neutral cell diffuser, a full-face 20 mm mirror cavity, a 66-LED inward ring,
and three 66-LED outside strips behind one continuous 30 mm side diffuser. The GPS footprint rotates 90 degrees; all
component envelopes keep their original dimensions.

From front to back: front two-way mirror, empty cavity with inward ring, rear
two-way coupling mirror, cell diffuser, original stencil, LED board, electronics
and internal battery, removable rear. The body and cavity frame form one printed
part. The separate front bezel uses six M2 × 6 countersunk screws and captive
M2 nuts with side insertion; the rear cover remains independent. The rear coating transmits the cell light
into the cavity and reflects returning light. Both coatings face the cavity.
The inward ring has 0.86 mm nominal clearance from the full 166 mm source.
The 30 mm side band spans Z=14 to 44 mm. Its three 10 mm strips sit side by side
across the case depth, with LED rows at Z=19, 29 and 39 mm. The case stays
190 mm wide and 72.6 mm deep. One side-band switch controls all three rows; the
preview blends their emitted light through the full sleeve and blends stored
afterglow without tripling it. The outside sleeve has its own broad axial scatter
profile; the inner mirror ring keeps its narrow profile. The outside model
conserves each row's integrated source light as it spreads. Its assumed maximum
RMS scatter scale is 7.5 mm, scaled by the diffusion control. This is an
unmeasured material assumption, not a prediction for the printed sleeve.
The outside rows form one 198-LED side chain. The CAD keeps the board clips
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

Edit `parameters.json`, then rebuild. The saved CAD spreadsheet records the
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
| Ocean | [MP4](exports/infinity-ocean.mp4) · [GIF](exports/infinity-ocean.gif) | [GIF](../../hardware/enclosure/exports/infinity-ocean.gif) |
| Sunset | [MP4](exports/infinity-sunset.mp4) · [GIF](exports/infinity-sunset.gif) | [GIF](../../hardware/enclosure/exports/infinity-sunset.gif) |

Additional separate stills show [front](exports/night-front.png),
[angled](exports/night-angled.png), [side](exports/night-side.png),
[inner ring off](exports/night-inner-off.png), [all LEDs off](exports/night-leds-off.png)
and [exploded layers](exports/exploded.png).

The playa backdrop, body pose, camp lights, world camera positions, source
brightness, exposure, 38-degree field of view, gradient formulas and 16-second sweeps match the first
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

Initial front and rear coatings each assume 0.65 reflection and 0.25
transmission. The cell image crosses both coatings, so the preview includes both
losses and does not raise source brightness to compensate. Thin-sheet transport
omits refraction and internal substrate ghosting. Diffusion, glow colour and
stored glow use the first preview's unmeasured material model. Printed and
optical samples must establish transmission, colour loss, cell separation,
mirror flatness and the visible depth effect before fabrication approval.

The original stencil, attribution and source remain in
`hardware/enclosure/vendor/evilgeniuslabs-fibonacci256`. The compact model uses
the exact source contours and volume, including the open perimeter cells.
