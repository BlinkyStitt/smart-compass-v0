"""Installed narrow wiring geometry and protection of original source bodies."""
import json,math
from pathlib import Path
import xml.etree.ElementTree as ET
import harness_ports,blackpill_mount,radio_mount
HERE=Path(__file__).resolve().parent

def joint_shapes(ports):
    import FreeCAD as App,Part
    out={}
    for pin,row in ports.items():
        if row['kind']!='solder':continue
        point=App.Vector(*row['terminal_mm']);axis=App.Vector(*row['axis'])
        shape=Part.makeCylinder(row['joint_diameter_target_mm']/2,row.get('joint_length_mm',row['strip_mm']),point,axis)
        if row.get('barrel_mm'):
            # Fabrication targets0.80mm for22AWG and0.52mm for26AWG,
            # versus source nominal bare0.762/0.4826mm. Neither is a
            # guaranteed supplied maximum. Inspect tinned fit; never trim
            # strands or drill a plated hole to force installation.
            radius=row['tinned_conductor_diameter_target_mm']/2
            shape=shape.fuse(Part.makeCylinder(radius,row['barrel_mm']+row['far_face_projection_mm'],point,-axis)).removeSplitter()
        out[pin]=shape
    import ring_harness
    out.update(ring_harness.joint_shapes(ports))
    return out

def source_bodies(p):
    """Preserve all source component spaces when allocating previous wire reserves."""
    import FreeCAD as App,Part
    out={};entries={e['name']:e for e in p['electronics']}
    e=entries['BlackPill'];z=e['pcb_bottom_z_mm'];dx,dy=e['mount_datum']
    facts=json.loads((HERE/'sources/blackpill-v31/component-bounds.json').read_text())
    for row in facts['bodies']:
        lo,hi=row['min_mm'],row['max_mm']
        body=Part.makeBox(*(b-a for a,b in zip(lo,hi)),App.Vector(lo[0],lo[1],z+1.6+lo[2]));body.translate(App.Vector(-blackpill_mount.DATUM[0],-blackpill_mount.DATUM[1],0));body.rotate(App.Vector(),App.Vector(0,0,1),e['rotation_deg']);body.translate(App.Vector(dx,dy,0))
        out['BLACKPILL.'+str(row['index'])]=body
    # The selected bare radio has only source top-side SMD components; the
    # source footprint reservations are retained at their original6.4mm height.
    e=entries['Radio'];z=e['pcb_bottom_z_mm'];dx,dy=e['mount_datum']
    for row in radio_mount.geometry()['footprint_bounds']:
        lo,hi=row['min_mm'],row['max_mm'];body=Part.makeBox(*(b-a for a,b in zip(lo,hi)),6.4,App.Vector(*lo,z+1.6));body.translate(App.Vector(-radio_mount.DATUM[0],-radio_mount.DATUM[1],0));body.rotate(App.Vector(),App.Vector(0,0,1),e['rotation_deg']);body.translate(App.Vector(dx,dy,0));out['RADIO.'+row['element']]=body
    import sparkle_mount,gps_mount
    e=next(e for e in p['electronics'] if e['name']=='SparkleMotion');source,_=sparkle_mount.source_module();removed=sparkle_mount.geometry()['removed_source_solid']
    for i,body in enumerate(source.Solids):
        if i==removed:continue
        shape=body.copy();shape.translate(App.Vector(-25.4,-16.51,e['pcb_bottom_z_mm']));shape.rotate(App.Vector(),App.Vector(0,0,1),e['rotation_deg']);shape.translate(App.Vector(*e['mount_datum'],0));out['SPARKLE.'+str(i)]=shape
    e=next(e for e in p['electronics'] if e['name']=='GPS');gps=gps_mount.geometry();source=Part.read(str(HERE/gps_mount.SOURCE/'3133.step'))
    if len(source.Solids)!=gps['source_solids']:raise ValueError('Original GPS mechanical body census changed')
    for i,body in enumerate(source.Solids):
        shape=body.copy();shape.translate(App.Vector(-25.4,-11.43,e['pcb_bottom_z_mm']));shape.rotate(App.Vector(),App.Vector(0,0,1),e['rotation_deg']);shape.translate(App.Vector(*e['mount_datum'],0));out['GPS.'+str(i)]=shape
    return out

