"""Five selected axial branch fuses on one removable printed carrier.

The drawing's nominal lead/body lengths are not guaranteed maxima. Completed
20x5x5mm insulated assemblies are specified gauge targets, still unmeasured.
"""
import itertools
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent
PARTS={'F_FIB':'Littelfuse 0251002.NRT1L, 2 A, axial',
       'F_AUX':'Littelfuse 0251.500NRT1L, 0.5 A, axial',
       **{name:'Littelfuse 0251001.NRT1L, 1 A, axial' for name in ('F_RING1','F_RING2','F_RING3')}}
FUSE_NAMES=frozenset('BranchFuse'+name for name in PARTS)
LACING_NAMES=frozenset('BranchFuseLacing'+str(i) for i in range(10))
HARDWARE_NAMES=frozenset('BranchFuseMount'+kind+str(i) for kind in ('Screw','Washer','Nut') for i in range(2))
PRINTED_PARTS=frozenset({'BranchFuseCarrier'})
PRODUCT_NAMES=FUSE_NAMES|LACING_NAMES|HARDWARE_NAMES|PRINTED_PARTS
REFERENCE_NAMES=frozenset(name+'Assembly' for name in FUSE_NAMES)
CHECK_NAMES=PRODUCT_NAMES|REFERENCE_NAMES


def geometry(design='narrow',electrical=None):
    if design not in ('wide','narrow'):raise ValueError('Choose a branch-fuse carrier design')
    electrical=json.loads((HERE/'electrical-design.json').read_text()) if electrical is None else electrical
    for name,part in PARTS.items():
        row=electrical['parts'][name]
        if (row['part']!=part or row.get('loaded_envelope_mm')!=[20,5,5]
                or row.get('source_revision')!='251 series, GK 18-Aug-2026, pp1-3; selected ratings0.5/1/2/4A'):
            raise ValueError('Review changed branch fuse/assembly space: '+name)
    return {'design':design,'rotation_deg':90 if design=='wide' else 0,
            'translation_xy_mm':[11,25] if design=='wide' else [0,0],
            'stations_mm':[[9,-5],[9,16]],'nut_entry_axes':[[0,-1],[0,1]],'nut_entry_length_mm':12,
            'floor_bottom_z_mm':16.75,'floor_thickness_mm':1.35,
            'fuses':{'F_FIB':[0,-3,0],'F_RING1':[0,5,0],'F_RING2':[0,13,0],
                     'F_RING3':[24.5,-7,90],'F_AUX':[32.5,-7,90]},
            'fuse_body_diameter_max_mm':2.8,'fuse_body_length_nominal_mm':7.11,
            'fuse_lead_diameter_nominal_mm':.64,'assembly_target_mm':[20,5,5],
            'stock_screw':'M2x20; finish17.5mm under head','stock_screw_tip_projection_mm':.4,
            'lacing':'Alpha Wire LC134 BK088; ten70mm blanks; separate square-knot spot ties',
            'insulation':'TE Raychem RNF-100-1/8-0-SP; recover before fitting PETG',
            'physical_acceptance':'unmeasured'}


def _place(shape,data):
    import FreeCAD as App
    shape.rotate(App.Vector(),App.Vector(0,0,1),data['rotation_deg'])
    shape.translate(App.Vector(*data['translation_xy_mm'],0))
    return shape


def ports(design='narrow'):
    """Specified insulated-joint exits; full external wire routes remain open."""
    data=geometry(design);angle=math.radians(data['rotation_deg']);c,s=math.cos(angle),math.sin(angle);dx,dy=data['translation_xy_mm'];out={}
    for name,(x,y,rotation) in data['fuses'].items():
        a=math.radians(rotation)
        for pin,t in (('1',0),('2',20)):
            px,py=x+t*math.cos(a),y+t*math.sin(a)
            out[name+'.'+pin]=[dx+c*px-s*py,dy+s*px+c*py,20.6]
    return out


