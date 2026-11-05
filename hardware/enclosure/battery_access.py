"""Shared one-cell access geometry and specified contact/removal constraints.

Native factories import FreeCAD only when called. Assembly settings below are
manufacturing requirements, not measurements of an owned cell or printed part.
"""

import itertools
import json
import math
from pathlib import Path


PRINTED_PARTS = frozenset({'BatteryCradle','BatteryDoor','BatteryKeeper',
                            'BatteryHingeSpacer0','BatteryHingeSpacer1'} | {
    'BatteryContact'+end+part for end in ('P','N')
    for part in ('Front','Back','Spacer0','Spacer1')})
SHIM_PARTS = frozenset('BatteryContact'+end+'Shim'+str(i) for end in ('P','N') for i in (0,1))
MOUNT_PARTS = frozenset('BatteryCaseMount'+part+str(i) for part in ('Screw','Washer','Nut') for i in range(4))
METAL_PARTS = MOUNT_PARTS | frozenset({'BatteryHingePin','BatteryHingeNut','BatteryHingeWasher0','BatteryHingeWasher1',
                         'BatteryKeeperScrew','BatteryKeeperNut0','BatteryKeeperNut1'} | {
    'BatteryContact'+end+part for end in ('P','N')
    for part in ('','Screw0','Screw1','Nut0','Nut1','Washer0','Washer1')})
PART_NAMES = PRINTED_PARTS | SHIM_PARTS | METAL_PARTS | {'BatteryCell','BatteryPullRibbon'}


def definition():
    spec=json.loads(Path(__file__).with_name('battery-compartment.json').read_text())
    if (type(spec['cell'].get('quantity')) is not int
            or spec['cell'] != {'quantity':1,'source_record':'site/electrical-inputs.json#cell'}):
        raise ValueError('The electrical input record owns the selected cell; reject a second cell definition')
    model=json.loads((Path(__file__).resolve().parents[2]/'site/electrical-inputs.json').read_text())['cell']
    spec['cell']={**model,'quantity':1,'part':model['name'].removeprefix('One ')}
    return spec


def contact_travel(spec):
    cell, contact = (spec[k] for k in ('cell', 'contact'))
    # The springs need not share compression equally. Enumerate the total
    # interference. The fixed insulating stop sets the extraction endpoint;
    # its specified compression must leave the positive end clear.
    total = [length-gap for length, gap in itertools.product(
        cell['length_mm'], contact['unloaded_tip_gap_mm'])]
    stop = contact['negative_stop_compression_mm']
    release = [gap+compression-length for gap, compression, length in itertools.product(
        contact['unloaded_tip_gap_mm'],stop,cell['length_mm'])]
    return {'initial_total_min_mm': min(total), 'initial_total_max_mm': max(total),
            'individual_initial_compression_mm': [0, max(total)],
            'compressed_max_mm': max(stop), 'released_gap_min_mm': min(release),
            'maximum_push_from_any_initial_mm': max(stop),
            'available_stroke_min_mm': contact['full_stroke_mm'] - contact['source_length_tolerance_mm']}



def validate(spec, design):
    if spec.get('schema_version') != 1 or design not in ('wide', 'narrow'):
        raise ValueError('Unknown removable-cell definition/design')
    if type(spec['cell']['quantity']) is not int or spec['cell']['quantity'] != 1 or type(spec['contact']['quantity']) is not int or spec['contact']['quantity'] != 2:
        raise ValueError('Use one selected cell and two fixed contacts; no adapter or second bay')
    for name in ('diameter_mm', 'length_mm'):
        values = spec['cell'][name]
        if (len(values) != 2 or any(isinstance(v, bool) or not isinstance(v, (float, int))
                                   or not math.isfinite(v) or v <= 0 for v in values)
                or values[0] > values[1]):
            raise ValueError('Cell ' + name + ' needs positive ordered limits')
    for name in ('unloaded_tip_gap_mm','negative_stop_compression_mm'):
        values=spec['contact'][name]
        if (len(values)!=2 or any(isinstance(v,bool) or not isinstance(v,(float,int))
                                 or not math.isfinite(v) or v<=0 for v in values)
                or values[0]>values[1]):
            raise ValueError('Contact '+name+' needs positive ordered limits')
    for section,keys in (
        ('contact',('full_stroke_mm','source_length_tolerance_mm')),
        ('removal',('positive_end_release_gap_mm','withdrawal_mm','finger_radius_mm','noncontact_clearance_mm')),
        ('cradle',('width_mm','length_mm','top_z_mm','wall_mm','ceiling_mm','cell_axis_z_mm'))):
        for name in keys:
            v=spec[section][name]
            if isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) or v<=0:
                raise ValueError(section+'/'+name+' must be finite and positive')
    if (spec['contact']['part']!='Mill-Max 0850-0-15-20-83-14-11-0'
            or spec['contact']['full_stroke_mm']!=2.286
            or spec['contact']['source_length_tolerance_mm']!=.15):
        raise ValueError('Contact source/stroke changed; review the selected part first')
    travel = contact_travel(spec)
    if (travel['initial_total_min_mm'] <= 0 or travel['released_gap_min_mm'] < spec['removal']['positive_end_release_gap_mm']
            or travel['available_stroke_min_mm']-travel['compressed_max_mm'] < spec['removal']['noncontact_clearance_mm']):
        raise ValueError('Contact travel cannot retain the cell and release its negative end')
    cradle = spec['cradle']
    if cradle['width_mm'] - 2*cradle['wall_mm'] <= spec['cell']['diameter_mm'][1]:
        raise ValueError('Cradle has no radial cell clearance')
    top = cradle['cell_axis_z_mm'] + spec['cell']['diameter_mm'][1]/2
    if cradle['top_z_mm'] - cradle['ceiling_mm'] - top < spec['removal']['noncontact_clearance_mm']:
        raise ValueError('Cell/insulating-ceiling clearance is insufficient')
    return travel


