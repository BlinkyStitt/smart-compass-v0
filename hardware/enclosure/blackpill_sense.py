"""Fixed battery-sense loom on the selected BlackPill perimeter carrier.

Source body limits and specified finished-assembly spaces are separate inputs.
No dimensions, insulation, knot retention or temperature have been measured.
"""
import json
import math
import blackpill_drains
from pathlib import Path

HERE=Path(__file__).resolve().parent
PASSIVES=frozenset({'BlackPillSenseTop','BlackPillSenseBottom','BlackPillSenseCapacitor'})
LACING=frozenset('BlackPillSenseLacing'+str(i) for i in range(7))
PRINTED=frozenset({'BlackPillSenseBridge'})|blackpill_drains.PRINTED
PRODUCT_NAMES=PASSIVES|LACING|PRINTED|blackpill_drains.PRODUCT_NAMES
REFERENCE_NAMES=frozenset(name+'Assembly' for name in PASSIVES)|blackpill_drains.REFERENCE_NAMES
CHECK_NAMES=PRODUCT_NAMES|REFERENCE_NAMES


def geometry(design=None):
    design=json.loads((HERE/'electrical-design.json').read_text()) if design is None else design
    parts=design['parts'];cap=parts['C_SENSE']
    if (cap['part']!='KEMET C315C104K5R5TA, 100 nF 50 V +/-10%, X7R radial'
            or cap.get('body_max_mm')!=[3.81,2.54,3.14]
            or cap.get('loaded_envelope_mm')!=[12,8.5,3.5]
            or cap.get('lead_pitch_mm')!=[1.76,3.32]
            or cap.get('lead_diameter_mm')!=[.485,.61] or cap.get('lead_length_min_mm')!=7
            or cap.get('source_sha256')!='3532a937a01c65f20f1a722a547962c9ceaf2ba4ffef1d2284be5bf380a516a5'):
        raise ValueError('Retain the complete KEMET source body, pitch and lead limits')
    for name in ('R_SENSE_TOP','R_SENSE_BOTTOM'):
        part=parts[name]
        if (part['part']!='Vishay MRS16000C1003FCT00, 100 kohm 1% 0.4 W, axial'
                or part.get('body_max_mm')!=[3.6,1.6] or part.get('loaded_envelope_mm')!=[12,3.5,3.5]
                or part.get('lead_diameter_nominal_mm')!=.5 or part.get('lead_length_min_mm')!=29
                or part.get('mounting_pitch_min_mm')!=5
                or part.get('source_sha256')!='645bb41aaa34f2a72fc19fc71d02ddb14ed400ae97634684ad1745189505f47e'):
            raise ValueError('Retain the Vishay source facts and finished resistor assembly target')
    # At the smallest supplied pitch, each formed lead uses less than the
    # published7mm stock minimum. Joint length is an assembly target.
    required=math.hypot(3,(5-min(cap['lead_pitch_mm']))/2)+3
    if required>cap['lead_length_min_mm']:raise ValueError('Capacitor formed lead exceeds its minimum stock length')
    return {'parts':['R_SENSE_TOP','R_SENSE_BOTTOM','C_SENSE'],
            'insulation':'TE Raychem RNF-100-1/8-0-SP; recover before PETG installation',
            'lacing':'Alpha Wire LC134 BK088; seven separate square-knot spot ties',
            'lacing_stock_max_mm':[.066*25.4,.017*25.4],
            'lacing_finished_space_mm':[1.7,.5],
            'lacing_cut_targets_mm':[70]*7,'finished_joint_max_od_mm':3.5,
            'cap_lead_stock_required_mm':required,'cap_finished_pitch_mm':5,
            'measurement_status':'unmeasured; all formed/joint/knot spaces are manufacturing targets'}