def native_shapes(design='narrow'):
    import FreeCAD as App
    import Part
    from fastener_access import native_tools
    from hardware_spec import hexagon,nut_dimensions,WASHERS
    data=geometry(design)
    def box(x0,x1,y0,y1,z0,z1):return Part.makeBox(x1-x0,y1-y0,z1-z0,App.Vector(x0,y0,z0))
    def cylinder(r,h,x,y,z):return Part.makeCylinder(r,h,App.Vector(x,y,z))
    floor=box(-2.25,36.35,-8.35,16.85,16.75,18.1)
    products={};additions=[];cuts=[];paths=[];probes=[]
    flat,nh=nut_dimensions('M2');pflat,ph=nut_dimensions('M2',pocket=True)
    for i,(x,y) in enumerate(data['stations_mm']):
        floor=floor.fuse(cylinder(3.1,16.1,x,y,2))
        points=[App.Vector(x+a,y+b,14.85) for a,b in hexagon(0,0,pflat)]
        pocket=Part.Face(Part.makePolygon(points+[points[0]])).extrude(App.Vector(0,0,ph))
        entry,path=native_tools(x,y,14.85,data['nut_entry_axes'][i],length=12);paths.append(path)
        # Stop the shaft bore below the floor top: retain the insulating roof
        # above the finished screw, rather than expose its tip to a fuse.
        floor=floor.cut(pocket.fuse(entry)).cut(cylinder(1.1,15.35,x,y,1.9))
        additions.append(cylinder(3.1,2,x,y,0));cuts.append(cylinder(1.1,2.2,x,y,-.1))
        w=WASHERS['M2'];wz=-w['thickness']
        if abs(wz+.35)>1e-8:raise ValueError('Review changed M2 rear washer stack')
        products['BranchFuseMountScrew'+str(i)]=cylinder(1,17.5,x,y,wz).fuse(cylinder(1.9,2,x,y,wz-2))
        products['BranchFuseMountWasher'+str(i)]=cylinder(w['od']/2,w['thickness'],x,y,wz).cut(cylinder(w['id']/2,w['thickness'],x,y,wz))
        points=[App.Vector(x+a,y+b,15.15) for a,b in hexagon(0,0,flat)]
        products['BranchFuseMountNut'+str(i)]=Part.Face(Part.makePolygon(points+[points[0]])).extrude(App.Vector(0,0,nh)).cut(cylinder(1.1,nh+.2,x,y,15.05))
        probes.append(cylinder(3.1,.05,x,y,1.95).cut(cylinder(1.1,.1,x,y,1.925)))
    for index,(name,(x,y,rotation)) in enumerate(data['fuses'].items()):
        body=Part.makeCylinder(1.4,7.11,App.Vector(6.445,0,20.6),App.Vector(1,0,0))
        body=body.fuse(Part.makeCylinder(.32,20,App.Vector(0,0,20.6),App.Vector(1,0,0))).removeSplitter()
        target=box(0,20,-2.5,2.5,18.1,23.1)
        ref=target.cut(body).removeSplitter()
        for shape in (body,ref):shape.rotate(App.Vector(),App.Vector(0,0,1),rotation);shape.translate(App.Vector(x,y,0))
        products['BranchFuse'+name]=body;products['BranchFuse'+name+'Assembly']=ref
        for j,t in enumerate((2,18)):
            outer=box(t-.85,t+.85,-3,3,16.25,23.6);inner=box(t-1,t+1,-2.5,2.5,16.75,23.1)
            loop=outer.cut(inner)
            # Each row's knot stays on its positive side. Its2.2mm side
            # space is checked against adjacent rows and neighbouring fuses.
            knot=(box(t-2,t+2,2.6,4.8,20,22) if rotation==0 else box(t-2,t+2,-4.8,-2.6,20,22))
            tie=loop.fuse(knot).removeSplitter()
            tie.rotate(App.Vector(),App.Vector(0,0,1),rotation);tie.translate(App.Vector(x,y,0))
            products['BranchFuseLacing'+str(2*index+j)]=tie
            for a,b in ((-3.15,-2.35),(2.35,3.15)):
                slot=box(t-1.05,t+1.05,a,b,16.65,18.2)
                slot.rotate(App.Vector(),App.Vector(0,0,1),rotation);slot.translate(App.Vector(x,y,0));floor=floor.cut(slot)
    products['BranchFuseCarrier']=floor.removeSplitter()
    result={**products,'rear_addition':Part.makeCompound(additions),'rear_cutout':Part.makeCompound(cuts),'mount_probes':probes,'nut_paths':paths}
    for value in result.values():
        for shape in value if isinstance(value,list) else [value]:_place(shape,data)
    return result


