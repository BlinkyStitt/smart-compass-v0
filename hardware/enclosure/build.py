"""Build a native FreeCAD pendant with no persistent Python feature proxies.

Run through Build.FCMacro in FreeCAD, or with FreeCADCmd and SC_CAD_DIR set.
The saved FCStd spreadsheet owns subsequent builds. parameters.json seeds the
first build only. Exported meshes and laser contours are derived outputs.
"""
import colorsys
import json
import math
import os
from pathlib import Path
import sys

import FreeCAD as App
import Part
import Sketcher

HERE = Path(os.environ.get('SC_CAD_DIR', Path(__file__).resolve().parent))
sys.path.insert(0, str(HERE))
from geometry import led_centres, mask_cells, mounting_points, ring_radius, ring_windows


class Builder:
    def __init__(self, p):
        self.p = p
        self.doc = App.newDocument('SmartCompass')
        self.parts, self.hardware, self.references = [], [], []
        self.sheet = self.doc.addObject('Spreadsheet::Sheet', 'Parameters')
        self.sheet.Label = 'Dimensions - edit values, then run Build.FCMacro'
        self.sheet.set('A1', 'Parameter')
        self.sheet.set('B1', 'Value (mm unless stated)')
        self.sheet.set('C1', 'Input status')
        self.keys = [k for k in p if not k.startswith('_')]
        scalar = {'inner_count', 'outer_count', 'strip_density', 'map_rotation_deg', 'map_mirror_x', 'map_mirror_y', 'sparkle_rotation', 'runtime_hours', 'example_total_current_a', 'example_output_voltage', 'assumed_efficiency'}
        for row, key in enumerate(self.keys, 2):
            self.sheet.set(f'A{row}', key)
            value = int(p[key]) if isinstance(p[key], bool) else p[key]
            self.sheet.set(f'B{row}', '=' + str(value) + ('' if key in scalar else ' mm'))
            self.sheet.setAlias(f'B{row}', key)
            self.sheet.set(f'C{row}', 'Published' if key in {'circle_diameter', 'circle_pcb_thickness', 'sparkle_width', 'sparkle_length', 'blackpill_width', 'blackpill_length'} else 'Provisional')
        self.sheet.setColumnWidth('A', 230)
        self.sheet.setColumnWidth('B', 180)
        self.sheet.setColumnWidth('C', 150)
        self.doc.recompute()
        for name, label in [('Manufactured', 'Manufactured parts'), ('Electronics', 'Electronics and battery - check fitted parts'), ('Optics', 'LED references'), ('Construction', 'Hidden native construction geometry')]:
            group = self.doc.addObject('App::DocumentObjectGroup', name)
            group.Label = label
        self.note = self.doc.addObject('App::FeaturePython', 'InputStatus')
        self.note.addProperty('App::PropertyString', 'Status').Status = 'PROVISIONAL FIT: measure battery, circle registration, strips and supplied board revisions before manufacture.'
        self.note.addProperty('App::PropertyString', 'DimensionStatus').DimensionStatus = json.dumps(p['_status'], sort_keys=True)
        self.note.addProperty('App::PropertyStringList', 'ParameterKeys').ParameterKeys = self.keys

    def expression(self, obj, prop, value):
        if isinstance(value, str):
            obj.setExpression(prop, value)
        else:
            setattr(obj, prop, value)

    def style(self, obj, color, alpha=0):
        if App.GuiUp:
            obj.ViewObject.ShapeColor = color
            obj.ViewObject.LineColor = (.12, .12, .12)
            obj.ViewObject.Transparency = alpha

    def hide(self, obj):
        if App.GuiUp:
            obj.Visibility = False

    def cylinder(self, name, radius, height, z=0, x=0, y=0):
        obj = self.doc.addObject('Part::Cylinder', name)
        for key, value in [('Radius', radius), ('Height', height), ('Placement.Base.x', x), ('Placement.Base.y', y), ('Placement.Base.z', z)]:
            if '.' in key:
                if isinstance(value, str):
                    obj.setExpression(key, value)
                else:
                    axis = key[-1]
                    pl = obj.Placement
                    v = pl.Base
                    setattr(v, axis, value)
                    pl.Base = v
                    obj.Placement = pl
            else:
                self.expression(obj, key, value)
        return obj

    def box(self, name, length, width, height, x, y, z):
        obj = self.doc.addObject('Part::Box', name)
        for key, value in [('Length', length), ('Width', width), ('Height', height)]:
            self.expression(obj, key, value)
        for axis, value in zip('xyz', (x, y, z)):
            if isinstance(value, str):
                obj.setExpression('Placement.Base.' + axis, value)
            else:
                pl = obj.Placement
                v = pl.Base
                setattr(v, axis, value)
                pl.Base = v
                obj.Placement = pl
        return obj

    def cut(self, name, base, tools):
        tool = self.compound(name + 'Tools', tools) if isinstance(tools, list) else tools
        obj = self.doc.addObject('Part::Cut', name)
        obj.Base, obj.Tool = base, tool
        obj.Refine = True
        self.hide(base)
        self.hide(tool)
        return obj

    def compound(self, name, objects):
        obj = self.doc.addObject('Part::Compound', name)
        obj.Links = objects
        for item in objects:
            self.hide(item)
        return obj

    def fuse(self, name, objects):
        obj = self.doc.addObject('Part::MultiFuse', name)
        obj.Shapes = objects
        obj.Refine = True
        for item in objects:
            self.hide(item)
        return obj

    def annulus(self, name, inner, outer, z, height):
        return self.cut(name, self.cylinder(name + 'Outer', outer, height, z), self.cylinder(name + 'Inner', inner, height, z))

    def profile(self, name, polygons, z, height):
        sketch = self.doc.addObject('Sketcher::SketchObject', name + 'Sketch')
        for polygon in polygons:
            for a, b in zip(polygon, polygon[1:] + polygon[:1]):
                sketch.addGeometry(Part.LineSegment(App.Vector(*a, 0), App.Vector(*b, 0)), False)
        # Native sketches remain editable; absolute XY follows the installed PCB.
        if isinstance(z, str):
            sketch.setExpression('Placement.Base.z', z)
        else:
            sketch.Placement = App.Placement(App.Vector(0, 0, z), App.Rotation())
        obj = self.doc.addObject('Part::Extrusion', name)
        obj.Base, obj.DirMode, obj.Solid = sketch, 'Normal', True
        self.expression(obj, 'LengthFwd', height)
        self.hide(sketch)
        return obj

    def add(self, obj, group, label, color, alpha=0, material=None):
        obj.Label = label
        obj.addProperty('App::PropertyString', 'FitStatus').FitStatus = 'PROVISIONAL - see InputStatus and README'
        obj.addProperty('App::PropertyString', 'Role').Role = group
        if material:
            obj.addProperty('App::PropertyString', 'Material').Material = material
        self.doc.getObject(group).addObject(obj)
        self.style(obj, color, alpha)
        if group == 'Manufactured':
            self.parts.append(obj)
        elif group == 'Electronics':
            self.hardware.append(obj)
        else:
            self.references.append(obj)
        return obj


