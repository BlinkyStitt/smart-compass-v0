"""Source-sized horizontal capacitor and a removable insulated clamshell.

All fits are assembly targets. Actual retention, shim fit, joints, temperatures
and pressure-valve clearance require physical inspection and qualification.
"""
import hashlib
import itertools
import json
import math
from pathlib import Path
HERE=Path(__file__).resolve().parent
SOURCE='sources/capacitor-fr-a'
FILES={'panasonic-fr-a-2025.pdf':'47cf18461482e03270f72e475f855080e11e2154e3f343f735e5cb0e61e27df7',
       'panasonic-safety-2025.pdf':'2e7d642ee8c1728bbde3ad9182f079f84e70620ea6a2c1cd7b611770b98f4347',
       'rs-pro-770787.pdf':'f537df569a389be7bdc669412c89fe85ba1491f49d9214e0cb86326d775b5967'}
PRODUCT_NAMES=frozenset({'BulkCapacitor','CapacitorCover','CapacitorUpperShim','CapacitorLowerShim'}|
                       {'Capacitor'+kind+str(i) for kind in ('Screw','Nut') for i in range(2)})
REFERENCE_NAMES=frozenset({'CapacitorVentClearance','CapacitorPositiveLeadVariation','CapacitorNegativeLeadVariation'})
CHECK_NAMES=PRODUCT_NAMES|REFERENCE_NAMES


def definition():return json.loads((HERE/'electrical-design.json').read_text())['parts']['C_OUT']


def geometry(part=None,directory=HERE):
    part=definition() if part is None else part
    expected={'part':'Panasonic EEUFR1A102, 1000 uF 10 V +/-20%, 10 x 16 mm body',
              'source':'https://industrial.panasonic.com/ww/products/pt/aluminum-cap-lead/models/EEUFR1A102',
              'source_record':SOURCE+'/index.json','body_diameter_mm':[9.5,10.5],
              'body_length_mm':[14.5,17.5],'lead_diameter_mm':[.55,.65],
              'lead_pitch_mm':[4.5,5.5],'minimum_vent_clearance_mm':2,
              'mount':{'shim_part':'RS PRO770-787 white polyester shim stock',
                       'shim_source':'https://uk.rs-online.com/web/p/plastic-shims/0770787','shim_nominal_mm':.25}}
    if any(part.get(key)!=value for key,value in expected.items()):raise ValueError('Retain the selected capacitor, source dimensions and pressure-valve clearance')
    index={row['file']:row for row in json.loads((Path(directory)/SOURCE/'index.json').read_text())}
    for name,digest in FILES.items():
        raw=(Path(directory)/SOURCE/name).read_bytes();row=index.get(name,{})
        if row.get('sha256')!=digest or row.get('bytes')!=len(raw) or hashlib.sha256(raw).hexdigest()!=digest:
            raise ValueError('Capacitor primary source hash mismatch: '+name)
    # These are defined assembly targets, not further manufacturer limits.
    return {'axis_z_mm':8.85,'can_start_y_mm':-5,'can_end_y_mm':12.5,
            'finished_lead_mm':9.5,'vent_target_mm':2.5,'maximum_accepted_axial_motion_mm':.25,
            'lead_channel_radius_mm':.8,'joint_channel_radius_mm':1.6,
            'shim_nominal_mm':.25,
            'profiles':{'wide':{'post_xy_mm':[[-10,8.5],[10,8.5]],'floor_width_mm':13.7,
                                'entry_axes':[[0,-1],[0,-1]],'entry_lengths_mm':[9,9],
                                'cover_ear_thickness_mm':1.35,'finished_screw_length_mm':6.6},
                        'narrow':{'post_xy_mm':[[.5,-9.5],[4.25,19]],'floor_width_mm':7,
                                  'entry_axes':[[1,0],[1,0]],'entry_lengths_mm':[12,9],
                                  'cover_ear_thickness_mm':2.35,'finished_screw_length_mm':7.6}},
            'post_radius_mm':3.9,'post_flat_width_mm':7.2}


