# Internal 915 MHz antenna installation

Each `parameters.json` owns one installation. Both use a **78 mm total** insulated
copper wire, including its 2 mm stripped end soldered directly into ANT. No extra
feed wire, coil or external antenna. Nominal outside diameter is 1 mm; conductor
must fit the 1 mm plated hole. Restraints use two small nonmetal ties through the
printed slots; tie width at most 2.5 mm, thickness at most 1 mm. Their retention,
wire flexibility and supplied board revision remain assembly assumptions.

## Datum and assumptions

[Adafruit's assembly guide](https://learn.adafruit.com/adafruit-rfm69hcw-and-rfm96-rfm95-rfm98-lora-packet-padio-breakouts/assembly)
specifies 78 mm for 915 MHz and direct ANT soldering. The nominal pad comes from
[Adafruit's Eagle board, revision 3ad6bed](https://github.com/adafruit/Adafruit-RFM-LoRa-Radio-Breakout-PCB/blob/3ad6bed6e1b407afa7119ae548b5c2f1b107c6b1/Adafruit%20RFM%2BLoRa%20Breakout.brd):
JP2 pad 1 is (21.590,24.511), outline bounds X0.254..25.654, Y0..29.210 mm.
Subtract outline centre (12.954,14.605) to get (8.636,9.906).
The source connects JP2 to the RF feed net N$1. Centre the real board in the
25.4 x 32 mm padded envelope without scaling it. Original: turn board 180°,
ANT toward -Y; compact: 0°, ANT toward +Y. Z starts at the PCB underside;
board thickness is the provisional 1.6 mm used elsewhere in the model.

The local component-free cylinder of radius 3.2 mm around JP2 is a **fit
assumption**, not a claim that all copper is absent. The radio's pad, feed trace
and PCB are permitted within that region only. The component placeholder is
relieved there; the PCB retains a 1 mm drill. Other objects never inherit that
exception. Check the supplied board before assembling; don't bend around a
surprise connector or shield and call it the same placement.

The full insulated envelope adds ±0.2 mm placement uncertainty. Beyond the local
feed region and the two 6 mm saddle contact windows, the assembled wire requires
at least 2 mm to
conductive components, fasteners, coatings and reserved wiring, and 0.5 mm to
uncoated plastic. These are selected **mechanical allowances**, not validated RF
keepout distances. Native checks use distances, including endpoints and the
curved bend, rather than a thin-wire overlap-volume threshold. Each view reports
the nearest modeled surface gaps after insulation and placement uncertainty.

A board-normal feed riser and a 3 mm radius bend lead to a long uncoiled run
parallel to the hanging Y axis. Original tip points down, compact tip up; their
polarization axes match. The original run is at Z17, the compact at Z24, away
from the body-facing rear. Limited bay depth prevents a fully straight wire
normal to the PCB. Compact placement is particularly close to its plastic shell
and board support. Neither layout claims to meet another vendor's RF spacing.
[Digi](https://www.digi.com/support/knowledge-base/integrated-wire-antenna)
recommends extending away from the board and maximizing separation from metal;
[Infineon](https://community.infineon.com/t5/Knowledge-Base-Articles/Layout-recommendations-for-Antenna/ta-p/248092)
discusses enclosure/ground interactions; [TI's antenna guide](https://www.ti.com/lit/an/swra161b/swra161b.pdf)
discusses orientation and polarization. These inform the compromise, not a
universal clearance rule. Keep the nearby plastic uncoated; conductive paint,
foil, metal ties, body proximity and altered bends can change RF performance.

## Assembly and service

Use the separate diagram in each enclosure README. Form the riser and bend
before soldering; measure 78 mm along the wire centreline including the stripped
end. Seat the straight run in the two saddles and fasten it gently with nonmetal
ties. The saddle walls sit below the wire crown so the ties bear on insulation;
verify each tie grips the wire without crushing it. The first saddle takes
handling load before it reaches ANT. Saddles and
the fixed board orientation restore the route after service; do not tension the
wire to make a misplaced board fit. Do not use ANT as a lifting handle.

Power off and disconnect the battery. Support the rear before releasing screws,
then disconnect any harness bridging the moving assembly. Original: withdraw
rear, radio and wire together axially toward -Z. Compact: remove the rear and
its removable seal first, disconnect radio wiring, release the provisional
radio shelf fastening, then withdraw RadioShelf with radio and wire along -Z.
Keep the wire tied during assembly withdrawal. For radio replacement, release
both ties before moving the board; support the wire beside the joint. Do not
pull against ANT. Battery service need not release the antenna restraints.

Before closure: compare the wire with the diagram; verify both saddles seated,
required gaps intact, joint unloaded, harness inside its reserved volume, screws
and removable seals clear. Reverse the checked axial motion without tilting the
carrier. If closure catches, reopen and reseat; **never force it**. Compare with
the diagram before cutting, bending or otherwise altering the antenna.

The harness envelope is a routing reservation, not an as-built harness model.
Keep LED/power leads in the shown central reservation, and route remaining
board leads away from the wire. Native checks cover actual screws, component
envelopes and seals plus a complete peripheral seal reservation. Withdrawal
checks maintain at least 0.5 mm mechanical clearance around the full wire
envelope throughout unpowered withdrawal, and conservatively sweep the radio and
restraint bounds; the original also retains its rear/frame checks. Released
seals travel with the rear or are removed first; they are never stretched over
an attached wire. Supplied connectors, IMU revision and other unmodeled details
still need fit inspection.

## Replacement, retrofit and evidence

Replace wire with the same insulated diameter, total cut length and formed path;
replace ties after cutting them. Original retrofit replaces the complete
RearPlate with its integral saddles. Compact retrofit replaces RadioShelf with
its connected saddle spine; shelf fastening is still provisional. Transfer the
radio in the documented orientation; preserve sensors, optics, seals and rear
access. Do not glue a wire across an opening or drill an external feedthrough.

Build original before compact because compact consumes original scene metadata.
Regenerate all outputs with their owning commands, including the diagrams, then
check both working and staged manifests. Rollback restores the prior **matching
source/export/manifest set**, then reruns both freshness checks.

CAD compliance is separate from unmeasured RF performance and physical
acceptance. There is no 6 km guarantee. Installed tuning and trials are outside
this change. The broader `design-v2.md` evidence requirements still apply:
record payload, modulation/profile, antenna, topology, delivery ratio and sample
age for direct and relayed operation, walking/body obstruction and combined
LED/radio/GPS loads. Use the same profile when comparing placements and check
heading during radio transmission and LED load changes. Display work must not
stop STM32 location broadcasts. Compact remains a CAD concept.
