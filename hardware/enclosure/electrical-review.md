# SKI-1230 electrical candidate review — 2026-10-31

**The proposed path fails the pre-compartment electrical gate.** This checkpoint
adds reproducible rejection evidence; it does not select a qualified assembly.
The enclosure geometry, inventory and published media still describe the legacy
pouch design. No fitted 26650, mass-limit, recovery or runtime acceptance is claimed.

Run `python3 hardware/enclosure/electrical.py check`. It returns **1** for this
candidate. `report` prints the same findings with exit 0 for inspection. The
unit tests validate the arithmetic and rejection behavior, not a physical
circuit or a completed transient model. Inputs, source revisions and the proposed
netlist are in [electrical-review.json](electrical-review.json).

## Candidate connections

```text
fixed positive contact -> F1 -> S1.ON
S1.COMMON = A -> TPS259474L -> B -> U3V70F5 -> 5 V loads
             -> LM66100 -> C -> LTC2955 + dividers
S1.OFF -> 1 kohm -> GND
fixed negative contact = GND (all returns)
LTC2955 EN -> eFuse EN/UVLO
eFuse PG -> boost ENABLE
```

F1 is contact-adjacent, with an insulated unfused termination. Switch OFF
physically disconnects the cell and connects A to the discharge resistor. This
is a proposed schematic topology, **not construction instructions**. Exact
passive part numbers, conductor/PCB design, branch fuses and loaded envelopes
have not been selected. The JSON makes those omissions explicit rather than
turning the 40 × 30 × 14 mm reservation into a manufactured-board dimension.

## Reproducible counterexamples

The divider calculation enumerates independent resistor, threshold and input
current corners using Kirchhoff's current law:

`V_supply = V_pin × (1 + R_top/R_bottom) + I_sink × R_top`.

Positive current sinks out of the divider node. U3's pull-up therefore has a
negative sign. All calculations retain raw precision.

| Boundary | Calculated result | Consequence |
| --- | --- | --- |
| KILL, 324 kohm / 100 kohm, 0.1% | C = 3.201296–3.583265 V | Does not protect the startup blanking interval. |
| Proposed backup UVLO, 17.8 kohm / 10 kohm | Conditional C = 2.935885–3.086857 V | Too low for the loaded regulator during blanking. |
| 6.25 W / 85%, 45 milliohm eFuse, at the lower backup corner | B = 2.818488 V, I = 2.608825 A | Below the boost's 2.9 V specified minimum even with all other drops omitted. |
| Unpowered PG driving boost ENABLE | PG low is specified as high as 1 V at the tabulated pull-up currents; boost shutdown requires <0.4 V | Charged B cannot be assumed to leave the boost disabled after A is disconnected. |

