# Smart Compass Rev A print package

This package is for the 200 mm narrow prototype with the plug-in carrier and
rear USB-C pigtail. Use one copy of each of the 14 named STL parts. Use either
the glow or the silver 3MF for each diffuser.

## Set up the printer

The 3MF projects hold the verified geometry, orientation, and print settings
for a 220 × 220 mm usable bed, 0.4 mm nozzle and PETG. They include a brim and
have the skirt off. Load your printer and PETG profile before you make G-code.
Set the nozzle and bed temperatures for your filament. Keep the supplied
geometry and process settings. Check the preview after any profile change.
Check that brims clear clips and excluded areas on the actual plate.

Print the structural parts in opaque PETG. Use the support settings in each
project. Remove support and brim material before the fit check. Keep both
diffusers upright and support-free. Use an abrasion-resistant nozzle for
glow PETG and check the thin wall paths in the preview.

## Print and fit in this order

1. Print `BatteryCradle`, `BatteryDoor` and `BatteryKeeper`. Fit the M3
   hinge pin and keeper screw with their specified hardware. Remove burrs
   from the holes. Check free movement and positive latch engagement before
   installing contacts or a cell. Use a nonconductive dummy cell to check
   that the keeper holds it with the door open and releases it only when
   turned. Check retention in the hanging orientation.
2. Print `RearCover`. Check flatness and test the three panel switches, the
   disconnect boot, the rear seal groove, the battery bay and the right-angle
   gland. The gland elbow points down. Fit and remove the battery bay with the rear cover
   off the shell. Confirm that the hinge swings with the bay mounted.
3. Print the shell, front bezel, two diffusers, stencil, disconnect guard and
   four battery contact carriers. Check the rim and all fastener seats
   before fitting mirrors, wiring or the cell.

The rear cover has the pigtail opening, flat control seals and door-hinge
relief. Its STL and project must agree with the checksum in `parts.json`.
The enclosed FreeCAD and slicer reports give the digital checks. Confirm
print fit, latch and hinge strength, and gasket compression on the first
build. See the [Rev A design and assembly guide](https://github.com/BlinkyStitt/smart-compass-v0/pull/43).
