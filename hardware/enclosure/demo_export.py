"""Export the saved assembly in metres; preview alternatives never alter the master.

The small GLB writer uses FreeCAD tessellation, not print-bed STL coordinates.
CAD and Godot both use X right, Y up, Z toward the front viewer.
"""
import hashlib
import json
import math
from pathlib import Path
import struct

from geometry import cavity_diffusers, led_centres, mask_cells, mounting_points, ring_pixel, ring_radius, strip_bottom

HERE = Path(__file__).resolve().parent


class GLB:
    def __init__(self):
        self.data = bytearray()
        self.doc = {'asset': {'version': '2.0', 'generator': 'FreeCAD assembled preview'},
                    'scene': 0, 'scenes': [{'nodes': []}], 'nodes': [], 'meshes': [],
                    'materials': [], 'accessors': [], 'bufferViews': []}

    def accessor(self, values, fmt, kind, component, bounds=False):
        while len(self.data) % 4:
            self.data.append(0)
        start = len(self.data)
        for value in values:
            self.data.extend(struct.pack('<' + fmt, *value))
        views = self.doc['bufferViews']
        views.append({'buffer': 0, 'byteOffset': start, 'byteLength': len(self.data)-start})
        record = {'bufferView': len(views)-1, 'componentType': component, 'count': len(values), 'type': kind}
        if bounds:
            record.update(min=[min(v[i] for v in values) for i in range(3)],
                          max=[max(v[i] for v in values) for i in range(3)])
        self.doc['accessors'].append(record)
        return len(self.doc['accessors'])-1

    def mesh(self, name, shape, color, variant='common', role='solid', label=None):
        import MeshPart
        mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=.12, AngularDeflection=.20, Relative=False)
        points, triangles = mesh.Topology
        positions, normals = [], []
        # Flat normals preserve tiny cell walls and sharp mechanical edges.
        for triangle in triangles:
            a, b, c = [points[i] for i in triangle]
            normal = (b-a).cross(c-a)
            if normal.Length < 1e-12:
                continue
            normal.normalize()
            for point in (a, b, c):
                positions.append(tuple(v/1000 for v in point))
                normals.append(tuple(normal))
        position = self.accessor(positions, 'fff', 'VEC3', 5126, True)
        normal = self.accessor(normals, 'fff', 'VEC3', 5126)
        material = len(self.doc['materials'])
        self.doc['materials'].append({'name': name, 'doubleSided': True,
            'pbrMetallicRoughness': {'baseColorFactor': [*color, 1], 'metallicFactor': 0, 'roughnessFactor': .65}})
        self.doc['meshes'].append({'name': name, 'primitives': [{'attributes': {'POSITION': position, 'NORMAL': normal}, 'material': material}]})
        self.doc['scenes'][0]['nodes'].append(len(self.doc['nodes']))
        self.doc['nodes'].append({'name': name, 'mesh': len(self.doc['meshes'])-1})
        bb = shape.BoundBox
        return {'name': name, 'label': label or name, 'variant': variant, 'role': role,
                'bounds_m': [[bb.XMin/1000, bb.YMin/1000, bb.ZMin/1000], [bb.XMax/1000, bb.YMax/1000, bb.ZMax/1000]],
                'volume_cm3': shape.Volume/1000}

    def save(self, path):
        self.doc['buffers'] = [{'byteLength': len(self.data)}]
        text = json.dumps(self.doc, separators=(',', ':')).encode()
        text += b' ' * (-len(text) % 4)
        self.data += b'\0' * (-len(self.data) % 4)
        path.write_bytes(struct.pack('<III', 0x46546c67, 2, 28+len(text)+len(self.data)) +
                         struct.pack('<II', len(text), 0x4e4f534a) + text +
                         struct.pack('<II', len(self.data), 0x004e4942) + self.data)


