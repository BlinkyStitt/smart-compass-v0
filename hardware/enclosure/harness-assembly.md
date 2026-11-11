# Narrow fixed loom assembly

Use the selected narrow CAD generation. The wide model is an inactive archive.
The loom is fixed during ordinary cell replacement. No connector is opened to
remove the cell. Supplied fit, joints, insulation, retention, reset timing and
electrical or thermal performance remain unmeasured.

## Assembly records

Use these records from one complete generation:

- [Circuit and module changes](electrical-design.md).
- [Exact wire paths, stock and cuts](harness-routing.json).
- [Splice gauges and positions](harness-splices.json).
- [Native loom check and cut list](../../designs/stacked/exports/loom-check.json).
- [Native assembly](../../designs/stacked/exports/stacked-fibonacci.FCStd) or
  [assembled STEP](../../designs/stacked/exports/stacked-fibonacci.step).
- [Installed census and mass allowances](../../designs/stacked/exports/parts.json).
- The named titanium cap-screw stock and finish settings in
  `designs/stacked/fasteners.json` (`04-REFERENCE/fasteners.json` in the ZIP).
- [Battery service](battery-access.md) and
  [physical qualification procedure](qualification-plan.md).

The service ZIP puts the circuit, routing, splice records, component instructions
and generated check records in `04-REFERENCE`. Match the archive manifest before
assembly. Do not combine cuts from one generation with another layout.

All coordinates use the native CAD frame in millimetres. A rear view reverses
the apparent left and right directions. Follow the physical pad names and
polarity marks. Do not mirror the coordinates to match a photograph.

## Hand assembly requirements

The current circuit is not released as a beginner hand-build kit. Its R20.2
low-battery tap requires small surface-mount rework. A CAD clearance pass does
not prove that this step is easy to solder. Keep this limitation visible until
the replacement circuit and its fitted connections pass review.

The charging revision must meet these requirements:

- Use assembled modules and their labeled through-hole pads or stock connectors.
  Do not require a wire on an IC leg, an individual USB contact or a small
  surface-mount resistor pad. Keep the factory surface-mount parts installed.
- Replace the R20 removal and tap with an interface at the PowerBoost LBO
  header. Check the input load, logic polarity and power-loss behavior of that
  interface. A motor-driver module with an input pull-down is not an automatic
  substitute for a high-impedance logic input.
- Use a dedicated input connector for charging and external power. Do not tap
  Sparkle Q1 or R5 to obtain USB input power. Select the complete power path
  before assigning those connections.
- Prefer purchased, keyed cable assemblies for connections that need removal.
  Do not require the builder to crimp small connector contacts. Check the
  selected cable gauge, connector rating and actual fitted cable length.
- Put one supported conductor in each screw clamp. Use a separate supported
  distribution connection where a rail needs more branches. Do not tin a wire
  that will enter a screw clamp.
- Solder module headers and wire leads on the bench before fitting the modules
  in their carriers. Both the joint and the iron tip need access. Do not plan
  to solder through a narrow gap in the assembled case.
- Assemble axial fuses, resistors and their insulated joints outside the case.
  Fit the sleeves before soldering. Support the leads during soldering, let
  the joints cool, then fit the assembly in its carrier and strain relief.
- Mark both ends of every lead with its wire ID and terminal name. Keep a
  component-side connector view in the assembly drawing. Do not rely on wire
  color alone.

Before calling the revised design hand-build ready, assemble a sample of its
smallest through-hole joint, its largest wire joint and each connector type.
Check actual wire insertion, access, insulation, continuity and retention.
Then assemble one complete unit in the documented order. Record problems and
revise the owning geometry or connection. These physical checks remain
unmeasured. No current CAD or source check supplies that evidence.

## Prepare and fit

1. Keep the cell and external power disconnected. Support the assembly on a
   padded surface. Print and inspect the fit samples before full parts.
2. Fit the selected modules and passives in their source-based carriers. Use the
   52 named titanium cap-screw selections from `fasteners.json`; keep the other
   selected hardware. Check actual stock, thread/runout, finished lengths,
   head fit and full nut engagement. Keep the factory components
   that the circuit retains. Remove only the named connectors, R20 and optional
   parts. Inspect reworked pads before wiring.
3. Fit the PCB-backed splice carriers, specified adhesive pads and two spot ties
   per splice. The adhesive thickness and completed splice envelopes are assembly
   targets. Use the recorded positions. The MOSI carrier centre is
   `(-20, 52, 28.25)`; its exits must stay clear of the separate MISO carrier.
