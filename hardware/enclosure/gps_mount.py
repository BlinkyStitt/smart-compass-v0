"""Source GPS assembly and four source-hole posts; physical fit is unmeasured."""
import hashlib
import itertools
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import electrical_peripherals

HERE=Path(__file__).resolve().parent
SOURCE='sources/gps-featherwing-mechanical'
STEP_SHA256='06856a162d7e0bcebbab60d46e2f8bc576b9c3aa938d96951d16a466e581814a'
STEP_REVISION='6c5cd9e3e65252bb5d5339608cf8d3cdabcef251'
HARDWARE_NAMES=frozenset('GPS'+kind+str(i) for kind in ('Screw','Nut') for i in range(4))
PRODUCT_NAMES=HARDWARE_NAMES|{'GPSPCB'}
REFERENCE_NAMES=frozenset({'GPSComponents'})
CHECK_NAMES=PRODUCT_NAMES|REFERENCE_NAMES


def definition():return json.loads((HERE/'electrical-design.json').read_text())['parts']['GPS']


def geometry(part=None,directory=HERE):
    directory=Path(directory);part=definition() if part is None else part
    terminals=electrical_peripherals.terminals('GPS',part,directory)
    board=ET.fromstring((directory/'sources/gps-featherwing/Adafruit Ultimate GPS FeatherWing.brd').read_bytes()).find('./drawing/board')
    ms=next(el for el in board.findall('./elements/element') if el.get('name')=='MS1')
    if ms.get('package')!='FEATHERWING' or [ms.get(k) for k in ('x','y')]!=['0','0'] or ms.get('rot','R0')!='R0':
        raise ValueError('Review the GPS MS1 outline and datum')
    library=next(row for row in board.findall('./libraries/library') if row.get('name')==ms.get('library'))
    package=next(row for row in library.findall('./packages/package') if row.get('name')==ms.get('package'))
    mounts=[{'xy':[float(p.get('x')),float(p.get('y'))],'drill':float(p.get('drill'))}
            for p in list(package) if p.tag=='hole' or p.tag=='pad' and p.get('name') in ('P$1','P$2')]
    if mounts!=[{'xy':[48.26,20.32],'drill':2.54},{'xy':[48.26,2.54],'drill':2.54},
                {'xy':[2.54,20.32],'drill':2.5},{'xy':[2.54,2.54],'drill':2.5}]:
        raise ValueError('Review changed GPS mounting holes; the antenna hole is not a board mount')
    index=json.loads((directory/SOURCE/'index.json').read_text())
    row=next(row for row in index if row['file']=='3133.step');raw=(directory/SOURCE/'3133.step').read_bytes()
    if (hashlib.sha256(raw).hexdigest()!=STEP_SHA256 or row.get('sha256')!=STEP_SHA256
            or row.get('bytes')!=len(raw) or row.get('repository_revision')!=STEP_REVISION):
        raise ValueError('GPS mechanical source hash/revision mismatch')
    return {'mounts':mounts,'terminals':terminals,'datum_mm':[25.4,11.43],
            'pcb_thickness_mm':1.57,'source_solids':55,'loaded_reservation_mm':[50.8,22.86,8]}


def envelope(pcb_bottom_z=6,rotation_deg=90):
    if pcb_bottom_z not in (6,9) or rotation_deg!=90:raise ValueError('Review GPS post height and installed orientation')
    return {'size':[22.86,50.8,8],'z':pcb_bottom_z}


def native_shapes(pcb_bottom_z=6,rotation_deg=90,part=None):
    import FreeCAD as App
    import Part
    from fastener_access import native_tools
    from hardware_spec import hexagon,nut_dimensions
    data=geometry(part);envelope(pcb_bottom_z,rotation_deg);z=pcb_bottom_z
    module=Part.read(str(HERE/SOURCE/'3133.step'))
    if not module.isValid() or len(module.Solids)!=data['source_solids']:raise ValueError('GPS source assembly is invalid/incomplete')
    bounds=module.BoundBox
    if any(abs(a-b)>1e-6 for a,b in zip((bounds.XMin,bounds.YMin,bounds.ZMin,bounds.XLength,bounds.YLength,bounds.ZLength),(0,0,0,50.8,22.86,6.62))):
        raise ValueError('GPS source assembly datum/bounds differ')
    # Keep the source PCB and the full conservative loaded space. The vendor's
    # detailed component bodies overlap one another and the PCB. They are not
    # a regular material solid suitable for a complementary empty-space cut.
    pcb=max(module.Solids,key=lambda shape:shape.Volume).copy()
    pcb.translate(App.Vector(-25.4,-11.43,z))
    reserved=Part.makeBox(50.8,22.86,8-1.57,App.Vector(-25.4,-11.43,z+1.57))
    products={'GPSPCB':pcb};additions=[];cuts=[];probes=[];paths=[]
    flat,nh=nut_dimensions('M2');pflat,ph=nut_dimensions('M2',pocket=True)
    def cylinder(radius,height,x,y,bottom):return Part.makeCylinder(radius,height,App.Vector(x,y,bottom))
    for i,row in enumerate(data['mounts']):
        x,y=[p-d for p,d in zip(row['xy'],data['datum_mm'])];nz=z-4.8
        additions.append(cylinder(3.1,z-1.5,x,y,0).fuse(cylinder(1.95,1.5,x,y,z-1.5)))
        vertices=[App.Vector(x+a,y+b,nz) for a,b in hexagon(0,0,pflat)]
        pocket=Part.Face(Part.makePolygon(vertices+[vertices[0]])).extrude(App.Vector(0,0,ph))
        entry,path=native_tools(x,y,nz,(0,1 if y>0 else -1));paths.append(path)
        cuts.extend((pocket,entry,cylinder(1.1,z+.2,x,y,-.1)))
        # The source model is 1.57mm thick. Use the selected M2x8 screws at
        # 6.8mm finished length, with a 3.8mm cap head and no PCB washer.
        products['GPSScrew'+str(i)]=cylinder(1,6.8,x,y,z+1.57-6.8).fuse(cylinder(1.9,2,x,y,z+1.57))
        vertices=[App.Vector(x+a,y+b,nz) for a,b in hexagon(0,0,flat)]
        products['GPSNut'+str(i)]=Part.Face(Part.makePolygon(vertices+[vertices[0]])).extrude(App.Vector(0,0,nh)).cut(cylinder(1.1,nh+.2,x,y,nz-.1))
        probes.append(cylinder(1.95,.05,x,y,z-.05).cut(cylinder(row['drill']/2,.1,x,y,z-.075)))
        # This is a design clearance, not a manufacturer component keepout.
        reserved=reserved.cut(cylinder(2.016,8.2,x,y,z-.1))
    products['GPSComponents']=reserved
    result={**products,'rear_addition':Part.makeCompound(additions),'rear_cutout':Part.makeCompound(cuts),
            'mount_probes':probes,'nut_paths':paths}
    for value in result.values():
        for shape in value if isinstance(value,list) else [value]:shape.rotate(App.Vector(),App.Vector(0,0,1),rotation_deg)
    return result


