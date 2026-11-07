"""PowerBoost source PCB, two source screw blocks and integral rear posts.

Nominal source geometry and assembly targets. Supplied fit, completed joints,
retention, vibration and enclosed operation still require physical tests.
"""
import itertools
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import electrical_boost

HERE=Path(__file__).resolve().parent
HARDWARE_NAMES=frozenset('Boost'+kind+str(i) for kind in ('Screw','Nut') for i in range(2))
PRODUCT_NAMES=HARDWARE_NAMES|{'BoostPCB','BoostTerminalX1','BoostTerminalX2'}
REFERENCE_NAMES=frozenset({'BoostComponents'})
CHECK_NAMES=PRODUCT_NAMES|REFERENCE_NAMES


def definition():return json.loads((HERE/'electrical-design.json').read_text())['parts']['BOOST']


def geometry(part=None):
    part=definition() if part is None else part
    terminals=electrical_boost.terminals(part)
    electrical_boost.terminal_blocks(part)
    board=ET.fromstring((HERE/electrical_boost.SOURCE/'Adafruit PowerBoost 1000 Basic.brd').read_bytes()).find('./drawing/board')
    libraries={row.get('name'):row for row in board.findall('./libraries/library')}
    outline=[{key:float(row.get(key,'0')) for key in ('x1','y1','x2','y2','curve')}
             for row in board.findall('./plain/wire') if row.get('layer')=='20']
    through=[];mounts=[]
    for element in board.findall('./elements/element'):
        package=next(row for row in libraries[element.get('library')].findall('./packages/package') if row.get('name')==element.get('package'))
        if not package.findall('pad'):continue
        rotation=element.get('rot','R0')
        if rotation not in {'R0','R90','R180','R270'}:raise ValueError('Unreviewed PowerBoost through-pad rotation')
        angle=math.radians(float(rotation[1:]));c,s=math.cos(angle),math.sin(angle)
        for pad in package.findall('pad'):
            x,y=float(pad.get('x')),float(pad.get('y'))
            row={'xy':[float(element.get('x'))+x*c-y*s,float(element.get('y'))+x*s+y*c],'drill':float(pad.get('drill'))}
            through.append(row)
            if element.get('package')=='MOUNTINGHOLE_2.5_PLATED':mounts.append(row)
    if mounts!=[{'xy':[2.794,20.32],'drill':2.5},{'xy':[2.54,2.54],'drill':2.5}]:
        raise ValueError('Review changed PowerBoost source mounting holes')
    package=next(row for row in board.findall('./libraries/library/packages/package') if row.get('name')=='MOUNTINGHOLE_2.5_PLATED')
    keepout=next(row for row in package.findall('circle') if row.get('layer')=='39')
    radius=float(keepout.get('radius'))+float(keepout.get('width'))/2
    if abs(radius-2.016)>1e-9:raise ValueError('Review the actual PowerBoost mounting keepout')
    return {'outline':outline,'through_pads':through,'mounts':mounts,'keepout_radius_mm':radius,'terminals':terminals}


def envelope(pcb_bottom_z=6,rotation_deg=0):
    if pcb_bottom_z not in (6,9) or rotation_deg not in (0,90):raise ValueError('Review PowerBoost post height and per-design orientation')
    # Preserve the earlier full loaded reservation. Terminal solids replace
    # only their own occupied volume; this is not a measured component scan.
    return {'size':[30,45,14] if rotation_deg==90 else [45,30,14],'z':pcb_bottom_z}


