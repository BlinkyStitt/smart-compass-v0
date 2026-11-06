# Original 166 mm Fibonacci256 terminals

Evil Genius Labs / Jason Coon supplied the photographs. The
[pinned original maker post](https://github.com/evilgeniuslabs/evilgeniuslabs.github.io/blob/a7bf6560d6adb5650abbef8b4c23d9d472e3b338/_posts/2020-02-27-fibonacci256.md)
links both originals. The [product specifications](https://www.evilgeniuslabs.org/fibonacci256#specifications)
give a 166 mm diameter and 1.6 mm PCB thickness. The rear silk identifies v0.1.
The index records the source revision, retrieval date, byte counts and hashes.
These photographs are source evidence, not new artwork or a replacement PCB.

The [bare rear photograph](fnqNrNl.png) clearly shows the input at its bottom.
Its pads read **GND, DI, 5V** from left to right. The opposite row has **DO**.
The [LED-side photograph](ISnaLBD.png) shows the other face of this board.
The maker's assembly instructions connect the controller data wire to **DI**.
Keep all three output pads unused for this single-board harness.

## Nominal routing frame

Set the origin at the PCB centre. Look at the LED side, with +X right, +Y up
and +Z toward the LEDs. Rotate the board so input DI is at the bottom (-Y).
In this front view the input order is **5V, DI, GND** from left to right.

| Input pad | Front X, mm | Front Y, mm |
| --- | ---: | ---: |
| 5V | -2.6 | -81.8 |
| DI | 0.0 | -81.9 |
| GND | 2.6 | -82.0 |

These are photo-estimated nominal coordinates. They are adequate starting
points for flexible rear wires. They are not a drill template, a rigid mating
connector specification or guaranteed manufacturer limits. Rounding to 0.1 mm
does not establish that accuracy. The retained terminal record describes the
manual landmarks, circle scale, projective assumptions and image-fit residual.
That residual is not a pad-position error bound.

Solder fixed wires at the labelled rear input pads. Check the supplied board's
labels and fit before soldering. Do not add PCB holes or use DO for data input.
The installed route must include the solder joints, insulation and strain relief.
Those design checks and physical acceptance remain separate.

This terminal frame does not change the original stencil or published pixel
map. Set the installed board-to-stencil rotation from their common physical
pattern. A local terminal map alone does not prove that registration.
