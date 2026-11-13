# 60 W USB-C wall power

Use a USB-C PD adapter and C-to-C cable that support 20 V at 3 A on the port
in use. A USB-C PD power bank works if its port offers that mode. Plug the
cable into the downward-facing USB-C socket on the rear cover. The inlet
board, 5 V converter, charger and LED power selector are inside the case.
Use the existing cell holder and thermistor.

| Condition | Operation |
| --- | --- |
| Qualified USB-C, cell and sensor fitted, S1 RUN | The charger charges the cell. Press START to run the brighter rainbow while charging. |
| Qualified USB-C, cell and sensor removed, S1 RUN | Press START to run the same rainbow. The charger supplies the controls from USB. |
| USB-C absent or below 20 V at 3 A, cell fitted, S1 RUN | Press START for the battery brightness limit. |
| USB-C absent or below 20 V at 3 A, no cell | The display and charger stay off. |
| S1 OFF | The display feed and positive cell contact open. |

Hang the compass by its strap on a rated hook. Allow 35 mm behind the
rear face for the port, plug and cable. Keep the cable clear of the wall.
Support the wall cable to keep its weight off the socket. Unplug USB and
set S1 to OFF before cell service.

## Assemble the USB-C inlet and regulator

1. Have the assembler reflow the [USB-C PCB](wall-power/README.md). Program
   it as described below. Use the 1.20 ± 0.10 mm board and the
   USB4736-GF-A-KIT receptacle with its USBTJ-06 gasket.
2. Finish the port and gasket pocket to the GCT panel drawing. Check the
   9.10–9.14 × 3.32–3.36 mm opening, 0.60 ± 0.03 mm pocket depth, and
   35–45% gasket compression on the printed sample. Remove support and
   smooth the gasket land. Check plug seating before attaching any wires.
3. On the bench, solder 22 AWG pairs between W1/W2 and regulator VIN and
   ground. Solder 18 AWG pairs between regulator VOUT and ground and W3/W4.
   Keep the leads flat and leave enough slack to lift both boards out
   without pulling on the pads. Insulate the solder joints from the cover
   and secure the leads inside the bay.
4. Set the inlet into the lower opening from inside the rear cover. Slide
   the socket forward to seat its gasket. Fit two M2 × 4 mm screws and
   insulating washers in the blind pilots. Check that the panel takes the
   plug load and the PCB stays flat. Seat the Pololu D24V90F5 in the upper
   opening and use four short M2 screws with insulating washers. Check
   screw depth and underside lead clearance before tightening.
5. Terminate W5 and W6 with a shrouded two-position Mini-Fit Jr. Use 18 AWG
   contacts, with cavity 1 for 5 V and cavity 2 for ground. Leave at least
   25 mm of service slack and keep the full inlet-to-selector lead at or
   below 400 mm. Fit a tethered dust cap to the USB-C receptacle.

