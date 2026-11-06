"""Fixed contact leads, secondary insulation and the selected main fuse assembly gauge.

This is specified assembly geometry. Wire cut lengths and support dimensions
are targets, not measurements or physical fault/abrasion qualification.
"""
import math
import json
from pathlib import Path

WIRE_NAMES=frozenset({'BatteryLeadP','BatteryLeadN'})
FUSE_NAME='BatteryMainFuse'
FUSE_TIE_NAMES=frozenset('BatteryMainFuseLacing'+str(i) for i in range(2))


def layout(spec, design, electrical=None):
    """Resolve the selected contact-lead targets without importing FreeCAD."""
    electrical = electrical if electrical is not None else json.loads(
        Path(__file__).with_name('electrical-design.json').read_text())
    settings = spec['contact_leads']
    if any(electrical['parts'][key]['part']!=spec['contact']['part'] for key in ('CONTACT_P','CONTACT_N')):
        raise ValueError('Contact geometry and selected circuit must use the same wire-mount part')
    for name,value in settings.items():
        if name.endswith('_mm') and (isinstance(value,bool) or not isinstance(value,(int,float))
                                    or not math.isfinite(value) or value<=0):
            raise ValueError('Contact-lead target must be finite and positive: '+name)
    lacing=settings.get('main_fuse_lacing',{})
    expected={'part':'Alpha Wire LC134 BK088','quantity':2,'blank_length_mm':70,
              'stock_section_max_mm':[1.6764,.4318],'finished_loop_section_mm':[1.7,.5],
              'knot_space_mm':[4,2.2,2],'knot_side':'negativeY','knot_x_offsets_mm':[0,1],
              'body_gauge_mm':[9,5,5],'joint_gauge_mm':[5.5,3.5,3.5],
              'source':'https://www.alphawire.com/products/accessories/fit-wire-management/lacing-tape/lc134',
              'source_revision':'Alpha specification printed13May2024; .060±.006in width/.014±.003in thickness;25lb tape breaking strength,not knot retention',
              'insulation':'TE Raychem RNF-100-1/8-0-SP; recover outside PETG; finish each fuse/joint assembly within20x5x5mm gauge'}
    if (any(lacing.get(key)!=value for key,value in expected.items()) or type(lacing.get('quantity')) is not int
            or not all(lacing.get(key) for key in ('source','source_revision','insulation'))
            or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v)
                   for v in lacing.get('knot_x_offsets_mm',[]))):
        raise ValueError('Keep both selected main-fuse lacing loops and their complete assembly spaces')
    stations=lacing.get('stations_from_fuse_centre_mm')
    if (not isinstance(stations,list) or len(stations)!=2 or
            any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in stations)
            or not stations[0]<0<stations[1]
            or any(abs(v)-.85<9/2+.25 or abs(v)+.85>10 for v in stations)):
        raise ValueError('Main-fuse ties must stay wholly on the two insulated lead regions, clear of the body gauge')
    tilt=settings['route_descent_deg']
    if isinstance(tilt,bool) or not isinstance(tilt,(int,float)) or not math.isfinite(tilt) or not 0<=tilt<45:
        raise ValueError('Contact route descent needs a finite angle in[0,45)degrees')
    tilt=math.radians(tilt)
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
    cup_start=tail-spec['contact']['drawing']['cup_length_mm']
    wall_start=spec['cradle']['length_mm']/2-spec['cradle']['wall_mm']
    collar_start=settings['cup_collar_start_x_from_cell_mm']
    collar_end=settings['cup_collar_end_x_from_cell_mm']
    collar_inner=settings['cup_collar_inner_radius_mm']
    collar_outer=settings['cup_collar_outer_radius_mm']
    cup_max_r=(spec['contact']['drawing']['cup_outer_diameter_mm']+.0508)/2
    if collar_inner-cup_max_r<spec['removal']['noncontact_clearance_mm'] or collar_outer-collar_inner<1.35:
        raise ValueError('The selected cup needs source-tolerance clearance and its full insulator wall')
    if (bend_x-tail<2*(2*wire_r) or not cup_start<collar_start<wall_start<tail<start_x<collar_end<bend_x
            or collar_end-tail<2*wire_r):
        raise ValueError('Keep supported cup/insulation overlap and the first bend clear of the joint')
    return_length=settings['final_return_straight_mm']
    length=bend_x-tail+math.pi*r+straight+return_length
    cut=length+2*settings['strip_each_end_mm']
    if cut>settings['blank_length_mm']:
        raise ValueError('The blank cannot supply the route and both stripped ends')
    if settings['main_fuse_centre_x_from_cell_mm']+10!=bend_x-return_length:
        raise ValueError('Positive lead must end at the selected main-fuse input')
    plane_offset=-2*r-straight
    final_drop=plane_offset*math.sin(tilt)
    if spec['cradle']['cell_axis_z_mm']+final_drop-5-2<1.35:
        raise ValueError('Fuse cavity leaves less than1.35mm above its rear-bearing hood brace')
    return {'cup_collar_start_mm':collar_start,'cup_collar_end_mm':collar_end,
            'cup_collar_inner_radius_mm':collar_inner,'cup_collar_outer_radius_mm':collar_outer,
            'tilt_rad':tilt,'plane_final_offset_mm':plane_offset,
            'radius_mm':r,'bend_x_mm':bend_x,'straight_mm':straight,
            'conduit_start_x_mm':start_x,'conduit_inner_radius_mm':inner_r,
            'conduit_outer_radius_mm':outer_r,'wire_radius_mm':wire_r,
            'return_length_mm':return_length,'tail_x_mm':tail,'final_offset_y_mm':plane_offset*math.cos(tilt),'final_offset_z_mm':final_drop,
            'routed_centreline_mm':length,'finished_cut_target_mm':cut,
            'cell_centre_xy_mm':spec['designs'][design]['cell_centre_xy_mm'],
            'main_fuse_lacing':dict(lacing)}


