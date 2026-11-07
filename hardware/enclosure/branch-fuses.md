# Fixed branch-fuse carrier

## Selected narrow assembly

Use this guide with the [fixed loom assembly guide](harness-assembly.md).
The complete narrow generation owns `installed-fit-check.json`, `loom-check.json`
and `inventory.md`. These records are in `designs/stacked/exports/` in the
repository and `04-REFERENCE/` in the service ZIP. A component test alone does
not establish installed fit or physical acceptance. Any Wide fixture data below
is an inactive component-study reference.

Use `designs/stacked/fasteners.json` for its 52 named narrow titanium cap screws.
The service ZIP includes `04-REFERENCE/fasteners.json`. All other hardware keeps
its specified parts, materials and mass allowances. Gauge the actual stock,
finished length, thread/runout, head fit and full nut engagement. Physical fit,
retention and strength remain unmeasured.

Fit one F_FIB 2 A fuse, three F_RING 1 A fuses and one F_AUX 0.5 A fuse.
Use the selected Littelfuse 251 axial parts in `electrical-design.json`.
Keep all five protected branches. Do not bypass a fuse with a second feed.
The main 4 A fuse remains at the positive contact in the battery compartment.
This carrier does not change the selected circuit or establish fault clearing.

The selected source is the Littelfuse 251 sheet, GK 18-Aug-2026, pages1–3:
[manufacturer PDF](https://www.littelfuse.com/assetdocs/littelfuse-fuse-251-253-datasheet?assetguid=f47a0bb7-8ede-4679-9646-7114c3787688).
For these ratings, the source drawing gives a 2.80 mm maximum body diameter,
7.11 mm body length and 0.64 mm wire diameter. The latter two dimensions have
no stated maximum tolerance in that drawing. The native source-body shape
uses those nominal values; it does not turn them into guaranteed limits.
The 52.4 mm T1 dimension is the between-tape dimension, not an assembled cut.
Nominal cold resistance and melting I²t are not guaranteed fault bounds.

Prepare each insulated assembly to fit a 20 × 5 × 5 mm gauge space. Fit one
22 AWG wire to each end with a separate fixed lap joint. Keep the wire ends
within the 3 mm end-joint regions. Use one conductor at each connected clamp.
Keep the epoxy body clear of clamps and ties. Inspect the supplied leads and
body before trimming. Use TE Raychem RNF-100-1/8-0-SP sleeves, with 3.2 mm
minimum expanded ID. Keep each joint small enough to fit the unshrunk sleeve.
Recover and inspect the sleeves outside the PETG case. Gauge full coverage
and the completed assembly. The 5 mm space is a manufacturing target, not a
manufacturer guarantee, measurement or insulation qualification.

Use the source hand-soldering conditions: 350 ±5 C iron temperature and
5 seconds maximum heating time. Protect the body from mechanical load while
soldering and forming. The published fuse lead-pull and vibration tests do
not qualify these finished joints, wires, ties or the printed carrier.
The [TE part page and A2 drawing](https://www.te.com/en/product-5052994073.html)
give the tubing conditions; do not shrink tubing inside the case.

The carrier has one 1.35 mm floor at Z = 16.95..18.3 mm. Two integral posts
stand on rear bosses at source XY [9,4] and [9,15] mm. Fit the two M2 nuts
before the fuses or other electronics. Insert the first from source −X through an 18 mm entry and
the second from source +Y through a 12 mm entry. The native check covers
the complete nut lowering/entry paths and full pocket-roof bearing.

Fit two selected SSC-M2-20-TI5 screws finished to 17.7 mm under head and
two 0.35 mm M2
washers from the rear. Deburr and gauge the finished lengths. The nominal
tip extends 0.4 mm beyond the nut. The screw bores stop below the floor top;
0.95 mm of nominal printed material covers each finished tip. The nut roof
has a 1.35 mm target thickness. The component check requires complete rear
bearing, full engagement and valid connected printed geometry.

In Narrow, the source coordinates are case coordinates. F_FIB, F_RING1 and
F_RING2 run from X = 0 to20 mm at Y = −3, 5 and13 mm. F_RING3 and F_AUX
run from Y = −7 to13 mm at X = 24.5 and32.5 mm. Each joint centre is at
Z = 20.8 mm. Pin1 is at the lower coordinate; pin2 is at the higher one.
In Wide, turn the whole carrier 90 degrees, then add [11,25] mm. Transform
both ends and every support together. `branch_fuses.ports()` supplies these
specified joint exits. The selected narrow wire cuts and fitted routes are
in the complete loom record and fixed loom assembly guide.

Use two Alpha Wire LC134 BK088 square-knot spot ties per fuse, over the
insulated joint regions at2 and18 mm along the axis. Cut ten70 mm blanks.
Keep each knot and its short tails in the modeled side space. The selected
stock has 1.6764 mm maximum width and0.4318 mm maximum thickness; the model
reserves1.7 mm and0.5 mm around each loop. The attached4 × 2.2 × 2 mm knot
space is a finished gauge target. It does not predict knot shape or force.
Check that no knot, loose tail or lead can touch an adjacent assembly.
See the [Alpha current LC134 specification](https://www.alphawire.com/products/accessories/fit-wire-management/lacing-tape/lc134)
and its linked lacing instructions. Do not use tape breaking strength as an
installed knot or printed-part retention rating.

Run `BranchFuseCheck.FCMacro` with `SC_CAD_DIR` set to this directory and
`SC_BRANCH_FUSE_CHECK_RESULT` set to a new result path. Require its named PASS
and unchanged source hashes. It checks all22 physical products and5 assembly
references, actual pair intersections, rear support, screw tips, covered
nut seats and complete nut paths. It rejects missing parts, floating support
and a short screw. This is a component check. Use the complete narrow
installed records for battery access, all fixed routes and service states.
Count each selected fuse, tie and hardware item once. Do not use
reference volumes as purchased parts or mass. Physical fit, joints, insulation,
fault interruption, vibration, temperature and wearing remain unmeasured.

The carrier floor gives 0.45 mm nominal clearance below its tie loops to the
Narrow radio loaded-space top. This exceeds the selected 0.25 mm service gap.
Keep that margin; the first placement gave only the minimum at an exact
geometry boundary. Physical clearance and assembly variation remain unmeasured.
