"""Narrow non-optical wall and ribbed rear panel.

Minimum skins and ribs are fabrication dimensions. Strength, print quality,
sealing and suspension remain physical qualification items.
"""
import math


def flush_perimeter(shell,p,d):
    """Replace recessed walls with hollow walls at the diffuser's radius."""
    import FreeCAD as App,Part
    from hardware_spec import hexagon,nut_dimensions
    def cyl(r,h,z):return Part.makeCylinder(r,h,App.Vector(0,0,z))
    def ann(a,b,h,z):return cyl(b,h,z).cut(cyl(a,h,z))
    radius=d['case_radius'];inner=radius-1.5
    band_end=p['side_bottom_z']+d['side_height']
    top=d['front_z']+p['front_mirror_thickness']
    nut_floor=d['front_z']-2.5
    original=shell
    # Keep the six rear clamp columns, both suspension lands and the actual
    # boost-input pad backing. The other lower carrier material moves outward.
    lower=ann(d['rear_fastener_radius'],inner,p['side_bottom_z']-3.5,2)
    for side in (-1,1):
        lower=lower.cut(Part.makeBox(20,20,11,App.Vector(side*d['suspension_x']-10,d['suspension_y']-10,2)))
    for i in range(6):
        a=i*math.tau/6
        lower=lower.cut(Part.makeCylinder(4,11,App.Vector(d['rear_fastener_radius']*math.cos(a),d['rear_fastener_radius']*math.sin(a),2)))
    lower=lower.cut(Part.makeBox(8,6.6,11.7,App.Vector(-94,-13.7,2.1)))
    shell=shell.cut(lower).fuse(ann(inner,radius,p['side_bottom_z']-2,2))
    # Keep the inward strip's original backing radius. Two1mm walls separated
    # by an air space replace the solid cavity rim. The mirror collars and
    # nut-pocket floors retain their original material.
    backing_outer=d['mirror_seat_radius']+1
    shell=shell.fuse(ann(inner,radius,top-band_end,band_end))
    shell=shell.cut(ann(backing_outer,radius-1,nut_floor-d['rear_z'],d['rear_z']))
    backing=original.common(ann(d['mirror_seat_radius'],backing_outer,nut_floor-d['rear_z'],d['rear_z']))
    backing_missing=backing.cut(shell).Volume
    if backing_missing>1e-6:raise ValueError('Flush case loses inner LED strip backing')
    core_outer=d['side_radius']+p['strip_thickness']/2+p['ring_led_depth']+.2
    shell=shell.fuse(ann(core_outer-.4,radius,1.5,band_end))
    # The outer wall must not close the six radial nut-loading passages.
    flats,height=nut_dimensions('M2',pocket=True);ports=[]
    for i in range(6):
        angle=i*60;a=math.radians(angle)
        x=d['front_fastener_radius']*math.cos(a);y=d['front_fastener_radius']*math.sin(a)
        z=d['front_z']-1
        points=[App.Vector(x+dx,y+dy,z) for dx,dy in hexagon(0,0,flats)]
        pocket=Part.Face(Part.makePolygon(points+[points[0]])).extrude(App.Vector(0,0,height))
        entry=Part.makeBox(radius+1-d['front_fastener_radius'],flats,height,App.Vector(d['front_fastener_radius'],-flats/2,z))
        entry.rotate(App.Vector(),App.Vector(0,0,1),angle)
        ports.append(pocket.fuse(entry))
    access=Part.makeCompound(ports);shell=shell.cut(access)
    if not shell.isValid() or len(shell.Solids)!=1:raise ValueError('Flush case disconnected or invalid')
    # A continuous skin, rather than six projecting lands, defines the outline.
    # Only the documented nut-loading passages may interrupt the front skin.
    lower_skin=ann(radius-.05,radius,p['side_bottom_z']-2,2)
    front_skin=ann(radius-.05,radius,top-band_end,band_end).cut(access)
    missing=[probe.cut(shell).Volume for probe in (lower_skin,front_skin)]
    if max(missing)>1e-6:raise ValueError('Flush case has a recessed or broken outer skin '+str(missing))
    band=cyl(radius+1,d['side_height'],p['side_bottom_z'])
    added=shell.common(band).cut(original).Volume
    if added>1e-6:raise ValueError('Flush case adds opaque material inside the glow band')
    return shell,{'outer_radius_mm':radius,'wall_mm':1.5,
        'cavity_wall_mm':1.0,'inner_strip_backing_radial_mm':[d['mirror_seat_radius'],backing_outer],
        'inner_strip_backing_missing_mm3':backing_missing,
        'rear_wall_z_mm':[2,p['side_bottom_z']], 'front_wall_z_mm':[band_end,top],
        'missing_outer_skin_mm3':missing,'side_band_added_opaque_mm3':added,
        'front_nut_loading_passages':len(ports)}


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
    # Prepare the thin mirror-support core and short nut lands. The hollow
    # outer wall below joins them into one flush circular perimeter.
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
    if shell.common(outline_probe).Volume>1e-6:raise ValueError('Unused full-height front fastener material retained')
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
    shell,flush=flush_perimeter(shell,p,d)
    for land in nut_lands:
        if land.cut(shell).Volume>1e-6:raise ValueError('Flush wall loses front nut support')
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
      'front_mirror_collar_inner_outer_mm':[d['mirror_seat_radius'],frame_outer],
      'flush_perimeter':flush,
      'front_nut_land_bottom_mm':nut_land_bottom,'front_nut_floor_mm':1.5,
      'front_nut_lands_preserved':len(nut_lands),
      'rear_skin_mm':.8,'rear_rib_mm':3,
      'rear_pocket_count':len(tool.Solids),'rear_rib_layout':{'radial_count':24,'angle_pitch_deg':15,'circular_radius_mm':50},'rear_grid_kept_for_mounts':kept,'bearing_faces':bearing,
      'suspension_removed_mm3':suspension,
      'case_saved_mm3':original.Volume-shell.Volume,'rear_saved_mm3':rear.Volume-newrear.Volume}
