"""One real latch PCB, two wire clamps and a four-screw insulated carrier.

This factory defines nominal geometry and assembly targets. It does not prove
supplied fit, soldering, retention, electrical behavior or temperatures.
"""
import itertools
import json
import math
from pathlib import Path

from electrical_latch import terminals,SOURCE

HERE=Path(__file__).resolve().parent
PRINTED_PARTS=frozenset({'LatchCarrier'}|{'LatchClamp'+str(i) for i in range(4)})
HARDWARE_PARTS=frozenset('LatchMount'+kind+str(i)
 for kind in ('Screw','LowerWasher','UpperWasher','Nut') for i in range(4))
PRODUCT_NAMES=PRINTED_PARTS|HARDWARE_PARTS|{'LatchModule','LatchTerminalVIN','LatchTerminalVOUT'}


def definition():return json.loads((HERE/'electrical-design.json').read_text())['parts']['LATCH']


def placement(part):
    terminals(part)
    m=part['mount']
    for name in ('pcb_bottom_z_mm','floor_bottom_z_mm','floor_thickness_mm','post_x_mm',
                 'post_radius_mm','lip_inner_x_mm','lip_y_length_mm','clamp_thickness_mm','finished_screw_length_mm'):
        value=m[name]
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<=0:
            raise ValueError('Finite positive latch mounting target required: '+name)
    if (m['floor_size_mm']!=[32,22.75] or m.get('floor_centre_xy_mm')!=[0,-.625]) or m['post_y_mm']!=[3.5,-7.8] or m['floor_bottom_z_mm']!=2:
        raise ValueError('Review the selected case clamp stations and full2mm bearing datum')
    if m['floor_thickness_mm']<1.35 or m['post_radius_mm']<2.75 or m['clamp_thickness_mm']<1.2:
        raise ValueError('Do not thin the selected carrier, full washer bearing or clamp')
    if m['pcb_bottom_z_mm']-8.5-m['floor_bottom_z_mm']-m['floor_thickness_mm']<.25:
        raise ValueError('The source terminal bodies need positive floor clearance')
    # Board edge tolerance is+/-0.3mm. These are defined bearing targets,
    # not a strength or manufactured-retention result.
    minimum_area=(15.24/2-.3-m['lip_inner_x_mm'])*m['lip_y_length_mm']
    if minimum_area<.5 or m['lip_inner_x_mm']-(6.35+.5/2+.1)<.25:
        raise ValueError('Clamp loses source-edge bearing or selected pin clearance')
    from hardware_spec import WASHERS,nut_dimensions
    washer=WASHERS['M2']['thickness'];_,nut_height=nut_dimensions('M2')
    nut_top=m['pcb_bottom_z_mm']+1.016+m['clamp_thickness_mm']+washer+nut_height
    tip=m['finished_screw_length_mm']-washer
    if not .2<=tip-nut_top<=.8:
        raise ValueError('Latch screw must engage the full nut and leave0.2..0.8mm tip projection')
    return {'stations':[(side*m['post_x_mm'],y) for side in (-1,1) for y in m['post_y_mm']],
            'minimum_specified_lip_bearing_mm2':minimum_area,
            'pcb_top_z_mm':m['pcb_bottom_z_mm']+1.016,
            'screw_tip_projection_mm':tip-nut_top,
            'terminal_floor_clearance_mm':m['pcb_bottom_z_mm']-8.5-m['floor_bottom_z_mm']-m['floor_thickness_mm']}


def envelope(part=None):
    part=definition() if part is None else part
    target=placement(part);m=part['mount']
    from hardware_spec import WASHERS,nut_dimensions
    washer=WASHERS['M2']['thickness'];_,nut=nut_dimensions('M2')
    low=-washer-2
    high=max(m['pcb_bottom_z_mm']+2.966,m['pcb_bottom_z_mm']+3.8,
             target['pcb_top_z_mm']+m['clamp_thickness_mm']+washer+nut,
             m['finished_screw_length_mm']-washer)
    return {'size':[2*abs(m['floor_centre_xy_mm'][0])+m['floor_size_mm'][0],2*abs(m['floor_centre_xy_mm'][1])+m['floor_size_mm'][1],high-low],'z':low}


