# Selected PowerBoost screw terminals

Use two Pololu2444 two-pin3.5mm side-entry terminal blocks at PowerBoost X1/X2.
The [seller page](https://www.pololu.com/product/2444) specifies24–18AWG wire,
10A and5mm stripped length. The retained dimension figure gives nominal body
size7.96x6.8x8.4mm,0.8mm round pins and3.7+/-0.3mm pin length. It does not
supply other body/pin tolerances. Its20mohm resistance entry has no maximum
qualifier. Do not infer worst-case path resistance or enclosed performance.

The index records each URL, revision, size and hash. The saved HTML removes
anonymous form session fields; the index records that transformation and the
original source hash. Specification text and source links remain unchanged.
The original manufacturer board/schematic and their attribution are in
[the PowerBoost source directory](../powerboost-1000-basic/README.md).

Adafruit's source assigns X1.1 and X2.1 to ground. X2.2 takes switched battery
input; X1.2 supplies the stock nominal5.2V output. The source calls that net
`5.0V`. The checker reads the actual pad positions and nets, including R20.2.
Nominal drills/footprints do not prove supplied-part fit or solder quality.
Complete carrier, wire routes/cuts, strain relief and physical tests remain
required. This selection does not close the fitted-harness design error.
