"""Native FreeCAD concept: separate optical stack, real-size hardware envelopes."""

import json
import math

import baffle
import antenna
import antenna_native
import battery_access
import rear_cover
import control_fixture
import latch_mount
import imu_mount
import boost_mount
import capacitor_mount
import gps_mount
import sparkle_mount
import blackpill_mount
import radio_mount
import branch_fuses
import harness_install,harness_contract,narrow_inventory,battery_leads,mass_core
import prints,service,narrow_fasteners
import antenna_view
import FreeCAD as App
import FreeCADGui as Gui
import Part
from solid_clearance import bounds
from demo_export import GLB
from geometry import led_centres, pixel_regions, ring_pixel
from hardware_spec import hexagon, nut_dimensions, WASHERS
from layout import ROOT, parameters, validate
from PySide import QtCore, QtGui


def cylinder(radius, height, z=0, x=0, y=0):
    return Part.makeCylinder(radius, height, App.Vector(x, y, z))


def annulus(inner, outer, height, z):
    return cylinder(outer, height, z).cut(cylinder(inner, height, z))


def box(w, l, h, x, y, z):
    return Part.makeBox(w, l, h, App.Vector(x - w / 2, y - l / 2, z))


def polygon_face(points, z):
    return Part.Face(
        Part.makePolygon([App.Vector(x, y, z) for x, y in points + [points[0]]])
    )


