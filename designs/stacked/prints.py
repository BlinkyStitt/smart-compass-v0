"""Narrow print exports and checks. Samples and trim waste are not worn mass."""
import hashlib,json,re,subprocess,tempfile,zipfile,struct,math
import xml.etree.ElementTree as ET
from collections import Counter
import itertools
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'hardware/enclosure'))
import slicing
from solid_clearance import bounds

RINGS=frozenset({'SideDiffuser','InnerDiffuser'})


def source_parts():
    """The selected narrow manufactured census, independently of exports."""
    import battery_access,control_fixture,latch_mount,blackpill_mount,radio_mount,branch_fuses,harness_plan,end_supports
    names={'RearCover','ElectronicsShell','FrontBezel','SideDiffuser','InnerDiffuser','EGLStencil','CapacitorCover',*('BoardEdgeClip'+str(i) for i in range(3))}
    names.update(end_supports.PRINTED_PARTS|battery_access.printed_parts('narrow')|control_fixture.printed_parts('narrow')|latch_mount.PRINTED_PARTS|blackpill_mount.PRINTED_PARTS|radio_mount.PRINTED_PARTS|branch_fuses.PRINTED_PARTS)
    names.update('HarnessSpliceCarrier'+name for name in harness_plan.HUBS)
    return frozenset(names)


def sample_parts():
    return {'Fit'+name:name for name in ['BatteryContactPFront','BatteryContactPBack','BatteryContactNFront','BatteryContactNBack','BatteryKeeper','BatteryDoor','BatteryCradle','BoardEdgeClip0','LatchCarrier','StartBezel','HarnessSpliceCarrierGND','HarnessSpliceCarrierSENSE','BoostInputRelief']} | {'FitSuspensionLeft':'ElectronicsShell','FitSuspensionRight':'ElectronicsShell','FitBoardEdgeSeat':'ElectronicsShell',**{'Fit'+name:name for name in RINGS}}


def print_layout(path=None):
    record=json.loads((Path(path) if path is not None else HERE/'print-layout.json').read_text())
    if record.get('revision')!='narrow-print-layout-1' or record.get('physical_acceptance')!='unmeasured':raise ValueError('Unsupported narrow print layout')
    known=source_parts();poses=record['orientations'];supported=record['temporary_support_parts']
    if set(poses)-known or set(supported)-known or len(set(supported))!=len(supported):raise ValueError('Unknown or duplicate narrow print part')
    if set(supported)&RINGS:raise ValueError('Optical rings must remain support-free')
    for name,pose in poses.items():
        axis,angle=pose['axis'],pose['angle_deg']
        if axis not in ([1,0,0],[0,1,0],[0,0,1]) or isinstance(angle,bool) or angle not in (-180,-90,0,90,180):raise ValueError('Unsupported narrow print rotation '+name)
        if name in RINGS and axis!=[0,0,1] and angle!=0:raise ValueError('Optical rings must remain upright')
    profile=record['temporary_support_settings']
    required={'support_material':'1','support_material_auto':'1','support_material_buildplate_only':'1','dont_support_bridges':'0'}
    if set(profile)!=set(required)|{'support_material_style'} or any(profile.get(key)!=value for key,value in required.items()) or profile['support_material_style'] not in ('grid','snug','organic'):raise ValueError('Invalid removable structural support profile')
    if not record.get('removal') or not record.get('source',{}).get('url'):raise ValueError('Missing narrow print removal instructions/source')
    return record


def orientation(name):
    pose=print_layout()['orientations'].get(name)
    if pose:return pose['axis'],pose['angle_deg']
    if name=='BoostInputRelief':return [1,0,0],90
    return [0,1,0],90 if name.startswith(('BatteryContact','BatteryHingeSpacer')) else 0


def required_exports(spec):
    names={name+'.stl' for name in source_parts()|sample_parts().keys()}
    for name in source_parts():
        names.update(project_name(name+'.stl',name,material) for material in spec['ring_materials'] if name in RINGS)
        if name not in RINGS:names.add(name+'.3mf')
    for name,parent in sample_parts().items():
        for material in spec['ring_materials'] if parent in RINGS else [spec['default_ring_material']]:names.add(project_name(name+'.stl',parent,material))
    return frozenset(names)

def settings(spec,part,material='glow'):
    name=Path(part).stem
    profile=spec['ring_outside'] if name=='SideDiffuser' else spec['ring_cavity'] if name=='InnerDiffuser' else spec['baffle'] if name=='EGLStencil' else spec['rear_plate'] if name=='RearCover' else {}
    extra={}
    if name in RINGS:
        choice=spec['ring_materials'][material]
        extra={'filament_density':str(choice['density_g_cm3']),'filament_colour':choice['filament_colour']}
    layout=print_layout();supports=layout['temporary_support_settings'] if name in layout['temporary_support_parts'] else {}
    return spec['reference_machine']|spec['common']|profile|extra|supports