def read_parameters(master):
    p = json.loads((HERE / 'parameters.json').read_text())
    if master.exists():
        old = App.openDocument(str(master))
        for key in old.InputStatus.ParameterKeys:
            value = old.Parameters.getPropertyByName(key)
            quantity = value.Value if hasattr(value, 'Value') else float(value)
            p[key] = bool(quantity) if isinstance(p[key], bool) else quantity
        App.closeDocument(old.Name)
    return p


def build():
    master = HERE / 'smart-compass.FCStd'
    p = read_parameters(master)
    validate_parameters(p)
    b = Builder(p)
    doc = b.doc
    E = lambda key: 'Parameters.' + key
    depth, wall, rear = p['case_depth'], p['shell_wall'], p['rear_thickness']
    wood_z = depth - p['front_bezel_thickness'] - p['acrylic_thickness'] - p['wood_thickness']
    wood_expr = E('case_depth') + '-' + E('front_bezel_thickness') + '-' + E('acrylic_thickness') + '-' + E('wood_thickness')
    radius = p['case_diameter'] / 2
    centres = led_centres(json.loads((HERE / 'fibonacci256-layout.json').read_text()), p)
    cells = mask_cells(centres, p['mask_edge_radius'], p['mask_web'])
    windows = ring_windows(p['inner_window_inner_radius'], p['inner_window_outer_radius']) + ring_windows(p['outer_window_inner_radius'], p['outer_window_outer_radius'])
    points = mounting_points(p)
    # Rev D Eagle coordinates, rotated about the actual outline centre.
    a = math.radians(p['sparkle_rotation'])
    sparkle_holes = [(dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a))
                     for dx, dy in [(x - 25.4, y - 16.5735) for x in (2.54, 48.26) for y in (2.54, 30.48)]]
    holes = lambda name, z, height: [b.cylinder(f'{name}{i}', E('fastener_hole_radius'), height, z, x, y) for i, (x, y) in enumerate(points)]

    # One printable optical frame carries the circle, both wrapped strips and lid posts.
    shell = b.annulus('Barrel', E('case_diameter') + '/2-' + E('shell_wall'), E('case_diameter') + '/2', E('rear_thickness'), wood_expr + '-' + E('rear_thickness'))
    floor = b.annulus('RingFloor', 'Parameters.circle_diameter/2+0.5 mm', 'Parameters.case_diameter/2-Parameters.shell_wall+0.5 mm', E('strip_bottom_z') + '-2 mm', 2)
    boundary = b.annulus('CircleBoundary', 'Parameters.circle_diameter/2+0.5 mm', 'Parameters.circle_diameter/2+2.5 mm', E('strip_bottom_z'), wood_expr + '-' + E('strip_bottom_z'))
    ledge = b.annulus('CircleEdgeLedge', 'Parameters.circle_diameter/2-3 mm', 'Parameters.circle_diameter/2+1 mm', E('circle_back_z') + '-1.4 mm', 1.4)
    # The ledge joins the ring floor through three rear ribs, away from PCB LEDs.
    ribs = []
    for i in range(3):
        angle = i * math.tau / 3
        rib = b.box(f'CircleSupportRib{i}', 5, 5, E('circle_back_z') + '-' + E('strip_bottom_z'), 80 * math.cos(angle) - 2.5, 80 * math.sin(angle) - 2.5, E('strip_bottom_z'))
        ribs.append(rib)
    walls = []
    for name, count in [('Inner', p['inner_count']), ('Outer', p['outer_count'])]:
        r = ring_radius(count, p)
        walls.append(b.annulus(name + 'StripWall', r + p['strip_thickness'] / 2, r + p['strip_thickness'] / 2 + 2.4, E('strip_bottom_z'), wood_expr + '-' + E('strip_bottom_z')))
    posts = [b.cylinder(f'LidPost{i}', E('post_radius'), wood_expr + '-' + E('rear_thickness'), E('rear_thickness'), x, y) for i, (x, y) in enumerate(points)]
    frame = b.fuse('FrameBlank', [shell, floor, boundary, ledge] + ribs + walls + posts)
    # Service windows have actual passages through the barrel.
    ports = [b.box('SparkleUSBPowerPort', 35, 38, 17, 88, 17, 5), b.box('RadioPort', 25, 12, 12, -125, 20, 7), b.box('PowerSwitchPort', 16, 25, 12, 28, -130, 7)]
    for i, x in enumerate((-35, 35)):
        port = b.cylinder(f'ControlPort{i}', 4.1, 25, 13, x, 125)
        port.Placement = App.Placement(port.Placement.Base, App.Rotation(App.Vector(1, 0, 0), 90))
        ports.append(port)
    for i in range(12):
        a = math.radians(i * 30)
        if i in (0, 1, 5, 6, 9):
            continue
        v = b.box(f'BarrelVent{i}', 12, 4, 5, radius - 8, -2, 15)
        v.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(App.Vector(0, 0, 1), math.degrees(a))).multiply(v.Placement)
        ports.append(v)
    frame = b.cut('OpticalFrame', frame, holes('FrameBore', rear, wood_z - rear) + ports)
    b.add(frame, 'Manufactured', '01 Optical frame - circle edge seat, ring walls, vents and service ports', (.15, .17, .20), material='Printed opaque polymer; optical channels white-lined')

    # Six full-length M3 bolts and rear nuts clamp the complete stack.
    back = b.cylinder('RearBlank', E('case_diameter') + '/2-' + E('fit_clearance'), E('rear_thickness'))
    vent_slots = [b.box(f'RearVent{i}', 48, 3, rear + 2, -24, 8 + i * 7, -1) for i in range(6)]
    back = b.cut('RearVentPlate', back, holes('RearHole', -1, rear + 2) + vent_slots)
    # Lugs are integral with the rear plate. The eye passes through both layers.
    lugs = [b.box(f'LugBlank{i}', 18, 15, 6, x - 9, 54.5, rear) for i, x in enumerate((-82, 82))]
    back = b.fuse('RearPlateWithLugs', [back] + lugs)
    eyes = [b.cylinder(f'LugEye{i}', 3, rear + 7, -0.5, x, 62) for i, x in enumerate((-82, 82))]
    back = b.cut('RearPlate', back, eyes)
    b.add(back, 'Manufactured', '02 Rear plate - integral necklace eyes, six bolt holes and vents', (.20, .22, .25), material='Printed polymer; attachment needs physical load check')

    carrier_items = []
    # Battery is a restrained envelope, not an electrical cell-holder design.
    bx, by, bw, bl = p['battery_x'], p['battery_y'], p['battery_width'], p['battery_length']
    battery_outer = b.box('BatteryCradleOuter', E('battery_width') + '+4 mm', E('battery_length') + '+4 mm', 7, E('battery_x') + '-' + E('battery_width') + '/2-2 mm', E('battery_y') + '-' + E('battery_length') + '/2-2 mm', rear)
    battery_cavity = b.box('BatteryCradleCavity', E('battery_width') + '+1 mm', E('battery_length') + '+1 mm', 8, E('battery_x') + '-' + E('battery_width') + '/2-0.5 mm', E('battery_y') + '-' + E('battery_length') + '/2-0.5 mm', rear + 1.5)
    cradle = b.cut('BatteryCradle', battery_outer, battery_cavity)
    strap_slots = []
    for i, x in enumerate((bx - bw / 3, bx + bw / 3)):
        for j, y in enumerate((by - bl / 2 - 2, by + bl / 2 - 2)):
            strap_slots.append(b.box(f'StrapSlot{i}{j}', 11, 4, 3, x - 5.5, y, rear + 2))
    cradle = b.cut('BatteryStrapSlots', cradle, strap_slots)
    b.add(cradle, 'Manufactured', '03 Battery cradle - two 10 mm hook-and-loop straps', (.20, .22, .25), material='Printed polymer with insulating padding')

    for key, label, color in [('sparkle', 'Sparkle Motion Rev D', (.12, .35, .20)), ('blackpill', 'BlackPill V3.1', (.08, .10, .13)), ('gps', 'GPS FeatherWing placeholder', (.16, .35, .20)), ('imu', 'LSM9DS1 breakout placeholder', (.15, .36, .20)), ('radio', 'RF95 carrier placeholder', (.20, .32, .22)), ('sense', 'Battery divider board placeholder', (.32, .26, .16))]:
        x, y, w, l = [p[key + '_' + suffix] for suffix in ('x', 'y', 'width', 'length')]
        if key == 'sparkle':
            for i, (dx, dy) in enumerate(sparkle_holes):
                standoff = b.cut(f'SparkleStandoff{i}', b.cylinder(f'SparkleStandBlank{i}', 2.5, 4, rear, x + dx, y + dy), b.cylinder(f'SparkleScrewHole{i}', 1.1, 4, rear, x + dx, y + dy))
                carrier_items.append(standoff)
        else:
            # Open-ended rails avoid guessed mounting holes; straps retain each board.
            for side in (-1, 1):
                start = x + w / 2 - 1 if side == 1 else x - w / 2 - 2.5
                foot = b.box(f'{key}Foot{side:+}', 3.5, l + 4, 4, start, y - l / 2 - 2, rear)
                wall = b.box(f'{key}Wall{side:+}', 2, l + 4, 7, x + side * (w / 2 + 1.5) - 1, y - l / 2 - 2, rear)
                rail = b.fuse(f'{key}Rail{side:+}', [foot, wall])
                slot = b.box(f'{key}TieSlot{side:+}', 6, 6, 1.5, start - 1, y - 3, rear + 1)
                carrier_items.append(b.cut(f'{key}TieRail{side:+}', rail, slot))
        pcb = b.box(key + 'PCB', w, l, 1.6, x - w / 2, y - l / 2, rear + 4)
        if key == 'sparkle':
            pcb = b.cut('SparklePCBWithHoles', pcb, [b.cylinder(f'SparklePCBHole{i}', 1.25, 1.6, rear + 4, x + dx, y + dy) for i, (dx, dy) in enumerate(sparkle_holes)])
        b.add(pcb, 'Electronics', label + ' - PCB footprint', color)
        env = b.box(key + 'Components', w - 4, l - 4, p[key + '_height'] - 1.6, x - w / 2 + 2, y - l / 2 + 2, rear + 5.6)
        b.add(env, 'Optics', label + ' - component clearance envelope', (.85, .55, .18), 70)
    # Small discrete supports are separate printable solids on a single sprue-free export.
    mounts = b.compound('BoardMounts', carrier_items)
    b.add(mounts, 'Manufactured', '04 Board rails and Sparkle M2.5 standoffs - bond to rear tray', (.20, .22, .25), material='Printed polymer; nonmagnetic screws and 5 mm retention straps')
    battery = b.box('BatteryEnvelope', E('battery_width'), E('battery_length'), E('battery_height'), E('battery_x') + '-' + E('battery_width') + '/2', E('battery_y') + '-' + E('battery_length') + '/2', rear + 1.5)
    b.add(battery, 'Electronics', f'Battery envelope - {bw:g} x {bl:g} x {p["battery_height"]:g} mm PLACEHOLDER', (.26, .36, .48), 30)
    battery.addProperty('App::PropertyString', 'ElectricalStatus').ElectricalStatus = 'No cell topology/BMS/charger/regulator selected. Six-hour animated runtime requires measured watts and usable Wh.'
    for i, x in enumerate((-35, 35)):
        body = b.cylinder(f'ButtonBody{i}', 5.5, 6, 13, x, 106)
        body.Placement = App.Placement(body.Placement.Base, App.Rotation(App.Vector(1, 0, 0), 90))
        b.add(body, 'Optics', ('Mode' if i == 0 else 'Action') + ' button body - placeholder', (.4, .4, .4))
        tip = b.cylinder(f'ButtonActuator{i}', 4, 15, 13, x, 121)
        tip.Placement = App.Placement(tip.Placement.Base, App.Rotation(App.Vector(1, 0, 0), 90))
        b.add(tip, 'Optics', ('Mode' if i == 0 else 'Action') + ' button actuator - placeholder', (.7, .7, .7))

    circle = b.cylinder('CirclePCB', E('circle_diameter') + '/2', E('circle_pcb_thickness'), E('circle_back_z'))
    b.add(circle, 'Electronics', 'Fibonacci256 - 166 x 1.6 mm PCB, no guessed mounting holes', (.09, .30, .18))
    led_shapes = []
    for x, y in centres:
        led_shapes.append(Part.makeBox(5, 5, p['led_height'], App.Vector(x - 2.5, y - 2.5, p['circle_back_z'] + p['circle_pcb_thickness'])))
    leds = doc.addObject('Part::Feature', 'CircleLEDs')
    leds.Shape = Part.makeCompound(led_shapes)
    b.add(leds, 'Optics', '256 LED positions - published map, provisional millimetre registration', (.93, .89, .65))
    if App.GuiUp:
        leds.ViewObject.DiffuseColor = [colorsys.hsv_to_rgb(i / 256, .65, .95) for i in range(256) for _ in range(6)]
    for name, count in [('Inner', int(p['inner_count'])), ('Outer', int(p['outer_count']))]:
        r = ring_radius(count, p)
        strip = b.annulus(name + 'Strip', r - p['strip_thickness'] / 2, r + p['strip_thickness'] / 2, E('strip_bottom_z'), E('strip_width'))
        strip = b.cut(name + 'StripSeam', strip, b.box(name + 'SeamGap', E('ring_seam_gap'), 8, E('strip_width'), -p['ring_seam_gap'] / 2, r - 4, E('strip_bottom_z')))
        b.add(strip, 'Electronics', f'{name} ring - {count} pixels, wrapped strip, top seam', (.15, .15, .15))
        shapes = []
        pitch = 1000 / p['strip_density']
        for i in range(count):
            angle = (p['ring_seam_gap'] / 2 + (i + .5) * pitch) / r
            x, y = (r - 1) * math.sin(angle), (r - 1) * math.cos(angle)
            shape = Part.makeBox(2, 5, 5, App.Vector(-1, -2.5, -2.5))
            shape.Placement = App.Placement(App.Vector(x, y, p['strip_bottom_z'] + p['strip_width'] / 2), App.Rotation(App.Vector(0, 0, 1), -math.degrees(angle) - 90))
            shapes.append(shape)
        obj = doc.addObject('Part::Feature', name + 'LEDs')
        obj.Shape = Part.makeCompound(shapes)
        b.add(obj, 'Optics', f'{name} ring LED references - inward facing', (.85, .65, .30))

    # Cell baffle and wood share exactly the same XY opening sketch.
    openings = b.profile('FibonacciApertures', cells, wood_expr, E('wood_thickness'))
    ring_openings = b.profile('RingWindows', windows, wood_expr, E('wood_thickness'))
    wood = b.cylinder('WoodBlank', 'Parameters.case_diameter/2-2.5 mm', E('wood_thickness'), wood_expr)
    wood = b.cut('WoodMask', wood, [openings, ring_openings] + holes('WoodHole', wood_z, p['wood_thickness']))
    b.add(wood, 'Manufactured', '06 Laser-cut wood - 256 Fibonacci cells, simple ring windows', (.53, .32, .13), material='3 mm nominal wood; measure thickness and kerf')
    baffle_z = p['circle_back_z'] + p['circle_pcb_thickness'] + p['led_height'] + .2
    baffle_openings = b.profile('BaffleApertures', cells, baffle_z, wood_z - baffle_z)
    baffle = b.cut('BaffleCells', b.cylinder('BaffleBlank', p['circle_diameter']/2, wood_z - baffle_z, baffle_z), baffle_openings)
    # Three rim feet hold the PCB down. Select clear positions against the LED
    # package references rather than covering an assumed empty edge sector.
    feet = []
    top = p['circle_back_z'] + p['circle_pcb_thickness']
    for i in range(3):
        for delta in [0] + [s*d for d in range(1, 41) for s in (-1, 1)]:
            angle = i*120 + delta
            trial = Part.makeBox(2, 4, baffle_z-top, App.Vector(p['circle_diameter']/2-2, -2, top))
            trial.rotate(App.Vector(), App.Vector(0, 0, 1), angle)
            if trial.common(leds.Shape).Volume < 1e-7:
                foot = b.box(f'CircleRimFoot{i}', 2, 4, baffle_z-top, p['circle_diameter']/2-2, -2, top)
                foot.Placement = App.Placement(App.Vector(), App.Rotation(App.Vector(0,0,1), angle)).multiply(foot.Placement)
                feet.append(foot)
                break
        else:
            raise ValueError('No clear PCB rim retention position')
    baffle = b.fuse('CellBaffle', [baffle] + feet)
    b.add(baffle, 'Manufactured', '07 Light-isolation baffle - Fibonacci cells and three PCB rim feet', (.12, .12, .13), material='Printed opaque polymer')
    acrylic = b.cylinder('AcrylicBlank', 'Parameters.case_diameter/2-2.5 mm', E('acrylic_thickness'), wood_expr + '+' + E('wood_thickness'))
    acrylic = b.cut('FrontAcrylic', acrylic, holes('AcrylicHole', wood_z + p['wood_thickness'], p['acrylic_thickness']))
    b.add(acrylic, 'Manufactured', '08 Front acrylic - wood lies directly behind it', (.80, .88, .92), 80, material='3 mm LED diffuser acrylic; actual transmission unknown')
    bezel = b.annulus('BezelBlank', 'Parameters.case_diameter/2-9.5 mm', E('case_diameter') + '/2', E('case_depth') + '-' + E('front_bezel_thickness'), E('front_bezel_thickness'))
    bezel = b.cut('FrontBezel', bezel, holes('BezelHole', depth - p['front_bezel_thickness'], p['front_bezel_thickness']))
    b.add(bezel, 'Manufactured', '09 Front bezel - captures acrylic and wood with six M3 screws', (.15, .17, .20), material='Printed polymer')

    doc.recompute()
    # Keep all tools in one hidden construction group, with top-level products visible.
    products = set(b.parts + b.hardware + b.references)
    for obj in doc.Objects:
        if obj.isDerivedFrom('Part::Feature') and obj not in products:
            doc.Construction.addObject(obj)
            b.hide(obj)
    if App.GuiUp:
        for obj in products:
            obj.Visibility = True
        # Envelopes are retained in the tree, hidden in the normal assembled view.
        for obj in b.references:
            if 'Components' in obj.Name:
                b.hide(obj)
        import FreeCADGui as Gui
        Gui.activeDocument().activeView().viewAxonometric()
        Gui.activeDocument().activeView().fitAll()
    doc.recompute()
    check_model(b, centres, cells)
    doc.saveAs(str(master))
    export_files(b, centres, cells, windows, points)
    print('CAD BUILD PASS:', master)
    return b


