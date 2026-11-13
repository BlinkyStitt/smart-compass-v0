# Wall USB-C power and in-place charging

Rev A uses a [routed USB-C pigtail and a routed internal charger](wall-power/README.md).
The external USB-C socket hangs below the case. Plug in a USB-C source
that advertises **5 V at 3 A**. A higher-wattage USB-C adapter works if it
offers that 5 V mode. The [Raspberry Pi 15 W USB-C supply](https://www.raspberrypi.com/products/type-c-power-supply/)
is a bench candidate. Verify its 3 A advertisement and loaded voltage.

```text
USB-C 5 V ── attach and 3 A gate ── sealed lead ── BQ25616 VBUS
Fused, switched protected 21700 ───────────────── BQ25616 BAT
Cell-mounted NTC in removable sleeve ─────────── BQ25616 TS
BQ25616 SYS ── Pololu 2808 ── PowerBoost 1000 Basic ── S1 ── Sparkle barrel
```

| Condition | Designed operation |
| --- | --- |
| USB-C valid, cell fitted, S1 RUN | USB supplies SYS. The charger uses the remaining input budget for the cell. Press START to run the display. |
| USB-C valid, cell removed, S1 RUN | USB supplies SYS. Press START to run the display. |
| USB-C absent, cell fitted, S1 RUN | The cell supplies SYS. Press START to run the display. |
| USB-C advertises default current or 1.5 A | The USB load gate stays off. The cell can still supply SYS. |
| S1 OFF | S1 opens the positive cell contact and the display feed. Use RUN for charging, and unplug USB before opening the hatch. |

## Assemble the two subassemblies

Use preassembled boards and precrimped harnesses. Make the solder joints
with the boards on the bench. The boards connect to the enclosure with two keyed plugs. The cell
sleeve has a separate two-pin sensor plug inside the hatch.

| Connection | Pins in numbered cavity order |
| --- | --- |
| USB head to charger, two-pin Molex Micro-Fit | 1 switched 5 V (red), 2 ground (black) |
| Charger to carrier J1, JST VHR-4N | 1 BAT to switched cell positive, 2 ground, 3 SYS, 4 TS to sleeve NTC |
| Carrier J2 to cell holder, existing JST VHR-3N | 1 fused and switched cell positive, 2 ground, 3 removable sleeve NTC |
| Removable sensor sleeve, keyed JST RCY | 1 NTC sense, 2 ground |

Use 22 AWG on the short board leads and two-conductor jacketed pigtail.
Use a shrouded female terminal housing on the powered USB-head lead.
Feed its precrimped ends through the rear gland before inserting the
contacts into the housing. Verify continuity by molded cavity numbers.
Leave at least 25 mm of service slack at the charger and carrier plugs
so you can lift and support the rear cover before unplugging them.
Secure the harness to the rear cover outside the board reservation.

The 24 × 26 mm charger PCB fits the 24 × 28 mm CAD reservation at
X −14 to 10, Y −95 to −67, Z 3.5 to 9.5 mm. Center it along the 28 mm
axis. Start with a thin insulating adhesive mounting pad and keep the
underside leads trimmed and insulated. The M2 holes are for fixture use
or a later mount. Keep wires flat over the pads. Allow 1.6 mm for the PCB,
2.0 mm for the tallest component, and at most 2.4 mm total for the
insulating mount, underside solder, and wire dressing. Place both plug
bodies outside the 6 mm height reservation. Check routing and access
with the actual rear cover before fixing the harness.

Fit the thin 103JT-025 thermistor to a removable insulating cell sleeve.
Hold the sensing tip against the intact cell wrapper, away from the
centre pull ribbon. Use a 10 mm wide band centered at X −24 mm in the
CAD frame, toward the negative end. Use thin insulating tape and limit
the finished sensor buildup to 0.7 mm above the wrapper. Keep the
sleeve open at both ends and keep the positive button, end insulator,
and contact path clear of adhesive and wire joints.
Use a keyed two-pin JST RCY connector in the holder to connect the
sleeve's thermistor to TS and ground. Park the mated plug under the
hatch with its long axis parallel to the cell, near X −38, Y −40 mm.
Keep it outside the seating and pull-ribbon paths.
Allow 25 mm of slack and use 26 AWG leads with the specified RCY
crimp insulation diameter. Unplug the sensor as part of cell removal and
remove it with the sleeve. This opens TS in batteryless use. The
charger then suspends charging while SYS stays available from USB.
[Semitec thin-film thermistor](https://www.semitec-global.com/products/thermistor_jt/),
[TI note on batteryless SYS ripple](https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/196/BQ2561x_5F00_-FAQ.pdf)

Preserve the protection circuit, contact-adjacent 4 A fuse and S1
disconnect. Use a dummy cell at the maximum 23.5 mm sleeved diameter
for the first fit. FreeCAD clears the sleeve and the parked plug.
Gauge spring travel, sleeve and plug clearance,
sensor contact, and cell removal before connecting wall power.

### External USB-C head

Use the gasketed Hammond 1551WHBK as the first housing. Fit the GCT
USB4736-GF-A-KIT receptacle and USBTJ-06 gasket. Machine or jig-cut the
socket opening and gasket recess to the GCT drawing on a flat wall of
the head. Support the PCB at its two M2 holes with an insulating bracket
or bonded standoffs. Dry-fit the board and adjust the supports before
bonding so the panel and receptacle shell take plug forces and compress
the 0.90 mm gasket by 35–45%. Inspect the fit with a C-to-C plug before
closing the housing. Fit the head gland on the opposite end and clamp
the round cable jacket. Fit a tethered cap to the socket.
[Housing](https://www.hammfg.com/part/1551WHBK),
[USB-C receptacle and panel drawing](https://gct.co/connector/usb4736)

Use the [sealed rear-cover exit](dust-sealing.md) for the same jacket.
Hang the compass by its strap on a rated hook and provide at least
35 mm behind the rear face for the elbow and cable. Leave enough slack
below the compass that the wall cable does not pull on the socket.

## Electrical settings

- The STUSB4500L uses its factory settings. It monitors VBUS and
  drives the attach P-channel MOSFET. The active-low RP_3A flag
  drives a PNP that enables the TPS259531 eFuse. The eFuse adds a
  5.7 V nominal overvoltage clamp threshold, controlled rise, current limiting,
  and thermal shutdown. R8 sets its nominal limit to approximately
  2.8 A. The BQ25616 controls steady input current below that limit.
  [ST sink reference](https://www.st.com/resource/en/schematic_pack/eval-scs002v1_schematic.pdf),
  [TI eFuse data sheet](https://www.ti.com/lit/ds/symlink/tps2595.pdf)
- The BQ25616 supplies SYS from USB even with the battery removed.
  OTG is off. The charger leaves D+/D− open for the ILIM setting.
  The 205 Ω resistor sets 2.33 A nominal and 2.46 A upper input
  limit from the specified resistor and IC tolerances. The 562 Ω
  resistor sets about 1.2 A charge current. VSET floats for 4.2 V.
  The 5.30 kΩ/31.1 kΩ TS network and 103JT-025 give the nominal
  0–45 °C charge window. An open or shorted thermistor suspends
  charging. For batteryless operation, remove the cell and its sensor
  together so TS opens.
  [TI charger data sheet](https://www.ti.com/lit/ds/symlink/bq25616.pdf),
  [XTAR cell specifications](https://www.xtar.cc/wp-content/uploads/2024/06/XTAR-Product-Catalog.pdf)
- The existing 5.2 V PowerBoost supplies the LEDs. During wall
  operation the carrier's voltage sense measures switched SYS.
  It does not report cell state of charge in that mode.

The 2% full-rainbow pattern models 5.7 W at the load. With assumed
85% boost and 90% charger conversion efficiency, it uses about 7.5 W
at USB before charging. A nominal 5 V source at the 2.33 A input
limit leaves about 4.2 W of input power before cable and switch losses.
The charger reduces charge current as the display load rises.
The stock LED supply cannot deliver the modeled 74 W full electrical
rainbow. Use the 2% setting for the first display test.

## First assembled pair

Use a current-limited supply and battery simulator for first power.
The PCBs have labelled lead pads and probe points for the measurements
below. Keep the real cell out until the first four rows pass.

| Check | Measure |
| --- | --- |
| USB source and pigtail | Use both plug orientations and default, 1.5 A and 3 A advertisements. Test a change from 3 A to a lower advertisement. Scope RAW, RP3_N and switched output. Check input current, inrush and connector drop. |
| No cell and source removal | Verify SYS before START. Run the 2% pattern from USB with BAT and the sleeve thermistor disconnected. Scope SYS ripple. Exercise PWM and radio load steps. Insert and remove USB with the simulator connected and check for resets and reverse current into the unplugged socket. |
| Charger and load sharing | Sweep simulated battery voltage. Verify charge regulation, taper, termination and charge-current reduction with load. Check startup and operation near the input voltage limit. |
| Thermistor and disconnect | Emulate 0 °C and 45 °C, open and short the NTC, and verify that charging stops. Measure S1 isolation with USB present. |
| Actual cell and enclosure | Confirm the delivered XTAR cell model and charge limits. Measure current and temperatures at the cell, charger, converter and cable in the assembled wall position. Verify the head and rear gland seals, cable support and service slack. |

KiCad DRC and schematic-to-board net checks passed for both designs.
The wall display, charge and sealing checks require assembled hardware.