def project_name(stl,source,material):
    return Path(stl).stem+('-'+material if Path(source).stem in RINGS and material!='glow' else '')+'.3mf'


def jobs(parts,spec):
    full=parts['print_parts']
    if [row['file'] for row in full]!=parts['stl_files']:
        raise ValueError('Narrow print metadata differs from the full STL census')
    entries=full+parts['fit_samples']
    for row in entries:
        for material in spec['ring_materials'] if row['source_part'] in RINGS else [spec['default_ring_material']]:
            yield row,project_name(row['file'],row['source_part'],material),material


def normalize_stl_bed(path):
    """Place the serialized mesh's lowest vertices on Z0 without scaling."""
    path=Path(path);data=bytearray(path.read_bytes())
    if len(data)<84:raise ValueError('Missing binary narrow STL for bed placement')
    count=struct.unpack_from('<I',data,80)[0]
    if not count or len(data)!=84+50*count:raise ValueError('Invalid binary narrow STL for bed placement')
    offsets=[84+i*50+20+j*12 for i in range(count) for j in range(3)]
    heights=[struct.unpack_from('<f',data,offset)[0] for offset in offsets]
    if not all(math.isfinite(value) for value in heights):raise ValueError('Nonfinite narrow STL bed placement')
    minimum=min(heights)
    if minimum==0:return 0.0
    for offset,value in zip(offsets,heights):struct.pack_into('<f',data,offset,value-minimum)
    path.write_bytes(data)
    return -minimum


def native_export(doc,out,p,d):
    import FreeCAD as App,Part,MeshPart
    out=Path(out);rows=[];samples=[]
    manufactured={o.Name:o.Shape for o in doc.Manufactured.Group if o.Name not in {'RearCouplingMirror','FrontMirror'}}
    if set(manufactured)!=source_parts():raise ValueError('Narrow manufactured census differs from print contract: '+str(set(manufactured)^source_parts()))
    source_volumes={name:shape.Volume for name,shape in manufactured.items()}
    def orient(name,shape):
        solid=shape.copy();axis,rotation=orientation(name)
        if rotation:solid.rotate(App.Vector(),App.Vector(*axis),rotation)
        bb=bounds(solid);solid.translate(App.Vector(-bb.XMin,-bb.YMin,-bb.ZMin))
        return solid,{'axis':axis,'angle_deg':rotation}
    def write(name,parent,shape,sample=False):
        if not shape.isValid() or len(shape.Solids)!=1:raise ValueError('Invalid narrow print part '+name)
        shape.check(True)
        solid,rotation=orient(parent,shape);bb=bounds(solid)
        if bb.XLength+10>300 or bb.YLength+10>300:raise ValueError('Narrow part exceeds reference print bed '+name)
        mesh=MeshPart.meshFromShape(Shape=solid,LinearDeflection=.02,AngularDeflection=.08,Relative=False)
        filename=name+'.stl';mesh.write(str(out/filename))
        # Curved source extrema can lie between mesh vertices. Bake the
        # actual serialized mesh onto the bed before creating its3MF.
        mesh_bed_shift=normalize_stl_bed(out/filename)
        record={'file':filename,'source_part':parent,'print_bounds_mm':[getattr(bb,a+'Length') for a in 'XYZ'],
                'source_volume_cm3':shape.Volume/1000,'rotation':rotation,'sha256':hashlib.sha256((out/filename).read_bytes()).hexdigest(),
                'mesh_bed_translation_z_mm':mesh_bed_shift,
                'physical_acceptance':'unmeasured'}
        (samples if sample else rows).append(record)
    for name,shape in sorted(manufactured.items()):write(name,name,shape)
    # Whole small interface parts are exact disposable first prints. They are
    # not additional installed products or a second copy in worn mass.
    for parent in ['BatteryContactPFront','BatteryContactPBack','BatteryContactNFront','BatteryContactNBack','BatteryKeeper','BatteryDoor','BatteryCradle','BoardEdgeClip0','LatchCarrier','StartBezel','HarnessSpliceCarrierGND','HarnessSpliceCarrierSENSE','BoostInputRelief']:
        if parent not in manufactured:raise ValueError('Missing narrow fit interface '+parent)
        write('Fit'+parent,parent,manufactured[parent],True)
    for side,x in [('Left',-d['suspension_x']),('Right',d['suspension_x'])]:
        crop=Part.makeBox(28,28,16,App.Vector(x-14,d['suspension_y']-14,2))
        write('FitSuspension'+side,'ElectronicsShell',manufactured['ElectronicsShell'].common(crop),True)
    for parent in sorted(RINGS):
        crop=Part.makeBox(32,40,80,App.Vector(78,-20,0))
        write('Fit'+parent,parent,manufactured[parent].common(crop),True)
    clip=manufactured['ElectronicsShell'].common(Part.makeBox(16,16,8,App.Vector(77.5,-8,p['circle_back_z']-4.3)))
    write('FitBoardEdgeSeat','ElectronicsShell',clip,True)
    # Coupon Booleans and meshing must not corrupt their installed parents.
    for name,shape in manufactured.items():
        shape.check(True)
        if abs(shape.Volume-source_volumes[name])>1e-6:raise ValueError('Print export changed installed source '+name)
    return {'parameters_for_inventory':p,'stl_files':[row['file'] for row in rows],'print_parts':rows,'fit_samples':samples,
            'scope':'Narrow only. Native millimetre geometry with baked bed orientation. Fit samples are disposable; supplied fit and print strength remain unmeasured.'}


