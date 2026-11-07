"""One explicit fixed narrow loom; every circuit terminal has one lead or cap."""
import json,math
from pathlib import Path
import harness_ports
HERE=Path(__file__).resolve().parent
# Complete insulated solder-splice fabrication gauges, not material volumes or
# guaranteed component dimensions. Axis isY; side entries are staggered.
HUBS={name:(row['centre_mm'],row['diameter_target_mm'],row['length_target_mm'])
      for name,row in json.loads((HERE/'harness-splices.json').read_text())['splices'].items()}

from harness_stock import group

def parameters():
    import importlib.util
    spec=importlib.util.spec_from_file_location('selected_narrow_harness_layout',HERE.parents[1]/'designs/stacked/layout.py')
    layout=importlib.util.module_from_spec(spec);spec.loader.exec_module(layout)
    return layout.parameters()

def definition(circuit=None):
    circuit=json.loads((HERE/'electrical-design.json').read_text()) if circuit is None else circuit
    from harness_stock import validate_limits
    validate_limits(circuit['wiring']['stock_limits'])
    p=parameters();ports=harness_ports.terminals(p,circuit);wires=[];hubs={}
    def wire(net,a,b):
        # Hub edges take the gauge required by their one device endpoint.
        device=b if a.startswith('SPLICE.') else a
        selected=group(device)
        if not a.startswith('SPLICE.') and not b.startswith('SPLICE.'):
            selected=max([group(a),group(b)],key=lambda x:{'signals':0,'branches':1,'main':2}[x])
        colour='0' if net=='GND' else '2' if selected in ['main','branches'] or device=='IMU.VIN' else '9'
        stock=circuit['wiring']['stock_limits'][selected]
        wires.append({'id':'W'+str(len(wires)+1).zfill(3),'net':net,'ends':[a,b],'wire_group':selected,'stock':stock['stock']+'-'+colour,'maximum_od_mm':stock['maximum_od_mm'],'strip_ends_mm':[ports[x]['strip_mm'] for x in (a,b)],'blank_trim_allowance_mm':20,'insertion_ends_mm':[ports[x]['strip_mm']+(2 if x.startswith('SPLICE.') else 0) for x in (a,b)]})
    for net,pins in circuit['nets'].items():
        if net in ['CONTACT_P','OUTPUT_OFF']:continue
        if net=='GND':
            # These are one published source GND copper net, not another wire.
            wire(net,'CONTACT_N.tail','BOOST.X2.1')
            pins=[pin for pin in pins if pin not in ['CONTACT_N.tail','BOOST.X2.1']]
        if len(pins)==2:wire(net,*pins);continue
        centre,diameter,length=HUBS[net];hubs[net]={**json.loads((HERE/'harness-splices.json').read_text())['splices'][net],'centre_mm':centre,'diameter_target_mm':diameter,'length_target_mm':length,'insulation':json.loads((HERE/'harness-splices.json').read_text())['splices'][net]['insulation'],'physical_acceptance':'unmeasured'}
        # Opposed end-face bundles leave the cradle's continuous side walls
        # intact. The18AWG core joins both end groups inside each sleeve.
        ordered=sorted(pins,key=lambda pin:-circuit['wiring']['stock_limits'][group(pin)]['maximum_od_mm'])
        for side,members in [(-1,ordered[::2]),(1,ordered[1::2])]:
            n=len(members)
            if n==1:offsets=[(0,0)]
            elif n==2:
                sep=sum(circuit['wiring']['stock_limits'][group(pin)]['maximum_od_mm']/2 for pin in members)+.1
                offsets=[(-sep/2,0),(sep/2,0)]
            elif n==3:offsets=[(.85*math.cos(k*math.tau/3),.85*math.sin(k*math.tau/3)) for k in range(3)]
            else:
                outer=n-2
                offsets=[(2.7*math.cos(k*math.tau/outer),2.7*math.sin(k*math.tau/outer)) for k in range(outer)]+[(-.65,0),(.65,0)]
            for i,(pin,(dx,dz)) in enumerate(zip(members,offsets)):
                key='SPLICE.'+net+'.'+str(side)+'.'+str(i)
                angle=math.radians(hubs[net].get('rotation_deg',0));c,s=round(math.cos(angle)),round(math.sin(angle))
                point=[centre[0]+dx*c-side*length/2*s,centre[1]+dx*s+side*length/2*c,centre[2]+dz]
                ports[key]={'terminal_mm':point,'wire_end_mm':point,'axis':[-side*s,side*c,0],'kind':'splice-exit','strip_mm':4,'joint_diameter_target_mm':diameter,'owner':'HarnessSplice'+net}
                wire(net,key,pin)
        hubs[net]['core']={'stock':'M22759/16-18-0' if net=='GND' else 'M22759/16-18-2','cut_mm':length,'strip_mm':length,'basis':'Continuous bare tinned core links both end bundles. Finished overall gauge includes the splice and sleeve; verify actual fit.'}
    # The negative contact conduit and W044 are two CAD segments of one
    #continuous18AWG conductor. There is no hidden tail splice or bare join.
    import battery_access,battery_leads
    contact=battery_access.definition();lead=battery_leads.layout(contact,'narrow')
    negative=next(w for w in wires if w['ends']==['CONTACT_N.tail','BOOST.X2.1'])
    negative['continuous_existing_part']='BatteryLeadN'
    negative['existing_segment_cut_mm']=lead['routed_centreline_mm']+contact['contact_leads']['strip_each_end_mm']
    negative['cut_basis']='One continuous negative lead: contact cup strip, fixed conduit segment, routed external segment and boost clamp strip; no tail strip or splice.'
    # Every connected device has exactly one external wire, except the
    # internally common BOOST ground pads and the already-built positive lead.
    expected={pin for pins in circuit['nets'].values() for pin in pins}-{'CONTACT_P.tail','F1.1','S1.6'}
    covered=[pin for w in wires for pin in w['ends'] if not pin.startswith('SPLICE.')]
    if set(covered)!=expected or len(covered)!=len(set(covered)):raise ValueError('Harness misses or duplicates device terminal')
    return {'revision':'narrow-fixed-loom-1','scope':'narrow only; fixed wires; no cell-service plug','ports':ports,'splices':hubs,'wires':wires,
            'support_pcb_back_z_mm':p['circle_back_z'],'rim_passages':__import__('ring_harness').rim_passages(),'source_internal_edges':[['BOOST.X1.1','BOOST.X2.1']],
            'existing_wired_edges':[['CONTACT_P.tail','F1.1']],
            'insulated_unused_terminals':['S1.6'],'physical_acceptance':'unmeasured'}

if __name__=='__main__':print(json.dumps(definition(),indent=2))
