"""Source Sparkle PCB, fixed input variant and four source-hole posts."""
import hashlib
import itertools
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import electrical_peripherals

HERE=Path(__file__).resolve().parent
SOURCE='sources/sparkle-motion-mechanical'
STEP_SHA256='ffa766ad93ef673a9cdd4d3d720250465180d765b05f07b30a11b8449fb8407f'
STEP_REVISION='6c5cd9e3e65252bb5d5339608cf8d3cdabcef251'
HARDWARE_NAMES=frozenset('Sparkle'+kind+str(i) for kind in ('Screw','Nut') for i in range(4))
PRODUCT_NAMES=HARDWARE_NAMES|{'SparklePCB'}
REFERENCE_NAMES=frozenset({'SparkleComponents','SparkleUnderboard'})
CHECK_NAMES=PRODUCT_NAMES|REFERENCE_NAMES


def definition():return json.loads((HERE/'electrical-design.json').read_text())


def geometry(design=None,directory=HERE):
    design=definition() if design is None else design;directory=Path(directory)
    terminals=electrical_peripherals.terminals('SPARKLE',design['parts']['SPARKLE'],directory)
    rework=design.get('module_rework',{})
    if (rework.get('SPARKLE.remove')!=['X7'] or rework.get('SPARKLE.retain')!=['D2','PTC1']
            or rework.get('SPARKLE.leave_open')!=['X7.GNDBREAK']):
        raise ValueError('Select only the reviewed X7 removal; retain D2/PTC1 and the unused ground pad')
    board=ET.fromstring((directory/'sources/sparkle-motion/Adafruit Sparkle Motion WLED Friend_Rev D.brd').read_bytes()).find('./drawing/board')
    mounts=[]
    for el in board.findall('./elements/element'):
        if el.get('package')=='MOUNTINGHOLE_2.5_PLATED':
            if el.get('rot','R0')!='R0':raise ValueError('Review changed Sparkle mounting-hole rotation')
            mounts.append([float(el.get('x')),float(el.get('y'))])
    if mounts!=[[2.54,2.54],[48.26,30.48],[2.54,30.48],[48.26,2.54]]:
        raise ValueError('Review changed Sparkle source mounting pattern')
    index=json.loads((directory/SOURCE/'index.json').read_text());row=next(row for row in index if row['file']=='6100.step')
    raw=(directory/SOURCE/'6100.step').read_bytes()
    if (hashlib.sha256(raw).hexdigest()!=STEP_SHA256 or row.get('sha256')!=STEP_SHA256
            or row.get('bytes')!=len(raw) or row.get('repository_revision')!=STEP_REVISION):
        raise ValueError('Sparkle mechanical source hash/revision mismatch')
    return {'mount_xy_mm':mounts,'mount_drill_mm':2.5,'terminals':terminals,'datum_mm':[25.4,16.51],
            'pcb_thickness_mm':1.57,'source_solids':239,'removed_source_solid':159,
            'underboard_source_indices':[174,177,180,183,186,189,192,195,198],
            'underboard_source_bounds_mm':{'x':[42.92,47.32],'y':[5.39,27.67],'z':[-1.93,0]},
            'underboard_xy_margin_mm':.25,
            'loaded_bounds_mm':{'x':[-1,50.8],'y':[0,33.147],'z':[-2.1,15]}}


def envelope(pcb_bottom_z=6,rotation_deg=None):
    rotation_deg=(180 if pcb_bottom_z==6 else 0) if rotation_deg is None else rotation_deg
    if (pcb_bottom_z,rotation_deg) not in ((6,180),(8,0)):raise ValueError('Review Sparkle post height and installed orientation')
    # Centre is the source hole-grid centre, not the slightly offset PCB centre.
    x=[-26.4,25.4] if rotation_deg==0 else [-25.4,26.4]
    y=[-16.51,16.637] if rotation_deg==0 else [-16.637,16.51]
    return {'x':x,'y':y,'z':[pcb_bottom_z-2.1,pcb_bottom_z+15]}


def source_module():
    import Part
    source=Part.read(str(HERE/SOURCE/'6100.step'))
    if not source.isValid() or len(source.Solids)!=239:raise ValueError('Sparkle original source assembly is incomplete/invalid')
    # Named-source inspection identifies DCJACK_2MM_PTH as this one solid.
    # Pin the original bytes, index, volume and bounds; do not choose a body
    # merely because it is inconvenient to fit.
    jack=source.Solids[159];b=jack.BoundBox
    measured=(jack.Volume,b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax)
    expected=(881.0812099467767,-3.258399699231602,6.068465547922076,-1.93,
              10.75160030076835,15.530985667923623,12.602447092482706)
    if any(abs(a-b)>1e-6 for a,b in zip(measured,expected)):raise ValueError('The reviewed X7 source body differs')
    pcb=max(source.Solids,key=lambda shape:shape.Volume);b=pcb.BoundBox
    if any(abs(a-b)>1e-6 for a,b in zip((b.XMin,b.YMin,b.ZMin,b.XLength,b.YLength,b.ZLength),(0,0,0,50.8,33.147,1.57))):
        raise ValueError('Sparkle source PCB datum/bounds differ')
    return source,pcb


