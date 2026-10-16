# Battery fit and power options

Research date: 2026-10-11. Target **four hours of bright animated patterns** with all four displays, GPS and radio active. Prefer Adafruit parts. Use protected raw LiPo or Li-ion cells with a separate regulator. USB power banks are excluded from the baseline because Bryan has experienced flicker and protection trips with changing LED loads.

## Field replacement requirement

The current CAD battery is a **provisional fit candidate**, not a purchase.
Its screw-fastened rear and two pack straps do not provide the quick cell changes
required for the field design. Bryan selected **one removable 26650 plus charged spares** for the next revision.
Battery replacement must use a dedicated, captive,
tool-free cover or removable cartridge, without opening the optical stack or
exposing the other electronics. Keep the current CAD weights and runtime tied
to its actual 190 g / 37 Wh pack until a replacement layout is built and checked.

Bryan already uses **Efest Purple IMR26650 5200 mAh flat-top, 15 A / 40 A** cells.
The [original tester's report](https://budgetlightforum.com/t/test-review-of-efest-imr26650-5200mah-purple-2016/41275)
lists nominal 3.7 V and about 26.2 mm diameter; the
[supplier identifies this variant as unprotected](https://www.batteryjunction.com/products/efest-imr26650-4335).
The report is for a 2016 sample, not a measurement of Bryan's cells. Do not use
the pulse rating to rate the holder or power path. His approximately 3 Ah 18650s
are another possible source; their exact model is not yet known.

At the existing assumed 6.25 W total load and 85% conversion efficiency:

| Arrangement to evaluate | Nominal energy | Calculated hours before reserve and extra losses | Access and circuit tradeoff |
| --- | ---: | ---: | --- |
| One 5200 mAh / 3.7 V 26650 | 19.24 Wh | 2.62 h | Simplest removable-cell bay; carry charged spares. Needs a rated holder and hardware cell protection. Does not meet four hours without a swap. |
| Two independently protected 26650 bays | 38.48 Wh total | 5.23 h total | Source selector draws from one bay at a time and blocks reverse current. Adds a second holder and selection/protection electronics. Can be designed for individual cell replacement. |
| Existing factory protected LiPo pack | 37 Wh | 5.03 h | Current geometry and mass basis. A dedicated pack cartridge/cover and keyed disconnect could allow a whole-pack swap. The present rear does not. |

Do not wire removable cells directly in parallel. A charged spare can drive
current into a depleted cell. [Adafruit's pack guidance](https://learn.adafruit.com/li-ion-and-lipoly-batteries/multi-battery-packs)
explains the difference between loose cells and a matched factory pack.
A factory pack is one solution, not the only possible architecture. A correctly
designed source selector can keep two cell bays electrically separate.
[TI's TPS2121](https://www.ti.com/lit/ds/symlink/tps2121.pdf) supports reverse-current
blocking and input selection at single-cell voltages. It is an IC design candidate,
not a selected or tested battery module. It does not replace each cell's
undervoltage/short-circuit protection, fuse or reverse-insertion protection.
Charge removable cells separately in the appropriate external charger; the
proposed selector does not charge or balance them.

A 26650 needs about 26 mm of depth before holder walls and clearance, compared
with the current 20 mm pack. Do not claim that either current case will accept
it unchanged. The single-cell arrangement is selected. Check the holder, protection
boards, door, removal path and wiring in both native layouts. A two-cell series
pack would also need a different regulator: the current boost accepts 1S only.
No alternative here has a completed layout or a verified runtime.

## Selected fit candidate

The CAD uses one [BatterySpace CU-MM109 / item 4816](https://www.batteryspace.com/customizepolymerli-ionbattery37v10ah37wh7aratethinpvcandnolabelcu-mm109pid4816.aspx): a factory **1S 10 Ah LiPo pack**, nominal **3.7 V / 37 Wh**, **80 × 65 × 20 mm**, **190 g**. The supplier lists an 8 A protection board, 7.3 A polyswitch, 7 A maximum discharge, and 18 AWG open leads. It supplies the matched cells and protection as one assembly. Do not build a pack by joining separate pouches. This is a provisional fit candidate, not a purchase or a measured runtime result. Confirm the supplied pack drawing, protection thresholds and lead arrangement before manufacture.

A [Pololu U3V70F5, item 2891](https://www.pololu.com/product/2891) supplies fixed 5 V. The published bare-board envelope is **40.6 × 15.2 × 4.6 mm**. Its input range is 2.9–5 V; current and efficiency depend on input voltage, load and temperature. Its 10 A switch limit is not an output-current rating. Use a **1.25 A total 5 V cap** provisionally, including all electronics and LED idle current. This requires about **2.45 A from a 3.0 V pack at assumed 85% efficiency**, below the candidate pack's stated discharge limit. Confirm continuous operation and transients in the enclosed pendant. Do not use the regulator's undervoltage lockout as the pack's protection circuit.

**1 A can be useful for wearable light.** The current 494-pixel idle estimate and 500 mA electronics reserve consume 994 mA before encoded light, so the unmeasured model leaves only 6 mA at a 1 A cap. That is a conservative calculation, not a measured brightness result. Measure LED idle, controller average/peaks, the intended sparse animations and radio/GPS together. Reconsider a 1 A supply if those measurements support a lower bounded current model. Do not reject a useful wearable brightness level from theoretical full-white ratings alone.

The Adafruit parts reviewed below do not provide both the required energy and a suitable discharge path for this baseline. The battery and regulator are therefore exceptions to the sourcing preference. Keep Adafruit for suitable sensors, controls and charging parts.

## Compartment and wiring

The body is **250 mm diameter × 38.5 mm deep**. One pack sits at **(0,-33) mm**, with its lower face at **Z=3.5 mm** and nominal top at **Z=23.5 mm**. The cradle has an **82 × 67 mm clear pocket** and **84 × 69 mm outside footprint**. Allow 0.5 mm insulating padding below it. Two independent **10 mm hook-and-loop straps** use four retention slots. Keep **2 mm free top clearance plus 0.5 mm strap allowance**, up to Z=26. The circle underside starts at Z=27. This allowance is for normal fit; replace a swollen or damaged pouch. Do not tighten straps to restrain swelling.

The regulator sits at **(72,-28) mm** with its long dimension along Y. Rails leave both ends open. A left-side pack lead exit routes wires around the lower bay to the regulator. Restrain the leads without pulling on the pouch tabs. The removable rear carries the cradle, board rails and service hatch. Exact connectors, fuse, switch, capacitors, lead bends and restraint points remain measured-part fit work.

Use this single power path:

```text
Factory protected 1S pack
  -> keyed power connector -> fuse -> physical latching switch
  -> Pololu fixed 5 V boost -> Sparkle Motion power input / LED VOUT
  -> Sparkle 3.3 V -> BlackPill, GPS, radio and sensors

Protected/switched pack voltage before boost -> divider -> BlackPill PA4
```

Use short paired supply/return wires and connectors rated above the complete input load. Keep the main pack-to-boost path free of JST-PH adapters with a 2 A limit. Fit bulk decoupling close to the regulator and LED distribution; select values from the regulator guidance and measured startup/LED transients. A frame's calculated average current does not bound every PWM pulse or capacitor inrush. Validate cold start, black-to-bright transitions, radio TX and low-pack operation without repeated protection trips. Record oscilloscope rail minima, input/output peaks and capacitor heating. These physical checks remain deferred.

Sparkle does not charge a raw LiPo or boost it to 5 V. Feed it regulated 5 V and keep its PD selection at 5 V. Sparkle's LED VOUT follows the input. Keep external 3.3 V demand within its published 500 mA peak limit. The battery divider measures the protected/switched raw pack before the boost; both sense and logic must turn off together. Keep battery profile 0 / Unknown until the actual divider and calibrated profile are installed. [Sparkle power pins](https://learn.adafruit.com/adafruit-sparkle-motion/pinouts).

For the MVP, **disconnect and remove the pack for external charging**. An [Adafruit 259 single-cell Li-ion/LiPo charger](https://www.adafruit.com/product/259), configured for the selected 4.2 V chemistry and at most 1 A, is a charging candidate. A charge-only adapter may use its connector within that charge current; never reuse that adapter in the higher-current discharge path. Confirm the supplied charger settings and pack compatibility. Do not run the pendant through the charger's load output. An onboard charger is outside the current model. Charge off-body and outside the sealed case. Turn power off before exchanging a spare; connect one factory pack at a time. Do not parallel separate packs or regulator outputs. [Adafruit multi-pack guidance](https://learn.adafruit.com/li-ion-and-lipoly-batteries/multi-battery-packs).

## External belt-pack option

Support the same protected **1S raw-pack input** from a belt carrier. Keep the 5 V boost in the pendant. Use a fused, switched pack in a closed, padded belt carrier, then run a flexible paired cable up the necklace and down the body. The native rear has a **12 mm provisional gland bore at (43,84) mm**, a reinforced sealing land, and a blanking-plug envelope. Fit a selected gland for external use; leave the entry capped for internal use. [Adafruit PG-7 gland 762](https://www.adafruit.com/product/762) is the fit reference, with listed 11.5 mm screw end and a 3.0–4.3 mm cable-jacket range. Its full dimensions and actual cable fit remain TODOs. The belt carrier is not yet modeled.

Use a keyed disconnect and strain relief at the belt, secure the lead to the necklace independently from its load-bearing loops, and leave slack at the shoulder and pendant. The cable must not tighten around the neck or pull a board connector during a snag. Select and test the disconnect's release behavior with the actual harness. Keep the pendant's physical switch and a belt master disconnect; fuse close to the pack so the whole cable has protection. Keep the cable away from the IMU and move the battery mass and magnetic material to the belt.

Start cable sizing with flexible **18 AWG paired conductors**, then choose the jacket/gland from its actual outside diameter. A 1.5 m one-way run has about 3 m conductor length. Using nominal copper resistance of 0.021 ohm/m gives about **0.063 ohm** before connectors: **0.15 V drop and 0.38 W loss at 2.45 A**. The [Belden 5300UE specification](https://www.belden.com/products/cable/audio-cable/speaker-cable/5300ue) provides an 18 AWG resistance reference of 6.5 ohm/1000 ft; it is not the selected wearable cable. This is an engineering estimate; strand construction, temperature and connections change it. Near pack depletion the drop can put the boost below its 2.9 V operating range. Measure the loaded pendant input and exclude that unusable energy from runtime. Shorten the route or increase conductor size if needed; select a larger gland when the jacket requires it. Do not raise the raw input above 4.2 V to compensate.

High-discharge 18650 or 26650 cells are possible pack ingredients, but a cell's current rating does not rate a holder, springs, connector, cable or BMS. Record the exact cell model and use a protected factory pack, or a separately designed protected assembly before installing loose cells. Cell chemistry/capacity and a suitable charger remain part-specific. This baseline accepts **1S only**; a 2S pack requires a different regulator and battery profile. Never feed 2S voltage into the selected boost or 5 V pixels.

An external regulated 5 V supply is another valid future packaging choice, with the regulator at the belt. It requires a separately keyed 5 V harness, no connection to the raw input, and a defined battery measurement route. It is not interchangeable with the modeled 1S input. The current handoff uses one raw-pack interface to avoid that ambiguity.

Sparkle's published input path and resettable fuse are **5 A total**, and its 3.3 V pin provides **500 mA peak**. If later measured demand needs LED power injection, branch a suitable regulated 5 V supply through separately fused LED feeds and share ground with Sparkle. Keep those feeds out of its logic regulator and do not parallel independent supplies. Keep aggregate and branch current limiting over all four displays. Raw 1S cells range below 5 V; do not assume direct battery wiring meets the Fibonacci256 or strip voltage requirements. Direct raw-cell LED operation is outside this baseline. [Sparkle ratings](https://learn.adafruit.com/adafruit-sparkle-motion/pinouts).

The current CAD supports both battery locations with the same 38.5 mm body. External use removes the **190 g pack** from the pendant; the empty cradle remains. The generated [parts manifest](exports/parts.json) and [complete build parts list](../../design-v2.md#complete-build-parts-list-and-mass-estimate) give the complete pendant, necklace, belt/lead and total-worn estimates, with explicit uncertainty allowances. See the [installed mass basis](README.md#current-weight-estimate). A later rear/layout revision can remove unused walls and investigate a thinner electronics-only body. Keep that reduction unclaimed until a rebuilt model and connectors fit. Record pendant mass separately from belt-carried mass and total carried mass.

## Adafruit comparison

| Item | Published size and mass | Nominal energy | Decision |
| --- | --- | --- | --- |
| [328, flat 2500 mAh LiPo](https://www.adafruit.com/product/328) | Page: 50 × 60 × 7.3 mm, 50 g. Linked [datasheet](https://cdn-shop.adafruit.com/datasheets/785060-2500mAh_specification_sheet.pdf): maximum 50.5 × 60.5 × 7.9 mm including protection. | 9.25 Wh at 3.7 V | Too little energy for the full four-output target. Two used in sequence also fall short under the conservative idle model. |
| [258, flat 1200 mAh LiPo](https://www.adafruit.com/product/258) | 34 × 62 × 5 mm, 23 g | 4.44 Wh | Less energy again; useful for smaller projects. |
| [5035, factory 10050 mAh 18650 pack](https://www.adafruit.com/product/5035) | 66.6 × 55.3 × 18.7 mm, 148 g | About 37 Wh | Good energy and size. The pack is rated for 3 A continuous, but the supplied cable is limited to 2 A. At 3 V and 85% efficiency that permits only about 1.02 A at 5 V, before margin. Do not select it for the 1.25 A cap or modify it by bypassing its protection. |
| [1566, 10000 mAh USB bank](https://www.adafruit.com/product/1566) | 90.3 × 63 × 23 mm, 212 g | About 37 Wh only if the rating refers to 3.7 V cells | Excluded. Adafruit describes general 5 V loads and links LED projects, but gives no LED-transient/no-trip guarantee. The page also describes output interruption when charging starts/stops and possible sleep below 100 mA. This does not resolve Bryan's observed failure. |
| [2465, PowerBoost 1000C](https://www.adafruit.com/product/2465) / [4654, MiniBoost](https://www.adafruit.com/product/4654) | Small single-cell boost boards | Not batteries | Approximately 1 A-class output cannot supply the present complete-display budget with useful margin. Neither is the selected regulator. |

Raw packs still have overcurrent protection. A separate regulator removes the consumer USB bank's sleep/load-detection behavior; it does not prove flicker-free operation. Preserve the pack protection and measure the actual changing LED load.

## Four-hour energy budget

For initial sizing, use `output_Wh = nominal_cell_Wh × efficiency`. Assume 85% efficiency only until measured. The following values exclude capacity reserve, aging, temperatures, unusable energy below the regulator's operating range, and swap downtime.

| Supply | Nominal cell energy | Average output power allowed for four hours | Average total 5 V current |
| --- | --- | --- | --- |
| One Adafruit 328 | 9.25 Wh | 1.97 W | 0.393 A |
| Two 328 packs, used in sequence | 18.50 Wh | 3.93 W | 0.786 A |
| Selected 10 Ah LiPo fit candidate | 37 Wh | 7.86 W | 1.573 A energy allowance; provisional operating cap is lower |

The current unmeasured model reserves **0.5 A for controllers/services** and **0.494 A of LED idle current** for 494 pixels. It leaves **0.256 A for encoded light above idle** at the provisional 1.25 A total cap. This supports initial sparse-pattern planning; it does not establish the desired apparent brightness. Keep the conservative current model until measured replacements bound the actual current.

At 5 V × 1.25 A, four hours needs **25 Wh output**. A nominal 37 Wh pack at assumed 85% efficiency provides **31.45 Wh**, or **5.03 calculated hours** at that load before further losses and reserve. The four-hour run leaves **6.45 Wh of calculated output reserve** under those assumptions. At 1.5 A the estimate falls to 4.19 hours before reserve. At sustained 2.5 A, four hours needs 50 Wh output / 58.8 Wh cell energy, which this pack cannot provide. The protocol's 2.5 A fixture remains an illustration, not this pendant's operating setting.

Provisional commissioning settings in mA are **total/reserve/circle/halo/inner/outer = 1250/500/400/80/120/150**. The four branch caps total 750 mA and each covers its modeled idle load. Battery factors and user brightness still apply. Keep the initial drive cap and Unknown battery factor until measurements permit otherwise. Measure intended pattern mix, useful brightness, actual input watts, usable Wh, regulator/pack temperatures and low-voltage behavior before claiming four hours.

**TODO: SC-BATTERY-THRESHOLDS — Confirm the supplied protected LiPo and regulator, pack/lead/connector/protection limits, fuse/switch/decoupling, charger settings, loaded cutoff/startup behavior, PA4 divider and calibrated gain, valid measurement range, and reduction/recovery thresholds. Confirm usable output energy and four-hour brightness with the intended patterns. Physical fit, transient, thermal, charge and runtime tests remain deferred.**