def verify_project_geometry(archive,stl_bytes):
    """Retain source triangles within0.0001mm serialization roundoff only."""
    if len(stl_bytes)<84:raise ValueError('Missing binary narrow STL')
    count=struct.unpack_from('<I',stl_bytes,80)[0]
    if len(stl_bytes)!=84+50*count or not count:raise ValueError('Invalid binary narrow STL')
    stl=Counter(tuple(sorted(stl_bytes[84+i*50+12+j*12:84+i*50+24+j*12] for j in range(3))) for i in range(count))
    root=ET.fromstring(archive.read('3D/3dmodel.model'));ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
    objects=root.findall('./m:resources/m:object',ns);items=root.findall('./m:build/m:item',ns)
    if root.get('unit')!='millimeter' or len(objects)!=1 or len(items)!=1 or objects[0].find('m:components',ns) is not None:raise ValueError('Unexpected narrow3MF mesh/units/instance count')
    item=items[0]
    if item.get('objectid')!=objects[0].get('id') or item.get('printable','1')!='1':raise ValueError('Narrow3MF does not print its one source object')
    transform=[float(v) for v in item.get('transform','1 0 0 0 1 0 0 0 1 0 0 0').split()]
    if len(transform)!=12 or any(not math.isfinite(v) for v in transform) or transform[:9]!=[1,0,0,0,1,0,0,0,1] or abs(transform[11])>1e-6:raise ValueError('Narrow3MF changed the baked print rotation,scale or bed height')
    vertices=[]
    for v in objects[0].findall('./m:mesh/m:vertices/m:vertex',ns):
        point=[float(v.get(axis)) for axis in 'xyz']
        if any(not math.isfinite(x) for x in point):raise ValueError('Nonfinite narrow3MF vertex')
        vertices.append(struct.pack('<3f',*point))
    # PrusaSlicer centring and float32 serialization can move a vertex by an
    # observed one ULP. This numerical tolerance is200x smaller than the
    # source0.02mm tessellation deflection; it is not a fabrication tolerance.
    tolerance=.0001;source_vertices={point:struct.unpack('<3f',point) for triangle in stl for point in triangle};grid={}
    for key,point in source_vertices.items():grid.setdefault(tuple(math.floor(v/tolerance) for v in point),[]).append(key)
    candidates=[]
    for vertex in vertices:
        point=struct.unpack('<3f',vertex);cell=tuple(math.floor(v/tolerance) for v in point);near=[]
        for delta in itertools.product([-1,0,1],repeat=3):
            for key in grid.get(tuple(a+b for a,b in zip(cell,delta)),[]):
                target=source_vertices[key]
                if max(abs(a-b) for a,b in zip(point,target))<=tolerance:near.append((sum((a-b)**2 for a,b in zip(point,target)),key))
        if not near:raise ValueError('Narrow3MF vertex differs from its source STL')
        candidates.append([key for _,key in sorted(near)])
    remaining=stl.copy();triangles=0
    for tri in objects[0].findall('./m:mesh/m:triangles/m:triangle',ns):
        ids=[int(tri.get('v'+str(i))) for i in [1,2,3]]
        if any(not 0<=i<len(vertices) for i in ids):raise ValueError('Invalid narrow3MF triangle')
        for combination in itertools.product(*(candidates[i] for i in ids)):
            key=tuple(sorted(combination))
            if remaining[key]:remaining[key]-=1;triangles+=1;break
        else:raise ValueError('Narrow3MF triangle differs from its source STL')
    if triangles!=count or any(remaining.values()):raise ValueError('Narrow3MF changed the source triangle count')
    return count


