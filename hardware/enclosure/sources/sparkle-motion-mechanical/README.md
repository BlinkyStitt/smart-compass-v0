# Original Adafruit Sparkle Motion mechanical source

The original Adafruit 6100 STEP, upstream README and MIT license are unchanged.
The index records the pinned source revision, URLs, byte counts and SHA-256
values. The electrical Eagle source has its own CC-BY-SA-3.0 license in the
adjacent `sparkle-motion` directory.

The source STEP has 239 solids. Its largest body is the nominal
50.8 × 33.147 × 1.57 mm PCB. All 31 source through-holes register with the
selected Rev D Eagle layout in the retained recovery inspection. This proves
mechanical registration, not electrical revision equivalence or supplied fit.

The original named `DCJACK_2MM_PTH` component corresponds to source solid159.
Its volume is 881.0812099467767 mm³. `sparkle_mount.py` pins the original file,
solid index, volume and bounds before selecting the X7 connector-removal
variant. The original file remains complete. No other component is removed.
The selected digital model uses the source PCB and conservative top/underside
reservations. It does not estimate the mass of mixed materials from CAD volume.