def augment(products,z,width,body_rows,design=None):
    """Add a removable bridge and a fixed insulated RC loom, in source XY."""
    import FreeCAD as App
    import Part
    geometry(design)
    def box(x0,x1,y0,y1,z0,z1):return Part.makeBox(x1-x0,y1-y0,z1-z0,App.Vector(x0,y0,z0))
    def cylinder(r,h,x,y,z0,direction=App.Vector(0,0,1)):
        return Part.makeCylinder(r,h,App.Vector(x,y,z0),direction)
    def lead(points,r):
        result=[]
        for a,b in zip(points,points[1:]):
            a,b=App.Vector(*a),App.Vector(*b);v=b-a;result.append(Part.makeCylinder(r,v.Length,a,v))
        result += [Part.makeSphere(r,App.Vector(*p)) for p in points[1:-1]]
        return result[0].multiFuse(result[1:]).removeSplitter() if len(result)>1 else result[0]
    bridge=box(13,43.3,1.3,width-1.3,z+5.5,z+6.85).fuse(box(39.4,47.2,-8.1,width+8.1,z+5.5,z+6.85))
    for i,y in ((2,-4.2),(3,width+4.2)):
        bridge=bridge.fuse(cylinder(3.1,3.65,43.3,y,z+3.2))
        top=z+6.85;length=z+6.4
        products['BlackPillScrew'+str(i)]=cylinder(1,length,43.3,y,top-length).fuse(cylinder(1.9,2,43.3,y,top))
    for y in (-4.2,width+4.2):bridge=bridge.cut(cylinder(1.1,4,43.3,y,z+3.1))
    added={};targets={}
    for name,y in (('BlackPillSenseTop',5.5),('BlackPillSenseBottom',10.5)):
        body=cylinder(.8,3.6,18.2,y,z+8.7,App.Vector(1,0,0))
        body=body.fuse(cylinder(.25,12,14,y,z+8.7,App.Vector(1,0,0))).removeSplitter()
        added[name]=body;targets[name]=box(14,26,y-1.75,y+1.75,z+6.95,z+10.45)
    name='BlackPillSenseCapacitor'
    body=box(28,31.14,9-3.81/2,9+3.81/2,z+8.7-1.27,z+8.7+1.27)
    for sign in (-1,1):
        body=body.fuse(lead([(31.14,9+sign*1.27,z+8.7),(34.14,9+sign*2.5,z+8.7),(37.14,9+sign*2.5,z+8.7)],.305))
    added[name]=body.removeSplitter()
    targets[name]=box(28,31.14,9-3.81/2,9+3.81/2,z+8.7-1.27,z+8.7+1.27).fuse(
        box(31.14,34.14,6.195,11.805,z+8.395,z+9.005))
    for y in (6.5,11.5):targets[name]=targets[name].fuse(box(34.14,40,y-1.75,y+1.75,z+6.95,z+10.45))
    for key,target in targets.items():
        if added[key].cut(target).Volume>1e-6:raise ValueError('Passive assembly space misses its nominal source body/lead: '+key)
        added[key+'Assembly']=target.cut(added[key]).removeSplitter()
    # Rectangular loop spaces include the complete stock section, with a
    # separate, attached finished knot/tail space. They do not claim a knot
    # shape, tension or installed retention measurement.
    stations=[(17,3.75,7.25,z+10.45,-1),(23,3.75,7.25,z+10.45,-1),
              (17,8.75,12.25,z+10.45,1),(23,8.75,12.25,z+10.45,1),
              (29,9-3.81/2,9+3.81/2,z+9.97,-1),
              (36.5,4.75,8.25,z+10.45,-1),(36.5,9.75,13.25,z+10.45,1)]
    for i,(x,low,high,top,side) in enumerate(stations):
        outer=box(x-.85,x+.85,low-.5,high+.5,z+5,top+.5)
        inner=box(x-1,x+1,low,high,z+5.5,top)
        loop=outer.cut(inner)
        knot=(box(x-2,x+2,low-2.3,low-.1,z+8.05,z+10.05) if side<0 else
              box(x-2,x+2,high+.1,high+2.3,z+8.05,z+10.05))
        added['BlackPillSenseLacing'+str(i)]=loop.fuse(knot).removeSplitter()
        for a,b in ((low-.65,low+.15),(high-.15,high+.65)):
            bridge=bridge.cut(box(x-1.05,x+1.05,a,b,z+5.4,z+6.95))
    added['BlackPillSenseBridge']=bridge.removeSplitter()
    blackpill_drains.augment(products,added,z,width,design)
    old=products['BlackPillLoadedReservation'].copy()
    for key,shape in added.items():
        if not shape.isValid() or len(shape.Solids)!=1:raise ValueError('Invalid/disconnected sense loom part: '+key)
    remove=Part.makeCompound(list(added.values()))
    remaining=old.cut(remove).removeSplitter()
    if not remaining.isValid() or len(remaining.Solids)!=1:raise ValueError('Remaining BlackPill module/wiring reservation is disconnected')
    # Cutting only the new assembly does not authorize deleting any original
    # source component space. Preserve every source body's previous coverage.
    for row in body_rows:
        lo,hi=row['min_mm'],row['max_mm']
        body=Part.makeBox(*(b-a for a,b in zip(lo,hi)),App.Vector(lo[0],lo[1],z+1.6+lo[2]))
        if body.common(old).cut(remaining).Volume>1e-6:raise ValueError('Sense loom removes original source component space: '+str(row['index']))
        for key,shape in added.items():
            if body.common(shape).Volume>1e-6:raise ValueError('Sense loom intersects original source component: '+key+'/'+str(row['index']))
    products['BlackPillLoadedReservation']=remaining
    products.update(added)


def native_check(shapes,z):
    import FreeCAD as App
    import Part
    # The feet must sit on the two existing retainer hard stops. Use exact
    # common faces after the shared90degree source transform.
    for i in (2,3):
        cap=shapes['BlackPillRetainer'+str(i)];bridge=shapes['BlackPillSenseBridge']
        faces=[f for f in cap.Faces if f.BoundBox.ZLength<1e-7 and abs(f.BoundBox.ZMin-cap.BoundBox.ZMax)<1e-7]
        contact=sum(f.common(bridge).Area for f in faces)
        expected=math.pi*(3.1**2-1.1**2)
        if contact<expected-1e-6:raise ValueError('Sense bridge lacks full bearing on existing retainer '+str(i))
    return {**geometry(),'physical_products':len(PRODUCT_NAMES),'assembly_space_references':len(REFERENCE_NAMES),
            'discharge_loom':blackpill_drains.native_check(shapes,z),
            'source_component_spaces_preserved':130,
            'bridge_screws':'Only2/3: stockM2x25; finish '+str(z+13.7)+'mm;0/1 unchanged',
            'physical_acceptance':'unmeasured; no assembled insulation, retention or thermal qualification'}
