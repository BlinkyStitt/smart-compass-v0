## Selected narrow build inventory

The wide design is an inactive archive. This inventory describes the narrow digital prototype.
It includes one protected XTAR21700 6000mAh button-top cell and the complete sewn necklace.
Masses use published component data, net CAD volumes, full installed wire cuts and stated engineering allowances.
Physical fit, strength, heat, electrical recovery and worn mass remain unmeasured.

Body: 200mm diameter x 60.6mm depth. Fitted assembly pose: 200 x 204.004 x 80.6mm (width x height x depth). The free neck span has no rigid envelope.
[Raw census, accounting owners and bounds](parts.json) · [Service and print package](prototype-service.zip).

| Ring material | Pendant nominal g | Necklace nominal g | Total worn nominal g | Worn low–high g | Margin to2.5lb g | Separate50g target |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| glow | 892.745 | 4.611 | 897.356 | 669.662–1129.838 | 4.143 | not met |
| silver | 885.727 | 4.611 | 890.338 | 664.749–1122.258 | 11.723 | not met |

The raw limit is1133.980925g. Raw arithmetic determines acceptance; display rounding does not.
Low/high allowances are added independently. They are not confidence intervals or guaranteed physical assembly bounds.
Exclude charger, carried spares, retail stock, trim waste, brims and disposable fit samples.