def mounting(design,part=None):
    data=geometry(part)
    if design not in data['profiles']:raise ValueError('Choose the Wide or Narrow capacitor holder')
    return {**data,**data['profiles'][design],'selected_design':design}


def native_shapes(design,part=None):
    import FreeCAD as App
    import Part
    from hardware_spec import nut_dimensions,hexagon
    from fastener_access import native_tools
    data=mounting(design,part);z=data['axis_z_mm'];ear_h=data['cover_ear_thickness_mm'];radius=data['post_radius_mm']
    def box(w,l,h,x,y,bottom):return Part.makeBox(w,l,h,App.Vector(x-w/2,y-l/2,bottom))
    def cylinder(r,h,x,y,bottom):return Part.makeCylinder(r,h,App.Vector(x,y,bottom))
    def post(h,x,y,bottom):
        return cylinder(radius,h,x,y,bottom).common(box(data['post_flat_width_mm'],2*radius,h,x,y,bottom))
    def axial(r,start,end,x=0):return Part.makeCylinder(r,end-start,App.Vector(x,start,z),App.Vector(0,1,0))
    outer=axial(6.85,-15.5,15.5)
    cavity=axial(5.5,-5.25,15.6)
    for x in (-2.5,2.5):cavity=cavity.fuse(axial(.8,-15.6,-5.15,x)).fuse(axial(1.6,-14.5,-10.5,x))
    shell=outer.cut(cavity)
    lowbox=box(40,40,z,-0.,0,0);highbox=box(40,40,20,0,0,z)
    lower=shell.common(lowbox).fuse(box(data['floor_width_mm'],31,3.35,0,0,0)).cut(cavity)
    if design=='wide':lower=lower.fuse(box(27.6,7.6,3.35,0,8.5,0)).cut(cavity)
    upper=shell.common(highbox)
    products={};cuts=[];probes=[];nut_paths=[]
    flat,nh=nut_dimensions('M2');pflat,ph=nut_dimensions('M2',pocket=True)
    for i,(x,y) in enumerate(data['post_xy_mm']):
        lower=lower.fuse(post(z,x,y,0))
        side=-1 if x<0 else 1
        ear=post(ear_h,x,y,z)
        if design=='wide':ear=ear.fuse(box(4,4,ear_h,side*8,y,z))
        elif i==1:ear=ear.fuse(box(1.35,5,ear_h,6.175,16.5,z))
        upper=upper.fuse(ear)
        nz=4.0;vertices=[App.Vector(x+a,y+b,nz) for a,b in hexagon(0,0,pflat)]
        pocket=Part.Face(Part.makePolygon(vertices+[vertices[0]])).extrude(App.Vector(0,0,ph))
        entry,path=native_tools(x,y,nz,data['entry_axes'][i],data['entry_lengths_mm'][i]);nut_paths.append(path)
        seat=z+ear_h;length=data['finished_screw_length_mm']
        bore=cylinder(1.1,seat-3.4+.2,x,y,3.4);cuts.extend((pocket,entry,bore))
        # Counterbore the compact interior screw so its head does not occupy
        # the solid roof. Its raised seat leaves1.55mm above the lead channel.
        upper=upper.cut(bore).cut(cylinder(2.15,20-seat,x,y,seat))
        products['CapacitorScrew'+str(i)]=cylinder(1,length,x,y,seat-length).fuse(cylinder(1.9,2,x,y,seat))
        vertices=[App.Vector(x+a,y+b,nz) for a,b in hexagon(0,0,flat)]
        products['CapacitorNut'+str(i)]=Part.Face(Part.makePolygon(vertices+[vertices[0]])).extrude(App.Vector(0,0,nh)).cut(cylinder(1.1,nh+.2,x,y,nz-.1))
        probes.append(post(.05,x,y,z-.05).cut(cylinder(1.1,.1,x,y,z-.075)).cut(cavity))
    # Recut both halves after adding the posts. The compact lead-side post
    # surrounds the two separate lead channels without filling either one.
    cutout=Part.makeCompound(cuts);lower=lower.cut(cutout).cut(cavity).removeSplitter()
    upper=upper.cut(cavity)
    can=axial(5.25,-5,12.5)
    for name,x in (('Positive',-2.5),('Negative',2.5)):
        can=can.fuse(axial(.325,-14.5,-5,x))
        products['Capacitor'+name+'LeadVariation']=axial(.575,-14.5,-5,x).cut(axial(.325,-14.6,-4.9,x))
    shim=axial(5.5,1.5,7.5).cut(axial(5.25,1.4,7.6))
    products.update(BulkCapacitor=can.removeSplitter(),CapacitorCover=upper.removeSplitter(),
                    CapacitorUpperShim=shim.common(highbox),CapacitorLowerShim=shim.common(lowbox),
                    CapacitorVentClearance=axial(5.25,12.5,15.0))
    return {**products,'rear_addition':lower,'rear_cutout':cutout,'mount_probes':probes,'nut_paths':nut_paths,'targets':data}