def native_check(shapes,design='narrow'):
    import FreeCAD as App
    import Part
    from fastener_access import native_check_paths
    from solid_clearance import box_distance
    from blackpill_mount import _top_contact
    data=geometry(design)
    if set(shapes)-{'rear_addition','rear_cutout','mount_probes','nut_paths'}!=CHECK_NAMES:raise ValueError('Incomplete branch-fuse carrier census')
    for name in CHECK_NAMES:
        if not shapes[name].isValid() or len(shapes[name].Solids)!=1:raise ValueError('Invalid/disconnected branch-fuse part: '+name)
    rear=_place(Part.makeBox(60,60,2,App.Vector(-15,-20,0)),data).fuse(shapes['rear_addition']).cut(shapes['rear_cutout']).removeSplitter()
    all_shapes={**{name:shapes[name] for name in CHECK_NAMES},'RearInterface':rear}
    for a,b in itertools.combinations(sorted(all_shapes),2):
        if box_distance(all_shapes[a].BoundBox,all_shapes[b].BoundBox)>1e-6:continue
        volume=all_shapes[a].common(all_shapes[b]).Volume
        if volume>1e-6:raise ValueError('Branch-fuse interference '+a+'/'+b+': '+str(volume))
    if len(shapes['mount_probes'])!=2:raise ValueError('Two branch-fuse mounting bearing probes are required')
    for probe in shapes['mount_probes']:
        if probe.cut(rear).Volume>1e-6:raise ValueError('Branch-fuse rear bearing is incomplete')
        expected,actual=_top_contact(probe,shapes['BranchFuseCarrier'])
        if expected-actual>1e-6:raise ValueError('Branch-fuse carrier lacks full rear bearing')
    tips=[]
    for i in range(2):
        screw=shapes['BranchFuseMountScrew'+str(i)];nut=shapes['BranchFuseMountNut'+str(i)]
        # This carrier uses +Z screws. The nut must reach the floor underside.
        tip=screw.BoundBox.ZMax-nut.BoundBox.ZMax;tips.append(tip)
        if not .2<=tip<=.8:raise ValueError('Branch-fuse screw lacks nut engagement or short projection')
        if abs(nut.BoundBox.ZMax-16.75)>1e-7:raise ValueError('Branch-fuse nut is not seated against its pocket roof')
        faces=[f for f in nut.Faces if f.BoundBox.ZLength<1e-7 and abs(f.BoundBox.ZMax-16.75)<1e-7]
        if sum(f.Area-f.common(shapes['BranchFuseCarrier']).Area for f in faces)>1e-6:
            raise ValueError('Branch-fuse nut lacks full pocket-roof bearing')
    native_check_paths(shapes['nut_paths'],shapes['BranchFuseCarrier'],2)
    native_check_paths(shapes['nut_paths'],rear,2)
    return {'scope':'branch-fuse carrier component study','design':design,'physical_products':len(PRODUCT_NAMES),'references':len(REFERENCE_NAMES),
            'selected_fuses':dict(PARTS),'ports_mm':ports(design),'screw_tip_projection_mm':tips,
            'roof_above_screw_tip_mm':18.1-max(shapes['BranchFuseMountScrew'+str(i)].BoundBox.ZMax for i in range(2)),
            'full_installed_harness':'not checked','physical_acceptance':'unmeasured'}
