"""Package the selected narrow prototype and draw its actual battery service states."""
import hashlib,html,json,zipfile,math,itertools
from pathlib import Path
import prints
from solid_clearance import bounds as shape_bounds

CAPTIONS=[
 ('Support and OFF','Support the pendant on a padded surface. Put S1 fully OFF. Disconnect all external power.'),
 ('Open captive door','Release the door catch and swing to its stop. The independent keeper still retains the cell.'),
 ('Release keeper','Hold the cell. Rotate the keeper. Pull the ribbon; do not pull any wire.'),
 ('Remove deliberately','Shift toward the negative contact, then withdraw through the rear opening. Inspect wrapper and end insulator.'),
 ('Insert one compatible cell','Use one protected XTAR21700 6000mAh button-top. Follow the permanent + and - marks. Keep the ribbon clear.'),
 ('Latch and START','Close the keeper and door. Check full catch engagement. Select ON and press START. Light does not prove navigation readiness.'),
]


def rotation_bounds(shape,origin,axis,last):
    """Conservative continuous bounds from its enclosing box and displacement."""
    bb=shape_bounds(shape);corners=list(itertools.product((bb.XMin,bb.XMax),(bb.YMin,bb.YMax),(bb.ZMin,bb.ZMax)))
    moving=[i for i in range(3) if i!=axis];radius=max(math.hypot(*(p[i]-origin[i] for i in moving)) for p in corners)
    count=max(1,math.ceil(abs(last)/.25));pad=2*radius*math.sin(math.radians(abs(last)/count)/4);points=[]
    for step in range(count+1):
        angle=math.radians(last*step/count);c,t=math.cos(angle),math.sin(angle)
        for point in corners:
            x,y,z=[a-b for a,b in zip(point,origin)]
            rotated=(x,c*y-t*z,t*y+c*z) if axis==0 else (c*x-t*y,t*x+c*y,z) if axis==2 else None
            if rotated is None:raise ValueError('Review this service rotation axis')
            points.append([a+b for a,b in zip(rotated,origin)])
    return [[min(p[i] for p in points)-(pad if i!=axis else 0),max(p[i] for p in points)+(pad if i!=axis else 0)] for i in range(3)]