def native_shapes(spec, design):
    """Make closed-position solids; builders own integration and native sweeps."""
    import FreeCAD as App
    import Part
    from hardware_spec import WASHERS, nut_dimensions

    validate(spec, design)
    c, door, keeper = (spec[k] for k in ('cradle', 'door', 'keeper'))
    cx, cy = spec['designs'][design]['cell_centre_xy_mm']

    def box(w, length, height, x, y, z):
        return Part.makeBox(w, length, height, App.Vector(x-w/2, y-length/2, z))

    def cylinder(radius, length, x, y, z, axis=(0, 0, 1)):
        return Part.makeCylinder(radius, length, App.Vector(x, y, z), App.Vector(*axis))

    outer = box(c['length_mm'], c['width_mm'], c['top_z_mm'], cx, cy, 0)
    inner = box(c['length_mm']-4, c['width_mm']-4,
                c['top_z_mm']-c['ceiling_mm']+1, cx, cy, -1)
    frame = outer.cut(inner)
    lip=box(c['length_mm'],c['width_mm'],3.4,cx,cy,-3.4).cut(
        box(c['length_mm']-4,c['width_mm']-4,5.4,cx,cy,-4.4))
    frame=frame.fuse(lip)
    cutout = box(*c['rear_opening_mm'], 10, cx, cy, -5)
    mounts = []
    for side, end in itertools.product((-1, 1), repeat=2):
        x, y = cx+side*c['mount_x_mm'], cy+end*c['mount_y_offset_mm']
        flange = box(12, 8, c['mount_thickness_mm'], x-side*2, y, c['mount_bottom_z_mm'])
        flange = flange.cut(cylinder(1.7, 8, x, y, 0))
        frame = frame.fuse(flange)
        cutout = cutout.fuse(box(14, 10, 5, x-side*2, y, 2))
        cutout = cutout.fuse(cylinder(1.7, 10, x, y, -5))
        mounts.append([x, y, c['mount_bottom_z_mm']])
    hy, hz = cy+door['hinge_y_offset_mm'], door['hinge_z_mm']
    hinge_parts = []
    for x in (-40, 40):
        ear = cylinder(door['hinge_radius_mm'], 8, cx+x-4, hy, hz, (1, 0, 0))
        ear = ear.fuse(box(8, 8, 5, cx+x, hy+2, hz+.6))
        ear = ear.cut(cylinder(door['hinge_bore_radius_mm'], 10, cx+x-5, hy, hz, (1, 0, 0)))
        frame = frame.fuse(ear)
        cutout=cutout.fuse(box(10,10,10,cx+x,hy+2,-5))
        hinge_parts.append(cylinder(door['hinge_radius_mm']+.3, 9, cx+x-4.5, hy, hz, (1, 0, 0)))
    lid = box(door['length_mm'], door['width_mm'], door['thickness_mm'], cx, cy, door['bottom_z_mm'])
    for relief in hinge_parts:
        lid = lid.cut(relief)
    for x in (-26, 0, 26):
        knuckle = cylinder(door['hinge_radius_mm'], 12, cx+x-6, hy, hz, (1, 0, 0))
        lid = lid.fuse(knuckle)
    lid = lid.cut(cylinder(door['hinge_bore_radius_mm'], 100, cx-50, hy, hz, (1, 0, 0)))
    pin = cylinder(door['hinge_pin_radius_mm'], door['hinge_pin_length_mm'],
                   cx-door['hinge_pin_length_mm']/2, hy, hz, (1, 0, 0))
    pin = pin.fuse(cylinder(2.75, 3, cx-door['hinge_pin_length_mm']/2-3,
                            hy, hz, (1, 0, 0)))
    def m3_nut(x,y,z,axis):
        from hardware_spec import hexagon
        flats,thickness=nut_dimensions('M3')
        outline=[App.Vector(a,b,0) for a,b in hexagon(0,0,flats)]
        nut=Part.Face(Part.makePolygon(outline+[outline[0]])).extrude(App.Vector(0,0,thickness))
        nut=nut.cut(cylinder(1.6,3,0,0,-.1))
        if axis == 'X': nut.rotate(App.Vector(),App.Vector(0,1,0),90)
        nut.translate(App.Vector(x,y,z))
        return nut
    hinge_nut = m3_nut(cx+45.5,hy,hz,'X')
    lid = lid.cut(cylinder(3.8, 16.5, cx-52, hy, hz, (1,0,0)))
    lid = lid.cut(cylinder(3.8, 14.5, cx+35.5, hy, hz, (1,0,0)))
    hinge_spacing={}
    m3_washer=WASHERS['M3']
    wt=m3_washer['thickness']
    for i,start,end in ((0,-48.5,-44-wt),(1,44+wt,45.3)):
        hinge_spacing['BatteryHingeSpacer'+str(i)]=cylinder(3.4,end-start,cx+start,hy,hz,(1,0,0)).cut(
            cylinder(1.6,end-start+.2,cx+start-.1,hy,hz,(1,0,0)))
    for i,start in enumerate((-44-wt,44)):
        hinge_spacing['BatteryHingeWasher'+str(i)]=cylinder(m3_washer['od']/2,wt,cx+start,hy,hz,(1,0,0)).cut(
            cylinder(m3_washer['id']/2,wt+.2,cx+start-.1,hy,hz,(1,0,0)))
    px, py = cx+keeper['pivot_x_mm'], cy+keeper['pivot_y_offset_mm']
    post = cylinder(4.5, 5, px, py, 0).fuse(box(9, 9, 5, px, py, 0))
    post = post.cut(cylinder(1.6, 6, px, py, -.5))
    frame = frame.fuse(post)
    # The bar rotates below the cell. Its rear bridge retains the pivot cap;
    # clearance is local to the bar's specified 90-degree opening quadrant.
    frame = frame.cut(box(40, 40, keeper['thickness_mm']+.5,
                          px+16, py-16, keeper['bottom_z_mm']-.25))
    frame=frame.cut(cylinder(3.1,2.15,px,py,keeper['bottom_z_mm']-2.15))
    keeper_head_z=keeper['bottom_z_mm']-.25
    keeper_pin=cylinder(1.5,12,px,py,keeper_head_z).fuse(
        cylinder(2.85,1.65,px,py,keeper_head_z-1.65))
    keeper_nuts=[m3_nut(px,py,z,'Z') for z in (5,7.4)]
    frame=frame.cut(cylinder(3.5,6,px,py,5))
    cutout = cutout.fuse(box(10, 11, 10, px, py, -5))
    bar = box(keeper['width_mm'], keeper['length_mm'], keeper['thickness_mm'],
              px, py-keeper['length_mm']/2, keeper['bottom_z_mm'])
    bar = bar.fuse(cylinder(keeper['width_mm']/2, keeper['thickness_mm'], px, py, keeper['bottom_z_mm']))
    bar = bar.cut(cylinder(1.6, 8, px, py, -3))
    # Captive flex catch: move the pad laterally left before opening the door.
    # The hook bears above a ledge; an outward pull alone cannot clear it.
    lx, ly = cx+35, cy+20
    for x in (lx-2.5, lx+2.5):
        lid = lid.cut(box(3, 10, 3, x, ly-7, door['bottom_z_mm']-.5))
    beam = box(2, 10, door['thickness_mm'], lx, ly+3, door['bottom_z_mm'])
    pad = box(8, 4, door['thickness_mm'], lx, ly+8, door['bottom_z_mm'])
    hook = box(1, 2, 1.3-door['bottom_z_mm']-door['thickness_mm'], lx+.5, ly, door['bottom_z_mm']+door['thickness_mm'])
    hook = hook.fuse(box(3, 2, .8, lx+1.5, ly, .5))
    lid = lid.fuse(beam).fuse(pad).fuse(hook)
    catch = box(3, 4, 5, lx+7, ly-2, 0)
    catch = catch.fuse(box(5, 5, .8, lx+5, ly-.5, -.3))
    frame = frame.fuse(catch)
    hood = box(18, 10, 1.5, lx+5, ly, 5)
    hood = hood.fuse(box(2, 10, 6.5, lx-3, ly, 0))
    hood = hood.fuse(box(2, 10, 6.5, lx+13, ly, 0))
    hood = hood.fuse(box(18, 2, 6.5, lx+5, ly+4, 0))
    frame = frame.fuse(hood)
    cutout = cutout.fuse(box(20,12,10,lx+5,ly+1,-5))
    # Cover the keeper's outward rotation slot. The roof and three outer
    # walls isolate unrelated electronics; the cell-facing side stays open.
    kcx,kcy=px+15,py+1.5
    keeper_hood=box(40,8.5,1.5,kcx,kcy,1.35)
    keeper_hood=keeper_hood.fuse(box(40,1.5,2.85,kcx,py+5,0))
    for end in (-19.5,19.5):
        keeper_hood=keeper_hood.fuse(box(1,8.5,2.85,kcx+end,kcy,0))
    frame=frame.fuse(keeper_hood).cut(cylinder(1.6,14,px,py,-3))
    cutout=cutout.fuse(box(40.6,9.1,10,kcx,kcy,-5))
    # Engrave enduring polarity strokes on the insulating ceiling. They remain
    # visible in the empty bay and do not depend on colour or a font renderer.
    marks = [box(8, 1.2, .5, cx+30, cy, c['top_z_mm']-c['ceiling_mm']-.1),
             box(1.2, 8, .5, cx+30, cy, c['top_z_mm']-c['ceiling_mm']-.1),
             box(8, 1.2, .5, cx-30, cy, c['top_z_mm']-c['ceiling_mm']-.1)]
    for mark in marks:
        frame = frame.cut(mark)
    # Capture each contact flange between two insulating plates. M2 fasteners
    # lie outside the cell diameter; only the intended gold plunger touches a
    # cell terminal. These are designed nominal solids, not supplied-part scans.
    contact_parts = {}
    contact_sleeves = {}
    pin_dims = spec['contact']['drawing']
    tip = sum(spec['contact']['unloaded_tip_gap_mm'])/4
    for side, suffix in ((1, 'P'), (-1, 'N')):
        face = tip+pin_dims['initial_tip_to_mount_mm']
        flange_front = face-pin_dims['flange_thickness_mm']
        front_x, back_x = flange_front-1.8, face
        cell_end = spec['cell']['length_mm'][1]/2
        nose_end = tip+spec['contact']['full_stroke_mm']
        def axial_cylinder(r, start, end):
            return cylinder(r, end-start, cx+side*start, cy, c['cell_axis_z_mm'], (side,0,0))
        sleeve = axial_cylinder(pin_dims['barrel_diameter_mm']/2, nose_end, flange_front)
        sleeve = sleeve.fuse(axial_cylinder(pin_dims['flange_diameter_mm']/2, flange_front, face))
        sleeve = sleeve.fuse(axial_cylinder(pin_dims['rear_diameter_mm']/2, face, tip+pin_dims['total_height_mm']))
        plunger = axial_cylinder(pin_dims['tip_diameter_mm']/2, cell_end, nose_end)
        contact_parts['BatteryContact'+suffix] = sleeve.fuse(plunger)
        contact_sleeves[suffix] = sleeve
        for label, start, bore in (('Front',front_x,1.5),('Back',back_x,1.4)):
            centre_x = cx+side*(start+.9)
            plate = box(1.8,36,18,centre_x,cy,c['cell_axis_z_mm']-9)
            plate = plate.cut(axial_cylinder(bore,start-.1,start+1.9))
            for y,z in ((-14.5,-5.5),(14.5,5.5)):
                hole = cylinder(1.2,20,cx+side*(front_x-.1),cy+y,c['cell_axis_z_mm']+z,(side,0,0))
                plate=plate.cut(hole)
                frame=frame.cut(hole)
            if suffix == 'N' and label == 'Front':
                stop_face=tip+sum(spec['contact']['negative_stop_compression_mm'])/2
                stop=axial_cylinder(3,stop_face,stop_face+1.2).cut(
                    axial_cylinder(1.5,stop_face-.1,stop_face+1.3))
                # For the negative end, the upper bridge joins the ring to the
                # front clamp plate while clearing the nominal sleeve.
                bridge=box(.9,6,6.3,cx+side*(front_x+.05),cy,c['cell_axis_z_mm']+2.7)
                plate=plate.fuse(stop).fuse(bridge)
                frame=frame.cut(box(2.2,7,7,cx+side*(front_x-.3),cy,c['cell_axis_z_mm']+2.4))
            contact_parts['BatteryContact'+suffix+label] = plate
            # The two plates leave the flange recess at the source datum.
            relief=box(2.3,36.5,18.5,centre_x,cy,c['cell_axis_z_mm']-9.25)
            frame=frame.cut(relief)
        # Extend the insulating end walls around the exposed solder tails.
        # The removable-cell opening cannot give access to unrelated boards.
        hood = box(13.8,41,22,cx+side*46.1,cy,2.5)
        hood = hood.cut(box(16,37,20,cx+side*46.1,cy,2.5))
        # Roof stays inside the full Fibonacci board's unobstructed central bay.
        hood = hood.common(cylinder(82.4,28,0,0,0))
        frame=frame.fuse(hood)
        cutout=cutout.fuse(box(16,42,10,cx+side*46.1,cy,2))
        # Remove plate seats after adding the surrounding terminal hoods.
        for start in (front_x,back_x):
            frame=frame.cut(box(2.3,36.5,18.5,cx+side*(start+.9),cy,c['cell_axis_z_mm']-9.25))
        for i,(y,z) in enumerate(((-14.5,-5.5),(14.5,5.5))):
            hole=cylinder(1.2,20,cx+side*(front_x-.1),cy+y,c['cell_axis_z_mm']+z,(side,0,0))
            # Printed compression tube and replaceable insulating shim connect
            # the back clamp plate to the case end wall. The screw does not
            # span an unsupported air gap under tightening load.
            inner_end=c['length_mm']/2-c['wall_mm']
            back_end=back_x+1.8
            spacer_start=back_end+.25
            frame=frame.fuse(cylinder(3.5,c['wall_mm'],cx+side*inner_end,
                                      cy+y,c['cell_axis_z_mm']+z,(side,0,0)))
            frame=frame.cut(cylinder(3.25,inner_end-back_end+.1,cx+side*(back_end-.1),
                                     cy+y,c['cell_axis_z_mm']+z,(side,0,0)))
            def ring(outer,inner,start,height):
                return cylinder(outer,height,cx+side*start,cy+y,c['cell_axis_z_mm']+z,(side,0,0)).cut(
                    cylinder(inner,height+.2,cx+side*(start-.1),cy+y,c['cell_axis_z_mm']+z,(side,0,0)))
            contact_parts[f'BatteryContact{suffix}Shim{i}']=ring(3,1.2,back_end,.25)
            contact_parts[f'BatteryContact{suffix}Spacer{i}']=ring(3,1.2,spacer_start,inner_end-spacer_start)
            m2_washer=WASHERS['M2']
            contact_parts[f'BatteryContact{suffix}Washer{i}']=ring(
                m2_washer['od']/2,m2_washer['id']/2,inner_end+c['wall_mm'],m2_washer['thickness'])
            frame=frame.cut(hole)
            frame=frame.cut(cylinder(2.15,2.3,cx+side*(front_x+.1),cy+y,
                                      c['cell_axis_z_mm']+z,(-side,0,0)))
            stem=cylinder(1,16,cx+side*front_x,cy+y,c['cell_axis_z_mm']+z,(side,0,0))
            head=cylinder(1.9,2,cx+side*front_x,cy+y,c['cell_axis_z_mm']+z,(-side,0,0))
            contact_parts[f'BatteryContact{suffix}Screw{i}']=stem.fuse(head)
            m2_flats,m2_thickness=nut_dimensions('M2')
            nut_start=inner_end+c['wall_mm']+m2_washer['thickness']
            verts=[App.Vector(cx+side*nut_start,cy+y+m2_flats/math.sqrt(3)*math.cos(j*math.tau/6),
                              c['cell_axis_z_mm']+z+m2_flats/math.sqrt(3)*math.sin(j*math.tau/6)) for j in range(6)]
            nut=Part.Face(Part.makePolygon(verts+[verts[0]])).extrude(App.Vector(side*m2_thickness,0,0))
            nut=nut.cut(cylinder(1.05,m2_thickness+.2,cx+side*(nut_start-.1),cy+y,c['cell_axis_z_mm']+z,(side,0,0)))
            contact_parts[f'BatteryContact{suffix}Nut{i}']=nut
    front_x=tip+pin_dims['initial_tip_to_mount_mm']-pin_dims['flange_thickness_mm']-1.8
    frame=frame.cut(box(2.2,7,7,cx-front_x+.3,cy,c['cell_axis_z_mm']+2.4))
    # Shallow door saddles prevent a cell outside the designed seat from
    # clearing the closed door. This is geometry, not a measured latch force.
    for offset in (-14,14):
        saddle=box(4,9,6,cx+offset,cy,door['bottom_z_mm']+door['thickness_mm'])
        saddle=saddle.cut(cylinder(spec['cell']['diameter_mm'][1]/2+.3,8,
                                    cx+offset-4,cy,c['cell_axis_z_mm'],(1,0,0)))
        lid=lid.fuse(saddle)
    # Source-sized insulating pull tape. The representative upper U-drape
    # touches the cell, while its fixed bar and stock maximum stay outside
    # the withdrawal cylinder. Cloth deformation and sewn strength are tests.
    tape=spec['ribbon']
    tw,th=tape['width_mm'][1],tape['thickness_mm'][1]
    rz=c['cell_axis_z_mm']
    rr=spec['cell']['diameter_mm'][1]/2
    band=cylinder(rr+th,tw,cx-tw/2,cy,rz,(1,0,0)).cut(
        cylinder(rr,tw+2,cx-tw/2-1,cy,rz,(1,0,0)))
    band=band.common(box(tw+2,2*(rr+th)+2,rr+th+1,cx,cy,rz))
    left=box(tw,th,rz-3+.02,cx,cy-rr-th/2,3)
    right=box(tw,th,rz+.02,cx,cy+rr+th/2,0)
    lower=box(tw,17-rr+th,th,cx,cy-(17+rr-th)/2,3)
    fold=box(tw,th,3.6+th,cx,cy-17+th/2,3)
    upper=box(tw,17-rr+th,th,cx,cy-(17+rr-th)/2,6.6)
    tab=box(tw,rr+th-3,2*th,cx,cy+(rr+th+3)/2,0)
    ribbon=band.fuse(left).fuse(right).fuse(lower).fuse(fold).fuse(upper).fuse(tab)
    well=box(tw+4,5,9.5,cx,cy-16.5,0)
    well=well.cut(box(tw+.5,4,7,cx,cy-15.8,1))
    anchor_bar=box(tw+4,3,2.2,cx,cy-14.3,3.8)
    # Cut the blind anchor well before adding its bridge; outer insulation
    # remains continuous between the compartment and unrelated electronics.
    frame=frame.cut(box(tw+.5,4,7,cx,cy-15.8,1)).fuse(well).fuse(anchor_bar)
    cutout=cutout.fuse(box(tw+5,7,10,cx,cy-16.5,-5))
    chamfer=c['upper_chamfer']
    low=chamfer['bottom_z_mm']
    height=c['top_z_mm']-low
    keep=cylinder(200,low,0,0,0).fuse(Part.makeCone(
        chamfer['bottom_radius_mm'],chamfer['top_radius_mm'],height,App.Vector(0,0,low)))
    # Preserve the projecting hinge/lip belowZ0 while trimming only the high
    # corners, where the existing Wide circle seat slopes inward.
    keep=keep.fuse(cylinder(200,10,0,0,-10))
    frame=frame.common(keep)
    case_hardware={}
    mt=c['mount_bottom_z_mm']+c['mount_thickness_mm']
    washer=WASHERS['M3']
    for i,(x,y,z) in enumerate(mounts):
        case_hardware['BatteryCaseMountScrew'+str(i)]=cylinder(1.5,10,x,y,0).fuse(cylinder(2.75,3,x,y,-3))
        case_hardware['BatteryCaseMountWasher'+str(i)]=cylinder(washer['od']/2,washer['thickness'],x,y,mt).cut(
            cylinder(washer['id']/2,washer['thickness']+.2,x,y,mt-.1))
        case_hardware['BatteryCaseMountNut'+str(i)]=m3_nut(x,y,mt+washer['thickness'],'Z')
    rear_interface=cylinder(spec['designs'][design]['case_diameter_mm']/2,2,0,0,0).cut(cutout)
    length = spec['cell']['length_mm'][1]
    cell = cylinder(spec['cell']['diameter_mm'][1]/2, length,
                    cx-length/2, cy, c['cell_axis_z_mm'], (1, 0, 0))
    return {**case_hardware, **hinge_spacing, **contact_parts, 'BatteryCradle': frame.removeSplitter(), 'BatteryDoor': lid.removeSplitter(),
            'BatteryKeeper': bar.removeSplitter(), 'BatteryHingePin': pin,
            'BatteryHingeNut': hinge_nut, 'BatteryKeeperScrew': keeper_pin,
            'BatteryKeeperNut0': keeper_nuts[0], 'BatteryKeeperNut1': keeper_nuts[1],
            'BatteryCell': cell, 'BatteryPullRibbon': ribbon.removeSplitter(), 'contact_sleeves': contact_sleeves, 'rear_cutout': cutout, 'mounts': mounts, 'rear_interface': rear_interface,
            'hinge_axis': [cx, hy, hz], 'keeper_axis': [px, py, 0],
            'latch_hook': hook, 'latch_pad': pad, 'latch_axis': [-1, 0, 0]}


