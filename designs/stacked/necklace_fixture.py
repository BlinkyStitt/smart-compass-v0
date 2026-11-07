"""Fixed suspension posts and fully retained textile attachment regions.

The loose neck span has no fixed rigid envelope. For battery service, lay that
span above the pendant, clear of the door and controls; leave attachments fitted.
Seam strength, tension, layer adhesion and wearing remain unmeasured.
"""
import math,json
from pathlib import Path


def definition(source):
    spec=json.loads(Path(source).read_text())
    width=max(spec['tape']['width_mm']);thick=max(spec['tape']['thickness_mm'])
    # Fold the width once at the two suspension passages. Use all tape stock.
    return {'tape':spec,'folded_width_mm':width/2,'folded_thickness_mm':2*thick,
      'post_tangent_width_mm':9,'post_outward_span_mm':[0,4],
      'post_height_mm':[2,13],'port_centres_tangent_mm':[-6,6],
      'port_width_mm':3,'port_height_mm':[4.6,11.6],'port_radial_mm':[-3,10],
      'wear_loop_bend_target_mm':1.3,'wear_loop_z_mm':8.1,
      'wear_loop_inner_radial_mm':-1,'wear_loop_tangent_width_mm':12,
      'wear_loop_overlap_mm':20,'physical_acceptance':'unmeasured'}


def native_shapes(shell,p,d,spec):
    import FreeCAD as App,Part
    import harness_route as geo
    result={};cuts=[];posts=[];probes=[];loops={};frames=[]
    def rectangle(w,l,h,x,y,z):return Part.makeBox(w,l,h,App.Vector(x-w/2,y-l/2,z))
    def place(shape,side):
        # Reversing the right slot tangent preserves its symmetric143degree
        #axis while making local+Y point radially outward on both sides.
        angle=-37 if side==1 else 37
        shape.rotate(App.Vector(),App.Vector(0,0,1),angle)
        shape.translate(App.Vector(side*d['suspension_x'],d['suspension_y'],0))
        return shape
    for i,side in enumerate((-1,1)):
        post=rectangle(9,4,11,0,2,2)
        probe=rectangle(7.8,2.8,6,0,1.6,5)
        posts.append(place(post,side));probes.append(place(probe,side))
        for x in [-6,6]:cuts.append(place(rectangle(3,13,7,x,3.5,4.6),side))
        R=spec['wear_loop_bend_target_mm'];inside=spec['wear_loop_inner_radial_mm'];span=spec['wear_loop_tangent_width_mm'];overlap=spec['wear_loop_overlap_mm']
        total=spec['tape']['tape']['wear_loop_cut_targets_mm'][i]
        # Rounded rectangle closed centreline plus its real sewn overlap uses
        # exactly the selected100mm blank, without a second mass owner.
        perimeter=total-overlap
        outside=(perimeter-(2*math.pi-8)*R)/2-span+inside
        z=spec['wear_loop_z_mm'];half=span/2
        points=[[0,outside,z],[-half,outside,z],[-half,inside,z],[half,inside,z],[half,outside,z],[0,outside,z]]
        segments=geo.segments(points,R);edges=[]
        for row in segments:
            ps=[App.Vector(*q) for q in row['points']]
            edges.append(Part.makeLine(*ps) if row['kind']=='line' else Part.Arc(*ps).toShape())
        path=Part.Wire(edges)
        if abs(path.Length-perimeter)>1e-6:raise ValueError('Wear loop stock length mismatch')
        w=spec['folded_width_mm'];t=spec['folded_thickness_mm']
        corners=[App.Vector(0,outside+a*t/2,z+b*w/2) for a,b in [(-1,-1),(1,-1),(1,1),(-1,1),(-1,-1)]]
        loop=path.makePipeShell([Part.Wire(Part.makePolygon(corners))],True,False)
        seam=rectangle(t,overlap,w,half+t,outside-R-overlap/2,z-w/2)
        loop=loop.fuse(seam).removeSplitter()
        if not loop.isValid() or len(loop.Solids)!=1:raise ValueError('Wear loop invalid or disconnected')
        loops['NecklaceWearLoop'+str(i)]=place(loop,side)
        # Each main end returns under the outer wear-loop bridge, then
        #converges into a real30mm two-layer sewn overlap above that bridge.
        rr=1.5;cy=outside;zz=z;ww=max(spec['tape']['tape']['width_mm']);tt=max(spec['tape']['tape']['thickness_mm'])
        bottom=zz-w/2-.6;join_z=16;overlap=spec['tape']['seams']['main_end_overlap_mm']
        left=[[0,cy-tt/2,join_z],[0,cy-tt/2,join_z-.5],[0,cy-rr,12],[0,cy-rr,bottom]]
        right=[[0,cy+rr,bottom],[0,cy+rr,12],[0,cy+tt/2,join_z-.5],[0,cy+tt/2,join_z]]
        edges=[]
        for row in geo.segments(left,1.3):
            ps=[App.Vector(*q) for q in row['points']]
            edges.append(Part.makeLine(*ps) if row['kind']=='line' else Part.Arc(*ps).toShape())
        edges.append(Part.Arc(App.Vector(*left[-1]),App.Vector(0,cy,bottom-rr),App.Vector(*right[0])).toShape())
        for row in geo.segments(right,1.3):
            ps=[App.Vector(*q) for q in row['points']]
            edges.append(Part.makeLine(*ps) if row['kind']=='line' else Part.Arc(*ps).toShape())
        path=Part.Wire(edges)
        cs=[App.Vector(xx*ww/2,cy-tt/2+yy*tt/2,join_z) for xx,yy in [(-1,-1),(1,-1),(1,1),(-1,1),(-1,-1)]]
        bend=path.makePipeShell([Part.Wire(Part.makePolygon(cs))],True,False)
        seam=rectangle(ww,2*tt,overlap,0,cy,join_z)
        stub=bend.fuse(seam).removeSplitter()
        if not stub.isValid() or len(stub.Solids)!=1:raise ValueError('Necklace main return invalid')
        loops['NecklaceAttachmentReturn'+str(i)]=place(stub,side)
        main_end_stock=path.Length+2*overlap
        frames.append({'side':side,'anchor_z_mm':z,'wear_loop_closed_centreline_mm':perimeter,'wear_loop_overlap_mm':overlap,'outer_radial_mm':outside,'main_end_stock_mm':main_end_stock,'main_overlap_mm':overlap,'free_span_entry_local_mm':[0,cy,join_z+overlap]})
    new=shell.fuse(Part.makeCompound(posts)).cut(Part.makeCompound(cuts))
    if not new.isValid() or len(new.Solids)!=1:raise ValueError('Suspension post cuts split the case')
    new.check(True)
    for probe in probes:
        if probe.cut(new).Volume>1e-6:raise ValueError('Suspension post cross-section lost')
    remaining=spec['tape']['tape']['main_cut_target_mm']-sum(f['main_end_stock_mm'] for f in frames)
    if remaining<=0:raise ValueError('Main sewn returns exceed selected strap stock')
    return {'free_main_span_target_mm':remaining,'case':new,'products':loops,'post_probes':probes,'frames':frames,
      'service_condition':'Keep free necklace span above the supported pendant and clear of the door/controls; both formed attachment regions remain fitted.',
      'physical_acceptance':'unmeasured'}