The voltage-drop calculation solves `B² − A×B + R×P = 0`, using the higher
positive root. It is an optimistic steady-state counterexample within the
startup interval, not a prediction of the actual transient. KILL is masked for
304–720 ms. The UVLO calculation also assumes that U3's specified EN pull-up
range at EN=0 V applies at the divider voltage; that extrapolation is **not a
qualified bound**. Even this provisional assumption fails headroom. See
[TI TPS25947 Rev C, §§6.5 and 7.3.11](https://www.ti.com/lit/ds/symlink/tps25947.pdf),
[ADI LTC2955, electrical characteristics pp. 3–4](https://www.analog.com/media/en/technical-documentation/data-sheets/2955fa.pdf)
and [Pololu U3V70F5 connections](https://www.pololu.com/product/2891).

The nominal 100 kohm regulator pull-up cannot be omitted: when B retains charge,
it continues sourcing ENABLE. PG's disabled state under normal supply and its
unpowered state have different guarantees. Do not model them as the same ideal
zero-volt signal. The sources do not certify shutdown for this connection.

A resistor-only adjustment is insufficient. For example, increasing the EN
upper resistor to 19.6 kohm raises the conditional boost input above 2.9 V, but
moves the backup cutoff into the KILL tolerance range. It does not resolve
startup transients, PG shutdown or fuse coordination. The regression suite
ensures such an edit cannot approve this candidate.

## Other limits and engineering work

These are agent-owned design/proof tasks; no schematic or measurements are
requested from Bryan.

- **Fault coordination:** the fuse datasheet specifies 300 A interruption, but
  19.7 milliohm cold resistance and 2.35 A²s melting energy are nominal values.
  Neither supplies a minimum loop resistance or maximum total clearing energy.
  Derive a bounded source/loop model, or add a suitably rated current-limiting
  element, and coordinate it with both contacts, the switch, every trace and
  conductor, and prefuse insulation. Include faults between F1, S1 and the eFuse.
  [Littelfuse 459, 2015-11-11](https://www.littelfuse.com/assetdocs/fuse-459-pico-smf-datasheet?assetguid=7f1922af-54f5-4bfd-8da8-a247513a6a05).
- **Peak demand and heat:** a 6.25 W average does not bound LED PWM, radio bursts,
  startup or a short. Define all branch loads and exact terminations, conductor
  gauges, PCB stack/copper, passive ratings and temperature derating. The 2025
  Mill-Max sheet gives 11 A at 30°C rise and 8.8 A after 20% derating; this is
  different evidence from the earlier 9 A / 10°C-rise catalog. Use the dated
  conditions explicitly. Neither qualifies the contact against the cell or
  the wearable enclosure. [Mill-Max manufacturer sheet, Arrow mirror](https://static6.arrow.com/aropdfconversion/51cd24f6bbea76697111e1326022061c9a4b0141/085-00-152-08-314110.pdf).
- **OFF and reset:** bound discharge and leakage on A, B, C and 5 V, plus the
  controller's 1.4 s maximum lockout. Prove the five-second dwell or replace it.
  LM66100 CE=GND is the reverse-polarity configuration; CE=VOUT is the distinct
  reverse-current-blocking configuration. Do not silently assume C is isolated
  from A during OFF. [LM66100 Rev A, §§8.3.1–8.3.2](https://www.ti.com/lit/ds/symlink/lm66100.pdf).
- **All states and branches:** complete the actual USB, sense and return paths;
  retain cell-removed, 5 V USB service pending that work. Model absent/depleted/
  reversed/bouncing cells, rebound, rapid replacement, charged capacitors,
  overload/short and a cleared fault, including controller blanking and eFuse
  fault-specific recovery. A blown fuse requires service. Neither a hardcoded
  state machine nor a successful arithmetic check proves the analogue circuit.

The cell reference remains 3.7 V × 5.2 Ah = 19.24 Wh; at the stated 6.25 W and
85% efficiency it gives **2.61664 h** before reserve and other losses. The dated
cell specification permits 4.2 V ±0.1 V charging, so component stress review
must include 4.3 V even though the service charger setting is 4.2 V. This does
not authorize a 4.35 V charger setting. [Dated cell evidence](https://budgetlightforum.com/t/test-review-of-efest-imr26650-5200mah-purple-2016/41275).

## Alternatives investigated during this review

A separate supply supervisor could replace the PG-to-ENABLE connection, but
its asserted-low level, unpowered output, discharge response, and restart
hysteresis all need bounds. [TPS3839 Rev D](https://www.ti.com/lit/ds/symlink/tps3839.pdf)
was examined: its table gives a typical 20 microsecond falling propagation
value, not a maximum. It is not a qualified drop-in fix for a proof requiring a
worst-case droop bound. Its output-low specification also needs checking against
the regulator's strict below-0.4 V shutdown requirement.

Higher-interrupt and total-clearing-energy fuse families were also checked.
[Littelfuse SPXC](https://www.littelfuse.com/assetdocs/spxc-datasheet?assetguid=76d9650a-2194-4fbe-93c9-35f4e0d320eb)
publishes total-clearing figures at 15 kA / 1500 VDC, a different operating point
from this one-cell circuit. [Eaton KLM](https://www.eaton.com/content/dam/eaton/products/electrical-circuit-protection/fuses/data-sheets/bus-ele-ds-2020-klm.pdf)
provides total-clearing curves, but no candidate was qualified against this
cradle's contact, trace and wire withstand. Do not replace a missing maximum
with a nominal melting value or extrapolate these operating conditions silently.
These searches do not establish a human dependency; further circuit engineering
remains necessary.

## Delivery and acceptance boundary

The PR #12 patterns and native macro shutdown fix are integrated from
`444166661a0b7f4ea736cfc9c344f5a81f6f16bd`, preserving the existing night lighting,
pattern IDs and default rainbow. No CAD or inventory is relabeled as 26650.

Next engineering checkpoint: repair the electrical topology and close the
sourced corner/state model, then design the fitted compartment and independent
mass/balance ledgers, then replace the calculator's unqualified study coefficients
with reviewed bounds and complete the native/Pages release. The current gate must remain failing until those required
electrical proofs exist. Physical fit, electrical protection, temperature,
optical performance, runtime and wearing comfort remain **unmeasured** and are
separate evidence limits, not prerequisites to a local source commit or requests
for human trials/sign-off.

## Control and discharge engineering trial

[electrical-control-study.json](electrical-control-study.json) records a new
concrete trial netlist and the additional discharge components. The buffer
separates U3 EN from the eFuse divider. A 1.96 kΩ / 1 kΩ UVLO divider and
365 kΩ / 100 kΩ KILL divider give conditional thresholds of 3.176634–3.311859 V
and 3.510226–3.930406 V. With the declared 0.1 Ω post-sense path study input,
the 6.25 W / 85% reference gives B=2.925275 V. This repairs the static ordering
and headroom calculation under those inputs; it does not select that path.

The proposed Nexperia 74LVC1G07GW fails its input-transition review. Even the
typical 5 pF input and optimistic maximum LTC pull-up assistance give
31.4945 ns/V across the central 30–70% transition, above Table 6's 10 ns/V
limit. Its description's Schmitt action does not override that table, and
there is no maximum capacitance to prove a better bound. The output-leakage
test conditions also require qualification at the actual divider node.
[Nexperia Rev. 18, Tables 6–7](https://assets.nexperia.com/documents/data-sheet/74LVC1G07.pdf).

The trial adds direct 1 kΩ bleeders on B and C, retaining the switched A drain
and output bleeder. The RC solver includes an incoming leakage current and
rejects targets below the resulting equilibrium voltage. A 1,000 µF nominal
5 V output capacitor with the study's 20% tolerance, 10 µA incoming leakage,
resistance tolerance/TCR/aging allowances, 5.25 V initial voltage and 0.1 V
target takes 5.060103 s. Adding the 1.4 s lockout gives **6.460103 s**. Thus this
trial does not support five seconds. The 0.1 V target is a study criterion,
not a sourced reset guarantee. Board capacitance, rail coupling and USB leakage
are still unbounded, so neither 6.46 s nor a rounded-up dwell is qualified.
The selected trial bleeder is CRCW06031K00FKEA; its 0.10 W standard-mode P70
rating and resistance allowances come from [Vishay document 20035](https://www.vishay.com/docs/20035/dcrcwe3.pdf).

A permanent C bleeder also worsens depletion drain while S1 remains ON:
at a nominal C=3.7 V it adds **3.7 mA / 0.32856 Wh per day**, in addition to
other branch demand. The original approximately 0.2 mA estimate therefore
does not apply to this trial. A switched discharge topology is preferable,
but must include its off-state leakage and failure states in the model.

`python3 -m unittest discover -s hardware/enclosure -p test_electrical.py -v`
checks the new equations, unreachable targets and both rejection cases.
`python3 hardware/enclosure/electrical.py check` includes this trial and still
returns 1. The original PG/ENABLE, short-current/clearing-energy, complete BOM,
transient, reversal/backfeed and thermal failures remain active. This is new
engineering evidence, not a repeated request for a human schematic.
