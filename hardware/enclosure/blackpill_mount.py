"""Source PCB, raised perimeter carrier and four loose edge retainers."""
import itertools
import json
import math
from pathlib import Path

import electrical_blackpill
import blackpill_sense

HERE=Path(__file__).resolve().parent
L=52.806999206543
W=20.778999328613253
DATUM=(L/2,W/2)
HARDWARE_NAMES=frozenset('BlackPill'+kind+str(i) for kind in ('Screw','Nut') for i in range(4))
PRINTED_PARTS=frozenset({'BlackPillCarrier'}|{'BlackPillRetainer'+str(i) for i in range(4)}|blackpill_sense.PRINTED)
PRODUCT_NAMES=HARDWARE_NAMES|PRINTED_PARTS|{'BlackPillPCB'}|blackpill_sense.PRODUCT_NAMES
REFERENCE_NAMES=frozenset({'BlackPillLoadedReservation','BlackPillUnderboardReservation'}|blackpill_sense.REFERENCE_NAMES)
CHECK_NAMES=PRODUCT_NAMES|REFERENCE_NAMES


def definition():return json.loads((HERE/'electrical-design.json').read_text())


def geometry(design=None,directory=HERE):
    design=definition() if design is None else design;directory=Path(directory)
    pins=electrical_blackpill.terminals(design['parts']['BLACKPILL'],directory)
    if design.get('module_rework',{}).get('BLACKPILL.do_not_install')!=['U3','P1','P2','P3']:
        raise ValueError('Select bare BlackPill PCB pads with U3 and P1/P2/P3 header parts absent')
    bounds=json.loads((directory/electrical_blackpill.SOURCE/'component-bounds.json').read_text())
    if (bounds.get('schema_version')!=1 or bounds.get('revision')!=electrical_blackpill.REVISION
            or bounds.get('source_sha256')!=electrical_blackpill.UPSTREAM['mechanical']
            or bounds.get('source_solid_count')!=131 or bounds.get('pcb_index')!=0
            or len(bounds.get('bodies',[]))!=130 or {row.get('index') for row in bounds['bodies']}!=set(range(1,131))):
        raise ValueError('Complete original BlackPill component bounds are required')
    for row in bounds['bodies']:
        lo,hi=row['min_mm'],row['max_mm']
        if len(lo)!=3 or len(hi)!=3 or not all(math.isfinite(v) for v in lo+hi) or any(a>=b for a,b in zip(lo,hi)):
            raise ValueError('Invalid original BlackPill component bounds')
    return {'pins':pins,'bodies':bounds['bodies'],'datum_mm':list(DATUM),'pcb_size_mm':[L,W],
            'pcb_thickness_target_mm':1.6,'source_pcb_thickness_mm':1.49143974,
            'stations_mm':[[9.5,-4.2],[31,W+4.2],[43.3,-4.2],[43.3,W+4.2]],
            'nut_entry_axes':[[1,0],[-1,0],[1,0],[1,0]],
            'nominal_side_gap_mm':.25,'retainer_slot_mm':1.85,'edge_overlap_mm':.8,
            'physical_dimensions':'unmeasured; source thickness disagreement is not a supplied tolerance range'}


def envelope(pcb_bottom_z=6,rotation_deg=90):
    if pcb_bottom_z not in (6,8) or rotation_deg!=90:raise ValueError('Review BlackPill PCB height and orientation')
    # COTS and wiring reservation only. The carrier/hardware are separate
    # products and require exact installed checks beyond this coarse box.
    return {'size':[W,L,13],'z':pcb_bottom_z-1}


