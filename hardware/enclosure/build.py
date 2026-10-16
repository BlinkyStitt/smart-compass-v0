"""Build a native FreeCAD pendant with no persistent Python feature proxies.

Run through Build.FCMacro in FreeCAD, or with FreeCADCmd and SC_CAD_DIR set.
parameters.json owns every build. The saved FCStd spreadsheet records inputs
and the derived stack. Exported meshes and laser contours are derived outputs.
"""
import colorsys
import json
import math
import os
from pathlib import Path
import sys
from xml.sax.saxutils import escape

import FreeCAD as App
import Part
import Sketcher

from hardware_spec import nut_dimensions, hexagon, body_bolt_length
import baffle

HERE = Path(os.environ.get('SC_CAD_DIR', Path(__file__).resolve().parent))
sys.path.insert(0, str(HERE))
from geometry import load_parameters, battery_centres, cavity_diffusers, led_centres, pixel_regions, mounting_points, necklace_anchors, optical_dimensions, ring_pixel, ring_radius, ring_locating_angles, ring_movement_limit, ring_led_clearances, outside_front_overlap, strip_bottom, rear_mounting_points, top_light_shields, baffle_bottom

DIFFUSER_TRANSPARENCY = 35  # CAD display only; not measured optical transmission.
DIFFUSER_TINT = (184 / 255, 209 / 255, 138 / 255)  # Use the native file's 8-bit RGB precision.


class Builder:
    def __init__(self, p):
        self.p = p
        self.doc = App.newDocument('SmartCompass')
        self.parts, self.hardware, self.references = [], [], []
        self.sheet = self.doc.addObject('Spreadsheet::Sheet', 'Parameters')
        self.sheet.Label = 'Dimensions - generated from parameters.json'
        self.sheet.set('A1', 'Parameter')
        self.sheet.set('B1', 'Value (mm unless stated)')
        self.sheet.set('C1', 'Input status')
        self.keys = [k for k in p if not k.startswith('_')]
        scalar = {'battery_count', 'battery_mass_g', 'halo_count', 'inner_count', 'outer_count', 'strip_density', 'map_rotation_deg', 'map_mirror_x', 'map_mirror_y', 'sparkle_rotation', 'fastener_phase_deg', 'runtime_hours', 'example_total_current_a', 'example_output_voltage', 'assumed_efficiency', 'front_washer_compression_ratio', 'ring_station_count'}
        for row, key in enumerate(self.keys, 2):
            self.sheet.set(f'A{row}', key)
            value = int(p[key]) if isinstance(p[key], bool) else p[key]
            self.sheet.set(f'B{row}', ('=front_plane_z + front_acrylic_thickness + front_washer_compressed_height' if key == 'case_depth' else '=rear_mirror_front_z - rear_acrylic_thickness' if key == 'mirror_back_z' else '=front_washer_free_thickness * front_washer_compression_ratio' if key == 'front_washer_compressed_height' else '=' + str(value) + ('' if key in scalar else ' mm')))
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

    def cone(self, name, r0, r1, height, z, x=0, y=0):
        obj = self.doc.addObject('Part::Cone', name)
        obj.Radius1, obj.Radius2, obj.Height = r0, r1, height
        obj.Placement.Base = App.Vector(x,y,z)
        return obj

    def bore_entries(self, name, points, radius, bottom, top, top_entry=.3):
        # 45-degree entries preserve the nominal bore through the bearing land.
        return [self.cone(f'{name}{i}{side}',r0,r1,abs(r1-r0),z,x,y)
                for i,(x,y) in enumerate(points)
                for side,r0,r1,z in (('Bottom',radius+.3,radius,bottom),
                                    ('Top',radius,radius+top_entry,top-top_entry))]

    def service_mount(self, name, x, y):
        """M2 nut slides in from +Y; the 4.4 mm roof bridge retains it axially."""
        boss = self.fuse(name,[
            # A flat loading face leaves two full-height cheeks supporting the
            # pocket roof. A round nose leaves an unsupported crescent.
            self.box(name+'Stem',7.6,7.2,5.8,x-3.8,y-4.4,0),
            self.cone(name+'Root',4.6,3.8,.8,self.p['rear_skin_thickness'],x,y)])
        pocket, entry = self.nut_pocket(name, 'M2', x, y, 2.4, 5)
        bore = self.cylinder(name+'Bore',1.2,10,-1,x,y)
        return boss, [pocket,entry,bore]

    def nut_pocket(self, name, size, x, y, z, entrance_length):
        """One hex construction and one allowance for every captive plain nut."""
        flats, thickness = nut_dimensions(size, pocket=True)
        pocket = self.profile(name+'Nut', [hexagon(x,y,flats)], z, thickness)
        entry = self.box(name+'Entry', flats, entrance_length, thickness, x-flats/2,y,z)
        return pocket, entry

    def fillet(self, name, base, radius, edges):
        obj = self.doc.addObject('Part::Fillet', name)
        obj.Base = base
        obj.Edges = [(i, radius, radius) for i in edges]
        self.hide(base)
        return obj

    def root_blend(self, name, length, edge, y, z, radius=.6):
        """Add a tangent quarter-round at a straight wall/skin junction."""
        block = self.box(name+'Block',radius,length,radius,edge,y,z)
        cylinder = self.cylinder(name+'Round',radius,length,0)
        cylinder.Placement = App.Placement(App.Vector(edge+radius,y,z+radius),App.Rotation(App.Vector(1,0,0),-90))
        return self.cut(name,block,cylinder)

    def circular_root(self,name,radius,z,x,y,round_radius=.6,up=True):
        # Net additive quarter-round; tangent to the boss and adjoining plane.
        bottom=z if up else z-round_radius
        ring=self.annulus(name+'Ring',radius,radius+round_radius,bottom,round_radius)
        torus=self.doc.addObject('Part::Torus',name+'Tool')
        torus.Radius1,torus.Radius2=radius+round_radius,round_radius
        torus.Placement.Base=App.Vector(x,y,z+round_radius if up else z-round_radius)
        ring.Placement.Base=App.Vector(x,y,0)
        return self.cut(name,ring,torus)

    def top_mark(self, name, y, z, upright=False):
        """Font-independent TOP strokes, recessed in a non-mating surface."""
        strokes = [(0,4.2,3,.8),(1.1,0,.8,5),
                   (4,0,.8,5),(6.2,0,.8,5),(4,0,3,.8),(4,4.2,3,.8),
                   (8,0,.8,5),(8,4.2,3,.8),(8,2.1,3,.8),(10.2,2.1,.8,2.9)]
        polygons = [[(x-5.5,v),(x+w-5.5,v),(x+w-5.5,v+h),(x-5.5,v+h)] for x,v,w,h in strokes]
        # Separate rectangles may overlap: fuse their tools before subtracting.
        tools = [self.profile(name+str(i),[poly],0,.7 if upright else .4) for i,poly in enumerate(polygons)]
        mark = self.fuse(name,tools)
        rotation = App.Rotation(App.Vector(1,0,0),90) if upright else App.Rotation()
        mark.Placement = App.Placement(App.Vector(0,y,z),rotation)
        return mark

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