[GCT panel drawing](https://datasheet.octopart.com/USB4736-GF-A-GCT-datasheet-189261393.pdf),
[Regulator](https://www.pololu.com/product/2866)

### Program the inlet once

With no regulator or selector connected, use the four probe pads and a
3.3 V I²C programmer. Connect 3.3 V to TP1, SDA to TP2, SCL to TP3, and
ground to TP4. Leave USB unplugged. Use the included Arduino [provisioning
sketch](wall-power/provision/provision.ino) with the
[SparkFun STUSB4500 library](https://github.com/sparkfun/SparkFun_STUSB4500_Arduino_Library/tree/7f76188b7900d930aeb7908319d463b6446257c6).
Send uppercase W in the 115200 baud serial console to write. Power-cycle
the target and send V to verify. Disconnect the programmer before
plugging in USB.

The first sink profile stays at 5 V for negotiation. PDO2 matches only
20 V with at least 3 A advertised and requests 3 A. POWER_OK2 asserts
after the source accepts PDO2 and reports ready. U2 also requires about
18 V at its input. Charging and wall display power require this contract.
The 5 V output eFuse blocks reverse current and disconnects the 5 V feed
above its voltage window.
[STUSB4500 decision algorithm](https://www.st.com/resource/en/datasheet/stusb4500.pdf),
[TPS25947 eFuse and priority switching](https://www.ti.com/lit/ds/symlink/tps25947.pdf)

## Fit the plug-in harness

Mount the [LED power selector](wall-power/README.md) flat on the rear
cover in the 28 × 28 mm reservation centered at X −44, Y 47 mm. Use a thin
insulating adhesive mount. Keep the board, mount, trimmed leads and
flat wire exits within the 5.5 mm height reservation. Put the inline
connector bodies outside that reservation. Make the harness at the
bench and secure its service folds with removable ties.

| Selector lead | Connection |
| --- | --- |
| W1, W2 | Inlet connector cavities 1 and 2. |
| W3, W4 | Existing charger two-position Micro-Fit, 5 V and ground. |
| W5 | Sparkle Motion JP1.9, the 5 V lead removed from the carrier side of the J7 harness. |
| W6, W7 | J7.1 and J7.2, LED 5 V and return. Join the Sparkle clamp ground to J7.2 at the bench splice. |
| W8 | J6.1 through a Y splice in the Sparkle barrel harness. |
| W9 | Sparkle Motion GPIO18 through JP3.5. Use a right-angle socket or terminate the lead at the module before fitting its carrier socket. |

Keep J7 data and the four LED plugs in their documented positions.
Leave 25 mm of service slack at the selector and charger. Leave the
original 40 mm at the four LED plugs. Keep the original 2 A and 1 A
fuses and the Fibonacci 1000 µF capacitor. The selector supplies LED
current through J7.1 and J7.2. The existing barrel and switch supply
logic on the wall. The selector isolates the battery and wall feeds
and uses the wall feed when available.

## Load the display firmware

Install CircuitPython 10.3.1 for the full Sparkle Motion. Use an A-to-C
data cable through a hub on macOS. Open the CircuitPython editor's USB
workflow and upload the matching NeoPixel library to the board's
`/lib` directory. Upload `power_policy.py` and then `code.py` from
[firmware](wall-power/firmware/) to the root of the board. Export the LED
map locally with the command below. Upload the map to the same root
before resetting the board. [Adafruit installation guide](https://learn.adafruit.com/adafruit-sparkle-motion/install-circuitpython),
[USB file upload](https://learn.adafruit.com/adafruit-sparkle-motion/usage)

```sh
python3 designs/carrier/wall-power/firmware/export_layout.py \
  designs/stacked/exports/scene.json led-layout.json
```

This image runs the moving, full-saturation rainbow on the four outputs.
Set the channel order to match the installed LEDs if a ring uses a
different order. GPIO18 reads the selector's active-low status. A loose
or unplugged sense lead leaves the display in battery mode. The firmware
applies the 2% battery cap at startup. Wall operation allows about 13%
electrical drive and also checks the encoded current for each frame.
The 1,024-frame model peaks at 2.34 A on the wall and 0.75 A on
battery. The limits leave headroom for the existing J7 connector and
branch fuses.
This firmware is for the standalone display. The navigation and radio
firmware described in the design spec is a separate implementation.

## Verify the power design

The 60 W rating is the negotiated adapter capability. The wall display
limits the four LED feeds to 2.4 A combined. The charger still limits its
input to 2.46 A at the upper tolerance and sets a nominal 1.2 A cell
charge rate. With a 5.2 V upper 5 V rail and an 80% conversion allowance,
the simultaneous input budget is under 32 W. The charger can reduce
charge current when its own input sags or it reaches its thermal limit.

Check the board files with the KiCad commands in the
[board guide](wall-power/README.md). Run the firmware and power-budget
tests from the repository root.

```sh
python3 -m unittest discover -s designs/carrier/wall-power/firmware
```

Board checks cover connection, design-rule and schematic parity.
The current limits are estimates for the encoded rainbow. The assembled
unit establishes sustained temperature, cable drop and source-change
behavior. Check the regulator, rear pocket, wearer contact surface, charger
and cell during sustained display plus charging in the closed case.
See [charger setup](wall-power.md) for the temperature sensor and cell sleeve.
