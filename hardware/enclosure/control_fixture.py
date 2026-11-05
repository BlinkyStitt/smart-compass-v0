"""Rear control fixture for the selected module prototype.

Nominal supplier outlines and specified assembly targets are separate from
physical acceptance. Builders supply per-design control locations. They must
check the installed assembly, including these parts and the finger approach.
"""

import math

START_DATUM_Z = 3.65
START_BODY_HEIGHT = 3.45
START_HEIGHT_LIMITS = (6.9, 7.1)
PRINTED_PARTS = frozenset({'StartBackplate','StartBezel','SwitchGuard','StartCompression0','StartCompression1'})
HARDWARE_PARTS = frozenset('StartMount'+kind+str(i)
                         for kind in ('Screw', 'Washer', 'Nut') for i in (0,1)) | frozenset('GuardMount'+kind+str(i) for kind in ('Screw','Washer','Nut') for i in (0,1))
PRODUCT_NAMES = PRINTED_PARTS | HARDWARE_PARTS | {'StartSwitch','PowerDisconnect','PowerDisconnectNut','PowerDisconnectLockwasher'}


def placement(switch_xy, start_xy, rear_thickness=2):
    if (len(switch_xy)!=2 or len(start_xy)!=2
            or any(isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v)
                   for v in (*switch_xy,*start_xy,rear_thickness))
            or rear_thickness != 2):
        raise ValueError('Rear controls require finite XY locations and the specified 2mm clamp lands')
    return {'switch_xy':tuple(switch_xy), 'start_xy':tuple(start_xy),
            'start_tip_z_mm':[START_DATUM_Z-h for h in reversed(START_HEIGHT_LIMITS)],
            'start_body_front_z_mm':START_DATUM_Z-START_BODY_HEIGHT,
            'start_projection_beyond_bezel_mm':START_HEIGHT_LIMITS[0]-START_DATUM_Z-.6,
            'start_screw_finish_length_mm':7.95,
            'switch_guard_inner_width_mm':26,
            'finger_radius_mm':12}