def boost_source_footprints(p):
    """Nominal component-side footprints around the removed R20 tap."""
    import FreeCAD as App,Part
    e=next(e for e in p['electronics'] if e['name']=='Boost5V');z=e['pcb_bottom_z_mm']
    board=ET.fromstring((HERE/'sources/powerboost-1000-basic/Adafruit PowerBoost 1000 Basic.brd').read_bytes()).find('./drawing/board');libs={r.get('name'):r for r in board.findall('./libraries/library')}
    out={}
    for element in board.findall('./elements/element'):
        name=element.get('name')
        if name in ['R20','B1','CN1','JP1','X1','X2'] or name.startswith(('U$','FID')):continue
        package=next(r for r in libs[element.get('library')].findall('./packages/package') if r.get('name')==element.get('package'))
        points=[]
        for row in package:
            if row.tag=='smd':
                x,y,dx,dy=[float(row.get(k)) for k in ('x','y','dx','dy')]
                a=math.radians(float(row.get('rot','R0')[1:]))
                for u in [-dx/2,dx/2]:
                    for v in [-dy/2,dy/2]:points.append((x+u*math.cos(a)-v*math.sin(a),y+u*math.sin(a)+v*math.cos(a)))
            if row.tag in ['rectangle','wire'] and row.get('layer') in ['21','51']:
                half=float(row.get('width','0'))/2
                for i in ['1','2']:
                    for j in ['1','2']:
                        x,y=float(row.get('x'+i)),float(row.get('y'+j))
                        points.extend((x+u*half,y+v*half) for u in [-1,1] for v in [-1,1])
            if row.tag=='polygon' and row.get('layer') in ['21','51']:
                points.extend((float(v.get('x')),float(v.get('y'))) for v in row.findall('vertex'))
        if not points:raise ValueError('Review unbounded source boost footprint '+name)
        a=math.radians(float(element.get('rot','R0')[1:]));c,s=math.cos(a),math.sin(a)
        xy=[(float(element.get('x'))+x*c-y*s,float(element.get('y'))+x*s+y*c) for x,y in points]
        lo=[min(t[i] for t in xy) for i in [0,1]];hi=[max(t[i] for t in xy) for i in [0,1]]
        body=Part.makeBox(hi[0]-lo[0],hi[1]-lo[1],12.4,App.Vector(lo[0]-14.605,lo[1]-11.43,z+1.6));body.rotate(App.Vector(),App.Vector(0,0,1),e['rotation_deg']);body.translate(App.Vector(*e['centre'],0));out['BOOST.'+name]=body
    return out

def allocate_joint_spaces(objects,ports,p):
    """Replace only empty parts of the older generic wiring reservations."""
    import FreeCAD as App,Part
    from solid_clearance import bounds,box_distance
    import ring_harness,switch_boots
    ring=ring_harness.shape_products(ports,p)
    objects['ElectronicsShell']=objects['ElectronicsShell'].fuse(ring['land']).cut(Part.makeCompound(ring['cut_tools']))
    if not objects['ElectronicsShell'].isValid() or len(objects['ElectronicsShell'].Solids)!=1:raise ValueError('Ring cable channels split the printed case')
    objects['ElectronicsShell'].check(True)
    objects.update(ring['ties']);objects.update(switch_boots.native_shapes(ports))
    joints=joint_shapes(ports);bodies=source_bodies(p);bodies.update(boost_source_footprints(p));proof=[]
    # Shapes remain fixed during this allocation. Reuse their exact curve
    #bounds locally; never cache across a placement or shape mutation.
    source_bounds={name:bounds(body) for name,body in bodies.items()}
    joint_bounds={pin:bounds(shape) for pin,shape in joints.items()}
    groups=[('BlackPillUnderboardReservation','BLACKPILL.'),('BlackPillLoadedReservation','BLACKPILL.'),('RadioUnderboardReservation','RADIO.'),('RadioLoadedReservation','RADIO.'),('GPSComponents','GPS.'),('BoostComponents','BOOST.'),('SparkleComponents','SPARKLE.')]
    for reservation,prefix in groups:
        selected={pin:shape for pin,shape in joints.items() if pin.startswith(prefix)}
        for pin,shape in selected.items():
            for name,body in bodies.items():
                if not name.startswith(prefix) or box_distance(joint_bounds[pin],source_bounds[name])>1e-6:continue
                if shape.common(body).Volume>1e-6:raise ValueError('Wire joint hits original source body '+pin+'/'+name)
        old=objects[reservation];occupied=Part.makeCompound(list(selected.values()));new=old.cut(occupied).removeSplitter()
        if not new.isValid() or len(new.Solids)!=1:raise ValueError('Wiring allocation splits the remaining source reservation '+reservation)
        for name,body in bodies.items():
            if name.startswith(prefix) and body.common(old).cut(new).Volume>1e-6:raise ValueError('Wiring allocation removes original source coverage '+name)
        objects[reservation]=new;proof.append({'reservation':reservation,'source_bodies_preserved':sum(name.startswith(prefix) for name in bodies),'allocated_joint_count':len(selected)})
    # Dedicated cable passages in the printed structure. No hole is added to
    # the original PCB, stencil or mirrors. These cuts clear the full joint
    # gauges plus0.25mm assembly clearance at the input seam and board edge.
    cuts=[]
    for pin in ['FIBONACCI.5V','FIBONACCI.DIN','FIBONACCI.GND']:
        row=ports[pin];start=App.Vector(*row['terminal_mm']);axis=App.Vector(*row['axis']);start-=axis*.25
        cuts.append(Part.makeCylinder(row['joint_diameter_target_mm']/2+.25,row['strip_mm']+.5,start,axis))
    shell=objects['ElectronicsShell'].cut(Part.makeCompound(cuts))
    if not shell.isValid() or len(shell.Solids)!=1:raise ValueError('Harness joint passages split the shell')
    shell.check(True)
    objects['ElectronicsShell']=shell
    return joints,proof

