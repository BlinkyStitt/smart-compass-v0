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
one protected XTAR INR21700-50E
  + contact -- F1 4 A -- S1 pole A -- Pololu 2808 VIN
  - contact ----------------------------------------------- GND
                             Pololu VOUT -- PowerBoost BAT
                             Pololu GND ------------------- GND

PowerBoost output -- S1 pole B -- LOAD_5V -- Sparkle barrel PWR pad
                              |             barrel GND ---- GND
                              +-- 1000 uF -- GND
                              +-- 1 kohm --- GND

Sparkle JP1 positive --> individual 1 A fuses --> Fibonacci + three ring groups
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

### Module changes

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
its stock 200 kohm pull-up. Do not install the optional JST battery connector,
USB-A socket or terminal blocks. Use fixed, insulated soldered leads.

### OFF and restart

S1 is C&K **7201SYZQE**, DPDT ON-ON. Terminal 2 is the cell-feed pole common;
terminal 5 is the output pole common. The selected RUN contacts are 1 and 4.
In OFF, terminal 2 connects to terminal 3 and a 1 kohm drain to ground; terminal
5 connects to insulated, otherwise unconnected terminal 6. Verify terminal view
and continuity against the delivered switch before wiring.

Thus OFF disconnects the cell's positive feed **and** the converter output from
the loads. R_B drains the boost input; R_OUT drains the load's 1000 uF capacitor.
Other board capacitors and signal paths still affect decay. There is no qualified
five-second or ten-second wait. `off_dwell_s` remains unset until measured.

After a supported cell swap, select ON and press START. Connect START from the
Pololu **A** pad to ground for **on-only** operation; the standard A-to-B toggle
connection is not this control. A start press does not establish GPS reacquisition,
radio readiness or pattern synchronization. After unexplained darkness, inspect
with power physically OFF. Permit only one charged-spare restart after clearing
an accessible cause; repeated trips, damage or abnormal heat require service.

### Protection, routing and USB

Use one protected XTAR INR21700-50E, not its unprotected or USB-equipped variants.
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
Complete board-level signal and backfeed review remains part of the design work.
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
0.085 ohm path estimate is a guaranteed bound.

## Physical qualification

The JSON retains procedures and empty result lists for startup/current pulses;
low-battery shutdown/rebound; OFF/decay/replacement; controlled fault/reversal;
both closed-enclosure temperatures; runtime; fit and complete worn mass.
Every outcome is **unmeasured**. Record conditions, revision, instruments and
observations before accepting a built unit. A digital release must retain these
limits prominently. Manufacturing and physical testing do not become a human
sign-off gate for this source delivery.