def export():
    import FreeCAD as App
    import Part
    import build
    master = HERE/'smart-compass.FCStd'
    original = hashlib.sha256(master.read_bytes()).hexdigest()
    p = build.read_parameters(master)
    source = App.openDocument(str(master))
    out = HERE/'exports'
    glb, parts = GLB(), []
    front = p['case_depth']-p['front_bezel_thickness']-p['acrylic_thickness']
    rear = p['mirror_back_z']+p['mirror_back_thickness']
    centers = led_centres(json.loads((HERE/'fibonacci256-layout.json').read_text()), p)
    cells = mask_cells(centers, p['mask_edge_radius'], p['mask_web'])
    leds = []
    for i, (x,y) in enumerate(centers):
        leds.append({'group': 0, 'index': i, 'position_m': [x/1000, y/1000, (p['circle_back_z']+p['circle_pcb_thickness']+p['led_height'])/1000], 'direction': [0,0,1]})
    for group, name in enumerate(('Halo','Inner','Outer'), 1):
        for i in range(int(p[name.lower()+'_count'])):
            (x,y),(nx,ny) = ring_pixel(p[name.lower()+'_count'], i, name != 'Inner', p)
            # Emitting surface, rather than the centre of the LED package.
            x += nx*p['ring_led_depth']/2
            y += ny*p['ring_led_depth']/2
            leds.append({'group': group, 'index': i, 'position_m': [x/1000,y/1000,(strip_bottom(name,p)+p['strip_width']/2)/1000], 'direction': [nx,ny,0]})
    replaced = {'FrontAcrylic','FrontBezel','FrontMirror','CircleBezel','EdgeDiffuserSeam','WoodMask'}
    replaced |= {f'CircleRimFoot{i}' for i in range(3)}
    replaced |= {f'{name}DiffuserPad{i}' for name in ('Halo','Inner') for i in range(3)}
    replaced |= {f'OpticalDeckQ{i}' for i in range(1,5)}
    objects = [o for group in (source.Manufactured,source.Electronics,source.Optics) for o in group.Group if o.Visibility]
    def add(name, shape, color, variant='common', role='solid', label=None):
        parts.append(glb.mesh(name,shape,color,variant,role,label))
    for obj in objects:
        role = 'solid'
        if obj.Name.endswith('LEDs'):
            role = 'packages'
        if obj.Name in ('HaloDiffuser','InnerDiffuser','EdgeDiffuserSeam'):
            role = 'sleeve'
        if obj.Name == 'FrontMirror':
            role = 'cavity'
        if obj.Name == 'FrontAcrylic':
            role = 'centre'
        add(obj.Name,obj.Shape,tuple(obj.ViewObject.ShapeColor[:3]),'current' if obj.Name in replaced else 'common',role,obj.Label)
    # Light exits through the same cell contours as the single wood grid.
    for i, polygon in enumerate(cells):
        wire = Part.makePolygon([App.Vector(x,y,front-.015) for x,y in polygon+[polygon[0]]])
        add(f'Cell{i:03}',Part.Face(wire),(.1,.1,.1),role='cell')

    def ring(inner,outer,z,height):
        return Part.makeCylinder(outer,height,App.Vector(0,0,z)).cut(Part.makeCylinder(inner,height,App.Vector(0,0,z)))
    # Preview design only: machine the existing deck down to the fixed plane.
    # Six 8 mm bearing lands carry the sheet directly to the body posts.
    # Integral 6 mm collars locate 6.4 mm sheet holes and stop washer travel.
    trim = Part.makeBox(300,300,20,App.Vector(-150,-150,front))
    deck = source.OpticalFrame.Shape.cut(trim)
    seats = []
    for x,y in mounting_points(p):
        land = Part.makeCylinder(4,2,App.Vector(x,y,front-2))
        land = land.cut(Part.makeCylinder(p['fastener_hole_radius'],2,App.Vector(x,y,front-2)))
        collar = Part.makeCylinder(3,1.5,App.Vector(x,y,front))
        collar = collar.cut(Part.makeCylinder(p['fastener_hole_radius'],1.5,App.Vector(x,y,front)))
        land = land.fuse(collar)
        seats.append(land)
    deck = deck.multiFuse(seats).removeSplitter()
    # Existing inner carrier is the radial seat. Small axial stops clamp only
    # the hidden mirror margin, beyond the 110.5 mm useful front aperture.
    captive = []
    inner = ring_radius(p['inner_count'],p)
    for angle in (30,150,270):
        a = math.radians(angle)
        r = inner-.35
        pad = Part.makeCylinder(.55,.4,App.Vector(r*math.cos(a),r*math.sin(a),rear))
        bridge = Part.makeBox(2,1.1,.4,App.Vector(r,-.55,rear))
        bridge.rotate(App.Vector(),App.Vector(0,0,1),angle)
        captive.extend([pad,bridge])
    deck = deck.multiFuse(captive).removeSplitter()
    # Sleeve end shoes capture 0.1 mm of each end on its LED-facing side.
    # They stay behind the cylindrical emitting surface and off useful rays.
    dims = cavity_diffusers(p)
    for name,d in dims.items():
        r0,r1 = (d['inner']-.6,d['inner']+.2) if name=='Halo' else (d['outer']-.2,d['outer']+.6)
        for angle in (30,150,270):
            shoe = ring(r0,r1,rear,.1)
            sector = Part.makeBox(4,1.2,.1,App.Vector(r0-1,-.6,rear))
            sector.rotate(App.Vector(),App.Vector(0,0,1),angle)
            shoe = shoe.common(sector)
            # Integral stem joins carrier behind the LEDs; top shoe uses the
            # continuous front as its axial stop, not another full ring.
            start = ring_radius(p[name.lower()+'_count'],p)
            lo,hi = sorted((start,r1 if name=='Halo' else r0))
            bridge = Part.makeBox(hi-lo+.4,1.2,.1,App.Vector(lo-.2,-.6,rear))
            bridge.rotate(App.Vector(),App.Vector(0,0,1),angle)
            deck = deck.fuse(shoe).fuse(bridge)
    # Keep four connected printable quarters; exact preview volumes feed mass.
    proposal_shapes = []
    for i,(sx,sy) in enumerate(((1,1),(-1,1),(-1,-1),(1,-1)),1):
        quarter = deck.common(Part.makeBox(150,150,front+1.5-(p['mirror_back_z']-p['strip_wall']),App.Vector(0 if sx>0 else -150,0 if sy>0 else -150,p['mirror_back_z']-p['strip_wall'])))
        assert quarter.isValid() and len(quarter.Solids)==1, 'Disconnected preview deck'
        assert quarter.BoundBox.XLength+10<=p['print_bed_x'] and quarter.BoundBox.YLength+10<=p['print_bed_y']
        proposal_shapes.append(quarter)
        add('ProposalDeck'+str(i),quarter,(.15,.17,.20),'proposal')
    # Retain the outer sleeve: shorten its upper lip to the unchanged mirror plane.
    edge = source.EdgeDiffuserSeam.Shape.cut(trim)
    add('ProposalEdge',edge,(.025,.025,.025),'proposal','sleeve')
    sheet = Part.makeCylinder(p['case_diameter']/2,1.5,App.Vector(0,0,front))
    for x,y in mounting_points(p):
        sheet = sheet.cut(Part.makeCylinder(3.2,1.5,App.Vector(x,y,front)))
    # One physical sheet, separate render regions permit coating comparison.
    center = Part.makeCylinder(p['circle_diameter']/2,1.5,App.Vector(0,0,front))
    optical = ring(p['circle_diameter']/2,p['mirror_view_outer_radius'],front,1.5)
    rim = sheet.cut(Part.makeCylinder(p['mirror_view_outer_radius'],1.5,App.Vector(0,0,front)))
    add('ProposalCentre',center,(.7,.8,.9),'proposal','centre')
    add('ProposalMirror',optical,(.6,.7,.8),'proposal','cavity')
    add('ProposalRim',rim,(.018,.018,.018),'proposal')
    # Keep a free gap under the sheet. The same grid sits 0.1 mm lower;
    # shortened feet preserve 0.2 mm LED clearance without screw preload.
    wood = source.WoodMask.Shape.copy()
    wood.translate(App.Vector(0,0,-.1))
    add('ProposalWood',wood,(.53,.32,.13),'proposal')
    feet = []
    foot_top = source.CircleRimFoot0.Shape.BoundBox.ZMax-.1
    foot_trim = Part.makeBox(300,300,20,App.Vector(-150,-150,foot_top))
    for i in range(3):
        foot = source.getObject(f'CircleRimFoot{i}').Shape.cut(foot_trim)
        feet.append(foot)
        add('ProposalFoot'+str(i),foot,(.12,.12,.13),'proposal')
    assert abs(wood.BoundBox.ZMin-source.CircleLEDs.Shape.BoundBox.ZMax-.2)<1e-7
    assert abs(front-wood.BoundBox.ZMax-.1)<1e-7
    # Concealed centre support uses the existing circle boundary at r=84..85.2.
    # It reaches the sheet plane; wood remains seated with zero screw preload.
    # No new full cell grid or load path through LED packages.
    led_shapes = [source.getObject(n+'LEDs').Shape for n in ('Circle','Halo','Inner','Outer')]
    for shape in proposal_shapes:
        assert all(shape.common(led).Volume<.05 for led in led_shapes), 'Preview support intersects LED'
        assert shape.common(sheet).Volume<1e-6, 'Sheet intersects its locating seat'
        assert shape.common(source.WoodMask.Shape).Volume<1e-6, 'Clamp structure intersects wood'
        for name in ('RearMirror','HaloDiffuser','InnerDiffuser'):
            assert shape.common(source.getObject(name).Shape).Volume<1e-6, 'Captive feature intersects '+name
    # Reuse the native build's radial path boundary convention for the mounts.
    for led in leds:
        group = led['group']
        if group==0:
            continue
        position = App.Vector(*[v*1000 for v in led['position_m']])
        normal = App.Vector(*led['direction'])
        end_radius = (ring_radius(p['inner_count'],p)-p['strip_thickness']/2-p['ring_led_depth']-.05
                      if group==1 else p['mirror_view_inner_radius']+.05
                      if group==2 else p['edge_diffuser_radius']-.05)
        end = normal*end_radius*(-1 if group==2 else 1)
        end.z = position.z
        ray = Part.makeLine(position+normal*.05,end)
        assert ray.common(deck).Length<.01, 'Preview mount blocks radial light path'
    # Actual CAD sections through one bolt and the centre, with independent
    # colours for the load-bearing frame and continuous acrylic sheet.
    angle = math.radians(p['fastener_phase_deg'])
    axis = App.Vector(math.cos(angle),math.sin(angle),0)
    corners = [axis*x+App.Vector(0,0,z) for x,z in ((-135,-5),(135,-5),(135,45),(-135,45))]
    plane = Part.Face(Part.makePolygon(corners+[corners[0]]))
    section_shapes = [(sheet,'#0072b2'),(wood,'#a4692a'),*((s,'#555555') for s in proposal_shapes+feet)]
    section_shapes += [(o.Shape,'#a4692a' if o.Name=='WoodMask' else '#999999') for o in objects if o.Name not in replaced]
    paths = []
    for shape,color in section_shapes:
        for section_edge in shape.section(plane).Edges:
            points = section_edge.discretize(Deflection=.08)
            paths.append('<polyline fill="none" stroke="'+color+'" stroke-width=".18" points="'+' '.join(f'{v.dot(axis):.5f},{-v.z:.5f}' for v in points)+'"/>')
    (out/'single-sheet-section.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="290mm" height="90mm" viewBox="-145 -65 290 90"><title>Proposed single sheet: section through body bolt and circle</title>'+''.join(paths)+f'<g font-family="sans-serif" font-size="3.5"><text x="-135" y="-58">PREVIEW ONLY: one 250 x 1.5 mm sheet, black masked rim</text><text x="-135" y="-51">6 mm printed collars / 6.4 mm sheet holes / existing six M3 positions</text><text x="-135" y="12">Blue: continuous sheet. Grey: printed load path. Brown: single wood grid.</text><text x="-135" y="19">Reflecting planes Z={rear:g} / {front:g} mm. Gap {front-rear:g} mm. Washer stops at Z={front+1.5:g}.</text></g></svg>\n')
    # Check each export against native emitting faces and count, independently
    # of GLB mesh rounding.
    for group,name in enumerate(('Circle','Halo','Inner','Outer')):
        solids = source.getObject(name+'LEDs').Shape.Solids
        group_leds = [led for led in leds if led['group']==group]
        assert len(solids)==len(group_leds)
        for solid,led in zip(solids,group_leds):
            point = Part.Vertex(App.Vector(*[v*1000 for v in led['position_m']]))
            assert point.distToShape(solid)[0]<1e-6
            normal = App.Vector(*led['direction'])
            faces = [face for face in solid.Faces if point.distToShape(face)[0]<1e-6]
            assert any(face.normalAt(0,0).dot(normal)>.999999 for face in faces), 'Wrong emitting face normal'
    old = json.loads((out/'parts.json').read_text())
    by_name = {v['name']:v for v in old['volumes']}
    acrylic_removed = sum(by_name[n]['volume_cm3'] for n in ('FrontAcrylic','FrontMirror','FrontBezel','EdgeDiffuserSeam'))
    petg_removed = sum(by_name[n]['volume_cm3'] for n in ('CircleBezel',*(f'OpticalDeckQ{i}' for i in range(1,5)),*(f'CircleRimFoot{i}' for i in range(3))))
    acrylic_g = old['mass_estimate']['acrylic_g'] + (sheet.Volume/1000+edge.Volume/1000-acrylic_removed)*1.19
    petg_g = old['mass_estimate']['printed_petg_g'] + (sum(s.Volume for s in proposal_shapes+feet)/1000-petg_removed)*1.27
    metadata = {'format_version':1,'units':'metres','axes':{'right':'+X','up':'+Y','front':'+Z'},
        'master_sha256':original,'parts':parts,'leds':leds,'groups':['Circle','Halo','Inner','Outer'],
        'comparison':{'still_time_s':2.0,'distance_m':.6,'exposure':1.0,'brightness':2.0,
            'front_reflectance':.65,'front_transmission':.25,'rear_reflectance':.94,
            'sleeve_transmission':.4,'sleeve_diffusion':.65,'centre_diffusion':.65,
            'clear_centre_transmission':.8,'clear_centre_reflectance':.04,
            'status':'Unmeasured assumptions; relative preview, not photometry'},
        'dimensions_m':{'diameter':p['case_diameter']/1000,'body_depth':p['case_depth']/1000},
        'optics':{'front_z':front/1000,'rear_z':rear/1000,'separation':(front-rear)/1000,
            'aperture_inner':p['mirror_view_inner_radius']/1000,'aperture_outer':p['mirror_view_outer_radius']/1000,
            'halo_radius':dims['Halo']['outer']/1000,'inner_radius':dims['Inner']['inner']/1000,
            'strip_z':(p['strip_bottom_z']+p['strip_width']/2)/1000,
            'strip_half_height':.0025,'sleeves':dims,
            'ring_pitch_radii':[ring_radius(p[n+'_count'],p)/1000 for n in ('halo','inner','outer')],
            'ring_seam_gap':p['ring_seam_gap']/1000,'pitch':1/p['strip_density'],
            'edge_radius':p['edge_diffuser_radius']/1000,'edge_z':(strip_bottom('Outer',p)+p['strip_width']/2)/1000},
        'proposal':{'status':'Preview only; finish selection and physical checks required',
            'sheet_thickness_m':.0015,'locating_hole_diameter_m':.0064,'compression_stop_diameter_m':.006,
            'fasteners_m':[[x/1000,y/1000,front/1000] for x,y in mounting_points(p)],
            'sheet_before_holes_g':math.pi*(p['case_diameter']/2)**2*1.5/1000*1.19,
            'sheet_g':sheet.Volume/1000*1.19,
            'current_front_g':sum(by_name[n]['volume_cm3'] for n in ('FrontAcrylic','FrontMirror','FrontBezel'))*1.19,
            'current_mechanical_g':old['mass_estimate']['mechanical_subset_g'],
            'printed_petg_g':petg_g,'acrylic_g':acrylic_g,'wood_g':old['mass_estimate']['wood_g'],
            'mechanical_g':petg_g+acrylic_g+old['mass_estimate']['wood_g'],
            'removed_parts':sorted(replaced),'wood_to_sheet_gap_m':.0001,'wood_to_led_gap_m':.0002,
            'added_parts':['One front sheet','Four revised deck quarters','Shortened outside sleeve','Same wood grid, 0.1 mm lower','Three shortened rim feet'],
            'part_count_delta':-9}}
    glb.save(out/'amulet.glb')
    (out/'scene.json').write_text(json.dumps(metadata,indent=2)+'\n')
    App.closeDocument(source.Name)
    assert hashlib.sha256(master.read_bytes()).hexdigest()==original
    print(f'DEMO EXPORT PASS: {len(parts)} meshes, {len(leds)} emitting faces; master unchanged',flush=True)
