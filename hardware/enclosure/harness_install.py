"""Install the complete selected narrow loom and check its actual native solids."""
import re
import harness_finish
import harness_contract,harness_plan,harness_native,harness_mounts,harness_route
from solid_clearance import bounds,box_distance


def native_name(prefix,pin):return prefix+re.sub('[^A-Za-z0-9_]','_',pin)


def install(objects,p,add):
    import Part
    plan=harness_plan.definition();record=harness_contract.load();contract=harness_contract.validate(record,plan)
    original={obj.Name:obj.Shape for obj in objects};existing=dict(original)
    ports=plan['ports'];joints,joint_allocation=harness_native.allocate_joint_spaces(existing,ports,p)
    mounts=harness_mounts.native_shapes(plan)
    physical={native_name('HarnessJoint',pin):shape for pin,shape in joints.items()}
    physical.update(mounts['products']);physical.update(mounts['splices'])
    wires={};cuts=[]
    for wid,row in sorted(record['routes'].items()):
        shape,length=harness_route.native(row['points_mm'],row['bend_radius_target_mm'],row['maximum_od_mm'])
        if abs(length-row['insulated_length_mm'])>1e-6:raise ValueError('Installed narrow wire length changed '+wid)
        wires[wid]=shape;cuts.append({key:row[key] for key in ['id','net','stock','ends','strip_ends_mm','insertion_ends_mm','insulated_length_mm','finished_cut_target_mm','blank_cut_target_mm','continuous_existing_part','existing_segment_cut_mm','cut_basis'] if key in row})
    import end_supports
    capture=end_supports.verify_wire_capture(wires)
    finish=harness_finish.apply(physical,existing,wires,plan,record,native_name)
    physical.update(wires)
    fixed_reliefs={name:shape for name,shape in existing.items() if name in {'BoostInputRelief','BoostInputReliefTape','BoostInputLacing'}}
    if set(fixed_reliefs)!={'BoostInputRelief','BoostInputReliefTape','BoostInputLacing'}:raise ValueError('Missing selected boost input strain relief')
    source_proof=harness_native.allocate_harness_reserves(existing,{**physical,**fixed_reliefs,**harness_native.clamp_entry_spaces(ports)},p)
    # New fixed ring ties and switch boots are introduced by the common source
    # allocator. Include them in the same all-part interference check.
    new={key:shape for key,shape in existing.items() if key not in original}
    physical.update(new)
    fixed={key:shape for key,shape in existing.items() if key in original}
    conflicts=[];pairs=0
    fixed_bounds={name:bounds(shape) for name,shape in fixed.items()}
    physical_bounds={name:bounds(shape) for name,shape in physical.items()}
    for name,shape in physical.items():
        if not shape.isValid() or not shape.Solids:raise ValueError('Invalid installed narrow loom part '+name)
        for other,body in fixed.items():
            if box_distance(physical_bounds[name],fixed_bounds[other])>1e-7:continue
            pairs+=1;volume=shape.common(body).Volume
            if volume>1e-6:conflicts.append({'part':name,'other':other,'volume_mm3':volume})
    items=list(physical.items())
    for i,(name,shape) in enumerate(items):
        for other,body in items[i+1:]:
            if box_distance(physical_bounds[name],physical_bounds[other])>1e-7:continue
            pairs+=1;volume=shape.common(body).Volume
            if volume>1e-6:conflicts.append({'part':name,'other':other,'volume_mm3':volume})
    if conflicts:raise ValueError('Installed narrow loom interference: '+str(conflicts))
    byname={obj.Name:obj for obj in objects}
    for key,shape in fixed.items():byname[key].Shape=shape
    # The source allocator can change only printed cable channels and empty
    # generic reservations. Every original manufacturer body remains protected.
    for key,shape in physical.items():
        printed=key.startswith('HarnessSpliceCarrier')
        material='Opaque black PETG' if printed else 'Selected insulated loom assembly target; physical fit/retention unmeasured'
        colour=(.025,.025,.03)
        if key in record['routes']:
            stock=record['routes'][key]['stock'];colour=(.65,.015,.015) if stock.endswith('-2') else (.7,.7,.72) if stock.endswith('-9') else (.025,.025,.03)
        add(key,shape,'Manufactured' if printed else 'Electronics',colour,material=material)
    return {'scope':'Complete selected narrow loom; actual source parts, max stock wire diameters, fabrication joint/fixture targets and exact rounded paths',
            'contract':contract,'cut_list':cuts,'source_protection':source_proof,'joint_allocations':joint_allocation,
            'wire_end_insulation':finish,'end_relief_captures':capture,'exact_pairs':pairs,'interference_threshold_mm3':1e-6,'conflicts':[],
            'parts':sorted(physical),'physical_acceptance':'unmeasured'}
