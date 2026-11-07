"""Six fixed discharge resistors above the source-selected BlackPill loom.

The body limits come from the MRS16 drawing. Joint, lacing and bridge spaces
are assembly targets, not measured parts or qualified insulation/retention.
"""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
STATIONS={'R_A':(14,2.5),'R_B':(32,2.5),'R_OUT':(14,9),
          'R_OFF':(32,9),'R_BOOST':(14,15.5),'R_LOAD':(32,15.5)}
PASSIVES=frozenset('BlackPillDrain'+name for name in STATIONS)
LACING=frozenset('BlackPillDrainLacing'+str(i) for i in range(12))
PRINTED=frozenset({'BlackPillDrainBridge'})
PRODUCT_NAMES=PASSIVES|LACING|PRINTED
REFERENCE_NAMES=frozenset(name+'Assembly' for name in PASSIVES)


def geometry(design=None):
    design=json.loads((HERE/'electrical-design.json').read_text()) if design is None else design
    for name in STATIONS:
        row=design['parts'][name]
        value='1003' if name=='R_OFF' else '1001'
        expected=f'Vishay MRS16000C{value}FCT00, '+('100 kohm' if name=='R_OFF' else '1 kohm')+' 1% 0.4 W, axial'
        if (row['part']!=expected or row.get('body_max_mm')!=[3.6,1.6]
                or row.get('loaded_envelope_mm')!=[12,3.5,3.5]
                or row.get('lead_diameter_nominal_mm')!=.5
                or row.get('lead_length_min_mm')!=29 or row.get('mounting_pitch_min_mm')!=5
                or row.get('source_sha256')!='645bb41aaa34f2a72fc19fc71d02ddb14ed400ae97634684ad1745189505f47e'):
            raise ValueError('Retain selected discharge resistor and MRS16 source facts: '+name)
    # Two opposed axial exits each retain2mm of jacket insulation. Keep
    # positive space between those fabrication targets; no supplied tolerance
    # or physical insulation/retention bound is inferred from this spacing.
    gaps={}
    for lower,upper in [('R_A','R_B'),('R_OUT','R_OFF'),('R_BOOST','R_LOAD')]:
        x0,y0=STATIONS[lower];x1,y1=STATIONS[upper]
        if y0!=y1 or x1-(x0+12)<=4:raise ValueError('Opposed drain exits cannot fit both2mm jacket cuffs')
        gaps[lower+'/'+upper]=x1-(x0+12)
    return {'opposed_exit_gaps_mm':gaps,'jacket_overlap_each_mm':2,
            'stations_source_xy_mm':{name:list(xy) for name,xy in STATIONS.items()},
            'axis_z_above_pcb_bottom_mm':16,'floor_z_above_pcb_bottom_mm':[12.8,14.15],
            'joint_space_mm':[12,3.5,3.5],'lacing_blank_mm':[70]*12,
            'mount':'Two existing BlackPill far stations; stockM2x25, finish z+13.7mm',
            'physical_acceptance':'unmeasured'}


def source_ports():
    """Specified joint exits in the BlackPill source XY; Z above PCB bottom."""
    return {name+'.'+pin:[x+offset,y,16]
            for name,(x,y) in STATIONS.items() for pin,offset in (('1',0),('2',12))}


def augment(products,added,z,width,design=None):
    """Add the second removable bridge; keep RC parts and their support intact."""
    import FreeCAD as App
    import Part
    geometry(design)
    def box(x0,x1,y0,y1,z0,z1):return Part.makeBox(x1-x0,y1-y0,z1-z0,App.Vector(x0,y0,z0))
    def cylinder(r,h,x,y,z0,direction=App.Vector(0,0,1)):
        return Part.makeCylinder(r,h,App.Vector(x,y,z0),direction)
    bridge=box(13,43.3,-2,width+1.2,z+12.8,z+14.15).fuse(
        box(39.4,47.2,-8.1,width+8.1,z+12.8,z+14.15))
    for i,y in ((2,-4.2),(3,width+4.2)):
        bridge=bridge.fuse(cylinder(3.1,7.3,43.3,y,z+6.85))
        bridge=bridge.cut(cylinder(1.1,7.5,43.3,y,z+6.75))
        top=z+14.15;length=z+13.7
        products['BlackPillScrew'+str(i)]=cylinder(1,length,43.3,y,top-length).fuse(
            cylinder(1.9,2,43.3,y,top))
    for index,(name,(x,y)) in enumerate(STATIONS.items()):
        key='BlackPillDrain'+name
        body=cylinder(.8,3.6,x+4.2,y,z+16,App.Vector(1,0,0)).fuse(
            cylinder(.25,12,x,y,z+16,App.Vector(1,0,0))).removeSplitter()
        target=box(x,x+12,y-1.75,y+1.75,z+14.25,z+17.75)
        added[key]=body;added[key+'Assembly']=target.cut(body).removeSplitter()
        for j,t in enumerate((x+3,x+9)):
            low,high=y-1.75,y+1.75
            loop=box(t-.85,t+.85,low-.5,high+.5,z+12.3,z+18.25).cut(
                box(t-1,t+1,low,high,z+12.8,z+17.75))
            knot=box(t-2,t+2,low-2.3,low-.1,z+15.35,z+17.35)
            added['BlackPillDrainLacing'+str(2*index+j)]=loop.fuse(knot).removeSplitter()
            for a,b in ((low-.65,low+.15),(high-.15,high+.65)):
                bridge=bridge.cut(box(t-1.05,t+1.05,a,b,z+12.7,z+14.25))
    added['BlackPillDrainBridge']=bridge.removeSplitter()


def native_check(shapes,z):
    # Both columns must sit on the actual first bridge, with complete annular
    # bearing. A touching bounding box is insufficient.
    import math
    bridge=shapes['BlackPillDrainBridge'];base=shapes['BlackPillSenseBridge']
    faces=[f for f in bridge.Faces if f.BoundBox.ZLength<1e-7 and abs(f.BoundBox.ZMin-bridge.BoundBox.ZMin)<1e-7]
    bearing=sum(f.common(base).Area for f in faces)
    expected=2*math.pi*(3.1**2-1.1**2)
    if bearing<expected-1e-6:raise ValueError('Discharge bridge lacks full bearing on the sense bridge')
    for i in (2,3):
        screw=shapes['BlackPillScrew'+str(i)]
        if abs(screw.BoundBox.ZMax-(bridge.BoundBox.ZMax+2))>1e-7:
            raise ValueError('Discharge bridge screw head is not seated')
    return {**geometry(),'physical_products':len(PRODUCT_NAMES),'assembly_space_references':len(REFERENCE_NAMES),
            'complete_column_bearing_mm2':bearing,'finished_screw_length_mm':z+13.7}
