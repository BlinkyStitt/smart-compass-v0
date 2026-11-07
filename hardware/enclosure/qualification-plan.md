# Built-prototype qualification procedure

All physical results are **unmeasured** for the selected narrow prototype.
The earlier wide design is an inactive archive. This procedure is part of the
digital delivery. It does not record physical acceptance or require a human
sign-off before the source work can finish. Manufacturing and these tests are
outside that delivery. Keep the seven outcome records in
[electrical-design.json](electrical-design.json) unmeasured until a separate
review can accept actual revision, conditions and results.

Use the selected module circuit in [electrical-design.md](electrical-design.md).
Do not test the rejected custom circuit as if it were this assembly. Use only a generation with passing fitted-loom, complete narrow inventory and
native release records before building from the design. Digital passing records
do not qualify the supplied assembly or authorize wearing it.

## Record each test

Keep separate records for fit, electrical behavior, temperature, optics, runtime
and worn mass/balance. Identify the narrow revision and selected ring material variant. Record:

- The Git commit, native manifest and source/export hashes.
- The actual cell model, lot, condition, initial voltage and charge method.
- All installed modules, rework, wire cuts, fuses, insulation and fasteners.
- Firmware revision, pattern, electrical brightness, enabled LED groups,
  non-LED activity and radio duty cycle. A rendered pattern is not firmware.
- Instruments, probe locations, calibration status, sample rate and bandwidth.
- Ambient conditions, enclosure state, support fixture and test duration.
- Raw traces, photographs, observations, failures and any change between trials.

Record a failure as a failure. Retain it when a later revision passes. A test on
one design or an open enclosure does not accept the other closed design. Keep
unexecuted rows unmeasured. Do not replace observations with calculator values,
nominal component figures or synthetic test fixtures.

## Initial conditions and limits

Start on the bench with a supported assembly. Use a current-limited laboratory
supply for initial circuit tests. Record its limit and any interaction with
startup. Then repeat normal-operation tests with the selected protected XTAR
cell. The supply trial does not establish the cell protection behavior.

Use the current shared planning scenario: 2% electrical brightness, the delivered
rainbow and three dark-mask patterns, a 2 W average non-LED allocation, a
3.2–4.2 V cell sweep and 10–30 C ambient. These are test conditions and budgets,
not measured limits or firmware controls. Test each pattern for complete
eight-second cycles. Test each design's actual pixel counts. Include black
output with powered pixels to measure idle demand. Full-white/full-brightness
operation is outside intended use and is not a required normal-load trial.

Keep separate transient and fault tests. Low average rainbow demand does not
bound internal PWM current, radio bursts, inrush or a fault. Do not infer a
system short-current limit from the cell's 10 A label. Use the retained maker
conditions for each component limit. Treat typical efficiency, contact
resistance and nominal fuse I²t as estimates, not guaranteed maxima.

