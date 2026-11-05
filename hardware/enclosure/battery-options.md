# Single removable protected cell: decision and qualification

Engineering decision, revised 2026-11-04 for SKI-1230: use one **XTAR protected
21700 6000 mAh / 3.6 V / 10 A button-top**, with charged spares carried separately.
Bryan authorized a safer cell and a module-based prototype. This selection replaces
the earlier XTAR 50E 5000 mAh candidate because the maker publishes a maximum
cell mass. It retains a protected single-cell architecture and external charging.
The existing CAD and mass ledger still describe the legacy pouch until rebuilt.
The historical custom-circuit review and recovery counters remain unchanged.

**Canonical release artifacts have not integrated this selection.** Component
and private installed-geometry studies do not complete the wired assembly.
Complete worn mass, including the installed cell and necklace, must be at most
**2.5 lb = 1,133.980925 g**, with a separate 50 g margin target. The active
[module design](electrical-design.md) still requires fitted integration. CAD,
inventory and publication remain pending. Physical acceptance stays unmeasured.

Use a dedicated holder for this exact protected button-top cell. Exclude adapters,
a second installed cell, selectors, series/parallel connections, hot swap and
onboard charging. Charge the removed cell externally. Firmware voltage reporting
is not cell protection. The protected product adds manufacturer protection;
it does not establish inherently safer chemistry or complete device safety.

## Energy and cell evidence

