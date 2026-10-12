# Round compass pendant

Open [smart-compass.FCStd](smart-compass.FCStd) in FreeCAD. The selected design uses
one **250 × 1.5 mm acrylic front sheet**, with a clear centre, a two-way mirror
ring, and a black masked outer rim. The sheet sits at Z=36.7..38.2 mm. Printed
compression stops end at Z=38.5 mm. Rear vent guards add 2.85 mm before hardware.
The rear mirror and all three curved diffusers remain separate optical parts.

[Moving rainbow](exports/infinity-rainbow.gif) · [Ocean](exports/infinity-ocean.gif) ·
[Sunset](exports/infinity-sunset.gif) · [Godot video](exports/amulet-demo.mp4)

All demo videos and GIFs come from Godot. They use smooth spatial gradients and
slow, seamless side-to-front sweeps. The [demo guide](../../demo/README.md) lists
controls and unmeasured optical assumptions. Its alternative full-mirror coating
uses the same mechanical assembly. The saved CAD defines the selected clear-centre design.

![Assembly](exports/assembly.png)

## Fewer parts and separate service access

| Printed part set | Previous | Selected design |
| --- | ---: | ---: |
| Deck, barrel and rear | 12 quarters | 3 whole parts |
| Loose seam straps | 12 | 0 |
| Centre snap rim | 1 | 0 |
| Rim spacers | 3 | 3 |
| Replaceable necklace brackets | 2 | 2 |
| Vent guards | 4 | 4 |
| USB service cover | 1 | 1 |
| **Printed pieces** | **35** | **13** |

The three flat front acrylic pieces become one sheet. Integral sleeve shoes
replace six adhesive locating pads. The single wood cell grid remains; there is
no second full cell grid. The large printed parts have no glued quarter seams.

Use a **300 × 300 mm printer or print service**. The 249 mm rear needs at least
259 mm usable bed width with the specified brim. Do not scale the model to fit a
smaller bed: that changes the optics, electronics pockets, and fasteners.

Six M3 through-bolts at the original 233 mm bolt circle retain the front and
frame. Their rear washers/nuts bear on the barrel or necklace brackets. The rear
cover has 10 mm access clearances around these nuts. **Do not loosen these six
bolts for battery or board service.** Six separate M3 screws at radius 112.5 mm,
starting at 0° and spaced by 60°, attach the rear to captive nuts in the barrel.
The nut-loading slots face the open electronics compartment.

Remove only the rear screws to lift the rear and its electronics. Three integral
barrel seats hold the outside diffuser while the rear is off. The two independent
necklace screws retain the brackets. Support the pendant during all service.
Use unplugged connectors and service slack; do not hang the rear from wires.
The small rear hatch still provides USB access. Full rear removal provides
battery, board, SWD/reset, nut and wiring access.

## Print settings and orientation

Load [print-settings.ini](print-settings.ini) in PrusaSlicer, then select the
**actual printer and its PETG filament preset**. The file supplies print settings;
it does not select a printer, heater limits or start/end machine code.

| Setting | Starting value |
| --- | --- |
| Material / nozzle | PETG / 0.4 mm |
| Layer / first layer | 0.2 / 0.2 mm |
| Nominal extrusion width | 0.45 mm |
| Perimeters / top / bottom | 5 / 5 / 5 |
| Infill | 25% gyroid |
| Necklace brackets | 6 perimeters, 100% rectilinear infill |
| Brim / separation | 5 / 0.15 mm |
| Outer wall / wall / infill speed | 25 / 35 / 50 mm/s |
| Bridge / first layer speed | 20 / 20 mm/s |
| Supports | Off for the checked geometry |

Keep the exported STL orientation. Print the deck floor-down, the barrel
**deck-joint face down**, the rear skin-down, guards roof-down, and brackets flat.
The barrel's mounting bosses reach its bed face. The battery strap passages have
45° roofs with a short central bridge. The deck stays separate from the barrel
so its broad annular floor never prints as an unsupported ceiling.