def build(p=None):
    acrylic = json.loads((HERE/'acrylic-optics.json').read_text())['materials']
    master = HERE / 'smart-compass.FCStd'
    if p is None:
        p = load_parameters()
    validate_parameters(p)
    b = Builder(p)
    doc = b.doc
    E = lambda key: 'Parameters.' + key
    depth, wall, rear = p['case_depth'], p['shell_wall'], p['rear_thickness']
    baffle_z = baffle_bottom(p)
    front = p['front_plane_z']
    deck_bottom = p['mirror_back_z']-p['strip_wall']
    baffle_expr = E('front_plane_z')+'-'+E('baffle_to_sheet_gap')+'-'+E('baffle_thickness')
    radius = p['case_diameter'] / 2
    centres = led_centres(json.loads((HERE / 'fibonacci256-layout.json').read_text()), p)
    cells = pixel_regions(centres, p['circle_diameter']/2)
    points = mounting_points(p)
    # Rev D Eagle coordinates, rotated about the actual outline centre.
    a = math.radians(p['sparkle_rotation'])
    sparkle_holes = [(dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a))
                     for dx, dy in [(x - 25.4, y - 16.5735) for x in (2.54, 48.26) for y in (2.54, 30.48)]]
    holes = lambda name, z, height: [b.cylinder(f'{name}{i}', E('fastener_hole_radius'), height, z, x, y) for i, (x, y) in enumerate(points)]

    # Replaceable brackets carry webbing through the rear. A second independent
    # screw retains each bracket when the main case bolts/rear are removed.
    suspension = []
    anchor_bosses, anchor_tools = [], []
    for i,side in enumerate((-1,1)):
        eye,bolt,secondary = necklace_anchors(p,side)
        x,y = eye
        # A common upper hub keeps the full-width webs above both vent mounts.
        hub=(-99,59.5) if side==-1 else (99,59.5)
        primary_path=(eye,hub,bolt) if bolt[1]<eye[1] else (eye,bolt)
        def outline_shape(label, margin):
            webs = []
            for j,path in enumerate((primary_path,(eye,secondary))):
                for k,(start,target) in enumerate(zip(path,path[1:])):
                    dx,dy=target[0]-start[0],target[1]-start[1]
                    length=math.hypot(dx,dy)
                    r0 = (11 if start == eye else 7)+margin
                    r1 = (7 if target == hub else 6)+margin
                    ux,uy=dx/length,dy/length
                    tangent=(r0-r1)/length
                    normal=math.sqrt(1-tangent*tangent)
                    polygon=[]
                    for sign in (1,-1):
                        nx,ny=tangent*ux-sign*normal*uy,tangent*uy+sign*normal*ux
                        polygon.append((start[0]+r0*nx,start[1]+r0*ny))
                    for sign in (-1,1):
                        nx,ny=tangent*ux-sign*normal*uy,tangent*uy+sign*normal*ux
                        polygon.append((target[0]+r1*nx,target[1]+r1*ny))
                    webs.append(b.profile(f'Necklace{label}Web{i}{j}{k}',[polygon],E('rear_thickness'),E('necklace_link_thickness')))
            if len(primary_path)==3:
                webs.append(b.cylinder(f'Necklace{label}Hub{i}',7+margin,E('necklace_link_thickness'),E('rear_thickness'),*hub))
            return b.fuse(f'Necklace{label}Blank{i}',webs+[
                b.cylinder(f'Necklace{label}EyePad{i}',11+margin,E('necklace_link_thickness'),E('rear_thickness'),x,y),
                b.cylinder(f'Necklace{label}BoltPad{i}',6+margin,E('necklace_link_thickness'),E('rear_thickness'),*bolt),
                b.cylinder(f'Necklace{label}AnchorPad{i}',6+margin,E('necklace_link_thickness'),E('rear_thickness'),*secondary)])
        link = outline_shape('Link',0)
        clearance = outline_shape('Clearance',p['bracket_side_clearance'])
        doc.recompute()
        # The common external tangents meet the round pads without a web fillet.
        # Capsule slot: 12 x 4 mm, with rounded ends for replaceable 10 mm tape.
        slot = b.fuse(f'NecklaceSlot{i}',[
            b.box(f'NecklaceSlotWeb{i}',8,4,p['necklace_link_thickness'],x-4,y-2,rear),
            b.cylinder(f'NecklaceSlotEnd{i}a',2,p['necklace_link_thickness'],rear,x-4,y),
            b.cylinder(f'NecklaceSlotEnd{i}b',2,p['necklace_link_thickness'],rear,x+4,y)])
        link = b.cut(f'NecklaceDrilled{i}',link,[
            slot,b.cylinder(f'NecklaceBolt{i}',E('fastener_hole_radius'),E('necklace_link_thickness'),E('rear_thickness'),*bolt),
            b.cylinder(f'NecklaceAnchorBore{i}',1.7,E('necklace_link_thickness'),E('rear_thickness'),*secondary)])
        doc.recompute()
        # Round both lips of the webbing slot; retain the 5 mm plate and webs.
        slot_edges = [n for n,e in enumerate(link.Shape.Edges,1)
                      if e.BoundBox.ZLength < 1e-7
                      and e.BoundBox.XMin >= x-6.01 and e.BoundBox.XMax <= x+6.01
                      and e.BoundBox.YMin >= y-2.01 and e.BoundBox.YMax <= y+2.01]
        link = b.fillet(f'NecklaceLink{i}',link,.5,slot_edges)
        doc.recompute()
        b.add(link,'Manufactured',f'Necklace bracket {i+1} - replaceable two-anchor webbing plate',(.20,.22,.25),material='Printed PETG; 5 mm plate; print flat, solid local fill; two bolted frame connections; physical strength TODO')
        suspension.append(clearance)
        top = rear+p['necklace_link_thickness']
        sx,sy = secondary
        # This boss/radial rib belongs to the barrel, above the replaceable link.
        radial = math.hypot(sx,sy)
        rib = b.box(f'AnchorRib{i}',120-radial,8,deck_bottom-top,radial-1,-4,top)
        rib.Placement = App.Placement(App.Vector(),App.Rotation(App.Vector(0,0,1),math.degrees(math.atan2(sy,sx)))).multiply(rib.Placement)
        anchor_bosses += [b.cylinder(f'AnchorBoss{i}',5.5,deck_bottom-top,top,sx,sy),
                          b.circular_root(f'AnchorRoot{i}',5.5,deck_bottom,sx,sy,up=False),rib]
        anchor_tools.append(b.cylinder(f'AnchorScrewPassage{i}',1.7,8,top,sx,sy))
        # Local +Y is the nut loading direction; rotate the complete pocket.
        pocket,entry = b.nut_pocket(f'AnchorPocket{i}','M3',0,0,top+3.4,10)
        rotation=App.Rotation(App.Vector(0,0,1),math.degrees(math.atan2(sy,sx))+90)
        for item in (pocket,entry):
            item.Placement=App.Placement(App.Vector(sx,sy,0),rotation).multiply(item.Placement)
        anchor_tools += [pocket,entry]

    # Annular mirrors surround the circle. The outer strip emits through the
    # open edge band: no opaque barrel lies in front of its LED faces.
    front_expr = E('front_plane_z')
    inner_r, outer_r = ring_radius(p['inner_count'], p), ring_radius(p['outer_count'], p)
    inner_back = inner_r + p['strip_thickness']/2
    mirror_outer = inner_back + p['strip_wall'] - p['fit_clearance']/2
    halo_r = ring_radius(p['halo_count'], p)
    outer_wall_low = outer_r-p['strip_thickness']/2-p['strip_wall']
    # The structural barrel is behind the outward strip. The whole exterior
    # between the two narrow lips is a sheet diffuser, not an opaque skirt.
    shell = b.annulus('Barrel', outer_r-p['strip_thickness']/2-p['structural_wall'], outer_wall_low+p['strip_wall'], E('rear_thickness'), E('mirror_back_z')+'-'+E('strip_wall')+'-'+E('rear_thickness'))
    floor = b.annulus('RingFloor', 'Parameters.circle_diameter/2+0.5 mm', outer_r-p['strip_thickness']/2, E('mirror_back_z') + '-' + E('strip_wall'), E('strip_wall'))
    boundary = b.annulus('CircleBoundary', 'Parameters.circle_diameter/2+1 mm', halo_r-p['strip_thickness']/2, E('mirror_back_z'), E('front_plane_z') + '-' + E('mirror_back_z'))
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
    posts = [b.cylinder(f'LidPost{i}', E('post_radius'), E('front_plane_z') + '-' + E('rear_thickness'), E('rear_thickness'), x, y) for i, (x, y) in enumerate(points)]
    post_bridges = []
    for i,(x,y) in enumerate(points):
        rib = b.box(f'PostRearBridge{i}',outer_r-p['strip_thickness']/2-p['fastener_radius']+2,6,p['structural_wall'],p['fastener_radius']-2,-3,rear)
        rib.Placement = App.Placement(App.Vector(),App.Rotation(App.Vector(0,0,1),math.degrees(math.atan2(y,x)))).multiply(rib.Placement)
        post_bridges.append(rib)
    # Offset each root inward: its outside stays behind the outer strip,
    # and its inside stays outside the rear mirror.
    root_scale=(p['fastener_radius']-.6)/p['fastener_radius']
    post_roots = [b.cone(f'PostFloorRoot{i}',3.6,3,.6,p['mirror_back_z'],x*root_scale,y*root_scale) for i,(x,y) in enumerate(points)]
    frame = b.fuse('FrameBlank', [shell, floor, boundary, ledge] + walls + posts + post_roots + post_bridges + anchor_bosses)
    # Whole barrel prints joint-face-down. Every boss reaches that bed face.
    rear_bosses, rear_tools, rear_clearances = [], [], []
    for i,(x,y) in enumerate(rear_mounting_points(p)):
        angle = math.degrees(math.atan2(y,x))
        boss = b.fuse(f'RearMountBoss{i}',[b.cylinder(f'RearMountRound{i}',4.5,deck_bottom-rear,rear,112.5,0),b.box(f'RearMountRib{i}',7,8,deck_bottom-rear,112,-4,rear)])
        pocket,entry = b.nut_pocket(f'RearMountPocket{i}','M3',0,0,5.4,7)
        for item in (pocket,entry):
            item.Placement=App.Placement(App.Vector(112.5,0,0),App.Rotation(App.Vector(0,0,1),90)).multiply(item.Placement)
        clearance = b.box(f'RearMountClearance{i}',11.6,9.6,deck_bottom-rear,107.7,-4.8,rear)
        rear_clearances.append(clearance)
        for item in (boss,pocket,entry,clearance):
            item.Placement = App.Placement(App.Vector(),App.Rotation(App.Vector(0,0,1),angle)).multiply(item.Placement)
        rear_bosses.append(boss)
        rear_tools += [pocket,entry,b.cylinder(f'RearMountBore{i}',1.7,8,rear,x,y)]
    # Radial stops retain the outside ring through its full permitted lift.
    toe_tip=p['edge_diffuser_radius']-p['ring_seat_play']+p['ring_cuff_height']
    for i,angle in enumerate(ring_locating_angles(p,0)):
        toe = b.profile(f'EdgeSeat{i}',[[(outer_wall_low, rear),(toe_tip,rear),(toe_tip,p['edge_bottom_z']),(outer_wall_low,p['edge_bottom_z']+toe_tip-outer_wall_low)]],-2,4)
        toe.Placement = App.Placement(App.Vector(),App.Rotation(App.Vector(0,0,1),angle)*App.Rotation(App.Vector(1,0,0),90)).multiply(toe.Placement)
        rear_bosses.append(toe)
    # Six seats carry screw load; collar tops follow sheet stock and compressed silicone.
    seats = []
    for i,(x,y) in enumerate(points):
        # Keep the complete collar and most of the sheet bearing annulus.
        # The outward trim clears the continuous moving shield at every lift.
        land_round=b.cylinder(f'FrontLandRound{i}',4,1.2,front-1.2,x,y)
        land_envelope=b.cylinder(f'FrontLandEnvelope{i}',p['fastener_radius']+p['post_radius'],1.2,front-1.2)
        land=doc.addObject('Part::Common',f'FrontLand{i}')
        land.Base,land.Tool=land_round,land_envelope
        seats += [land,
                  b.fuse(f'FrontStop{i}',[
                      b.cylinder(f'FrontStopStem{i}',3,p['front_acrylic_thickness']+p['front_washer_compressed_height']-.15,front,x,y),
                      b.cone(f'FrontStopTip{i}',3,2.85,.15,front+p['front_acrylic_thickness']+p['front_washer_compressed_height']-.15,x,y)])]
    # Printable sleeve shoes/keyways lie behind the emitting surfaces. The
    # continuous front traps the sleeves; no fixed lip obstructs mirror removal.
    sleeve_seats, mirror_keys = [], []
    for name,d in cavity_diffusers(p).items():
        carrier = halo_r-p['strip_thickness']/2 if name=='Halo' else inner_back+p['strip_wall']
        lo,hi = (carrier-.2,d['outer']) if name=='Halo' else (d['inner'],carrier+.2)
        cuff_lo,cuff_hi = (d['inner']-p['ring_seat_play']-p['strip_wall'],d['inner']-p['ring_seat_play']) if name=='Halo' else (d['outer']+p['ring_seat_play'],d['outer']+p['ring_seat_play']+p['strip_wall'])
        for i,angle in enumerate(ring_locating_angles(p)):
            shoe = b.box(f'{name}Shoe{i}',hi-lo,3.6,d['bottom']-p['mirror_back_z'],lo,-1.8,p['mirror_back_z'])
            cuff_blank = b.annulus(f'{name}CuffBlank{i}',cuff_lo,cuff_hi,d['bottom'],p['ring_cuff_height'])
            cuff_tool = b.box(f'{name}CuffTool{i}',cuff_hi-cuff_lo+1,3.6,p['ring_cuff_height'],cuff_lo-.5,-1.8,d['bottom'])
            cuff = doc.addObject('Part::Common',f'{name}Cuff{i}')
            cuff.Base,cuff.Tool = cuff_blank,cuff_tool
            key = b.box(f'{name}MirrorKey{i}',hi-lo+.6,4.2,p['rear_acrylic_thickness'],lo-.3,-2.1,p['mirror_back_z'])
            for item in (shoe,cuff,key):
                item.Placement = App.Placement(App.Vector(),App.Rotation(App.Vector(0,0,1),angle)).multiply(item.Placement)
            sleeve_seats += [shoe,cuff]
            mirror_keys.append(key)
    frame = b.fuse('FrameWithSeats',[frame]+rear_bosses+seats+sleeve_seats)
    # Only internal wire passages remain. Close optical cavity lead gaps with
    # removable opaque sealant/tape after routing; none opens onto the outside.
    leads = [b.box(name+'LeadExit', p['ring_seam_gap'], 5, 5, -p['ring_seam_gap']/2, r-2.5, p['mirror_back_z']-p['strip_wall']) for name,r in [('Halo',halo_r),('Inner',inner_r),('Outer',outer_r)]]
    frame_entries = []
    for name,z,h in [('Deck',deck_bottom,depth-deck_bottom),('Barrel',rear,deck_bottom-rear)]:
        frame_entries += b.bore_entries(name+'BoreEntry',points,p['fastener_hole_radius'],z,z+h,top_entry=.15 if name=='Deck' else .3)
    frame_entries += [b.cone(f'RearBossEntry{i}',2,1.7,.3,rear,x,y) for i,(x,y) in enumerate(rear_mounting_points(p))]
    for i, clearance in enumerate(suspension):
        frame = b.cut(f'FrameBracketClearance{i}',frame,clearance)
    frame = b.cut('OpticalFrame', frame, holes('FrameBore', rear, depth-rear) + leads + anchor_tools + rear_tools + frame_entries + [b.top_mark('DeckTopMark',113,p['mirror_back_z']-.4), b.top_mark('BarrelTopMark',outer_r-p['strip_thickness']/2-p['structural_wall']+.45,10,True), b.annulus('SleeveSeatRelief',p['edge_diffuser_radius']-p['ring_seat_play'],radius+1,p['edge_bottom_z'],depth)])
    b.add(frame, 'Manufactured', '01 Hidden optical support - halo, inward mirror ring, centered outer row', (.15, .17, .20), material='Printed opaque polymer')

    # Six full-length bolts retain the optics. Separate screws retain the rear.
    rear_blank = b.cylinder('RearBlank', E('case_diameter') + '/2-' + E('fit_clearance'), E('rear_skin_thickness'))
    # One removable rear subassembly: skin, ribs, lands and integral mounts.
    vent_points = [(x,y) for x in (-95,95) for y in (-30,30)]
    control_points = [(-35,100),(35,100),(35,-100)]
    hatch_x,hatch_y = 48,54
    hatch_screws = (hatch_x-23,hatch_x+23)
    rear_cuts = [b.cylinder(f'RearBodyAccess{i}',5,rear+12,-1,x,y) for i,(x,y) in enumerate(points)]
    rear_cuts += [b.cylinder(f'RearHole{i}',1.7,rear+12,-1,x,y) for i,(x,y) in enumerate(rear_mounting_points(p))]
    rear_cuts += b.bore_entries('RearScrewEntry',rear_mounting_points(p),1.7,0,rear)
    rear_cuts += [b.cylinder(f'VentHole{i}',E('vent_hole_radius'),rear+12,-1,x,y) for i,(x,y) in enumerate(vent_points)]
    rear_cuts += [b.cylinder(f'RearControlBore{i}',4.2,rear+12,-1,x,y) for i,(x,y) in enumerate(control_points)]
    rear_cuts += [b.box('RearServiceOpening',38,18,rear+12,hatch_x-19,hatch_y-9,-1)]
    rear_cuts += [b.cylinder(f'RearHatchHole{i}',1.2,rear+12,-1,x,hatch_y) for i,x in enumerate(hatch_screws)]
    rear_cuts += [b.box(f'RearEyeClearance{i}',16,8,rear+12,x-8,58,-1) for i,x in enumerate((-82,82))]
    rear_cuts += [b.cylinder(f'RearAnchorAccess{i}',3.8,rear+12,-1,*necklace_anchors(p,side)[2]) for i,side in enumerate((-1,1))]
    # A reinforced, capped cable entry supports a belt battery without an open
    # side window. Actual gland thread, jacket and strain relief need fit checks.
    rear_cuts.append(b.cylinder('ExternalPowerBore','Parameters.external_port_diameter/2',rear+12,-1,p['external_port_x'],p['external_port_y']))
    rear_cuts.append(b.cylinder('ExternalPowerNutClearance','Parameters.external_port_diameter/2+2.25 mm',rear+12,rear,p['external_port_x'],p['external_port_y']))
    rear_cuts.append(b.top_mark('RearTopMark',112,p['rear_skin_thickness']-.4))
    rear_items = [rear_blank,b.annulus('RearSealRim',119,p['case_diameter']/2-p['fit_clearance'],0,E('rear_thickness'))]
    rear_items.append(b.cylinder('ExternalPowerLand',10,E('rear_thickness'),0,p['external_port_x'],p['external_port_y']))
    for i,(x,y) in enumerate(points+rear_mounting_points(p)+vent_points+control_points+[(x,hatch_y) for x in hatch_screws]):
        r = 10 if (x,y) in vent_points else 8 if (x,y) in control_points else 6
        rear_items += [b.cylinder(f'RearClampLand{i}',r,E('rear_thickness'),0,x,y),
                       b.circular_root(f'RearClampRoot{i}',r,p['rear_skin_thickness'],x,y)]
    rib_blanks = []
    for i,offset in enumerate((-80,-40,0,40,80)):
        rib_blanks += [b.box(f'RearRibX{i}',220,E('rear_rib_width'),E('rear_rib_height'),-110,offset-p['rear_rib_width']/2,E('rear_skin_thickness')),
                       b.box(f'RearRibY{i}',E('rear_rib_width'),220,E('rear_rib_height'),offset-p['rear_rib_width']/2,-110,E('rear_skin_thickness'))]
    ribs = doc.addObject('Part::Common','RearRibs')
    ribs.Base = b.fuse('RearRibGrid',rib_blanks)
    ribs.Tool = b.cylinder('RearRibLimit',110,p['rear_skin_thickness']+p['rear_rib_height'])
    rear_items.append(ribs)
    for i,offset in enumerate((-80,-40,0,40,80)):
        for j,angle in enumerate((0,90,180,270)):
            root = b.root_blend(f'RearRibBlend{i}{j}',200,offset+p['rear_rib_width']/2,-100,p['rear_skin_thickness'])
            root.Placement=App.Placement(App.Vector(),App.Rotation(App.Vector(0,0,1),angle))
            limited = doc.addObject('Part::Common',f'RearRibBlendLimit{i}{j}')
            limited.Base,limited.Tool = root,ribs.Tool
            rear_items.append(limited)
    for i,x in enumerate(hatch_screws):
        post,tools = b.service_mount(f'HatchStandoff{i}',x,hatch_y)
        rear_items.append(post)
        rear_cuts += tools

    # Guards remain separate, roof-down prints. Two screws replace adhesive;
    # pockets retain replaceable M2 nuts without heat-set inserts or snap tabs.
    for i,(x,y) in enumerate(vent_points):
        patch = b.cylinder(f'VentMembrane{i}',E('vent_patch_radius'),E('vent_patch_thickness'),-p['vent_patch_thickness'],x,y)
        b.add(patch,'Manufactured',f'Vent {i+1} - replaceable adhesive membrane',(.75,.77,.8),material='Nonprinted ePTFE adhesive patch; exact part and adhesion TODO')
        screws = [(x,y-11),(x,y+11)]
        feet = [b.box(f'VentGuardFoot{i}{j}',8,4,1.5,sx-4,sy-2,-1.5) for j,(sx,sy) in enumerate(screws)]
        roof = b.box(f'VentRoof{i}',20,28,p['structural_wall'],x-10,y-14,-p['structural_wall']-1.5)
        guard = b.fuse(f'VentGuardBlank{i}',[roof]+feet)
        guard = b.cut(f'VentGuard{i}',guard,[b.cylinder(f'VentGuardBore{i}{j}',1.2,5,-4,sx,sy) for j,(sx,sy) in enumerate(screws)])
        for j,(sx,sy) in enumerate(screws):
            post,tools = b.service_mount(f'VentMount{i}{j}',sx,sy)
            rear_items.append(post)
            rear_cuts += tools
        b.add(guard,'Manufactured',f'Vent {i+1} - removable two-screw guard',(.20,.22,.25),material='Printed PETG; two M2 screws into replaceable captive nuts; membrane remains accessible')
    hatch = b.box('ServiceCoverBlank',54,26,p['structural_wall'],hatch_x-27,hatch_y-13,-p['structural_wall']-.35)
    hatch = b.cut('ServiceCover',hatch,[b.cylinder(f'HatchCoverHole{i}',1.2,p['structural_wall'],-p['structural_wall']-.35,x,hatch_y) for i,x in enumerate(hatch_screws)])
    b.add(hatch,'Manufactured','Rear service cover - USB/programming access; two M2 captive-nut screws',(.20,.22,.25),material='Printed PETG; replaceable M2 nuts; 0.35 mm compressed closed-cell gasket')
    gasket = b.cut('HatchGasket',b.box('HatchGasketBlank',54,26,.35,hatch_x-27,hatch_y-13,-.35),[b.box('HatchGasketWindow',38,18,.35,hatch_x-19,hatch_y-9,-.35)]+[b.cylinder(f'HatchGasketHole{i}',1.2,.35,-.35,x,hatch_y) for i,x in enumerate(hatch_screws)])
    b.add(gasket,'Manufactured','Service hatch gasket - nominal compressed outline',(.3,.3,.3),material='Nonprinted closed-cell foam; material/compression TODO')

    carrier_items = []
    # Restrain one protected factory LiPo pack without altering its cell wiring.
    # Exchange a carried spare with power off; never parallel separate packs.
    bw,bl = p['battery_width'],p['battery_length']
    cradles = []
    for i,(bx,by) in enumerate(battery_centres(p)):
        outer = b.box(f'BatteryCradleOuter{i}',bw+4,bl+4,rear+10,bx-bw/2-2,by-bl/2-2,0)
        cavity = b.box(f'BatteryCradleCavity{i}',bw+2,bl+2,rear+12,bx-bw/2-1,by-bl/2-1,rear+1)
        cradle = b.cut(f'BatteryCradle{i}',outer,cavity)
        relief = b.box(f'BatteryFloorRelief{i}',bw-4,bl-4,rear+1,bx-bw/2+2,by-bl/2+2,p['rear_skin_thickness'])
        slots = []
        for j,x in enumerate((bx-bw/3,bx+bw/3)):
            for k,y in enumerate((by-bl/2-2,by+bl/2-2)):
                # A 45-degree roof leaves only a 2 mm bridge above the strap.
                polygon=[(x-6,rear+1),(x+6,rear+1),(x+6,rear+2),(x+1,rear+7),(x-1,rear+7),(x-6,rear+2)]
                slot=b.profile(f'BatteryStrapSlot{i}{j}{k}',[polygon],-y-4,4)
                slot.Placement=App.Placement(App.Vector(),App.Rotation(App.Vector(1,0,0),90)).multiply(slot.Placement)
                slots.append(slot)
        wire_exit = b.box(f'BatteryWireExit{i}',5,10,5,bx-bw/2-3,by-5,rear+1)
        cradles.append(b.cut(f'BatteryPocket{i}',cradle,[relief,wire_exit]+slots))
        battery = b.box(f'BatteryEnvelope{i}',E('battery_width'),E('battery_length'),E('battery_height'),bx-bw/2,by-bl/2,rear+1.5)
        b.add(battery,'Electronics',f'Protected 1S LiPo pack {i+1} - BatterySpace CU-MM109 nominal {bw:g} x {bl:g} x {p["battery_height"]:g} mm',(.26,.36,.48),30)
        battery.addProperty('App::PropertyString','ElectricalStatus').ElectricalStatus = 'Protected factory 1S 10 Ah LiPo fit candidate; separate Pololu 5 V boost, provisional 1.25 A total output cap. Disconnect for external charging. Four-hour bright runtime requires measured capacity, patterns, transients and heat.'
        reserve = b.box(f'BatteryHeadroom{i}',bw+2,bl+2,2.5,bx-bw/2-1,by-bl/2-1,rear+1.5+p['battery_height'])
        b.add(reserve,'Optics',f'Pack {i+1} - 2 mm fit/headroom plus 0.5 mm strap reserve',(.85,.55,.18),80)
    cradle = b.compound('BatteryPockets',cradles)
    rear_items += cradles

    for key, label, color in [('sparkle', 'Sparkle Motion Rev D', (.12, .35, .20)), ('blackpill', 'BlackPill V3.1', (.08, .10, .13)), ('gps', 'GPS FeatherWing placeholder', (.16, .35, .20)), ('imu', 'LSM9DS1 breakout placeholder', (.15, .36, .20)), ('radio', 'RF95 carrier placeholder', (.20, .32, .22)), ('sense', 'BlackPill PA4 raw-pack divider board placeholder', (.32, .26, .16)), ('power', 'Pololu U3V70F5 fixed 5 V boost envelope', (.12,.35,.20))]:
        x, y, w, l = [p[key + '_' + suffix] for suffix in ('x', 'y', 'width', 'length')]
        if key == 'sparkle':
            for i, (dx, dy) in enumerate(sparkle_holes):
                pocket, entry = b.nut_pocket(f'SparklePocket{i}','M2',x+dx,y+dy,2.4,5)
                standoff = b.cut(f'SparkleStandoff{i}', b.cylinder(f'SparkleStandBlank{i}', 3.8, rear+4, 0, x + dx, y + dy), [pocket,entry,b.cylinder(f'SparkleScrewHole{i}',1.2,7,p['rear_skin_thickness'],x+dx,y+dy)])
                root = b.cone(f'SparkleRoot{i}',4.4,3.8,.6,p['rear_skin_thickness'],x+dx,y+dy)
                carrier_items.append(b.fuse(f'SparkleMount{i}',[standoff,root]))
        else:
            # Open-ended rails avoid guessed mounting holes; straps retain each board.
            for side in (-1, 1):
                start = x + w / 2 - 1 if side == 1 else x - w / 2 - 2.5
                foot = b.box(f'{key}Foot{side:+}', 3.5, l + 4, rear+4, start, y - l / 2 - 2, 0)
                side_name='Right' if side==1 else 'Left'
                # Open windows under the bearing lip, above the continuous skin.
                # Keep end ribs and the tie land; the outer wall remains intact.
                inner_x = start if side==1 else start+2
                reliefs = [b.box(f'{key}FootRelief{side_name}{j}',1.5,(l-6)/2,2.8,
                                inner_x, yy, p['rear_skin_thickness'])
                           for j,yy in enumerate((y-l/2+1,y+3))]
                foot = b.cut(f'{key}OpenFoot{side_name}',foot,reliefs)
                wall = b.box(f'{key}Wall{side:+}', 2, l + 4, 7, x + side * (w / 2 + 1.5) - 1, y - l / 2 - 2, rear)
                rail = b.fuse(f'{key}Rail{side:+}', [foot, wall])
                slot = b.box(f'{key}TieSlot{side:+}', 6, 6, 1.5, start - 1, y - 3, rear + 1)
                blend = b.root_blend(f'{key}RailRoot{side_name}',l+4,start+3.5,y-l/2-2,p['rear_skin_thickness'])
                carrier_items.append(b.cut(f'{key}TieRail{side:+}', b.fuse(f'{key}BlendedRail{side_name}',[rail,blend]), slot))
        pcb = b.box(key + 'PCB', w, l, 1.6, x - w / 2, y - l / 2, rear + 4)
        if key == 'sparkle':
            pcb = b.cut('SparklePCBWithHoles', pcb, [b.cylinder(f'SparklePCBHole{i}', 1.2, 1.6, rear + 4, x + dx, y + dy) for i, (dx, dy) in enumerate(sparkle_holes)])
        b.add(pcb, 'Electronics', label + ' - PCB footprint', color)
        env = b.box(key + 'Components', w - 4, l - 4, p[key + '_height'] - 1.6, x - w / 2 + 2, y - l / 2 + 2, rear + 5.6)
        if key == 'sparkle':
            env = b.cut('sparkleComponentsWithMountKeepouts',env,[b.cylinder(f'SparkleDriverKeepout{i}',2.2,p[key+'_height'],rear+5.6,x+dx,y+dy) for i,(dx,dy) in enumerate(sparkle_holes)])
        b.add(env, 'Optics', label + ' - component clearance envelope', (.85, .55, .18), 70)
    mounts = b.compound('BoardMounts',carrier_items)
    rear_items += carrier_items
    reinforced = b.fuse('RearReinforcedBlank',rear_items)
    # Remove bracket volumes from tall ribs. Covers never carry suspension load.
    for i, clearance in enumerate(suspension):
        reinforced = b.cut(f'RearBracketClearance{i}',reinforced,clearance)
    back = b.cut('RearPlate',reinforced,rear_cuts+rear_clearances)
    b.add(back,'Manufactured','02 Removable PETG rear - thin skin, ribs and integral mounts',(.20,.22,.25),material='Printed PETG; 1 mm skin, 1.8 x 2 mm ribs; 2 mm clamp/seal lands; integral supports')
    plug_r = p['external_port_diameter']/2
    plug = b.fuse('ExternalPowerBlank',[b.cylinder('PowerBlankHead',plug_r+2,1,-1,p['external_port_x'],p['external_port_y']),
                                      b.cylinder('PowerBlankStem',plug_r-.25,rear+3,-1,p['external_port_x'],p['external_port_y']),
                                      b.cylinder('PowerBlankNut',plug_r+2,2,rear,p['external_port_x'],p['external_port_y'])])
    b.add(plug,'Electronics','External battery entry - gasketed blanking plug fit reference; replace with cable gland',(.20,.22,.25))
    for i, ((x,y),name) in enumerate(zip(control_points,('Mode','Action','Physical power'))):
        body = b.cylinder(f'RearButtonBody{i}',4,6,0,x,y)
        flange = b.cylinder(f'RearButtonFlange{i}',6,1.5,rear,x,y)
        b.add(b.fuse(f'RearButton{i}',[body,flange]),'Optics',name+' rear button - exact switch TBD',(.4,.4,.4))
        membrane = b.cylinder(f'ControlMembrane{i}',8,.5,-.5,x,y)
        b.add(membrane,'Manufactured',name+' flexible rear cover - no side peg',(.3,.3,.3),material='Nonprinted silicone/TPU membrane; seal perimeter; switch travel TODO')

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
    for name, count in [('Halo', int(p['halo_count'])), ('Inner', int(p['inner_count'])), ('Outer', int(p['outer_count']))]:
        r = ring_radius(count, p)
        bottom = '('+E('edge_bottom_z')+'+'+E('front_plane_z')+'-'+E('ring_front_clearance')+'-'+E('strip_width')+')/2' if name == 'Outer' else E('strip_bottom_z')
        strip = b.annulus(name + 'Strip', r - p['strip_thickness'] / 2, r + p['strip_thickness'] / 2, bottom, E('strip_width'))
        strip = b.cut(name + 'StripSeam', strip, b.box(name + 'SeamGap', E('ring_seam_gap'), 8, E('strip_width'), -p['ring_seam_gap'] / 2, r - 4, bottom))
        b.add(strip, 'Electronics', f'{name} ring - {count} pixels, wrapped strip, top seam', (.15, .15, .15))
        shapes = []
        outward = name != 'Inner'
        for i in range(count):
            (x,y),(nx,ny) = ring_pixel(count, i, outward, p)
            shape = Part.makeBox(p['ring_led_depth'], 5, 5, App.Vector(-p['ring_led_depth']/2, -2.5, -2.5))
            shape.Placement = App.Placement(App.Vector(x, y, strip_bottom(name,p) + p['strip_width'] / 2), App.Rotation(App.Vector(0, 0, 1), math.degrees(math.atan2(ny,nx))))
            shapes.append(shape)
        obj = doc.addObject('Part::Feature', name + 'LEDs')
        obj.Shape = Part.makeCompound(shapes)
        b.add(obj, 'Optics', f'{name} ring LED references - {"outward" if outward else "inward"} facing', (.85, .65, .30))
        obj.addProperty('App::PropertyString', 'EmissionDirection').EmissionDirection = 'Radially outward' if outward else 'Radially inward toward circle'

    rear_mirror = b.annulus('RearMirrorBlank', E('mirror_inner_radius'), inner_back-p['mirror_fit_clearance'], E('mirror_back_z'), E('rear_acrylic_thickness'))
    rear_mirror = b.cut('RearMirror',rear_mirror,[b.box('MirrorLeadNotch',E('ring_seam_gap'),6,E('rear_acrylic_thickness'),-p['ring_seam_gap']/2,inner_r-3,E('mirror_back_z'))]+mirror_keys)
    b.add(rear_mirror, 'Manufactured', '05 Rear mirror annulus - reflective face toward front', (.60,.65,.72),round(100*acrylic['two_way_mirror']['transmission']), material='1.5 mm two-way acrylic; nominal 70% reflection / 30% transmission; coating on +Z face')
    edge = b.annulus('EdgeDiffuser', E('edge_diffuser_radius'), E('edge_diffuser_radius')+'+'+E('edge_diffuser_thickness'), E('edge_bottom_z'), E('front_plane_z')+'-'+E('edge_bottom_z')+'-'+E('ring_front_clearance'))

    b.add(edge, 'Manufactured', 'OutsideRing - whole glow PETG print', DIFFUSER_TINT, DIFFUSER_TRANSPARENCY, material=f"Prusament PETG Ultraglow Green; {p['edge_diffuser_thickness']:g} mm wall; optical transmission unmeasured")

    # Curved bands diffuse the radial emitting faces. They do not cover the
    # flat front mirror annulus or replace the original printed Fibonacci baffle.
    for name,d in cavity_diffusers(p).items():
        band = b.annulus(name+'Ring',d['inner'],d['outer'],d['bottom'],d['height'])
        band.Label = name+'Ring - whole glow PETG print'
        b.add(band,'Manufactured',name+'Ring - whole glow PETG print',DIFFUSER_TINT,DIFFUSER_TRANSPARENCY,material='Prusament PETG Ultraglow Green; 1.0 mm wall; optical transmission unmeasured')
    for name,d in top_light_shields(p).items():
        shield = b.annulus(name+'LightShield',d['inner'],d['outer'],d['bottom'],d['height'])
        b.add(shield,'Manufactured',name+' opaque LED-edge shield - die-cut tape on ring top',(.015,.015,.015),material='tesa 7160 black PET light-blocking tape, 0.06 mm; adhesive on ring end face; retain liner beneath free span')
    # Original EGL STL walls, at the original STL's 2 mm thickness.
    stencil = b.profile('FibonacciBaffle', baffle.polygons(p), baffle_expr, E('baffle_thickness'))
    b.add(stencil, 'Manufactured', '08 Original EGL Fibonacci256 printed baffle', (.012,.012,.012), material='Opaque black PETG; original Jason Coon / Evil Genius Labs profile, CC Attribution; 2 mm flat print')
    doc.recompute()
    bases = [f for f in stencil.Shape.Faces if f.BoundBox.ZLength<1e-7 and abs(f.BoundBox.ZMin-baffle_z)<1e-7]
    # Three rim feet hold the PCB down. Select clear positions against the LED
    # package references rather than covering an assumed empty edge sector.
    top = p['circle_back_z'] + p['circle_pcb_thickness']
    for i in range(3):
        for delta in [0] + [s*d for d in range(1, 41) for s in (-1, 1)]:
            angle = i*120 + delta
            trial = Part.makeBox(2, 4, baffle_z-top, App.Vector(p['circle_diameter']/2-4, -2, top))
            trial.rotate(App.Vector(), App.Vector(0, 0, 1), angle)
            tops = [f for f in trial.Faces if f.BoundBox.ZLength<1e-7 and abs(f.BoundBox.ZMin-baffle_z)<1e-7]
            contact = sum(top.common(base).Area for top in tops for base in bases)
            if trial.common(leds.Shape).Volume < 1e-7 and contact>=1.5:
                foot = b.box(f'CircleRimFoot{i}', 2, 4, baffle_z-top, p['circle_diameter']/2-4, -2, top)
                foot.Placement = App.Placement(App.Vector(), App.Rotation(App.Vector(0,0,1), angle)).multiply(foot.Placement)
                b.add(foot, 'Manufactured', f'Circle rim spacer {i+1} - supports original printed baffle above LED packages', (.12, .12, .13), material='Opaque black PETG; tack to baffle for service, not to LEDs; inspect actual bearing and board clearance')
                break
        else:
            raise ValueError('No clear PCB rim retention position')
    sheet = b.cylinder('FrontSheetBlank','Parameters.case_diameter/2',E('front_acrylic_thickness'),front_expr)
    sheet = b.cut('FrontSheet',sheet,[b.cylinder(f'FrontSheetHole{i}',3.5,E('front_acrylic_thickness'),front_expr,x,y) for i,(x,y) in enumerate(points)])
    b.add(sheet,'Manufactured','09 One-piece black LED acrylic front with mirror annulus',(.025,.025,.025),round(100*acrylic['black_led']['transmission']),material='3 mm nominal black LED acrylic, not opaque black acrylic; cavity-facing mirror coating 85.5..110.5; estimated complete-sheet cavity R70/T9, reverse R10/T9; opaque rim and cut edge; custom coating data unmeasured')
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
    b.hide(frame)

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
            if 'Components' in obj.Name or obj.Name.startswith('BatteryHeadroom'):
                b.hide(obj)
        import FreeCADGui as Gui
        Gui.activeDocument().activeView().viewAxonometric()
        Gui.activeDocument().activeView().fitAll()
    doc.recompute()
    from hardware_spec import add_envelopes
    add_envelopes(b)
    check_model(b, centres, cells)
    doc.saveAs(str(master))
    export_files(b, centres, cells)
    print('CAD BUILD PASS:', master)
    return b