def validate_parameters(p):
    if not (0 < p['assumed_efficiency'] <= 1):
        raise ValueError('Efficiency must lie in (0,1]')
    for key in ('inner_count', 'outer_count'):
        if int(p[key]) != p[key] or not 1 <= p[key] <= 512:
            raise ValueError('Ring counts must be integers in 1..512')
    if p['sparkle_rotation'] not in (0, 180):
        raise ValueError('The axis-aligned Sparkle footprint supports rotations 0 or 180 only')
    for key in ('battery_width', 'battery_length', 'battery_height', 'strip_density', 'mask_web'):
        if p[key] <= 0 or not math.isfinite(p[key]):
            raise ValueError(key + ' must be finite and positive')
    led_top = p['circle_back_z'] + p['circle_pcb_thickness'] + p['led_height']
    wood_z = p['case_depth'] - p['front_bezel_thickness'] - p['acrylic_thickness'] - p['wood_thickness']
    if led_top + .2 >= wood_z:
        raise ValueError('No light-baffle gap below the wood')
    if p['rear_thickness'] + 1.5 + p['battery_height'] + 1 >= p['circle_back_z']:
        raise ValueError('Battery leaves less than 1 mm rear PCB clearance')
    if math.hypot(abs(p['battery_x']) + p['battery_width'] / 2 + 2, abs(p['battery_y']) + p['battery_length'] / 2 + 2) >= p['case_diameter'] / 2 - p['shell_wall']:
        raise ValueError('Battery cradle is outside the shell')


