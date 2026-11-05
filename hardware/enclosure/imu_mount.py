"""Actual classic Rev A PCB and its four source-hole mounting posts.

The40x28x12mm loaded reservation stays in force. Native nominal geometry does
not establish supplied dimensions, finished joints or physical retention.
"""
import itertools
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import electrical_imu

HERE=Path(__file__).resolve().parent
HARDWARE_NAMES=frozenset('IMU'+kind+str(i) for kind in ('Screw','Nut') for i in range(4))
PRODUCT_NAMES=HARDWARE_NAMES|{'IMUPCB'}
REFERENCE_NAMES=frozenset({'IMUComponents'})
CHECK_NAMES=PRODUCT_NAMES|REFERENCE_NAMES


def definition():return json.loads((HERE/'electrical-design.json').read_text())['parts']['IMU']


def geometry(part=None):
    part=definition() if part is None else part
    terminals=electrical_imu.terminals(part)
    if part['loaded_envelope_mm']!=[40,28,12]:raise ValueError('Retain the selected full IMU loaded reservation')
    board=ET.fromstring((HERE/electrical_imu.SOURCE/'Adafruit LSM9DS1 Rev A.brd').read_bytes()).find('./drawing/board')
    outline=[{key:float(row.get(key,'0')) for key in ('x1','y1','x2','y2','curve')}
             for row in board.findall('./plain/wire') if row.get('layer')=='20']
    holes=[]
    for row in board.findall('./elements/element'):
        if row.get('package')=='MOUNTINGHOLE_2.5_PLATED':holes.append([float(row.get('x')),float(row.get('y'))])
    if holes!=[[2.54,2.54],[30.48,2.54],[30.48,17.78],[2.54,17.78]]:
        raise ValueError('IMU source mounting pattern changed')
    package=next(row for row in board.findall('./libraries/library/packages/package') if row.get('name')=='MOUNTINGHOLE_2.5_PLATED')
    pad=package.find('pad');keepout=next(row for row in package.findall('circle') if row.get('layer')=='39')
    radius=float(keepout.get('radius'))+float(keepout.get('width'))/2
    if float(pad.get('drill'))!=2.5 or abs(radius-2.016)>1e-9:
        raise ValueError('Review the actual hole and component keepout before selecting a screw head')
    libraries={row.get('name'):row for row in board.findall('./libraries/library')}
    through=[]
    for element in board.findall('./elements/element'):
        package=next(row for row in libraries[element.get('library')].findall('./packages/package') if row.get('name')==element.get('package'))
        pads=package.findall('pad')
        if not pads:continue
        rotation=element.get('rot','R0')
        if rotation not in {'R0','R90','R180','R270'}:raise ValueError('Unreviewed IMU through-pad rotation')
        angle=math.radians(float(rotation[1:]));c,s=math.cos(angle),math.sin(angle)
        for pad in pads:
            x,y=float(pad.get('x')),float(pad.get('y'))
            through.append({'xy':[float(element.get('x'))+x*c-y*s,float(element.get('y'))+x*s+y*c],
                            'drill':float(pad.get('drill'))})
    return {'outline':outline,'mount_xy_mm':holes,'mount_drill_mm':2.5,'through_pads':through,
            'keepout_radius_mm':radius,'terminals':terminals}


