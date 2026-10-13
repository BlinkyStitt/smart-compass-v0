"""Export the selected single-sheet assembly in metres.

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
    front = p['front_plane_z']
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
    objects = [o for group in (source.Manufactured,source.Electronics,source.Optics) for o in group.Group if o.Visibility]
    def add(name,shape,color,role='solid',label=None):
        parts.append(glb.mesh(name,shape,color,role=role,label=label))
    for obj in objects:
        if obj.Name=='FrontSheet':
            continue
        role = ('hardware' if 'HardwareVariant' in obj.PropertiesList else
                'packages' if obj.Name.endswith('LEDs') else
                'sleeve' if obj.Name in ('HaloDiffuser','InnerDiffuser','EdgeDiffuserSeam') else 'solid')
        add(obj.Name,obj.Shape,tuple(obj.ViewObject.ShapeColor[:3]),role,obj.Label)
        if role=='hardware':
            parts[-1]['explosion_offset_m']=obj.ExplosionOffsetM
    # Three render regions, one manufactured sheet and one CAD source.
    sheet=source.FrontSheet.Shape
    inner=Part.makeCylinder(p['circle_diameter']/2,p['acrylic_thickness'],App.Vector(0,0,front))
    outer=Part.makeCylinder(p['mirror_view_outer_radius'],p['acrylic_thickness'],App.Vector(0,0,front))
    regions=[sheet.common(inner),sheet.common(outer).cut(inner),sheet.cut(outer)]
    assert abs(sum(region.Volume for region in regions)-sheet.Volume)<1e-6
    for name,region,colour,role in zip(('FrontCentre','FrontMirrorCoating','FrontRim'),regions,((.7,.8,.9),(.6,.7,.8),(.018,.018,.018)),('centre','cavity','solid')):
        add(name,region,colour,role)
    for i,polygon in enumerate(cells):
        wire=Part.makePolygon([App.Vector(x,y,front-.015) for x,y in polygon+[polygon[0]]])
        add(f'Cell{i:03}',Part.Face(wire),(.1,.1,.1),'cell')
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
    metadata={'format_version':1,'units':'metres','axes':{'right':'+X','up':'+Y','front':'+Z'},
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
        'design':{'selected_finish':'clear centre, mirror ring, black masked rim',
            'sheet_thickness_m':p['acrylic_thickness']/1000,'locating_hole_diameter_m':.0066,
            'compression_stop_diameter_m':.006,'front_sheet_volume_cm3':sheet.Volume/1000,
            'fasteners_m':[[x/1000,y/1000,front/1000] for x,y in mounting_points(p)],
            'printed_part_count':len(inventory['stl_files']),'mass_estimate':inventory['mass_estimate']}}
    glb.save(out/'amulet.glb')
    (out/'scene.json').write_text(json.dumps(metadata,indent=2)+'\n')
    App.closeDocument(source.Name)
    assert hashlib.sha256(master.read_bytes()).hexdigest()==original
    print(f'DEMO EXPORT PASS: {len(parts)} meshes, {len(leds)} emitting faces; selected single-sheet master unchanged',flush=True)