def build(out):
    out.mkdir(parents=True, exist_ok=True)
    p = parameters()
    d = validate(p)
    doc = App.newDocument("StackedFibonacci")
    sheet = doc.addObject("Spreadsheet::Sheet", "Parameters")
    sheet.set("A1", "Compact concept - regenerate from parameters.json")
    row = 2
    for key, value in {**p, **d}.items():
        if isinstance(value, (float, int)):
            sheet.set(f"A{row}", key)
            sheet.set(f"B{row}", str(value))
            row += 1
    groups = {
        name: doc.addObject("App::DocumentObjectGroup", name)
        for name in ("Manufactured", "Electronics", "Optics", "Hardware")
    }
    objects = []
    fastener_data,fastener_selection=narrow_fasteners.load()

    def add(
        name, shape, group, colour, role="solid", material="Opaque black PETG", offset=0
    ):
        # Keep the owning construction's topology. Same-domain refinement
        # corrupts the valid case's curved board-seat faces in FreeCAD1.1.4.
        shape = shape.copy()
        assert shape.isValid() and shape.Volume > 0, name + " invalid or empty"
        if group == "Manufactured":
            assert len(shape.Solids) == 1, name + " is disconnected"
            shape.check(True)
        obj = doc.addObject("PartDesign::Feature", name)
        obj.Shape = shape
        obj.Label = name
        obj.addProperty(
            "App::PropertyString", "FitStatus"
        ).FitStatus = "Concept only; supplied hardware, coatings and fit unmeasured"
        if name in fastener_selection:material=fastener_data['material']+'; '+fastener_selection[name]['stock_part']+'; finished under-head target '+str(fastener_selection[name]['finished_under_head_length_target_mm'])+'mm'
        obj.addProperty("App::PropertyString", "Material").Material = material
        obj.addProperty("App::PropertyString", "PreviewRole").PreviewRole = role
        obj.addProperty("App::PropertyFloat", "ExplodeOffsetM").ExplodeOffsetM = offset
        groups[group].addObject(obj)
        obj.ViewObject.ShapeColor = colour
        if role in ("mirror", "rear_mirror"):
            face = "rear" if role == "rear_mirror" else "front"
            obj.ViewObject.Transparency = round(100 * p[face + "_transmission"])
        elif role == "side":
            obj.ViewObject.Transparency = 25  # Diagram-only diffuser visibility.
        objects.append(obj)
        return obj

    R = d["case_radius"]
    rear_points = [
        (
            d["rear_fastener_radius"] * math.cos(i * math.tau / 6),
            d["rear_fastener_radius"] * math.sin(i * math.tau / 6),
        )
        for i in range(6)
    ]
    front_points = [
        (
            d["front_fastener_radius"] * math.cos(i * math.tau / 6),
            d["front_fastener_radius"] * math.sin(i * math.tau / 6),
        )
        for i in range(6)
    ]
    access=battery_access.definition()
    cell_parts=battery_access.native_shapes(access,'narrow')
    controls=control_fixture.native_shapes(
        *((p['control_'+key+'_x'],p['control_'+key+'_y']) for key in ('switch','start','mode','action')),
        switch_rotation_deg=p['control_switch_rotation_deg'],guard_mount_offset_mm=p['control_guard_mount_offset'],design='narrow')
    rear=rear_cover.native_blank(R,rear_points,p['rear_vents_xy_mm'],cell_parts,controls)
    for name in sorted(control_fixture.product_names('narrow')):
        add(name,controls[name],'Manufactured' if name in control_fixture.printed_parts('narrow') else 'Electronics',(.2,.3,.2),material='Selected rear control; specified assembly target, physical fit unmeasured')
    for name in sorted(battery_access.part_names('narrow')):
        group='Manufactured' if name in battery_access.printed_parts('narrow') else 'Electronics'
        add(name,cell_parts[name],group,(.2,.25,.3),material='Candidate geometry; not a release')
    # Rear service uses six separate M3 clamp stacks. These are fitted assembly
    # targets, not a torque/strength qualification or a measured screw length.
    for i,(x,y) in enumerate(rear_points):
        washer=WASHERS['M3']
        wz=-washer['thickness']
        shaft=cylinder(1.5,6,wz,x,y)
        head=cylinder(2.75,3,wz-3,x,y)
        add('RearScrew'+str(i),shaft.fuse(head),'Hardware',(.4,.4,.42),material='DIN912 M3x6; assembly target')
        ring=cylinder(washer['od']/2,washer['thickness'],wz,x,y).cut(cylinder(washer['id']/2,washer['thickness'],wz,x,y))
        add('RearWasher'+str(i),ring,'Hardware',(.4,.4,.42),material='DIN125 M3 washer')
        flats,height=nut_dimensions('M3')
        nut=polygon_face(hexagon(x,y,flats),2).extrude(App.Vector(0,0,height)).cut(cylinder(1.5,height,2,x,y))
        add('RearNut'+str(i),nut,'Hardware',(.4,.4,.42),material='A4 M3 plain nut')
    # The shared rear base owns all openings before module fixtures are added.
    add("RearCover", rear, "Manufactured", (0.025, 0.025, 0.03), offset=-0.035)
    shell = annulus(d['shell_inner_radius'],R,d['rear_bottom']-2.8,2)
    # Lower wall has no LED carrier. Keep its full suspension lands and the
    # original full annular transition below the unchanged side strip datum.
    lower_tool=annulus(d['shell_inner_radius'],R-2,3.5,2).fuse(
        Part.makeCone(R-2,d['shell_inner_radius'],7,App.Vector(0,0,5.5)).cut(
            cylinder(d['shell_inner_radius'],7.2,5.4)))
    for side in (-1,1):
        land=box(20,20,11,side*d['suspension_x'],d['suspension_y'],2)
        lower_tool=lower_tool.cut(land)
    shell=shell.cut(lower_tool)
    shell = shell.cut(
        annulus(
            d["side_radius"] - p["strip_thickness"] / 2,
            R + 1,
            d["side_height"],
            p["side_bottom_z"],
        )
    )
    shell = shell.fuse(
        annulus(82.5, d["board_support_outer_radius"], 2, p["circle_back_z"] - 2)
    )
    # Captive M3 nuts insert from the open rear, below each support post.
    for x, y in rear_points:
        post = cylinder(3, p["circle_back_z"] - 4, 2, x, y).cut(
            cylinder(1.7, p["circle_back_z"] - 3, 1.5, x, y)
        )
        pocket = polygon_face(
            [(x + a, y + b) for a, b in hexagon(0, 0, 5.8)], 2
        ).extrude(App.Vector(0, 0, 2.6))
        shell = shell.fuse(post.cut(pocket))
    for side in (-1, 1):
        slot = box(12, 4, 11, 0, 0, 2)
        slot.rotate(App.Vector(), App.Vector(0, 0, 1), 143 if side == 1 else 37)
        slot.translate(App.Vector(side * d["suspension_x"], d["suspension_y"], 0))
        shell = shell.cut(slot)
    shell = shell.cut(
        annulus(
            d["side_radius"] - p["strip_thickness"] / 2,
            R + 1,
            d["side_height"],
            p["side_bottom_z"],
        )
    )
    for i in range(3):
        # Captive nut sits BELOW the board ledge, with a radial insertion slot.
        # The old empty pocket above that ledge could not clamp the edge clip.
        pocket_flats,pocket_height=nut_dimensions('M2',pocket=True)
        pocket_z=p['circle_back_z']-3.7
        pocket=polygon_face(hexagon(85.5,0,pocket_flats),pocket_z).extrude(App.Vector(0,0,pocket_height))
        pocket=pocket.fuse(box(4.5,pocket_flats,pocket_height,83.25,0,pocket_z))
        nut_boss=cylinder(3.8,2.2,p['circle_back_z']-4.2,85.5,0)
        spacer=cylinder(1.8,1.6,p['circle_back_z'],85.5,0)
        bore=cylinder(1.1,9,p['circle_back_z']-4.3,85.5,0)
        for shape in (pocket,nut_boss,spacer,bore):
            shape.rotate(App.Vector(),App.Vector(0,0,1),i*120)
        shell=shell.fuse(nut_boss).fuse(spacer).cut(pocket).cut(bore)
    add("ElectronicsShell", shell, "Manufactured", (0.025, 0.025, 0.03))
    # Three shallow edge clips retain the unmodified board; no invented PCB holes.
    for i in range(3):
        clip = box(
            6.0, 6, 1.2, 85.5, 0, p["circle_back_z"] + p["circle_pcb_thickness"]
        ).cut(cylinder(1.1, 2, p["circle_back_z"] + 1.5, 85.5, 0))
        clip.rotate(App.Vector(), App.Vector(0, 0, 1), i * 120)
        add("BoardEdgeClip" + str(i), clip, "Manufactured", (0.03, 0.03, 0.035))
        x,y=85.5*math.cos(i*math.tau/3),85.5*math.sin(i*math.tau/3)
        washer=WASHERS['M2']
        wz=p['circle_back_z']+p['circle_pcb_thickness']+1.2
        ring=cylinder(washer['od']/2,washer['thickness'],wz,x,y).cut(cylinder(washer['id']/2,washer['thickness'],wz,x,y))
        add('BoardClipWasher'+str(i),ring,'Hardware',(.4,.4,.42),material='DIN125 M2 washer')
        seat=wz+washer['thickness']
        screw=cylinder(1,8,seat-8,x,y).fuse(cylinder(1.9,2,seat,x,y))
        add('BoardClipScrew'+str(i),screw,'Hardware',(.4,.4,.42),material='DIN912 M2x8; assembly target')
        flats,height=nut_dimensions('M2')
        nut_z=p['circle_back_z']-2-height
        nut=polygon_face(hexagon(85.5,0,flats),nut_z).extrude(App.Vector(0,0,height))
        nut=nut.cut(cylinder(1,height,nut_z,85.5,0))
        nut.rotate(App.Vector(),App.Vector(0,0,1),i*120)
        add('BoardClipNut'+str(i),nut,'Hardware',(.4,.4,.42),material='A4 M2 plain nut')
    frame = annulus(
        d["mirror_seat_radius"],
        R,
        d["front_z"] + p["front_mirror_thickness"] - d["rear_bottom"],
        d["rear_bottom"],
    )
    frame = frame.fuse(
        annulus(d["mirror_lip_radius"], R, 0.8, d["rear_bottom"] - 0.8)
    )
    flute=annulus(96,R+1,d['front_z']+p['front_mirror_thickness']-d['rear_bottom'],d['rear_bottom'])
    for x,y in front_points:
        angle=math.degrees(math.atan2(y,x))
        land=box(12,12,d['front_z']+p['front_mirror_thickness']-d['rear_bottom'],d['front_fastener_radius'],0,d['rear_bottom'])
        land.rotate(App.Vector(),App.Vector(0,0,1),angle)
        flute=flute.cut(land)
    frame=frame.cut(flute)
    nut_flats, nut_height = nut_dimensions("M2")
    pocket_flats, pocket_height = nut_dimensions("M2", pocket=True)
    nut_bottom = d["front_z"] - 1.0
    for x, y in front_points:
        frame = frame.cut(
            cylinder(
                1.1,
                d["front_z"] + p["front_mirror_thickness"] - d["rear_bottom"] + 1,
                d["rear_bottom"] - 0.5,
                x,
                y,
            )
        )
        pocket = polygon_face(hexagon(x, y, pocket_flats), nut_bottom)
        angle = math.degrees(math.atan2(y, x))
        entry = box(
            R + 1 - d["front_fastener_radius"],
            pocket_flats,
            pocket_height,
            (R + 1 + d["front_fastener_radius"]) / 2,
            0,
            nut_bottom,
        )
        entry.rotate(App.Vector(), App.Vector(0, 0, 1), angle)
        frame = frame.cut(pocket.extrude(App.Vector(0, 0, pocket_height)).fuse(entry))
    # One continuous body removes the unfastened frame-to-shell joint.
    body = doc.getObject("ElectronicsShell")
    body.Shape = body.Shape.fuse(frame)
    assert body.Shape.isValid() and len(body.Shape.Solids) == 1
    body.Shape.check(True)
    bezel = annulus(
        p["front_aperture_radius"],
        R,
        p["bezel_thickness"],
        d["front_z"] + p["front_mirror_thickness"],
    )
    bezel_top = d["depth"]
    for x, y in front_points:
        bezel = bezel.cut(
            cylinder(1.1, 3, d["front_z"] + p["front_mirror_thickness"] - 0.5, x, y)
        )
        bezel = bezel.cut(
            Part.makeCone(1.1, 2.0, 0.9, App.Vector(x, y, bezel_top - 0.9))
        )
    add("FrontBezel", bezel, "Manufactured", (0.025, 0.025, 0.03), offset=0.12)
    for i, (x, y) in enumerate(front_points):
        nut_z = nut_bottom + pocket_height - nut_height
        nut = polygon_face(hexagon(x, y, nut_flats), nut_z).extrude(
            App.Vector(0, 0, nut_height)
        )
        nut = nut.cut(cylinder(1.1, nut_height + 0.2, nut_z - 0.1, x, y))
        add(
            "FrontNut" + str(i),
            nut,
            "Hardware",
            (0.4, 0.4, 0.42),
            "hardware",
            "M2 steel nut",
        )
        bolt = cylinder(1.0, 5.1, bezel_top - 6, x, y)
        bolt = bolt.fuse(
            Part.makeCone(1.0, 1.9, 0.9, App.Vector(x, y, bezel_top - 0.9))
        )
        add(
            "FrontBolt" + str(i),
            bolt,
            "Hardware",
            (0.4, 0.4, 0.42),
            "hardware",
            "M2 x 6 countersunk screw",
            0.12,
        )
    # Side diffuser occupies the shell's independent window.
    add(
        "SideDiffuser",
        annulus(
            R - p["side_diffuser_thickness"], R, d["side_height"], p["side_bottom_z"]
        ),
        "Manufactured",
        (0.72, 0.82, 0.54),
        "side",
        "Glow PETG; optical response unmeasured",
    )
    # Inner diffuser seats directly against the rear mirror at its outer feet.
    inner = annulus(
        d["wall_radius"], d["inner_outer"], p["mirror_gap"] - 1, d["rear_z"] + 0.5
    )
    inner = inner.fuse(
        annulus(d["wall_radius"], d["inner_foot_radius"], 0.5, d["rear_z"])
    )
    add(
        "InnerDiffuser",
        inner,
        "Manufactured",
        (0.72, 0.82, 0.54),
        "inner",
        "Glow PETG; optical response unmeasured",
        0.045,
    )
    add(
        "FibonacciPCB",
        cylinder(83, p["circle_pcb_thickness"], p["circle_back_z"]),
        "Electronics",
        (0.025, 0.035, 0.025),
        material="Original 166 mm PCB",
        offset=0.015,
    )
    centres = led_centres(
        json.loads((ROOT / "hardware/enclosure/fibonacci256-layout.json").read_text()),
        p,
    )
    packages = [
        box(5, 5, p["led_height"], x, y, p["circle_back_z"] + p["circle_pcb_thickness"])
        for x, y in centres
    ]
    add(
        "CircleLEDs",
        Part.makeCompound(packages),
        "Optics",
        (0.7, 0.7, 0.6),
        "packages",
        "256 WS2812 packages",
        0.015,
    )
    polygons = baffle.polygons(p)
    wires = [
        Part.makePolygon([App.Vector(x, y, d["baffle_z"]) for x, y in loop + [loop[0]]])
        for loop in polygons
    ]
    stencil = Part.makeFace(wires, "Part::FaceMakerBullseye").extrude(
        App.Vector(0, 0, p["baffle_thickness"])
    )
    assert abs(stencil.Volume - baffle.source_volume()) < 0.02, (
        "Original stencil volume changed"
    )
    add("EGLStencil", stencil, "Manufactured", (0.02, 0.02, 0.025), offset=0.04)
    add(
        "RearCouplingMirror",
        cylinder(
            p["mirror_radius"], p["rear_black_acrylic_thickness"], d["rear_bottom"]
        ),
        "Manufactured",
        (0.025, 0.025, 0.025),
        "rear_mirror",
        "3 mm nominal Black LED acrylic with cavity-facing mirror coating; complete-sheet estimate R70/T9/absorption21; reverse R10/T9; coating unmeasured",
        0.065,
    )
    add(
        "FrontMirror",
        cylinder(p["mirror_radius"], p["front_mirror_thickness"], d["front_z"]),
        "Manufactured",
        (0.35, 0.35, 0.38),
        "mirror",
        "Two-way acrylic mirror; finished-sheet nominal 70% reflection / 30% transmission; coating faces cavity",
        0.10,
    )
    leds = [
        {
            "group": 0,
            "index": i,
            "position_m": [
                x / 1000,
                y / 1000,
                (p["circle_back_z"] + p["circle_pcb_thickness"] + p["led_height"])
                / 1000,
            ],
        }
        for i, (x, y) in enumerate(centres)
    ]
    strips = [(1, "Inner", p["inner_count"], False, d["ring_z"])]
    strips.extend(
        (2 + row, f"Side{row}", p["side_count"], True, z)
        for row, z in enumerate(d["side_row_z"])
    )
    for group, name, count, outward, z in strips:
        pitch_radius = (
            count * 1000 / p["strip_density"] + p["ring_seam_gap"]
        ) / math.tau
        strip = annulus(
            pitch_radius - p["strip_thickness"] / 2,
            pitch_radius + p["strip_thickness"] / 2,
            p["strip_width"],
            z - p["strip_width"] / 2,
        )
        # The strip has its physical seam, not a closed conductive loop.
        seam = box(
            p["ring_seam_gap"],
            5,
            p["strip_width"] + 1,
            0,
            pitch_radius,
            z - p["strip_width"] / 2 - 0.5,
        )
        add(
            name + "Strip",
            strip.cut(seam),
            "Optics",
            (0.03, 0.03, 0.035),
            material="Flexible LED PCB",
            offset=0.04 if group == 1 else 0,
        )
        packages = []
        for i in range(count):
            (x, y), _direction = ring_pixel(count, i, outward, p)
            package = box(
                5,
                p["ring_led_depth"],
                5,
                0,
                pitch_radius
                + (1 if outward else -1)
                * (p["strip_thickness"] / 2 + p["ring_led_depth"] / 2)
                - (0 if outward else 0.05),
                z - 2.5,
            )
            angle = math.degrees(math.atan2(x, y))
            package.rotate(App.Vector(), App.Vector(0, 0, 1), -angle)
            packages.append(package)
            leds.append(
                {
                    "group": group,
                    "index": i,
                    "position_m": [x / 1000, y / 1000, z / 1000],
                }
            )
        add(
            name + "LEDs",
            Part.makeCompound(packages),
            "Optics",
            (0.7, 0.7, 0.6),
            "ring_packages",
            "LED package references",
            0.04 if group == 1 else 0,
        )
    latch_entry=next(e for e in p['electronics'] if e['name']=='PowerLatch')
    latch_local=latch_mount.native_shapes()
    latch_mount.native_check(latch_local)
    latch_delta=App.Vector(*latch_entry['centre'],0)
    rear_obj=doc.getObject('RearCover')
    additions=latch_local['rear_addition'].copy();additions.translate(latch_delta)
    cuts=latch_local['rear_cutout'].copy();cuts.translate(latch_delta)
    rear_obj.Shape=rear_obj.Shape.fuse(additions).cut(cuts).removeSplitter()
    for probe in latch_local['rear_bearing']:
        actual=probe.copy();actual.translate(latch_delta)
        if actual.cut(rear_obj.Shape).Volume>1e-6:raise ValueError('Source latch fixture lacks full rear bearing')
    for name in sorted(latch_mount.PRODUCT_NAMES):
        shape=latch_local[name].copy();shape.translate(latch_delta)
        add(name,shape,'Manufactured' if name in latch_mount.PRINTED_PARTS else 'Electronics',(.15,.3,.2),material='Source-based latch fixture; nominal assembly targets, physical acceptance unmeasured')
    imu_entry=next(e for e in p['electronics'] if e['name']=='IMU')
    imu_local=imu_mount.native_shapes(imu_entry['pcb_bottom_z_mm'],imu_entry['rotation_deg'])
    imu_mount.native_check(imu_local,imu_entry['pcb_bottom_z_mm'])
    imu_delta=App.Vector(*imu_entry['centre'],0)
    additions=imu_local['rear_addition'].copy();additions.translate(imu_delta)
    cuts=imu_local['rear_cutout'].copy();cuts.translate(imu_delta)
    rear_obj.Shape=rear_obj.Shape.fuse(additions).cut(cuts).removeSplitter()
    for probe in imu_local['mount_probes']:
        actual=probe.copy();actual.translate(imu_delta)
        if actual.cut(rear_obj.Shape).Volume>1e-6:raise ValueError('Actual IMU mounting annulus lacks full rear bearing')
    for name in sorted(imu_mount.CHECK_NAMES):
        shape=imu_local[name].copy();shape.translate(imu_delta)
        add(name,shape,'Optics' if name in imu_mount.REFERENCE_NAMES else 'Electronics',(.15,.3,.2),material='Source-hole IMU fixture; nominal assembly targets, physical acceptance unmeasured')
    boost_entry=next(e for e in p['electronics'] if e['name']=='Boost5V')
    boost_local=boost_mount.native_shapes(boost_entry['pcb_bottom_z_mm'],boost_entry['rotation_deg'])
    boost_mount.native_check(boost_local,boost_entry['pcb_bottom_z_mm'],boost_entry['rotation_deg'])
    boost_delta=App.Vector(*boost_entry['centre'],0)
    additions=boost_local['rear_addition'].copy();additions.translate(boost_delta)
    cuts=boost_local['rear_cutout'].copy();cuts.translate(boost_delta)
    rear_obj.Shape=rear_obj.Shape.fuse(additions).cut(cuts).removeSplitter()
    for probe in boost_local['mount_probes']:
        actual=probe.copy();actual.translate(boost_delta)
        if actual.cut(rear_obj.Shape).Volume>1e-6:raise ValueError('Actual PowerBoost mounting annulus lacks full rear bearing')
    for name in sorted(boost_mount.CHECK_NAMES):
        shape=boost_local[name].copy();shape.translate(boost_delta)
        add(name,shape,'Optics' if name in boost_mount.REFERENCE_NAMES else 'Electronics',(.15,.3,.2),material='Source-hole PowerBoost fixture; nominal assembly targets, physical acceptance unmeasured')
    capacitor_entry=next(e for e in p['electronics'] if e['name']=='BulkCapacitor')
    capacitor_local=capacitor_mount.native_shapes('narrow')
    capacitor_mount.native_check(capacitor_local,'narrow')
    capacitor_delta=App.Vector(*capacitor_entry['centre'],0)
    additions=capacitor_local['rear_addition'].copy();additions.translate(capacitor_delta)
    cuts=capacitor_local['rear_cutout'].copy();cuts.translate(capacitor_delta)
    rear_obj.Shape=rear_obj.Shape.fuse(additions).cut(cuts).removeSplitter()
    for probe in capacitor_local['mount_probes']:
        actual=probe.copy();actual.translate(capacitor_delta)
        if actual.cut(rear_obj.Shape).Volume>1e-6:raise ValueError('Actual capacitor hard stop lacks full rear bearing')
    for name in sorted(capacitor_mount.CHECK_NAMES):
        shape=capacitor_local[name].copy();shape.translate(capacitor_delta)
        add(name,shape,'Optics' if name in capacitor_mount.REFERENCE_NAMES else 'Manufactured' if name=='CapacitorCover' else 'Electronics',(.2,.3,.2),material='Source-sized capacitor holder; physical fit, retention and joints unmeasured')
    source_board_fixtures=[]
    for name,factory in (('GPS',gps_mount),('SparkleMotion',sparkle_mount),('BlackPill',blackpill_mount),('Radio',radio_mount)):
        entry=next(e for e in p['electronics'] if e['name']==name)
        local=factory.native_shapes(entry['pcb_bottom_z_mm'],entry['rotation_deg'])
        if factory is radio_mount:
            local=radio_mount.carrier_with_antenna(local,antenna.validate(p,compact=True),entry['mount_datum'])
        factory.native_check(local,entry['pcb_bottom_z_mm'],entry['rotation_deg'])
        delta=App.Vector(*entry['mount_datum'],0)
        additions=local['rear_addition'].copy();additions.translate(delta)
        cuts=local['rear_cutout'].copy();cuts.translate(delta)
        rear_obj.Shape=rear_obj.Shape.fuse(additions).cut(cuts).removeSplitter()
        for probe in local['mount_probes']:
            actual=probe.copy();actual.translate(delta)
            if actual.cut(rear_obj.Shape).Volume>1e-6:raise ValueError(name+' mounting annulus lacks full rear bearing')
        for product in sorted(factory.CHECK_NAMES):
            shape=local[product].copy();shape.translate(delta)
            group='Optics' if product in factory.REFERENCE_NAMES else 'Hardware' if product in factory.HARDWARE_NAMES else 'Manufactured' if product in blackpill_mount.PRINTED_PARTS|radio_mount.PRINTED_PARTS else 'Electronics'
            add(product,shape,group,(.15,.3,.2),material=('Printed PETG; ' if group=='Manufactured' else '')+'Source module fixture; physical fit, retention and joints unmeasured')
        source_board_fixtures.append((local,delta,len(local['nut_paths'])))
    fuse_local=branch_fuses.native_shapes('narrow')
    branch_fuses.native_check(fuse_local,'narrow')
    rear_obj.Shape=rear_obj.Shape.fuse(fuse_local['rear_addition'])
    source_board_fixtures.append((fuse_local,App.Vector(),2))
    # One final cut set owns every void. No later source-fixture union may
    # refill a previously checked bore or nut insertion entry.
    cutters=[cell_parts['rear_cutout'],controls['rear_cutout']]
    all_fixtures=[(latch_local,latch_delta,'rear_bearing'),(imu_local,imu_delta,'mount_probes'),
                  (boost_local,boost_delta,'mount_probes'),(capacitor_local,capacitor_delta,'mount_probes')]
    all_fixtures += [(local,delta,'mount_probes') for local,delta,count in source_board_fixtures]
    for local,delta,probe_key in all_fixtures:
        cut=local['rear_cutout'].copy();cut.translate(delta);cutters.append(cut)
    rear_obj.Shape=rear_obj.Shape.cut(Part.makeCompound(cutters)).removeSplitter()
    if not rear_obj.Shape.isValid() or len(rear_obj.Shape.Solids)!=1:
        raise ValueError('Final source-fixture rear panel is invalid/disconnected')
    for local,delta,probe_key in all_fixtures:
        for probe in local[probe_key]:
            actual=probe.copy();actual.translate(delta)
            if actual.cut(rear_obj.Shape).Volume>1e-6:
                raise ValueError('Source fixture loses bearing after final rear cuts at '+str(delta)+' using '+probe_key)
    for name in sorted(branch_fuses.CHECK_NAMES):
        group='Optics' if name in branch_fuses.REFERENCE_NAMES else 'Hardware' if name in branch_fuses.HARDWARE_NAMES else 'Manufactured' if name in branch_fuses.PRINTED_PARTS else 'Electronics'
        add(name,fuse_local[name],group,(.25,.3,.2),material=('Printed PETG; ' if group=='Manufactured' else '')+'Selected branch fuse carrier; assembly gauges and physical acceptance unmeasured')
    import case_structure
    body=doc.getObject('ElectronicsShell')
    body.Shape,rear_obj.Shape,case_proof=case_structure.lighten(
        body.Shape,rear_obj.Shape,[(o.Name,o.Shape) for o in objects],p,d)
    (out/'case-structure-check.json').write_text(json.dumps(case_proof,indent=2)+'\n')
    # Repeat the independently defined source-fixture bearing probes after
    # case lightening. A mass reduction must preserve every actual support.
    for local,delta,probe_key in all_fixtures:
        for probe in local[probe_key]:
            actual=probe.copy();actual.translate(delta)
            if actual.cut(rear_obj.Shape).Volume>1e-6:raise ValueError('Ribbed rear panel loses source mounting bearing '+str(delta))
    from fastener_access import native_check_paths
    for local,delta,count in [(imu_local,imu_delta,4),(boost_local,boost_delta,2),(capacitor_local,capacitor_delta,2)]+source_board_fixtures:
        paths=[]
        for path in local['nut_paths']:
            actual=path.copy();actual.translate(delta);paths.append(actual)
        native_check_paths(paths,rear_obj.Shape,count)
    import necklace_fixture
    necklace_spec=necklace_fixture.definition(ROOT/'hardware/enclosure/necklace.json')
    necklace_fit=necklace_fixture.native_shapes(body.Shape,d,necklace_spec)
    body.Shape=necklace_fit['case']
    for name,shape in necklace_fit['products'].items():
        add(name,shape,'Electronics',(.025,.025,.03),material='Selected sewn nylon tape; stock counted once in necklace ledger; fitted textile targets and physical acceptance unmeasured')
    necklace_record={key:value for key,value in necklace_fit.items() if key not in {'case','products'}}
    (out/'necklace-fit-check.json').write_text(json.dumps(necklace_record,indent=2)+'\n')
    import end_supports
    input_relief=end_supports.boost_input_pair(body.Shape,p,d)
    for name,shape in input_relief['products'].items():
        add(name,shape,'Manufactured' if name in end_supports.PRINTED_PARTS else 'Electronics',(.025,.025,.03),material='Opaque black PETG' if name in end_supports.PRINTED_PARTS else 'Selected VHB5952 fitted pad or LC134 lacing; physical retention unmeasured')
    (out/'end-support-check.json').write_text(json.dumps({key:value for key,value in input_relief.items() if key!='products'},indent=2)+'\n')
    route = antenna.installation(p, compact=True)
    add('RadioAntenna', antenna_native.wire(route), 'Electronics', (0.0,.45,.7), material='Insulated copper; 78 mm total including feed')
    for obj in groups['Manufactured'].Group:
        obj.Shape.check(True)
    print('NARROW CHECK: complete installed loom',flush=True)
    loom_proof=harness_install.install(objects,p,add)
    (out/'loom-check.json').write_text(json.dumps(loom_proof,indent=2)+'\n')
    print('NARROW CHECK: antenna fit and service',flush=True)
    gaps = antenna_native.check(p, objects, compact=True)
    antenna_native.regression_checks(p,d['depth'],compact=True)
    # Service removes the rear and releases the three carrier screws. The
    # source radio, carrier and restrained wire leave together; disconnect
    # every bridging lead first and support the assembly by hand.
    radio_service={'RearCover','RadioAntenna','BatteryCell'}|radio_mount.CHECK_NAMES
    # Ordinary battery service leaves the entire loom fitted. Radio/rear
    # maintenance requires desoldering/releasing every external wire and
    # removing the loose joint insulation/boots first. Fixed splice carriers
    # stay fitted to the original Fibonacci board; do not omit their geometry.
    removed_for_radio={name for name in loom_proof['parts'] if not name.startswith('HarnessSpliceCarrier')}
    fixed=[(o.Name,o.Shape) for o in objects if o.Name not in radio_service|removed_for_radio]
    # The closed empty door is an actual negative service state. It must
    # remain visible as a required precondition, rather than omit that part.
    try:antenna_native.removal(p,fixed,antenna_native.radio_products(doc),d['depth'],compact=True)
    except ValueError as error:
        prefix='200 mm compact antenna removal: '
        if not str(error).startswith(prefix):raise
        blocked=json.loads(str(error)[len(prefix):])
        if not blocked or any(row['part']!='BatteryDoor' for row in blocked):raise
        closed_door_failure=blocked
    else:raise ValueError('Closed battery door no longer exercises the recorded blocked service state')
    opened_door=battery_access.door_at_open_stop(access,cell_parts)
    fixed=[(name,opened_door if name=='BatteryDoor' else shape) for name,shape in fixed]
    radio_removal=antenna_native.removal(p,fixed,antenna_native.radio_products(doc),d['depth'],compact=True)
    (out/'antenna-service-check.json').write_text(json.dumps({'preconditions':['physical OFF','qualified dwell remains unmeasured','open captive door; release keeper; remove cell; close keeper in empty bay','desolder or unclamp every external loom wire at both ends; release ties and remove loose wires/joints/boots before rear/radio service; fixed PCB-backed splice carriers stay fitted','release rear; support by hand'],
        'door_open_stop_deg':access['door']['open_angle_deg'],'closed_door_rejected':closed_door_failure,'continuous_withdrawal':radio_removal,'physical_acceptance':'unmeasured'},indent=2,allow_nan=False)+'\n')
    antenna_view.export(route, antenna.component_boxes(p, compact=True, include_radio=True), gaps, out/'antenna-placement.svg')
    # Selected source bodies and every fitted wire were checked above.
    status = doc.addObject("App::FeaturePython", "Acceptance")
    status.addProperty(
        "App::PropertyString", "Status"
    ).Status = "Narrow digital prototype: fitted source parts, loom and continuous battery motions checked. Supplied fit, insulation, retention, heat, mass and wearing remain unmeasured."
    doc.recompute()
    # Check real solids, including components against shelves and shell.
    checked = [o for o in objects if o.Name != 'RadioAntenna']  # Dedicated distance and bounded-contact checks above.
    # Geometry is fixed for this census. Cache actual curve bounds only
    #within this block; service motions below do not reuse this cache.
    closed_bounds={obj.Name:bounds(obj.Shape) for obj in objects}
    collisions = []
    for i, a in enumerate(checked):
        print('NARROW PAIR CHECK: '+a.Name,flush=True)
        for b in checked[i + 1 :]:
            if closed_bounds[a.Name].intersect(closed_bounds[b.Name]):
                volume = a.Shape.common(b.Shape).Volume
                if volume > 0.02:
                    collisions.append([a.Name, b.Name, round(volume, 4)])
    if collisions:
        raise ValueError("CAD interference: " + json.dumps(collisions))
    # The200mm dimension describes the rigid body. The four explicit sewn
    #attachment targets can project beyond it and enter the full closed bounds
    #below. They are also checked in all-part fit and ordinary cell service.
    textile_names=necklace_fixture.PART_NAMES
    if not textile_names<={obj.Name for obj in objects}:raise ValueError('Missing fixed necklace geometry')
    body_objects=[obj for obj in objects if obj.Name not in textile_names]
    if max(closed_bounds[o.Name].XMax for o in body_objects)-min(closed_bounds[o.Name].XMin for o in body_objects)>p['case_diameter']+.001:raise ValueError('Rigid narrow body exceeds selected diameter')
    doc.recompute()
    Gui.activeDocument().activeView().viewAxonometric()
    Gui.activeDocument().activeView().fitAll()
    installed=[(o.Name,o.Shape) for o in objects]
    cell_fixed=[(name,shape) for name,shape in installed if name not in battery_access.part_names('narrow')]
    records=[]
    for obj in objects:
        solids=obj.Shape.Solids
        volume=math.fsum(solid.Volume for solid in solids)
        centre=[math.fsum(getattr(solid.CenterOfMass,axis)*solid.Volume for solid in solids)/volume for axis in ('x','y','z')] if volume>0 else None
        group=next((name for name,container in groups.items() if obj in container.Group),'UNKNOWN')
        records.append({'name':obj.Name,'group':group,'volume_cm3':obj.Shape.Volume/1000,
              'centre_mm':centre,'bounds_mm':[getattr(closed_bounds[obj.Name],axis+'Length') for axis in 'XYZ']})
    loom=harness_contract.load()
    lead=battery_leads.layout(access,'narrow')
    variants={}
    for material in ['glow','silver']:
        inventory=narrow_inventory.resolve(records,p,loom,{name:lead for name in ['BatteryLeadP','BatteryLeadN']},material)
        inventory['balance']=mass_core.balance(inventory['components'],[[-d['suspension_x'],d['suspension_y'],necklace_spec['anchor_z_mm']],[d['suspension_x'],d['suspension_y'],necklace_spec['anchor_z_mm']]])
        if not inventory['mass_estimate']['ceiling_pass']:raise ValueError('Narrow worn upper mass exceeds limit for '+material+': '+str(inventory['mass_estimate']))
        if not inventory['balance']['positive_two_point_support_for_mass_range']:raise ValueError('Narrow conditional CG leaves its two suspension supports')
        variants[material]=inventory
        print('NARROW MASS: '+material+' '+json.dumps(inventory['mass_estimate']),flush=True)
    print_data=prints.native_export(doc,out,p,d)
    inventory_record={**print_data,**variants['glow'],'products':records,'material_variants':variants,'parameters_for_inventory':p,'suspension_points_mm':[[-d['suspension_x'],d['suspension_y'],necklace_spec['anchor_z_mm']],[d['suspension_x'],d['suspension_y'],necklace_spec['anchor_z_mm']]],
                      'dimensions_mm':{'diameter':p['case_diameter'],'body_depth':d['depth'],
                      'closed_width':max(closed_bounds[o.Name].XMax for o in objects)-min(closed_bounds[o.Name].XMin for o in objects),
                      'closed_height':max(closed_bounds[o.Name].YMax for o in objects)-min(closed_bounds[o.Name].YMin for o in objects),
                      'closed_depth':max(closed_bounds[o.Name].ZMax for o in objects)-min(closed_bounds[o.Name].ZMin for o in objects),
                      'rear_min_z':min(closed_bounds[o.Name].ZMin for o in objects),'front_max_z':max(closed_bounds[o.Name].ZMax for o in objects),
                      'closed_minimum_mm':[min(getattr(closed_bounds[o.Name],a+'Min') for o in objects) for a in 'XYZ'],
                      'closed_maximum_mm':[max(getattr(closed_bounds[o.Name],a+'Max') for o in objects) for a in 'XYZ'],
                      'scope':'Fitted closed CAD products including textile attachment targets; free neck span has no fixed rigid envelope'},
                      'source_status':'Source nominal geometry and specified fabrication targets; supplied tolerances and physical qualification remain unmeasured'}
    (out/'parts.json').write_text(json.dumps(inventory_record,indent=2,allow_nan=False)+'\n')
    def control_states():
        states={}
        for name in sorted(control_fixture.product_names('narrow')):
            original=controls[name];actual=doc.getObject(name).Shape
            states[name]={'generated_valid':original.isValid(),'generated_solids':len(original.Solids),
                'installed_valid':actual.isValid(),'installed_solids':len(actual.Solids),
                'generated_volume_mm3':original.Volume,'installed_volume_mm3':actual.Volume}
        return states
    controls_before=control_states()
    # Validate the products actually stored by add(), not stale factory
    # intermediates. Keep both states for diagnosis.
    installed_controls={**controls,**{name:doc.getObject(name).Shape for name in control_fixture.product_names('narrow')}}
    print('NARROW CHECK: rear controls before service queries',flush=True)
    controls_early=control_fixture.native_check(installed_controls,installed,design='narrow')
    print('NARROW CHECK: full installed battery service',flush=True)
    battery_result=battery_access.native_check(access,'narrow',cell_parts,surroundings=cell_fixed)
    negative_cut=next(row for row in loom_proof['cut_list'] if row.get('continuous_existing_part')=='BatteryLeadN')
    battery_result['contact_wire_cuts']['BatteryLeadN']={
        'loom_wire':negative_cut['id'],'finished_cut_target_mm':negative_cut['finished_cut_target_mm'],
        'blank_mm':negative_cut['blank_cut_target_mm'],'cut_basis':negative_cut['cut_basis'],
        'instruction':'One continuous conductor through the fixed negative conduit toBOOST.X2.1. Use the full loom cut; do not cut a separate contact tail or add a splice.',
        'physical_acceptance':'unmeasured'}

    controls_after=control_states()
    control_result=control_fixture.native_check(installed_controls,installed,design='narrow')
    invalid=[obj.Name for obj in objects if not obj.Shape.isValid()]
    if invalid:raise ValueError('Final document geometry became invalid: '+str(invalid))
    for obj in groups['Manufactured'].Group:
        obj.Shape.check(True)
    census_volumes={row['name']:row['volume_cm3']*1000 for row in records}
    changed=[obj.Name for obj in objects if abs(obj.Shape.Volume-census_volumes[obj.Name])>1e-6]
    if changed:raise ValueError('Service checks changed installed mass geometry: '+str(changed))
    (out/'installed-fit-check.json').write_text(json.dumps({'battery':battery_result,'controls':control_result},indent=2)+'\n')
    doc.saveAs(str(out / "stacked-fibonacci.FCStd"))
    print('NARROW INSTALLED LOOM AND BATTERY FIT PASS',flush=True)
    inventory_record['service_clearance']=service.native_guide(out,access,cell_parts,installed,controls['finger_probes'])
    inventory_record['dimension_drawing']=service.native_dimensions(out,installed,inventory_record)
    (out/'parts.json').write_text(json.dumps(inventory_record,indent=2,allow_nan=False)+'\n')
    Part.export(objects, str(out / "stacked-fibonacci.step"))
    glb = GLB()
    parts = []
    for o in objects:
        colour = tuple(o.ViewObject.ShapeColor[:3])
        parts.append(
            glb.mesh(
                o.Name,
                o.Shape,
                colour,
                role=o.PreviewRole,
                pixel_centres=centres if o.Name == "CircleLEDs" else None,
            )
        )
        parts[-1]["explosion_offset_m"] = o.ExplodeOffsetM
    glb.save(out / "amulet.glb")
    # Rasterize actual clipped apertures, not an invented replacement stencil.
    image = QtGui.QImage(1024, 1024, QtGui.QImage.Format_RGB32)
    image.fill(QtGui.QColor(0, 0, 0))
    painter = QtGui.QPainter(image)
    painter.setPen(QtCore.Qt.NoPen)
    for i, poly in enumerate(pixel_regions(centres, 83)):
        aperture = polygon_face(poly, d["baffle_z"]).cut(stencil)
        assert aperture.Area > 0 and aperture.common(stencil).Area < 1e-7
        vertices, triangles = aperture.tessellate(0.1)
        painter.setBrush(QtGui.QColor(i, 255, 0))
        for tri in triangles:
            painter.drawPolygon(
                QtGui.QPolygonF(
                    [
                        QtCore.QPointF(
                            1024 * (0.5 + vertices[j].x / 166),
                            1024 * (0.5 - vertices[j].y / 166),
                        )
                        for j in tri
                    ]
                )
            )
    painter.end()
    assert image.save(str(out / "cell-map.png"))
    optics = {
        k: d[k] / 1000
        for k in (
            "source_z",
            "rear_z",
            "front_z",
            "wall_radius",
            "ring_z",
            "pitch_radius",
            "side_radius",
        )
    }
    optics.update(
        side_first_z=d["side_row_z"][0] / 1000,
        side_pitch=p["strip_width"] / 1000,
        side_rows=p["side_rows"],
        side_axial_scatter=p["side_axial_scatter_mm"] / 1000,
    )
    optics.update(
        diffusion=p["diffusion"],
        strip_half_height=0.005,
        source_diameter=0.166,
        rear_external_reflectance=p["rear_external_reflectance"],
    )
    metadata = {
        "format_version": 1,
        "units": "metres",
        "groups": ["Fibonacci", "Inner"]
        + [f"Side{row}" for row in range(p["side_rows"])],
        "counts": [256, p["inner_count"]] + [p["side_count"]] * p["side_rows"],
        "parts": parts,
        "leds": leds,
        "centres_m": [[x / 1000, y / 1000] for x, y in centres],
        "optics": optics,
        "dimensions_m": {
            "diameter": p["case_diameter"] / 1000,
            "body_depth": d["depth"] / 1000,
            "closed_depth":inventory_record["dimensions_mm"]["closed_depth"]/1000,
        },
        "suspension": {
            "anchor_x": abs(necklace_fit["frames"][0]["free_span_entry_mm"][0]) / 1000,
            "anchor_y": necklace_fit["frames"][0]["free_span_entry_mm"][1] / 1000,
            "anchor_z": necklace_fit["frames"][0]["free_span_entry_mm"][2]/1000,
        },
        "comparison": {
            "brightness": p["brightness"],
            "exposure": p["exposure"],
            "diffusion": p["diffusion"],
            "ring_transmission": p["ring_transmission"],
            "front_reflectance": p["front_reflectance"],
            "front_transmission": p["front_transmission"],
            "rear_reflectance": p["rear_reflectance"],
            "rear_transmission": p["rear_transmission"],
            "source_time_s": 2,
            "still_distance_m": 0.6,
            "night_distance_m": 0.46,
            "full_pose_distance_m": 3.5,
            "source_status": "Outer clear mirror uses supplier-nominal R70/T30. Inner coated Black LED acrylic combines source cover and rear mirror: complete-sheet estimate cavity R70/T9/absorption21, reverse R10/T9. First cell image T=.09*.30=.027; do not multiply by black stock T29 again. Custom coating, scattering, RGB, glow and assembly response remain unmeasured. Source brightness and exposure match the first design.",
        },
        "mass_estimate":variants["glow"]["mass_estimate"],
        "balance":variants["glow"]["balance"],
        "ring_materials":json.loads((ROOT/"hardware/enclosure/print-spec.json").read_text())["ring_materials"],
        "acrylic_materials": json.loads(
            (ROOT / "hardware/enclosure/acrylic-optics.json").read_text()
        ),
        "validation": {
            "collisions": collisions,
            "original_stencil_volume_mm3": stencil.Volume,
            "inner_ring_board_clearance_mm": d["wall_radius"] - 83,
            "mirror_gap_mm": p["mirror_gap"],
            "maximum_width_mm": p["case_diameter"],
            "depth_mm": d["depth"],
            "side_band_width_mm": d["side_height"],
            "side_strip_count": p["side_rows"],
            "electronics": "Source parts, selected fixed fixtures and complete routed loom checked digitally. Physical supplied fit, retention, insulation, temperatures and operation remain unmeasured.",
        },
    }
    (out / "scene.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(
        f"STACKED CAD PASS: {p['case_diameter']:g} x {d['depth']:.1f} mm; {len(leds)} LEDs; no solid collisions",
        flush=True,
    )
    App.closeDocument(doc.Name)
