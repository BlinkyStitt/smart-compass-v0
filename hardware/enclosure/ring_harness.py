"""Formed, insulated input tails and printed routing lands for three LED strips.

Pad positions, lead forming, tape/joint gauges and ties are assembly targets.
They require physical fit inspection. No supplied pad tolerance is claimed.
The original166mm board, stencil, mirror sheets and LED count stay intact.
"""
import math,json
from pathlib import Path
import harness_route

JOINT_ENVELOPE_ALLOWANCE_MM=.005
INNER_PASSAGE_CLEARANCE_MM=.3

# Highest pad fans farthest from the input edge. Its descending lead cannot
# cross a lower pad's fan. Each ring has separate5V,DI,GND lanes.
LANES={
 'RING1':{'5V':(-.8,94.85,-1),'DIN':(0,96.1,1),'GND':(.8,94.85,1)},
 'RING2':{'5V':(-3.8,89.8,0),'DIN':(-2.2,89.8,0),'GND':(-.6,89.8,0)},
 'RING3':{'5V':(7.6,89.8,0),'DIN':(6,89.8,0),'GND':(4.4,89.8,0)},
}

def augment_ports(ports,stock):
    for ring,lanes in LANES.items():
        for pin,(x,y,escape) in lanes.items():
            key=ring+'.'+pin;row=ports[key];start=list(row['terminal_mm']);side=row['axis'][1];source_rad=math.sqrt(start[1]**2+(1.6-side*.55)**2);start[1]=math.sqrt(source_rad**2-(1.6-side*.7)**2);row['terminal_mm']=start;points=[start,[start[0],y,start[2]],[x,y,start[2]],[x,y,start[2]-.8]]
            pieces=harness_route.segments(points,.4)
            # Wrapped formed tail target1.1mm OD. The native guide follows
            # the actual rounded centreline with a separate0.005mm allowance.
            row.update(kind='formed-solder',axis=[0,0,-1],wire_end_mm=points[-1],
                       strip_mm=math.fsum(s['length_mm'] for s in pieces)+1,
                       joint_path_points_mm=points,bare_bend_target_mm=.4,
                       pad_lap_target_mm=1,joint_diameter_target_mm=1.1,
                       physical_acceptance='unmeasured')
            radius=3*stock['branches' if pin in ['5V','GND'] else 'signals']['maximum_od_mm']
            if ring=='RING1':
                # Stay vertical through ties at42/10mm. The first bend is below
                # the lower tie; its lateral exit avoids the side-wire land.
                endx=-14 if escape<0 else 14
                floor=2.55 if pin=='DIN' else 3.2 if pin=='GND' else 3.05
                row['fixed_prefix_mm']=[points[-1],[x,y,floor],[endx,y,floor]]
            else:row['fixed_prefix_mm']=[points[-1],[x,y,3.05],[x,77,3.05]]
            harness_route.segments(row['fixed_prefix_mm'],radius)
    return ports


def joint_shapes(ports):
    import FreeCAD as App,Part
    shapes={}
    for pin,row in ports.items():
        if row['kind']!='formed-solder':continue
        r=row['joint_diameter_target_mm']/2+JOINT_ENVELOPE_ALLOWANCE_MM;points=[]
        for piece in harness_route.segments(row['joint_path_points_mm'],row['bare_bend_target_mm']):
            if piece['kind']=='line':ps=[App.Vector(*p) for p in piece['points']]
            else:
                edge=Part.Arc(*[App.Vector(*p) for p in piece['points']]).toShape()
                ps=edge.discretize(Distance=.08)
            if points and (points[-1]-ps[0]).Length<1e-7:points.extend(ps[1:])
            else:points.extend(ps)
        tubes=[]
        for a,b in zip(points,points[1:]):
            delta=b-a;tubes.append(Part.makeCylinder(r,delta.Length,a,delta))
        tubes += [Part.makeSphere(r,p) for p in points[1:-1]]
        solid=tubes[0].multiFuse(tubes[1:]).removeSplitter()
        # The wrapper terminates at the insulated-wire interface. Sampling
        # spheres may extend beyond it; retain the complete bare conductor
        # path and trim only this wrapper gauge to its declared end plane.
        bb=solid.BoundBox;end_z=row['wire_end_mm'][2]
        solid=solid.common(Part.makeBox(bb.XLength+2,bb.YLength+2,bb.ZMax-end_z+1,App.Vector(bb.XMin-1,bb.YMin-1,end_z))).removeSplitter()
        if not solid.isValid() or len(solid.Solids)!=1:raise ValueError('Invalid formed strip lead gauge '+pin)
        shapes[pin]=solid
    return shapes