def native_shapes(spec,design):
    import FreeCAD as App
    import Part
    data=layout(spec,design)
    settings=spec['contact_leads']
    cx,cy=data['cell_centre_xy_mm']
    z=spec['cradle']['cell_axis_z_mm']
    r=data['radius_mm'];bend_x=data['bend_x_mm'];straight=data['straight_mm']
    final_offset=data['plane_final_offset_mm'];tail=data['tail_x_mm']
    wire_r=data['wire_radius_mm'];inner_r=data['conduit_inner_radius_mm']
    outer_r=data['conduit_outer_radius_mm']
    def point(side,x,y):return App.Vector(cx+side*x,cy+y*math.cos(data['tilt_rad']),z+y*math.sin(data['tilt_rad']))
    def route(side,start_x):
        q=math.sqrt(.5)
        a=point(side,bend_x,0)
        b=point(side,bend_x+r,-r)
        c=point(side,bend_x+r,-r-straight)
        d=point(side,bend_x,final_offset)
        return Part.Wire([Part.makeLine(point(side,start_x,0),a),
            Part.Arc(a,point(side,bend_x+r*q,-r+r*q),b).toShape(),
            Part.makeLine(b,c),
            Part.Arc(c,point(side,bend_x+r*q,final_offset+r-r*q),d).toShape(),
            Part.makeLine(d,point(side,bend_x-data['return_length_mm'],final_offset))])
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
        collar_length=data['cup_collar_end_mm']-data['cup_collar_start_mm']
        shells.append(Part.makeCylinder(data['cup_collar_outer_radius_mm'],collar_length,
                      point(side,data['cup_collar_start_mm'],0),App.Vector(side,0,0)))
        bores.append(Part.makeCylinder(data['cup_collar_inner_radius_mm'],collar_length,
                     point(side,data['cup_collar_start_mm'],0),App.Vector(side,0,0)))
        lengths[name]={'routed_insulated_centreline_mm':path.Length,
                       'finished_cut_target_mm':path.Length+2*settings['strip_each_end_mm'],
                       'blank_mm':settings['blank_length_mm'],'strip_each_end_mm':settings['strip_each_end_mm'],
                       'instruction':'Thread before closing the fixed contact carriers; fit and trim the blank to the declared route/joint target. Bottom the stripped conductor in the selected0854 solder cup; keep the insulation outside the joint. No live plug. Cut/fit settings are unmeasured.'}
    # Specified complete20x5x5mm insulated assembly gauge; physical fit is unmeasured.
    fx,fy=cx+settings['main_fuse_centre_x_from_cell_mm'],cy+data['final_offset_y_mm']
    z+=data['final_offset_z_mm']
    fuse=Part.makeBox(9,5,5,App.Vector(fx-4.5,fy-2.5,z-2.5)).fuse(
        Part.makeBox(20,3.5,3.5,App.Vector(fx-10,fy-1.75,z-1.75))).removeSplitter()
    housing=Part.makeBox(23.2,8.2,8.2,App.Vector(fx-11.6,fy-4.1,z-4.1))
    cavity=Part.makeBox(20.5,5.5,7.75,App.Vector(fx-10.25,fy-2.75,z-5))
    # Rear-open installation is inside the intact rear panel, outside its cell
    # opening. Two lacing slots restrain sleeved lead joints, not the epoxy fuse body.
    for i,dx in enumerate(data['main_fuse_lacing']['stations_from_fuse_centre_mm']):
        # Each loop captures the negative housing wall and a sleeved lead.
        # Both crossing bands pass through actual wall slots below the roof.
        for bottom in (-2.4,1.6):
            cavity=cavity.fuse(Part.makeBox(2.9,2.4,.8,App.Vector(fx+dx-1.45,fy-4.8,z+bottom)))
        outer=Part.makeBox(1.7,6.85,4.5,App.Vector(fx+dx-.85,fy-4.6,z-2.25))
        inner=Part.makeBox(2,5.85,3.5,App.Vector(fx+dx-1,fy-4.1,z-1.75))
        knot_x=fx+dx+data['main_fuse_lacing']['knot_x_offsets_mm'][i]
        knot=Part.makeBox(4,2.2,2,App.Vector(knot_x-2,fy-6.4,z+.5))
        result['BatteryMainFuseLacing'+str(i)]=outer.cut(inner).fuse(knot).removeSplitter()
    exit_hole=Part.makeCylinder(inner_r,5,App.Vector(fx-13,fy,z),App.Vector(1,0,0))
    cavity=cavity.fuse(exit_hole)
    result.update({FUSE_NAME:fuse,'secondary_shells':shells+[housing],
                   'secondary_bores':bores+[cavity],'wire_cuts':lengths,
                   'fuse_mount_centre_mm':[fx,fy,z],
                   'main_fuse_lacing':data['main_fuse_lacing'],
                   'main_fuse_ports_mm':{'F1.1':[fx+10,fy,z],'F1.2':[fx-10,fy,z]},
                   'individual_wire_bend_radius_mm':r,
                   'conduit_radial_clearance_mm':inner_r-wire_r,
                   'conduit_wall_mm':outer_r-inner_r})
    return result
