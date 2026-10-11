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
from geometry import led_centres, mask_cells, mounting_points, optical_dimensions, ring_pixel, ring_radius


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
        scalar = {'inner_count', 'outer_count', 'strip_density', 'map_rotation_deg', 'map_mirror_x', 'map_mirror_y', 'sparkle_rotation', 'fastener_phase_deg', 'runtime_hours', 'example_total_current_a', 'example_output_voltage', 'assumed_efficiency'}
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
    points = mounting_points(p)
    # Rev D Eagle coordinates, rotated about the actual outline centre.
    a = math.radians(p['sparkle_rotation'])
    sparkle_holes = [(dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a))
                     for dx, dy in [(x - 25.4, y - 16.5735) for x in (2.54, 48.26) for y in (2.54, 30.48)]]
    holes = lambda name, z, height: [b.cylinder(f'{name}{i}', E('fastener_hole_radius'), height, z, x, y) for i, (x, y) in enumerate(points)]

    # Annular mirrors surround the circle. The outer strip emits through the
    # open edge band: no opaque barrel lies in front of its LED faces.
    front_expr = E('case_depth') + '-' + E('front_bezel_thickness') + '-' + E('acrylic_thickness')
    inner_r, outer_r = ring_radius(p['inner_count'], p), ring_radius(p['outer_count'], p)
    inner_back = inner_r + p['strip_thickness']/2
    mirror_outer = inner_back + p['strip_wall'] - p['fit_clearance']/2
    shell = b.annulus('Barrel', E('case_diameter') + '/2-' + E('shell_wall'), E('case_diameter') + '/2', E('rear_thickness'), E('edge_bottom_z') + '-' + E('rear_thickness'))
    floor = b.annulus('RingFloor', 'Parameters.circle_diameter/2+0.5 mm', 'Parameters.case_diameter/2-Parameters.shell_wall+0.5 mm', E('mirror_back_z') + '-' + E('strip_wall'), E('strip_wall'))
    boundary = b.annulus('CircleBoundary', 'Parameters.circle_diameter/2+0.5 mm', E('mirror_inner_radius'), E('mirror_back_z'), E('case_depth') + '-' + E('front_bezel_thickness') + '-' + E('mirror_back_z'))
    seat_blank = b.cylinder('CircleSeatBlank', 'Parameters.circle_diameter/2+1.5 mm', 3.5, E('circle_back_z')+'-3.5 mm')
    seat_tool = doc.addObject('Part::Cone','CircleSeatSlope')
    seat_tool.Radius1,seat_tool.Radius2,seat_tool.Height = p['circle_diameter']/2+.5,p['circle_diameter']/2-3,3.5
    seat_tool.Placement = App.Placement(App.Vector(0,0,p['circle_back_z']-3.5),App.Rotation())
    ledge = b.cut('CircleEdgeLedge',seat_blank,seat_tool)
    walls = []
    for name, count in [('Inner', p['inner_count']), ('Outer', p['outer_count'])]:
        r = ring_radius(count, p)
        # The carrier touches the BACK of each strip, never its emitting face.
        low = r + p['strip_thickness']/2 if name == 'Inner' else r - p['strip_thickness']/2 - p['strip_wall']
        walls.append(b.annulus(name + 'StripWall', low, low + p['strip_wall'], E('mirror_back_z'), front_expr + '-' + E('mirror_back_z')))
    posts = [b.cylinder(f'LidPost{i}', E('post_radius'), E('case_depth') + '-' + E('front_bezel_thickness') + '-' + E('rear_thickness'), E('rear_thickness'), x, y) for i, (x, y) in enumerate(points)]
    post_bridges = []
    for i,(x,y) in enumerate(points):
        rib = b.box(f'PostRearBridge{i}',radius-p['fastener_radius']+2,6,p['strip_wall'],p['fastener_radius']-2,-3,rear)
        rib.Placement = App.Placement(App.Vector(),App.Rotation(App.Vector(0,0,1),math.degrees(math.atan2(y,x)))).multiply(rib.Placement)
        post_bridges.append(rib)
    frame = b.fuse('FrameBlank', [shell, floor, boundary, ledge] + walls + posts + post_bridges)
    # Service windows have actual passages through the barrel.
    ports = [b.box('SparkleUSBPowerPort', radius-83, 38, 17, 88, 17, 5), b.box('RadioPort', 30, 12, 12, -radius-5, 20, 7), b.box('PowerSwitchPort', 16, 30, 12, 28, -radius-5, 7)]
    for i, x in enumerate((-35, 35)):
        port = b.cylinder(f'ControlPort{i}', 4.1, 30, 13, x, radius+5)
        port.Placement = App.Placement(port.Placement.Base, App.Rotation(App.Vector(1, 0, 0), 90))
        ports.append(port)
    for i in range(12):
        a = math.radians(i * 30)
        if i in (0, 1, 5, 6, 9):
            continue
        v = b.box(f'BarrelVent{i}', 12, 4, 5, radius - 8, -2, 15)
        v.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(App.Vector(0, 0, 1), math.degrees(a))).multiply(v.Placement)
        ports.append(v)
    circle_points = [(p['circle_screw_radius']*math.cos(i*math.tau/3), p['circle_screw_radius']*math.sin(i*math.tau/3)) for i in range(3)]
    circle_bores = [b.cylinder(f'CircleClampBore{i}', E('circle_screw_hole_radius'), 8, depth-p['front_bezel_thickness']-8, x, y) for i,(x,y) in enumerate(circle_points)]
    # Independent rearward lead slots at the two top strip seams.
    leads = [b.box(name+'LeadExit', p['ring_seam_gap'], 5, 5, -p['ring_seam_gap']/2, r-2.5, p['mirror_back_z']-p['strip_wall']) for name,r in [('Inner',inner_r),('Outer',outer_r)]]
    frame = b.cut('OpticalFrame', frame, holes('FrameBore', rear, depth-p['front_bezel_thickness']-rear) + ports + circle_bores + leads)
    b.add(frame, 'Manufactured', '01 Optical frame - inward mirror ring, outward edge ring', (.15, .17, .20), material='Printed opaque polymer')

    # Six full-length M3 bolts and rear nuts clamp the complete stack.
    rear_blank = b.cylinder('RearBlank', E('case_diameter') + '/2-' + E('fit_clearance'), E('rear_thickness'))
    skeleton = [b.annulus('RearRim', radius-8, radius-p['fit_clearance'], 0, rear), b.cylinder('RearHub', 12, rear)]
    for i in range(6):
        rib = b.box(f'RearSpoke{i}', radius, 6, rear, 0, -3, 0)
        rib.Placement = App.Placement(App.Vector(), App.Rotation(App.Vector(0,0,1), i*60))
        skeleton.append(rib)
    # Continuous cross rails carry all board mounts, rather than leaving feet
    # suspended over the openings in a decorative lattice.
    for i,y in enumerate((p['battery_y']-p['battery_length']/2, p['battery_y']+p['battery_length']/2, 31, 70)):
        skeleton.append(b.box(f'RearCrossRail{i}', 2*radius, 8, rear, -radius, y-4, 0))
    for key in ('blackpill','gps','imu','radio','sense'):
        x,y,w,l = [p[key+'_'+suffix] for suffix in ('x','y','width','length')]
        for side in (-1,1):
            start = x+w/2-1 if side == 1 else x-w/2-2.5
            skeleton.append(b.box(f'{key}RearPad{side:+}', 3.5, l+4, rear, start, y-l/2-2, 0))
    for i,(dx,dy) in enumerate(sparkle_holes):
        y = p['sparkle_y']+dy
        skeleton.append(b.box(f'SparkleRearPad{i}', 6, abs(y-31)+6, rear, p['sparkle_x']+dx-3, min(y,31)-3, 0))
    bx,by,bw,bl = [p['battery_'+key] for key in ('x','y','width','length')]
    for i,x in enumerate((bx-bw/3,bx+bw/3)):
        skeleton.append(b.box(f'RearBatteryRail{i}', 8, bl+4, rear, x-4, by-bl/2-2, 0))
    rear_skeleton = b.fuse('RearSkeletonBlank', skeleton)
    back = doc.addObject('Part::Common', 'RearSkeleton')
    back.Base,back.Tool = rear_blank,rear_skeleton
    b.hide(rear_blank)
    b.hide(rear_skeleton)
    back = b.cut('RearVentPlate', back, holes('RearHole', -1, rear+2))
    # Lugs are integral with the rear plate. The eye passes through both layers.
    lugs = [b.box(f'LugBlank{i}', 18, 15, 6, x - 9, 54.5, rear) for i, x in enumerate((-82, 82))]
    back = b.fuse('RearPlateWithLugs', [back] + lugs)
    eyes = [b.cylinder(f'LugEye{i}', 3, rear + 7, -0.5, x, 62) for i, x in enumerate((-82, 82))]
    back = b.cut('RearPlate', back, eyes)
    b.add(back, 'Manufactured', '02 Open rear support - necklace eyes, board pads and battery rails', (.20, .22, .25), material='Printed polymer; attachment needs physical load check')

    carrier_items = []
    # Battery is a restrained envelope, not an electrical cell-holder design.
    bx, by, bw, bl = p['battery_x'], p['battery_y'], p['battery_width'], p['battery_length']
    battery_outer = b.box('BatteryCradleOuter', E('battery_width') + '+4 mm', E('battery_length') + '+4 mm', 7, E('battery_x') + '-' + E('battery_width') + '/2-2 mm', E('battery_y') + '-' + E('battery_length') + '/2-2 mm', rear)
    battery_cavity = b.box('BatteryCradleCavity', E('battery_width') + '+1 mm', E('battery_length') + '+1 mm', 8, E('battery_x') + '-' + E('battery_width') + '/2-0.5 mm', E('battery_y') + '-' + E('battery_length') + '/2-0.5 mm', rear + 1.5)
    cradle = b.cut('BatteryCradle', battery_outer, battery_cavity)
    cradle = b.cut('OpenBatteryCradle', cradle, b.box('BatteryCradleWeightRelief', bw-4, bl-4, 2, bx-bw/2+2, by-bl/2+2, rear-.1))
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
        tip = b.cylinder(f'ButtonActuator{i}', 4, 22, 13, x, radius+3)
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
        outward = name == 'Outer'
        for i in range(count):
            (x,y),(nx,ny) = ring_pixel(count, i, outward, p)
            shape = Part.makeBox(p['ring_led_depth'], 5, 5, App.Vector(-p['ring_led_depth']/2, -2.5, -2.5))
            shape.Placement = App.Placement(App.Vector(x, y, p['strip_bottom_z'] + p['strip_width'] / 2), App.Rotation(App.Vector(0, 0, 1), math.degrees(math.atan2(ny,nx))))
            shapes.append(shape)
        obj = doc.addObject('Part::Feature', name + 'LEDs')
        obj.Shape = Part.makeCompound(shapes)
        b.add(obj, 'Optics', f'{name} ring LED references - {"outward" if outward else "inward"} facing', (.85, .65, .30))
        obj.addProperty('App::PropertyString', 'EmissionDirection').EmissionDirection = 'Radially outward' if outward else 'Radially inward toward circle'

    rear_mirror = b.annulus('RearMirrorBlank', E('mirror_inner_radius'), inner_back, E('mirror_back_z'), E('mirror_back_thickness'))
    rear_mirror = b.cut('RearMirror',rear_mirror,b.box('MirrorLeadNotch',E('ring_seam_gap'),6,E('mirror_back_thickness'),-p['ring_seam_gap']/2,inner_r-3,E('mirror_back_z')))
    b.add(rear_mirror, 'Manufactured', '05 Rear mirror annulus - reflective face toward front', (.60,.65,.72), material='1.5 mm acrylic with full mirror film on +Z face')
    mirror = b.annulus('FrontMirror', E('mirror_inner_radius'), mirror_outer, front_expr, E('acrylic_thickness'))
    b.add(mirror, 'Manufactured', '06 Front two-way mirror annulus - visible infinity gap', (.65,.75,.86), 65, material='1.5 mm clear acrylic plus two-way film; reflective surface faces -Z')
    edge = b.annulus('EdgeDiffuser', E('edge_diffuser_radius'), E('edge_diffuser_radius')+'+'+E('edge_diffuser_thickness'), E('edge_bottom_z'), E('case_depth')+'-'+E('front_bezel_thickness')+'-'+E('edge_bottom_z'))
    edge = b.cut('EdgeDiffuserSeam', edge, b.box('EdgeDiffuserGap', 1, 4, depth, -.5, p['edge_diffuser_radius']-1, 0))
    b.add(edge, 'Manufactured', '07 Wrapped edge diffuser - outer LEDs visible edge-on', (.85,.88,.93), 65, material='0.5 mm translucent PET sheet; removable top seam')

    # Cell baffle and wood share exactly the same XY opening sketch.
    openings = b.profile('FibonacciApertures', cells, wood_expr, E('wood_thickness'))
    wood = b.cylinder('WoodBlank', 'Parameters.circle_diameter/2', E('wood_thickness'), wood_expr)
    wood = b.cut('WoodMask', wood, openings)
    b.add(wood, 'Manufactured', '08 Laser-cut wood - 256 Fibonacci cells, circle only', (.53, .32, .13), material='2 mm nominal wood; measure thickness and kerf')
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
    acrylic = b.cylinder('FrontAcrylic', 'Parameters.circle_diameter/2', E('acrylic_thickness'), front_expr)
    b.add(acrylic, 'Manufactured', '09 Central acrylic - wood lies directly behind it', (.80, .88, .92), 80, material='1.5 mm LED diffuser acrylic; actual transmission unknown')
    bezel = b.annulus('BezelBlank', E('mirror_view_outer_radius'), E('case_diameter') + '/2', E('case_depth') + '-' + E('front_bezel_thickness'), E('front_bezel_thickness'))
    bezel = b.cut('FrontBezel', bezel, holes('BezelHole', depth - p['front_bezel_thickness'], p['front_bezel_thickness']))
    b.add(bezel, 'Manufactured', '10 Outer bezel - captures mirror and edge diffuser', (.15, .17, .20), material='Printed polymer')
    clamp = b.annulus('CircleBezelBlank', E('circle_retainer_inner_radius'), E('circle_retainer_outer_radius'), E('case_depth')+'-'+E('front_bezel_thickness'), E('front_bezel_thickness'))
    clamp = b.cut('CircleBezel', clamp, [b.cylinder(f'CircleClampHole{i}', E('circle_screw_hole_radius'), E('front_bezel_thickness'), depth-p['front_bezel_thickness'], x,y) for i,(x,y) in enumerate(circle_points)])
    b.add(clamp, 'Manufactured', '11 Circle retainer - three M2 screws, clamps central face and mirror inner edge', (.15,.17,.20), material='Printed polymer')

    # Bond the butt joints with flat lap straps. Each subassembly stays
    # removable; no strap bridges the frame-to-rear service joint.
    straps = []
    for prefix,r,z,width in [('Rear',radius-4.75,rear,6),('Frame',(inner_back+p['strip_wall']+outer_r-p['strip_thickness']/2-p['strip_wall'])/2,p['mirror_back_z'],3.6),('Bezel',outer_r-1,depth-p['front_bezel_thickness']-p['splice_thickness'],6)]:
        for i in range(4):
            strap = b.box(f'{prefix}Splice{i}', width, 14, p['splice_thickness'], r-width/2, -7, z)
            strap.Placement = App.Placement(App.Vector(), App.Rotation(App.Vector(0,0,1), i*90)).multiply(strap.Placement)
            straps.append(strap)
    for i in range(4):
        strap = b.annulus(f'BarrelSpliceBlank{i}',radius-p['shell_wall']-p['splice_thickness'],radius-p['shell_wall'],rear+2,12)
        tool = b.box(f'BarrelSpliceTool{i}',5,14,12,radius-p['shell_wall']-3,-7,rear+2)
        tool.Placement = App.Placement(App.Vector(),App.Rotation(App.Vector(0,0,1),i*90)).multiply(tool.Placement)
        curved = doc.addObject('Part::Common',f'BarrelSplice{i}')
        curved.Base,curved.Tool = strap,tool
        b.hide(strap)
        b.hide(tool)
        straps.append(curved)
    b.add(b.compound('SeamStraps',straps), 'Manufactured', '12 Splice straps - bond four butt seams per subassembly', (.30,.31,.34), material='Printed polymer; adhesive and load acceptance remain provisional')
    # Print the optical deck on its floor. Print the lower skirt separately,
    # so the wide annular floor is not a large unsupported radial overhang.
    b.parts.remove(frame)
    doc.Manufactured.removeObject(frame)
    doc.Construction.addObject(frame)
    deck_bottom = p['mirror_back_z']-p['strip_wall']
    for name,z,h in [('OpticalDeck',deck_bottom,depth-deck_bottom),('BarrelFrame',rear,deck_bottom-rear)]:
        tool = b.box(name+'Tool',2*radius+2,2*radius+2,h,-radius-1,-radius-1,z)
        piece = doc.addObject('Part::Common',name)
        piece.Base,piece.Tool = frame,tool
        b.add(piece,'Manufactured',name+' - separately printed level',(.15,.17,.20),material=frame.Material)
        b.hide(tool)
        split_printed_part(b,piece)
    b.hide(frame)
    split_printed_part(b, back)
    split_printed_part(b, bezel)

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
    export_files(b, centres, cells)
    print('CAD BUILD PASS:', master)
    return b