def native_guide(out,spec,shapes,installed,control_probes):
    """Illustration only. Native continuous sweeps provide the fit evidence."""
    import FreeCAD as App,Part,battery_access
    out=Path(out)
    opened=battery_access.door_at_open_stop(spec,shapes)
    keeper=shapes['BatteryKeeper'].copy();keeper.rotate(App.Vector(*shapes['keeper_axis']),App.Vector(0,0,1),spec['keeper']['open_angle_deg'])
    cx,cy=spec['designs']['narrow']['cell_centre_xy_mm'];length=spec['cell']['length_mm'][1]
    stop=cx-sum(spec['contact']['unloaded_tip_gap_mm'])/4-sum(spec['contact']['negative_stop_compression_mm'])/2
    shift=stop+length/2-cx
    removed=shapes['BatteryCell'].copy();removed.translate(App.Vector(shift,0,-spec['removal']['withdrawal_mm']))
    backgrounds={name:shape for name,shape in installed if name in {'RearCover','SwitchGuard','PowerDisconnect','StartBezel','StartSwitch'}}
    all_installed=list(installed)
    def bounds(shape):
        box=shape_bounds(shape)
        return [[getattr(box,axis+'Min'),getattr(box,axis+'Max')] for axis in 'XYZ']
    closed=[bounds(shape) for _,shape in all_installed]
    released=opened.copy();released.rotate(App.Vector(*shapes['hinge_axis']),App.Vector(1,0,0),spec['door']['open_angle_deg'])
    service_bounds=closed+[bounds(removed),rotation_bounds(released,shapes['hinge_axis'],0,-spec['door']['open_angle_deg']),rotation_bounds(shapes['BatteryKeeper'],shapes['keeper_axis'],2,spec['keeper']['open_angle_deg'])]
    finger=Part.makeCylinder(spec['removal']['finger_radius_mm'],45,App.Vector(cx,cy,spec['removal']['finger_start_z_mm']-30))
    service_bounds += [bounds(finger),*[bounds(probe) for probe in control_probes.values()]]
    union=[[min(row[i][0] for row in service_bounds),max(row[i][1] for row in service_bounds)] for i in range(3)]
    clearance={'minimum_mm':[row[0] for row in union],'maximum_mm':[row[1] for row in union],
               'width_height_depth_mm':[row[1]-row[0] for row in union],
               'cell_withdrawal_mm':spec['removal']['withdrawal_mm'],'door_open_deg':spec['door']['open_angle_deg'],
               'basis':'Conservative continuous nominal CAD bounding box: closed assembly, released door and keeper sweeps, full cell withdrawal and specified finger approaches. This is not a supplied tolerance or full human-hand bound; physical access remains unmeasured.'}
    frames=[];panels=[]
    colours={'BatteryCell':'#854694','BatteryDoor':'#555b65','BatteryKeeper':'#d5a13c','BatteryCradle':'#d3d6dc','BatteryContactP':'#be6060','BatteryContactN':'#506dbe'}
    for index,(title,caption) in enumerate(CAPTIONS):
        door=opened if index in [1,2,3,4] else shapes['BatteryDoor']
        keep=keeper if index in [2,3,4] else shapes['BatteryKeeper']
        cell=removed if index==3 else shapes['BatteryCell']
        parts={**backgrounds,'BatteryCradle':shapes['BatteryCradle'],'BatteryContactP':shapes['BatteryContactP'],'BatteryContactN':shapes['BatteryContactN'],'BatteryCell':cell,'BatteryKeeper':keep,'BatteryDoor':door}
        # Rear orthographic view with a small depth offset. Draw back-to-front
        # from the real mm meshes; this is not an invented silhouette.
        faces=[]
        for name,shape in parts.items():
            vertices,triangles=shape.tessellate(.8)
            for tri in triangles:
                points=[vertices[i] for i in tri];depth=sum(p.z for p in points)/3
                xy=[(151-.98*p.x+.2*p.z,124-.98*p.y+.17*p.z) for p in points]
                faces.append((depth,name,xy))
        drawing=[]
        for _,name,xy in sorted(faces,reverse=True):
            points=' '.join(f'{x:.3f},{y:.3f}' for x,y in xy)
            colour=colours.get(name,'#c6c8cf');drawing.append(f'<polygon points="{points}" fill="{colour}" stroke="{colour}" stroke-width="0.15"/>')
        col,row=index%3,index//3;x0,y0=col*320,row*360
        # Wrapped text uses explicit short lines to keep the standalone SVG
        # readable in print services and ordinary browsers.
        words=caption.split();lines=[];line=''
        for word in words:
            if len(line)+len(word)>44:lines.append(line);line=word
            else:line+=(' ' if line else '')+word
        if line:lines.append(line)
        text=''.join(f'<tspan x="12" dy="17">{html.escape(line)}</tspan>' for line in lines)
        panels.append(f'<g transform="translate({x0},{y0})"><rect x="4" y="4" width="312" height="352" rx="8" fill="#fff" stroke="#888"/><text x="12" y="24" font-size="15" font-weight="bold">{index+1}. {html.escape(title)}</text><g transform="translate(0,30)">{"".join(drawing)}</g><text x="12" y="270" font-size="12">{text}</text></g>')
        frames.append({'index':index+1,'title':title,'caption':caption,'geometry_parts':sorted(parts),'cell_translation_mm':[shift,0,-spec['removal']['withdrawal_mm']] if index==3 else [0,0,0]})
    svg='<svg xmlns="http://www.w3.org/2000/svg" width="960" height="790" viewBox="0 0 960 790"><title>Narrow prototype battery service</title><rect width="960" height="790" fill="#eee"/><g font-family="sans-serif">'+''.join(panels)+'<text x="12" y="748" font-size="13">Digital prototype. Physical insulation, retention, reset timing and temperatures are unmeasured.</text><text x="12" y="770" font-size="13">Charge the removed cell off-body. Stop after damage, heat or repeated darkness; do not bypass protection.</text></g></svg>'
    (out/'service-guide.svg').write_text(svg)
    (out/'service-guide.json').write_text(json.dumps({'scope':'Actual narrow CAD service poses; illustrations do not prove continuous clearance or physical operation','frames':frames,'service_clearance':clearance,'physical_acceptance':'unmeasured'},indent=2)+'\n')

    return clearance


