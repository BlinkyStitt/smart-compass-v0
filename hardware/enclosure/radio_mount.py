"""Source-outline radio carrier; nominal geometry, no RF or supplied-fit claim."""
import itertools
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import electrical_peripherals

HERE=Path(__file__).resolve().parent
L,W=25.4,29.21
DATUM=(L/2,W/2)
HARDWARE_NAMES=frozenset('Radio'+kind+str(i) for kind in ('Screw','Nut') for i in range(3))
PRINTED_PARTS=frozenset({'RadioCarrier'}|{'RadioRetainer'+str(i) for i in range(3)})
PRODUCT_NAMES=HARDWARE_NAMES|PRINTED_PARTS|{'RadioPCB'}
REFERENCE_NAMES=frozenset({'RadioLoadedReservation','RadioUnderboardReservation'})
CHECK_NAMES=PRODUCT_NAMES|REFERENCE_NAMES
BARE=['JP1','JP2','JP3','X1']
UNWIRED=['JP1.'+str(i) for i in range(1,6)]+['JP3.3']
PHYSICAL_ELEMENTS={'U1','U2','U3','C1','C2','C3','R1','R2','R3'}


def definition():return json.loads((HERE/'electrical-design.json').read_text())


def _rotate(x,y,rotation):
    if rotation not in ('R0','R90','R180','R270'):raise ValueError('Unreviewed radio source rotation')
    a=math.radians(float(rotation[1:]));return x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a)


def geometry(design=None,directory=HERE):
    design=definition() if design is None else design;directory=Path(directory)
    terminals=electrical_peripherals.terminals('RADIO',design['parts']['RADIO'],directory)
    rework=design.get('module_rework',{})
    if rework.get('RADIO.do_not_install')!=BARE or rework.get('RADIO.leave_open')!=UNWIRED:
        raise ValueError('Select bare radio pads, no X1 antenna connector and only the reviewed fixed wires')
    selected=electrical_peripherals.BOARDS['RADIO']
    board=ET.fromstring((directory/selected['source']/'Adafruit RFM+LoRa Breakout.brd').read_bytes()).find('./drawing/board')
    libraries={row.get('name'):row for row in board.findall('./libraries/library')}
    elements=board.findall('./elements/element');pads=[];bounds=[]
    physical={e.get('name') for e in elements if not e.get('name').startswith(('U$','FID')) and e.get('name') not in BARE}
    if physical!=PHYSICAL_ELEMENTS:raise ValueError('Review every changed populated radio source element')
    def placed(e,x,y):
        u,v=_rotate(x,y,e.get('rot','R0'));return [float(e.get('x'))+u-.254,float(e.get('y'))+v]
    for e in elements:
        package=next(row for row in libraries[e.get('library')].findall('./packages/package') if row.get('name')==e.get('package'))
        if package.findall('hole'):raise ValueError('Review new radio mechanical holes; the selected board has none')
        for pad in package.findall('pad'):
            pads.append({'pad':e.get('name')+'.'+pad.get('name'),'xy':placed(e,float(pad.get('x')),float(pad.get('y'))),'drill':float(pad.get('drill'))})
        if e.get('name') not in physical:continue
        points=[]
        for row in package:
            if row.tag=='wire' and row.get('layer') in ('21','51'):
                if float(row.get('curve','0')):raise ValueError('Review curved populated radio package bounds')
                half=float(row.get('width','0'))/2
                for i in ('1','2'):
                    x,y=float(row.get('x'+i)),float(row.get('y'+i))
                    points.extend((x+dx*half,y+dy*half) for dx in (-1,1) for dy in (-1,1))
            if row.tag=='circle' and row.get('layer') in ('21','51'):
                x,y,radius=[float(row.get(k)) for k in ('x','y','radius')];radius+=float(row.get('width','0'))/2
                points.extend((x+dx*radius,y+dy*radius) for dx in (-1,1) for dy in (-1,1))
            if row.tag=='polygon' and row.get('layer') in ('21','51'):
                for vertex in row.findall('vertex'):
                    if float(vertex.get('curve','0')):raise ValueError('Review curved radio package polygon')
                    x,y=float(vertex.get('x')),float(vertex.get('y'));half=float(row.get('width','0'))/2
                    points.extend((x+dx*half,y+dy*half) for dx in (-1,1) for dy in (-1,1))
            if row.tag=='rectangle' and row.get('layer') in ('1','21','51'):
                if row.get('rot','R0')!='R0':raise ValueError('Review rotated radio package rectangle')
                points.extend((float(row.get('x'+i)),float(row.get('y'+j))) for i in ('1','2') for j in ('1','2'))
            if row.tag=='smd' and row.get('layer')=='1':
                x,y,dx,dy=[float(row.get(k)) for k in ('x','y','dx','dy')]
                for u,v in itertools.product((-dx/2,dx/2),(-dy/2,dy/2)):
                    u,v=_rotate(u,v,row.get('rot','R0'));points.append((x+u,y+v))
        if not points:raise ValueError('Radio source element has no footprint boundary')
        xy=[placed(e,*p) for p in points];lo=[min(p[i] for p in xy) for i in (0,1)];hi=[max(p[i] for p in xy) for i in (0,1)]
        if not 0<=lo[0]<hi[0]<=L or not .6<lo[1]<hi[1]<W-.6:
            raise ValueError('Populated radio source footprint reaches an edge capture land: '+e.get('name'))
        bounds.append({'element':e.get('name'),'package':e.get('package'),'min_mm':lo,'max_mm':hi})
    if len(pads)!=15 or any(p['pad'].split('.')[0] not in ('JP1','JP2','JP3') for p in pads):
        raise ValueError('Review radio through-pad census')
    outline=[{key:float(row.get(key,'0')) for key in ('x1','y1','x2','y2','curve')} for row in board.findall('./plain/wire') if row.get('layer')=='20']
    if len(outline)!=7:raise ValueError('Review radio source outline')
    return {'terminals':terminals,'through_pads':pads,'outline':outline,'footprint_bounds':bounds,
            'stations_mm':[[5,W+4.2],[20.4,W+4.2],[23.8,-4.2]],
            'nut_entry_axes':[[1,0],[1,0],[-1,0]],
            'edge_overlap_mm':.6,'retainer_slot_mm':1.85,'pcb_thickness_target_mm':1.6,
            'physical_acceptance':'unmeasured; package drawings are nominal XY inputs, not supplied 3D maximum bounds'}