def native_check(spec, design, shapes):
    """Check closed solids and continuous motion envelopes of the prototype.

    The latch path assumes the specified hook deflection. It does not prove
    print strain, release force or fatigue. Contact/end-insulator wiping and
    fitted electrical hardware remain separate open physical/design reviews.
    """
    import FreeCAD as App
    import Part

    names=tuple(sorted(PART_NAMES))
    actual={name for name in shapes if name.startswith('Battery')}
    if actual != PART_NAMES:
        raise ValueError('Battery component census differs: missing='+str(sorted(PART_NAMES-actual))
                         +', extra='+str(sorted(actual-PART_NAMES)))
    for name in names:
        shape = shapes[name]
        if not shape.isValid() or len(shape.Solids) != 1 or shape.Volume <= 0:
            raise ValueError(name + ' must be one valid solid')
    checked={name:shapes[name] for name in names}
    checked['rear_interface']=shapes['rear_interface']
    for a, b in itertools.combinations(checked, 2):
        ab,bb=checked[a].BoundBox,checked[b].BoundBox
        if any(min(getattr(ab,axis+'Max'),getattr(bb,axis+'Max'))
               -max(getattr(ab,axis+'Min'),getattr(bb,axis+'Min')) <= 1e-7 for axis in 'XYZ'):
            continue
        volume = checked[a].common(checked[b]).Volume
        if volume > 1e-5:
            raise ValueError(f'Battery closed-position interference: {a}/{b}: {volume:g} mm3')

    def rotate(shape, axis, direction, angle):
        moved = shape.copy()
        moved.rotate(App.Vector(*axis), App.Vector(*direction), angle)
        return moved

    def rotation_clearance(moving, fixed, axis, direction, last, step=.5):
        # Distance is 1-Lipschitz in point displacement. This converts the
        # sampled distances to a conservative bound over every angle interval.
        origin = App.Vector(*axis)
        unit = App.Vector(*direction)
        radius = max((v.Point-origin).cross(unit).Length for v in moving.Vertexes)
        # Curved surfaces can extend beyond their topological vertices.
        bb = moving.BoundBox
        corners = itertools.product((bb.XMin, bb.XMax), (bb.YMin, bb.YMax), (bb.ZMin, bb.ZMax))
        radius = max(radius, *( (App.Vector(*p)-origin).cross(unit).Length for p in corners))
        count = math.ceil(abs(last)/step)
        half_interval = math.radians(abs(last)/count)/2
        displacement = 2*radius*math.sin(half_interval/2)
        distances = [rotate(moving, axis, direction, last*i/count).distToShape(fixed)[0]
                     for i in range(count+1)]
        bound = min(distances)-displacement
        if bound <= 0:
            raise ValueError(f'Battery motion has no positive continuous clearance: {bound:g} mm')
        return bound

    released = shapes['latch_hook'].copy()
    released.translate(App.Vector(-spec['door']['latch_release_mm'], 0, 0))
    released_door = shapes['BatteryDoor'].cut(shapes['latch_hook']).fuse(released)
    fixed_door=Part.makeCompound([shapes['rear_interface']]+[shapes[name] for name in names if name not in {'BatteryDoor','BatteryPullRibbon'}])
    door_gap = rotation_clearance(released_door, fixed_door,
                                  shapes['hinge_axis'], (1, 0, 0),
                                  -spec['door']['open_angle_deg'],step=.25)
    opened_door = rotate(released_door, shapes['hinge_axis'], (1, 0, 0),
                         -spec['door']['open_angle_deg'])
    fixed_keeper=Part.makeCompound([opened_door,shapes['rear_interface']]+[shapes[name] for name in names
                                  if name not in {'BatteryDoor','BatteryKeeper','BatteryPullRibbon'}])
    keeper_gap = rotation_clearance(shapes['BatteryKeeper'], fixed_keeper,
                                    shapes['keeper_axis'], (0, 0, 1),
                                    spec['keeper']['open_angle_deg'],step=.25)
    opened_keeper = rotate(shapes['BatteryKeeper'], shapes['keeper_axis'], (0, 0, 1),
                           spec['keeper']['open_angle_deg'])
    c, removal = spec['cradle'], spec['removal']
    cx, cy = spec['designs'][design]['cell_centre_xy_mm']
    radius, length = spec['cell']['diameter_mm'][1]/2, spec['cell']['length_mm'][1]
    # Include every initial axial position permitted by the tip gap, not only
    # the centred display pose. The final positive end clears its contact.
    half_gap = spec['contact']['unloaded_tip_gap_mm'][0]/2
    stop_face=cx-sum(spec['contact']['unloaded_tip_gap_mm'])/4-sum(spec['contact']['negative_stop_compression_mm'])/2
    final_centre_x = stop_face+length/2
    initial_centre_max_x = cx - half_gap + length/2
    shift = final_centre_x-cx
    # Exact Minkowski sweep: axial translation, followed by straight -Z
    # withdrawal. No isolated animation frames substitute for this envelope.
    axial = Part.makeCylinder(radius, length+initial_centre_max_x-final_centre_x,
                               App.Vector(final_centre_x-length/2, cy, c['cell_axis_z_mm']),
                               App.Vector(1,0,0))
    moved = shapes['BatteryCell'].copy()
    moved.translate(App.Vector(shift,0,-removal['withdrawal_mm']))
    middle = Part.makeBox(length, 2*radius, removal['withdrawal_mm'],
                          App.Vector(cx-length/2+shift,cy-radius,
                                     c['cell_axis_z_mm']-removal['withdrawal_mm']))
    sweep = Part.makeCompound([axial, middle, moved])
    gaps = {name:sweep.distToShape(shape)[0] for name,shape in (
        ('cradle', shapes['BatteryCradle']), ('rear_interface',shapes['rear_interface']), ('opened_door', opened_door),
        ('opened_keeper', opened_keeper))}
    gaps.update({'contact_body_'+name:sweep.distToShape(shape)[0]
                 for name,shape in shapes['contact_sleeves'].items()})
    gaps.update({name:sweep.distToShape(shapes[name])[0] for name in names
                 if name not in {'BatteryCell','BatteryCradle','BatteryDoor','BatteryKeeper',
                                 'BatteryContactP','BatteryContactN','BatteryPullRibbon'}})
    finger=Part.makeCylinder(removal['finger_radius_mm'],45,
                              App.Vector(cx,cy,removal['finger_start_z_mm']-30))
    finger_fixed=[shapes['rear_interface'],shapes['BatteryCradle'],opened_door,opened_keeper]
    finger_fixed += [shapes[name] for name in names if name not in
                    {'BatteryCell','BatteryCradle','BatteryDoor','BatteryKeeper','BatteryPullRibbon'}]
    finger_gap=min(finger.distToShape(shape)[0] for shape in finger_fixed)
    if finger_gap < removal['noncontact_clearance_mm']:
        raise ValueError('Finger approach has insufficient clearance: '+str(finger_gap))
    # The insulating negative stop intentionally bears on the end face. It
    # must never intersect the cell volume. All other fixed solids need the
    # stated positive non-contact clearance.
    stop_part=shapes['BatteryContactNFront']
    if sweep.common(stop_part).Volume > 1e-5:
        raise ValueError('Cell crosses its insulating end stop')
    stop_gap=gaps.pop('BatteryContactNFront')
    # A minimum-size cell displaced 1 mm outward cannot clear the seating
    # saddles. This does not claim a measured latch or cloth-compression test.
    small=Part.makeCylinder(spec['cell']['diameter_mm'][0]/2,spec['cell']['length_mm'][0],
                            App.Vector(cx-spec['cell']['length_mm'][0]/2,cy,c['cell_axis_z_mm']-1),
                            App.Vector(1,0,0))
    unseated_interference=small.common(shapes['BatteryDoor']).Volume
    if unseated_interference <= 1e-5:
        raise ValueError('A 1 mm unseated cell clears the closed seating saddles')
    if min(gaps.values()) < removal['noncontact_clearance_mm']-1e-6:
        raise ValueError('Cell removal clearance failed: ' + str(gaps))
    return {'closed_interference_mm3': 0, 'one_mm_unseated_cell_interference_mm3': unseated_interference, 'finger_approach_clearance_mm': finger_gap, 'door_continuous_clearance_mm': door_gap,
            'keeper_continuous_clearance_mm': keeper_gap,
            'cell_continuous_clearance_mm': gaps,
            'intended_insulating_stop_contact_mm3': sweep.common(stop_part).Volume,
            'insulating_stop_nominal_gap_mm': stop_gap,
            'contact_body_stroke_margin_mm': validate(spec, design)['available_stroke_min_mm']-validate(spec, design)['compressed_max_mm'],
            'contact_travel': validate(spec, design),
            'proof_boundary': 'Specified prototype geometry only; no physical fit/force/temperature acceptance.'}