def split_printed_part(b, obj):
    """Four native quarter solids; bond their seams with separate lap straps."""
    radius, depth = b.p['case_diameter']/2+1, b.p['case_depth']+1
    b.parts.remove(obj)
    b.doc.Manufactured.removeObject(obj)
    b.doc.Construction.addObject(obj)
    for i,(sx,sy) in enumerate(((1,1),(-1,1),(-1,-1),(1,-1))):
        clip = b.box(f'{obj.Name}QuarterTool{i}', radius, radius, depth, 0 if sx>0 else -radius, 0 if sy>0 else -radius, 0)
        quarter = b.doc.addObject('Part::Common', f'{obj.Name}Q{i+1}')
        quarter.Base,quarter.Tool = obj,clip
        b.add(quarter,'Manufactured',f'{obj.Label} / quarter {i+1}',(.15,.17,.20),material=obj.Material)
        b.hide(clip)
    b.hide(obj)


def validate_parameters(p):
    if not (0 < p['assumed_efficiency'] <= 1):
        raise ValueError('Efficiency must lie in (0,1]')
    for key in ('inner_count', 'outer_count'):
        if int(p[key]) != p[key] or not 1 <= p[key] <= 512:
            raise ValueError('Ring counts must be integers in 1..512')
    if p['sparkle_rotation'] not in (0, 180):
        raise ValueError('The axis-aligned Sparkle footprint supports rotations 0 or 180 only')
    for key in ('battery_width', 'battery_length', 'battery_height', 'strip_density', 'mask_web', 'shell_wall', 'rear_thickness', 'strip_wall', 'ring_led_depth', 'print_bed_x', 'print_bed_y'):
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
    optics = optical_dimensions(p)
    if optics['visible_mirror_width'] < 20 or optics['circle_to_inner_led'] < 20:
        raise ValueError('Infinity annulus requires at least 20 mm visible width and circle-to-LED gap')
    if p['mirror_view_inner_radius'] < p['circle_retainer_outer_radius']:
        raise ValueError('Circle retainer masks the specified mirror view')
    if p['strip_bottom_z'] < p['mirror_back_z'] + p['mirror_back_thickness'] + .2 or p['strip_bottom_z'] + p['strip_width'] > p['case_depth'] - p['front_bezel_thickness'] - p['acrylic_thickness'] - .2:
        raise ValueError('Strip does not fit between the mirror surfaces')
    if optics['outer_led_clearance'] < .5:
        raise ValueError('Outer LED packages leave less than 0.5 mm diffuser clearance')
    if optics['inner_radius'] + p['strip_thickness']/2 + p['strip_wall'] >= p['fastener_radius']-p['post_radius']:
        raise ValueError('Perimeter posts intrude into the front mirror seat')
    if p['rear_thickness']+1.5+p['battery_height']+.5 > p['mirror_back_z']-p['strip_wall']:
        raise ValueError('Battery leaves less than 0.5 mm optical-floor clearance')