def validate_parameters(p):
    if (abs(p['mirror_back_z']-(p['rear_mirror_front_z']-p['rear_acrylic_thickness']))>1e-6
            or abs(p['front_washer_compressed_height']-p['front_washer_free_thickness']*p['front_washer_compression_ratio'])>1e-6
            or abs(p['case_depth']-(p['front_plane_z']+p['front_acrylic_thickness']+p['front_washer_compressed_height']))>1e-6
            or p['baffle_to_sheet_gap'] < .3):
        raise ValueError('Front needs compression-stop height and free baffle clearance')
    if (not .25 <= p['body_bolt_tip_projection'] <= .4
            or not .1 <= p['body_bolt_tip_chamfer'] <= .2
            or p['body_bolt_tip_projection']-p['body_bolt_tip_chamfer'] < .1-1e-7
            or body_bolt_length(p)>p['body_bolt_stock_length']):
        raise ValueError('Finished body bolts need full nut engagement, a deburred lead and adequate stock')
    if not (0 < p['assumed_efficiency'] <= 1):
        raise ValueError('Efficiency must lie in (0,1]')
    if p['battery_mass_g'] <= 0:
        raise ValueError('Battery mass must be positive')
    if not 10 <= p['external_port_diameter'] <= 14 or math.hypot(p['external_port_x'],p['external_port_y'])+10 >= p['case_diameter']/2-p['fit_clearance']:
        raise ValueError('External battery entry needs a bore within its reinforced rear land')
    for key in ('halo_count', 'inner_count', 'outer_count'):
        if int(p[key]) != p[key] or not 1 <= p[key] <= 512:
            raise ValueError('Ring counts must be integers in 1..512')
    if int(p['battery_count']) != p['battery_count'] or not 1 <= p['battery_count'] <= 2:
        raise ValueError('Use one or two separate pack pockets')
    if p['battery_spacing'] < p['battery_width']+4:
        raise ValueError('Battery pockets overlap or leave no lead channel')
    if not 1.8 <= p['structural_wall'] <= 2.2:
        raise ValueError('Structural barrel and covers need 1.8..2.2 mm walls')
    if int(p['ring_station_count']) != p['ring_station_count'] or p['ring_station_count'] < 3:
        raise ValueError('Ring locating stations need an integer count of at least three')
    if not .2 <= p['ring_seat_play'] <= .3 or p['ring_radial_error_budget'] < 0 or min(ring_led_clearances(p).values())-ring_movement_limit(p,p['ring_radial_error_budget']) < .5-1e-7:
        raise ValueError('Sleeve fit must preserve at least 0.5 mm LED clearance')
    if not .3 <= p['mirror_fit_clearance'] <= .5:
        raise ValueError('Rear mirror needs 0.3..0.5 mm outer radial clearance')
    if not .8 <= p['rear_skin_thickness'] < p['rear_thickness'] or p['rear_rib_width'] < 1.2 or p['rear_rib_height'] < 1:
        raise ValueError('Rear needs a printable skin, thicker clamp lands and structural ribs')
    if p['rear_skin_thickness']+p['rear_rib_height'] > p['rear_thickness']+1:
        raise ValueError('Rear ribs invade battery padding or board mount clearance')
    if not 5 <= p['necklace_link_thickness'] <= 6:
        raise ValueError('Necklace brackets need 5..6 mm thickness below the optical floor')
    if p['sparkle_rotation'] not in (0, 180):
        raise ValueError('The axis-aligned Sparkle footprint supports rotations 0 or 180 only')
    for key in ('battery_width', 'battery_length', 'battery_height', 'baffle_thickness', 'strip_density', 'shell_wall', 'rear_thickness', 'strip_wall', 'ring_led_depth', 'print_bed_x', 'print_bed_y'):
        if p[key] <= 0 or not math.isfinite(p[key]):
            raise ValueError(key + ' must be finite and positive')
    if p['baffle_thickness'] != 2 or p['circle_diameter'] != 166:
        raise ValueError('Retain original 166 mm board and 2 mm EGL stencil thickness')
    led_top = p['circle_back_z'] + p['circle_pcb_thickness'] + p['led_height']
    baffle_z = baffle_bottom(p)
    if not .5-1e-7 <= baffle_z-led_top <= .8+1e-7:
        raise ValueError('Original printed baffle must end 0.5..0.8 mm above LED packages')
    if p['rear_thickness']+1.5+p['battery_height']+2.5+1 > p['circle_back_z']:
        raise ValueError('Battery fit/headroom and strap leave less than 1 mm circle PCB clearance')
    for x,y in battery_centres(p):
        if math.hypot(abs(x)+p['battery_width']/2+2,abs(y)+p['battery_length']/2+2) >= p['case_diameter']/2-p['shell_wall']:
            raise ValueError('Battery cradle is outside the shell')
    optics = optical_dimensions(p)
    if p['ring_diffuser_thickness'] != 1 or p['ring_diffuser_led_gap'] < 1 or not .05 <= p['ring_bottom_clearance'] <= .2 or p['ring_cuff_height']+1e-7 < .8+.4 or p['ring_front_clearance'] != .5 or not .5 <= p['front_washer_compression_ratio'] <= .7:
        raise ValueError('Printed rings need specified walls, LED clearance, and axial retention')
    if not 0 < p['light_shield_thickness'] <= .1 or not .05 <= p['light_shield_edge_clearance'] <= .25:
        raise ValueError('Opaque LED-edge shields need thin tape and a clear frame edge')
    outside_shield=top_light_shields(p)['Outer']
    if outside_shield['inner']-p['fastener_radius']-p['post_radius']-ring_movement_limit(p,p['ring_radial_error_budget']) < .04-1e-7:
        raise ValueError('Outside shield must clear the trimmed front lands at every ring position')
    for name, dim in top_light_shields(p).items():
        count=int(p[name.lower()+'_count'])
        (x,y),_=ring_pixel(count,0,name!='Inner',p)
        margin=ring_movement_limit(p,p['ring_radial_error_budget'])
        if not dim['inner']+margin < math.hypot(x,y) < dim['outer']-margin:
            raise ValueError('Moving shield exposes an LED upper edge')
        wall_edge = (ring_radius(p['halo_count'],p)-p['strip_thickness']/2 if name == 'Halo'
                     else ring_radius(p['inner_count'],p)+p['strip_thickness']/2 if name == 'Inner'
                     else ring_radius(p['outer_count'],p)-p['strip_thickness']/2)
        radial_clearance = (dim['inner']-wall_edge if name != 'Inner' else wall_edge-dim['outer'])
        if radial_clearance-ring_movement_limit(p,p['ring_radial_error_budget']) < .04-1e-7:
            raise ValueError('Moving LED-edge shield can catch the opaque carrier')
        if dim['bottom']-(strip_bottom(name,p)+p['strip_width']) < .05-1e-7 or p['front_plane_z']-dim['bottom']-dim['height'] < .2:
            raise ValueError('LED-edge shield needs strip and front-sheet clearance')
    if optics['diffuser_gap'] < 18:
        raise ValueError('Curved diffusers leave less than 18 mm of radial mirror cavity')
    if optics['visible_mirror_width'] < 20 or optics['circle_to_inner_led'] < 20:
        raise ValueError('Infinity annulus requires at least 20 mm visible width and circle-to-LED gap')
    halo_r = optics['halo_radius']
    halo_face = halo_r+p['strip_thickness']/2+p['ring_led_depth']
    inner_face = optics['inner_radius']-p['strip_thickness']/2-p['ring_led_depth']
    if halo_r-p['strip_thickness']/2 <= p['circle_diameter']/2+1 or inner_face-halo_face < 20:
        raise ValueError('Halo needs a carrier wall and at least 20 mm to the inward LED faces')
    if p['strip_bottom_z'] < p['mirror_back_z'] + p['rear_acrylic_thickness'] + .2 or p['strip_bottom_z'] + p['strip_width'] > p['front_plane_z'] - .2:
        raise ValueError('Strip does not fit between the mirror surfaces')
    if optics['outer_led_clearance'] < .5:
        raise ValueError('Outer LED packages leave less than 0.5 mm diffuser clearance')
    if p['edge_diffuser_thickness'] < 2 or p['edge_diffuser_radius']+p['edge_diffuser_thickness'] > p['case_diameter']/2:
        raise ValueError('Outside printed ring needs at least a 2 mm wall and must fit the nominal front diameter')
    if outside_front_overlap(p) < 1.5:
        raise ValueError('Outside ring needs at least 1.5 mm continuous front-sheet overlap at maximum movement')
    if p['edge_bottom_z'] < p['rear_thickness']+1.2-1e-7 or optics['edge_height'] < 2*p['strip_width']:
        raise ValueError('Outside diffuser must span the body between the rear and front lips')
    # The outer strip sits outside the floor radius. It can span the floor's
    # height while the uninterrupted carrier behind it supports the strip.
    if strip_bottom('Outer',p) < p['rear_thickness']+.5 or strip_bottom('Outer',p)+p['strip_width'] > p['front_plane_z']-.5:
        raise ValueError('Centered outer strip does not clear the rear and front lips')
    if not 0 < p['vent_hole_radius'] < p['vent_patch_radius']-2 or p['vent_patch_radius'] > 8 or not 0 < p['vent_patch_thickness'] < 1.5:
        raise ValueError('Vent needs a membrane sealing land and clearance below its guard')
    if optics['inner_radius'] + p['strip_thickness']/2 + p['strip_wall'] >= p['fastener_radius']-p['post_radius']:
        raise ValueError('Perimeter posts intrude into the front mirror seat')
    # Actual 3D collision checks determine floor/seat clearance. A pack wholly
    # inside the central opening can extend above the annular floor plane.


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
    if len(b.doc.FibonacciBaffle.Shape.Solids) != 1:
        raise ValueError('Original baffle contains detached islands')
    for obj in b.parts:
        if obj.Name not in {'BoardMounts'} and len(obj.Shape.Solids) != 1:
            raise ValueError(obj.Name + ' is not one connected manufactured part: '+repr([(round(s.Volume,4),str(s.BoundBox)) for s in obj.Shape.Solids]))
    if len(centres) != 256 or len(cells) != 256:
        raise ValueError('Preview partitions must preserve 256 LED identities')
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
                overlap = a.Shape.common(other.Shape).BoundBox
                failures.append((a.Name, other.Name, round(volume, 4),
                                 (round(overlap.XMin, 3), round(overlap.YMin, 3),
                                  round(overlap.XMax, 3), round(overlap.YMax, 3))))
    if failures:
        raise ValueError('Unintended assembly collisions (mm^3): ' + repr(failures))
    # Tall component envelopes matter when controllers sit under the circle
    # opening instead of below the annular floor. Do not check just bare PCBs.
    for env in [o for o in b.references if o.Name.endswith('Components')]:
        for obj in b.parts+b.hardware:
            if env.Shape.common(obj.Shape).Volume > .05:
                raise ValueError('Component envelope collision: '+env.Name+' / '+obj.Name)
    for reserve in [o for o in b.references if o.Name.startswith('BatteryHeadroom')]:
        for obj in b.parts+b.hardware:
            if reserve.Shape.common(obj.Shape).Volume > .05:
                raise ValueError('Battery headroom/strap collision: '+reserve.Name+' / '+obj.Name)
    for i in range(2):
        link = b.doc.getObject(f'NecklaceLink{i}')
        # Solid common excludes a zero-volume bearing interface. Intersect
        # the coplanar top/bottom faces to measure the actual contact area.
        z = link.Shape.BoundBox.ZMax
        tops = [f for f in link.Shape.Faces if f.BoundBox.ZLength < 1e-7 and abs(f.BoundBox.ZMin-z) < 1e-7]
        seats = [f for f in b.doc.OpticalFrame.Shape.Faces if f.BoundBox.ZLength < 1e-7 and abs(f.BoundBox.ZMin-z) < 1e-7]
        area = sum(top.common(seat).Area for top in tops for seat in seats)
        if area < 10:
            raise ValueError('Necklace link does not bear directly on the body frame')
    for name in ('CircleLEDs','HaloLEDs','InnerLEDs','OuterLEDs'):
        leds = b.doc.getObject(name)
        for obj in b.parts:
            if leds.Shape.common(obj.Shape).Volume > .05:
                raise ValueError(f'{obj.Name} intersects {name}')
    for name,count,outward in [('Halo',int(b.p['halo_count']),True),('Inner',int(b.p['inner_count']),False),('Outer',int(b.p['outer_count']),True)]:
        # Light-path test at every LED angle. Mirror optics are not simulated.
        if name == 'Outer':
            end_radius = b.p['edge_diffuser_radius']-.05
        elif name == 'Halo':
            end_radius = optical_dimensions(b.p)['inner_radius']-b.p['strip_thickness']/2-b.p['ring_led_depth']-.05
        else:
            end_radius = b.p['mirror_view_inner_radius']+.05
        for i in range(count):
            (x,y),(nx,ny) = ring_pixel(count,i,outward,b.p)
            start = App.Vector(x+nx*(b.p['ring_led_depth']/2+.05),y+ny*(b.p['ring_led_depth']/2+.05),strip_bottom(name,b.p)+b.p['strip_width']/2)
            sign = 1 if outward else -1
            end = App.Vector(sign*nx*end_radius,sign*ny*end_radius,start.z)
            ray = Part.makeLine(start,end)
            if ray.common(b.doc.OpticalFrame.Shape).Length > .01:
                raise ValueError(f'Opaque frame blocks {name} pixel {i}')
            if name != 'Outer' and ray.common(b.doc.getObject(name+'Ring').Shape).Length < b.p['ring_diffuser_thickness']-.01:
                raise ValueError(f'Curved diffuser does not cover {name} pixel {i}')
    for name in ('Halo','Inner','Outer'):
        shield = b.doc.getObject(name+'LightShield')
        for i in range(int(b.p[name.lower()+'_count'])):
            (x,y),_ = ring_pixel(int(b.p[name.lower()+'_count']),i,name!='Inner',b.p)
            axial = Part.makeLine(App.Vector(x,y,strip_bottom(name,b.p)+b.p['strip_width']/2+2.5),
                                  App.Vector(x,y,b.p['front_plane_z']))
            if axial.common(shield.Shape).Length < b.p['light_shield_thickness']-.01:
                raise ValueError(f'LED upper edge has a direct unshielded path: {name} {i}')
    print('CAD geometry checks: connected parts, no product/LED collisions, inward and outward light paths clear',flush=True)


