# Removable-cell module prototype

This is the active electrical design candidate for SKI-1230. It is **incomplete**.
Run `python3 hardware/enclosure/electrical.py check` for the current design errors.
The same command reports every required physical test as **unmeasured**. It does
not certify an assembled pendant, temperature, fault withstand or safe wearing.

The machine-readable owner is [electrical-design.json](electrical-design.json).
The previous [electrical review](electrical-review.md) and its calculations remain
rejected custom-circuit evidence. Their source records and recovery history remain
intact. They do not describe this module circuit.

## Acceptance boundary

Bryan requested an assembled-module prototype and a safer cell. On 2026-11-04,
he identified the excessive electrical proof requirement and authorized further
issue/PR work after the proposed correction: check a concrete prototype design,
retain real design errors, and separate physical qualification. This document
records that correction without editing the original approved specification.

Digital review checks the selected parts, explicit circuit connections, physical
OFF topology, low-battery latch interface, supply ranges, connector policy and
source revision. Missing design inputs fail. Passing these checks means only that
the reviewed design records agree. A source check or a synthetic test is not
assembly evidence. The checker does not have a flag that marks physical tests
passed. A future physical acceptance review needs actual revision, conditions,
measurements and results.

The previous thermal study tried to prove instantaneous hot/cold limits for all
components, optical reabsorption, initial temperatures and wearing conditions.
It remains historical research. The prototype requires a loss estimate and an
enclosure test procedure; measured thermal acceptance belongs to the built unit.
The new checker also replaces the five unconditional failure entries in the old
candidate report with checks of the active circuit. The old report remains
available to its regression tests and still rejects that circuit.

## Circuit

```text
one protected XTAR 21700 6000 mAh button-top
  + contact -- F1 4 A -- S1 pole A -- Pololu 2808 VIN
  - contact ----------------------------------------------- GND
                             Pololu VOUT -- PowerBoost BAT
                             Pololu GND ------------------- GND

PowerBoost output -- S1 pole B -- LOAD_5V -- Sparkle barrel PWR pad
                              |             barrel GND ---- GND
                              +-- R_LOAD 1 kohm -- GND
PowerBoost output -------------- R_BOOST 1 kohm -- GND

Sparkle JP1 positive --> F_FIB 2 A --> Fibonacci
                                 +-- C_OUT 1000 uF -- GND
                                 +-- R_OUT 1 kohm ---- GND
Sparkle JP1 positive --> three individual 1 A fuses --> three ring groups
Sparkle JP3.2 3.3 V --> 0.5 A fuse --> BlackPill + GPS + IMU + RFM95W
all returns ------------------------------------------------ GND

PowerBoost T1 collector (R20.2 pad) --> Pololu OFF
                                    +-- 100 kohm --> GND
Pololu A --> on-only START button --> GND
Pololu ON / CTRL / B: no external connection
```

The JSON lists exact terminal labels, separate branch fuses and every selected
supply/return. Do not connect 5 V LED terminals to the peripheral 3.3 V rail.
Do not use the GPS FeatherWing as a 5 V load. The existing BlackPill PA4 sense
divider connects to switched/protected B, not directly to the cell.

### Selected IMU revision and header pads

Use the **classic blue Adafruit LSM9DS1 Rev A**, PID3387. Its retained
[manufacturer sources](sources/lsm9ds1-classic/README.md) come from upstream
`9f6db79a66ae599aa410a2a14b161e26216e8bd4`. The source index retains the
original URLs, revisions and hashes. The checker verifies both original Eagle
files and derives the component-side pad coordinates from their header placements.

| Assembly terminal | Rev A header pad | Use |
| --- | --- | --- |
| VIN | JP4.9 | Fused auxiliary3.3V supply |
| GND | JP4.7 | Common return |
| SCL | JP4.6 | SPI clock |
| SDA | JP4.5 | SPI MOSI |
| SDOAG | JP4.2 | SPI MISO, accelerometer/gyro |
| SDOM | JP4.1 | SPI MISO, magnetometer |
| CSAG | JP4.4 | Accelerometer/gyro select |
| CSM | JP4.3 | Magnetometer select |
| INT1 | JP2.3 | Accelerometer/gyro ready |
| DRDY | JP2.4 | Magnetometer ready |