def native_shapes(part=None):
    import FreeCAD as App
    import Part
    from hardware_spec import WASHERS,nut_dimensions,hexagon
    part=definition() if part is None else part
    target=placement(part);m=part['mount'];z=m['pcb_bottom_z_mm'];top=target['pcb_top_z_mm']
    def box(w,l,h,x,y,bottom):return Part.makeBox(w,l,h,App.Vector(x-w/2,y-l/2,bottom))
    def cylinder(r,h,x,y,bottom):return Part.makeCylinder(r,h,App.Vector(x,y,bottom))
    pcb=Part.read(str(HERE/SOURCE/'pololu-2808.step'))
    if not pcb.isValid() or len(pcb.Solids)!=1:raise ValueError('Manufacturer latch STEP must be one valid solid')
    pcb.translate(App.Vector(-7.62,-8.89,z))
    products={'LatchModule':pcb}
    # Conservative full body boxes. Use the source3.8mm pin maximum.
    # The underside strips leave the actual populated component face clear.
    for side,name in ((-1,'VIN'),(1,'VOUT')):
        body=box(6.2,10.62,8.5,side*6.35,3.81,z-8.5)
        for y in (7.62,5.08,2.54,0):body=body.fuse(box(.5,.8,3.8,side*6.35,y,z))
        products['LatchTerminal'+name]=body.removeSplitter()
    floor=m['floor_bottom_z_mm'];thickness=m['floor_thickness_mm']
    carrier=box(*m['floor_size_mm'],thickness,*m['floor_centre_xy_mm'],floor).fuse(box(4,16.8,z-floor-thickness,0,0,floor+thickness))
    rear_lands=[];rear_cuts=[];bearing=[]
    washer=WASHERS['M2'];flats,nh=nut_dimensions('M2')
    def ring(x,y,bottom):return cylinder(washer['od']/2,washer['thickness'],x,y,bottom).cut(cylinder(washer['id']/2,washer['thickness']+.2,x,y,bottom-.1))
    for i,(x,y) in enumerate(target['stations']):
        post=cylinder(m['post_radius_mm'],top-floor-thickness,x,y,floor+thickness)
        carrier=carrier.fuse(post)
        side=-1 if x<0 else 1
        inner=m['lip_inner_x_mm'];arm_length=abs(x)-inner
        arm=box(arm_length,m['lip_y_length_mm'],m['clamp_thickness_mm'],side*(inner+arm_length/2),y,top)
        clamp=cylinder(m['post_radius_mm'],m['clamp_thickness_mm'],x,y,top).fuse(arm)
        bore=cylinder(1.1,top+3,x,y,floor-.1)
        products['LatchClamp'+str(i)]=clamp.cut(bore).removeSplitter()
        carrier=carrier.cut(bore)
        low=-washer['thickness'];upper=top+m['clamp_thickness_mm'];nz=upper+washer['thickness']
        products['LatchMountLowerWasher'+str(i)]=ring(x,y,low)
        products['LatchMountUpperWasher'+str(i)]=ring(x,y,upper)
        products['LatchMountScrew'+str(i)]=cylinder(1,m['finished_screw_length_mm'],x,y,low).fuse(cylinder(1.9,2,x,y,low-2))
        points=[App.Vector(x+a,y+b,nz) for a,b in hexagon(0,0,flats)]
        products['LatchMountNut'+str(i)]=Part.Face(Part.makePolygon(points+[points[0]])).extrude(App.Vector(0,0,nh)).cut(cylinder(1.1,nh+.2,x,y,nz-.1))
        rear_lands.append(cylinder(3.5,2,x,y,0))
        rear_cuts.append(cylinder(1.1,2.2,x,y,-.1))
        bearing.append(cylinder(2.5,.05,x,y,1.95).cut(cylinder(1.1,.1,x,y,1.925)))
    products['LatchCarrier']=carrier.removeSplitter()
    return {**products,'rear_addition':Part.makeCompound(rear_lands),'rear_cutout':Part.makeCompound(rear_cuts),
            'rear_bearing':bearing,'targets':target}


def native_check(shapes,part=None):
    import FreeCAD as App
    import Part
    from solid_clearance import bounds,box_distance
    part=definition() if part is None else part
    if set(shapes)-{'rear_addition','rear_cutout','rear_bearing','targets'}!=PRODUCT_NAMES:
        raise ValueError('Latch component census is incomplete')
    for name in PRODUCT_NAMES:
        shape=shapes[name]
        if not shape.isValid() or len(shape.Solids)!=1:raise ValueError('Invalid or detached latch part: '+name)
    for a,b in itertools.combinations(sorted(PRODUCT_NAMES),2):
        if box_distance(bounds(shapes[a]),bounds(shapes[b]))>1e-6:continue
        volume=shapes[a].common(shapes[b]).Volume
        if volume>1e-6:raise ValueError('Latch interference '+a+'/'+b+': '+str(volume))
    # Move the source PCB by0.05mm for an independent contact-area probe.
    # Closed intersections above must remain zero; this is deliberate probing.
    raised=shapes['LatchModule'].copy();raised.translate(App.Vector(0,0,.05))
    bearings={name:raised.common(shapes[name]).Volume/.05 for name in sorted(PRINTED_PARTS-{'LatchCarrier'})}
    if any(area<.5 for area in bearings.values()):raise ValueError('Latch clamps do not bear on the actual source PCB: '+str(bearings))
    # Retain the nominal PCB itself on the central underside spine.
    lowered=shapes['LatchModule'].copy();lowered.translate(App.Vector(0,0,-.05))
    support=lowered.common(shapes['LatchCarrier']).Volume/.05
    if support<50:raise ValueError('Latch PCB floats above its carrier')
    rear=Part.makeBox(40,32,2,App.Vector(-20,-16,0)).cut(shapes['rear_cutout'])
    for probe in shapes['rear_bearing']:
        if probe.cut(rear).Volume>1e-6:raise ValueError('Latch rear washer/post has incomplete bearing')
    return {'scope':'source-based latch component mount only','product_count':len(PRODUCT_NAMES),
            'clamp_nominal_bearing_mm2':bearings,'pcb_underside_bearing_mm2':support,
            'targets':placement(part),'installed_assembly':'not checked','physical_acceptance':'unmeasured'}