def native_shapes(switch_xy, start_xy, rear_thickness=2, *, switch_rotation_deg=0, guard_mount_offset_mm=6):
    """Return actual products, rear additions/cuts and service probes.

    The guard and START bezel bolt to full-height panel lands. The direct actuator
    has no printed plunger. Cut the retaining screws from M2x10 stock to the
    specified finished length; verify the actual clamp stack before assembly.
    """
    import FreeCAD as App
    import Part
    from hardware_spec import WASHERS, nut_dimensions, hexagon

    settings=placement(switch_xy,start_xy,rear_thickness)
    sx,sy=switch_xy; bx,by=start_xy
    if switch_rotation_deg not in (0,90) or guard_mount_offset_mm not in (6,13.5):
        raise ValueError('Review the rear control orientation and attachment before changing it')
    rear_lands=[]
    def box(w,l,h,x,y,z):return Part.makeBox(w,l,h,App.Vector(x-w/2,y-l/2,z))
    def cylinder(r,h,x,y,z):return Part.makeCylinder(r,h,App.Vector(x,y,z))
    def washer(r,inside,h,x,y,z):return cylinder(r,h,x,y,z).cut(cylinder(inside,h+.2,x,y,z-.1))
    def nut(size,x,y,z):
        flat,h=nut_dimensions(size)
        points=[App.Vector(a+x,b+y,z) for a,b in hexagon(0,0,flat)]
        shape=Part.Face(Part.makePolygon(points+[points[0]])).extrude(App.Vector(0,0,h))
        return shape.cut(cylinder(1.1 if size=='M2' else 3.3,h+.2,x,y,z-.1))
    # A 26mm clear U guard accepts the declared 24mm finger probe. The
    # crossbar carries a recessed O mark. Terminal continuity sets orientation.
    guard=box(3,22,20,sx-14.5,sy,-20).fuse(box(3,22,20,sx+14.5,sy,-20)).fuse(
        box(32,3,3,sx,sy+9.5,-3))
    # The O recess is geometric; it does not depend on paint or illumination.
    guard=guard.cut(washer(2,1.1,.5,sx,sy+9.5,-3.01))
    body=box(11.43,12.70,8.89,sx,sy,2)
    bushing=cylinder(3.175,8.89,sx,sy,2-8.89)
    body=body.fuse(bushing)
    # Six solder-lug nominal envelopes, 4.83mm column and 4.70mm row pitch.
    for dx in (-2.415,2.415):
        for dy in (-4.70,0,4.70):
            body=body.fuse(box(.76,2.03,3.94,sx+dx,sy+dy,10.89))
    pivot=App.Vector(sx,sy,2-8.89)
    lever=cylinder(1.46,10.67,sx,sy,2-8.89-10.67)
    lever.rotate(pivot,App.Vector(1,0,0),25)
    # Combine as a component envelope. Internal pivot detail is not modeled.
    switch=Part.makeCompound([body,lever])
    # C&K700303202 lockwasher and700201201 OPEN hex nut, source nominal
    # imperial dimensions. Do not substitute the blind dress nut709901201.
    lock_h=.018*25.4
    nut_h=.062*25.4
    lockwasher=washer(.402*25.4/2,3.175,lock_h,sx,sy,-lock_h)
    points=[App.Vector(a+sx,b+sy,-lock_h-nut_h) for a,b in hexagon(0,0,.307*25.4)]
    switch_nut=Part.Face(Part.makePolygon(points+[points[0]])).extrude(App.Vector(0,0,nut_h)).cut(
        cylinder(3.175,nut_h+.2,sx,sy,-lock_h-nut_h-.1))
    bezel=box(10,20,.8,bx,by,-.6).cut(cylinder(2.1,1,bx,by,-.7))
    back=box(10,20,1.5,bx,by,START_DATUM_Z)
    start=box(6,6,START_BODY_HEIGHT,bx,by,.2)
    start=start.fuse(cylinder(1.75,START_HEIGHT_LIMITS[1]-START_BODY_HEIGHT,bx,by,START_DATUM_Z-START_HEIGHT_LIMITS[1]))
    for dy in (-7,7):
        back=back.fuse(cylinder(3.8,1.5,bx,by+dy,START_DATUM_Z))
    for dx in (-3.25,3.25):
        for dy in (-2.25,2.25):
            # Keep the full lead envelope, including source outer span7.9.
            start=start.fuse(box(1.4,.8,3,bx+dx,by+dy,START_DATUM_Z))
            back=back.cut(cylinder(.85,1.7,bx+dx,by+dy,START_DATUM_Z-.1))
    products={'StartSwitch':start,'StartBackplate':back,'SwitchGuard':guard,'PowerDisconnect':switch,
              'PowerDisconnectNut':switch_nut,'PowerDisconnectLockwasher':lockwasher}
    cuts=box(8.4,6.4,8,bx,by,-1).fuse(box(10.4,20.4,1.2,bx,by,-1)).fuse(cylinder(3.4,8,sx,sy,-4))
    for i,dy in enumerate((-7,7)):
        x,y=bx,by+dy
        bezel=bezel.fuse(cylinder(2.4,START_DATUM_Z-.2,x,y,.2))
        bezel=bezel.cut(cylinder(1.1,6,x,y,-.7))
        back=back.cut(cylinder(1.1,2,x,y,START_DATUM_Z-.1))
        products['StartMountScrew'+str(i)]=cylinder(1,7.95,x,y,-.6).fuse(cylinder(1.9,2,x,y,-2.6))
        products['StartMountWasher'+str(i)]=washer(WASHERS['M2']['od']/2,WASHERS['M2']['id']/2,.35,x,y,5.15)
        products['StartMountNut'+str(i)]=nut('M2',x,y,5.50)
        products['StartCompression'+str(i)]=washer(3.8,2.6,1.65,x,y,2)
        rear_lands.append(cylinder(4.5,2,x,y,0))
        cuts=cuts.fuse(cylinder(2.6,4,x,y,-1))
    products['StartBackplate']=back
    products['StartBezel']=bezel
    # Two guard screws clamp its three-mm flange and the two-mm panel.
    guard_names={'SwitchGuard','PowerDisconnect','PowerDisconnectNut','PowerDisconnectLockwasher'}
    for i,side in enumerate((-1,1)):
        x,y=sx+side*14.5,sy+guard_mount_offset_mm
        guard=guard.fuse(cylinder(4.5,3,x,y,-3)).cut(cylinder(1.1,4,x,y,-3.5))
        guard=guard.cut(cylinder(2.15,17.1,x,y,-20.1))
        stem=cylinder(1,7.2,x,y,-3).fuse(cylinder(1.9,2,x,y,-5))
        products['GuardMountScrew'+str(i)]=stem
        products['GuardMountWasher'+str(i)]=washer(2.5,1.1,.35,x,y,2)
        products['GuardMountNut'+str(i)]=nut('M2',x,y,2.35)
        guard_names.update('GuardMount'+kind+str(i) for kind in ('Screw','Washer','Nut'))
        land=cylinder(4.5,2,x,y,0)
        hole=cylinder(1.1,8,x,y,-4)
        if switch_rotation_deg:
            for item in (land,hole):item.rotate(App.Vector(sx,sy,0),App.Vector(0,0,1),switch_rotation_deg)
        rear_lands.append(land);cuts=cuts.fuse(hole)
    products['SwitchGuard']=guard
    if switch_rotation_deg:
        for name in guard_names:products[name].rotate(App.Vector(sx,sy,0),App.Vector(0,0,1),switch_rotation_deg)
    probes={'START':cylinder(12,30,bx,by,-33.25)}
    # Continuous full-throw finger approach: convex sweep between both ends.
    throw=10.67*math.sin(math.radians(25))
    probes['OFF_ON']=cylinder(12,30,sx,sy-throw,-45.5).fuse(
        cylinder(12,30,sx,sy+throw,-45.5)).fuse(box(24,2*throw,30,sx,sy,-45.5))
    if switch_rotation_deg:probes['OFF_ON'].rotate(App.Vector(sx,sy,0),App.Vector(0,0,1),switch_rotation_deg)
    settings.update(switch_rotation_deg=switch_rotation_deg,guard_mount_offset_mm=guard_mount_offset_mm)
    bearing=[(name,washer(2.5,1.1,.05,*((sx+side*14.5,sy+guard_mount_offset_mm)),1.95)) for side,name in ((-1,'Guard0'),(1,'Guard1'))]
    if switch_rotation_deg:
        for _,shape in bearing:shape.rotate(App.Vector(sx,sy,0),App.Vector(0,0,1),switch_rotation_deg)
    bearing += [('Start'+str(i),washer(3.8,2.6,.05,bx,by+dy,1.95)) for i,dy in enumerate((-7,7))]
    return {**products,'panel_bearing':bearing,'rear_addition':Part.makeCompound(rear_lands).cut(cuts),'rear_cutout':cuts,
            'finger_probes':probes,'settings':settings}