4. Identify each lead by its wire ID on the cut tray. Use its selected stock,
   colour, strip lengths and blank cut target. Form its route before final trim.
   The finished cut includes the declared stripped and inserted ends. The extra
   blank allowance is trim waste and is not installed mass.
5. Form the listed centreline bend radius. The target is at least three times
   the selected maximum wire diameter. It is a fabrication target, not a
   manufacturer fatigue or bend guarantee. Do not stretch a lead to reach a pad.
6. Use one continuous W044 negative conductor from its contact cup, through the
   fixed conduit, to `BOOST.X2.1`. Do not cut a separate negative contact tail or
   add a splice. Keep the short positive contact lead and F1 inside their
   insulating housing. Retain both main-fuse ties.
7. Seat W006 and W044 in the fitted boost-input relief. Fit its curved VHB pad
   and specified LC134 tie. Keep each module clamp to one untinned conductor.
   Do not use solder to increase a conductor's fit in a screw clamp.
8. Complete the specified solder laps and insulation gauges. The original
   Fibonacci input pads stay on the rear face. The selected module PTH joints
   use the component face, except the documented latch controls and antenna.
   Leave S1.6 insulated and otherwise unconnected. Do not connect unused module
   headers or an external power input.
9. Seat each path as shown in the native model. Keep it clear of the cell bay,
   contact backs, door, keeper, fasteners, controls and antenna. Do not add a
   connector, sleeve or wire bundle in an unallocated gap. Inspect each joint
   before fitting the original board and closing the assembly.

The W017 START lead uses a narrow nominal passage between the fuse carrier and
auxiliary splice fixture. Its vertical centre is at Y=17.425 mm. The selected
0.8636 mm maximum OD leaves 0.1432 mm nominal clearance at each side. This is a
CAD target, not a supplied tolerance or physical fit result. Inspect that passage
and the complete formed route before accepting the built unit.

Keep the three inner-ring input finishes separate. The DIN tail descends at
X=0 mm/Y=96.1 mm; the power tails descend at X=−0.8/+0.8 mm and Y=94.85 mm.
Use the formed paths and finished insulation gauges in the routing record.
Inspect the space between the completed joints before fitting the ring.
These coordinates are fabrication targets; supplied pad fit remains unmeasured.
The shell passage height follows the complete upper formed joint, with a
0.3 mm nominal clearance target. Keep the joint inside that opening. The tie
support web retains its separate specified height.
The wire-support land preserves the outside diffuser and strip window. Its
upper web joins the existing case shoulder above that window. Keep both side
LED rows and the continuous 2 mm diffuser at their recorded dimensions.

The W084 source exit passes below the BlackPill sense bridge. Its first
horizontal centre is at Z=13.0108 mm. The selected maximum OD leaves
0.0574 mm nominal clearance below the Z=13.5 mm bridge face. Preform this
lead during board assembly. Check the actual board, jacket and printed bridge
before fitting the bridge. This nominal gap is not a supplied tolerance or
physical fit result.

## Component instructions

Use the individual instructions for the [controls](control-mounts.md),
[latch](latch-mounts.md), [boost](boost-mounts.md),
[capacitor](capacitor-mounts.md), [fuse carrier](branch-fuses.md),
[Sparkle](sparkle-mounts.md), [BlackPill](blackpill-mounts.md),
[GPS](gps-mounts.md), [IMU](imu-mounts.md) and [radio](radio-mounts.md).
Keep the soldering conditions and source limits in those records. A completed
insulation gauge does not prove solder quality or electrical withstand.

## Check and service

Inspect the complete wiring, polarity and two physical switch poles before
applying power. Use the qualification procedure for the initial bench tests.
Use the actual rainbow workload and declared brightness scenario. No firmware
current ceiling or safe wearing condition is established by the calculator.

Ordinary battery service keeps the rear, optics, necklace and complete loom
fitted. Support the pendant, select physical OFF and remove external power.
Open the captive door, hold the cell, release the independent keeper and use
the ribbon. Follow the illustrated service guide for insertion and START.
There is no qualified reset wait.

Rear or radio maintenance is a separate operation. Remove the cell first.
Disconnect each bridging external lead at both ends. Remove loose leads,
joint insulation and boots before withdrawing the rear or radio assembly.
The fixed PCB-backed splice carriers stay fitted. Release the relevant ties
before board replacement. Support every removed assembly by hand.