def envelope(pcb_bottom_z=6,rotation_deg=180):
    if (pcb_bottom_z,rotation_deg) not in ((6,180),(8,0)):raise ValueError('Review radio PCB height and per-design orientation')
    return {'size':[L,W,10.1],'z':pcb_bottom_z-2.1}


def native_shapes(pcb_bottom_z=6,rotation_deg=180,design=None):
    import FreeCAD as App
    import Part
    from fastener_access import native_tools
    from hardware_spec import hexagon,nut_dimensions
    data=geometry(design);envelope(pcb_bottom_z,rotation_deg);z=pcb_bottom_z
    def box(x0,x1,y0,y1,bottom,height):return Part.makeBox(x1-x0,y1-y0,height,App.Vector(x0,y0,bottom))
    def cylinder(r,h,x,y,bottom):return Part.makeCylinder(r,h,App.Vector(x,y,bottom))
    edges=[]
    for row in data['outline']:
        a=App.Vector(row['x1']-.254,row['y1'],0);b=App.Vector(row['x2']-.254,row['y2'],0);angle=math.radians(row['curve'])
        if not angle:edges.append(Part.makeLine(a,b));continue
        chord=b-a;left=App.Vector(-chord.y/chord.Length,chord.x/chord.Length,0)
        centre=(a+b)*.5+left*(chord.Length/(2*math.tan(angle/2)));offset=a-centre;c,s=math.cos(angle/2),math.sin(angle/2)
        mid=centre+App.Vector(offset.x*c-offset.y*s,offset.x*s+offset.y*c,0)
        edges.append(Part.Arc(a,mid,b).toShape())
    pcb=Part.Face(Part.Wire(edges)).extrude(App.Vector(0,0,1.6));pcb.translate(App.Vector(0,0,z))
    for pad in data['through_pads']:pcb=pcb.cut(cylinder(pad['drill']/2,1.8,*pad['xy'],z-.1))
    pieces=[box(-1.5,L+.25,y0,y1,4.1,z+1.85-4.1) for y0,y1 in ((-1.6,-.25),(W+.25,W+1.6))]
    pieces.append(box(-2.85,-.25,-1.6,W+1.6,4.1,1.35))
    pieces.append(box(24,L+1.6,-1.6,W+1.6,z-1.35,1.35))
    for y0,y1 in ((-1.6,.6),(W-.6,W+1.6)):pieces.append(box(0,L,y0,y1,z-1.35,1.35))
    # End stops meet straight board edges, beyond the rounded corner regions.
    pieces.append(box(-1.6,-.25,4,W-4,4.1,z+1.35-4.1))
    pieces.append(box(L+.25,L+1.6,4,W-4,z-1.35,2.7))
    products={'RadioPCB':pcb.removeSplitter()};additions=[];cuts=[];probes=[];stops=[];paths=[]
    flat,nh=nut_dimensions('M2');pflat,ph=nut_dimensions('M2',pocket=True)
    for i,(x,y) in enumerate(data['stations_mm']):
        pieces.append(cylinder(3.9,z+1.85-4.1,x,y,4.1));additions.append(cylinder(3.9,4.1,x,y,0))
        points=[App.Vector(x+a,y+b,.85) for a,b in hexagon(0,0,pflat)]
        pocket=Part.Face(Part.makePolygon(points+[points[0]])).extrude(App.Vector(0,0,ph))
        entry,path=native_tools(x,y,.85,data['nut_entry_axes'][i],length=9);paths.append(path)
        cuts.extend((pocket,entry,cylinder(1.1,4.3,x,y,-.1)))
        y0,y1=(y-3.9,.6) if y<0 else (W-.6,y+3.9)
        products['RadioRetainer'+str(i)]=box(x-3.9,x+3.9,y0,y1,z+1.85,1.35).cut(cylinder(1.1,1.55,x,y,z+1.75))
        top=z+3.2;length=z+2.75
        products['RadioScrew'+str(i)]=cylinder(1,length,x,y,top-length).fuse(cylinder(1.9,2,x,y,top))
        points=[App.Vector(x+a,y+b,.85) for a,b in hexagon(0,0,flat)]
        products['RadioNut'+str(i)]=Part.Face(Part.makePolygon(points+[points[0]])).extrude(App.Vector(0,0,nh)).cut(cylinder(1.1,nh+.2,x,y,.75))
        probes.append(cylinder(3.9,.05,x,y,4.05).cut(cylinder(1.1,.1,x,y,4.025)))
        stops.append(cylinder(3.9,.05,x,y,z+1.8).cut(cylinder(1.1,.1,x,y,z+1.775)))
    carrier=pieces[0].multiFuse(pieces[1:]).removeSplitter()
    for x,y in data['stations_mm']:carrier=carrier.cut(cylinder(1.1,z+4,x,y,4))
    products['RadioCarrier']=carrier.removeSplitter()
    # Keep the existing bounded ANT launch neighbourhood. No other pad gets
    # this exception; all future joints/wires need their own complete check.
    ant=data['terminals']['ANT']['board_xy_mm'];relief=cylinder(3.2,13,*ant,z-3)
    products['RadioLoadedReservation']=box(0,L,.6,W-.6,z+1.6,6.4).cut(relief).removeSplitter()
    products['RadioUnderboardReservation']=box(0,23.75,.8,W-.8,z-2.1,2.1).cut(relief).removeSplitter()
    result={**products,'rear_addition':Part.makeCompound(additions),'rear_cutout':Part.makeCompound(cuts),'mount_probes':probes,'stop_probes':stops,'nut_paths':paths}
    for value in result.values():
        for shape in value if isinstance(value,list) else [value]:
            shape.translate(App.Vector(-DATUM[0],-DATUM[1],0));shape.rotate(App.Vector(),App.Vector(0,0,1),rotation_deg)
    return result