def allocate_harness_reserves(objects,physical,p):
    """Turn previous nominal wire space into explicit occupied wire/fixture space.

    Original source component geometry remains protected. Only seven generic
    reservations can change; actual PCB, components, fasteners and mounts cannot.
    """
    import FreeCAD as App,Part
    import sparkle_mount,gps_mount
    from solid_clearance import bounds,box_distance
    bodies=source_bodies(p);bodies.update(boost_source_footprints(p))
    source_bounds={name:bounds(body) for name,body in bodies.items()}
    protected=0
    for name,shape in physical.items():
        shape_bounds=bounds(shape)
        for key,body in bodies.items():
            if box_distance(shape_bounds,source_bounds[key])>1e-6:continue
            protected+=1
            if shape.common(body).Volume>1e-6:raise ValueError('Explicit harness hits retained manufacturer body '+name+'/'+key)
    whole=Part.makeCompound(list(physical.values()));proof=[]
    for name,prefix in [('BlackPillUnderboardReservation','BLACKPILL.'),('BlackPillLoadedReservation','BLACKPILL.'),('RadioUnderboardReservation','RADIO.'),('RadioLoadedReservation','RADIO.'),('GPSComponents','GPS.'),('BoostComponents','BOOST.'),('SparkleComponents','SPARKLE.')]:
        old=objects[name];old_bounds=bounds(old);new=old.cut(whole).removeSplitter()
        # Unoccupied reservation space may become disconnected. It is not a
        # manufactured part. Every original source body remains protected below.
        if not new.isValid() or not new.Solids:raise ValueError('Invalid remaining module reservation '+name)
        count=0
        for key,body in bodies.items():
            if not key.startswith(prefix):continue
            count+=1
            if box_distance(source_bounds[key],old_bounds)>1e-6:continue
            if body.common(old).cut(new).Volume>1e-6:raise ValueError('Harness allocation removes source-body coverage '+key)
        objects[name]=new;proof.append({'reservation':name,'source_bodies_preserved':count,'removed_empty_volume_mm3':old.Volume-new.Volume})
    return {'source_bodies':len(bodies),'exact_body_pairs':protected,'allocations':proof}


def clamp_entry_spaces(ports):
    """Source-opening routing tunnels; never remove actual connector material."""
    import FreeCAD as App,Part
    out={}
    for pin,row in ports.items():
        if row['kind']!='clamp':continue
        radius=.999 if pin.startswith('BOOST.X2') else .8 if pin.startswith(('BOOST.','SPARKLE.')) else .999
        # The complete original Sparkle entry opening is2.15 x4.45mm.
        # It is centred at sourceZ3.945 on the X48.87 face, body201/face319.
        if pin.startswith('SPARKLE.'):
            if abs(row['terminal_mm'][2]-11.945)>1e-6:raise ValueError('Sparkle wire must enter the retained source opening')
            radius=.8
        out['ClampEntry'+pin]=Part.makeCylinder(radius,5,App.Vector(*row['terminal_mm']),App.Vector(*row['axis']))
    return out