def native_shapes(pcb_bottom_z=6,rotation_deg=None,design=None):
    import FreeCAD as App
    import Part
    from fastener_access import native_tools
    from hardware_spec import hexagon,nut_dimensions
    data=geometry(design);rotation_deg=(180 if pcb_bottom_z==6 else 0) if rotation_deg is None else rotation_deg
    envelope(pcb_bottom_z,rotation_deg);z=pcb_bottom_z;source,pcb=source_module()
    for i,body in enumerate(source.Solids):
        if i==data['removed_source_solid']:continue
        b=body.BoundBox
        if b.XMin < -1-1e-6 or b.XMax>50.8+1e-6 or b.YMin < -1e-6 or b.YMax>33.147+1e-6 or b.ZMin < -2.1-1e-6 or b.ZMax>15+1e-6:
            raise ValueError('A retained source body exceeds the full loaded reservation: '+str(i))
    pcb=pcb.copy();pcb.translate(App.Vector(-25.4,-16.51,z))
    top=Part.makeBox(51.8,33.147,15-1.57,App.Vector(-26.4,-16.51,z+1.57))
    # Only the nine retained JP1 pin bodies extend below the source PCB.
    # Preserve their complete source bounds plus an explicit assembly margin.
    # The earlier whole-board underside box also reserved empty board space.
    underside=[(i,body.BoundBox) for i,body in enumerate(source.Solids)
               if i!=data['removed_source_solid'] and body.BoundBox.ZMin < -1e-6]
    if [i for i,b in underside]!=data['underboard_source_indices']:raise ValueError('Review changed Sparkle underside bodies')
    actual=(min(b.XMin for i,b in underside),max(b.XMax for i,b in underside),
            min(b.YMin for i,b in underside),max(b.YMax for i,b in underside),min(b.ZMin for i,b in underside))
    if any(abs(a-b)>1e-6 for a,b in zip(actual,(42.92,47.32,5.39,27.67,-1.93))):
        raise ValueError('Review changed Sparkle underside source bounds')
    margin=data['underboard_xy_margin_mm'];x0,x1=data['underboard_source_bounds_mm']['x'];y0,y1=data['underboard_source_bounds_mm']['y']
    lower=Part.makeBox(x1-x0+2*margin,y1-y0+2*margin,2.1,App.Vector(x0-margin-25.4,y0-margin-16.51,z-2.1))
    products={'SparklePCB':pcb};additions=[];cuts=[];probes=[];paths=[]
    flat,nh=nut_dimensions('M2');pflat,ph=nut_dimensions('M2',pocket=True)
    def cylinder(radius,height,x,y,bottom):return Part.makeCylinder(radius,height,App.Vector(x,y,bottom))
    for i,(sx,sy) in enumerate(data['mount_xy_mm']):
        x,y=sx-25.4,sy-16.51;nz=z-4.8
        additions.append(cylinder(3.1,z-2.1,x,y,0).fuse(cylinder(1.95,2.1,x,y,z-2.1)))
        vertices=[App.Vector(x+a,y+b,nz) for a,b in hexagon(0,0,pflat)]
        pocket=Part.Face(Part.makePolygon(vertices+[vertices[0]])).extrude(App.Vector(0,0,ph))
        entry,path=native_tools(x,y,nz,(0,-1 if y<0 else 1));paths.append(path)
        cuts.extend((pocket,entry,cylinder(1.1,z+.2,x,y,-.1)))
        products['SparkleScrew'+str(i)]=cylinder(1,6.8,x,y,z+1.57-6.8).fuse(cylinder(1.9,2,x,y,z+1.57))
        vertices=[App.Vector(x+a,y+b,nz) for a,b in hexagon(0,0,flat)]
        products['SparkleNut'+str(i)]=Part.Face(Part.makePolygon(vertices+[vertices[0]])).extrude(App.Vector(0,0,nh)).cut(cylinder(1.1,nh+.2,x,y,nz-.1))
        probes.append(cylinder(1.95,.05,x,y,z-.05).cut(cylinder(1.25,.1,x,y,z-.075)))
        top=top.cut(cylinder(2.016,15,x,y,z+1.5));lower=lower.cut(cylinder(2.016,2.3,x,y,z-2.2))
    products.update(SparkleComponents=top,SparkleUnderboard=lower)
    result={**products,'rear_addition':Part.makeCompound(additions),'rear_cutout':Part.makeCompound(cuts),
            'mount_probes':probes,'nut_paths':paths}
    for value in result.values():
        for shape in value if isinstance(value,list) else [value]:shape.rotate(App.Vector(),App.Vector(0,0,1),rotation_deg)
    return result


