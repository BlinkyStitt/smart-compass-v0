# Wall USB-C power and in-place charging

The Rev A carrier uses a four-wire plug for a small internal charger board.
The USB-C socket hangs below the case on a captive pigtail. Use a 5 V
source that advertises 3 A over USB-C. The [Raspberry Pi 15 W USB-C
supply](https://www.raspberrypi.com/products/type-c-power-supply/) is a
5.1 V, 3 A bench candidate. Confirm the actual CC advertisement and loaded
voltage at the receptacle. This circuit uses Type-C current advertisement and
keeps VBUS at 5 V.

```text
USB-C 5 V ── STUSB4500L attach switch ── 3 A detect gate ── sealed cable ── BQ25616 VBUS
                                                            │
Fused, switched protected 21700 ─────────────────────── BQ25616 BAT
Holder-mounted NTC ──────────────────────────────────── BQ25616 TS
                                                            │
BQ25616 SYS ── Pololu 2808 ── PowerBoost 1000 Basic ── S1 ── Sparkle barrel
```

| Condition | Intended operation |
| --- | --- |
| USB-C valid, cell installed, S1 RUN | USB supplies SYS. The charger uses the remaining input budget to charge the cell. Press START to run the display. |
| USB-C valid, no cell, S1 RUN | USB supplies SYS. Press START to run the display. |
| USB-C absent, cell installed, S1 RUN | The cell feeds SYS through the charger BATFET. Press START to run the display. |
| USB-C advertises default or 1.5 A | USB load gate stays off. The cell can still supply SYS. |
| S1 OFF | The cell positive contact and display feed are open. Charging needs S1 in RUN. |

The charger supplies SYS from USB as soon as input is valid and reduces
charge current before reaching the input limit. If the load exceeds the input
budget, the charger can draw from the cell. Use the 2% rainbow load for
initial validation, including batteryless start. The cell protection, 4 A
fuse and physical switch stay in the battery harness. OTG is disabled. USB
source, battery and display share a ground. The charger provides the reverse
blocking between its input and the cell/SYS path.

## USB input and charger circuit

Place the receptacle, CC and ESD network, attach-controlled switch and
3 A gate in the pigtail head. Use the GCT USB4736-GF-A charging receptacle
with its USBTJ-06 gasket and a tethered cap. Take only switched 5 V and
ground through the rear cover. Keep the CC lines at the receptacle.
The head is the device's inlet. Plug a standard C-to-C cable into it.
Use a sealed cable exit at the head and a keyed 3 A service connector at
the charger. [GCT receptacle and gasket](https://gct.co/connector/usb4736)

Take the protected `VSNK` output and the open-drain `RP_3A` flag from the
ST reference circuit. Add a second series switch so the charger starts
only on the 3 A advertisement.
Copy the layout and attach behavior from the [ST reference
schematic](https://www.st.com/resource/en/schematic_pack/eval-scs002v1_schematic.pdf)
and [STUSB4500L data sheet](https://www.st.com/resource/en/datasheet/stusb4500l.pdf).

- Use a TPS22965N with VIN and VBIAS at VSNK, both VOUT pins feeding charger
  VBUS, and GND and the pad to ground. Use 1 µF input bypass at the switch
  and 1 nF on CT as the first inrush setting. Verify the total capacitance on
  the receptacle side and the turn-on waveform with the actual pigtail.
  The ST attach switch must drop VSNK on disconnect or an invalid voltage.
- Use a PNP MMBT3906 from VSNK to the active-high ON pin. Connect the emitter
  to VSNK, collector to ON, and base through 47 kΩ to RP_3A. Pull base to
  emitter with 100 kΩ. Pull ON to ground with 100 kΩ. A low RP_3A enables
  the switch. With RP_3A open or VSNK absent, ON stays low. Verify that a
  source changing its advertisement drops the load within the Type-C
  timing requirement. [Load switch data sheet](https://www.ti.com/lit/ds/symlink/tps22965.pdf)
- Use TI BQ25616RTWR with its 0–45 °C hot/cold reference network. Use a
  103AT-2 thermistor in thermal contact with the cell sleeve. Attach the
  sensor to the holder with light spring pressure and an insulated face.
  Keep it clear of the contact travel and cell wrapper. Use 5.30 kΩ from
  REGN to TS and 31.1 kΩ from TS to ground, in parallel with the NTC.
  Verify cold, hot, unplugged and shorted sensor conditions.
- Follow the TI application drawing and switching layout. Connect VAC to
  VBUS, leave ACDRV open in this 5 V configuration, and leave the two D
  pins open for the ILIM setting. Ground CE and OTG. Leave VSET open for
  the 4.2 V setting. Connect 191 Ω 1% at ILIM and 562 Ω 1% at ICHG.
  The input limit is 2.50 A nominal and about 2.65 A at the upper
  resistor and IC tolerance combination. The charge setting is about
  1.20 A. Verify actual regulation and termination with the selected
  XTAR cell.
- Use a 1 µH shielded inductor with the saturation and loss characteristics
  of the TI reference. Keep the SW loop tight and on the top layer. Use
  the reference 47 nF bootstrap, 4.7 µF REGN bypass, 10 µF PMID bypass,
  1 µF VBUS bypass, and the BAT and SYS capacitors at the chip. Select
  capacitors by effective capacitance at bias. Use the reference ground
  and thermal via layout. Expose VBUS, SYS, BAT, TS, PG and STAT for
  the first board measurements. [Charger data sheet](https://www.ti.com/lit/ds/symlink/bq25616.pdf)

The carrier regulates the display with the stock 5.2 V PowerBoost. It uses
the stock LBO header to trigger the Pololu OFF input through a PNP inverter.
This keeps the module's factory low-battery LED and uses no small resistor
pad tap. The BlackPill PA4 divider reads the switched boost input and is
isolated from PA4 by a TS5A3160 switch when the 3.3 V rail is inactive.
The switch takes power from the boost input through the 100 Ω supply filter.
The auxiliary 3.3 V rail enables it. [Switch data sheet](https://www.ti.com/lit/ds/symlink/ts5a3160.pdf)

When USB is active, that voltage represents SYS through the latch. It cannot be
used as a battery state-of-charge reading in wall mode.

## Bench first

Use [ST EVAL-SCS002V1](https://www.st.com/en/evaluation-tools/eval-scs002v1.html)
for USB-C input and [TI BQ25616EVM](https://www.ti.com/tool/BQ25616EVM) for
the charger. TP13 and TP6 on the ST board give VSNK and RP_3A. Use a
bench fixture for the series switch, or use a current-limited bench supply
at the charger VBUS terminal to test the charger separately. TI provides a
[TPS22965 evaluation module](https://www.ti.com/tool/TPS22965EVM-023) with an
external ON input for the gate test. Set the TI charger EVM per its
[user guide](https://www.ti.com/lit/ug/sluuc73a/sluuc73a.pdf). Remove the
JP6 and JP9 shunts so the D pins are open. Keep the ILIM, ICHG, REGN and
charge-enable shunts in place. Keep JP20 installed. Remove JP16 and JP18
when installing the external thermistor at the TS node in parallel with
the reference lower resistor. Set and measure the limits with a battery
simulator and an electronic load before connecting the cell.

| Check | Evidence to collect |
| --- | --- |
| USB-C power | Use both connector orientations. Test default, 1.5 A, 3 A and a source that reduces its advertised current. Measure VBUS, gate state, inrush and steady input. |
| No battery | Start from USB with the cell absent. Verify SYS before pressing START. Check repeated starts and PWM/radio load steps for resets or input collapse. |
| Charge and display | Sweep cell voltage with the emulator. Measure USB, SYS and battery current with the 2% rainbow. Confirm input limiting reduces charge as load rises. Verify net charge current, taper and termination with the selected cell. |
| Source removal and low battery | Remove USB during display. Measure whether the display resets during handoff. Verify the boost LBO threshold and latch OFF. Check reverse voltage and leakage at the unplugged USB socket. |
| Temperature and service | Open and short the thermistor and test the hot/cold thresholds. Check the assembled wall orientation and worst-case charger, cell, converter, cable and case temperatures. Verify S1 and the fuse isolate the cell during service. |

## Mounting and load limit

Use the existing strap on a rated wall hook for the first fit. Provide at
least 35 mm between the rear face and the wall for the cordgrip and cable.
Keep the charging cable below the case with enough slack to keep its weight
and plug forces off the connector. The internal charger has a 28 × 24 × 6 mm
reservation at X −14 to 10, Y −95 to −67, Z 3.5 to 9.5 mm from the rear datum.
See the [sealed pigtail and enclosure plan](dust-sealing.md) for the rear
cover, cable gland and complete enclosure checks.

The 2% rainbow mode draws about 5.7 W in the existing model. At 85% boost
and 90% charger conversion efficiency, that is about 7.5 W at USB before
charging. A 5 V, 2.50 A input target leaves about 5 W at USB under nominal
conditions. Expect less charge current at low input voltage, high temperature
or higher display load. The approximate 74 W full electrical rainbow load
exceeds this supply, the PowerBoost and the stock LED distribution. A 20 V
adapter profile would require a higher-current regulated LED supply and a
requalified distribution and thermal design. The first board keeps the
bench target at the current display setting.