def check_partition(parent, children):
    # Compare solids directly: trimmed-cylinder volume integrals can differ
    # after splitting even when the geometric symmetric difference is empty.
    joined = children[0].Shape.multiFuse([o.Shape for o in children[1:]])
    if not joined.isValid() or parent.Shape.cut(joined).Solids or joined.cut(parent.Shape).Solids:
        raise ValueError('Print split lost or added geometry: '+parent.Name)
    for i,a in enumerate(children):
        for other in children[i+1:]:
            if a.Shape.common(other.Shape).Solids:
                raise ValueError('Print split overlaps: '+a.Name+' / '+other.Name)


def check_model(b, centres, cells):
    bad = [(o.Name, list(o.State)) for o in b.doc.Objects if 'Invalid' in o.State or 'Error' in o.State]
    if bad:
        raise ValueError('Invalid document objects: ' + repr(bad))
    for obj in b.parts + b.hardware + b.references:
        if obj.Shape.isNull() or not obj.Shape.isValid() or obj.Shape.Volume <= 0:
            raise ValueError('Invalid solid geometry: ' + obj.Name)
    if len(b.doc.WoodMask.Shape.Solids) != 1:
        raise ValueError('Wood mask contains detached islands')
    for obj in b.parts:
        if obj.Name not in {'BoardMounts','SeamStraps'} and len(obj.Shape.Solids) != 1:
            raise ValueError(obj.Name + ' is not one connected manufactured part: '+repr([(round(s.Volume,4),str(s.BoundBox)) for s in obj.Shape.Solids]))
    if len(centres) != 256 or len(cells) != 256:
        raise ValueError('Circle mask must preserve 256 LED apertures')
    for prefix in ('OpticalDeck','BarrelFrame','RearPlate','FrontBezel'):
        check_partition(b.doc.getObject(prefix),[b.doc.getObject(prefix+f'Q{i}') for i in range(1,5)])
    check_partition(b.doc.OpticalFrame,[b.doc.OpticalDeck,b.doc.BarrelFrame])
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
    for name in ('CircleLEDs','InnerLEDs','OuterLEDs'):
        leds = b.doc.getObject(name)
        for obj in b.parts:
            if leds.Shape.common(obj.Shape).Volume > .05:
                raise ValueError(f'{obj.Name} intersects {name}')
    for name,count,outward in [('Inner',int(b.p['inner_count']),False),('Outer',int(b.p['outer_count']),True)]:
        # Light-path test at every LED angle. Mirror optics are not simulated.
        for i in range(count):
            (x,y),(nx,ny) = ring_pixel(count,i,outward,b.p)
            start = App.Vector(x+nx*(b.p['ring_led_depth']/2+.05),y+ny*(b.p['ring_led_depth']/2+.05),b.p['strip_bottom_z']+b.p['strip_width']/2)
            end_radius = b.p['edge_diffuser_radius']-.05 if outward else b.p['mirror_view_inner_radius']+.05
            sign = 1 if outward else -1
            end = App.Vector(sign*nx*end_radius,sign*ny*end_radius,start.z)
            if Part.makeLine(start,end).common(b.doc.OpticalFrame.Shape).Length > .01:
                raise ValueError(f'Opaque frame blocks {name} pixel {i}')
    print('CAD geometry checks: connected parts, no product/LED collisions, inward and outward light paths clear',flush=True)