def rim_passages():
    record=json.loads(Path(__file__).with_name('rim-loom-passages.json').read_text())
    if record.get('physical_acceptance')!='unmeasured' or len(record['openings'])!=2:raise ValueError('Review both specified rim cable passages')
    for row in record['openings']:
        if len(row['bounds_mm'])!=3 or any(len(pair)!=2 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in pair) or pair[0]>=pair[1] for pair in row['bounds_mm']):raise ValueError('Invalid rim cable passage')
        if row['bounds_mm'][2][1]>=14:raise ValueError('Rim cable passage must stay below the optical strip band')
    return record


def inner_passage_top(ports):
    """Clear the complete formed input joints, including their upper wraps."""
    return max(point[2]+row['joint_diameter_target_mm']/2
               +JOINT_ENVELOPE_ALLOWANCE_MM+INNER_PASSAGE_CLEARANCE_MM
               for pin,row in ports.items() if pin.startswith('RING1.')
               for point in row['joint_path_points_mm'])


def side_window(p):
    """Keep the original outside-strip and diffuser seat free of new supports."""
    inner=(p['side_count']*1000/p['strip_density']+p['ring_seam_gap'])/math.tau-p['strip_thickness']/2
    return inner,p['side_bottom_z'],p['side_bottom_z']+p['side_rows']*p['strip_width']