def native_shapes(pcb_bottom_z=6,rotation_deg=0,part=None):
    import FreeCAD as App
    import Part
    from fastener_access import native_tools
    from hardware_spec import nut_dimensions,hexagon
    part=definition() if part is None else part;data=geometry(part)
    envelope(pcb_bottom_z,rotation_deg);z=pcb_bottom_z
    def point(x,y,h=0):return App.Vector(x-14.605,y-11.43,h)
    def cylinder(r,h,x,y,bottom):return Part.makeCylinder(r,h,App.Vector(x,y,bottom))
    def box(w,l,h,x,y,bottom):return Part.makeBox(w,l,h,App.Vector(x-w/2,y-l/2,bottom))
    edges=[]
    for row in data['outline']:
        a=point(row['x1'],row['y1']);b=point(row['x2'],row['y2']);angle=math.radians(row['curve'])
        if not angle:edges.append(Part.makeLine(a,b));continue
        chord=b-a;length=chord.Length;left=App.Vector(-chord.y/length,chord.x/length,0)
        centre=(a+b)*.5+left*(length/(2*math.tan(angle/2)));offset=a-centre;c,s=math.cos(angle/2),math.sin(angle/2)
        mid=centre+App.Vector(offset.x*c-offset.y*s,offset.x*s+offset.y*c,0)
        edges.append(Part.Arc(a,mid,b).toShape())
    pcb=Part.Face(Part.Wire(edges)).extrude(App.Vector(0,0,1.6));pcb.translate(App.Vector(0,0,z))
    for row in data['through_pads']:
        x,y=row['xy'];pcb=pcb.cut(cylinder(row['drill']/2,1.8,x-14.605,y-11.43,z-.1))
    products={};component=box(45,30,12.4,0,0,z+1.6)
    for name,keys in (('X1',('OUT','OUTPUT_GND')),('X2',('BAT','INPUT_GND'))):
        pins=[data['terminals'][key]['board_xy_mm'] for key in keys]
        x=pins[0][0]-14.605;ys=[row[1]-11.43 for row in pins]
        # The drawing locates one end2.28mm from the outer pin. Reserve that
        # distance at BOTH ends (8.06mm total) to cover the0.1mm end asymmetry.
        # This is a conservative nominal reservation, not a body tolerance.
        body=box(6.8,max(ys)-min(ys)+2*2.28,8.4,x,sum(ys)/2,z+1.6)
        for y in ys:body=body.fuse(cylinder(.4,4,x,y,z+1.6-4))
        products['BoostTerminal'+name]=body.removeSplitter()
        component=component.cut(body)
    additions=[];cuts=[];probes=[];nut_paths=[]
    flat,nh=nut_dimensions('M2');pflat,ph=nut_dimensions('M2',pocket=True)
    for i,row in enumerate(data['mounts']):
        sx,sy=row['xy'];x,y=sx-14.605,sy-11.43;nz=z-4.8
        additions.append(cylinder(3.1,z-1.5,x,y,0).fuse(cylinder(1.95,1.5,x,y,z-1.5)))
        vertices=[App.Vector(x+a,y+b,nz) for a,b in hexagon(0,0,pflat)]
        pocket=Part.Face(Part.makePolygon(vertices+[vertices[0]])).extrude(App.Vector(0,0,ph))
        entry,path=native_tools(x,y,nz,(-1,0));nut_paths.append(path)
        cuts.extend((pocket,entry,cylinder(1.1,z+.2,x,y,-.1)))
        products['BoostScrew'+str(i)]=cylinder(1,6.8,x,y,z+1.6-6.8).fuse(cylinder(1.9,2,x,y,z+1.6))
        vertices=[App.Vector(x+a,y+b,nz) for a,b in hexagon(0,0,flat)]
        products['BoostNut'+str(i)]=Part.Face(Part.makePolygon(vertices+[vertices[0]])).extrude(App.Vector(0,0,nh)).cut(cylinder(1.1,nh+.2,x,y,nz-.1))
        component=component.cut(cylinder(data['keepout_radius_mm'],14,x,y,z+1.5))
        probes.append(cylinder(1.95,.05,x,y,z-.05).cut(cylinder(1.25,.1,x,y,z-.075)))
    products.update(BoostPCB=pcb.removeSplitter(),BoostComponents=component.removeSplitter())
    result={**products,'rear_addition':Part.makeCompound(additions),'rear_cutout':Part.makeCompound(cuts),'mount_probes':probes,'nut_paths':nut_paths}
    for value in result.values():
        for shape in value if isinstance(value,list) else [value]:shape.rotate(App.Vector(),App.Vector(0,0,1),rotation_deg)
    return result


def native_check(shapes,pcb_bottom_z=6,rotation_deg=0):
    import FreeCAD as App
    import Part
    from solid_clearance import bounds,box_distance
    if set(shapes)-{'rear_addition','rear_cutout','mount_probes','nut_paths'}!=CHECK_NAMES:raise ValueError('PowerBoost fixture census is incomplete')
    for name in CHECK_NAMES:
        if not shapes[name].isValid() or len(shapes[name].Solids)!=1:raise ValueError('PowerBoost fixture is invalid or detached: '+name)
    rear=Part.makeBox(55,55,2,App.Vector(-27.5,-27.5,0)).fuse(shapes['rear_addition']).cut(shapes['rear_cutout']).removeSplitter()
    if not rear.isValid() or len(rear.Solids)!=1:raise ValueError('PowerBoost posts do not connect to the rear interface')
    all_shapes={**{name:shapes[name] for name in CHECK_NAMES},'RearInterface':rear}
    for a,b in itertools.combinations(sorted(all_shapes),2):
        if box_distance(bounds(all_shapes[a]),bounds(all_shapes[b]))>1e-6:continue
        volume=all_shapes[a].common(all_shapes[b]).Volume
        if volume>1e-6:raise ValueError('PowerBoost interference '+a+'/'+b+': '+str(volume))
    if any(probe.cut(rear).Volume>1e-6 for probe in shapes['mount_probes']):raise ValueError('Actual PowerBoost PCB mounting annulus lacks full bearing')
    tips=[shapes['BoostNut'+str(i)].BoundBox.ZMin-shapes['BoostScrew'+str(i)].BoundBox.ZMin for i in range(2)]
    if any(not .2<=tip<=.8 for tip in tips):raise ValueError('PowerBoost screw must engage the full nut with0.2..0.8mm tip projection')
    from fastener_access import native_check_paths
    native_check_paths(shapes.get('nut_paths'),rear,2)
    return {'scope':'source PCB and terminal component study','physical_products':len(PRODUCT_NAMES),'references':len(REFERENCE_NAMES),
            'source_holes':2,'full_loaded_reservation':envelope(pcb_bottom_z,rotation_deg),
            'screw_tip_projection_mm':tips,'terminal_pin_below_pcb_mm':2.4,'physical_acceptance':'unmeasured','installed_assembly':'not checked'}