def native_check(shapes,pcb_bottom_z=6,rotation_deg=None):
    import FreeCAD as App
    import Part
    from fastener_access import native_check_paths
    from solid_clearance import box_distance
    rotation_deg=(180 if pcb_bottom_z==6 else 0) if rotation_deg is None else rotation_deg;envelope(pcb_bottom_z,rotation_deg)
    if set(shapes)-{'rear_addition','rear_cutout','mount_probes','nut_paths'}!=CHECK_NAMES:raise ValueError('Sparkle fixture census is incomplete')
    for name in CHECK_NAMES:
        if not shapes[name].isValid() or len(shapes[name].Solids)!=1:raise ValueError('Invalid or detached Sparkle shape: '+name)
    rear=Part.makeBox(80,65,2,App.Vector(-40,-32.5,0)).fuse(shapes['rear_addition']).cut(shapes['rear_cutout']).removeSplitter()
    if not rear.isValid() or len(rear.Solids)!=1:raise ValueError('Sparkle posts do not connect to the rear interface')
    all_shapes={**{name:shapes[name] for name in CHECK_NAMES},'RearInterface':rear}
    for a,b in itertools.combinations(sorted(all_shapes),2):
        if box_distance(all_shapes[a].BoundBox,all_shapes[b].BoundBox)>1e-6:continue
        volume=all_shapes[a].common(all_shapes[b]).Volume
        if volume>1e-6:raise ValueError('Sparkle fixture interference '+a+'/'+b+': '+str(volume))
    source,_=source_module();source.translate(App.Vector(-25.4,-16.51,pcb_bottom_z));source.rotate(App.Vector(),App.Vector(0,0,1),rotation_deg)
    clip=Part.makeBox(100,100,2.1,App.Vector(-50,-50,pcb_bottom_z-2.1))
    for i in geometry()['underboard_source_indices']:
        below=source.Solids[i].common(clip)
        if below.Volume<=0 or below.cut(shapes['SparkleUnderboard']).Volume>1e-6:
            raise ValueError('Sparkle underside pins exceed their reservation: '+str(i))
    for name in HARDWARE_NAMES:
        for i,body in enumerate(source.Solids):
            if i==159 or box_distance(shapes[name].BoundBox,body.BoundBox)>1e-6:continue
            volume=shapes[name].common(body).Volume
            if volume>1e-6:raise ValueError('Sparkle hardware intersects retained source body '+name+'/'+str(i)+': '+str(volume))
    if len(shapes['mount_probes'])!=4 or any(probe.cut(rear).Volume>1e-6 for probe in shapes['mount_probes']):
        raise ValueError('Actual Sparkle PCB mounting annulus lacks full bearing')
    tips=[shapes['SparkleNut'+str(i)].BoundBox.ZMin-shapes['SparkleScrew'+str(i)].BoundBox.ZMin for i in range(4)]
    if any(not .2<=tip<=.8 for tip in tips):raise ValueError('Sparkle screw must engage the full nut with0.2..0.8mm tip projection')
    native_check_paths(shapes.get('nut_paths'),rear,4)
    data=geometry()
    import math
    angle=math.radians(rotation_deg);c,s=math.cos(angle),math.sin(angle)
    for row in data['terminals'].values():
        x,y=row['board_xy_mm'];x-=25.4;y-=16.51
        probe=Part.makeCylinder(row['drill_mm']/2,1.57,App.Vector(c*x-s*y,s*x+c*y,pcb_bottom_z))
        if probe.common(shapes['SparklePCB']).Volume>1e-6:raise ValueError('Sparkle mechanical/electrical pad registration differs: '+row['pad'])
    return {'scope':'source Sparkle PCB and mount component study','physical_products':9,'references':2,
            'source_solids':239,'removed_source_solid':159,'removed_component':'X7 / DCJACK_2MM_PTH',
            'retained_input_protection':['D2','PTC1'],'source_body_hardware_clearance':'pass',
            'source_underside_pin_containment':'pass','underboard_xy_assembly_margin_mm':.25,
            'screw_tip_projection_mm':tips,'loaded_reservation':envelope(pcb_bottom_z,rotation_deg),
            'physical_acceptance':'unmeasured','installed_assembly':'not checked'}
