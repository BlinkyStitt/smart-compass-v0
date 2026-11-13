# 60 W USB-C wall power

Use a USB-C PD adapter and C-to-C cable that support 20 V at 3 A on the port
in use. The gasketed USB-C head hangs below the compass. It accepts the
20 V contract, then converts it to 5 V before the cable enters the case.
Use the existing charger, cell holder, and thermistor.

| Condition | Operation |
| --- | --- |
| Qualified USB-C, cell and sensor fitted, S1 RUN | The charger charges the cell. Press START to run the brighter rainbow while charging. |
| Qualified USB-C, cell and sensor removed, S1 RUN | Press START to run the same rainbow. The charger supplies the controls from USB. |
| USB-C absent or below 20 V at 3 A, cell fitted, S1 RUN | Press START for the battery brightness limit. |
| USB-C absent or below 20 V at 3 A, no cell | The display and charger stay off. |
| S1 OFF | The display feed and positive cell contact open. |

Hang the compass by its strap on a rated hook. Leave at least 35 mm behind
the rear face for the cable elbow. Support the wall cable so it does not
pull on the socket. Unplug USB and set S1 to OFF before cell service.

## Prepare the USB-C head

1. Have the assembler reflow the [USB-C PCB](wall-power/README.md).
   Program the STUSB4500 as described below. Fit the GCT USB4736-GF-A-KIT
   and its USBTJ-06 gasket on the short wall of a Hammond 1551WYBK.
2. Mount the USB PCB on insulating supports. Align the connector to the
   GCT panel drawing and compress the 0.90 mm gasket by 35–45%. Leave
   room to fully seat the USB plug. Fit the tethered cap.
3. Mount the Pololu D24V90F5 behind the PCB along the long axis of the
   head. Use the large power holes. Connect W1 and W2 to VIN and input
   ground with 22 AWG. Connect VOUT and output ground to W3 and W4 with
   18 AWG. Keep the paired leads short. Use an insulating mount that
   clears the solder joints and holds both boards clear of each other.
   Allow 8 mm between the boards and about 10 mm at the gland end for
   flat leads and the locknut. The head measures 100 × 50 × 24 mm.
4. Fit a Heyco M4332 straight M12 gland on the opposite end. Solder the
   red and black leads of Q4560-1 round 18 AWG cable to W5 and W6. Fit a
   Heyco M4450 elbow in the existing rear-cover hole. Clamp the jacket
   at both ends and leave at least 25 mm of slack inside the cover.
5. Fit a shrouded **two-position Mini-Fit Jr.** receptacle to the
   powered lead after threading the gland. Use cavity 1 for 5 V and
   cavity 2 for ground. Use 18 AWG contacts on both halves. Keep the
   head-to-selector lead at or below 400 mm. Measure the dressed route
   around the carrier before cutting. Include the 25 mm service fold.

[Receptacle](https://gct.co/connector/usb4736),
[Housing drawing](https://www.hammfg.com/files/parts/pdf/1551WYGY.pdf?v=1697661936),
[Regulator](https://www.pololu.com/product/2866),
[Cable specification](https://cdn.automationdirect.com/static/specs/18awgushctrlandsigcbl.pdf)

### Program the head once

With no regulator or pigtail connected, use the four probe pads and a
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
18 V at its input. The head supplies neither charging nor wall display
power from a lower profile. The 5 V output eFuse blocks reverse current
and disconnects the pigtail above its voltage window.
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
| W1, W2 | Head connector cavities 1 and 2. |
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
behavior. See [charger setup](wall-power.md) for the temperature sensor
and cell sleeve.
