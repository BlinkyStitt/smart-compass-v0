# Shared removable-cell compartment

The selected narrow prototype uses this shared mechanism. The wide branch of
the factory remains an inactive reference; it is not an installed release.
Use the [actual narrow fit record](../../designs/stacked/exports/installed-fit-check.json),
[full loom](../../designs/stacked/exports/loom-check.json),
[inventory](../../designs/stacked/exports/inventory.md) and
[illustrated service guide](../../designs/stacked/exports/service-guide.svg).
A component check alone does not establish full assembly or physical acceptance.

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
guarantees. The narrow cradle has four integral compression bosses and nominal 0.25 mm insulating shim washers. Retain the four removable clamp plates for contact installation and adjustment.
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

The compartment JSON owns the hinge, keeper and clamp geometry. For the active
Narrow assembly, use `designs/stacked/fasteners.json` for its 52 named titanium
cap screws; the service ZIP includes `04-REFERENCE/fasteners.json`. The four
contact-clamp screws use SSCF-M2-16-TI5 stock finished to 13 mm under the head.
The four case mounts use ZS755M3X10 screws at 10 mm, M3 washers and M3 nuts.
Keep the other selected hinge/keeper hardware and all washers and nuts. Gauge
the actual stock, finished lengths, threads and full engagement. The case-mount
clamp stack bears on a 2 mm rear interface without a floating flange. The hinge
pin has a head and retained nut larger than its bore. The narrow cradle has integral hinge shoulders. Place the two M3 thrust
washers under the pin head and retaining nut. The stack retains the nominal
0.2 mm axial play; gauge the actual assembly. The keeper uses a button-head screw
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
remain **unmeasured**. Only the selected narrow assembly enters the release
contract. Its full native build adds the complete installed loom, strain relief,
guarded controls, mass and balance ledgers, and illustrated service instructions.
The wide component model stays an inactive study.

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
three diameters. Joint soldering, fuse lacing, insulation and strain relief
remain physically unmeasured. The complete narrow loom record supplies the
downstream design; the component study alone does not supply that result.
Use the selected ZS755M3X10 case screws at their 10 mm finished length in
`designs/stacked/fasteners.json`. Keep the washers and nuts. The wire-only
tubes leave room for that complete stack.
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
before bolting down the cradle. Four side-wall slots carry two joint restraints.
The negative-X exit has a 3.5 mm diameter for the finished 3 mm sleeve and
0.25 mm radial clearance. Its housing retains a 2.35 mm wall target. These
are assembly dimensions, not supplied-fit or strength guarantees.
The two selected main-fuse ties and joint gauge are specified below. The generated narrow full-loom record owns downstream cuts, routes and restraints.
Supplied fit, insulation, restraint force and fault withstand remain unmeasured.

The rear opening is 106 mm long. The end walls stay 2 mm thick. The long side
walls are 1.35 mm thick, with the existing 2 mm lower lip and 1.5 mm ceiling.
Each actual rear panel must support the full case-mount bearing ring at the
specified 2 mm datum. The checker rejects a thin rear skin below that datum.
These geometry checks do not establish printed strength.

For initial assembly, read the generated full wire cut list. Use the specified
positive-contact blank. Use the fullW044 blank for the negative contact-to-boost
lead; the conduit datum is not a tail cut or splice. Thread each unterminated
lead through its tube before closing the carriers. Pull the cup end into the
empty bay and solder it outside the printed part. Let it cool. Draw the wire
through while you seat the cup and collar. Fit and gauge clamps and shims.
Solder the positive fuse end last. Route the continuous negative wire to
BOOST.X2.1 and clamp its untinned stripped end. Keep insulation outside each
cup and clamp. The printed collar supplies secondary insulation. Joint quality,
strain relief, physical assembly and fault withstand remain unmeasured.

## Main-fuse joint restraints

Use the selected Littelfuse 0251004.NRT1L 4 A axial fuse. The native
BatteryMainFuse shape reserves the complete insulated fuse and lap-joint
assembly. Its overall gauge is 20 × 5 × 5 mm. The central body gauge is
9 × 5 × 5 mm. Each end has a 5.5 × 3.5 × 3.5 mm joint gauge. These are
finished assembly requirements. They are not supplied size guarantees or
material volumes for the mass ledger. Count one fuse. The retained source is
Littelfuse 251, GK 18-Aug-2026, pages 1–3. Keep the nominal lead/body lengths
separate from the 2.80 mm maximum body diameter.
See the [current fuse source and joint process](branch-fuses.md).