def package(out,parts,spec,docs):
    out=Path(out);files={}
    for row,name,material in prints.jobs(parts,spec):
        stage='01-SAMPLES' if row['file'] in {p['file'] for p in parts['fit_samples']} else '02-FULL-PARTS'
        files[f'{stage}/{material}/{name}']=(out/name).read_bytes()
        files[f'03-STL-ALTERNATIVES/{stage}/{row["file"]}']=(out/row['file']).read_bytes()
    for name in ['stacked-fibonacci.step','service-guide.svg','assembly-dimensions.svg','service-guide.json','parts.json','inventory.md','case-structure-check.json','necklace-fit-check.json','end-support-check.json','loom-check.json','installed-fit-check.json','antenna-service-check.json','slicing-check.json','night-mannequin.png','night-front.png','night-side.png','exploded.png']:
        files['04-REFERENCE/'+name]=(out/name).read_bytes()
    for path in docs:files['04-REFERENCE/'+Path(path).name]=Path(path).read_bytes()
    files['README.txt']=('NARROW PROTOTYPE ONLY\nPrint the selected material samples first. Inspect fit before full parts. Choose glow OR silver ring projects; do not install both. Optical rings and their samples stay upright without supports. Selected structural projects use removable build-plate supports; read print-layout.json. Remove supports and brims before assembly or weighing. Inspect bearing faces, bores, contact guides and wire/lacing channels. Do not cut retaining lips or integrated fixtures. Stop if features are incomplete or damaged. Support removal, fit and strength remain unmeasured.\nProfiles preserve the reviewed settings. STL files are alternatives. Samples, waste, supports, tools and spares do not enter worn mass.\nThis package is a digital prototype, not a purchase or physical acceptance. Use only the documented module and protected cell revisions. Every physical qualification outcome remains unmeasured. Read battery-access.md, qualification-plan.md and the service guide before assembly or testing.\n').encode()
    manifest={name:hashlib.sha256(data).hexdigest() for name,data in sorted(files.items())}
    files['MANIFEST.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    with zipfile.ZipFile(out/'prototype-service.zip','w',compression=zipfile.ZIP_DEFLATED) as archive:
        for name,data in sorted(files.items()):archive.writestr(name,data)
    with zipfile.ZipFile(out/'prototype-service.zip') as archive:
        if set(archive.namelist())!=set(files) or archive.testzip():raise ValueError('Incomplete narrow service archive')
        for name,digest in manifest.items():
            if hashlib.sha256(archive.read(name)).hexdigest()!=digest:raise ValueError('Narrow service archive changed '+name)


def native_dimensions(out,installed,parts):
    """Draw real external CAD products at one front/side scale, with raw bounds."""
    out=Path(out);scale=2.0;origin_y=310;front_x=270;side_x=630
    product={row['name']:row for row in parts['products']}
    shapes=[(name,shape) for name,shape in installed if product[name]['group']=='Manufactured' or name in {'FibonacciPCB','CircleLEDs','BatteryCell','PowerDisconnect','SwitchGuard'} or name.startswith('Necklace')]
    dims=parts['dimensions_mm'];clearance=parts['service_clearance'];zmin=dims['rear_min_z'];cg=parts['balance'];fragments=[]
    def line(x1,y1,x2,y2,label,ytext):
        return f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" stroke="#222" marker-start="url(#arrow)" marker-end="url(#arrow)"/><text x="{(x1+x2)/2:.3f}" y="{ytext:.3f}" text-anchor="middle">{html.escape(label)}</text>'
    for view in ['front','side']:
        faces=[]
        for name,shape in shapes:
            vertices,triangles=shape.tessellate(.8)
            for tri in triangles:
                ps=[vertices[i] for i in tri]
                if view=='front':xy=[(front_x+scale*p.x,origin_y-scale*p.y) for p in ps];depth=sum(p.z for p in ps)
                else:xy=[(side_x+scale*(p.z-zmin),origin_y-scale*p.y) for p in ps];depth=-sum(p.x for p in ps)
                faces.append((depth,name,xy))
        for _,name,xy in sorted(faces):
            colour='#b5cda3' if name in ['SideDiffuser','InnerDiffuser'] else '#8f70ab' if name=='BatteryCell' else '#fff0a6' if name=='CircleLEDs' else '#444b54'
            opacity='.2' if name in ['FrontMirror','RearCouplingMirror'] else '1'
            points=' '.join(f'{x:.3f},{y:.3f}' for x,y in xy)
            fragments.append(f'<polygon points="{points}" fill="{colour}" fill-opacity="{opacity}" stroke="{colour}" stroke-opacity="{opacity}" stroke-width=".12"/>')
        if view=='front':x=front_x+scale*cg['centre_mm'][0];y=origin_y-scale*cg['centre_mm'][1];axis=0
        else:x=side_x+scale*(cg['centre_mm'][2]-zmin);y=origin_y-scale*cg['centre_mm'][1];axis=2
        ranges=cg['centre_mass_allowance_range_mm'];left=(front_x if axis==0 else side_x-scale*zmin)+scale*ranges[axis][0]
        top=origin_y-scale*ranges[1][1]
        fragments.append(f'<rect x="{left:.3f}" y="{top:.3f}" width="{scale*(ranges[axis][1]-ranges[axis][0]):.3f}" height="{scale*(ranges[1][1]-ranges[1][0]):.3f}" fill="none" stroke="#c33232" stroke-dasharray="3 2"/>')
        fragments.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="4" fill="#d02020"/><path d="M{x-8:.3f},{y:.3f}h16 M{x:.3f},{y-8:.3f}v16" stroke="#fff"/>')
        if view=='front':
            # Actual two-point locations come from the generated balance input.
            for anchor in parts['suspension_points_mm']:
                fragments.append(f'<circle cx="{front_x+scale*anchor[0]:.3f}" cy="{origin_y-scale*anchor[1]:.3f}" r="4" fill="#3177c1"/>')
    lo,hi=clearance['minimum_mm'],clearance['maximum_mm']
    sx=side_x+scale*(lo[2]-zmin);sy=origin_y-scale*hi[1]
    fragments.append(f'<rect x="{sx:.3f}" y="{sy:.3f}" width="{scale*(hi[2]-lo[2]):.3f}" height="{scale*(hi[1]-lo[1]):.3f}" fill="none" stroke="#3177c1" stroke-dasharray="5 4"/>')
    fragments.append(line(front_x-dims['diameter']/2*scale,75,front_x+dims['diameter']/2*scale,75,f"{dims['diameter']:g}mm body diameter",65))
    fragments.append(line(side_x+scale*(0-zmin),555,side_x+scale*(dims['body_depth']-zmin),555,f"{dims['body_depth']:g}mm body",546))
    fragments.append(line(side_x,590,side_x+scale*dims['closed_depth'],590,f"{dims['closed_depth']:.3f}mm closed projection",611))
    fragments.append(line(sx,635,sx+scale*(hi[2]-lo[2]),635,f"{hi[2]-lo[2]:.3f}mm continuous service bound",655))
    tilt=cg['nominal_tilt_deg'];angles=cg['tilt_mass_allowance_range_deg']
    summary=f"Conditional nominal hanging tilt {tilt:.2f}deg; mass-only interval {angles[0]:.2f} to {angles[1]:.2f}deg."
    svg='<svg xmlns="http://www.w3.org/2000/svg" width="960" height="790" viewBox="0 0 960 790"><title>Narrow actual CAD front and side dimensions at one scale</title><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto-start-reverse"><path d="M0,0 L8,4 L0,8 Z" fill="#222"/></marker></defs><rect width="960" height="790" fill="#fafafa"/><g font-family="sans-serif" font-size="13"><text x="24" y="25" font-size="20">Narrow source CAD: front and side at the same scale</text><text x="24" y="47">2pixels/mm. External products shown; internal loom is in the native model and its full fit record.</text>'+''.join(fragments)+f'<text x="24" y="700">Red: nominal pendant CG and fixed-position mass-allowance interval. Blue: suspension / service bound.</text><text x="24" y="723">{html.escape(summary)}</text><text x="24" y="746">Free necklace span is laid clear for service. Full human hand, strap twist and supplied tolerances are not bounded.</text><text x="24" y="769">Physical fit, mass, strength and wearing angle are unmeasured. Optical colours here are diagram-only.</text></g></svg>'
    (out/'assembly-dimensions.svg').write_text(svg)
    return {'file':'assembly-dimensions.svg','scale_px_per_mm':scale,'dimension_basis':'Actual curve-and-tolerance source bounds; mesh silhouettes are illustration only','physical_acceptance':'unmeasured'}
