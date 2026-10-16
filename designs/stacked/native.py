"""Native FreeCAD concept: separate optical stack, real-size hardware envelopes."""

import json
import math

import baffle
import FreeCAD as App
import FreeCADGui as Gui
import Part
from demo_export import GLB
from geometry import led_centres, pixel_regions, ring_pixel
from hardware_spec import hexagon, nut_dimensions
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

    def add(
        name, shape, group, colour, role="solid", material="Opaque black PETG", offset=0
    ):
        shape = shape.removeSplitter()
        assert shape.isValid() and shape.Volume > 0, name + " invalid or empty"
        if group == "Manufactured":
            assert len(shape.Solids) == 1, name + " is disconnected"
        obj = doc.addObject("PartDesign::Feature", name)
        obj.Shape = shape
        obj.Label = name
        obj.addProperty(
            "App::PropertyString", "FitStatus"
        ).FitStatus = "Concept only; supplied hardware, coatings and fit unmeasured"
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

    R = p["case_diameter"] / 2
    rear_points = [
        (85 * math.cos(i * math.tau / 6), 85 * math.sin(i * math.tau / 6))
        for i in range(6)
    ]
    front_points = [
        (91.5 * math.cos(i * math.tau / 6), 91.5 * math.sin(i * math.tau / 6))
        for i in range(6)
    ]
    rear = cylinder(R, 2)
    # Six rear M3 screws and four rear ventilation openings; no optical opening.
    for x, y in rear_points:
        rear = rear.cut(cylinder(1.7, 3, -0.5, x, y))
    for x, y in ((-45, 0), (45, 0), (-30, 60), (30, 60)):
        rear = rear.cut(cylinder(3, 3, -0.5, x, y))
    add("RearCover", rear, "Manufactured", (0.025, 0.025, 0.03), offset=-0.035)
    shell = annulus(86, R, d["rear_bottom"] - 2.8, 2)
    shell = shell.cut(
        annulus(
            d["side_radius"] - p["strip_thickness"] / 2,
            R + 1,
            d["side_height"],
            p["side_bottom_z"],
        )
    )
    shell = shell.fuse(annulus(82.5, 88.3, 2, 36))
    # Captive M3 nuts insert from the open rear, below each support post.
    for x, y in rear_points:
        post = cylinder(3, 34, 2, x, y).cut(cylinder(1.7, 35, 1.5, x, y))
        pocket = polygon_face(
            [(x + a, y + b) for a, b in hexagon(0, 0, 5.8)], 2
        ).extrude(App.Vector(0, 0, 2.6))
        shell = shell.fuse(post.cut(pocket))
    for side in (-1, 1):
        slot = box(9, 3, 11, 0, 0, 2)
        slot.rotate(App.Vector(), App.Vector(0, 0, 1), 143 if side == 1 else 37)
        slot.translate(App.Vector(side * 55, 73, 0))
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
        pocket = box(6.1, 4.2, 1.4, 85.25, 0, 39.5)
        boss = cylinder(1.8, 1.6, 38, 85.5, 0)
        bore = cylinder(1.1, 5, 35.5, 85.5, 0)
        for shape in (pocket, boss, bore):
            shape.rotate(App.Vector(), App.Vector(0, 0, 1), i * 120)
        shell = shell.cut(pocket).fuse(boss).cut(bore)
    add("ElectronicsShell", shell, "Manufactured", (0.025, 0.025, 0.03))
    # Three shallow edge clips retain the unmodified board; no invented PCB holes.
    for i in range(3):
        clip = box(5.0, 4, 1.2, 84.8, 0, 39.6).cut(cylinder(1.1, 2, 39.5, 85.5, 0))
        clip.rotate(App.Vector(), App.Vector(0, 0, 1), i * 120)
        add("BoardEdgeClip" + str(i), clip, "Manufactured", (0.03, 0.03, 0.035))
    frame = annulus(
        88.3,
        R,
        d["front_z"] + p["front_mirror_thickness"] - d["rear_bottom"],
        d["rear_bottom"],
    )
    frame = frame.fuse(annulus(87.4, R, 0.8, d["rear_bottom"] - 0.8))
    nut_flats, nut_height = nut_dimensions("M2")
    pocket_flats, pocket_height = nut_dimensions("M2", pocket=True)
    nut_bottom = d["front_z"] - 1.0
    for x, y in front_points:
        frame = frame.cut(cylinder(1.1, 30, d["rear_bottom"] - 0.5, x, y))
        pocket = polygon_face(hexagon(x, y, pocket_flats), nut_bottom)
        angle = math.degrees(math.atan2(y, x))
        entry = box(
            R + 1 - 91.5, pocket_flats, pocket_height, (R + 1 + 91.5) / 2, 0, nut_bottom
        )
        entry.rotate(App.Vector(), App.Vector(0, 0, 1), angle)
        frame = frame.cut(pocket.extrude(App.Vector(0, 0, pocket_height)).fuse(entry))
    # One continuous body removes the unfastened frame-to-shell joint.
    body = doc.getObject("ElectronicsShell")
    body.Shape = body.Shape.fuse(frame).removeSplitter()
    assert body.Shape.isValid() and len(body.Shape.Solids) == 1
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
    inner = inner.fuse(annulus(d["inner_outer"] - 0.05, 87.9, 0.5, d["rear_z"]))
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
    for e in p["electronics"]:
        x, y = e["centre"]
        w, l, h = e["size"]
        z = e["z"]
        colour = (0.18, 0.18, 0.20) if e["name"] == "Battery" else (0.04, 0.22, 0.13)
        add(
            e["name"],
            box(w, l, h, x, y, z),
            "Electronics",
            colour,
            material="Unscaled component envelope",
        )
        if e["name"] == "Battery":
            cradle = box(w + 2, l + 2, 1, x, y, z - 1)
            add("BatteryCradle", cradle, "Manufactured", (0.025, 0.025, 0.03))
        else:
            shelf = box(w + 1, l + 1, 1, x, y, z - 1)
            for sx, sy in ((-1, -1), (1, 1)):
                shelf = shelf.fuse(
                    box(3, 3, z - 3, x + sx * (w / 2 - 2), y + sy * (l / 2 - 2), 2)
                )
            add(e["name"] + "Shelf", shelf, "Manufactured", (0.025, 0.025, 0.03))
    # Cable space remains a reservation, not an invented electrical connector.
    status = doc.addObject("App::FeaturePython", "Acceptance")
    status.addProperty(
        "App::PropertyString", "Status"
    ).Status = "CAD concept: optical coefficients, hardware revisions, shelf fastening, wiring, membrane vents and suspension require physical qualification. Not a print order."
    doc.recompute()
    # Check real solids, including components against shelves and shell.
    checked = objects
    collisions = []
    for i, a in enumerate(checked):
        for b in checked[i + 1 :]:
            if a.Shape.BoundBox.intersect(b.Shape.BoundBox):
                volume = a.Shape.common(b.Shape).Volume
                if volume > 0.02:
                    collisions.append([a.Name, b.Name, round(volume, 4)])
    if collisions:
        raise ValueError("CAD interference: " + json.dumps(collisions))
    assert (
        max(o.Shape.BoundBox.XMax for o in objects)
        - min(o.Shape.BoundBox.XMin for o in objects)
        <= p["case_diameter"] + 0.001
    )
    doc.recompute()
    Gui.activeDocument().activeView().viewAxonometric()
    Gui.activeDocument().activeView().fitAll()
    doc.saveAs(str(out / "stacked-fibonacci.FCStd"))
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
            "electronics": "Unscaled envelopes; GPS rotated 90 degrees. Fastening and wiring remain provisional.",
        },
    }
    (out / "scene.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(
        f"STACKED CAD PASS: 190 x {d['depth']:.1f} mm; {len(leds)} LEDs; no solid collisions",
        flush=True,
    )
    App.closeDocument(doc.Name)