Do not substitute JP4.8, the regulator output, for VIN. The source names
`SCL_5V`, `SDA_5V` and `CS_*_5V` identify the board's external logic nets;
this assembly supplies VIN with3.3V. They do not direct the builder to apply5V.
Leave the unused header pads insulated and unconnected.

Rev C has a25.4x17.78mm nominal outline and puts DRDY_M at **JP2.5**.
Rev A has a33.02x20.32mm nominal outline and puts it at **JP2.4**. Thus the
two source layouts cannot share a fitted wire map. Retain the larger40x28x12mm
loaded reservation. Published nominal geometry and1mm source drills do not
prove supplied-board tolerances or completed solder-joint fit. Installed wire
routes, cut lengths and strain relief remain required work.

### GPS and radio source pads

The GPS uses the pinned Adafruit Ultimate GPS FeatherWing source at
`1b15a4f782c555903c0cfd7174d0616d2e128887`. The radio uses the common RFM/LoRa
breakout layout at `3ad6bed6e1b407afa7119ae548b5c2f1b107c6b1`, selected for
PID3072 RFM95W. Original Eagle files, upstream attribution and licenses are
retained in [GPS sources](sources/gps-featherwing/README.md) and
[radio sources](sources/rfm-lora/README.md). The checker verifies source bytes,
board/schematic agreement, actual header rotations and all selected pad names.

| GPS terminal | Physical pad | Radio terminal | Physical pad |
| --- | --- | --- | --- |
| 3V | JP4.9 | VIN | JP3.1 |
| GND | JP4.7 | GND | JP3.2 |
| RX | JP3.1 | G0 / DIO0 | JP3.4 |
| TX | JP3.2 | SCK | JP3.5 |
| PPS | JP1.3 | MISO | JP3.6 |
| EN | JP1.4 | MOSI | JP3.7 |
| | | CS | JP3.8 |
| | | RST | JP3.9 |
| | | ANT | JP2.1 |

GPS TX connects to BlackPill PA3; GPS RX connects to PA2. Do not reverse the
UART by following the MCU pin label instead of the GPS terminal label. Keep
the existing PB7 enable control and leave the backup coin absent. Leave all
unused external GPS header connections open.

Coordinates use the component-side outline lower-left. The GPS source board
is50.8mm along X and22.86mm along Y. Its installed long-Y pose requires a
90degree rotation. The radio outline starts at CAD X0.254mm, not zero;
subtract that offset before locating its pads on the25.4mm-wide board.
ANT is thus at outline-relative(21.336,24.511)mm. Retain the existing78mm
internal wire at JP2.1; leave other RF connector footprints without external
connections. Leave JP1 DIO1..5 and JP3.3 EN externally unconnected.

Source names such as `SCK_5V` identify the radio board's logic-input nets.
This assembly supplies VIN with3.3V and uses the existing3.3V MCU signals.
The map does not direct a builder to supply5V. Nominal1mm drills do not prove
finished-wire fit, joints, strain relief, supplied dimensions or electrical
performance. Both installed harnesses and all physical outcomes remain open.

### Module changes