def native_shapes(pcb_bottom_z=6,rotation_deg=0,part=None):
    import FreeCAD as App
    import Part
    from fastener_access import native_tools
    from hardware_spec import nut_dimensions,hexagon
    data=geometry(part);part=definition() if part is None else part
    if pcb_bottom_z not in (6,9) or rotation_deg not in (0,90):
        raise ValueError('Review IMU source post height and per-design orientation')
    z=pcb_bottom_z
    def point(x,y,h=0):return App.Vector(x-16.51,y-10.16,h)
    edges=[]
    for row in data['outline']:
        a=point(row['x1'],row['y1']);b=point(row['x2'],row['y2']);angle=math.radians(row['curve'])
        if not angle:edges.append(Part.makeLine(a,b));continue
        chord=b-a;length=chord.Length
        left=App.Vector(-chord.y/length,chord.x/length,0)
        centre=(a+b)*.5+left*(length/(2*math.tan(angle/2)))
        offset=a-centre;c,s=math.cos(angle/2),math.sin(angle/2)
        mid=centre+App.Vector(offset.x*c-offset.y*s,offset.x*s+offset.y*c,0)
        edges.append(Part.Arc(a,mid,b).toShape())
    pcb=Part.Face(Part.Wire(edges)).extrude(App.Vector(0,0,1.6));pcb.translate(App.Vector(0,0,z))
    def cylinder(r,h,x,y,bottom):return Part.makeCylinder(r,h,App.Vector(x,y,bottom))
    def box(w,l,h,x,y,bottom):return Part.makeBox(w,l,h,App.Vector(x-w/2,y-l/2,bottom))
    holes=[]
    for row in data['through_pads']:
        x,y=row['xy'];holes.append(cylinder(row['drill']/2,1.8,x-16.51,y-10.16,z-.1))
    pcb=pcb.cut(Part.makeCompound(holes))
    additions=[];cuts=[];products={};mount_probes=[];nut_paths=[]
    flat,nh=nut_dimensions('M2');pflat,pheight=nut_dimensions('M2',pocket=True)
    component=box(40,28,12-1.6,0,0,z+1.6)
    for i,(sx,sy) in enumerate(data['mount_xy_mm']):
        x,y=sx-16.51,sy-10.16
        pcb=pcb.cut(cylinder(1.25,1.8,x,y,z-.1))
        # The source2.016mm keepout accepts a3.8mm M2 cap head.
        # A standard5mm DIN125 washer would exceed that keepout; omit it here.
        component=component.cut(cylinder(data['keepout_radius_mm'],12,x,y,z+1.5))
        pod=cylinder(3.1,z-1.5,x,y,0).fuse(cylinder(1.95,1.5,x,y,z-1.5))
        nz=z-4.8
        vertices=[App.Vector(x+a,y+b,nz) for a,b in hexagon(0,0,pflat)]
        pocket=Part.Face(Part.makePolygon(vertices+[vertices[0]])).extrude(App.Vector(0,0,pheight))
        direction=-1 if x<0 else 1
        entry,path=native_tools(x,y,nz,(direction,0));nut_paths.append(path)
        bore=cylinder(1.1,z+.2,x,y,-.1)
        additions.append(pod);cuts.extend((pocket,entry,bore))
        products['IMUScrew'+str(i)]=cylinder(1,6.8,x,y,z+1.6-6.8).fuse(cylinder(1.9,2,x,y,z+1.6))
        vertices=[App.Vector(x+a,y+b,nz) for a,b in hexagon(0,0,flat)]
        products['IMUNut'+str(i)]=Part.Face(Part.makePolygon(vertices+[vertices[0]])).extrude(App.Vector(0,0,nh)).cut(cylinder(1.1,nh+.2,x,y,nz-.1))
        mount_probes.append(cylinder(1.95,.05,x,y,z-.05).cut(cylinder(1.25,.1,x,y,z-.075)))
    # Reserve the selected direct-wire header sites above the board. These are
    # nominal assembly channels, not measured solder or component tolerances.
    for row in data['terminals'].values():
        x,y=row['board_xy_mm'];x-=16.51;y-=10.16
        pcb=pcb.cut(cylinder(row['drill_mm']/2,1.8,x,y,z-.1))
        component=component.cut(cylinder(1.1,12,x,y,z+1.5))
    products.update(IMUPCB=pcb.removeSplitter(),IMUComponents=component.removeSplitter())
    result={**products,'rear_addition':Part.makeCompound(additions),'rear_cutout':Part.makeCompound(cuts),'mount_probes':mount_probes,'nut_paths':nut_paths}
    for value in result.values():
        for shape in value if isinstance(value,list) else [value]:shape.rotate(App.Vector(),App.Vector(0,0,1),rotation_deg)
    return result


def native_check(shapes,pcb_bottom_z):
    import FreeCAD as App
    import Part
    if set(shapes)-{'rear_addition','rear_cutout','mount_probes','nut_paths'}!=CHECK_NAMES:
        raise ValueError('IMU fixture census is incomplete')
    for name in CHECK_NAMES:
        shape=shapes[name]
        if not shape.isValid() or len(shape.Solids)!=1:raise ValueError('IMU part is invalid or detached: '+name)
    rear=Part.makeBox(45,36,2,App.Vector(-22.5,-18,0)).fuse(shapes['rear_addition']).cut(shapes['rear_cutout']).removeSplitter()
    if not rear.isValid() or len(rear.Solids)!=1:raise ValueError('IMU source posts do not connect to the rear interface')
    all_shapes={**{name:shapes[name] for name in CHECK_NAMES},'RearInterface':rear}
    for a,b in itertools.combinations(sorted(all_shapes),2):
        volume=all_shapes[a].common(all_shapes[b]).Volume
        if volume>1e-6:raise ValueError('IMU fixture interference '+a+'/'+b+': '+str(volume))
    missing=[probe.cut(rear).Volume for probe in shapes['mount_probes']]
    if any(value>1e-6 for value in missing):raise ValueError('An actual PCB mounting annulus lacks full bearing')
    projections=[shapes['IMUNut'+str(i)].BoundBox.ZMin-shapes['IMUScrew'+str(i)].BoundBox.ZMin for i in range(4)]
    if any(not .2<=tip<=.8 for tip in projections):raise ValueError('IMU screw must engage the full nut with0.2..0.8mm tip projection')
    from fastener_access import native_check_paths
    native_check_paths(shapes.get('nut_paths'),rear,4)
    return {'scope':'actual source PCB mount component study','physical_product_count':len(PRODUCT_NAMES),'reference_count':len(REFERENCE_NAMES),
            'mounts':4,'nominal_head_keepout_gap_mm':geometry()['keepout_radius_mm']-1.9,
            'screw_tip_projection_mm':projections,'physical_acceptance':'unmeasured','installed_assembly':'not checked'}