def check_model(b, centres, cells):
    bad = [(o.Name, list(o.State)) for o in b.doc.Objects if 'Invalid' in o.State or 'Error' in o.State]
    if bad:
        raise ValueError('Invalid document objects: ' + repr(bad))
    for obj in b.parts + b.hardware + b.references:
        if obj.Shape.isNull() or not obj.Shape.isValid() or obj.Shape.Volume <= 0:
            raise ValueError('Invalid solid geometry: ' + obj.Name)
    if len(b.doc.WoodMask.Shape.Solids) != 1:
        raise ValueError('Wood mask contains detached islands')
    for name in ('OpticalFrame', 'RearPlate', 'CellBaffle'):
        if len(b.doc.getObject(name).Shape.Solids) != 1:
            raise ValueError(name + ' is not one connected printable part')
    if len(centres) != 256 or len(cells) != 256:
        raise ValueError('Circle mask must preserve 256 LED apertures')
    # Intersections of separate manufactured parts and hardware are defects.
    # References are not measured solids; board rails/lugs meet the rear plate by design.
    objects = b.parts + b.hardware
    failures = []
    for i, a in enumerate(objects):
        for other in objects[i + 1:]:
            ab, bb = a.Shape.BoundBox, other.Shape.BoundBox
            if any(min(getattr(ab, axis+'Max'), getattr(bb, axis+'Max')) - max(getattr(ab, axis+'Min'), getattr(bb, axis+'Min')) <= 1e-7 for axis in 'XYZ'):
                continue
            volume = a.Shape.common(other.Shape).Volume
            if volume > .05:
                failures.append((a.Name, other.Name, round(volume, 4)))
    if failures:
        raise ValueError('Unintended assembly collisions (mm^3): ' + repr(failures))
    print('CAD geometry checks: valid products, connected frame/mask and no product collisions')


