# Smart Compass Rev A print package

This package is for the 200 mm narrow prototype with the plug-in carrier and
rear USB-C pigtail. Use one copy of each of the 15 named STL parts. Use either
the glow or the silver 3MF for each diffuser.

## Set up the printer

The 3MF projects hold the verified geometry, orientation, and print settings
for a 220 × 220 mm usable bed, 0.4 mm nozzle and PETG. They include a brim and
have the skirt off. Load your printer and PETG profile before you make G-code.
Set the nozzle and bed temperatures for your filament. Keep the supplied
geometry and process settings. Check the preview after any profile change.
Check that brims clear clips and excluded areas on the actual plate.

Print the structural parts in opaque PETG. Use the support settings in each
project. Remove support and brim material before the fit check. Clear the
retainer toes and screw recesses before fitting the silicone pads. Keep both
diffusers upright and support-free. Use an abrasion-resistant nozzle for
glow PETG and check the thin wall paths in the preview.

## Print and fit in this order

1. Print `BatteryCradle`, `BatteryHatch` and `BatteryKeeper`. Check the
   keeper's travel and the hatch fit with a nonconductive dummy cell. Check
   that the keeper holds it while the hatch is off. Leave the battery contacts
   out until this fit check passes.
2. Print `RearCover` and `CarrierRetainer`. Check that the hatch lies flat
   and its screws seat. Dry fit the rear seal, buttons, disconnect boot,
   gland and carrier. Check that the retainer feet seat and its pads bear
   on the PCB edges and mounting holes.
3. Print the shell, front bezel, two diffusers, stencil, disconnect guard and
   four battery contact carriers. Check the lens and glow band seal lands
   before installing optics or wiring.

Use four M3 × 14 mm hatch screws with 0.5 mm washers and five
M2.5 × 25 mm button-head retainer screws. The rear cover has blind
tap pilots. The hatch, rear cover and lens seats use 1 mm silicone cord.
The assembly guide gives the seal sizes and fastener steps.

The rear cover has the pigtail opening, flat control seals and door-hinge
relief and blind pilots. Each STL and project must agree with `parts.json`.
The enclosed FreeCAD and slicer reports give the digital checks. Confirm
print fit, screw and keeper strength, and gasket compression on the first
build. See the [Rev A design and assembly guide](https://github.com/BlinkyStitt/smart-compass-v0/pull/43).