The [XTAR official-store specification](https://xtardirect.com/products/xtar-21700-6000mah-10a-lithium-ion-battery-for-flashlight) lists
6000 mAh, 3.6 V, 10 A continuous discharge, a button top and integrated protection.
It gives diameter 21.8 +/-0.3 mm, length 74.8 +/-0.5 mm and net weight **<=76 g**.
Use **22.1 x 75.3 mm** cell-only maxima before holder, contact travel, insulation,
clearance and removal space. The source has no numbered revision; retrieved
2026-11-04. These data apply to this exact product, not the 50E, unprotected,
high-current or USB-equipped variants.

The maker does not publish this product's exact protection thresholds, delays,
short-current let-through or recovery sequence. Keep those physical outcomes
unmeasured. Its 10 A label does not qualify the installed contacts, fuse, harness
or enclosed temperature. The <=76 g cell bound does not establish complete worn
mass or a finished-assembly measurement.

Retain the 6.25 W / 85% nominal energy reference:

```text
6.0 Ah x 3.6 V = 21.6 Wh
21.6 Wh x 0.85 / 6.25 W = 2.9376 h (display 2.94 h)
```

The shared [electrical input record](../../site/electrical-inputs.json) owns this
reference and the calculator defaults. This is nominal arithmetic before
reserve, efficiency variation, aging, temperature, contact/wire loss, cutoff
and swap downtime. It is not measured runtime, guaranteed usable energy or a
peak-load rating. The
[rainbow demand basis](../../site/README.md#rainbow-demand-basis) uses
Adafruit's NeoPixel channel/idle estimates and samples the real shared pattern.
This estimate does not require replacing Fibonacci256 or obtaining supplier
data. At the current 2% calculator brightness, all Wide pixels average about
0.786 A at 5 V; Narrow averages 0.742 A. With the documented reserve and other
loss assumptions, calculated runtime is about 2.14 h / 2.23 h respectively.
Two percent is not a firmware-enforced limit. Physical brightness and runtime
remain unmeasured; fault, inrush and thermal checks remain separate.

Historical Efest evidence remains in the original electrical review:
[HKJ's 2016 report](https://budgetlightforum.com/t/test-review-of-efest-imr26650-5200mah-purple-2016/41275)
reproduced 26.22 ±0.15 × 66.2 ±0.15 mm and 92 ±1 g for the reviewed variant.
Its 19.24 Wh nominal reference gave 2.61664 h at the same output/efficiency.
Do not transfer that cell's mass, dimensions or current labels to the XTAR.

## Historical candidate investigations

The following table records earlier candidate investigations. These parts do not
define the active module prototype. Use [electrical-design.json](electrical-design.json)
and its [design review](electrical-design.md) for the selected circuit, open
design items and physical test procedures. The fitted harness remains incomplete.

| Element | Evidence | Decision / missing qualification |
| --- | --- | --- |
| Fixed holder: Keystone 1107 | [Manufacturer product](https://www.keyelco.com/product.cfm/product_id/14077) and [drawing](https://www.keyelco.com/product-pdf.cfm?p=14077) identify a one-cell 26650 solder-lug holder; the [catalog, page 30](https://beta.keyelco.com/userAssets/file/M70p23-33.pdf) specifies PBT and nickel-plated stainless-steel lugs. | Candidate only. Reviewed evidence does not establish continuous/pulse current, contact resistance, or allowable loaded contact travel for the 66.35 mm flat-top reference. Do not infer loaded height, terminal clearance or removal travel from an empty-holder outline. |
| Pack protector: Tenergy 32195 | [Manufacturer specification](https://power.tenergy.com/tenergy-1s-li-ion-8-5a-18a-pcb-discharging-cut-off-voltage-2-8v/) lists 28.8 × 7 × 2.5 mm, 8.5 A operation, 2.80 ± 0.10 V undervoltage detection and 18.5 ± 4 A overcurrent detection; overcurrent release requires removing the load. | Not selected. Reverse insertion is unspecified. The undervoltage delay mixes seconds and milliseconds, and the release tolerance needs clarification. Removal/reinsertion startup and charger-reset requirements are unspecified. Its trip range cannot be assumed to protect an unrated holder or harness. |
| Integrated circuit alternative: TI TPS25947 | [TI datasheet, sections 4, 7 and 8](https://www.ti.com/lit/ds/symlink/tps25947.pdf) specifies 2.7–23 V operation, negative-input tolerance, adjustable UVLO/current limit/inrush, and distinct auto-retry/latch-off variants. | Plausible custom circuit, not a selected module. Requires an exact variant, schematic, tolerance analysis, upstream fuse coordination, PCB/thermal design, loaded envelope and depletion/restart analysis. A 2 × 2 mm IC package is not a board envelope. |
| Retained boost: Pololu U3V70F5, item 2891 | [Manufacturer specification](https://www.pololu.com/product/2891): 2.9–5 V input, 40.6 × 15.2 × 4.6 mm bare board, reverse-voltage protection and short-circuit hiccup recovery. | Historical regulator assumption; an assembled replacement is permitted. Its protection applies at the regulator, not to upstream contacts, wires or protection electronics. Its typical 2.4 V falling UVLO and 10 A switch limit do not replace cell/path protection. |

The earlier [TI BQ2970 recovery discussion](https://e2e.ti.com/support/power-management-group/power-management/f/power-management-forum/818910/bq2970-removable-batteries)
shows why a different pack protector can need a wake-up intervention. It does
not establish the selected XTAR cell's recovery behavior. Its exact protection
thresholds, delays and fault recovery remain unpublished and physically unmeasured.
Do not transfer another protector's settings or test results to this cell.

## Active module design and remaining work

The selected topology is:

```text
cell+ → fixed contact → adjacent F1 → S1 pole A → Pololu 2808 → PowerBoost
PowerBoost output → S1 pole B → Sparkle Motion → separately fused displays
                                             → fused 3.3 V peripherals
cell− → fixed return/star → all required returns
```

The [complete netlist](electrical-design.json) owns the individual terminals,
branch fuses, drains, sense filter, START and existing controls. Use its selected
wire gauges and terminations. The boost input return goes directly to the
negative star; it does not carry boost current through the latch ground trace.
The battery sense divider connects to switched B. Keep the selected USB policy:
remove the cell, leave S1 OFF and use only Sparkle USB at 5 V, off-body. Do not
connect a powered BlackPill USB cable or a probe target supply at the same time.
Do not charge a cell inside the pendant.

The digital review checks concrete parts, connections, supply interfaces,
physical OFF topology and source records. It still rejects the missing fitted
harness. Both designs need installed wire routes and cut lists, joint insulation,
taps, bends, strain relief and clearance checks. The final per-design inventory,
worn-mass and balance ledgers, CAD exports, service illustrations, media and
Pages remain required. A passing component study does not close these items.

The old 2.9 V boost calculation belongs to the superseded Pololu design. It is
not the PowerBoost's minimum input rating or a measured shutdown point. The
active bench plan uses 2% electrical brightness and a 2 W non-LED allowance;
these are planning settings, not firmware limits or guaranteed peak bounds.
The loss/runtime model and electrical review retain their stated approximations.
Measure PWM/radio/inrush behavior, depletion/rebound, OFF decay, fault withstand
and temperatures on the actual assemblies. Keep those physical outcomes
unmeasured until results exist. Physical manufacturing and qualification are
outside this digital delivery and do not require a human sign-off to finish it.

## Specified replacement sequence

This is the specified sequence for the unbuilt removable-cell assembly. It is
not an instruction to put a loose cell into the existing pouch cradle. Both
final service guides must illustrate it with the rear, optics and necklace fitted.

1. Support the pendant by hand or on a padded surface. Use the case as support.
   Do not hang it from wires or the door.
2. Put physical S1 fully OFF. Disconnect USB, SWD and every other live interface.
   A dark display does not prove that S1 is OFF.
3. Release the door catch and open the captive door. The separate keeper still
   retains the cell. Release the keeper only when you have control of the cell.
4. Press the cell towards the fixed negative insulating stop. Lift the positive
   end clear and use the ribbon to remove the cell deliberately. Keep it clear
   of the contacts and protect the wrapper and end insulator.
5. Check the accessible contacts, wrapper, end insulator and polarity marks.
   Insert one compatible, externally charged XTAR cell to the durable +/− marks.
   Put the ribbon in its specified path. Close the keeper, then latch the door.
   Do not force a partly seated cell or trapped ribbon into closure.
6. Select ON and press the on-only START button. A swap interrupts operation.
   Power restoration does not prove GPS acquisition, radio synchronization or
   pattern readiness. No new diagnostic indication is delivered by this task.

With S1 OFF and external power absent, the reviewed topology disconnects the
positive cell contact from the downstream stored-charge rails. Mechanical removal
does not depend on a timed electronic reset. **No qualified OFF/reset dwell is
available.** Residual charge and all decay/reset times remain unmeasured. A rapid
replacement can retain electronic state. Do not promise a full reset from this
sequence or use blank LEDs as evidence that stored charge has disappeared.

| Event | Specified action and evidence limit |
| --- | --- |
| Depletion | Support, OFF and remove the depleted cell. This separates it from residual downstream drain. Insert a compatible charged spare, latch, ON and START. Verify actual latch/rebound and startup behavior during physical qualification. |
| Reverse insertion | OFF before correcting orientation. Inspect the wrapper, end insulator and contacts. Stop if damaged, hot, contaminated or abnormal. The selected protection does not establish whole-assembly fault acceptance. |
| Short, overload or repeated trip | OFF first. Remove the known cause before a reset. Persistent or unexplained trips need service. Do not repeatedly cycle power, bridge a fuse or bypass protection. |
| Darkness, cause unknown | Support and OFF. Check the latch, marked polarity and accessible cell/contact condition. If normal, permit one compatible charged-spare restart. If it stays dark or trips again, stop and service it. Darkness does not diagnose depletion. |
| Cell protection will not recover | Remove the cell for inspection and follow the cell maker's limits. Do not apply a charger across the pendant contacts or bypass protection to wake it. A blown fuse needs service. |

Charge off-body, outside the enclosure, in a charger explicitly supporting
3.6 V nominal, 4.2 V charge-termination Li-ion protected button-top 21700 cells
up to the selected cell length. Follow
the cell and charger current/temperature limits. The
[XTAR VC4SL manufacturer manual](https://www.xtar.cc/companyfile/vc4sl-user-manual-88.html)
is a candidate reference, not an owned or qualified charger. Do not use a 4.35 V
or LiFePO4 charge setting, force-charge a damaged/deeply discharged cell, or use
a charger's recovery function to conceal repeated protection faults. Carry each
spare in its own insulating terminal-covering case; distinguish charged and
depleted cases with text or shape, not colour alone. Spares and charger are not
installed worn mass.

## Existing geometry and mass are legacy evidence

At baseline `7449b57648bb006e8d53136469745242bf09b43c`, both parameter JSON files
and generated inventories still represent the **190 g / 37 Wh,
80 × 65 × 20 mm CU-MM109 pouch candidate**. Its two-strap wide cradle and
screw-fastened rear access do not satisfy field replacement. The old 5.03-hour
calculation on Pages describes that pack, not the selected protected XTAR. Historical
belt/pouch guidance in `design-v2.md` and generated tables is not an alternative
approved architecture for SKI-1230. Do not relabel existing CAD, clips or mass
numbers as the removable-cell design.

The wide scene records a 38.0048 mm body depth; its assembly bounds span
47.2048 mm including screw projections. The narrow body is 200 mm diameter ×
57.6 mm deep. Future comparisons must distinguish body dimensions from complete
occupied bounds and include the open-door/removal envelope. Evaluate widening
against depth and mass after the complete fitted layout review.

Legacy complete-worn estimates from the regenerated inventory and site resolver
(2026-11-03):

| Legacy design | Nominal | Summed allowance bounds | Margin to 1,133.980925 g at upper bound |
| --- | ---: | ---: | ---: |
| Wide | 1,082.9 g | 834.6–1,347.3 g | −213.3 g |
| Narrow | 1,123.6 g | 862.3–1,388.1 g | −254.1 g |

These bounds are not confidence intervals; neither establishes weight acceptance.
The narrow result still transfers wide fittings/harness allowances. Replacing
only the pouch mass with the dated cell mass would not close either upper-bound
deficit, even before adding a holder and protection. Do not shrink allowances
just to pass the ceiling.

After layout review, give each design its own complete inventory and unrounded
upper-bound comparison. Count the cell, holder, protection, door, latch, seal,
fasteners, wiring and necklace once; exclude stock, samples, spares and charger.
Publish nominal mass, summed bounds, installed cell mass, upper-bound margin and
unresolved allowances prominently. Derive each pendant's mass-weighted centre of
gravity and bounded uncertainty from its installed parts relative to its own
suspension points. Assess fore/aft tilt and lateral imbalance; reposition parts
before adding counterweights. Current renders establish neither balance nor
walking comfort.

## Resume and release boundary

After required digital design checks pass, update each design's parameter JSON;
saved CAD spreadsheets and Pages are outputs. Rebuild Wide, then Narrow, then
Pages.
Update `design-v2.md` through its inventory generator, both enclosure READMEs,
service materials, site calculations/cards and size comparison in the same
release. Remove obsolete pouch/belt accounting with its replacement inventory.
Verify one-cell enforcement, loaded and moving clearances, complete per-design
accounting, unrounded mass bounds, runtime and centre-of-gravity uncertainty.

Preserve Fibonacci256/stencil, configurable optical gaps and distinct whole
circles. Coordinate shared preview work with SKI-1225: retain separate moving
rainbow clips, the matched 384-frame/24-fps figure-eight loop, stationary
mannequin and field, zero night sun, and sky/amber/blue lights.

Run `just validate` for the serial automated contract. It includes host tests,
`electrical.py check`, actual Godot sampling and energy tests, both native
pipelines and the Pages/browser checks. A failed electrical gate stops dependent
publication. Require complete LFS content and matching input/export hashes;
reject changed inputs. The orchestrator owns deployment verification and
complete-release rollback.

Digital validation does not establish physical fit, repeated low-light swaps,
latch/seal/retention, protection/recovery, rail transients, enclosed heat,
optics/runtime, magnetic interference, hanging angle/twist, walking comfort or
measured worn mass. These outcomes remain unmeasured evidence limits for both
designs, not manual acceptance gates, owner assignments or a human handoff.
Automated geometry sweeps, injected electrical states, rendered assertions and
raw mass arithmetic remain required and must fail when their bounds are missing.