def fit_sample(shape, p):
    """One common cut contains a body collar, deck joint and rear captive nut."""
    sample=shape.copy()
    sample.rotate(App.Vector(),App.Vector(0,0,1),-p['fastener_phase_deg'])
    return sample.common(Part.makeBox(36,54,p['case_depth']+2,App.Vector(90,-8,-1)))


def optical_fit_sample(shape):
    """Exact deck sector containing both sleeve shoes at the 30-degree station."""
    sample=shape.copy()
    sample.rotate(App.Vector(),App.Vector(0,0,1),-30)
    return sample.common(Part.makeBox(34,10,45,App.Vector(82,-5,0)))


def service_fit_sample(shape):
    """Exact rear cut around the left hatch nut and its loading mouth."""
    return shape.common(Part.makeBox(10,15,8,App.Vector(20,47,0)))


def ring_fit_sample(shape):
    """Production wall and curvature over a short arc at the top of a ring."""
    radius = shape.BoundBox.YMax
    return shape.common(Part.makeBox(30,6,40,App.Vector(-15,radius-4,0)))


def controller_fit_sample(shape, p):
    """Rear skin, one board support, and its side-loading nut path."""
    x, y = p['sparkle_x']-22.86, p['sparkle_y']-13.97
    return shape.common(Part.makeBox(14,20,10,App.Vector(x-7,y-5,0)))