def shape_products(ports,p):
    """Case-integrated side-wire land and four fixed, accessible lacing loops."""
    import FreeCAD as App,Part
    def box(x0,x1,y0,y1,z0,z1):return Part.makeBox(x1-x0,y1-y0,z1-z0,App.Vector(x0,y0,z0))
    inner_top=max(row['wire_end_mm'][2] for pin,row in ports.items() if pin.startswith('RING1.'))+1.2
    # The upper power joint extends above its jacket endpoint. Its complete
    # wrapped envelope owns the opening height; the tie web stays unchanged.
    passage_top=max(inner_top,inner_passage_top(ports))
    radial,side_bottom,side_top=side_window(p)
    land=Part.makeCylinder(radial,32,App.Vector(0,0,2)).cut(Part.makeCylinder(86.5,32,App.Vector(0,0,2)))
    land=land.common(box(-7,11.3,86,94,2,34))
    # A real north reaction web supports the two inner-ring ties. The old
    # flute ended atR96 and left the outer tie leg floating atR99.5.
    # Preserve the unchanged glass radius93.5 plus0.3mm clearance aboveZ34.
    lower_web=Part.makeCylinder(100,32,App.Vector(0,0,2)).cut(Part.makeCylinder(92.8,32,App.Vector(0,0,2)))
    upper_web=Part.makeCylinder(100,inner_top-34,App.Vector(0,0,34)).cut(Part.makeCylinder(93.8,inner_top-34,App.Vector(0,0,34)))
    web=lower_web.fuse(upper_web).common(box(-9,9,92,101,2,inner_top))
    # Join the upper reaction web through the existing case shoulder above
    # the optical window. This keeps the land connected when its window is cut.
    radius=p['case_diameter']/2
    shoulder=Part.makeCylinder(radius,1.35,App.Vector(0,0,side_top)).cut(
        Part.makeCylinder(radius-9,1.35,App.Vector(0,0,side_top)))
    shoulder=shoulder.common(box(-9,11.3,86,101,side_top,side_top+1.35))
    land=land.fuse(web).fuse(shoulder)
    window=Part.makeCylinder(radius+1,side_top-side_bottom,App.Vector(0,0,side_bottom)).cut(
        Part.makeCylinder(radial,side_top-side_bottom,App.Vector(0,0,side_bottom)))
    window=window.common(box(-10,12.3,85,102,side_bottom,side_top))

    trench=box(-4.8,8.6,88.8,90.6,1.9,34.1)
    exit_window=box(-4.8,8.6,85,90.6,1.9,9)
    land=land.cut(trench.fuse(exit_window)).removeSplitter()
    ties={};cuts=[trench,exit_window,window,box(-2.8,2.8,93.1,97.0,1.9,passage_top),
        # Lower serviceable exit for all three inner-ring fixed prefixes.
        # The outer tie reaction web atY97..99.4 remains continuous.
        box(-16,16,93.1,97.0,1.9,5.2)]
    for row in rim_passages()['openings']:
        (x0,x1),(y0,y1),(z0,z1)=row['bounds_mm'];cuts.append(box(x0,x1,y0,y1,z0,z1))
    # Two side-wire ties enclose the inboard land and the complete loom.
    # The24mm tie captures Side1; the12mm tie captures both side rows.
    for z in [12,24]:
        outer=box(-5.55,9.35,86.0,91.1,z-.85,z+.85)
        inner=box(-5.05,8.85,86.5,90.6,z-1,z+1)
        loop=outer.cut(inner)
        knot=box(-7.0,-3.0,85.0,87.2,z-1.1,z+1.1)
        ties['RingSideLacing'+str(z)]=loop.fuse(knot).removeSplitter()
        # The retained outer carrier wall remains continuous; slots only
        # carry the tie around the inboard land. Physical retention unmeasured.
        cuts.append(box(-5.65,-4.95,85.9,91.2,z-1.05,z+1.05))
        cuts.append(box(8.75,9.45,85.9,91.2,z-1.05,z+1.05))
        cuts.append(box(-5.65,9.45,85.9,86.6,z-1.05,z+1.05))
        cuts.append(box(-7.1,-2.9,84.9,87.3,z-1.2,z+1.2))
        cuts.append(box(-5.65,9.45,90.5,91.2,z-1.05,z+1.05))
    # Inner-ring ties wrap a retained case web. The outer leg lies in a case
    # groove. No tie hole or notch is made in either acrylic mirror or PCB.
    for z in [10,42]:
        outer=box(-3.2,3.2,93.6642,100,z-.85,z+.85)
        inner=box(-2.7,2.7,94.1642,99.5,z-1,z+1)
        loop=outer.cut(inner).common(Part.makeCylinder(100,2,App.Vector(0,0,z-1)))
        knot=box(-6.5,-2.5,95.4,97.6,z-1.1,z+1.1)
        ties['RingInnerLacing'+str(z)]=loop.fuse(knot).removeSplitter()
        cuts += [box(-3.3,3.3,93.55,94.2642,z-1.05,z+1.05),box(-3.3,-2.6,93.55,100.1,z-1.05,z+1.05),box(2.6,3.3,93.55,100.1,z-1.05,z+1.05),box(-3.3,3.3,99.4,100.1,z-1.05,z+1.05),box(-6.6,-2.4,95.3,97.7,z-1.2,z+1.2)]
    for pin,row in ports.items():
        if not pin.startswith('RING'):continue
        # The open inner-ring channel and side trench are source-case cuts.
        # Full occupied wire geometry is checked separately against every part.
        x,y,z=row['wire_end_mm'];radius=(1.3716 if pin.endswith(('.5V','.GND')) else .8636)/2+.25
        cuts.append(Part.makeCylinder(radius,max(0,z-1.9),App.Vector(x,y,1.9)))
    # Formed lead gauges need the same0.25mm allowance in printed material.
    for pin,row in ports.items():
        if row['kind']!='formed-solder':continue
        ps=[App.Vector(*p) for p in row['joint_path_points_mm']]
        for a,b in zip(ps,ps[1:]):delta=b-a;cuts.append(Part.makeCylinder(.95,delta.Length,a,delta))
        cuts.extend(Part.makeSphere(.95,p) for p in ps[1:-1])
    # Intersecting compound children are not a regularized cutting union.
    # Merge the channel/tie/joint tools first; no isolated internal residue
    # may survive inside a declared open passage.
    cut_union=cuts[0].multiFuse(cuts[1:]).removeSplitter()
    if not cut_union.isValid():raise ValueError('Invalid ring cable cutting union')
    land=land.cut(cut_union).removeSplitter()
    if not land.isValid() or len(land.Solids)!=1:
        print('INVALID LAND DIAGNOSTIC '+str({'valid':land.isValid(),'solids':[(s.Volume,str(s.BoundBox),s.isValid()) for s in land.Solids]}),flush=True)
        raise ValueError('Invalid side-wire land')
    for name,shape in ties.items():
        if not shape.isValid() or len(shape.Solids)!=1:raise ValueError('Invalid LED loom tie '+name)
    return {'land':land,'cut_tools':[cut_union],'ties':ties,'physical_acceptance':'unmeasured'}