def native_check(shapes,pcb_bottom_z=6,rotation_deg=90):
    import FreeCAD as App
    import Part
    from fastener_access import native_check_paths
    from solid_clearance import box_distance
    envelope(pcb_bottom_z,rotation_deg)
    if set(shapes)-{'rear_addition','rear_cutout','mount_probes','nut_paths'}!=CHECK_NAMES:raise ValueError('GPS fixture census is incomplete')
    for name in CHECK_NAMES:
        shape=shapes[name]
        if shape.isNull() or not shape.isValid():raise ValueError('Invalid GPS shape: '+name)
        if len(shape.Solids)!=1:raise ValueError('GPS source/hardware solid count differs: '+name)
    rear=Part.makeBox(65,65,2,App.Vector(-32.5,-32.5,0)).fuse(shapes['rear_addition']).cut(shapes['rear_cutout']).removeSplitter()
    if not rear.isValid() or len(rear.Solids)!=1:raise ValueError('GPS source posts do not connect to the rear interface')
    all_shapes={**{name:shapes[name] for name in CHECK_NAMES},'RearInterface':rear}
    for a,b in itertools.combinations(sorted(all_shapes),2):
        if box_distance(all_shapes[a].BoundBox,all_shapes[b].BoundBox)>1e-6:continue
        volume=all_shapes[a].common(all_shapes[b]).Volume
        if volume>1e-6:raise ValueError('GPS fixture interference '+a+'/'+b+': '+str(volume))
    # Independently check the original component bodies against the selected
    # hardware. Internal overlap in a publisher assembly is not permission to
    # clear a real component away for a screw or nut.
    original=Part.read(str(HERE/SOURCE/'3133.step'))
    original.translate(App.Vector(-25.4,-11.43,pcb_bottom_z))
    original.rotate(App.Vector(),App.Vector(0,0,1),rotation_deg)
    for name in HARDWARE_NAMES:
        for i,body in enumerate(original.Solids):
            if box_distance(shapes[name].BoundBox,body.BoundBox)>1e-6:continue
            volume=shapes[name].common(body).Volume
            if volume>1e-6:raise ValueError('GPS hardware intersects original source body '+name+'/'+str(i)+': '+str(volume))
    if len(shapes['mount_probes'])!=4 or any(probe.cut(rear).Volume>1e-6 for probe in shapes['mount_probes']):
        raise ValueError('Actual GPS PCB mounting annulus lacks full bearing')
    tips=[shapes['GPSNut'+str(i)].BoundBox.ZMin-shapes['GPSScrew'+str(i)].BoundBox.ZMin for i in range(4)]
    if any(not .2<=tip<=.8 for tip in tips):raise ValueError('GPS screw must engage the full nut with0.2..0.8mm tip projection')
    native_check_paths(shapes.get('nut_paths'),rear,4)
    # Verify all six selected direct-wire pad bores against the original PCB.
    pcb=shapes['GPSPCB']
    import math
    angle=math.radians(rotation_deg);c,s=math.cos(angle),math.sin(angle)
    for row in geometry()['terminals'].values():
        x,y=row['board_xy_mm'];x-=25.4;y-=11.43
        probe=Part.makeCylinder(row['drill_mm']/2,1.57,App.Vector(c*x-s*y,s*x+c*y,pcb_bottom_z))
        if probe.common(pcb).Volume>1e-6:raise ValueError('GPS mechanical/electrical pad registration differs: '+row['pad'])
    return {'scope':'source GPS module and mount component study','physical_products':9,'references':1,
            'source_module_solids':55,'source_body_hardware_clearance':'pass',
            'representation':'source PCB plus conservative loaded reference','mount_drills_mm':[row['drill'] for row in geometry()['mounts']],
            'screw_tip_projection_mm':tips,'loaded_reservation':envelope(pcb_bottom_z,rotation_deg),
            'physical_acceptance':'unmeasured','installed_assembly':'not checked'}