def native_check(shapes, surroundings):
    from solid_clearance import distance
    actual={name for name in shapes if name.startswith(('Start','GuardMount','PowerDisconnect','SwitchGuard'))}
    if actual!=PRODUCT_NAMES:
        raise ValueError('Rear control component census differs')
    for name in PRODUCT_NAMES:
        shape=shapes[name]
        if not shape.isValid() or shape.Volume<=0 or (name in PRINTED_PARTS and len(shape.Solids)!=1):
            raise ValueError('Invalid rear control product: '+name)
    panels=[shape for name,shape in surroundings if name in ('RearPlate','RearCover')]
    if len(panels)!=1:raise ValueError('Control bearing check requires one actual rear panel')
    for name,bearing in shapes['panel_bearing']:
        if bearing.cut(panels[0]).Volume>1e-6:
            raise ValueError('Missing full-height control bearing: '+name)
    gaps={}
    for name,probe in shapes['finger_probes'].items():
        target='StartSwitch' if name=='START' else 'PowerDisconnect'
        fixed=[shape for part,shape in surroundings if part!=target]
        gap=distance(probe,fixed)
        if gap < .2:
            raise ValueError('Rear control finger approach blocked: '+name+' '+str(gap))
        gaps[name]=gap
    return {'finger_approach_clearance_mm':gaps,'settings':shapes['settings'],
            'proof_boundary':'Specified nominal component/assembly geometry; supplied fit, force and physical switching unmeasured'}
