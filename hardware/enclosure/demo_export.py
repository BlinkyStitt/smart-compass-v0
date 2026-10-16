"""Export the selected single-sheet assembly in metres.

The small GLB writer uses FreeCAD tessellation, not print-bed STL coordinates.
CAD and Godot both use X right, Y up, Z toward the front viewer.
"""
import hashlib
import json
import math
from pathlib import Path
import struct

from geometry import cavity_diffusers, led_centres, pixel_regions, mounting_points, ring_pixel, ring_radius, strip_bottom

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

    def mesh(self, name, shape, color, variant='common', role='solid', label=None, pixel_centres=None):
        import MeshPart
        mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=.12, AngularDeflection=.20, Relative=False)
        points, triangles = mesh.Topology
        positions, normals, pixel_colours = [], [], []
        # Flat normals preserve tiny cell walls and sharp mechanical edges.
        for triangle in triangles:
            a, b, c = [points[i] for i in triangle]
            normal = (b-a).cross(c-a)
            if normal.Length < 1e-12:
                continue
            normal.normalize()
            if pixel_centres is not None:
                centre=(a+b+c)/3
                index=min(range(len(pixel_centres)),key=lambda i: math.hypot(centre.x-pixel_centres[i][0],centre.y-pixel_centres[i][1]))
                x,y=pixel_centres[index]
                assert all(abs(point.x-x)<=2.50001 and abs(point.y-y)<=2.50001 for point in (a,b,c)), 'LED triangle crosses published pixel identities'
            for point in (a, b, c):
                positions.append(tuple(v/1000 for v in point))
                normals.append(tuple(normal))
                if pixel_centres is not None: pixel_colours.append((index/255,0.0,0.0,1.0))
        position = self.accessor(positions, 'fff', 'VEC3', 5126, True)
        normal = self.accessor(normals, 'fff', 'VEC3', 5126)
        material = len(self.doc['materials'])
        self.doc['materials'].append({'name': name, 'doubleSided': True,
            'pbrMetallicRoughness': {'baseColorFactor': [*color, 1], 'metallicFactor': 0, 'roughnessFactor': .65}})
        attributes={'POSITION':position,'NORMAL':normal}
        if pixel_colours:
            attributes['COLOR_0']=self.accessor(pixel_colours,'ffff','VEC4',5126)
        self.doc['meshes'].append({'name': name, 'primitives': [{'attributes': attributes, 'material': material}]})
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
    p = build.load_parameters()
    source = App.openDocument(str(master))
    out = HERE/'exports'
    glb, parts = GLB(), []
    front = p['front_plane_z']
    rear = p['mirror_back_z']+p['rear_acrylic_thickness']
    centers = led_centres(json.loads((HERE/'fibonacci256-layout.json').read_text()), p)
    cells = pixel_regions(centers,p['circle_diameter']/2)
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
    objects = [o for group in (source.Manufactured,source.Electronics,source.Optics) for o in group.Group if o.Visibility]
    def add(name,shape,color,role='solid',label=None,pixel_centres=None):
        parts.append(glb.mesh(name,shape,color,role=role,label=label,pixel_centres=pixel_centres))
    for obj in objects:
        if obj.Name=='FrontSheet':
            continue
        role = ('hardware' if 'HardwareVariant' in obj.PropertiesList else
                'packages' if obj.Name.endswith('LEDs') else
                'sleeve' if obj.Name in ('HaloRing','InnerRing','EdgeDiffuser') else 'solid')
        add(obj.Name,obj.Shape,tuple(obj.ViewObject.ShapeColor[:3]),role,obj.Label,centers if obj.Name=='CircleLEDs' else None)
        if role=='hardware':
            parts[-1]['explosion_offset_m']=obj.ExplosionOffsetM
    # Three render regions, one manufactured sheet and one CAD source.
    sheet=source.FrontSheet.Shape
    inner=Part.makeCylinder(p['mirror_view_inner_radius'],p['front_acrylic_thickness'],App.Vector(0,0,front))
    outer=Part.makeCylinder(p['mirror_view_outer_radius'],p['front_acrylic_thickness'],App.Vector(0,0,front))
    regions=[sheet.common(inner),sheet.common(outer).cut(inner),sheet.cut(outer)]
    assert abs(sum(region.Volume for region in regions)-sheet.Volume)<1e-6
    for name,region,colour,role in zip(('FrontCentre','FrontMirrorCoating','FrontRim'),regions,((.025,.025,.025),(.025,.025,.025),(.012,.012,.012)),('centre','cavity','solid')):
        add(name,region,colour,role)
    for i,polygon in enumerate(cells):
        # Optical partitions have no invented web. The actual original walls clip
        # every partition, including the open cells at the source perimeter.
        z=source.FibonacciBaffle.Shape.BoundBox.ZMin
        wire=Part.makePolygon([App.Vector(x,y,z) for x,y in polygon+[polygon[0]]])
        aperture=Part.Face(wire).cut(source.FibonacciBaffle.Shape)
        assert not aperture.isNull() and aperture.Area>0
        assert aperture.common(source.FibonacciBaffle.Shape).Area<1e-7
        aperture.translate(App.Vector(0,0,front-.015-z))
        add(f'Cell{i:03}',aperture,(.012,.012,.012),'cell')
    dims=cavity_diffusers(p)
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
    inventory=json.loads((out/'parts.json').read_text())
    acrylic=json.loads((HERE/'acrylic-optics.json').read_text())
    mirror=acrylic['materials']['two_way_mirror']
    black=acrylic['materials']['black_led']
    black_mirror=acrylic['materials']['black_mirror']
    metadata={'format_version':1,'units':'metres','axes':{'right':'+X','up':'+Y','front':'+Z'},
        'acrylic_materials':acrylic,'master_sha256':original,'parts':parts,'leds':leds,'groups':['Circle','Halo','Inner','Outer'],
        'comparison':{'still_time_s':2.0,'distance_m':.6,'exposure':1.0,'brightness':2.0,
            'front_reflectance':black_mirror['reflectance'],'front_transmission':black_mirror['transmission'],
            'front_external_reflectance':black_mirror['reverse_reflectance'],
            'rear_reflectance':mirror['reflectance'],'rear_transmission':mirror['transmission'],
            'sleeve_transmission':.4,'sleeve_diffusion':.65,'centre_diffusion':.65,
            'black_acrylic_transmission':black['transmission'],'black_acrylic_surface_reflectance':black['surface_reflectance'],
            'status':'Rear clear mirror: supplier-nominal R70/T30. Custom coated black front: estimated cavity-side R70/T9/absorption21, reverse-side R10/T9/absorption81. This complete-sheet estimate already includes black substrate loss. Uncoated black centre T29 is supplier nominal. No measured data establish the custom coated black sheet; scattering, RGB, glow and assembly response remain unmeasured'},
        'dimensions_m':{'diameter':p['case_diameter']/1000,'body_depth':p['case_depth']/1000},
        'optics':{'front_z':front/1000,'rear_z':rear/1000,'separation':(front-rear)/1000,
            'aperture_inner':p['mirror_view_inner_radius']/1000,'aperture_outer':p['mirror_view_outer_radius']/1000,
            'halo_radius':dims['Halo']['outer']/1000,'inner_radius':dims['Inner']['inner']/1000,
            'strip_z':(p['strip_bottom_z']+p['strip_width']/2)/1000,
            'strip_half_height':.0025,'sleeves':dims,
            'ring_pitch_radii':[ring_radius(p[n+'_count'],p)/1000 for n in ('halo','inner','outer')],
            'ring_wall_mm':[p['ring_diffuser_thickness'],p['ring_diffuser_thickness'],p['edge_diffuser_thickness']],
            'ring_seam_gap':p['ring_seam_gap']/1000,'pitch':1/p['strip_density'],
            'edge_radius':p['edge_diffuser_radius']/1000,'edge_z':(strip_bottom('Outer',p)+p['strip_width']/2)/1000},
        'design':{'selected_finish':'black LED acrylic centre, cavity-facing mirror annulus, opaque rim',
            'sheet_thickness_m':p['front_acrylic_thickness']/1000,'locating_hole_diameter_m':.007,
            'compression_stop_diameter_m':.006,'front_sheet_volume_cm3':sheet.Volume/1000,
            'fasteners_m':[[x/1000,y/1000,front/1000] for x,y in mounting_points(p)],
            'printed_part_count':len(inventory['stl_files']),'mass_estimate':inventory['mass_estimate']}}
    materials=json.loads((HERE/'print-spec.json').read_text())['ring_materials']
    metadata['ring_materials']=materials
    for material_id,material in materials.items():
        render=material['render']
        for part,entry in zip(parts,glb.doc['materials']):
            if part['role']=='sleeve':
                entry['pbrMetallicRoughness']={'baseColorFactor':[*render['albedo'],1], 'metallicFactor':render['metallic'], 'roughnessFactor':render['roughness']}
        glb.save(out/('amulet.glb' if material_id=='glow' else 'amulet-'+material_id+'.glb'))
    (out/'scene.json').write_text(json.dumps(metadata,indent=2)+'\n')
    App.closeDocument(source.Name)
    assert hashlib.sha256(master.read_bytes()).hexdigest()==original
    print(f'DEMO EXPORT PASS: {len(parts)} meshes, {len(leds)} emitting faces; selected single-sheet master unchanged',flush=True)