def native_shapes(pcb_bottom_z=6,rotation_deg=90,design=None):
    import FreeCAD as App
    import Part
    from fastener_access import native_tools
    from hardware_spec import hexagon,nut_dimensions
    data=geometry(design);envelope(pcb_bottom_z,rotation_deg);z=pcb_bottom_z
    original=Part.read(str(HERE/electrical_blackpill.SOURCE/'pcb.brep'))
    if not original.isValid() or len(original.Solids)!=1:raise ValueError('Functional source PCB is invalid/detached')
    b=original.BoundBox
    if any(abs(a-b)>1e-6 for a,b in zip((b.XMin,b.YMin,b.ZMin,b.XLength,b.YLength,b.ZLength),(0,0,-1.49143974,L,W,1.49143974))):
        raise ValueError('Functional source PCB bounds differ')
    face=max((f for f in original.Faces if f.BoundBox.ZLength<1e-7 and abs(f.BoundBox.ZMax)<1e-7),key=lambda f:f.Area)
    if len(face.Wires)!=51 or len(face.OuterWire.Edges)!=8:raise ValueError('Source functional PCB outline/holes differ')
    # Use the published 1.6mm nominal assembly target, keeping the different
    # CAD thickness in the source record. Do not infer a supplied tolerance.
    pcb=face.extrude(App.Vector(0,0,1.6));pcb.translate(App.Vector(0,0,z))
    def box(x0,x1,y0,y1,bottom,height):return Part.makeBox(x1-x0,y1-y0,height,App.Vector(x0,y0,bottom))
    def cylinder(r,h,x,y,bottom):return Part.makeCylinder(r,h,App.Vector(x,y,bottom))
    pieces=[]
    for y0,y1 in ((-1.6,-.25),(W+.25,W+1.6)):
        pieces.append(box(-1.5,L+.25,y0,y1,4.1,z+1.85-4.1))
    # The near bridge sits outside the board. The far bridge bears on the
    # source-verified unused end, outside all selected solder-pad X positions.
    pieces.append(box(-2.85,-1.5,-1.6,W+1.6,4.1,1.35))
    pieces.append(box(51,52.35,-1.6,W+1.6,z-1.35,1.35))
    for y0,y1 in ((-1.6,.8),(W-.8,W+1.6)):
        pieces.append(box(0,L,y0,y1,z-1.35,1.35))
    for x0,x1 in ((-1.6,-.25),(L+.25,L+1.6)):
        for y0,y1 in ((-1.6,1.2),(W-1.2,W+1.6)):
            pieces.append(box(x0,x1,y0,y1,z-1.35,2.7))
    products={'BlackPillPCB':pcb};additions=[];cuts=[];mount_probes=[];stop_probes=[];paths=[]
    flat,nh=nut_dimensions('M2');pflat,ph=nut_dimensions('M2',pocket=True)
    for i,(x,y) in enumerate(data['stations_mm']):
        pieces.append(cylinder(3.9,z+1.85-4.1,x,y,4.1))
        additions.append(cylinder(3.9,4.1,x,y,0))
        points=[App.Vector(x+a,y+b,.85) for a,b in hexagon(0,0,pflat)]
        pocket=Part.Face(Part.makePolygon(points+[points[0]])).extrude(App.Vector(0,0,ph))
        entry,path=native_tools(x,y,.85,data['nut_entry_axes'][i],length=9);paths.append(path)
        cuts.extend((pocket,entry,cylinder(1.1,4.3,x,y,-.1)))
        y0,y1=(y-3.9,.8) if y<0 else (W-.8,y+3.9)
        cap=box(x-3.9,x+3.9,y0,y1,z+1.85,1.35).cut(cylinder(1.1,1.55,x,y,z+1.75))
        products['BlackPillRetainer'+str(i)]=cap
        top=z+3.2;length=z+2.75
        products['BlackPillScrew'+str(i)]=cylinder(1,length,x,y,top-length).fuse(cylinder(1.9,2,x,y,top))
        points=[App.Vector(x+a,y+b,.85) for a,b in hexagon(0,0,flat)]
        products['BlackPillNut'+str(i)]=Part.Face(Part.makePolygon(points+[points[0]])).extrude(App.Vector(0,0,nh)).cut(cylinder(1.1,nh+.2,x,y,.75))
        mount_probes.append(cylinder(3.9,.05,x,y,4.05).cut(cylinder(1.1,.1,x,y,4.025)))
        stop_probes.append(cylinder(3.9,.05,x,y,z+1.8).cut(cylinder(1.1,.1,x,y,z+1.775)))
    carrier=pieces[0].multiFuse(pieces[1:]).removeSplitter()
    for x,y in data['stations_mm']:carrier=carrier.cut(cylinder(1.1,z+4,x,y,4))
    products['BlackPillCarrier']=carrier.removeSplitter()
    top=box(0,L,0,W,z+1.6,12-1.6)
    for y0,y1 in ((0,1.2),(W-1.2,W)):top=top.cut(box(-.1,L+.1,y0,y1,z+1.65,12))
    products['BlackPillLoadedReservation']=top
    products['BlackPillUnderboardReservation']=box(0,49.75,1.2,W-1.2,z-1,1)
    blackpill_sense.augment(products,z,W,data['bodies'],design)
    result={**products,'rear_addition':Part.makeCompound(additions),'rear_cutout':Part.makeCompound(cuts),
            'mount_probes':mount_probes,'stop_probes':stop_probes,'nut_paths':paths}
    for value in result.values():
        for shape in value if isinstance(value,list) else [value]:
            shape.translate(App.Vector(-DATUM[0],-DATUM[1],0));shape.rotate(App.Vector(),App.Vector(0,0,1),rotation_deg)
    return result