def native_check(shapes,design,part=None):
    import FreeCAD as App
    import Part
    from solid_clearance import box_distance
    data=mounting(design,part)
    if shapes.get('targets')!=data:raise ValueError('Capacitor fixture differs from its selected design')
    if set(shapes)-{'rear_addition','rear_cutout','mount_probes','nut_paths','targets'}!=CHECK_NAMES:raise ValueError('Capacitor fixture census is incomplete')
    for name in CHECK_NAMES|{'rear_addition'}:
        if not shapes[name].isValid() or len(shapes[name].Solids)!=1:raise ValueError('Capacitor fixture is invalid or detached: '+name)
    rear=Part.makeBox(32,36,2,App.Vector(-16,-18,0)).fuse(shapes['rear_addition']).cut(shapes['rear_cutout']).removeSplitter()
    if not rear.isValid() or len(rear.Solids)!=1:raise ValueError('Capacitor holder does not connect to the rear interface')
    items={**{name:shapes[name] for name in CHECK_NAMES},'RearInterface':rear}
    for a,b in itertools.combinations(sorted(items),2):
        if box_distance(items[a].BoundBox,items[b].BoundBox)>1e-6:continue
        volume=items[a].common(items[b]).Volume
        if volume>1e-6:raise ValueError('Capacitor fixture interference '+a+'/'+b+': '+str(volume))
    for probe in shapes['mount_probes']:
        if probe.cut(rear).Volume>1e-6:raise ValueError('Capacitor cover has incomplete hard-stop bearing')
    tips=[shapes['CapacitorNut'+str(i)].BoundBox.ZMin-shapes['CapacitorScrew'+str(i)].BoundBox.ZMin for i in range(2)]
    if any(not .2<=tip<=.8 for tip in tips):raise ValueError('Capacitor screw must engage the full nut with0.2..0.8mm tip projection')
    # A nominal support probe is separate from the zero-interference check.
    moved=shapes['BulkCapacitor'].copy();moved.translate(App.Vector(0,0,-.05))
    support=moved.common(shapes['CapacitorLowerShim']).Volume/.05
    if support<5:raise ValueError('Capacitor floats above the specified lower shim')
    if data['vent_target_mm']-data['maximum_accepted_axial_motion_mm']<2:raise ValueError('Capacitor pressure-valve margin is insufficient')
    from fastener_access import native_check_paths
    native_check_paths(shapes.get('nut_paths'),rear,2)
    return {'scope':'source-sized capacitor holder component only','physical_products':len(PRODUCT_NAMES),'references':len(REFERENCE_NAMES),
            'nominal_support_probe_mm2':support,'screw_tip_projection_mm':tips,'targets':data,
            'physical_acceptance':'unmeasured','installed_assembly':'not checked','fitted_joints':'not checked'}