def generate(out,parts,spec):
    out=Path(out);bed=slicing.bed_bounds(spec);centre=f'{(bed[0]+bed[2])/2:g},{(bed[1]+bed[3])/2:g}'
    with tempfile.TemporaryDirectory(prefix='narrow-project-',dir=out.parent) as temporary:
        for row,name,material in jobs(parts,spec):
            config=Path(temporary)/'settings.ini';expanded=Path(temporary)/'expanded.ini'
            expected=settings(spec,row['source_part'],material);config.write_text(''.join(f'{k} = {v}\n' for k,v in expected.items()))
            result=subprocess.run([slicing.executable(),'--load',str(config),'--center',centre,'--export-3mf','--save',str(expanded),'--output',str(out/name),str(out/row['file'])],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            if result.returncode:raise RuntimeError('Narrow project export failed '+name+': '+result.stdout)
            embedded=''.join('; '+line+'\n' for line in expanded.read_text().splitlines() if re.match(r'^[a-z][a-z_0-9]* = ',line))
            with zipfile.ZipFile(out/name,'a',compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('Metadata/Slic3r_PE.config',embedded)
                archive.writestr('Metadata/compass-source.json',json.dumps({'stl':row['file'],'sha256':row['sha256'],'source_part':row['source_part'],'material':material,'print_bounds_mm':row['print_bounds_mm']},sort_keys=True))


def verify_support_toolpaths(code,expected,name):
    roles=set(re.findall(r'^;TYPE:(.*)$',code,re.M))
    present=bool(roles&{'Support material','Support material interface'})
    required=expected['support_material']=='1'
    if present!=required:raise ValueError('Narrow support toolpaths differ from the selected print profile '+name)
    return present


def check(out,parts,spec):
    out=Path(out);report=[]
    with tempfile.TemporaryDirectory(prefix='narrow-slice-',dir=out.parent) as temporary:
        for row,name,material in jobs(parts,spec):
            expected=settings(spec,row['source_part'],material)
            if hashlib.sha256((out/row['file']).read_bytes()).hexdigest()!=row['sha256']:raise ValueError('Narrow STL differs from source inventory '+name)
            with zipfile.ZipFile(out/name) as archive:
                verify_project_geometry(archive,(out/row['file']).read_bytes())
                slicing.verify_settings(slicing.configuration(archive.read('Metadata/Slic3r_PE.config').decode()),expected,name)
                source=json.loads(archive.read('Metadata/compass-source.json'))
                if source!={'stl':row['file'],'sha256':row['sha256'],'source_part':row['source_part'],'material':material,'print_bounds_mm':row['print_bounds_mm']}:raise ValueError('Narrow project provenance differs '+name)
            path=Path(temporary)/'part.gcode'
            result=subprocess.run([slicing.executable(),'--export-gcode','--output',str(path),str(out/name)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            if result.returncode or re.search(r'warning|error|empty layer',result.stdout,re.I):raise RuntimeError('Narrow slicing failed '+name+': '+result.stdout)
            code=path.read_text();slicing.verify_settings(slicing.configuration(code),expected,name)
            layers=code.count(';LAYER_CHANGE');mass=re.search(r'; filament used \[g\] = ([\d.]+)',code)
            if not mass or layers<2 or ';TYPE:External perimeter' not in code:raise ValueError('Missing narrow model toolpaths '+name)
            support_present=verify_support_toolpaths(code,expected,name)
            paths=slicing.perimeter_layers(code);slicing.verify_bed(paths,slicing.bed_bounds(spec),name)
            if row['source_part']=='InnerDiffuser' and ';TYPE:Solid infill' not in code:raise ValueError('Narrow inner diffuser requires a connected solid seating foot '+name)
            if row['source_part']=='SideDiffuser' and any(';TYPE:'+kind in code for kind in ['Internal infill','Gap fill','Solid infill']):raise ValueError('Narrow outside diffuser must retain its continuous perimeter wall '+name)
            report.append({'project':name,'source_stl_sha256':row['sha256'],'layers':layers,'toolpath_mass_g':float(mass[1]),'material':material,'temporary_support_toolpaths':support_present,'physical_acceptance':'unmeasured'})
    return {'scope':'Exact delivered3MF sliced without external transforms/settings; toolpaths do not establish physical print fit/strength','projects':report,'physical_acceptance':'unmeasured'}