def _top_contact(probe,shape):
    z=probe.BoundBox.ZMax
    target=max((f for f in probe.Faces if f.BoundBox.ZLength<1e-7 and abs(f.BoundBox.ZMax-z)<1e-7),key=lambda f:f.Area)
    faces=[f for f in shape.Faces if f.BoundBox.ZLength<1e-7 and abs(f.BoundBox.ZMin-z)<1e-7]
    return target.Area,sum(target.common(f).Area for f in faces)


def native_service_check(shapes,pcb_bottom_z,obstacles):
    """Conservative continuous vertical assembly sweep, after caps/screws removal."""
    import FreeCAD as App
    import Part
    from solid_clearance import box_distance
    # These boxes enclose the complete source PCB/loaded space through a
    # continuous 20mm vertical lift. Underboard space excludes the bare rails.
    sweeps=[Part.makeBox(L,W,32,App.Vector(0,0,pcb_bottom_z)),
            Part.makeBox(49.75,W-2.4,33,App.Vector(0,1.2,pcb_bottom_z-1))]
    for sweep in sweeps:
        sweep.translate(App.Vector(-DATUM[0],-DATUM[1],0));sweep.rotate(App.Vector(),App.Vector(0,0,1),90)
        for name,shape in obstacles.items():
            if box_distance(sweep.BoundBox,shape.BoundBox)>1e-6:continue
            if sweep.common(shape).Volume>1e-6:raise ValueError('BlackPill vertical assembly path is blocked: '+name)
    return {'motion':'continuous vertical20mm; all four retainers/screws removed','scope':'component assembly, before wiring and case installation'}