def carrier_with_antenna(shapes,route,datum_xy):
    """Join the actual two saddles to the removable carrier, beyond the PCB."""
    import FreeCAD as App
    import Part
    import antenna_native
    rotation=0 if route.direction==1 else 180
    envelope(route.feed[2],rotation)
    pin=geometry()['terminals']['ANT']['board_xy_mm']
    expected=[datum_xy[i]+route.direction*(pin[i]-DATUM[i]) for i in (0,1)]
    if any(abs(a-b)>1e-6 for a,b in zip(route.feed[:2],expected)):
        raise ValueError('Radio carrier and actual ANT route have different source datums')
    begin=datum_xy[1]+route.direction*(W/2+.25)
    lo=min(begin,*(route.point(v)[1]-3 for v in route.restraints))
    hi=max(begin,*(route.point(v)[1]+3 for v in route.restraints))
    spine=Part.makeBox(6,hi-lo,3,App.Vector(route.feed[0]-3,lo,4.1))
    extension=spine.multiFuse(antenna_native.restraints(route,4.1)).removeSplitter()
    extension.translate(App.Vector(-datum_xy[0],-datum_xy[1],0))
    result=dict(shapes)
    result['RadioCarrier']=shapes['RadioCarrier'].fuse(extension).removeSplitter()
    # Late support material must preserve every original screw clearance.
    for x,y in geometry()['stations_mm']:
        x,y=_rotate(x-DATUM[0],y-DATUM[1],'R'+str(rotation))
        result['RadioCarrier']=result['RadioCarrier'].cut(Part.makeCylinder(1.1,route.feed[2]+4,App.Vector(x,y,4)))
    result['RadioCarrier']=result['RadioCarrier'].removeSplitter()
    if not result['RadioCarrier'].isValid() or len(result['RadioCarrier'].Solids)!=1:
        raise ValueError('Radio antenna carrier is disconnected')
    return result