def export_files(b, centres, cells, windows, points):
    out = HERE / 'exports'
    out.mkdir(exist_ok=True)
    Part.export(b.parts + b.hardware + [b.doc.CircleLEDs, b.doc.InnerLEDs, b.doc.OuterLEDs], str(out / 'smart-compass.step'))
    import Mesh
    for obj in b.parts:
        if obj.Name not in {'WoodMask', 'FrontAcrylic'}:
            Mesh.export([obj], str(out / (obj.Name + '.stl')))
    svg_files(b.p, cells, windows, points, out)
    section_drawing(b, out)
    if App.GuiUp:
        export_previews(b, out)


def section_drawing(b, out):
    """Cut actual native solids at Y=0; X is horizontal and Z is vertical."""
    r, depth = b.p['case_diameter']/2, b.p['case_depth']
    corners = [App.Vector(-r-10,0,-10), App.Vector(r+10,0,-10), App.Vector(r+10,0,depth+10), App.Vector(-r-10,0,depth+10)]
    plane = Part.Face(Part.makePolygon(corners + corners[:1]))
    paths = []
    for obj in b.parts + b.hardware:
        for edge in obj.Shape.section(plane).Edges:
            pts = edge.discretize(Deflection=.08)
            paths.append('<polyline points="' + ' '.join(f'{pt.x:.5f},{-pt.z:.5f}' for pt in pts) + '"/>')
    drawing = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{2*r+40}mm" height="{depth+45}mm" viewBox="{-r-15} {-depth-22} {2*r+40} {depth+45}">
