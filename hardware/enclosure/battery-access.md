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
