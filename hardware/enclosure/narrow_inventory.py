"""Narrow installed census. Every CAD object has one accounting owner.

Mass ranges are explicit engineering allowances unless a record says published.
They are not guaranteed assembly bounds, confidence intervals or measurements.
"""
import json,math,re
from pathlib import Path
import mass_core,narrow_fasteners
HERE=Path(__file__).resolve().parent

def module_records():
    return json.loads((HERE/'narrow-inventory-records.json').read_text())['modules']

def resolve(products,parameters,loom,contact_leads,ring_material=None):
    if not products or len({p['name'] for p in products})!=len(products):raise ValueError('Missing or duplicate narrow CAD census')
    print_spec=json.loads((HERE/'print-spec.json').read_text())
    material=print_spec['ring_materials'][ring_material or print_spec['default_ring_material']]
    geometry={p['name']:p for p in products};owners={};rows=[]
    fasteners,selected_screws=narrow_fasteners.load()
    if not set(selected_screws)<=geometry.keys():raise ValueError('Selected narrow cap-screw census is incomplete')
    def row(key,label,names,nominal,bounds,basis,group='pendant',centre=None,quantity=1):
        if not names and centre is None:raise ValueError('Mass row has no placement '+key)
        for name in names:
            if name not in geometry:raise ValueError('Inventory references absent narrow part '+name)
            if name in owners:raise ValueError('Narrow part counted twice '+name)
            owners[name]=key
        if centre is None:
            total=math.fsum(geometry[n]['volume_cm3'] for n in names)
            centre=[math.fsum(geometry[n]['volume_cm3']*geometry[n]['centre_mm'][i] for n in names)/total for i in range(3)]
        rows.append({'id':key,'label':label,'installed_quantity':quantity,'mass_g_per_unit':nominal,
                     'mass_range_g_per_unit':bounds,'mass_basis':basis,'group':group,'cad_parts':names,
                     'mass_centre_mm':centre,'physical_acceptance':'unmeasured'})
    for key,record in module_records().items():row(key,record['label'],record['cad_parts'],record['nominal_g'],record['range_g'],record['basis'])
    for name in ['StartSwitch','ModeSwitch','ActionSwitch']:
        row(name,'C&K PTS645SL70-2', [name],1,[.5,3],'Existing component-inventory.json#buttons allowance per fitted switch')
    for name,p in geometry.items():
        if name in owners:continue
        if p['group']=='Manufactured':
            acrylic=name in ['RearCouplingMirror','FrontMirror'];density=1.19 if acrylic else material['density_g_cm3'] if name in ['SideDiffuser','InnerDiffuser'] else 1.27
            mass=p['volume_cm3']*density;lo,hi=(.9,1.1) if acrylic else (.7,1.08)
            row(name,name,[name],mass,[mass*lo,mass*hi],f"CAD net solid volume x{density}g/cm3; existing material allowances; actual part mass unmeasured")
        elif name in selected_screws:
            selected,nominal,limits=narrow_fasteners.selected_mass(p,fasteners,selected_screws)
            row(name,selected['stock_part']+'; finished under-head target '+str(selected['finished_under_head_length_target_mm'])+'mm',[name],nominal,limits,fasteners['mass_basis']+'; source: designs/stacked/sources/fasteners/'+selected['source_file'])
        elif any(word in name for word in ['Screw','Nut','Washer','Bolt','HingePin']):
            mass=p['volume_cm3']*7.9
            row(name,name,[name],mass,[mass*.65,mass*1.5],'Nominal solid CAD metal envelope x7.9g/cm3, existing65..150% hardware allowance; threads/head sockets and actual alloy unmeasured')
        elif 'Shim' in name:
            mass=p['volume_cm3']*1.4
            row(name,name,[name],mass,[mass*.7,mass*1.5],'Selected polyester shim; nominal CAD volume x1.4g/cm3 with engineering70..150% allowance')
        elif 'Lacing' in name or name.startswith('HarnessSpliceTie'):
            # Total LC134 ties are declared by their complete fixed loop; the
            # uninstalled remainder of the cut blank is not worn.
            mass=p['volume_cm3']*1.4
            row(name,'Selected LC134 tie '+name,[name],mass,[mass*.7,mass*1.5],'Complete fitted loop/knot envelope x1.4g/cm3, engineering70..150% allowance; no blank tails added')
        elif name.startswith(('HarnessSpliceTape','BoostInputReliefTape')):
            mass=p['volume_cm3']*.59
            row(name,'3M VHB5952 fitted pad',[name],mass,[mass*.7,mass*1.5],'3M typical590kg/m3 x CAD fitted pad volume; engineering70..150% allowance, not a supplier bound')
        elif name.startswith('HarnessSpliceCarrier'):
            mass=p['volume_cm3']*1.27
            row(name,name,[name],mass,[mass*.7,mass*1.08],'CAD PETG net solid volume; existing70..108% allowance')
    for key,prefix,nominal,bounds in [('main_fuse','BatteryMainFuse',4,[2,8]),('branch_fuses','BranchFuseF_',.7,[.3,2]),('drains','BlackPillDrainR',.12,[.05,.4]),('sense_top','BlackPillSenseTop',.12,[.05,.4]),('sense_bottom','BlackPillSenseBottom',.12,[.05,.4]),('sense_cap','BlackPillSenseCapacitor',.12,[.05,.4])]:
        names=[name for name in geometry if name not in owners and (name==prefix or name.startswith(prefix))]
        # One physical passive plus its assembly reservation. Each fuse/resistor
        # has one stock mass; the nominal reservation is not another component.
        bases=[name for name in names if not name.endswith('Assembly')]
        for name in bases:
            associated=[n for n in names if n==name or n==name+'Assembly']
            row(key+'_'+name,name,associated,nominal,bounds,'Existing main-fuse allowance or explicit engineering passive allowance; full leads included')
    for name,count in [('Inner',parameters['inner_count']),('Side0',parameters['side_count']),('Side1',parameters['side_count'])]:
        length=count/parameters['strip_density'];row(name+'_strip',name+' fitted LED strip',[name+'Strip',name+'LEDs'],25,[15,40],'Existing component-inventory.json fitted strip allowance g/m; pixels and back counted together',quantity=length)
    if loom is None:raise ValueError('Complete routed narrow loom is required for installed mass')
    import harness_contract
    harness_contract.validate(loom)
    stock=json.loads((HERE/'electrical-design.json').read_text())['wiring']['stock_limits']
    for wire in loom['routes'].values():
        s=stock[wire['wire_group']];length=wire['finished_cut_target_mm']/1000;nominal=length*s['nominal_mass_g_m']
        row(wire['id'],wire['stock'],[wire['id']]+([wire['continuous_existing_part']] if 'continuous_existing_part' in wire else []),nominal,[nominal*.7,nominal*1.5],'Selected stock nominalg/m x full continuous stock cut including the declared internal jacket insertions and stripped ends; engineering70..150% allowance, no trim waste')
    for name,record in contact_leads.items():
        if name not in geometry or any(w.get('continuous_existing_part')==name for w in loom['routes'].values()):continue
        length=record['finished_cut_target_mm']/1000;nominal=length*stock['main']['nominal_mass_g_m'];row(name,name,[name],nominal,[nominal*.7,nominal*1.5],'Same selected18AWG stock/full finished contact lead; excludes duplicate F1 onward wire')
    # Splice gauges include sleeves/solder/core; use declared material cuts and
    # one complete fabrication allowance rather than filled-cylinder density.
    for name,splice in loom['splices'].items():
        core=splice['core']['cut_mm']/1000*stock['main']['nominal_mass_g_m']
        nominal=core+.25;upper=core*1.5+1
        row('splice_'+name,'Insulated solder splice '+name,['HarnessSplice'+name],nominal,[core*.7+.1,upper],'Selected18AWG continuous core cut once plus0.1..1g solder/sleeve allowance per completed splice; actual fabrication unmeasured')
    row('battery_ribbon','Selected100mm insulating pull ribbon',['BatteryPullRibbon'],.5,[.2,1.5],'Engineering complete fitted ribbon allowance')
    # Count the single stock cut once, including both direct sewn returns.
    tape = json.loads((HERE/'necklace.json').read_text())['tape']
    tape_upper = tape['main_cut_target_mm'] / 1000 / .9144 * tape['published_max_mass_oz_yd'] * 28.349523125
    necklace_parts = {name for name in geometry if name.startswith('Necklace')}
    if necklace_parts != {'NecklaceAttachmentReturn0','NecklaceAttachmentReturn1'}:
        raise ValueError('Missing direct necklace returns')
    row('necklace_tape','WayneMills5038 TypeIII Class1A3/8 nylon, 1.1 m direct strap',sorted(necklace_parts),tape_upper*.85,[tape_upper*.6,tape_upper],'MIL-DTL5038K2016 TableIII maximum0.12oz/yd conditional on conforming stock; includes both sewn returns',group='necklace',centre=[0,0,0])
    row('necklace_thread','Bonded nylon sewing thread, completed box-X seams',[],.5,[.2,1],'Engineering installed stitching allowance; seams and wearing unmeasured',group='necklace',centre=[0,0,0])
    row('joint_finish','Fitted solder,3M5413 joint insulation and labels',[name for name in geometry if name.startswith(('Joint','HarnessJoint','HarnessFinish','SwitchLugBoot'))],3,[1.5,6],'Retained component-inventory wire_finish allowance; splice sleeve/solder allowances above separate; measure finished assembly',centre=[0,0,15])
    legacy=json.loads((HERE/'component-inventory.json').read_text())
    records={entry['id']:entry for entry in legacy['components']}
    for name in ['front_coating','rear_coating','rim_mask','baffle_spacer_tack','joint_seals','seam_adhesive','vents']:
        entry=records[name]
        row(name,entry['label'],[],entry['mass_g_per_unit'],entry['mass_range_g_per_unit'],entry['mass_basis']+'; retained unresolved allowance, source: '+entry['source'],centre=[0,0,44] if name!='vents' else [0,0,1],quantity=entry['installed_quantity'])
    missing=set(geometry)-set(owners)
    if missing:raise ValueError('Narrow objects have no mass owner: '+', '.join(sorted(missing)))
    return {'components':rows,'cad_owners':owners,'mass_estimate':mass_core.totals(rows),'physical_acceptance':'unmeasured'}