Keep the factory JP1 LED screw terminals on Sparkle Motion Rev D. Adafruit
specifies 20–26 AWG wire and a 5 A rating for these connections. Use the selected
22 AWG branch wire for the positive distribution feed and 26 AWG for data. Put
one lead in each used clamp. A fixed 22 AWG pigtail from JP1.9 supplies the
separate insulated fuse/distribution carrier; do not put four branch leads
under one screw. The pin names in the circuit identify the stock terminal
positions, not bare PCB holes that need oversized wire soldered through them.
[Maker pinouts](https://learn.adafruit.com/adafruit-sparkle-motion/pinouts).

Strip to a 3.2 mm assembly target, from the maker's approximate 1/8 inch guidance.
Inspect insertion and insulation, tighten gently, and restrain the insulated
leads near the board. The maker's current rating does not establish our PWM
peak, wire temperature, screw retention or enclosed thermal performance. Keep
those physical tests unmeasured. The fitted carrier, cuts and complete wire
routes remain required design work.
[Maker assembly instructions](https://learn.adafruit.com/adafruit-sparkle-motion/connecting-leds).

Use **Adafruit PowerBoost 1000 Basic, PID 2030**, with no charger. The reviewed
[Eagle source](https://github.com/adafruit/Adafruit-PowerBoost-1000-PCB/tree/493d06d70537ce418355b395bb251a661d683150)
is pinned at `493d06d70537ce418355b395bb251a661d683150`. Retained connectivity,
original source hashes and attribution are in
[sources/powerboost-1000-basic](sources/powerboost-1000-basic/README.md).

Retain the stock nominal 5.2 V feedback setting. The selected Sparkle barrel
path includes D2 and PTC1 before the LED/logic supply rail. The module's extra
headroom reduces the drop through that path; it does not establish a measured
5.0 V rail. Review/measure the rail at the actual loads before accepting input
limits, buck-regulator headroom, LED voltage or runtime. The calculator's 5 V
load is a stated planning assumption. It is not the measured module output.
Do not rework the feedback divider to 5.0 V while retaining this drop budget.
[TPS61030 SLUS534G](https://www.ti.com/lit/ds/symlink/tps61030.pdf).

Remove only the stock Sparkle **X7 barrel jack** to expose its fixed-wire input
holes. Fit the paired 22 AWG supply and return at **X7.PWR** and **X7.GND**.
Leave **X7.GNDBREAK** open. Keep **D2 and PTC1** installed. This preserves the
reviewed diode/PTC input path. Do not feed an output power clamp instead. The
retained Rev D source gives nominal 0.9 mm holes at [10.239, 10.922] and
[4.339, 10.922] mm from the lower-left PCB corner, viewed from the component
side. Verify actual wire/hole fit, inspect the reworked pads, and restrain the
insulated wires near the board. Final joint envelopes and fitted restraint
locations remain part of the open harness work. Removal of the connector does
not qualify the electrical or thermal limits.

Remove **R20**, the red low-battery LED's series resistor. Connect its **R20.2**
pad, on net N$6, to Pololu OFF. That pad connects to the existing PNP transistor
T1 collector. Add the specified 100 kohm pull-down. The opposite R20 pad goes to
the LED and is not the shutdown signal. The red LED no longer indicates low
battery; do not publish it as a delivered indication.

This uses the board's existing inversion: low battery pulls LBO low, T1 raises
its collector, and a positive pulse requests Pololu OFF. Pololu remains powered
at VIN after its VOUT turns off, so its latch can retain OFF when battery voltage
rebounds. [Pololu control documentation](https://www.pololu.com/product/2808).
The interface voltage, pulse duration and recovery behavior are unmeasured. The
manufacturer warns that supply interruption/noise can lose switch state. The
latch is not a safety disconnect; S1 supplies that separate mechanical function.

Do not connect LBO directly to EN. The TPS61030 disables its low-battery
comparator when EN is low. That arrangement cannot provide this latched shutdown.
Leave PowerBoost EN and LBO header pins without external connections. EN retains
its stock 200 kohm pull-up. Do not install the optional JST battery connector
or USB-A socket. Install two **Pololu2444 two-pin3.5mm side-entry terminal
blocks** at X1 and X2. Keep every JP1 header pad without an external lead.
The retained board and schematic bind the actual positions; positive is pin2
on both blocks. The source net label `5.0V` identifies the stock nominal5.2V
output. Do not change the feedback setting to match that label.

| Pad | Use | Wire |
| --- | --- | --- |
| X2.2 | Switched battery input from latch VOUT |18AWG main |
| X2.1 | Input return directly to the negative star |18AWG main |
| X1.2 | Output through S1 poleB to Sparkle X7.PWR |22AWG branch |
| X1.1 | Output return to Sparkle X7.GND |22AWG branch |
| R20.2 | Low-battery request to Pololu OFF |26AWG signal |

The input return bypasses the Pololu ground trace. Its ground lead carries
control current. Keep each power feed with its return. The seller specifies
24–18AWG wire,10A and5mm stripped length for2444. Put one untinned stranded
conductor in each used clamp. Support the insulated leads near the entries.
These clamps remain closed during cell replacement.
[Seller specifications](https://www.pololu.com/product/2444).

The nominal terminal body is7.96x6.8x8.4mm, with0.8mm round pins. Published pin
length is3.7+/-0.3mm. Adafruit's footprints have1mm nominal drills. The output
body reaches X30.451mm on the29.21mm nominal board. Use these actual source
positions for the carrier; the old rectangular PCB reservation does not prove
fit. The retained seller drawing gives no other body/pin tolerance. Supplied
fit, solder quality, screw retention and enclosed operation remain unmeasured.
Do not force pins or enlarge plated holes. The published20mohm resistance has
no stated maximum qualifier, so it cannot supply a worst-case loss bound.

### OFF and restart

Use the source-based [latch carrier and clamp map](latch-mounts.md). The maker
component-side pinout places A at13.97/3.81mm, below B. Two underside
CamdenBoss CTBP2054/4 blocks accept the18AWG feed and output leads. A separate
26AWG ground lead carries control current. The retained source model and
component check do not replace either installed harness check.

S1 is C&K **7201SYZQE**, DPDT ON-ON. Terminal 2 is the cell-feed pole common;
terminal 5 is the output pole common. The selected RUN contacts are 1 and 4.
In OFF, terminal 2 connects to terminal 3 and a 1 kohm drain to ground; terminal
5 connects to insulated, otherwise unconnected terminal 6. Verify terminal view
and continuity against the delivered switch before wiring.

Thus OFF disconnects the cell's positive feed **and** the converter output from
the loads. R_B drains the boost input. R_BOOST drains its isolated output.
R_LOAD drains the load rail; R_OUT drains C_OUT after the Fibonacci fuse, even
when that fuse opens. Place C_OUT at the Fibonacci feed with short paired leads.
Other board capacitors and signal paths still affect decay. There is no qualified
five-second or ten-second reset wait. `off_dwell_s` remains unset until measured.

For ordinary cell removal, S1 OFF separates the positive contact from all those
stored-charge rails. The digital check conservatively treats every module's
internal terminals as conducting and still requires that separation. Thus a
timed electronic reset does not gate mechanical removal in this prototype plan.
Support the assembly, put S1 fully OFF and remove USB, SWD and every other
live interface before opening. Actual
switch operation, insulation and assembly safety remain unmeasured. A rapid swap
can retain electronic state; do not claim that all boards reset.

After a supported cell swap, select ON and press START. Connect START from the
Pololu **A** pad to ground for **on-only** operation; the standard A-to-B toggle
connection is not this control. A start press does not establish GPS reacquisition,
radio readiness or pattern synchronization. After unexplained darkness, inspect
with power physically OFF. Permit only one charged-spare restart after clearing
an accessible cause; repeated trips, damage or abnormal heat require service.

### Protection, routing and USB

Use one XTAR protected 21700 6000 mAh button-top, not its unprotected or USB-equipped variants.
Its protection is a manufacturer feature, not a published system fault-current
or fuse-clearing bound. F1 remains contact-adjacent. Insulate its unfused tail
and both contact backs. Preserve individual branch protection and the physical
disconnect. The exact short-circuit let-through, fuse/contact/harness withstand
and PCM recovery remain unmeasured; do not infer them from the 10 A cell label.

Use the specified 18 AWG main pair and 22 AWG branch pairs, with soldered joints,
insulation and strain relief. Keep supply and return together and away from the
magnetometer. Wire lengths and loaded module placement must come from each new
native layout. They remain an explicit design error until that work is done.

USB service is off-body with the cell removed and S1 OFF. Select only 5 V USB-PD.
Do not connect another barrel supply or a live external interface at the same
time. S1's second pole separates the USB-powered load rail from the boost output.
Use only the Sparkle USB connector for powered service. Leave BlackPill USB and5V disconnected; use SWD with no probe target-power feed. Install no GPS backup coin cell or other sensor supply. The pin map retains the existing design-v2.md allocation and all shared signals use3.3V. Power-sequencing and injection measurements remain in the bench procedure.
Charge the removed cell externally in a compatible 4.2 V Li-ion charger.

## Load and thermal planning

The candidate's initial bench scenario is 2% electrical brightness, saturated
rainbow/dark-mask patterns, a 2 W non-LED budget, 3.2-4.2 V cell voltage and
10-30 C ambient. These are proposed operating conditions, not measured limits,
firmware ceilings or a safe wearing envelope. The site calculator remains an
adjustable study; a calculator result does not authorize a brightness setting.
Retain the shared Adafruit-based RGB/idle model and `site/energy.mjs` for estimates.
Do not add a second runtime formula to this checker.

The [PowerBoost page](https://www.adafruit.com/product/2030) gives output-current
examples at specific input conditions. The [Pololu page](https://www.pololu.com/product/2808)
gives thermal-current examples at 12 V input and 22 C still air. Neither establishes
an enclosed single-cell thermal limit. Use these conditions as source context,
not as wearable acceptance. Review average/frame demand separately from internal
PWM, radio bursts, inrush and faults. Do not claim that the 85% efficiency or
0.12 ohm path estimate is a guaranteed bound.

## Physical qualification

The JSON retains procedures and empty result lists for startup/current pulses;
low-battery shutdown/rebound; OFF/decay/replacement; controlled fault/reversal;
both closed-enclosure temperatures; runtime; fit and complete worn mass.
Every outcome is **unmeasured**. Record conditions, revision, instruments and
observations before accepting a built unit. A digital release must retain these
limits prominently. Manufacturing and physical testing do not become a human
sign-off gate for this source delivery.

## Selected peripheral and strip inputs

Retain the existing classic **Adafruit LSM9DS1 PID3387**. Feed its VIN from3.3V;
its3V3 pin is a regulator output. Its published33.4x20.4mm board does not fit the
old25x25mm square placeholder. Reserve40x28x12mm with fixed soldered leads and
change both native pockets accordingly. This is a loaded design reservation,
not a measurement or permission to substitute the newer STEMMA board.
[Maker](https://www.adafruit.com/product/3387),
[pin definitions](https://learn.adafruit.com/adafruit-lsm9ds1-accelerometer-plus-gyro-plus-magnetometer-9-dof-breakout/pinouts).

Use **Allcoola WTP-2812-2020-120-0405**, IP20 black FPC, for the cut rings.
The maker identifies120 independent pixels/m, one pixel/cut,4mm width and1.5mm
assembled thickness. The existing10mm-wide seat and2mm package reservation
remain conservative envelopes; optical calibration/adhesive/fit stay unmeasured.
The prior DreamLED page mixes2020 LEDs with a COB description and10mm cutting
segments, so it is not the selected stock. Preserve ring counts and pitch;
remove the stock plug leads and use the fused fixed harness.
[Maker specification](https://www.sk6812.com/?p=2760).

The3.3V external peak allocations are100mA BlackPill,50mA GPS,20mA IMU and150mA
radio:320mA total against the maker's500mA peak external supply figure. These
are engineering allocations to check on the bench, not guaranteed device maxima.
The2W average and3W peak non-LED targets include the controller/logic allowance;
radio duty cycles and actual current remain unmeasured. The checker rejects
missing loads, non-finite allocations and an allocated peak above500mA.

## PWM fuse and bulk-capacitor selection

Use a2A Fibonacci fuse and1A for each ring. The previous1A Fibonacci fuse
did not allow enough for PWM heating. Using the adopted approximate20mA per
channel and1mA idle model, a saturated rainbow at2% gives about1.31Arms
under a conservative coherent-PWM estimate for256 pixels. This estimate is
not a guaranteed current bound. The selected251 series requires25% continuous-current
derating, plus temperature derating. Its nominal cold resistance and melting
I²t do not prove assembly fault withstand.
[Littelfuse251,26-Sep-2024, pp1-3](https://www.littelfuse.com/assetdocs/littelfuse-fuse-251-253-datasheet?assetguid=f47a0bb7-8ede-4679-9646-7114c3787688).

Retain the Panasonic EEUFR1A1021000uF/10V bulk capacitor. Its source body
maxima are10.5x17.5mm. The12x31x14mm horizontal loaded reservation includes
lead space. The1.79Arms rating applies at100kHz/+105C. Apply the maker's
frequency factors to the measured waveform before physical acceptance.
Do not treat its100kHz impedance as a broadband maximum ESR.
[Panasonic FR-A,01-Sep-2025](https://industrial.panasonic.com/cdbs/www-data/pdf/RDF0000/ABA0000C1259.pdf).

The calculator now defaults to the same2%/2W bench scenario. Its0.045W
input-side static-loss allowance and0.12ohm path are estimates. The old0.085ohm
path omitted too much of the selected contacts, switch, fuse and latch. The25%
reserve is an engineering allowance, not a measured cutoff-capacity result.
`site/electrical-inputs.json` owns these assumptions and their loss basis; the
electrical check rejects drift from the shared planning scenario.

## Fixed leaded passives for the module prototype

Use the selected axial251 fuses and axial Vishay MRS16 resistors. This removes
the need for small SMD adapter boards. Keep their insulated soldered joints
fixed and strain-relieved. An opened fuse requires electronics service; it is
not part of ordinary cell replacement. The JSON lists each exact part and its
loaded reservation. These reservations do not establish the fitted harness.

The251 source specifies300A DC interruption at125V and opening within1s
at twice the rating for the selected currents. Its continuous rating needs25%
derating and temperature correction. Do not reuse the459 series'300% opening
time or nominal I²t for these parts. The new4A fuse has20.4mohm nominal cold
resistance; this is not a guaranteed maximum. Fault/thermal tests remain
unmeasured. Preserve the2A Fibonacci,1A ring and0.5A auxiliary protection.

The MRS16 source gives maximum3.6mm length and1.6mm diameter. Its0.4W P70
rating depends on film and joint temperature; it does not rate the completed
wire assembly. Use1%1kohm parts for the five drain positions and1%100kohm
parts for OFF and the two sense-divider positions. The12x3.5x3.5mm loaded
reservation includes formed/sleeved leads. The source125mg mass is a
published value without a maximum tolerance.
[Vishay28724,07-Mar-2016](https://www.vishay.com/docs/28724/mrs16m25.pdf).

### Direct START actuator and wire stock

START uses C&K **PTS645SL70-2 LFS**, a normally-open through-hole switch
with a 7 mm round actuator. Use its stock actuator directly. The selected
[PTS645 source](https://www.ckswitches.com/media/1471/pts645.pdf)
(MI 10/02/26, pages 1, 2, 5 and 7) gives the ordering code, 7 ±0.1 mm
height from the PCB datum and the 6 ×6 ×3.45 mm nominal body. Actuator
height is not operating travel. The source's mechanical-characteristics table
contains inconsistent option/height entries; the design does not use those
entries as guaranteed travel or force bounds. A printed plunger would need
additional overtravel data. It is not part of this direct-actuator proposal.
Actual mounting, finger reach and switching force remain unmeasured.
Connect pin 1 to Pololu A and pin 3 to ground. Pins 1/2 form one internal
contact group; pins 3/4 form the other. Leave duplicate pins 2/4 externally
unconnected and insulate them. Wiring pins 1 and 2 would hold START closed.

Use M22759/16-18 for the main paths, /16-22 for protected power branches and
**M22759/18-26** for signals and control. The selected catalog does not list
26 AWG in /16. The [Thermax/Amphenol catalog](https://www.amphenol-cit.com/wp-content/uploads/pdfs/prodinfo/M22759.pdf)
(header 2012-09-07, printed pages 41–42) supplies maximum outer diameters and
20 °C resistance values. Convert the imperial maximum resistance column
with exactly 304.8 m per 1000 ft; the printed metric column is rounded.
Its wire masses are nominal. The JSON retains this
distinction. Actual route lengths, joints and strain relief remain open.

The 3.2–4.2 V bench sweep includes depletion. PowerBoost senses its own input,
after the loaded input path. Its nominal 3.2 V threshold does not imply
operation down to 3.2 V at the cell contacts.

The rear controls use separate printed mounts and the sourced open mounting
nut/lockwasher. See [control-mounts.md](control-mounts.md) for the specified
clamp stack and component-study command. Full enclosure integration remains
open. GPS EN has a factory pull-down and is **high to disable**; retain that
default and the assigned PB7 control. No pull-up or new firmware is added.

### Retained Mode/Action and ADC filter

Keep Mode on BlackPill PB13 and Action on PB14. Each uses the same direct
C&K PTS645SL70-2 actuator as START. Connect pin 1 to its assigned input and
pin 3 to ground. Leave pins 2/4 externally unconnected and insulated. These
are active-low inputs with the existing MCU pull-up configuration. Their
mounts and wiring remain part of the unfinished fitted layout.

Retain a 100 nF capacitor from the PA4/divider midpoint to ground, beside
BlackPill. Select **KEMET C315C104K5R5TA**, 100 nF, 50 V, ±10%, X7R, radial
leads. The maker's sheet, generated 11/05/2026, gives maximum body dimensions
of 3.81 x 2.54 x 3.14 mm and lead pitch of 2.54 ±0.78 mm. It specifies
capacitance at 1 kHz/1 Vrms. The 7 x 7 x 6 mm loaded reservation is an
assembly target. Temperature, bias and aging affect capacitance.

Do not infer a guaranteed settling time or reset delay from nominal RC
values. Measure PA4 settling and injection during power sequencing. The
source's simulation pages show typical responses, not maximum ratings.
[Manufacturer part sheet](https://search.kemet.com/component-documentation/download/specsheet/C315C104K5R5TA).

Select the **WeAct V3.1 STM32F411CEU6 without optional U3 flash**. Its original
schematic connects U3 to PA4/PA5/PA6/PA7. PA4 is the battery-sense input in this
design. An installed flash chip can conflict with that function. The newer
upstream KiCad README describes different SPI2 pins; use the original V3.1
schematic for this board. Preserve the existing firmware pin allocation.
[WeAct schematic, 17 April 2021, pinned revision](https://github.com/WeActStudio/WeActStudio.MiniSTM32F4x1/blob/6a7f7d434a9d6361f91590d4cdd16b4a70ce7513/Hardware/MiniF4x1Cx_V31%20SchDoc.pdf).

Use manufacturer **P1.3** for 3.3 V and **P1.2** for GND. Battery sense PA4 is
**P1.11**. The selected 21 header pads and their original source coordinates
are in [the V3.1 pin record](sources/blackpill-v31/README.md). The original STEP
has P1 at Y = 18.009 mm and P2 at Y = 2.794 mm, with 2.54 mm X pitch. Do not
replace those positions with the later carrier footprint. Apply one assembly
transform to the board and every pad. No circuit or firmware pin is reassigned.

These are nominal source coordinates. The STEP's PCB thickness is about
1.49144 mm; the release notes state 1.6 mm nominal. Neither gives a guaranteed
supplied-part tolerance. Keep the discrepancy visible and inspect actual parts
before fitting. This source record does not complete a fixture, joint, cut list
or fitted wire route. Physical qualification remains unmeasured.

## Wire-mount cell contacts

Use two Mill-Max0854-0-15-20-82-14-11-0 wire-mount contacts. The selected18AWG
leads use their solder cups. The retained2-Feb-2024 manufacturer sheet and its
hash bind this selection. The sheet gives12A at30C rise,9.6A after20% derating,
and20mohm maximum component resistance under its stated test methods. These
figures do not qualify the assembled cell interface, solder joints, fault
withstand or enclosed temperature. See [the compartment study](battery-access.md)
for clamp gauge targets, wire routing and the limits of the native checks.
