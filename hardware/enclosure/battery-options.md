# Battery fit and power options

Research date: 2026-10-11. Prefer Adafruit. These are fit candidates, not a purchase list or measured runtime result. Keep the six-hour bright-pattern target open until power measurements establish the required usable energy.

## Sourced packs

| Adafruit item | Published size and mass | Nominal energy | Fit and use |
| --- | --- | --- | --- |
| [328, flat 2500 mAh LiPo](https://www.adafruit.com/product/328) | Product page: 50 × 60 × 7.3 mm, 50 g. Linked [pack datasheet](https://cdn-shop.adafruit.com/datasheets/785060-2500mAh_specification_sheet.pdf): maximum 50.5 × 60.5 × 7.9 mm including protection. | 9.25 Wh, calculated at 3.7 V | Current CAD uses the larger envelope. Two separate pockets fit side by side. |
| [258, flat 1200 mAh LiPo](https://www.adafruit.com/product/258) | 34 × 62 × 5 mm, 23 g | 4.44 Wh | A smaller alternative needs revised pocket/padding dimensions; its 62 mm length exceeds the modeled 328 envelope. |
| [5035, factory 10050 mAh Li-ion pack](https://www.adafruit.com/product/5035) | 66.6 × 55.3 × 18.7 mm, 148 g; cylindrical cells | About 37 Wh | Too thick for this bay, including its fit and strap allowance. Factory protection included; 3 A pack discharge rating, but supplied cable limited to 2 A. Requires a suitable boost and charger. |
| [1566, complete 10000 mAh USB bank](https://www.adafruit.com/product/1566) | 90.3 × 63 × 23 mm, 212 g | About 37 Wh if capacity refers to 3.7 V cells; this is a sizing assumption, not measured usable USB energy | Too thick internally. A belt/pocket option with integrated charger and 5 V outputs, each rated 2 A. Use one output; do not parallel ports. |

The 328 product page specifies a maximum 1.2 A charge rate. Keep its original protection and connector. Its older linked datasheet and current product description differ; use the conservative fit envelope, then measure supplied packs. Do not treat a cell's C rating as a connector or complete-system current rating.

## Compartment in the model

Two 328 envelopes sit at **(-48.25,-37)** and **(8.25,-37) mm**. Each padded pocket has **52.5 × 62.5 mm** clear plan dimensions and a **54.5 × 64.5 mm** outside footprint. A 2 mm gap between pocket walls provides a lead-routing channel. Each pack has its own 10 mm hook-and-loop strap, retention slots, a top lead exit, and insulating padding. Pack lower faces sit at Z=3.5 and nominal tops at Z=11.4. Keep another **2 mm of free height plus 0.5 mm for the strap**. This allowance is for fit and clearance; a swollen or damaged pouch requires replacement, not tighter straps.

The model also reserves **23 × 45 × 10 mm** at **(60,-42) mm** for an [Adafruit PowerBoost 1000C, item 2465](https://www.adafruit.com/product/2465). Its published assembled dimensions include USB-A. The rails leave both ends open; lead bends, plug clearance, fuse and switch placement still need measured components. This board combines a single-cell charger with a 5.2 V, approximately 1 A boost. It is a **fit reference for limited bench bring-up**, not the final supply for four bright displays. Its 1 A output cannot supply the example 2.5 A budget. Charging takes place with the pendant off and opened, under supervision; do not charge it while worn or sealed in playa heat.

The two pockets are mechanical storage, not a two-cell electrical pack. **Connect only one battery to the boost at a time.** Turn power off, disconnect the first battery, cap its connector, then connect the spare. The device restarts. Charge each pack separately; no Y cable, series connection, simultaneous charging, or automatic changeover circuit. This follows [Adafruit's multi-pack guidance](https://learn.adafruit.com/li-ion-and-lipoly-batteries/multi-battery-packs). Remove the rear to exchange packs; support the assembly and keep its wiring slack restrained. The cover, board mounts and pockets form one removable printed subassembly.

Sparkle takes regulated LED-compatible power; it does not charge a raw LiPo or boost it to 5 V. Set USB PD to 5 V for these pixels. Sparkle supplies BlackPill 3.3 V. Sense the selected protected/switched battery before regulation through the specified PA4 divider. If using a complete USB bank, its regulated output does not expose battery voltage; keep battery state Unknown until a real measurement source exists. [Sparkle power pins](https://learn.adafruit.com/adafruit-sparkle-motion/pinouts).

## Six-hour budget

Use `output_Wh = nominal_cell_Wh × efficiency` only for initial sizing. The table assumes 85% conversion efficiency and no capacity reserve, aging, low-voltage loss, or downtime during swaps. Each row uses 5 V output. These are upper planning allowances, not runtime promises.

| Carried supply | Nominal cell energy | Average output power permitted for six hours | Average total 5 V current |
| --- | --- | --- | --- |
| One 328 | 9.25 Wh | 1.31 W | 0.262 A |
| Two 328, used in sequence | 18.50 Wh | 2.62 W | 0.524 A |
| One 5035 | 37.19 Wh | 5.27 W | 1.054 A |
| One 1566, assumed 37 Wh | 37 Wh | 5.24 W | 1.048 A |
| Two 1566 banks, used in sequence externally | 74 Wh | 10.48 W | 2.097 A energy allowance; each port still limited to 2 A |

The design currently reserves at least **0.5 A for controllers/services** and conservatively estimates **0.494 A of LED idle load** for 494 pixels. Thus two internal 328 packs cannot meet six hours even at black under that model. A 1 A boost leaves almost no modeled animation budget with every output attached. Do not weaken that current model to make the battery fit appear sufficient. Limited bench bring-up can connect fewer LED branches and use a matching safe current cap; it does not validate the complete pendant.

For sustained 5 V × 2.5 A, six hours needs **75 Wh output**, or **88.2 Wh cell energy** at 85% efficiency, before reserve. No listed internal candidate meets that requirement. A practical next comparison is external Adafruit USB banks used one at a time, with a total cap below one port's 2 A rating, against a larger factory pack and regulator from another source. Two nominal 37 Wh banks at a **1.5 A / 7.5 W** total cap provide a calculated 8.39 hours before reserve. This still needs measured bank capacity, operating temperature, pattern brightness, cable drop, and actual duty cycle. It also requires a sealed, strain-relieved cable route; no external battery mount or feedthrough is yet modeled.

**TODO: SC-BATTERY-THRESHOLDS — Select the final supply after measuring all-output pattern power. Resolve usable energy, pack/connector discharge limits, charger/regulator heat, physical cutoff, sense point, divider and voltage thresholds. Decide between the internal short-runtime packs, a deeper body, and an external factory supply. Preserve the six-hour target; physical measurements remain deferred.**
