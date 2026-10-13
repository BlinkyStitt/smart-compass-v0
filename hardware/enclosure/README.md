# Round compass pendant

Open [smart-compass.FCStd](smart-compass.FCStd) in FreeCAD. The selected design uses
one **250 × 1.5 mm acrylic front sheet**, with a clear centre, a two-way mirror
ring, and a black masked outer rim. The sheet sits at Z=36.7..38.2 mm. Printed
compression stops end at Z=38.5 mm. Rear vent guards add 3.3 mm before hardware.
The rear mirror and all three curved diffusers remain separate optical parts.

[Moving rainbow](exports/infinity-rainbow.gif) · [Ocean](exports/infinity-ocean.gif) ·
[Sunset](exports/infinity-sunset.gif) · [Godot video](exports/amulet-demo.mp4) ·
[Explode and reassemble](exports/exploded.gif) ([MP4](exports/exploded.mp4))

All demo videos and GIFs come from Godot. The lighting loops use smooth spatial
gradients and slow, seamless side-to-front sweeps. The exploded loop separates
the current layers, pauses, and reassembles them. All main circles stay whole.
The [demo guide](../../demo/README.md) lists controls and unmeasured optical assumptions. Its alternative full-mirror coating
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
**Keep every main circle whole.** Stack the deck, barrel and rear along their
axis; do not split any of them into arcs to fit a smaller printer. The checks
require full-size, connected circular parts. The front sheet and wood grid also
remain one piece each.

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
| First-layer bulge compensation | 0.15 mm; check with fit samples |
| Outer wall / wall / infill speed | 25 / 35 / 50 mm/s |
| Bridge / first layer speed | 20 / 20 mm/s |
| Supports | Off for the checked geometry |

Keep the exported STL orientation. Print the deck floor-down, the barrel
**deck-joint face down**, the rear skin-down, guards roof-down, and brackets flat.
The barrel's mounting bosses reach its bed face. Product and fit-sample STLs
use 0.02 mm linear mesh deflection for smooth circular outlines. The battery
strap passages have
45° roofs with a short central bridge. The deck stays separate from the barrel
so its broad annular floor never prints as an unsupported ceiling.