| Installed item | Quantity | Nominal g per unit | Low–high g per unit | Basis |
| --- | ---: | ---: | ---: | --- |
| 166mm Fibonacci256 v0.1 board and256LEDs | 1 | 82 | 65–105 | Existing component-inventory.json#circle allowance |
| Adafruit6100 SparkleMotion RevD, jack removed | 1 | 18 | 12–25 | Existing component-inventory.json#sparkle allowance; removed jack mass not subtracted |
| WeAct BlackPill V3.1, no P1/P2/P3/U3 | 1 | 7 | 4–10 | Existing component-inventory.json#blackpill allowance; no subtraction for removed parts |
| Adafruit3133 Ultimate GPS FeatherWing | 1 | 8.8 | 8–10 | Existing component-inventory.json#gps allowance |
| Adafruit3387 LSM9DS1 | 1 | 2.5 | 2–4 | Existing component-inventory.json#imu allowance |
| Adafruit3072 RFM95W breakout, no connectors | 1 | 3.1 | 2.8–4.5 | Existing component-inventory.json#radio allowance |
| Adafruit2030 PowerBoost1000Basic, no JST/USB-A/R20 | 1 | 5 | 3.2–8 | Engineering allowance for selected replacement board; supplied mass unmeasured |
| Pololu2808 psw03a | 1 | 2 | 1–6 | Engineering allowance; supplied mass unmeasured |
| One protected XTAR21700 6000mAh button-top | 1 | 73 | 65–76 | XTAR manufacturer net weight <=76g; lower/nominal estimates, not measurements |
| Selected1000uF output capacitor | 1 | 2 | 1–4 | Existing component-inventory.json#bulk_cap allowance; source includes full leads |
| C&K7201SYZQE DPDT | 1 | 8 | 4–15 | Engineering allowance for selected replacement switch, nut/lockwasher included |
| Selected78mm insulated radio wire antenna | 1 | 0.25 | 0.15–0.6 | Existing component-inventory.json#rf_antenna allowance |
| Mill-Max0854 wire-mount contact positive | 1 | 1.5 | 0.5–3 | Engineering allowance; supplied contact mass unmeasured |
| Mill-Max0854 wire-mount contact negative | 1 | 1.5 | 0.5–3 | Engineering allowance; supplied contact mass unmeasured |
| CamdenBoss CTBP2054/4 | 1 | 1.5 | 0.5–3 | Engineering allowance per complete four-position block |
| CamdenBoss CTBP2054/4 | 1 | 1.5 | 0.5–3 | Engineering allowance per complete four-position block |
| Pololu2444 two-pin3.5mm side-entry screw terminal block | 1 | 1.5 | 0.5–3 | Engineering allowance per complete clamp block |
| Pololu2444 two-pin3.5mm side-entry screw terminal block | 1 | 1.5 | 0.5–3 | Engineering allowance per complete clamp block |
| C&K PTS645SL70-2 | 1 | 1 | 0.5–3 | Existing component-inventory.json#buttons allowance per fitted switch |
| C&K PTS645SL70-2 | 1 | 1 | 0.5–3 | Existing component-inventory.json#buttons allowance per fitted switch |
| C&K PTS645SL70-2 | 1 | 1 | 0.5–3 | Existing component-inventory.json#buttons allowance per fitted switch |
| ActionBackplate | 1 | 0.358919 | 0.251243–0.387633 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| ActionBezel | 1 | 0.30666 | 0.214662–0.331193 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| ActionCompression0 | 1 | 0.050559 | 0.0353913–0.0546038 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| ActionCompression1 | 1 | 0.050559 | 0.0353913–0.0546038 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| ActionMountNut0 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| ActionMountNut1 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| SSCF-M2-8-TI5; finished under-head target 7.95mm | 1 | 0.210648 | 0.136921–0.315972 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-8-datasheet.pdf |
| SSCF-M2-8-TI5; finished under-head target 7.95mm | 1 | 0.210648 | 0.136921–0.315972 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-8-datasheet.pdf |
| ActionMountWasher0 | 1 | 0.04378 | 0.028457–0.06567 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| ActionMountWasher1 | 1 | 0.04378 | 0.028457–0.06567 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| GuardMountNut0 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| GuardMountNut1 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| SSCF-M2-8-TI5; finished under-head target 7.2mm | 1 | 0.200234 | 0.130152–0.300351 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-8-datasheet.pdf |
| SSCF-M2-8-TI5; finished under-head target 7.2mm | 1 | 0.200234 | 0.130152–0.300351 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-8-datasheet.pdf |
| GuardMountWasher0 | 1 | 0.04378 | 0.028457–0.06567 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| GuardMountWasher1 | 1 | 0.04378 | 0.028457–0.06567 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| ModeBackplate | 1 | 0.358919 | 0.251243–0.387633 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| ModeBezel | 1 | 0.30666 | 0.214662–0.331193 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| ModeCompression0 | 1 | 0.050559 | 0.0353913–0.0546038 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| ModeCompression1 | 1 | 0.050559 | 0.0353913–0.0546038 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| ModeMountNut0 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| ModeMountNut1 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| SSCF-M2-8-TI5; finished under-head target 7.95mm | 1 | 0.210648 | 0.136921–0.315972 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-8-datasheet.pdf |
| SSCF-M2-8-TI5; finished under-head target 7.95mm | 1 | 0.210648 | 0.136921–0.315972 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-8-datasheet.pdf |
| ModeMountWasher0 | 1 | 0.04378 | 0.028457–0.06567 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| ModeMountWasher1 | 1 | 0.04378 | 0.028457–0.06567 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| StartBackplate | 1 | 0.358919 | 0.251243–0.387633 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| StartBezel | 1 | 0.30666 | 0.214662–0.331193 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| StartCompression0 | 1 | 0.050559 | 0.0353913–0.0546038 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| StartCompression1 | 1 | 0.050559 | 0.0353913–0.0546038 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| StartMountNut0 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| StartMountNut1 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| SSCF-M2-8-TI5; finished under-head target 7.95mm | 1 | 0.210648 | 0.136921–0.315972 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-8-datasheet.pdf |
| SSCF-M2-8-TI5; finished under-head target 7.95mm | 1 | 0.210648 | 0.136921–0.315972 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-8-datasheet.pdf |
| StartMountWasher0 | 1 | 0.04378 | 0.028457–0.06567 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| StartMountWasher1 | 1 | 0.04378 | 0.028457–0.06567 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| SwitchGuard | 1 | 3.36448 | 2.35514–3.63364 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| BatteryCaseMountNut0 | 1 | 0.344215 | 0.22374–0.516322 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BatteryCaseMountNut1 | 1 | 0.344215 | 0.22374–0.516322 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BatteryCaseMountNut2 | 1 | 0.344215 | 0.22374–0.516322 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BatteryCaseMountNut3 | 1 | 0.344215 | 0.22374–0.516322 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| ZS755M3X10; finished under-head target 10.0mm | 1 | 0.627466 | 0.407853–0.9412 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/ampg.pdf |
| ZS755M3X10; finished under-head target 10.0mm | 1 | 0.627466 | 0.407853–0.9412 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/ampg.pdf |
| ZS755M3X10; finished under-head target 10.0mm | 1 | 0.627466 | 0.407853–0.9412 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/ampg.pdf |
| ZS755M3X10; finished under-head target 10.0mm | 1 | 0.627466 | 0.407853–0.9412 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/ampg.pdf |
| BatteryCaseMountWasher0 | 1 | 0.132271 | 0.0859759–0.198406 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BatteryCaseMountWasher1 | 1 | 0.132271 | 0.0859759–0.198406 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BatteryCaseMountWasher2 | 1 | 0.132271 | 0.0859759–0.198406 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BatteryCaseMountWasher3 | 1 | 0.132271 | 0.0859759–0.198406 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BatteryContactNBack | 1 | 1.44707 | 1.01295–1.56283 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| BatteryContactNFront | 1 | 1.64371 | 1.1506–1.77521 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| BatteryContactNNut0 | 1 | 0.131365 | 0.0853872–0.197047 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BatteryContactNNut1 | 1 | 0.131365 | 0.0853872–0.197047 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| SSCF-M2-16-TI5; finished under-head target 13.0mm | 1 | 0.280772 | 0.182502–0.421158 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-16-datasheet.pdf |
| SSCF-M2-16-TI5; finished under-head target 13.0mm | 1 | 0.280772 | 0.182502–0.421158 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-16-datasheet.pdf |
| BatteryContactNShim0 | 1 | 0.00831265 | 0.00581886–0.012469 | Selected polyester shim; nominal CAD volume x1.4g/cm3 with engineering70..150% allowance |
| BatteryContactNShim1 | 1 | 0.00831265 | 0.00581886–0.012469 | Selected polyester shim; nominal CAD volume x1.4g/cm3 with engineering70..150% allowance |
| BatteryContactNSpacer0 | 1 | 0.0720716 | 0.0504501–0.0778373 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| BatteryContactNSpacer1 | 1 | 0.0720716 | 0.0504501–0.0778373 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| BatteryContactNWasher0 | 1 | 0.04378 | 0.028457–0.06567 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BatteryContactNWasher1 | 1 | 0.04378 | 0.028457–0.06567 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BatteryContactPBack | 1 | 1.44707 | 1.01295–1.56283 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| BatteryContactPFront | 1 | 1.44707 | 1.01295–1.56283 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| BatteryContactPNut0 | 1 | 0.131365 | 0.0853872–0.197047 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BatteryContactPNut1 | 1 | 0.131365 | 0.0853872–0.197047 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| SSCF-M2-16-TI5; finished under-head target 13.0mm | 1 | 0.280772 | 0.182502–0.421158 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-16-datasheet.pdf |
| SSCF-M2-16-TI5; finished under-head target 13.0mm | 1 | 0.280772 | 0.182502–0.421158 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-16-datasheet.pdf |
| BatteryContactPShim0 | 1 | 0.00831265 | 0.00581886–0.012469 | Selected polyester shim; nominal CAD volume x1.4g/cm3 with engineering70..150% allowance |
| BatteryContactPShim1 | 1 | 0.00831265 | 0.00581886–0.012469 | Selected polyester shim; nominal CAD volume x1.4g/cm3 with engineering70..150% allowance |
| BatteryContactPSpacer0 | 1 | 0.0720716 | 0.0504501–0.0778373 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| BatteryContactPSpacer1 | 1 | 0.0720716 | 0.0504501–0.0778373 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| BatteryContactPWasher0 | 1 | 0.04378 | 0.028457–0.06567 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BatteryContactPWasher1 | 1 | 0.04378 | 0.028457–0.06567 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BatteryCradle | 1 | 31.2314 | 21.862–33.73 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| BatteryDoor | 1 | 10.4847 | 7.33931–11.3235 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| BatteryHingeNut | 1 | 0.344215 | 0.22374–0.516322 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BatteryHingePin | 1 | 5.97973 | 3.88682–8.96959 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BatteryHingeSpacer0 | 1 | 0.141838 | 0.0992867–0.153185 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| BatteryHingeSpacer1 | 1 | 0.0269313 | 0.0188519–0.0290858 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| BatteryHingeWasher0 | 1 | 0.132271 | 0.0859759–0.198406 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BatteryHingeWasher1 | 1 | 0.132271 | 0.0859759–0.198406 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BatteryKeeper | 1 | 0.402528 | 0.28177–0.434731 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| BatteryKeeperNut0 | 1 | 0.344215 | 0.22374–0.516322 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BatteryKeeperNut1 | 1 | 0.344215 | 0.22374–0.516322 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BatteryKeeperScrew | 1 | 1.00272 | 0.65177–1.50409 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| Selected LC134 tie BatteryMainFuseLacing0 | 1 | 0.047607 | 0.0333249–0.0714105 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie BatteryMainFuseLacing1 | 1 | 0.047607 | 0.0333249–0.0714105 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| ZS755M3X6; finished under-head target 6.0mm | 1 | 0.502494 | 0.326621–0.753741 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/ampg.pdf |
| RearWasher0 | 1 | 0.132271 | 0.0859759–0.198406 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| RearNut0 | 1 | 0.36268 | 0.235742–0.54402 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| ZS755M3X6; finished under-head target 6.0mm | 1 | 0.502494 | 0.326621–0.753741 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/ampg.pdf |
| RearWasher1 | 1 | 0.132271 | 0.0859759–0.198406 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| RearNut1 | 1 | 0.36268 | 0.235742–0.54402 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| ZS755M3X6; finished under-head target 6.0mm | 1 | 0.502494 | 0.326621–0.753741 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/ampg.pdf |
| RearWasher2 | 1 | 0.132271 | 0.0859759–0.198406 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| RearNut2 | 1 | 0.36268 | 0.235742–0.54402 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| ZS755M3X6; finished under-head target 6.0mm | 1 | 0.502494 | 0.326621–0.753741 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/ampg.pdf |
| RearWasher3 | 1 | 0.132271 | 0.0859759–0.198406 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| RearNut3 | 1 | 0.36268 | 0.235742–0.54402 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| ZS755M3X6; finished under-head target 6.0mm | 1 | 0.502494 | 0.326621–0.753741 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/ampg.pdf |
| RearWasher4 | 1 | 0.132271 | 0.0859759–0.198406 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| RearNut4 | 1 | 0.36268 | 0.235742–0.54402 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| ZS755M3X6; finished under-head target 6.0mm | 1 | 0.502494 | 0.326621–0.753741 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/ampg.pdf |
| RearWasher5 | 1 | 0.132271 | 0.0859759–0.198406 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| RearNut5 | 1 | 0.36268 | 0.235742–0.54402 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| RearCover | 1 | 50.1394 | 35.0976–54.1506 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| ElectronicsShell | 1 | 117.306 | 82.1143–126.691 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| BoardEdgeClip0 | 1 | 0.0490708 | 0.0343495–0.0529964 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| BoardClipWasher0 | 1 | 0.04378 | 0.028457–0.06567 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| SSCF-M2-8-TI5; finished under-head target 8.0mm | 1 | 0.211342 | 0.137373–0.317014 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-8-datasheet.pdf |
| BoardClipNut0 | 1 | 0.135435 | 0.0880329–0.203153 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BoardEdgeClip1 | 1 | 0.0490708 | 0.0343495–0.0529964 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| BoardClipWasher1 | 1 | 0.04378 | 0.028457–0.06567 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| SSCF-M2-8-TI5; finished under-head target 8.0mm | 1 | 0.211342 | 0.137373–0.317014 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-8-datasheet.pdf |
| BoardClipNut1 | 1 | 0.135435 | 0.0880329–0.203153 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BoardEdgeClip2 | 1 | 0.0490708 | 0.0343495–0.0529964 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| BoardClipWasher2 | 1 | 0.04378 | 0.028457–0.06567 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| SSCF-M2-8-TI5; finished under-head target 8.0mm | 1 | 0.211342 | 0.137373–0.317014 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-8-datasheet.pdf |
| BoardClipNut2 | 1 | 0.135435 | 0.0880329–0.203153 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| FrontBezel | 1 | 11.0466 | 7.73259–11.9303 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| FrontNut0 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| FrontBolt0 | 1 | 0.175045 | 0.11378–0.262568 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| FrontNut1 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| FrontBolt1 | 1 | 0.175045 | 0.11378–0.262568 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| FrontNut2 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| FrontBolt2 | 1 | 0.175045 | 0.11378–0.262568 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| FrontNut3 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| FrontBolt3 | 1 | 0.175045 | 0.11378–0.262568 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| FrontNut4 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| FrontBolt4 | 1 | 0.175045 | 0.11378–0.262568 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| FrontNut5 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| FrontBolt5 | 1 | 0.175045 | 0.11378–0.262568 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| SideDiffuser | 1 | 37.3221 | 26.1255–40.3079 | CAD net solid volume x1.5g/cm3; existing material allowances; actual part mass unmeasured |
| InnerDiffuser | 1 | 12.8068 | 8.96477–13.8314 | CAD net solid volume x1.5g/cm3; existing material allowances; actual part mass unmeasured |
| EGLStencil | 1 | 8.18447 | 5.72913–8.83923 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| RearCouplingMirror | 1 | 98.0486 | 88.2437–107.853 | CAD net solid volume x1.19g/cm3; existing material allowances; actual part mass unmeasured |
| FrontMirror | 1 | 98.0486 | 88.2437–107.853 | CAD net solid volume x1.19g/cm3; existing material allowances; actual part mass unmeasured |
| LatchCarrier | 1 | 2.97761 | 2.08433–3.21582 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| LatchClamp0 | 1 | 0.045471 | 0.0318297–0.0491086 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| LatchClamp1 | 1 | 0.045471 | 0.0318297–0.0491086 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| LatchClamp2 | 1 | 0.045471 | 0.0318297–0.0491086 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| LatchClamp3 | 1 | 0.045471 | 0.0318297–0.0491086 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| LatchMountLowerWasher0 | 1 | 0.04378 | 0.028457–0.06567 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| LatchMountLowerWasher1 | 1 | 0.04378 | 0.028457–0.06567 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| LatchMountLowerWasher2 | 1 | 0.04378 | 0.028457–0.06567 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| LatchMountLowerWasher3 | 1 | 0.04378 | 0.028457–0.06567 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| LatchMountNut0 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| LatchMountNut1 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| LatchMountNut2 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| LatchMountNut3 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| SSC-M2-20-TI5; finished under-head target 17.0mm | 1 | 0.336315 | 0.218605–0.504473 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-20-datasheet.pdf |
| SSC-M2-20-TI5; finished under-head target 17.0mm | 1 | 0.336315 | 0.218605–0.504473 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-20-datasheet.pdf |
| SSC-M2-20-TI5; finished under-head target 17.0mm | 1 | 0.336315 | 0.218605–0.504473 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-20-datasheet.pdf |
| SSC-M2-20-TI5; finished under-head target 17.0mm | 1 | 0.336315 | 0.218605–0.504473 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-20-datasheet.pdf |
| LatchMountUpperWasher0 | 1 | 0.04378 | 0.028457–0.06567 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| LatchMountUpperWasher1 | 1 | 0.04378 | 0.028457–0.06567 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| LatchMountUpperWasher2 | 1 | 0.04378 | 0.028457–0.06567 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| LatchMountUpperWasher3 | 1 | 0.04378 | 0.028457–0.06567 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| IMUNut0 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| IMUNut1 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| IMUNut2 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| IMUNut3 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| SSCF-M2-8-TI5; finished under-head target 6.8mm | 1 | 0.194679 | 0.126542–0.292019 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-8-datasheet.pdf |
| SSCF-M2-8-TI5; finished under-head target 6.8mm | 1 | 0.194679 | 0.126542–0.292019 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-8-datasheet.pdf |
| SSCF-M2-8-TI5; finished under-head target 6.8mm | 1 | 0.194679 | 0.126542–0.292019 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-8-datasheet.pdf |
| SSCF-M2-8-TI5; finished under-head target 6.8mm | 1 | 0.194679 | 0.126542–0.292019 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-8-datasheet.pdf |
| BoostNut0 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BoostNut1 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| SSCF-M2-8-TI5; finished under-head target 6.8mm | 1 | 0.194679 | 0.126542–0.292019 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-8-datasheet.pdf |
| SSCF-M2-8-TI5; finished under-head target 6.8mm | 1 | 0.194679 | 0.126542–0.292019 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-8-datasheet.pdf |
| CapacitorCover | 1 | 1.50448 | 1.05314–1.62484 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| CapacitorLowerShim | 1 | 0.0354607 | 0.0248225–0.0531911 | Selected polyester shim; nominal CAD volume x1.4g/cm3 with engineering70..150% allowance |
| CapacitorNut0 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| CapacitorNut1 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| SSCF-M2-8-TI5; finished under-head target 7.6mm | 1 | 0.205788 | 0.133762–0.308682 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-8-datasheet.pdf |
| SSCF-M2-8-TI5; finished under-head target 7.6mm | 1 | 0.205788 | 0.133762–0.308682 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-8-datasheet.pdf |
| CapacitorUpperShim | 1 | 0.0354607 | 0.0248225–0.0531911 | Selected polyester shim; nominal CAD volume x1.4g/cm3 with engineering70..150% allowance |
| GPSNut0 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| GPSNut1 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| GPSNut2 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| GPSNut3 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| SSCF-M2-8-TI5; finished under-head target 6.8mm | 1 | 0.194679 | 0.126542–0.292019 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-8-datasheet.pdf |
| SSCF-M2-8-TI5; finished under-head target 6.8mm | 1 | 0.194679 | 0.126542–0.292019 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-8-datasheet.pdf |
| SSCF-M2-8-TI5; finished under-head target 6.8mm | 1 | 0.194679 | 0.126542–0.292019 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-8-datasheet.pdf |
| SSCF-M2-8-TI5; finished under-head target 6.8mm | 1 | 0.194679 | 0.126542–0.292019 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-8-datasheet.pdf |
| SparkleNut0 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| SparkleNut1 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| SparkleNut2 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| SparkleNut3 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| SSCF-M2-8-TI5; finished under-head target 6.8mm | 1 | 0.194679 | 0.126542–0.292019 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-8-datasheet.pdf |
| SSCF-M2-8-TI5; finished under-head target 6.8mm | 1 | 0.194679 | 0.126542–0.292019 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-8-datasheet.pdf |
| SSCF-M2-8-TI5; finished under-head target 6.8mm | 1 | 0.194679 | 0.126542–0.292019 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-8-datasheet.pdf |
| SSCF-M2-8-TI5; finished under-head target 6.8mm | 1 | 0.194679 | 0.126542–0.292019 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-8-datasheet.pdf |
| BlackPillCarrier | 1 | 2.5378 | 1.77646–2.74082 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| BlackPillDrainBridge | 1 | 1.89654 | 1.32758–2.04826 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| Selected LC134 tie BlackPillDrainLacing0 | 1 | 0.045227 | 0.0316589–0.0678405 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie BlackPillDrainLacing1 | 1 | 0.045227 | 0.0316589–0.0678405 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie BlackPillDrainLacing10 | 1 | 0.045227 | 0.0316589–0.0678405 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie BlackPillDrainLacing11 | 1 | 0.045227 | 0.0316589–0.0678405 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie BlackPillDrainLacing2 | 1 | 0.045227 | 0.0316589–0.0678405 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie BlackPillDrainLacing3 | 1 | 0.045227 | 0.0316589–0.0678405 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie BlackPillDrainLacing4 | 1 | 0.045227 | 0.0316589–0.0678405 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie BlackPillDrainLacing5 | 1 | 0.045227 | 0.0316589–0.0678405 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie BlackPillDrainLacing6 | 1 | 0.045227 | 0.0316589–0.0678405 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie BlackPillDrainLacing7 | 1 | 0.045227 | 0.0316589–0.0678405 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie BlackPillDrainLacing8 | 1 | 0.045227 | 0.0316589–0.0678405 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie BlackPillDrainLacing9 | 1 | 0.045227 | 0.0316589–0.0678405 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| BlackPillNut0 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BlackPillNut1 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BlackPillNut2 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BlackPillNut3 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BlackPillRetainer0 | 1 | 0.112503 | 0.0787523–0.121503 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| BlackPillRetainer1 | 1 | 0.112503 | 0.0787523–0.121503 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| BlackPillRetainer2 | 1 | 0.112503 | 0.0787523–0.121503 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| BlackPillRetainer3 | 1 | 0.112503 | 0.0787523–0.121503 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| SSCF-M2-16-TI5; finished under-head target 10.75mm | 1 | 0.249529 | 0.162194–0.374293 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-16-datasheet.pdf |
| SSCF-M2-16-TI5; finished under-head target 10.75mm | 1 | 0.249529 | 0.162194–0.374293 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-16-datasheet.pdf |
| BlackPillScrew2 | 1 | 0.717753 | 0.46654–1.07663 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BlackPillScrew3 | 1 | 0.717753 | 0.46654–1.07663 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BlackPillSenseBridge | 1 | 1.41816 | 0.992714–1.53162 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| Selected LC134 tie BlackPillSenseLacing0 | 1 | 0.045227 | 0.0316589–0.0678405 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie BlackPillSenseLacing1 | 1 | 0.045227 | 0.0316589–0.0678405 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie BlackPillSenseLacing2 | 1 | 0.045227 | 0.0316589–0.0678405 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie BlackPillSenseLacing3 | 1 | 0.045227 | 0.0316589–0.0678405 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie BlackPillSenseLacing4 | 1 | 0.0448224 | 0.0313757–0.0672336 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie BlackPillSenseLacing5 | 1 | 0.045227 | 0.0316589–0.0678405 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie BlackPillSenseLacing6 | 1 | 0.045227 | 0.0316589–0.0678405 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| RadioCarrier | 1 | 4.41936 | 3.09355–4.7729 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| RadioNut0 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| RadioNut1 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| RadioNut2 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| RadioRetainer0 | 1 | 0.109829 | 0.07688–0.118615 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| RadioRetainer1 | 1 | 0.109829 | 0.07688–0.118615 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| RadioRetainer2 | 1 | 0.109829 | 0.07688–0.118615 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| SSCF-M2-16-TI5; finished under-head target 10.75mm | 1 | 0.249529 | 0.162194–0.374293 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-16-datasheet.pdf |
| SSCF-M2-16-TI5; finished under-head target 10.75mm | 1 | 0.249529 | 0.162194–0.374293 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-16-datasheet.pdf |
| SSCF-M2-16-TI5; finished under-head target 10.75mm | 1 | 0.249529 | 0.162194–0.374293 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-16-datasheet.pdf |
| BranchFuseCarrier | 1 | 2.52639 | 1.76848–2.72851 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| Selected LC134 tie BranchFuseLacing0 | 1 | 0.052129 | 0.0364903–0.0781935 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie BranchFuseLacing1 | 1 | 0.052129 | 0.0364903–0.0781935 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie BranchFuseLacing2 | 1 | 0.052129 | 0.0364903–0.0781935 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie BranchFuseLacing3 | 1 | 0.052129 | 0.0364903–0.0781935 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie BranchFuseLacing4 | 1 | 0.052129 | 0.0364903–0.0781935 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie BranchFuseLacing5 | 1 | 0.052129 | 0.0364903–0.0781935 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie BranchFuseLacing6 | 1 | 0.052129 | 0.0364903–0.0781935 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie BranchFuseLacing7 | 1 | 0.052129 | 0.0364903–0.0781935 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie BranchFuseLacing8 | 1 | 0.052129 | 0.0364903–0.0781935 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie BranchFuseLacing9 | 1 | 0.052129 | 0.0364903–0.0781935 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| BranchFuseMountNut0 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BranchFuseMountNut1 | 1 | 0.127096 | 0.0826125–0.190644 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| SSC-M2-20-TI5; finished under-head target 17.7mm | 1 | 0.346035 | 0.224923–0.519053 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-20-datasheet.pdf |
| SSC-M2-20-TI5; finished under-head target 17.7mm | 1 | 0.346035 | 0.224923–0.519053 | Actual nominal solid CAD envelopes x nominal material density; retained65..150% engineering hardware allowance. Published typical density and catalogue piece weights are not guaranteed supplied mass bounds. Full worn mass remains unmeasured.; source: designs/stacked/sources/fasteners/accu-m2-20-datasheet.pdf |
| BranchFuseMountWasher0 | 1 | 0.04378 | 0.028457–0.06567 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BranchFuseMountWasher1 | 1 | 0.04378 | 0.028457–0.06567 | Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured |
| BoostInputRelief | 1 | 0.25287 | 0.177009–0.273099 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| 3M VHB5952 fitted pad | 1 | 0.0458697 | 0.0321088–0.0688046 | 3M typical590kg/m3 x CAD fitted pad volume; engineering70..150% allowance, not a supplier bound |
| Selected LC134 tie BoostInputLacing | 1 | 0.052962 | 0.0370734–0.079443 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie HarnessSpliceTieB0 | 1 | 0.059829 | 0.0418803–0.0897435 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie HarnessSpliceTieB1 | 1 | 0.059829 | 0.0418803–0.0897435 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| HarnessSpliceCarrierB | 1 | 0.281109 | 0.196777–0.303598 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| 3M VHB5952 fitted pad | 1 | 0.020532 | 0.0143724–0.030798 | 3M typical590kg/m3 x CAD fitted pad volume; engineering70..150% allowance, not a supplier bound |
| Selected LC134 tie HarnessSpliceTieBOOST_OUT0 | 1 | 0.059829 | 0.0418803–0.0897435 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie HarnessSpliceTieBOOST_OUT1 | 1 | 0.059829 | 0.0418803–0.0897435 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| HarnessSpliceCarrierBOOST_OUT | 1 | 0.298254 | 0.208778–0.322115 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| 3M VHB5952 fitted pad | 1 | 0.020532 | 0.0143724–0.030798 | 3M typical590kg/m3 x CAD fitted pad volume; engineering70..150% allowance, not a supplier bound |
| Selected LC134 tie HarnessSpliceTieLOAD_5V0 | 1 | 0.059829 | 0.0418803–0.0897435 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie HarnessSpliceTieLOAD_5V1 | 1 | 0.059829 | 0.0418803–0.0897435 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| HarnessSpliceCarrierLOAD_5V | 1 | 0.298254 | 0.208778–0.322115 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| 3M VHB5952 fitted pad | 1 | 0.020532 | 0.0143724–0.030798 | 3M typical590kg/m3 x CAD fitted pad volume; engineering70..150% allowance, not a supplier bound |
| Selected LC134 tie HarnessSpliceTieLATCH_OFF0 | 1 | 0.055069 | 0.0385483–0.0826035 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie HarnessSpliceTieLATCH_OFF1 | 1 | 0.055069 | 0.0385483–0.0826035 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| HarnessSpliceCarrierLATCH_OFF | 1 | 0.246819 | 0.172774–0.266565 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| 3M VHB5952 fitted pad | 1 | 0.020532 | 0.0143724–0.030798 | 3M typical590kg/m3 x CAD fitted pad volume; engineering70..150% allowance, not a supplier bound |
| Selected LC134 tie HarnessSpliceTieSENSE0 | 1 | 0.055069 | 0.0385483–0.0826035 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie HarnessSpliceTieSENSE1 | 1 | 0.055069 | 0.0385483–0.0826035 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| HarnessSpliceCarrierSENSE | 1 | 0.246819 | 0.172774–0.266565 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| 3M VHB5952 fitted pad | 1 | 0.020532 | 0.0143724–0.030798 | 3M typical590kg/m3 x CAD fitted pad volume; engineering70..150% allowance, not a supplier bound |
| Selected LC134 tie HarnessSpliceTieLED_DISTRIBUTION0 | 1 | 0.059829 | 0.0418803–0.0897435 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie HarnessSpliceTieLED_DISTRIBUTION1 | 1 | 0.059829 | 0.0418803–0.0897435 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| HarnessSpliceCarrierLED_DISTRIBUTION | 1 | 0.366834 | 0.256784–0.396181 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| 3M VHB5952 fitted pad | 1 | 0.027612 | 0.0193284–0.041418 | 3M typical590kg/m3 x CAD fitted pad volume; engineering70..150% allowance, not a supplier bound |
| Selected LC134 tie HarnessSpliceTieFIB_5V0 | 1 | 0.059829 | 0.0418803–0.0897435 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie HarnessSpliceTieFIB_5V1 | 1 | 0.059829 | 0.0418803–0.0897435 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| HarnessSpliceCarrierFIB_5V | 1 | 0.298254 | 0.208778–0.322115 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| 3M VHB5952 fitted pad | 1 | 0.020532 | 0.0143724–0.030798 | 3M typical590kg/m3 x CAD fitted pad volume; engineering70..150% allowance, not a supplier bound |
| Selected LC134 tie HarnessSpliceTieAUX_3V30 | 1 | 0.059829 | 0.0418803–0.0897435 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie HarnessSpliceTieAUX_3V31 | 1 | 0.059829 | 0.0418803–0.0897435 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| HarnessSpliceCarrierAUX_3V3 | 1 | 0.366834 | 0.256784–0.396181 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| 3M VHB5952 fitted pad | 1 | 0.027612 | 0.0193284–0.041418 | 3M typical590kg/m3 x CAD fitted pad volume; engineering70..150% allowance, not a supplier bound |
| Selected LC134 tie HarnessSpliceTieGND0 | 1 | 0.064589 | 0.0452123–0.0968835 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie HarnessSpliceTieGND1 | 1 | 0.064589 | 0.0452123–0.0968835 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| HarnessSpliceCarrierGND | 1 | 0.535198 | 0.374639–0.578014 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| 3M VHB5952 fitted pad | 1 | 0.055932 | 0.0391524–0.083898 | 3M typical590kg/m3 x CAD fitted pad volume; engineering70..150% allowance, not a supplier bound |
| Selected LC134 tie HarnessSpliceTieSPI_CLOCK0 | 1 | 0.055069 | 0.0385483–0.0826035 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie HarnessSpliceTieSPI_CLOCK1 | 1 | 0.055069 | 0.0385483–0.0826035 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| HarnessSpliceCarrierSPI_CLOCK | 1 | 0.246819 | 0.172774–0.266565 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| 3M VHB5952 fitted pad | 1 | 0.020532 | 0.0143724–0.030798 | 3M typical590kg/m3 x CAD fitted pad volume; engineering70..150% allowance, not a supplier bound |
| Selected LC134 tie HarnessSpliceTieSPI_MOSI0 | 1 | 0.055069 | 0.0385483–0.0826035 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie HarnessSpliceTieSPI_MOSI1 | 1 | 0.055069 | 0.0385483–0.0826035 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| HarnessSpliceCarrierSPI_MOSI | 1 | 0.246819 | 0.172774–0.266565 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| 3M VHB5952 fitted pad | 1 | 0.020532 | 0.0143724–0.030798 | 3M typical590kg/m3 x CAD fitted pad volume; engineering70..150% allowance, not a supplier bound |
| Selected LC134 tie HarnessSpliceTieSPI_MISO0 | 1 | 0.055069 | 0.0385483–0.0826035 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie HarnessSpliceTieSPI_MISO1 | 1 | 0.055069 | 0.0385483–0.0826035 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| HarnessSpliceCarrierSPI_MISO | 1 | 0.246819 | 0.172774–0.266565 | CAD net solid volume x1.27g/cm3; existing material allowances; actual part mass unmeasured |
| 3M VHB5952 fitted pad | 1 | 0.020532 | 0.0143724–0.030798 | 3M typical590kg/m3 x CAD fitted pad volume; engineering70..150% allowance, not a supplier bound |
| Selected LC134 tie RingSideLacing12 | 1 | 0.0684565 | 0.0479195–0.102685 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie RingSideLacing24 | 1 | 0.0684565 | 0.0479196–0.102685 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie RingInnerLacing10 | 1 | 0.0521572 | 0.03651–0.0782358 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| Selected LC134 tie RingInnerLacing42 | 1 | 0.0521572 | 0.03651–0.0782358 | Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added |
| BatteryMainFuse | 1 | 4 | 2–8 | Existing main-fuse allowance or explicit engineering passive allowance; full leads included |
| BranchFuseF_AUX | 1 | 0.7 | 0.3–2 | Existing main-fuse allowance or explicit engineering passive allowance; full leads included |
| BranchFuseF_FIB | 1 | 0.7 | 0.3–2 | Existing main-fuse allowance or explicit engineering passive allowance; full leads included |
| BranchFuseF_RING1 | 1 | 0.7 | 0.3–2 | Existing main-fuse allowance or explicit engineering passive allowance; full leads included |
| BranchFuseF_RING2 | 1 | 0.7 | 0.3–2 | Existing main-fuse allowance or explicit engineering passive allowance; full leads included |
| BranchFuseF_RING3 | 1 | 0.7 | 0.3–2 | Existing main-fuse allowance or explicit engineering passive allowance; full leads included |
| BlackPillDrainR_A | 1 | 0.12 | 0.05–0.4 | Existing main-fuse allowance or explicit engineering passive allowance; full leads included |
| BlackPillDrainR_B | 1 | 0.12 | 0.05–0.4 | Existing main-fuse allowance or explicit engineering passive allowance; full leads included |
| BlackPillDrainR_BOOST | 1 | 0.12 | 0.05–0.4 | Existing main-fuse allowance or explicit engineering passive allowance; full leads included |
| BlackPillDrainR_LOAD | 1 | 0.12 | 0.05–0.4 | Existing main-fuse allowance or explicit engineering passive allowance; full leads included |
| BlackPillDrainR_OFF | 1 | 0.12 | 0.05–0.4 | Existing main-fuse allowance or explicit engineering passive allowance; full leads included |
| BlackPillDrainR_OUT | 1 | 0.12 | 0.05–0.4 | Existing main-fuse allowance or explicit engineering passive allowance; full leads included |
| BlackPillSenseTop | 1 | 0.12 | 0.05–0.4 | Existing main-fuse allowance or explicit engineering passive allowance; full leads included |
| BlackPillSenseBottom | 1 | 0.12 | 0.05–0.4 | Existing main-fuse allowance or explicit engineering passive allowance; full leads included |
| BlackPillSenseCapacitor | 1 | 0.12 | 0.05–0.4 | Existing main-fuse allowance or explicit engineering passive allowance; full leads included |
| Inner fitted LED strip | 0.583333333 | 25 | 15–40 | Existing component-inventory.json fitted strip allowance g/m; pixels and back counted together |
| Side0 fitted LED strip | 0.583333333 | 25 | 15–40 | Existing component-inventory.json fitted strip allowance g/m; pixels and back counted together |
| Side1 fitted LED strip | 0.583333333 | 25 | 15–40 | Existing component-inventory.json fitted strip allowance g/m; pixels and back counted together |
| M22759/16-18-2 | 1 | 1.73318 | 1.21323–2.59978 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-18-2 | 1 | 2.27356 | 1.59149–3.41034 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.280215 | 0.196151–0.420323 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-18-2 | 1 | 2.38405 | 1.66883–3.57607 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.162466 | 0.113726–0.243699 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-18-2 | 1 | 1.27809 | 0.894661–1.91713 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.162789 | 0.113952–0.244183 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-22-2 | 1 | 0.40815 | 0.285705–0.612224 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.209231 | 0.146462–0.313846 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-22-2 | 1 | 0.761273 | 0.532891–1.14191 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-22-2 | 1 | 0.60703 | 0.424921–0.910546 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.246565 | 0.172596–0.369848 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-22-2 | 1 | 0.507193 | 0.355035–0.76079 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.160248 | 0.112173–0.240371 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.271933 | 0.190353–0.407899 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.336321 | 0.235425–0.504482 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.469507 | 0.328655–0.704261 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.132076 | 0.092453–0.198114 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.193099 | 0.135169–0.289648 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.18894 | 0.132258–0.28341 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.130669 | 0.0914683–0.196004 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-22-2 | 1 | 0.387216 | 0.271051–0.580823 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-22-2 | 1 | 0.333344 | 0.233341–0.500016 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-22-2 | 1 | 0.480463 | 0.336324–0.720694 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-22-2 | 1 | 0.498408 | 0.348885–0.747612 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-22-2 | 1 | 0.707475 | 0.495232–1.06121 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-22-2 | 1 | 0.36907 | 0.258349–0.553605 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-22-2 | 1 | 0.30372 | 0.212604–0.45558 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-22-2 | 1 | 0.618773 | 0.433141–0.928159 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.175167 | 0.122617–0.262751 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-22-2 | 1 | 1.4223 | 0.995613–2.13346 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-22-2 | 1 | 0.892413 | 0.624689–1.33862 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-22-2 | 1 | 0.773066 | 0.541146–1.1596 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-22-2 | 1 | 0.363223 | 0.254256–0.544834 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-22-2 | 1 | 0.544209 | 0.380947–0.816314 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-22-2 | 1 | 0.432726 | 0.302908–0.649089 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-2 | 1 | 0.227176 | 0.159023–0.340764 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-22-2 | 1 | 0.530248 | 0.371174–0.795372 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-22-2 | 1 | 0.629891 | 0.440924–0.944836 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.48291 | 0.338037–0.724365 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.401498 | 0.281048–0.602247 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.428552 | 0.299987–0.642829 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.468977 | 0.328284–0.703465 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-18-0 | 1 | 2.19191 | 1.53433–3.28786 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-22-0 | 1 | 0.736086 | 0.51526–1.10413 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-22-0 | 1 | 0.642602 | 0.449821–0.963902 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-22-0 | 1 | 0.763162 | 0.534214–1.14474 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-22-0 | 1 | 1.5794 | 1.10558–2.36909 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-22-0 | 1 | 0.96638 | 0.676466–1.44957 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-0 | 1 | 0.376567 | 0.263597–0.56485 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-0 | 1 | 0.124166 | 0.086916–0.186249 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-0 | 1 | 0.109755 | 0.0768287–0.164633 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-0 | 1 | 0.119805 | 0.0838634–0.179707 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-0 | 1 | 0.303517 | 0.212462–0.455275 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-0 | 1 | 0.0917719 | 0.0642404–0.137658 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-0 | 1 | 0.317864 | 0.222504–0.476795 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-22-0 | 1 | 0.52167 | 0.365169–0.782505 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-22-0 | 1 | 0.383484 | 0.268439–0.575226 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-22-0 | 1 | 1.41922 | 0.993452–2.12883 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-22-0 | 1 | 0.63805 | 0.446635–0.957074 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/16-22-0 | 1 | 1.05276 | 0.736931–1.57914 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-0 | 1 | 0.268251 | 0.187776–0.402376 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-0 | 1 | 0.304708 | 0.213296–0.457062 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-0 | 1 | 0.323063 | 0.226144–0.484594 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-0 | 1 | 0.19675 | 0.137725–0.295124 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-0 | 1 | 0.162579 | 0.113806–0.243869 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-0 | 1 | 0.31592 | 0.221144–0.473879 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.360269 | 0.252189–0.540404 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.367743 | 0.25742–0.551615 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.23054 | 0.161378–0.34581 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.262417 | 0.183692–0.393625 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.124919 | 0.0874435–0.187379 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.331937 | 0.232356–0.497905 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.15614 | 0.109298–0.234211 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.229548 | 0.160683–0.344322 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.339393 | 0.237575–0.50909 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.265434 | 0.185804–0.398151 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.182594 | 0.127816–0.273891 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.193024 | 0.135117–0.289535 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.229982 | 0.160987–0.344973 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.348945 | 0.244261–0.523417 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.205522 | 0.143865–0.308283 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.301749 | 0.211224–0.452623 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.309922 | 0.216945–0.464883 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.258227 | 0.180759–0.387341 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.443124 | 0.310187–0.664686 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.223947 | 0.156763–0.33592 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.227779 | 0.159445–0.341668 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.149412 | 0.104588–0.224117 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.192591 | 0.134813–0.288886 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.209737 | 0.146816–0.314605 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| M22759/18-26-9 | 1 | 0.132472 | 0.0927303–0.198708 | Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste |
| BatteryLeadP | 1 | 0.520457 | 0.36432–0.780685 | Same selected18AWG stock/full finished contact lead; excludes duplicate F1 onward wire |
| Insulated solder splice B | 1 | 0.364 | 0.1798–1.171 | Selected18AWG continuous core cut once plus0.1..1g solder/sleeve allowance per completed splice; actual fabrication unmeasured |
| Insulated solder splice BOOST_OUT | 1 | 0.364 | 0.1798–1.171 | Selected18AWG continuous core cut once plus0.1..1g solder/sleeve allowance per completed splice; actual fabrication unmeasured |
| Insulated solder splice LOAD_5V | 1 | 0.364 | 0.1798–1.171 | Selected18AWG continuous core cut once plus0.1..1g solder/sleeve allowance per completed splice; actual fabrication unmeasured |
| Insulated solder splice LATCH_OFF | 1 | 0.364 | 0.1798–1.171 | Selected18AWG continuous core cut once plus0.1..1g solder/sleeve allowance per completed splice; actual fabrication unmeasured |
| Insulated solder splice SENSE | 1 | 0.364 | 0.1798–1.171 | Selected18AWG continuous core cut once plus0.1..1g solder/sleeve allowance per completed splice; actual fabrication unmeasured |
| Insulated solder splice LED_DISTRIBUTION | 1 | 0.3868 | 0.19576–1.2052 | Selected18AWG continuous core cut once plus0.1..1g solder/sleeve allowance per completed splice; actual fabrication unmeasured |
| Insulated solder splice FIB_5V | 1 | 0.364 | 0.1798–1.171 | Selected18AWG continuous core cut once plus0.1..1g solder/sleeve allowance per completed splice; actual fabrication unmeasured |
| Insulated solder splice AUX_3V3 | 1 | 0.3868 | 0.19576–1.2052 | Selected18AWG continuous core cut once plus0.1..1g solder/sleeve allowance per completed splice; actual fabrication unmeasured |
| Insulated solder splice GND | 1 | 0.478 | 0.2596–1.342 | Selected18AWG continuous core cut once plus0.1..1g solder/sleeve allowance per completed splice; actual fabrication unmeasured |
| Insulated solder splice SPI_CLOCK | 1 | 0.364 | 0.1798–1.171 | Selected18AWG continuous core cut once plus0.1..1g solder/sleeve allowance per completed splice; actual fabrication unmeasured |
| Insulated solder splice SPI_MOSI | 1 | 0.364 | 0.1798–1.171 | Selected18AWG continuous core cut once plus0.1..1g solder/sleeve allowance per completed splice; actual fabrication unmeasured |
| Insulated solder splice SPI_MISO | 1 | 0.364 | 0.1798–1.171 | Selected18AWG continuous core cut once plus0.1..1g solder/sleeve allowance per completed splice; actual fabrication unmeasured |
| Selected100mm insulating pull ribbon | 1 | 0.5 | 0.2–1.5 | Engineering complete fitted ribbon allowance |
| WayneMills5038 TypeIII Class1A3/8 nylon,1.1m main+2x0.1m wearloops | 1 | 4.11105 | 2.90192–4.83653 | MIL-DTL5038K2016 TableIII maximum0.12oz/yd conditional on conforming stock; includes sewn overlaps |
| Bonded nylon sewing thread, completed box-X seams | 1 | 0.5 | 0.2–1 | Engineering installed stitching allowance; seams and wearing unmeasured |
| Fitted solder,3M5413 joint insulation and labels | 1 | 3 | 1.5–6 | Retained component-inventory wire_finish allowance; splice sleeve/solder allowances above separate; measure finished assembly |
| Front two-way coating | 1 | 1 | 0.3–3 | Engineering allowance; weigh installed item; retained unresolved allowance, source: hardware/enclosure/exports/front-coating.svg |
| Rear mirror coating/film | 1 | 1.5 | 0.5–4 | Engineering allowance; weigh installed item; retained unresolved allowance, source: hardware/enclosure/exports/rear-mirror.svg |
| Front black rim mask | 1 | 1 | 0.3–3 | Engineering allowance; weigh installed item; retained unresolved allowance, source: hardware/enclosure/exports/front-coating.svg |
| Baffle spacer tack | 1 | 2 | 1–5 | Engineering allowance; weigh installed item; retained unresolved allowance, source: hardware/enclosure/vendor/evilgeniuslabs-fibonacci256/SOURCE.md |
| Removable body joint seals | 1 | 3 | 1.5–7 | Engineering allowance; weigh installed item; retained unresolved allowance, source: hardware/enclosure/README.md |
| Optical lead and joint seals | 1 | 3 | 1–7 | Engineering allowance; weigh installed item; retained unresolved allowance, source: hardware/enclosure/README.md |
| Four adhesive vent membranes | 4 | 0.15 | 0.05–0.4 | Engineering allowance; weigh installed item; retained unresolved allowance, source: hardware/enclosure/README.md |

The raw JSON lists each CAD owner exactly once. Alternate ring material changes only its selected material rows.
The complete loom record includes endpoint strips, internal jacket insertions and one continuous negative contact-to-boost lead.
The service guide distinguishes ordinary cell access from rear/radio maintenance. Keep all unexecuted physical tests unmeasured.

