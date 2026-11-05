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

Two fixed Mill-Max 0850-0-15-20-83-14-11-0 contacts use screwed insulating flange
clamps. The 2018-06-07 manufacturer drawing defines the nominal barrel, flange,
plunger and tail. The 2025-04-29 sheet gives 2.286 mm stroke and standard length
tolerance +/-0.15 mm. The study conservatively uses 2.136 mm available stroke.
[Dimensioned maker sheet](https://static.chipdip.ru/lib/717/DOC051717440.pdf),
[2025 maker sheet](https://static6.arrow.com/aropdfconversion/51cd24f6bbea76697111e1326022061c9a4b0141/085-00-152-08-314110.pdf).

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
- The conservative remaining mechanical stroke is at least 0.266 mm.

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
Littelfuse 0251004.NRT1L main-fuse assembly reservation. The common JSON owns
the lead targets. Each lead follows two 6 mm-radius quarter turns and a
10.5 mm straight section. The exact centreline is 33.3919559 mm. Add 3 mm at
each end for the specified lap joint. The finished cut target is 39.3919559 mm
from a 42 mm blank. These are fabrication targets, not measured lengths.
Positive and negative use separate conduits. A thicker bundle needs a new
bend-radius review.

The wire maker gives a 1.8542 mm maximum outer diameter. Each conduit has
2.4 mm inside diameter and 5.2 mm outside diameter. Radial wire clearance is
0.2729 mm; the printed wall is 1.4 mm. The conduit starts before the first
bend. Contact hoods cover the contact tails. Joint insulation and its fit at
the hood/conduit transition still need completion. This study does not accept
an exposed solder joint. Do not add sleeving through the bends without a
review of its larger diameter and bend radius.
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