def export_files(b, centres, cells):
    out = HERE / 'exports'
    out.mkdir(exist_ok=True)
    Part.export(b.parts + b.hardware + [b.doc.CircleLEDs, b.doc.InnerLEDs, b.doc.OuterLEDs], str(out / 'smart-compass.step'))
    import MeshPart
    mesh_names = []
    volumes = []
    nonprinted = {'WoodMask','FrontAcrylic','RearMirror','FrontMirror','EdgeDiffuserSeam'}
    for obj in b.parts:
        volumes.append({'name':obj.Name,'volume_cm3':round(obj.Shape.Volume/1000,4),'printed':obj.Name not in nonprinted})
        if obj.Name in nonprinted:
            continue
        for i,solid in enumerate(obj.Shape.Solids):
            # Translate each connected part onto Z=0 in its own bed footprint.
            shape = solid.copy()
            if obj.Name == 'CellBaffle' or obj.Name == 'SeamStraps':
                # Baffle face down, rim feet up; flat splice backs down.
                shape.rotate(App.Vector(),App.Vector(1,0,0),180)
            bb = shape.BoundBox
            shape.translate(App.Vector(-bb.XMin,-bb.YMin,-bb.ZMin))
            bounds = shape.BoundBox
            if bounds.XLength+2*b.p['print_margin'] > b.p['print_bed_x'] or bounds.YLength+2*b.p['print_margin'] > b.p['print_bed_y']:
                raise ValueError('Printed part does not fit the configured bed: '+obj.Name)
            name = obj.Name + (f'-{i+1:02}' if len(obj.Shape.Solids)>1 else '') + '.stl'
            MeshPart.meshFromShape(Shape=shape,LinearDeflection=.08,AngularDeflection=.15,Relative=False).write(str(out/name))
            mesh_names.append(name)
    # Remove superseded generator-owned STL outputs, never user-created files.
    for name in ('OpticalFrame.stl','RearPlate.stl','FrontBezel.stl','BoardMounts.stl'):
        (out/name).unlink(missing_ok=True)
    (out/'parts.json').write_text(json.dumps({'stl_files':mesh_names,'volumes':volumes,'printed_volume_cm3':round(sum(o.Shape.Volume/1000 for o in b.parts if o.Name not in nonprinted),4),'optics_mm':optical_dimensions(b.p)},indent=2)+'\n')
    svg_files(b.p, cells, out)
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
<text x="{-r}" y="20">Circle: baffle → {b.p['wood_thickness']:g} mm wood → {b.p['acrylic_thickness']:g} mm acrylic. Rings: inward mirror annulus / outward edge band.</text>
</g></svg>'''
    (out / 'assembly-section.svg').write_text(drawing)


def svg_files(p, cells, out):
    # Nominal design contours. Apply measured kerf once in the laser CAM software.
    r = p['circle_diameter'] / 2
    def document(paths, description, r=r):
        return '<svg xmlns="http://www.w3.org/2000/svg" width="%gmm" height="%gmm" viewBox="%g %g %g %g">\n<title>%s</title>\n<desc>PROVISIONAL alignment and material fit; nominal paths, no kerf compensation. Front view, X right, Y up.</desc>\n<g transform="scale(1,-1)" fill="none" stroke="#ff0000" stroke-width="0.08">\n%s\n</g></svg>\n' % (2*r, 2*r, -r, -r, 2*r, 2*r, description, '\n'.join(paths))
    outline = f'<circle cx="0" cy="0" r="{r:.6f}"/>'
    polygons = ['<polygon points="' + ' '.join(f'{x:.6f},{y:.6f}' for x,y in poly) + '"/>' for poly in cells]
    (out / 'wood-fibonacci-mask.svg').write_text(document([outline] + polygons, f'Circle wood mask - 256 Fibonacci cells, {p["wood_thickness"]:g} mm nominal'))
    (out / 'front-acrylic.svg').write_text(document([outline], f'Central diffuser acrylic - {p["acrylic_thickness"]:g} mm nominal'))
    inner_r = ring_radius(p['inner_count'],p)
    rear_outer = inner_r+p['strip_thickness']/2
    front_outer = rear_outer+p['strip_wall']-p['fit_clearance']/2
    inner_path = f'<circle cx="0" cy="0" r="{p["mirror_inner_radius"]:.6f}"/>'
    (out/'front-mirror.svg').write_text(document([inner_path,f'<circle cx="0" cy="0" r="{front_outer:.6f}"/>'],'Front two-way annulus - reflective film faces rear',front_outer))
    # The rear mirror lead notch joins the outer contour, not a detached hole.
    gap = p['ring_seam_gap']/2
    notch_y = inner_r-3
    phi = math.asin(gap/rear_outer)
    a = (rear_outer*math.sin(phi),rear_outer*math.cos(phi))
    contour = f'<path d="M {a[0]:.6f},{a[1]:.6f} A {rear_outer:.6f},{rear_outer:.6f} 0 1 0 {-a[0]:.6f},{a[1]:.6f} L {-gap:.6f},{notch_y:.6f} L {gap:.6f},{notch_y:.6f} Z"/>'
    (out/'rear-mirror.svg').write_text(document([inner_path,contour],'Rear mirror annulus - reflective face toward front; top lead notch',rear_outer))
    width = math.tau*(p['edge_diffuser_radius']+p['edge_diffuser_thickness']/2)-1
    height = p['case_depth']-p['front_bezel_thickness']-p['edge_bottom_z']
    (out/'edge-diffuser.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.6f}mm" height="{height:.6f}mm" viewBox="0 0 {width:.6f} {height:.6f}"><title>Wrapped 0.5 mm edge diffuser; nominal 1 mm end gap</title><path fill="none" stroke="#ff0000" stroke-width="0.08" d="M 0,0 H {width:.6f} V {height:.6f} H 0 Z"/></svg>\n')
    # The inspection overlay never enters a laser cut file.
    overlay = [outline, '<path d="M -50,-92 L 50,-92 M -50,-90 L -50,-94 M 50,-90 L 50,-94"/>'] + polygons + [f'<circle cx="{x:.6f}" cy="{y:.6f}" r="0.5"/>' for x,y in led_centres(json.loads((HERE/'fibonacci256-layout.json').read_text()),p)]
    (out / 'circle-alignment-overlay.svg').write_text(document(overlay, 'Print at 100 percent and check 166 mm circle / LED registration',98))


def export_previews(b, out):
    import FreeCADGui as Gui
    view = Gui.activeDocument().activeView()
    animation = view.isAnimationEnabled()
    view.setAnimationEnabled(False)
    Gui.updateGui()
    view.viewTop()
    view.fitAll()
    view.saveImage(str(out / 'front.png'), 1400, 1400, 'White')
    view.viewAxonometric()
    view.fitAll()
    view.saveImage(str(out / 'assembly.png'), 1600, 1400, 'White')
    # A real exploded placement, saved only in the preview, never in the master.
    moved = []
    for obj in b.parts:
        offset = 65 if obj.Name.startswith('FrontBezelQ') or obj.Name=='CircleBezel' else {'FrontAcrylic':50,'FrontMirror':50,'WoodMask':35,'CellBaffle':20}.get(obj.Name,0)
        if not offset:
            continue
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
    hidden = [obj for obj in b.parts+b.hardware+b.references if not (obj.Name.startswith('RearPlateQ') or obj.Name in {'BatteryStrapSlots','BoardMounts','BatteryEnvelope'} or obj in b.hardware and 'PCB' in obj.Name and obj.Name!='CirclePCB')]
    visibility = [(obj,obj.Visibility) for obj in hidden]
    for obj in hidden:
        obj.Visibility = False
    Gui.updateGui()
    view.viewTop()
    view.fitAll()
    view.saveImage(str(out / 'electronics.png'), 1400, 1400, 'White')
    for obj,was_visible in visibility:
        obj.Visibility = was_visible
    view.viewRear()
    view.fitAll()
    view.saveImage(str(out / 'edge.png'), 1600, 900, 'White')
    view.viewAxonometric()
    view.fitAll()
    b.doc.save()
    view.setAnimationEnabled(animation)