In the selected narrow assembly, pin1 is the right end atX51mm. It connects to the fixed
positive contact lead. Pin 2 is the left end at X31 mm and goes to FUSED_CELL
and S1.1. Both joint axes are Y−69.5 mm/Z8.3814132935 mm. These are assembly
coordinates. The fixed contact lead includes its existing 3.5 mm stripped-end
allowance. Keep each lap joint inside its end region. Use one 18 AWG wire at
each fuse end. Keep insulation beyond the joint. Use the selected TE
RNF-100-1/8 sleeves. Recover and inspect them outside PETG. Gauge the central
body and both completed joints against their separate limits. In particular,
3.5 mm is a finished joint target, not a vendor guarantee for a soldered lap
joint. Joint quality, actual fit and insulation remain unmeasured.

The downstream housing opening has a 3.5 mm diameter. It clears the 3 mm
recovered-sleeve gauge by 0.25 mm radially and retains a 2.35 mm housing wall.
The contact conduits keep their specified bore and wall. These dimensions are
fabrication targets. Check the finished sleeve and printed opening before assembly.

Use two Alpha Wire LC134 BK088 square-knot spot ties, at X33 and X49 mm.
Cut 70 mm blanks. Each tie captures its sleeved lead and the negative-Y
housing wall. Pass its two crossing bands through the two slots in that wall.
Keep the loop below the roof. Put the knot and trimmed tails on the negative-Y
side, inside the modeled 4 × 2.2 × 2 mm space. Centre the left knot at
X33 mm and the right knot at X50 mm. The right knot sits 1 mm along X from
its band centre to clear the Narrow rear fastener post. Keep both knots
clear of the cell-bay wall. Seat each tie without crushing the joint. Do not put a tie
on the epoxy fuse body.

The stock maximum width/thickness is 1.6764/0.4318 mm. The native loop reserves
1.7 mm width and 0.5 mm thickness. Each 0.8 mm high wall slot gives 0.15 mm
clearance above and below its band. The slots extend from −2.4 to −1.6 mm
and from +1.6 to +2.4 mm relative to the fuse axis. The housing keeps 1.7 mm
of side wall below and above those slots. Its roof remains 1.35 mm thick.
The rear-bearing brace remains unchanged. These are geometry targets, not
knot shape, force, retention or printed-strength ratings.

Use the [Alpha specification](https://www.alphawire.com/products/accessories/fit-wire-management/lacing-tape/lc134),
printed 13-May-2024, and its [square-knot instructions](https://www.alphawire.com/-/media/project/alphawire/alphawire/files/other/lacing-cord-installation-instructions.pdf?rev=4c0c10ce440d4bdfbef409fef7b4e7d7).
Its 25 lb minimum tape breaking strength does not rate an installed knot or
holder. Gauge every completed knot and trimmed-tail space. The component
check requires both ties and rejects a tie that intrudes into the joint or
housing. Physical fit, retention, temperature, insulation and fault withstand
remain unmeasured.

## Narrow fitted service

Support the pendant and keep the free necklace span above it, clear of the bay
and controls. Put S1 fully OFF and remove USB, SWD and other live interfaces.
Open the captive door. Hold the cell, release its independent keeper and pull
the ribbon. Inspect the wrapper, end insulator, guides and contacts. Insert one
compatible protected XTAR21700 6000mAh button-top to the permanent+/-marks.
Close the keeper and door; inspect the catch. Select ON and press START.

No reset dwell is qualified. A rapid replacement may retain state. Light does
not establish GPS acquisition, radio synchronization or navigation readiness.
After heat, damage or repeated darkness, stop and service; do not bypass a fuse
or repeatedly cycle a fault. Charge removed cells off-body. Remove the cell for
USB5V service and keep S1 OFF.

Ordinary cell service leaves the full loom fitted. Rear/radio maintenance requires
releasing every bridging wire at both ends and removing loose wires, insulation
and boots. Fixed PCB-backed splice carriers stay on the original board. Empty
the bay and put the captive door at its open stop before radio withdrawal.
The generated antenna-service record states all removal preconditions.

The lower carrier has two source-defined cable passages below the LED band.
Do not trap a lead when fitting the rear. Fit and inspect the removable cable
seals. The existing seal allowance remains in worn mass; no dust/water rating
is established. Inspect insulation, supplied fit and all physical outcomes
under [the qualification procedure](qualification-plan.md).

## Narrow panel pockets

The narrow cradle retains its 1.35 mm side walls and full contact supports,
mounting flanges, hinge and latch. Four pockets in the flat roof retain a
continuous 1 mm insulating skin. The perimeter and 3 mm cross ribs stay full depth.
The permanent polarity marks stay outside the pockets. Door pockets retain a
1.35mm continuous skin and full hinge/latch ends. The archived wide geometry
keeps its original panels. These dimensions reduce calculated solid volume.
They do not prove impact strength, print bonding, cell retention or fatigue.