def export_files(b, centres, cells):
    out = HERE / 'exports'
    out.mkdir(exist_ok=True)
    manifest_path = out / 'parts.json'
    previous_meshes = set(json.loads(manifest_path.read_text())['stl_files']) if manifest_path.exists() else set()
    Part.export(b.parts + b.hardware + [b.doc.CircleLEDs, b.doc.HaloLEDs, b.doc.InnerLEDs, b.doc.OuterLEDs], str(out / 'smart-compass.step'))
    import MeshPart
    def print_mesh(shape):
        # Use the same fine circular tessellation for products and fit samples.
        return MeshPart.meshFromShape(Shape=shape,LinearDeflection=.02,AngularDeflection=.08,Relative=False)
    mesh_names = []
    volumes = []
    nonprinted = {'FrontSheet','RearMirror','HatchGasket'} | {o.Name for o in b.parts if o.Name.startswith(('VentMembrane','ControlMembrane','HaloRingPad','InnerRingPad')) or o.Name.endswith('LightShield')}
    for obj in b.parts:
        volumes.append({'name':obj.Name,'volume_cm3':round(obj.Shape.Volume/1000,4),'printed':obj.Name not in nonprinted,'bounds_mm':[round(getattr(obj.Shape.BoundBox,a+'Length'),3) for a in 'XYZ']})
        if obj.Name in nonprinted:
            continue
        for i,solid in enumerate(obj.Shape.Solids):
            # Translate each connected part onto Z=0 in its own bed footprint.
            shape = solid.copy()
            if obj.Name == 'BarrelFrame':
                # Joint face down; all barrel bosses start on the bed.
                shape.rotate(App.Vector(),App.Vector(1,0,0),180)
            bb = shape.BoundBox
            shape.translate(App.Vector(-bb.XMin,-bb.YMin,-bb.ZMin))
            bounds = shape.BoundBox
            if bounds.XLength+2*b.p['print_margin'] > b.p['print_bed_x'] or bounds.YLength+2*b.p['print_margin'] > b.p['print_bed_y']:
                raise ValueError('Printed part does not fit the configured bed: '+obj.Name)
            name = obj.Name + (f'-{i+1:02}' if len(obj.Shape.Solids)>1 else '') + '.stl'
            print_mesh(shape).write(str(out/name))
            mesh_names.append(name)
    fit_samples = []
    for name, parent in (('FitFibonacciBaffle','FibonacciBaffle'),('FitDeck','OpticalDeck'),('FitBarrel','BarrelFrame'),('FitRear','RearPlate'),('FitOptics','OpticalDeck'),('FitService','RearPlate'),('FitSuspensionBracket','NecklaceLink1'),('FitSuspensionBracketLeft','NecklaceLink0'),('FitSuspensionFrame','BarrelFrame'),('FitSuspensionRear','RearPlate'),('FitController','RearPlate'),('FitRingHalo','HaloRing'),('FitRingInner','InnerRing'),('FitRingOutside','EdgeDiffuser')):
        source = b.doc.getObject(parent).Shape
        sample = (source.copy() if name=='FitFibonacciBaffle' or name.startswith('FitSuspensionBracket') else source.common(Part.makeBox(40,50,25,App.Vector(70,35,0))) if name.startswith('FitSuspension') else optical_fit_sample(source) if name=='FitOptics' else service_fit_sample(source) if name=='FitService' else controller_fit_sample(source,b.p) if name=='FitController' else ring_fit_sample(source) if name.startswith('FitRing') else fit_sample(source,b.p))
        if not sample.isValid() or len(sample.Solids)!=1:
            raise ValueError('Disconnected fit sample: '+name)
        if parent == 'BarrelFrame':
            sample.rotate(App.Vector(),App.Vector(1,0,0),180)
        bb=sample.BoundBox
        sample.translate(App.Vector(-bb.XMin,-bb.YMin,-bb.ZMin))
        filename=name+'.stl'
        print_mesh(sample).write(str(out/filename))
        fit_samples.append({'file':filename,'source_part':parent,'purpose':'Disposable fit test, not an assembly part'})
    # Remove superseded generator-owned STL outputs, never user-created files.
    for name in previous_meshes - set(mesh_names):
        if Path(name).name != name or not name.endswith('.stl'):
            raise ValueError('Invalid generator-owned STL name: '+name)
        (out/name).unlink(missing_ok=True)
    printed_volume = sum(v['volume_cm3'] for v in volumes if v['printed'])
    (out/'parts.json').write_text(json.dumps({'stl_files':mesh_names,'volumes':volumes,
        'printed_volume_cm3':round(printed_volume,4),'optics_mm':optical_dimensions(b.p),
        'parameters_for_inventory':b.p,'fit_samples':fit_samples,
        'print_basis':{'bed_mm':[b.p['print_bed_x'],b.p['print_bed_y']],'margin_mm':b.p['print_margin'],
                       'nozzle_mm':.4,'layer_mm':.2,'orientation':'Delivered projects preserve the intended bed face'}},indent=2)+'\n')
    svg_files(b, cells, out)
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
<text x="{-r}" y="20">Circle: LEDs → single {b.p['baffle_thickness']:g} mm original printed baffle → {b.p['front_acrylic_thickness']:g} mm acrylic.</text>
</g></svg>'''
    (out / 'assembly-section.svg').write_text(drawing)


def svg_files(b, cells, out):
    p = b.p
    # Nominal design contours. Apply measured kerf once in the laser CAM software.
    r = p['circle_diameter'] / 2
    def document(paths, description, r=r):
        return '<svg xmlns="http://www.w3.org/2000/svg" width="%gmm" height="%gmm" viewBox="%g %g %g %g">\n<title>%s</title>\n<desc>PROVISIONAL alignment and material fit; nominal paths, no kerf compensation. Front view, X right, Y up.</desc>\n<g transform="scale(1,-1)" fill="none" stroke="#ff0000" stroke-width="0.08">\n%s\n</g></svg>\n' % (2*r, 2*r, -r, -r, 2*r, 2*r, escape(description), '\n'.join(paths))
    outline = f'<circle cx="0" cy="0" r="{r:.6f}"/>'
    sheet_paths = [f'<circle cx="0" cy="0" r="{p["case_diameter"]/2:.6f}"/>']
    sheet_paths += [f'<circle cx="{x:.6f}" cy="{y:.6f}" r="3.500000"/>' for x,y in mounting_points(p)]
    from hardware_spec import SOFT_WASHER
    washer_paths=[f'<circle cx="0" cy="0" r="{SOFT_WASHER[key]/2:.6f}"/>' for key in ('od','id')]
    (out/'soft-front-washer.svg').write_text(document(washer_paths,
        f'Six soft front retention washers; {SOFT_WASHER["free_thickness"]:g} mm silicone stock; knife/die cut; compression must be tested',SOFT_WASHER['od']/2+1))
    (out/'fit-sheet.svg').write_text(document(['<path d="M -9,-9 H 9 V 9 H -9 Z"/>','<circle cx="0" cy="0" r="3.500000"/>'],'FIT SAMPLE ONLY: 18 mm square in actual front-sheet stock; test on FitDeck collar',9))
    (out/'front-sheet.svg').write_text(document(sheet_paths,'One front sheet; 3 mm black LED acrylic nominal; six 7.0 mm locating holes',p['case_diameter']/2))
    for name, dim in top_light_shields(p).items():
        paths = [f'<circle cx="0" cy="0" r="{dim[key]:.6f}"/>' for key in ('outer','inner')]
        (out/(name.lower()+'-light-shield.svg')).write_text(document(paths,
            f'{name} opaque LED-edge shield; die-cut 0.06 mm tesa 7160; retain release liner below free span; bond only to printed ring top',dim['outer']))
    (out/'front-coating.svg').write_text(document([f'<circle cx="0" cy="0" r="{v:.6f}"/>' for v in (p['mirror_view_inner_radius'],p['mirror_view_outer_radius'],p['case_diameter']/2)],'COATING MAP ONLY, DO NOT CUT: black LED centre; rear-facing two-way mirror 85.5..110.5; opaque rim 110.5..125 and cut edge',p['case_diameter']/2))
    inner_r = ring_radius(p['inner_count'],p)
    rear_outer = inner_r+p['strip_thickness']/2
    # Export the actual keyed mirror contour. Polygon chord error <=0.02 mm.
    face = next(f for f in b.doc.RearMirror.Shape.Faces if f.BoundBox.ZLength<1e-7 and abs(f.BoundBox.ZMin-p['mirror_back_z'])<1e-7)
    paths=[]
    for wire in face.Wires:
        # OCC wire sampling can exceed its requested deflection at edge joins.
        # Use half the allowed error; check.py measures the exported chords.
        points=wire.discretize(Deflection=.01)
        paths.append('<polygon points="'+' '.join(f'{v.x:.6f},{v.y:.6f}' for v in points)+'"/>')
    (out/'rear-mirror.svg').write_text(document(paths,'Rear mirror with printed-ring locating notches; reflective face toward front',rear_outer))
    # The inspection overlay never enters a laser cut file.
    overlay=[outline, '<path d="M -50,-92 L 50,-92 M -50,-90 L -50,-94 M 50,-90 L 50,-94"/>']
    overlay += ['<polygon points="'+' '.join(f'{x:.6f},{y:.6f}' for x,y in polygon)+'"/>' for polygon in baffle.polygons(p)]
    overlay += [f'<rect x="{x-2.5:.6f}" y="{y-2.5:.6f}" width="5" height="5"/>' for x,y in led_centres(json.loads((HERE/'fibonacci256-layout.json').read_text()),p)]
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
        offset = 65 if obj.Name in {'FrontSheet'} else {'FibonacciBaffle':35}.get(obj.Name,20 if obj.Name.startswith('CircleRimFoot') else 0)
        if not offset:
            continue
        moved.append((obj, obj.Placement))
        pl = obj.Placement
        pl.Base.z += offset
        obj.Placement = pl
    transparent=[(obj,obj.ViewObject.Transparency) for obj in (b.doc.FrontSheet,b.doc.RearMirror)]
    for obj,_ in transparent:
        obj.ViewObject.Transparency=65
    b.doc.recompute()
    Gui.updateGui()
    view.fitAll()
    view.saveImage(str(out / 'exploded.png'), 1600, 1400, 'White')
    for obj,alpha in transparent:
        obj.ViewObject.Transparency=alpha
    for obj, pl in moved:
        obj.Placement = pl
    b.doc.recompute()
    # Isolate all three sleeves and their LEDs at assembled positions so their
    # radial coverage stays visible without the front mirror or printed frame.
    products = b.parts+b.hardware+b.references
    visibility = [(obj,obj.Visibility) for obj in products]
    diffuser_view = {'HaloRing','InnerRing','EdgeDiffuser','HaloLightShield','InnerLightShield','OuterLightShield','HaloLEDs','InnerLEDs','OuterLEDs','HaloStripSeam','InnerStripSeam','OuterStripSeam'}
    for obj in products:
        obj.Visibility = obj.Name in diffuser_view
    Gui.updateGui()
    view.viewAxonometric()
    view.fitAll()
    view.saveImage(str(out / 'diffusers.png'), 1600, 1200, 'White')
    for obj,was_visible in visibility:
        obj.Visibility = was_visible
    # Remove the face/frame in this preview to show the rear's integral ribs,
    # individual battery pockets and electronics. Normal rear view stays opaque.
    hidden = [obj for obj in b.parts+b.hardware+b.references if not (obj.Name.startswith(('RearPlate','NecklaceLink','BatteryEnvelope')) or obj in b.hardware and obj.Name != 'CirclePCB' and 'Strip' not in obj.Name)]
    visibility = [(obj,obj.Visibility) for obj in hidden]
    for obj in hidden:
        obj.Visibility = False
    Gui.updateGui()
    view.viewAxonometric()
    view.fitAll()
    view.saveImage(str(out / 'electronics.png'), 1400, 1400, 'White')
    for obj,was_visible in visibility:
        obj.Visibility = was_visible
    view.viewRear()
    view.fitAll()
    view.saveImage(str(out / 'edge.png'), 1600, 900, 'White')
    # Look at the rear with physical +Y still up (Bottom flips the top down).
    view.setCameraOrientation(App.Rotation(App.Vector(0,1,0),180))
    view.fitAll()
    view.saveImage(str(out / 'rear.png'), 1400, 1400, 'White')
    view.viewAxonometric()
    view.fitAll()
    b.doc.save()
    view.setAnimationEnabled(animation)
