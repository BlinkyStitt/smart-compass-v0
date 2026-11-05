"""Fixed contact leads, secondary insulation and the one main fuse reservation.

This is specified assembly geometry. Wire cut lengths and support dimensions
are targets, not measurements or physical fault/abrasion qualification.
"""
import math
import json
from pathlib import Path

WIRE_NAMES=frozenset({'BatteryLeadP','BatteryLeadN'})
FUSE_NAME='BatteryMainFuse'


def layout(spec, design, electrical=None):
    """Resolve the selected contact-lead targets without importing FreeCAD."""
    electrical = electrical if electrical is not None else json.loads(
        Path(__file__).with_name('electrical-design.json').read_text())
    settings = spec['contact_leads']
    for name,value in settings.items():
        if name.endswith('_mm') and (isinstance(value,bool) or not isinstance(value,(int,float))
                                    or not math.isfinite(value) or value<=0):
            raise ValueError('Contact-lead target must be finite and positive: '+name)
    main=electrical['wiring']['stock_limits']['main']
    if main['stock']!='M22759/16-18' or electrical['parts']['F1']['part']!='Littelfuse 0251004.NRT1L, 4 A, axial':
        raise ValueError('Review the contact wire/fuse before changing their mechanical model')
    if electrical['parts']['F1']['loaded_envelope_mm'] != [20,5,5]:
        raise ValueError('Main-fuse reservation changed; regenerate its holder and clearances')
    diameter=main['maximum_od_mm']
    if (isinstance(diameter,bool) or not isinstance(diameter,(int,float))
            or not math.isfinite(diameter) or abs(diameter-1.8542)>1e-12):
        raise ValueError('Retain the selected wire source maximum; review changed stock before regenerating')
    wire_r=diameter/2
    r=settings['individual_bend_radius_mm']
    bend_x=settings['bend_start_x_from_cell_mm']
    straight=settings['between_bends_straight_mm']
    start_x=settings['conduit_start_x_from_cell_mm']
    inner_r=settings['conduit_inner_radius_mm']
    outer_r=settings['conduit_outer_radius_mm']
    if inner_r-wire_r<spec['removal']['noncontact_clearance_mm']:
        raise ValueError('Insulated main lead has no specified tube clearance')
    if outer_r-inner_r<1.35 or r<3*(2*wire_r):
        raise ValueError('Retain the specified insulation wall and individual-wire bend radius')
    tip=sum(spec['contact']['unloaded_tip_gap_mm'])/4
    tail=tip+spec['contact']['drawing']['total_height_mm']
    if bend_x-tail<2*(2*wire_r) or not tail<start_x<bend_x:
        raise ValueError('The first bend must clear the supported contact joint')
    length=bend_x-tail+math.pi*r+straight
    cut=length+2*settings['strip_each_end_mm']
    if cut>settings['blank_length_mm']:
        raise ValueError('The blank cannot supply the route and both stripped ends')
    if settings['main_fuse_centre_x_from_cell_mm']+10!=bend_x:
        raise ValueError('Positive lead must end at the selected main-fuse input')
    return {'radius_mm':r,'bend_x_mm':bend_x,'straight_mm':straight,
            'conduit_start_x_mm':start_x,'conduit_inner_radius_mm':inner_r,
            'conduit_outer_radius_mm':outer_r,'wire_radius_mm':wire_r,
            'tail_x_mm':tail,'final_offset_y_mm':-2*r-straight,
            'routed_centreline_mm':length,'finished_cut_target_mm':cut,
            'cell_centre_xy_mm':spec['designs'][design]['cell_centre_xy_mm']}


def native_shapes(spec,design):
    import FreeCAD as App
    import Part
    data=layout(spec,design)
    settings=spec['contact_leads']
    cx,cy=data['cell_centre_xy_mm']
    z=spec['cradle']['cell_axis_z_mm']
    r=data['radius_mm'];bend_x=data['bend_x_mm'];straight=data['straight_mm']
    final_offset=data['final_offset_y_mm'];tail=data['tail_x_mm']
    wire_r=data['wire_radius_mm'];inner_r=data['conduit_inner_radius_mm']
    outer_r=data['conduit_outer_radius_mm']
    def point(side,x,y):return App.Vector(cx+side*x,cy+y,z)
    def route(side,start_x):
        q=math.sqrt(.5)
        a=point(side,bend_x,0)
        b=point(side,bend_x+r,-r)
        c=point(side,bend_x+r,-r-straight)
        d=point(side,bend_x,final_offset)
        return Part.Wire([Part.makeLine(point(side,start_x,0),a),
            Part.Arc(a,point(side,bend_x+r*q,-r+r*q),b).toShape(),
            Part.makeLine(b,c),
            Part.Arc(c,point(side,bend_x+r*q,final_offset+r-r*q),d).toShape()])
    def sweep(path,radius,side,start_x):
        profile=Part.Wire(Part.makeCircle(radius,point(side,start_x,0),App.Vector(side,0,0)))
        return path.makePipeShell([profile],True,False)
    result={};shells=[];bores=[];lengths={}
    for side,name in ((1,'BatteryLeadP'),(-1,'BatteryLeadN')):
        path=route(side,tail)
        if abs(path.Length-data['routed_centreline_mm'])>1e-7:
            raise ValueError('Native wire centreline differs from its cut-list record')
        result[name]=sweep(path,wire_r,side,tail)
        protected=route(side,data['conduit_start_x_mm'])
        shell=sweep(protected,outer_r,side,data['conduit_start_x_mm'])
        bore=sweep(protected,inner_r,side,data['conduit_start_x_mm'])
        shells.append(shell);bores.append(bore)
        lengths[name]={'routed_insulated_centreline_mm':path.Length,
                       'finished_cut_target_mm':path.Length+2*settings['strip_each_end_mm'],
                       'blank_mm':settings['blank_length_mm'],'strip_each_end_mm':settings['strip_each_end_mm'],
                       'instruction':'Thread before closing the fixed contact carriers; fit and trim the blank to the declared route/joint target. Support the lap joint. No live plug. Cut/fit settings are unmeasured.'}
    # Main fuse is an insulated20x5x5 assembly reservation, not a glass-body scan.
    fx,fy=cx+settings['main_fuse_centre_x_from_cell_mm'],cy+final_offset
    fuse=Part.makeBox(20,5,5,App.Vector(fx-10,fy-2.5,z-2.5))
    housing=Part.makeBox(23.2,8.2,8.2,App.Vector(fx-11.6,fy-4.1,z-4.1))
    cavity=Part.makeBox(20.5,5.5,7.75,App.Vector(fx-10.25,fy-2.75,z-5))
    # Rear-open installation is inside the intact rear panel, outside its cell
    # opening. Two lacing slots restrain sleeved lead joints, not the glass body.
    for dx in (-8,8):
        cavity=cavity.fuse(Part.makeBox(2.9,10,1.1,App.Vector(fx+dx-1.45,fy-5,z-2.25)))
    exit_hole=Part.makeCylinder(inner_r,5,App.Vector(fx-13,fy,z),App.Vector(1,0,0))
    cavity=cavity.fuse(exit_hole)
    result.update({FUSE_NAME:fuse,'secondary_shells':shells+[housing],
                   'secondary_bores':bores+[cavity],'wire_cuts':lengths,
                   'fuse_mount_centre_mm':[fx,fy,z],
                   'individual_wire_bend_radius_mm':r,
                   'conduit_radial_clearance_mm':inner_r-wire_r,
                   'conduit_wall_mm':outer_r-inner_r})
    return result
