# Shared removable-cell compartment

This source implements a **compartment component study** for both enclosures.
The complete installed CAD, harness, inventory and service release still need
integration. The existing canonical files continue to describe the pouch design.
Do not use a passing component check as complete assembly or physical acceptance.

The [electrical input record](../../site/electrical-inputs.json) owns the selected
protected XTAR 21700 6000 mAh cell, including its 22.1 x 75.3 mm cell-only maxima
and published 76 g maximum. [battery-compartment.json](battery-compartment.json)
owns the common mechanism and specified assembly settings.
[battery_access.py](battery_access.py) creates the native solids and checks them.
The source contains no physical measurements or automatic physical-pass flag.

## Mechanism and source limits

The cell lies parallel to the face. An insulating cradle and terminal hoods
separate the removable cell from unrelated boards. A positive flex catch retains
the hinged door. A separate captive quarter-turn bar retains the cell when the
door opens. Both controls require deliberate movement. Engraved + and - strokes
remain visible in the empty compartment. The lower door saddles constrain seating.

Two fixed Mill-Max0854-0-15-20-82-14-11-0 contacts use screwed insulating flange
clamps. The2-Feb-2024 manufacturer drawing defines the nominal barrel, flange,
plunger and wire solder cup. It gives2.286mm stroke with+/-0.127mm stroke
tolerance and+/-0.1524mm ordinary length tolerance. The study uses2.159mm
available stroke. Finish both bores to2.75+/-0.05mm. At the source diameter limits, the minimum bore clears the maximum cup by0.1092mm in diameter. Each bore retains at least0.1621mm radial flange bearing. These are assembly gauge requirements, not guaranteed print output. The intended wire-mount cup accepts up to16AWG; use the
selected18AWG wire with its insulation outside the soldered cup. The cup has a
1.7018mm nominal bore and2.8448mm nominal depth. Physical insertion, solder
quality, strain relief and temperatures remain unmeasured.
[Maker sheet,2-Feb-2024](https://www1.futureelectronics.com/doc/Mill-Max/0854-0-15-20-82-14-11-0.pdf).

Set the unloaded contact-tip gap to **73.9 +/-0.1 mm**. Set the fixed negative
insulating stop for **1.82 +/-0.05 mm** negative-contact compression. These are
assembly acceptance targets. They are not achieved print dimensions or vendor
guarantees. Each clamp has compression tubes and nominal 0.25 mm insulating shim washers.
Replace matched shim stacks to set the actual tip gap, then lock and gauge the
carriers. Finish/shim the negative bearing face to its specified measured setting.
These initial setup operations do not occur during ordinary cell replacement.
Do not assume that the two springs divide compression equally.

Across the selected cell and assembly settings:

- Total initial contact interference is 0.3-1.5 mm.
- Pressing against the negative insulating stop leaves at least 0.27 mm at the
  positive end. The maximum negative-contact compression is 1.87 mm.
- The conservative remaining mechanical stroke is at least 0.289 mm.

The negative stop gives a defined release endpoint. The ribbon then pulls the
cell outward. The intended gold-plunger contact with the negative end face
requires a physical wrapper/end-insulator wiping test. Native clearance of the
barrel and fasteners does not establish scratch-free contact with a real cell.

Use unfinished **Bally Ribbon Mills pattern 4462, Type III Class 1A, 3/8 inch
nylon tape**, cut to 100 mm. The maker lists 0.015-0.025 inch thickness and
0.12 oz/yard maximum mass. MIL-DTL-5038K Table III gives +/-1/32 inch width
variation. The model reserves 10.31875 mm width and 0.635 mm thickness; the stock
cut weighs at most 0.373 g before sewing. Thread the fixed end around the
insulating anchor bar and sew the loop before enclosure assembly. Fold and sew
the free pull tab. Inspect and finish cut edges. The stock breaking-strength
figure does not rate the sewn joint or the installed mechanism.
[Maker](https://www.ballyribbon.com/mil-spec/5038),
[MIL-DTL-5038K, 22 June 2016, Table III, manufacturer mirror](https://acw1.com/wp-content/uploads/2024/08/ACW-MIL-DTL-5038K.pdf).

The JSON selects the hinge, keeper, clamp and four case-mount fastener sets.
The case mounts useM3x10 screws, M3 washers and M3 nuts. Their clamp stack
bears on a2mm rear interface without a floating flange. The hinge pin has a
head and retained nut larger than its bore. Two printed spacers and two M3
washers limit its nominal axial play to 0.2 mm. The keeper uses a button-head screw
and jammed nuts with specified rotational play. These parts remain installed
during ordinary access. Verify actual hardware, thread retention, clearances
and compass disturbance before physical acceptance.

## Checks and limits

Run the Python input and failure tests:

```sh
python3 -m unittest discover -s hardware/enclosure -p test_battery_access.py
```

Run `BatteryAccessCheck.FCMacro` in FreeCAD. For an isolated command, set
`SC_CAD_DIR` to this directory and `SC_BATTERY_CHECK_RESULT` to a new result file
outside Git, then pass the macro to the installed FreeCAD executable. Require
the **BATTERY ACCESS COMPONENT CHECK PASS** marker and matching result hashes.
FreeCAD exit zero alone does not confirm a pass. The macro preserves an existing
result file and rejects changes to its inputs during the check.

The native check verifies valid connected solids and closed-position interference,
including the cut 2 mm rear interface and all case-mount fasteners. The interface
check includes hinge-stem and latch-guard reliefs. An insulating hood covers
the keeper rotation slot. Upper cradle corners slope inward below the existing
Wide circle seat; the original board support and optics remain unchanged. It does not model the complete
rear ribs or the other installed parts.
It bounds continuous door/keeper rotation from sampled exact distances and the
maximum displacement between samples. The extraction check uses a continuous
axial/withdrawal volume, including the range of initial axial cell positions.
It checks the contact barrels, clamp screws and other fixed hardware. The
insulating stop is a declared bearing contact: it may touch the cell end face
but cannot intersect its volume. A 12 mm radius finger approach must remain clear.
The minimum-size cell displaced 1 mm outward must obstruct the closed saddles.
The flexible ribbon uses a representative maximum-stock drape.

These checks do not prove print tolerance, spring force, sewn strength, latch
strain or fatigue, compressed/trapped-ribbon response, dust sealing, actual hand
use, worn mass, electrical performance or temperature. Those physical outcomes
remain **unmeasured**. The common mechanism also needs both complete installed
assemblies, wire exits/strain relief, guarded power controls, the full mass and
balance ledgers, and illustrated service instructions before digital closeout.

The native function also accepts named fixed `surroundings`. It checks every
supplied solid against the closed components and all service motions. The
complete assembly caller must supply its full fixed-product census. An empty
list remains a component study; no argument marks an assembly complete. The
macro rejects a thin obstruction along a service motion as a negative test.

The native motion check keeps each fixed solid separate. It computes the exact
minimum distance and uses whole-solid axis-aligned box distances only as lower
bounds to skip solids that cannot improve an already computed minimum. It
does not exempt names or materials. The continuous-motion displacement bound
and required clearances stay unchanged. A thin obstacle in the service sweep
must still fail. This avoids repeated FreeCAD support-index work on one large
compound of every installed object.

## Fixed contact leads and main fuse

The component census includes two M22759/16-18 contact leads and a
Littelfuse0251004.NRT1L main-fuse reservation. The JSON owns the route.
Each lead has two6mm-radius quarter turns, a10.9691389296mm straight
section and a5mm inward return. The plane descends11.6degrees. Its fuse centre
isX41/Y-69.5/Z8.3814132935mm. The38.6540948511mm centreline plus3.5mm at each
end gives a45.6540948511mm cut target from50mm stock. These are fabrication
targets; fit and trim the actual joints. They are not measured lengths.

Use separate printed insulators. Each straight cup collar starts atX49.8mm
inside the end wall and ends atX54.5mm. Its inner/outer radii are1.6/2.95mm,
with0.3046mm source-tolerance cup clearance and1.35mm wall. The wire-only tube
starts atX54.4mm, overlaps the collar by0.1mm, and uses1.25/2.6mm radii. It
retains0.3229mm radial wire clearance and1.35mm wall. Keep the first bend at
X56mm, more than two wire diameters beyond the cup. The hood bridge starts
atZ2mm; at least1.3814132935mm remains below the fuse cavity. This specifies
connected geometry, not a measured bearing against the assembled rear skin.

The source wire maximum OD remains1.8542mm. The6mm bend radius exceeds
three diameters. Joint soldering, fuse lacing, insulation inspection and
strain relief still need assembly qualification and downstream design. No
accepted full harness follows from this component study. StandardM3x10 case
screws remain; the smaller wire-only tubes remove the need to shorten them.
[Wire catalog, printed page 41](https://www.amphenol-cit.com/wp-content/uploads/pdfs/prodinfo/M22759.pdf).

The 6 mm radius exceeds three times the wire's maximum diameter. This uses
NASA-STD 8739.4A Change 4 Table 7-1 as a workmanship reference for a harness
with AWG 10 or smaller wire, without coaxial or polyimide-insulated wire.
It is not a wire-maker flex limit or NASA qualification. The source also
requires fixed routing without installation stress and protected joints
outside bends.
[Source, pages 30–31](https://standards.nasa.gov/sites/default/files/standards/NASA/A/4/nasa-std-87394a_w_change_4_0.pdf).

The positive lead ends at the 20 x 5 x 5 mm main-fuse reservation. Its integral
insulating holder opens toward the rear, outside the cell opening. Fit it
before bolting down the cradle. Two lacing slots reserve joint restraint.
Lacing selection, joint insulation, downstream wiring, actual strain relief,
fault withstand and both full installed checks remain incomplete.
The electrical `fitted-harness` failure stays active.

The rear opening is 106 mm long. The end walls stay 2 mm thick. The long side
walls are 1.35 mm thick, with the existing 2 mm lower lip and 1.5 mm ceiling.
Each actual rear panel must support the full case-mount bearing ring at the
specified 2 mm datum. The checker rejects a thin rear skin below that datum.
These geometry checks do not establish printed strength.

For initial assembly, thread each unterminated50mm blank through its fixed tube.
Pull its contact end into the empty cell bay. Solder the contact cup off the
printed part. Let the joint cool completely. Pull the far wire end through the
fuse outlet while you slide the cup into its collar. Fit and gauge the clamps
and shims. Solder the fuse end last. Keep the wire insulation outside the cup;
the printed collar supplies secondary insulation. This sequence is a specified
process. Joint quality, retention and physical assembly remain unmeasured.