<title>Native solid section at Y=0; all dimensions mm; provisional fit</title>
<g fill="none" stroke="#222" stroke-width="0.15">{''.join(paths)}</g>
<g fill="none" stroke="#1765a1" stroke-width="0.2">
<path d="M {-r},10 H {r} M {-r},7 V 13 M {r},7 V 13 M {r+12},0 V {-depth} M {r+9},0 H {r+15} M {r+9},{-depth} H {r+15}"/>
</g><g font-family="sans-serif" font-size="3.5" fill="#1765a1">
<text x="-10" y="9">Ø {2*r:g}</text><text x="{r+14}" y="{-depth/2}">{depth:g}</text>
<text x="{-r}" y="{-depth-13}">Y=0 section • rear Z=0 • front Z={depth:g} • nominal geometry</text>
<text x="{-r}" y="20">Top stack: baffle → 3 mm wood → 3 mm acrylic → bezel. See README for all Z levels.</text>
</g></svg>'''
    (out / 'assembly-section.svg').write_text(drawing)


def svg_files(p, cells, windows, points, out):
    # Nominal design contours. Apply measured kerf once in the laser CAM software.
    r = p['case_diameter'] / 2 - 2.5
    def document(paths, description):
        return '<svg xmlns="http://www.w3.org/2000/svg" width="%gmm" height="%gmm" viewBox="%g %g %g %g">\n<title>%s</title>\n<desc>PROVISIONAL alignment and material fit; nominal paths, no kerf compensation. Front view, X right, Y up.</desc>\n<g transform="scale(1,-1)" fill="none" stroke="#ff0000" stroke-width="0.08">\n%s\n</g></svg>\n' % (2*r, 2*r, -r, -r, 2*r, 2*r, description, '\n'.join(paths))
    outline = f'<circle cx="0" cy="0" r="{r:.6f}"/>'
    holes = [f'<circle cx="{x:.6f}" cy="{y:.6f}" r="{p["fastener_hole_radius"]:.6f}"/>' for x, y in points]
    polygons = ['<polygon points="' + ' '.join(f'{x:.6f},{y:.6f}' for x,y in poly) + '"/>' for poly in cells + windows]
    (out / 'wood-fibonacci-mask.svg').write_text(document([outline] + holes + polygons, 'Wood mask - 256 Fibonacci cells plus simple ring windows'))
    (out / 'front-acrylic.svg').write_text(document([outline] + holes, 'Front acrylic - 3 mm nominal'))
    # The inspection overlay never enters a laser cut file.
    overlay = [outline, f'<circle cx="0" cy="0" r="{p["circle_diameter"]/2:.6f}"/>', '<path d="M -50,-110 L 50,-110 M -50,-108 L -50,-112 M 50,-108 L 50,-112"/>'] + polygons[:256] + [f'<circle cx="{x:.6f}" cy="{y:.6f}" r="0.5"/>' for x,y in led_centres(json.loads((HERE/'fibonacci256-layout.json').read_text()),p)]
    (out / 'circle-alignment-overlay.svg').write_text(document(overlay, 'Print at 100 percent and check 166 mm circle / LED registration'))


def export_previews(b, out):
    import FreeCADGui as Gui
    view = Gui.activeDocument().activeView()
    Gui.updateGui()
    view.viewTop()
    view.fitAll()
    view.saveImage(str(out / 'front.png'), 1400, 1400, 'White')
    view.viewAxonometric()
    view.fitAll()
    view.saveImage(str(out / 'assembly.png'), 1600, 1400, 'White')
    # A real exploded placement, saved only in the preview, never in the master.
    moved = []
    for name, offset in [('FrontBezel', 65), ('FrontAcrylic', 50), ('WoodMask', 35), ('CellBaffle', 20)]:
        obj = b.doc.getObject(name)
        moved.append((obj, obj.Placement))
        pl = obj.Placement
        pl.Base.z += offset
        obj.Placement = pl
    b.doc.recompute()
    Gui.updateGui()
    view.fitAll()
    view.saveImage(str(out / 'exploded.png'), 1600, 1400, 'White')
    for obj, pl in moved:
        obj.Placement = pl
    b.doc.recompute()
    # Reveal the battery and boards through the back for a clear packaging view.
    hidden = [b.doc.OpticalFrame, b.doc.FrontBezel, b.doc.FrontAcrylic, b.doc.WoodMask, b.doc.CellBaffle, b.doc.CirclePCB, b.doc.CircleLEDs, b.doc.InnerLEDs, b.doc.OuterLEDs, b.doc.InnerStripSeam, b.doc.OuterStripSeam]
    for obj in hidden:
        obj.Visibility = False
    Gui.updateGui()
    view.viewTop()
    view.fitAll()
    view.saveImage(str(out / 'electronics.png'), 1400, 1400, 'White')
    for obj in hidden:
        obj.Visibility = True
    view.viewAxonometric()
    view.fitAll()
    b.doc.save()