The 1.35 mm thin walls use about three 0.45 mm paths even with five perimeters
requested. Five solid layers preserve the 1 mm rear skin. Inspect the actual
paths; wall count alone cannot make a thin wall thicker. These choices follow
[Prusa's model guidance](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135).

Use the filament maker's temperature profile and a PETG-compatible build surface.
Prusa recommends textured or satin surfaces and warns that PETG can bond too
strongly to smooth PEI. PETG also needs care with bridges and support removal.
[Prusa PETG guidance](https://help.prusa3d.com/article/petg_2059).

Run `just print-check` to slice every current STL with the checked settings.
The check rejects slicer warnings, empty output and support-dependent paths.
It uses temporary generic G-code for inspection and deletes it afterwards.
**Generate final G-code with the real printer profile.** Slicing does not prove
bed adhesion, layer strength, dimensional fit, or service life. Print and inspect
one bracket before committing to the large parts.

## Optical stack and load paths

![Assembly section](exports/assembly-section.svg)

The reflecting surfaces stay at **Z=25.5 and 36.7 mm**, with **11.2 mm separation**.
The useful front mirror annulus spans radii 85.5..110.5 mm. Keep opaque supports
outside the useful paths. The circle remains a floating island on its hidden seat.

The front sheet has six 6.6 mm holes over 6 mm locating collars. Six 8 mm bearing
lands support it. Washers stop on the collars, **0.3 mm above the sheet**. Use
soft annular washers under the metal washers to hold the sheet without rattling;
select their free thickness for this compression space. Bolt load travels
through the collars and frame. Do not use the wood or LED packages as stops.
Do not tighten screws to flatten warped sheet or printed parts.

The single wood grid uses **4 mm stock**, with **0.5 mm sheet clearance** and
**0.6 mm nominal LED clearance**. Three rim spacers contact clear PCB edge areas.
Tack the spacers to the wood rim so they lift with it. Use light, compliant rim
pads to restrain the grid below the sheet; keep them off the cell openings.
Measure stock and fitted gaps before assembly. The larger gaps need a physical
light-leak check; the demo is not a scattering simulation.

The halo and inner sleeves sit on **1.6 mm high integral shoes**, with **0.8 mm
high locating cuffs** on their LED side. The cuffs have 1.35 mm radial thickness.
The cuffs leave 0.25 mm radial fit clearance. The rear mirror has 0.3 mm
outer radial clearance. Matching notches provide sleeve-seat clearance and alignment. The front
sheet limits sleeve lift; the sleeves limit rear-mirror lift. Remove them from
the front in reverse order. No fixed overhanging lip traps the rear mirror.

| Output | Direction | Pixels | Strip length |
| --- | --- | ---: | ---: |
| Fibonacci circle | Front | 256 | PCB |
| Halo | Radially outward | 64 | 533.3 mm |
| Inner ring | Radially inward | 84 | 700 mm |
| Outer ring | Radially outward | 90 | 750 mm |

The three strips use 120 LED/m and one top seam each. Each carrier supports the
strip back. Bend the strip in its normal plane, not sideways into a flat ring.
Route independent leads through the top exits, with slack and removable seals.
Bond the outer strip only to the barrel below the Z=22.65 mm deck joint. Its
upper margin rests against the deck without adhesive. All outer LED packages
sit below that joint, so the deck can lift past the strip during repair.

The two cavity sleeves use nominal 1 mm dark diffusing acrylic, 0.8 mm nominal LED
clearance and 0.1 mm end gaps. The outside sleeve uses nominal 2 mm stock,
246/250 mm inside/outside diameters and Z=3.2..36.7 mm. Its LED row stays centred.
The clear centre means no mirror coating; its diffusion finish remains a
physical sample choice, with an adjustable assumption in Godot.
Use **light-transmitting** black material. Ordinary opaque acrylic will hide LEDs.
The 60% CAD display transparency is not a measured optical property.
Heat-form, cool and trim the bands. SVG developments are nominal forming
references, not proven final blanks. Match the tint across all three sleeves.

## Assembly and repair

1. Measure the boards, pack, LED strips and sheet stock. Set the saved spreadsheet.
   Rebuild. Laser-cut the one wood grid, front sheet and keyed rear mirror. Use
   `front-coating.svg` only as a coating map, not a cut file. Apply kerf once in CAM.
2. Print the 13 pieces in their exported orientations. Check flatness, nut slots,
   strap passages, bores, collars and sleeve seats. Fit-test hardware first.
3. Load the captive nuts. Fit the two necklace brackets and their independent
   screws. Use washers and full nut engagement. Smooth the rounded webbing slots.
4. Fit the LED strips and rear mirror. Seat both cavity sleeves in their shoes.
   Fit the outer sleeve on the barrel seats. Keep all three seams at the top.
5. Seat the circle PCB, three attached rim spacers and the single wood grid.
   Check all LED clearances. Fit the front sheet, soft washers and metal washers.
   Tighten the six body bolts against the stops. Check that the grid stays free
   of bolt preload. Select bolt length with the actual washer/nut stack.
6. Fit electronics and the padded protected pack to the rear. Use both battery
   straps. Install rated wiring, fuse, switch and connectors. Fit the covered
   controls, vent membranes/guards, USB cover/gasket and battery-entry blank.
7. Connect service leads, fit the rear with its six separate screws and seal the
   removable joints. The body nuts remain accessible through the cover clearances.
8. For battery or board repair, switch off, support the frame, remove the rear
   screws, and disconnect service leads. Leave the optical-stack bolts tightened.
   For optical repair, remove the front bolts and lift the sheet, grid/spacers,
   sleeves and mirror. Replacement parts do not require breaking frame glue joints.

The rear holds Sparkle Motion at (47,20), BlackPill, GPS, IMU, RF95, the divider,
and the Pololu boost at (72,-28) mm. Board envelopes remain provisional. The
protected 80 × 65 × 20 mm pack sits at (0,-33), with insulating padding, two
10 mm straps, a left lead exit and 2.5 mm top reserve. Disconnect it for external
charging. Use one factory pack at a time. The four-hour bright-pattern target
and provisional 1.25 A total 5 V current cap remain unchanged and unmeasured. See [battery and power details](battery-options.md).

The optional belt pack moves the candidate pack's 190 g off the neck. Its lead
uses the reinforced, capped 12 mm rear port at (43,84), follows the necklace, and
needs separate cable restraints. The lead must carry no necklace load. The gland,
cable, belt carrier and strain relief remain fit tasks.

The replaceable 5 mm PETG brackets have 12 × 4 mm rounded slots for 10 mm webbing.
Each uses the main body bolt and an independent M3 anchor. Use closed, deburred,
nonmagnetic metal rings and sewn loops. Replace a bracket or webbing without
replacing the frame. Keep spares. Check magnetic effects of all actual hardware.

Four covered 6 mm vents use nominal 16 mm adhesive ePTFE membranes and removable
bonded guards. Seal the side seam, lips, rear joint, bolt access clearances,
controls, hatch and lead exits with suitable removable seals. These vents provide
breathing; they do not prove adequate cooling or dust exclusion. The model has
no tested dust or IP rating.

## Sources, exports and checks

The saved `Parameters` spreadsheet owns dimensions. `parameters.json` supplies
initial values. Run `just cad` after editing and closing the master. It rebuilds
CAD, checks collisions/removal paths and meshes, slices all printed parts, then
renders Godot media. It publishes only after all stages pass. `just cad-check`
and the commit hook reject missing, stale or extra generated outputs.

`exports/parts.json` lists printed pieces, solid volumes, optical dimensions and
mass terms. `front-sheet.svg` is the sheet cut file. `front-coating.svg` marks
coating boundaries. `rear-mirror.svg` comes from the keyed native contour, with
at most 0.02 mm polygon chord error. `assembly-section.svg` cuts actual solids.
`amulet.glb` is the sole assembled Godot asset, in metres; STLs are print-bed parts.

## Current weight estimate

| Term | CAD estimate |
| --- | ---: |
| Printed PETG, solid-volume basis | 240.5 g |
| Acrylic, including all three sleeves | 194.3 g |
| Single wood grid | 16.7 g |
| **Mechanical subtotal** | **451.5 g** |
| Candidate internal pack | 190.0 g |
| **Subtotal with pack** | **641.5 g** |

The single front sheet is about 87.3 g after holes, or 87.6 g before holes,
compared with about 92 g for the previous three front pieces. The full mechanical
subtotal changes from about 456 g to 452 g. Fewer parts and simpler service are
the main gains.

Mass uses PETG 1.27 g/cm³, acrylic 1.19 g/cm³ and an unmeasured wood assumption of
0.60 g/cm³. Both subtotals exclude films, electronics, LEDs, wiring, fasteners,
seals, straps, gland and necklace. Slicer estimates use actual infill and include
brims; they have a different basis. Weigh the finished device. External battery
use removes the 190 g pack from the pendant; it does not reduce total carried mass.

Sources: [Fibonacci256 and pixel map](https://www.evilgeniuslabs.org/fibonacci256),
[Sparkle PCB](https://github.com/adafruit/Adafruit-Sparkle-Motion-PCB),
[BlackPill hardware](https://github.com/WeActStudio/WeActStudio.MiniSTM32F4x1/tree/master/Hardware),
[Prusament PETG density](https://www.prusa3d.com/file/3464616/prusament-petg-technical-data-sheet.pdf),
[ACRYLITE density](https://www.acrylite.co/files/content/acrylite.co/documents/product-information/ACRYLITE-cast-Physical-Properties.pdf).

**SC-ENCLOSURE physical TODOs:** verify actual materials, stock, kerf, circle
registration, formed sleeves, coating, diffuser uniformity, cell light leakage,
fit, nut retention, washer compression, sealing, connector access, thermal limits,
magnetic effects and four-hour runtime. Test complete suspension off-body at the
existing provisional 100 N per-side static target for 60 seconds in hanging and pull-out
directions. Set cyclic, snag and drop checks from measured assembled mass.
These are acceptance targets, not a load rating or proof of a successful print.