The [PowerBoost source](https://www.adafruit.com/product/2030),
[Pololu control source](https://www.pololu.com/product/2808) and
[selected cell source](https://xtardirect.com/products/xtar-21700-6000mah-10a-lithium-ion-battery-for-flashlight)
describe component behavior. They do not accept this enclosed assembly. Keep
the separate mechanical S1 disconnect; the Pololu latch is not a safety
disconnect. Retain each source revision and applicable test conditions with
the record. Do not add an assumed reset time or thermal acceptance limit when
the source or physical review does not supply one.

## Fit, captive access and repeated service

Inspect the unpowered assembly first. Check contact travel, wrapper and end
insulator clearance, contact-back insulation, wire restraint, full fastener
engagement, polarity marks and every finished joint/knot gauge. The fuse
assembly gauge is an inspection target, not a guarantee of a supplied joint.

Repeat the complete documented service sequence on each design with its rear,
optics and necklace installed: support, S1 OFF, remove live interfaces, open the
captive door, release the keeper, extract deliberately, insert the compatible
cell, close the keeper/door, select ON and press START. Check the sequence in
ordinary light and low light. Record the light level and cycle count. Check
that access needs no tool and does not require pulling wires or removing other
electronics. The open door must stay captive and opening must not drop the cell.

Try a partially seated cell and a trapped pull ribbon with power OFF. Neither
must produce an apparently complete latch. Inspect for wrapper scraping,
positive-terminal-to-can contact, sharp edges, pinch points and loosened
contacts after repeated swaps. Record any wear, intermittent contact or changed
retention. Check reachable tactile OFF and latch cues without relying on color.

Check the documented darkness response. Permit one charged-spare restart after
inspection and removal of an accessible cause. Continued darkness, damage,
contamination, repeated trips or abnormal heat require service. Do not count
repeated cycling or a bypass as successful recovery.

## Electrical behavior

For `startup_and_pulses`, capture cell/input/output voltage and current during
ON/START, each normal pattern, group changes and representative radio activity.
Probe the load ends as well as module terminals. Record peak, average and RMS
values with the measurement bandwidth. Check the 3.3 V external load allocation,
logic-pin voltage and power sequencing. Inspect Mode/Action and the PA4 filter
response; do not claim ADC calibration from an RC calculation.

Measure actual LED PWM frequency and each fuse's RMS current. Apply the selected
251 fuse's continuous-current and temperature derating. Measure C_OUT ripple
and terminal voltage. Its 100 kHz/+105 C ripple rating is not the rating for an
arbitrary measured waveform; apply the source frequency factors. Normal use
must not cause a reset, trip, unintended latch change or an out-of-rating pin
voltage. Record any current-limit interaction instead of masking it.

For `latch_and_rebound`, lower the supply through depletion while recording
PowerBoost R20.2, Pololu OFF, B and load current. Repeat with a slow decline,
fast drop and contact interruption/bounce. Confirm shutdown and no restart on
rebound while VIN remains present. Record the actual threshold, request-pulse
amplitude/duration and power-loss default. Distinguish latch retention from
state lost during a supply interruption. Do not fit nominal values as bounds.

For `off_and_replacement`, verify both S1 poles by continuity with power removed.
Then capture A, B, isolated boost output, LOAD_5V and the Fibonacci capacitor
rail after OFF. Remove USB/SWD and other live interfaces. START must not restore
the load while S1 is OFF. Repeat a rapid replacement and a warm replacement.
Repeat with F_FIB open to test the three separate output drains. Measure decay
and retained state. No five- or ten-second reset dwell is accepted in this plan.
OFF contact isolation permits the specified mechanical service sequence;
it does not prove that every board has reset.

For USB service, remove the cell, select S1 OFF and use only the Sparkle USB
connector at 5 V. Keep BlackPill USB, probe target power and other external
supplies absent. Check for backfeed at the cell contacts, latch and boost
terminals, and for injection into unpowered signal pins. Record current and
voltage. Do not test simultaneous supplies as an approved operating mode.

For `short_and_reversal`, use a controlled laboratory fault fixture and an
independently reviewed test energy/current limit. Do not deliberately short a
loose cell. Test reversal, branch overload/faults, cell PCM recovery and faults
on both sides of the downstream protection. Record actual clearing, component
stress and damage, including the prefuse termination. A cleared fault must not
cause depletion cycling or an unintended restart. An opened fuse requires
service; an electronic restart cannot repair it. A low-energy supply test does
not establish cell-fed let-through or harness/contact withstand.

## Closed-enclosure temperature

For `thermal`, record a baseline and time series for cell, contacts, switch,
latch, converter, fuse/joint areas, wire groups and front/rear touch surfaces.
Use the complete closed narrow enclosure at the declared ambient and normal rainbow
settings. Record support, orientation, insulation from clothing and radio/load
activity. Keep the first enclosed trials off-body. Include warm restart and
the longest intended normal run.

Compare measurements with each selected part's applicable source limits and
review touch/skin conditions separately. Record the maximum, rise and whether
temperature has stabilized. A free-air module rating or an open-case trial
does not accept a closed pendant. Do not fill an unknown maximum with a typical
value or call a planning temperature a measured wearing limit.

## Runtime and optics

For `runtime`, record usable input energy and elapsed powered time with the
named pattern, brightness, groups, non-LED activity and cell condition. Capture
shutdown and the voltage rebound. Compare measured demand/energy with
`site/energy.mjs`; record converter, path and cutoff losses separately. Do not
count cell reserve or conversion loss twice. Record swap downtime separately
from GPS reacquisition and pattern/radio synchronization. There is no
four-hour-per-cell promise or delivered navigation-ready indication.

Record optics separately under named ambient/light conditions. Inspect low-light
glare, moving spatial color, mask continuity, stored glow, and light leaking
through battery/access openings. Keep separate silver/glow results for the active narrow assembly. Preserve any
older wide results as historical records. A rendered night scene does not establish physical optical performance.

## Complete worn mass, balance and comfort

For `fit_and_worn_mass`, weigh the complete ready-to-wear unit with its installed
cell and necklace. Exclude charger, unused stock and carried spares. Reconcile
the measured assembly against its per-design inventory, including every wire,
fuse, passive, tie, fitting and fastener. Report scale uncertainty. Compare the
complete upper bound with 1,133.980925 g; report the separate 50 g margin target.
Neither a bare printed mass nor a partial rigid-part subtotal is worn mass.

Record hanging angle, lateral twist, fore/aft tilt and changes during walking.
Check switch/door reach while supporting the pendant, necklace pressure, seam
abrasion and snag/release behavior. Compare installed balance with the native
mass/moment model. Keep wearing trials separate from the initial bench checks.
Do not accept a clasp or sewn joint from tape breaking strength alone.

Record compass behavior separately with the assembled wiring, cell, necklace
fittings and fasteners installed. Compare power OFF, black powered output,
rainbow and representative radio activity at fixed orientations. Keep a stable
reference and report heading changes and repeatability. Do not infer magnetic
compatibility from a material label or an RF service check.

## Result status

| Outcome owner | Present result |
| --- | --- |
| `startup_and_pulses` | Unmeasured |
| `latch_and_rebound` | Unmeasured |
| `off_and_replacement` | Unmeasured |
| `short_and_reversal` | Unmeasured |
| `thermal` | Unmeasured |
| `runtime` | Unmeasured |
| `fit_and_worn_mass` | Unmeasured |

Keep the separate fit, optics and balance/comfort observations with these
records. A source commit, native geometry pass, CI pass, merge or deployment
does not change any physical outcome to accepted.