def _contact(probe,shape):
    z=probe.BoundBox.ZMax;face=max((f for f in probe.Faces if f.BoundBox.ZLength<1e-7 and abs(f.BoundBox.ZMax-z)<1e-7),key=lambda f:f.Area)
    return face.Area,sum(face.common(f).Area for f in shape.Faces if f.BoundBox.ZLength<1e-7 and abs(f.BoundBox.ZMin-z)<1e-7)


def native_service_check(shapes,pcb_bottom_z,rotation_deg,obstacles):
    import FreeCAD as App
    import Part
    from solid_clearance import bounds,box_distance
    for sweep in (Part.makeBox(L,W,28,App.Vector(0,0,pcb_bottom_z)),Part.makeBox(23.75,W-1.6,30.1,App.Vector(0,.8,pcb_bottom_z-2.1))):
        sweep.translate(App.Vector(-DATUM[0],-DATUM[1],0));sweep.rotate(App.Vector(),App.Vector(0,0,1),rotation_deg)
        for name,shape in obstacles.items():
            if box_distance(bounds(sweep),bounds(shape))>1e-6:continue
            if sweep.common(shape).Volume>1e-6:raise ValueError('Radio vertical assembly path is blocked: '+name)
    return {'motion':'continuous vertical20mm; all three retainers/screws removed','scope':'component assembly, before wiring and case installation'}


