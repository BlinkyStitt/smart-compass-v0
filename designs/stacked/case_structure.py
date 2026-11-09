"""Narrow non-optical wall and ribbed rear panel.

Minimum skins and ribs are fabrication dimensions. Strength, print quality,
sealing and suspension remain physical qualification items.
"""
import math

def lighten(shell,rear,parts,p,d):
    import FreeCAD as App,Part
    def cyl(r,h,z):return Part.makeCylinder(r,h,App.Vector(0,0,z))
    def ann(a,b,h,z):return cyl(b,h,z).cut(cyl(a,h,z))
    def box(w,l,h,x,y,z):return Part.makeBox(w,l,h,App.Vector(x-w/2,y-l/2,z))
    # Retain both original suspension blocks, including their insertion slots.
    lands=[box(20,20,11,side*d['suspension_x'],d['suspension_y'],2) for side in (-1,1)]
    original=shell
    lower=ann(91,101,10.5,2)
    for land in lands:lower=lower.cut(land)
    shell=shell.cut(lower)
    wall=ann(91,d['side_radius']-p['strip_thickness']/2,10.5,2)
    # Reapply the source nut access and suspension slots to the replacement
    # wall. These are the original fabrication dimensions.
    from hardware_spec import hexagon
    for i in range(6):
        x=d['rear_fastener_radius']*math.cos(i*math.tau/6)
        y=d['rear_fastener_radius']*math.sin(i*math.tau/6)
        points=[App.Vector(x+a,y+b,2) for a,b in hexagon(0,0,5.8)]
        face=Part.Face(Part.makePolygon(points+[points[0]]))
        wall=wall.cut(face.extrude(App.Vector(0,0,2.6)))
        wall=wall.cut(Part.makeCylinder(1.7,12,App.Vector(x,y,1.5)))
    for side in (-1,1):
        slot=box(12,4,11,0,0,2)
        slot.rotate(App.Vector(),App.Vector(0,0,1),143 if side==1 else 37)
        slot.translate(App.Vector(side*d['suspension_x'],d['suspension_y'],0))
        wall=wall.cut(slot)
    shell=shell.fuse(wall)
    # The transition carries the unchanged mirror seat and glass lip.
    transition_top=d['rear_bottom']-.8
    transition_h=transition_top-34
    inner=Part.makeCone(d['side_radius']-p['strip_thickness']/2-.5,d['mirror_seat_radius'],transition_h,App.Vector(0,0,34))
    shell=shell.cut(inner.cut(cyl(91,transition_h+.2,33.9)))
    # Keep one smooth outline in front of the side diffuser. The old full-depth
    # fastener lands cut black notches into the far side of the glowing ring.
    # Cover the LED-package tips with0.2mm radial margin; retain the nut lands
    # only where the pockets need their1.5mm floor below the front fasteners.
    frame_outer=d['side_radius']+p['strip_thickness']/2+p['ring_led_depth']+.2
    nut_land_bottom=d['front_z']-1-1.5
    frame_top=d['front_z']+p['front_mirror_thickness']
    trim=ann(frame_outer,101,frame_top-34,34)
    nut_lands=[]
    for i in range(6):
        land=box(9,9,frame_top-nut_land_bottom,d['front_fastener_radius'],0,nut_land_bottom)
        land.rotate(App.Vector(),App.Vector(0,0,1),i*60)
        nut_lands.append(shell.common(land))
        trim=trim.cut(land)
    shell=shell.cut(trim)
    for land in nut_lands:
        if land.cut(shell).Volume>1e-6:raise ValueError('Front nut land or pocket floor lost')
    outline_probe=ann(frame_outer,101,nut_land_bottom-34,34)
    if shell.common(outline_probe).Volume>1e-6:raise ValueError('Fastener land interrupts smooth side-band outline')
    # Three-sided board ledges retain the unchanged source clip and nut bosses.
    # Keep the continuous0.5mm PCB edge bearing and three24mm-wide radial ribs.
    ledge_tool=ann(84.5,91,2,p['circle_back_z']-2)
    for i in range(3):
        rib=box(24,24,2.2,85.5,0,p['circle_back_z']-2.1)
        rib.rotate(App.Vector(),App.Vector(0,0,1),i*120)
        ledge_tool=ledge_tool.cut(rib)
    shell=shell.cut(ledge_tool)
    # A1.5mm opaque carrier wall retains the unchanged strip seat radius.
    inner_r=d['side_radius']-p['strip_thickness']/2-1.5
    thin=ann(91,inner_r,32,2)
    for i in range(6):
        x=d['rear_fastener_radius']*math.cos(i*math.tau/6);y=d['rear_fastener_radius']*math.sin(i*math.tau/6)
        thin=thin.cut(Part.makeCylinder(4,33,App.Vector(x,y,1.5)))
    for land in lands:thin=thin.cut(land)
    thin=thin.cut(ann(82.4,94,2,p['circle_back_z']-2))
    shell=shell.cut(thin)
    # The two source contact-conduit returns cross the lower carrier near
    # the south edge. One bounded south relief clears their full outer shell,
    # wire diameter, main-fuse lacing and assembly margin.
    shell=shell.cut(box(140,22,12,-0,-72,1.9))
    # The outer switch-guard washer/nut stack sits atX93.5,Y-12.
    shell=shell.cut(box(9,9,5,93.5,-12,1.9))
    if not shell.isValid() or len(shell.Solids)!=1:raise ValueError('Lightened case disconnected or invalid')
    shell.check(True)
    suspension=[]
    for land in lands:
        missing=original.common(land).cut(shell).Volume
        if missing>1e-6:raise ValueError('Suspension material removed '+str(missing))
        suspension.append(missing)
    # Keep complete 2mm mounting faces. Grid pockets open toward electronics;
    # a continuous0.8mm external skin remains, with3mm ribs and3mm outer rim.
    retained=[(name,shell if name=='ElectronicsShell' else shape) for name,shape in parts if name!='RearCover']
    support_band=Part.makeBox(204,204,.1,App.Vector(-102,-102,1.95))
    feet=[]
    for name,shape in retained:
        if shape.BoundBox.ZMin<=2.05 and shape.BoundBox.ZMax>=1.95:
            footprint=shape.common(support_band)
            if not footprint.isNull() and footprint.Volume>1e-8:feet.append((name,footprint))
    # Partial pockets retain1.5mm around each actual mounting footprint.
    # Splitting disconnected source feet avoids reserving empty space between
    # two separate posts. No source-bearing surface may lose its full thickness.
    integrated_band=Part.makeBox(204,204,.05,App.Vector(-102,-102,2.01))
    integrated=rear.common(integrated_band)
    if not integrated.isNull() and integrated.Volume>1e-8:feet.append(('IntegratedRearMounts',integrated))
    keepouts=[]
    for name,foot in feet:
        for solid in foot.Solids:
            faces=[f for f in solid.Faces if f.BoundBox.ZLength<1e-7]
            if not faces:raise ValueError('Source foot has no planar contact section '+name)
            top=max(f.BoundBox.ZMin for f in faces)
            for face in faces:
                if abs(face.BoundBox.ZMin-top)>1e-7:continue
                # Offset the actual planar face, including its holes, rather
                #than filling a ring's empty centre with a bounding rectangle.
                expanded=face.makeOffset2D(1.5,join=0)
                if not expanded.isValid() or not expanded.Faces or face.cut(expanded).Area>1e-6:raise ValueError('Invalid source-foot clearance '+name)
                expanded.translate(App.Vector(0,0,-top))
                keep=expanded.extrude(App.Vector(0,0,2))
                if not keep.isValid() or not keep.Solids:raise ValueError('Invalid extruded source-foot clearance '+name)
                keepouts.append((name,keep))
    # A continuous0.8mm skin with24radial3mm ribs and one3mm circular
    #rib carries the unchanged mounting islands to the retained outer rim.
    # It prints flat on the skin; no removable support fills these pockets.
    spokes=[]
    for i in range(24):
        rib=box(97,3,2,48.5,0,0)
        rib.rotate(App.Vector(),App.Vector(0,0,1),i*15)
        spokes.append(rib)
    ribs=spokes[0].multiFuse(spokes[1:]+[ann(48.5,51.5,2,0)]).removeSplitter()
    if not ribs.isValid():raise ValueError('Rear radial rib network invalid')
    tool=cyl(97,1.2,.8).cut(ribs);kept=[]
    for name,keep in keepouts:
        if tool.common(keep).Volume>1e-8:
            tool=tool.cut(keep);kept.append({'mount':name})
    if not tool.isValid() or not tool.Solids:raise ValueError('Rear source-mount pockets invalid')
    pockets=[tool]
    print('STRUCTURE: radial rib pockets retain '+str(len(kept))+' actual mounting zones',flush=True)
    newrear=rear.cut(Part.makeCompound(pockets)).removeSplitter()
    if not newrear.isValid() or len(newrear.Solids)!=1:
        print('REAR FAILURE '+str({'valid':newrear.isValid(),'solids':[(t.Volume,t.isValid(),str(t.BoundBox)) for t in newrear.Solids]}),flush=True)
        raise ValueError('Ribbed rear panel disconnected or invalid')
    integrated_probe=integrated.copy();integrated_probe.translate(App.Vector(0,0,-.08))
    if integrated_probe.common(rear).Volume-integrated_probe.common(newrear).Volume>1e-6:raise ValueError('Integrated rear fixture loses full-thickness base bearing')
    # Every original fitted interface atZ2 must still have its complete surface.
    bearing=[]
    for name,shape in retained:
        for face in shape.Faces:
            bb=face.BoundBox
            if abs(bb.ZMin-2)<1e-6 and abs(bb.ZMax-2)<1e-6:
                test=face.extrude(App.Vector(0,0,-.02))
                old=test.common(rear).Volume;new=test.common(newrear).Volume
                if old-new>1e-6:raise ValueError('Rear mounting face lost '+name)
                if old>1e-7:bearing.append({'part':name,'preserved_contact_mm2':new/.02})
    return shell,newrear,{'scope':'Non-optical printed case structure; physical strength and print quality unmeasured',
      'lower_wall_radial_mm':[inner_r,d['side_radius']-p['strip_thickness']/2],
      'frame_inner_outer_mm':[d['mirror_seat_radius'],frame_outer],
      'front_nut_land_bottom_mm':nut_land_bottom,'front_nut_floor_mm':1.5,
      'front_nut_lands_preserved':len(nut_lands),
      'side_band_outline_obstruction_mm3':shell.common(outline_probe).Volume,
      'rear_skin_mm':.8,'rear_rib_mm':3,
      'rear_pocket_count':len(tool.Solids),'rear_rib_layout':{'radial_count':24,'angle_pitch_deg':15,'circular_radius_mm':50},'rear_grid_kept_for_mounts':kept,'bearing_faces':bearing,
      'suspension_removed_mm3':suspension,
      'case_saved_mm3':original.Volume-shell.Volume,'rear_saved_mm3':rear.Volume-newrear.Volume}