def native_check(shapes,pcb_bottom_z=6,rotation_deg=90):
    import FreeCAD as App
    import Part
    from fastener_access import native_check_paths
    from solid_clearance import box_distance
    data=geometry();envelope(pcb_bottom_z,rotation_deg);z=pcb_bottom_z
    if set(shapes)-{'rear_addition','rear_cutout','mount_probes','stop_probes','nut_paths'}!=CHECK_NAMES:
        raise ValueError('BlackPill fixture census is incomplete')
    sense_result=blackpill_sense.native_check(shapes,z)
    for name in CHECK_NAMES:
        if not shapes[name].isValid() or len(shapes[name].Solids)!=1:raise ValueError('Invalid/detached BlackPill shape: '+name)
    rear=Part.makeBox(80,60,2,App.Vector(-40,-30,0)).fuse(shapes['rear_addition']).cut(shapes['rear_cutout']).removeSplitter()
    if not rear.isValid() or len(rear.Solids)!=1:raise ValueError('BlackPill rear bosses are disconnected')
    all_shapes={**{name:shapes[name] for name in CHECK_NAMES},'RearInterface':rear}
    for a,b in itertools.combinations(sorted(all_shapes),2):
        if box_distance(all_shapes[a].BoundBox,all_shapes[b].BoundBox)>1e-6:continue
        volume=all_shapes[a].common(all_shapes[b]).Volume
        if volume>1e-6:raise ValueError('BlackPill fixture interference '+a+'/'+b+': '+str(volume))
    if len(shapes['mount_probes'])!=4 or len(shapes['stop_probes'])!=4:raise ValueError('Four BlackPill bearing and hard-stop probes are required')
    for i,probe in enumerate(shapes['mount_probes']):
        if probe.cut(rear).Volume>1e-6:raise ValueError('BlackPill rear mounting annulus lacks full bearing')
        area,actual=_top_contact(probe,shapes['BlackPillCarrier'])
        if area-actual>1e-6:raise ValueError('BlackPill carrier lacks full rear bearing')
        area,actual=_top_contact(shapes['stop_probes'][i],shapes['BlackPillRetainer'+str(i)])
        if area-actual>1e-6:raise ValueError('BlackPill retainer hard stop is not seated')
    bottom=max((f for f in shapes['BlackPillPCB'].Faces if f.BoundBox.ZLength<1e-7 and abs(f.BoundBox.ZMin-z)<1e-7),key=lambda f:f.Area)
    faces=[f for f in shapes['BlackPillCarrier'].Faces if f.BoundBox.ZLength<1e-7 and abs(f.BoundBox.ZMax-z)<1e-7]
    bearing=sum(bottom.common(f).Area for f in faces)
    if bearing<80:raise ValueError('BlackPill source PCB lacks its specified80mm2 bearing target')
    tips=[shapes['BlackPillNut'+str(i)].BoundBox.ZMin-shapes['BlackPillScrew'+str(i)].BoundBox.ZMin for i in range(4)]
    if any(not .2<=value<=.8 for value in tips):raise ValueError('BlackPill screw lacks full nut engagement and short tip projection')
    native_check_paths(shapes.get('nut_paths'),rear,4)
    angle=math.radians(rotation_deg);c,s=math.cos(angle),math.sin(angle)
    for pin in data['pins'].values():
        x,y=[a-b for a,b in zip(pin['board_xy_mm'],DATUM)]
        probe=Part.makeCylinder(pin['drill_mm']/2,1.6,App.Vector(c*x-s*y,s*x+c*y,z))
        if probe.common(shapes['BlackPillPCB']).Volume>1e-6:raise ValueError('BlackPill source pad does not register: '+pin['pad'])
    fixtures={name:shapes[name] for name in PRODUCT_NAMES if name!='BlackPillPCB'}
    # Conservative nominal source boxes, not material/mass solids. No source
    # body is omitted because it is difficult to fit, including U3's space.
    for row in data['bodies']:
        lo,hi=row['min_mm'],row['max_mm'];body=Part.makeBox(*(b-a for a,b in zip(lo,hi)),App.Vector(*lo))
        body.translate(App.Vector(-DATUM[0],-DATUM[1],z+1.6));body.rotate(App.Vector(),App.Vector(0,0,1),rotation_deg)
        for name,shape in fixtures.items():
            if box_distance(body.BoundBox,shape.BoundBox)>1e-6:continue
            if body.common(shape).Volume>1e-6:raise ValueError('BlackPill fixture intersects nominal source body '+name+'/'+str(row['index']))
    original=Part.read(str(HERE/electrical_blackpill.SOURCE/'pcb.brep'))
    face=max((f for f in original.Faces if f.BoundBox.ZLength<1e-7 and abs(f.BoundBox.ZMax)<1e-7),key=lambda f:f.Area)
    captures=[]
    for thickness in (1.6,1.49143974):
        board=face.extrude(App.Vector(0,0,thickness));board.translate(App.Vector(-DATUM[0],-DATUM[1],z));board.rotate(App.Vector(),App.Vector(0,0,1),rotation_deg)
        for delta in ((.4,0,0),(-.4,0,0),(0,.4,0),(0,-.4,0),(0,0,.4),(0,0,-.05)):
            moved=board.copy();moved.translate(App.Vector(*delta))
            if not any(moved.common(shapes[name]).Volume>1e-6 for name in PRINTED_PARTS):
                raise ValueError('BlackPill capture fails source thickness case '+str((thickness,delta)))
        captures.append({'source_thickness_case_mm':thickness,'capture_translation_checks':'pass','supplied_tolerance_claim':False})
    remaining={name:shapes[name] for name in PRODUCT_NAMES if name=='BlackPillCarrier' or name.startswith('BlackPillNut')}
    service=native_service_check(shapes,z,{**remaining,'RearInterface':rear})
    return {'scope':'source-based BlackPill carrier component study','physical_products':len(PRODUCT_NAMES),'references':len(REFERENCE_NAMES),'sense_loom':sense_result,
            'nominal_source_component_boxes':130,'source_body_fixture_clearance':'pass','pcb_bearing_area_mm2':bearing,
            'capture_cases':captures,'screw_tip_projection_mm':tips,'stock_screws':{'0/1':'M2x12; finish '+str(z+2.75)+'mm','2/3':'M2x16; finish '+str(z+6.4)+'mm'},
            'service':service,'installed_assembly':'not checked','physical_acceptance':'unmeasured'}