def native_check(shapes,pcb_bottom_z=6,rotation_deg=180):
    import FreeCAD as App
    import Part
    from fastener_access import native_check_paths
    from solid_clearance import bounds,box_distance
    data=geometry();envelope(pcb_bottom_z,rotation_deg);z=pcb_bottom_z
    if set(shapes)-{'rear_addition','rear_cutout','mount_probes','stop_probes','nut_paths'}!=CHECK_NAMES:raise ValueError('Radio fixture census is incomplete')
    for name in CHECK_NAMES:
        if not shapes[name].isValid() or len(shapes[name].Solids)!=1:raise ValueError('Invalid/detached radio shape: '+name)
    rear=Part.makeBox(70,75,2,App.Vector(-35,-37.5,0)).fuse(shapes['rear_addition']).cut(shapes['rear_cutout']).removeSplitter()
    if not rear.isValid() or len(rear.Solids)!=1:raise ValueError('Radio rear bosses are disconnected')
    all_shapes={**{name:shapes[name] for name in CHECK_NAMES},'RearInterface':rear}
    for a,b in itertools.combinations(sorted(all_shapes),2):
        if box_distance(bounds(all_shapes[a]),bounds(all_shapes[b]))>1e-6:continue
        volume=all_shapes[a].common(all_shapes[b]).Volume
        if volume>1e-6:raise ValueError('Radio fixture interference '+a+'/'+b+': '+str(volume))
    if len(shapes['mount_probes'])!=3 or len(shapes['stop_probes'])!=3:raise ValueError('Three radio bearing and hard-stop probes are required')
    for i,probe in enumerate(shapes['mount_probes']):
        if probe.cut(rear).Volume>1e-6:raise ValueError('Radio rear mounting annulus lacks full bearing')
        area,actual=_contact(probe,shapes['RadioCarrier'])
        if area-actual>1e-6:raise ValueError('Radio carrier lacks full rear bearing')
        area,actual=_contact(shapes['stop_probes'][i],shapes['RadioRetainer'+str(i)])
        if area-actual>1e-6:raise ValueError('Radio retainer hard stop is not seated')
    bottom=max((f for f in shapes['RadioPCB'].Faces if f.BoundBox.ZLength<1e-7 and abs(f.BoundBox.ZMin-z)<1e-7),key=lambda f:f.Area)
    faces=[f for f in shapes['RadioCarrier'].Faces if f.BoundBox.ZLength<1e-7 and abs(f.BoundBox.ZMax-z)<1e-7]
    bearing=sum(bottom.common(f).Area for f in faces)
    if bearing<50:raise ValueError('Radio source PCB lacks its specified50mm2 bearing target')
    tips=[shapes['RadioNut'+str(i)].BoundBox.ZMin-shapes['RadioScrew'+str(i)].BoundBox.ZMin for i in range(3)]
    if any(not .2<=value<=.8 for value in tips):raise ValueError('Radio screw lacks full nut engagement and short tip projection')
    native_check_paths(shapes.get('nut_paths'),rear,3)
    a=math.radians(rotation_deg);c,s=math.cos(a),math.sin(a)
    for pin in data['through_pads']:
        x,y=[a-b for a,b in zip(pin['xy'],DATUM)];probe=Part.makeCylinder(pin['drill']/2,1.6,App.Vector(c*x-s*y,s*x+c*y,z))
        if probe.common(shapes['RadioPCB']).Volume>1e-6:raise ValueError('Radio source pad does not register: '+pin['pad'])
    fixtures={name:shapes[name] for name in PRODUCT_NAMES if name!='RadioPCB'}
    for row in data['footprint_bounds']:
        lo,hi=row['min_mm'],row['max_mm'];body=Part.makeBox(*(b-a for a,b in zip(lo,hi)),6.4,App.Vector(*lo,z+1.6))
        body.translate(App.Vector(-DATUM[0],-DATUM[1],0));body.rotate(App.Vector(),App.Vector(0,0,1),rotation_deg)
        for name,shape in fixtures.items():
            if box_distance(bounds(body),bounds(shape))>1e-6:continue
            if body.common(shape).Volume>1e-6:raise ValueError('Radio fixture intersects nominal source footprint '+row['element']+'/'+name)
    for delta in ((.4,0,0),(-.4,0,0),(0,.4,0),(0,-.4,0),(0,0,.4),(0,0,-.05)):
        board=shapes['RadioPCB'].copy();board.translate(App.Vector(*delta))
        if not any(board.common(shapes[name]).Volume>1e-6 for name in PRINTED_PARTS):raise ValueError('Radio capture fails translation '+str(delta))
    for axis in (App.Vector(1,0,0),App.Vector(0,1,0),App.Vector(0,0,1)):
        for angle in (-2,2):
            board=shapes['RadioPCB'].copy();board.rotate(App.Vector(0,0,z+.8),axis,angle)
            if not any(board.common(shapes[name]).Volume>1e-6 for name in PRINTED_PARTS):
                raise ValueError('Radio capture fails rigid rocking rotation '+str((axis,angle)))
    remaining={name:shapes[name] for name in PRODUCT_NAMES if name=='RadioCarrier' or name.startswith('RadioNut')}
    service=native_service_check(shapes,z,rotation_deg,{**remaining,'RearInterface':rear})
    return {'scope':'source-outline radio carrier component study','physical_products':11,'references':2,'source_through_pads':15,
            'nominal_populated_footprints':9,'pcb_bearing_area_mm2':bearing,'screw_tip_projection_mm':tips,
            'capture_translation_checks':'pass','capture_rocking_rotation_checks_deg':[-2,2],'service':service,'installed_assembly':'not checked','physical_acceptance':'unmeasured'}