The optical walls remain 1.35 mm, about three 0.45 mm paths even with five
perimeters requested. The lower barrel, rear ribs, USB cover and vent roofs
now use 1.8 mm material. Broader post roots and 1.8 mm rear bridges reinforce
connections without moving the LED carriers or mirror planes. Five solid layers
preserve the 1 mm rear skin. Inspect the actual paths; wall count alone cannot make a thin wall thicker. These choices follow
[Prusa's model guidance](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135).

Use the filament maker's temperature profile and a PETG-compatible build surface.
Prusa recommends textured or satin surfaces and warns that PETG can bond too
strongly to smooth PEI. PETG also needs care with bridges and support removal.
[Prusa PETG guidance](https://help.prusa3d.com/article/petg_2059).

Run `just print-check` to slice every product and fit-sample STL with the checked
settings.
The check rejects slicer warnings, empty output and support-dependent paths.
It uses temporary generic G-code for inspection and deletes it afterwards.
**Generate final G-code with the real printer profile.** Slicing does not prove
bed adhesion, layer strength, dimensional fit, or service life. Print and inspect
the fit samples and one bracket before committing to the large parts.

## Print the fit samples first

Use [FitDeck.stl](exports/FitDeck.stl), [FitBarrel.stl](exports/FitBarrel.stl),
[FitRear.stl](exports/FitRear.stl), [FitOptics.stl](exports/FitOptics.stl) and
[FitService.stl](exports/FitService.stl) with the same PETG, nozzle, layers and supplied
orientations as the full parts. These small samples are exact cuts from the
current CAD, not independently drawn substitutes. They are test pieces only;
they do not enter the 13-piece assembly or its mass estimate.

The tall sample with the front collar is the deck. The sample with the sideways
nut pocket is the barrel. The thin skin is the rear. Stack them in that order,
with the deck's broad floor on the barrel's broad joint face. Match the large
body-bolt bore and curved outside walls. The rear's large access hole surrounds
the body-bolt location; its smaller hole meets the barrel's captive nut.

1. Remove the brim and loose strands. The joint faces must sit flat by hand.
   A 3 mm screw must slide through each nominal 3.4 mm body bore without cutting
   a thread in the plastic.
2. Slide an actual M3 hex nut into the barrel's side pocket. It must seat fully
   and resist turning. Thread the rear screw by hand without using it to force
   misaligned parts together. Select screw length for the actual nut/washer stack.
3. Cut [fit-sheet.svg](exports/fit-sheet.svg) from an offcut of the chosen front
   stock, using the same laser kerf setting. Its 6.6 mm hole must drop over the
   collar. Fit the intended soft and metal washers. The metal washer must stop
   on the printed collar while the soft washer holds the sheet.
4. Correct first-layer bulge, extrusion or measured fit before the large prints.
   Keep nominal screw passages and washer stops intact. Do not scale the whole
   compass to correct a local hole fit.

Joint and rear screw entries have 0.3 mm, 45° lead-ins. Front collar tips and
their screw entries use shorter 0.15 mm lead-ins. The top bearing annulus now
has 1.0 mm radial width, up from 0.6 mm, at the same stop height. These guides help
parts start square. They do not make a tight joint acceptable. The slicer also
sets 0.15 mm first-layer compensation. Prusa explains how first-layer bulge can
change fits and how compensation interacts with the brim; inspect both in the
slicer. [First-layer compensation](https://help.prusa3d.com/article/elephant-foot-compensation_114487).

The optical sample contains both sleeve seats from the 30° station of the real
deck. Rest the corresponding sections of the actual formed bands on it without
forcing them. The nominal seat play is now **0.30 mm radially**; this preserves
at least **0.50 mm to the LED faces** at the inward limit of that play. The rear
mirror has **0.45 mm outer radial clearance**. These are starting allowances,
not measured fits. Check the full mirror and all three sleeve stations together
on the complete deck before coating or bonding. Do not widen the sleeve play
without checking the remaining LED clearance.

The service sample is an exact rear cut around one hatch nut pocket. Slide a
nominal **M2 hex nut, 4 mm across flats and 1.6 mm thick**, into its side mouth.
The pocket allows 4.4 mm across flats and 1.9 mm height. The nut must slide in by
hand, resist turning, and remain trapped along the screw axis. Test the intended
M2 screw before printing the rear. Do not substitute a taller locknut or force
an oversize nut. The sample does not test the full rear's stiffness.

Test the front collar with the actual sheet offcut and washers. Tighten only
until the metal washer contacts the stop. Confirm that the sheet stays retained,
the collar does not crush, and the sheet can move within its clearance without
cracking. Establish the usable tightening limit from a physical sample; the CAD
check proves bearing geometry, not an allowable torque.

Small samples cannot prove roundness or warping across a 250 mm part. Print the
whole barrel first, then inspect it after cooling. Check its joint face on a flat
surface and measure the diameter in two perpendicular directions. Keep the brim,
use a clean PETG-compatible build plate and avoid drafts. Use the chosen printer's
PETG cooling profile. Do not force a bowed part flat with the body bolts.
[Prusa warping guidance](https://help.prusa3d.com/article/warping_2011).

## Assemble the whole circles without juggling them

Work with the barrel upright on a flat padded surface. Align the recessed
**TOP** marks on the deck, inner barrel wall and inside of the rear. The marks
identify the same top sector. Align the deck's wire exits with the barrel's
exit. Insert two opposite body bolts loosely to guide the circles while you check the remaining holes. Keep all six bolts loose until
they pass freely. Then remove the temporary bolts as needed to install the optics.
The bolts guide the parts; they must not pull a distorted ring into position.

Dry-fit the rear and its six separate screws before wiring. Load the captive nuts
with the electronics compartment open. A short screw can hold a loose nut during
handling. Keep connectors unplugged and add service slack before closing the rear.
Tack the three tiny rim spacers to the wood grid before installing that grid, so
you handle one subassembly. Keep the single laser-cut grid aligned to the PCB with
the supplied registration overlay.

Each curved diffuser remains one continuous band with one top seam. It is not a
set of arc segments. Have the bands formed to the drawing or form them on a round
mandrel, then cool and trim. Do not use the LEDs as a forming tool. Test their fit
before applying mirror film or bonding the strips.

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
The cuffs leave 0.30 mm radial fit clearance. The rear mirror has 0.45 mm
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
2. Pass the five small fit-sample checks, then print the 13 pieces in their exported
   orientations. Check flatness, nut slots,
   strap passages, bores, collars and sleeve seats. Fit-test hardware first.
3. Load the captive nuts, including ten M2 nuts for the hatch and vent guards.
   Fit the two necklace brackets and their independent
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

Four covered 6 mm vents use nominal 16 mm adhesive ePTFE membranes and
screw-removable guards. Seal the side seam, lips, rear joint, bolt access clearances,
controls, hatch and lead exits with suitable removable seals. These vents provide
breathing; they do not prove adequate cooling or dust exclusion. The model has
no tested dust or IP rating.

Each guard uses two M2 screws, replacing the bonded feet. Its 1.5 mm stand-off
keeps the roof clear of the membrane. The roof prints flat on the bed. Two M2
screws also retain the thicker USB cover; its screws now enter replaceable metal
nuts rather than plastic pilot holes. The ten side-loaded nut pockets are
integral with the rear, so the printed part count stays **13**. This change adds
eight vent screws and ten nuts. Use the same M2 nut type throughout. Select screw
length with the actual gasket, cover and nut stack; tips must clear electronics.

Load the nuts with the rear removed. Their side mouths face +Y (toward TOP).
The roof and floor trap each nut along the screw axis; a loose nut can still
slide from its loading mouth during handling. A temporary screw holds it during
assembly. For membrane service, remove the two guard screws and lift the guard.
Keep the membrane's sealing face and screw passages sealed with replaceable
seals. A damaged nut can slide out after removal of the rear; no heating or
frame replacement is required.

## Ordering a print from a service

Keep the deck, barrel and rear as full, single-piece circles. Supply the STL
orientations, material choice and this assembly guide. Require the supplier to
review the mating-face flatness, six body-hole positions, collar stops and nut
pockets. Agree on the allowed errors before ordering; general print tolerances
do not establish functional fit or flatness. Have the supplier print the fit
samples with the production material and settings first. A full-size barrel
still needs inspection after cooling.

[Xometry's standards](https://www.xometry.com/manufacturing-standards/) require
individual review for guaranteed tolerances and otherwise let the supplier
choose orientation. [Protolabs Network's FDM guidance](https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/)
describes hole undersizing and build-direction effects.
[Xometry's design guide](https://xometry.pro/en/articles/fdm-design-tips/)
supports local ribs and stronger roots rather than excessive solid thickness.
The dimensions here remain specific starting values for this design.

PA12 SLS or MJF is a possible service alternative, not a verified drop-in
material change. Request a fresh fit and flatness review for that process;
[Protolabs Network](https://www.hubs.com/knowledge-base/hp-mjf-vs-sls-3d-printing-technology-comparison/)
warns that both powder processes can warp large flat parts. No supplier has
reviewed this design or agreed to its tolerances yet.

## Sources, exports and checks

The saved `Parameters` spreadsheet owns dimensions. `parameters.json` supplies
initial values. Run `just cad` after editing and closing the master. It rebuilds
CAD, checks collisions/removal paths and meshes, slices all printed parts and
fit samples, then
renders Godot media. It publishes only after all stages pass. `just cad-check`
and the commit hook reject missing, stale or extra generated outputs.

`exports/parts.json` lists assembly pieces, separate fit samples, solid volumes,
optical dimensions and
mass terms. `front-sheet.svg` is the sheet cut file. `front-coating.svg` marks
coating boundaries. `rear-mirror.svg` comes from the keyed native contour, with
at most 0.02 mm polygon chord error. `assembly-section.svg` cuts actual solids.
`amulet.glb` is the sole assembled Godot asset, in metres; STLs are print-bed parts.

## Current weight estimate

| Term | CAD estimate |
| --- | ---: |
| Printed PETG, solid-volume basis | 254.0 g |
| Acrylic, including all three sleeves | 194.1 g |
| Single wood grid | 16.7 g |
| **Mechanical subtotal** | **464.8 g** |
| Candidate internal pack | 190.0 g |
| **Subtotal with pack** | **654.8 g** |

The single front sheet is about 87.3 g after holes, or 87.6 g before holes,
compared with about 92 g for the previous three front pieces. The previous
whole-circle design had a 451.5 g mechanical subtotal. The stronger barrel,
ribs, stops and service mounts increase this to 464.8 g, a 13.3 g change before the added metal fasteners. Fewer assembly pieces and
replaceable service hardware are the main gains.

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
