"""Fail-closed input contract for the one fixed narrow loom."""
import hashlib,json,math
from pathlib import Path
import harness_plan,harness_route
HERE=Path(__file__).resolve().parent

def numeric_record(value):
    # Normalize derived libm coordinates to one nanometre in this mm model.
    # Raw source bytes remain independently hashed by the release manifest.
    if isinstance(value,float):return round(value,9)
    if isinstance(value,list):return [numeric_record(item) for item in value]
    if isinstance(value,dict):return {key:numeric_record(item) for key,item in value.items()}
    return value

def fingerprint(plan):
    return hashlib.sha256(json.dumps(numeric_record(plan),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def validate(record,plan=None):
    plan=harness_plan.definition() if plan is None else plan
    if record.get('definition_sha256')!=fingerprint(plan):raise ValueError('Narrow loom definition changed; reroute and regenerate')
    routes=record.get('routes',{});expected={w['id']:w for w in plan['wires']}
    if set(routes)!=set(expected):raise ValueError('Missing or unexpected narrow routes: '+str(sorted(set(routes)^set(expected))))
    if record.get('splices')!=plan['splices']:raise ValueError('Narrow splice assembly differs from selected plan')
    if record.get('insulated_unused_terminals')!=plan['insulated_unused_terminals']:raise ValueError('Missing unused-terminal insulation')
    for key,wire in expected.items():
        row=routes[key]
        for name,value in wire.items():
            if numeric_record(row.get(name))!=numeric_record(value):raise ValueError('Narrow wire binding/stock changed: '+key+'/'+name)
        points=row.get('points_mm',[]);radius=row.get('bend_radius_target_mm')
        if isinstance(radius,bool) or not isinstance(radius,(int,float)) or not math.isfinite(radius) or radius<3*wire['maximum_od_mm']:
            raise ValueError('Narrow wire bend target is below3x selected maximum OD: '+key)
        if len(points)<2:raise ValueError('Narrow route has no path: '+key)
        for i,pin in [(0,wire['ends'][0]),(-1,wire['ends'][1])]:
            target=plan['ports'][pin]
            if any(abs(a-b)>1e-6 for a,b in zip(points[i],target['wire_end_mm'])):raise ValueError('Narrow route endpoint changed: '+key+'/'+pin)
            direction=harness_route.unit(harness_route.sub(points[1],points[0]) if i==0 else harness_route.sub(points[-2],points[-1]))
            if any(abs(a-b)>1e-6 for a,b in zip(direction,target['axis'])):raise ValueError('Narrow route exits through its terminal: '+key+'/'+pin)
        computed=harness_route.cut_record(wire,points,radius)
        for name in ['insulated_length_mm','finished_cut_target_mm','blank_cut_target_mm']:
            actual=row.get(name)
            if isinstance(actual,bool) or not isinstance(actual,(int,float)) or not math.isfinite(actual) or abs(actual-computed[name])>1e-6:raise ValueError('Narrow wire cut does not match actual path: '+key+'/'+name)
        if row.get('physical_acceptance')!='unmeasured':raise ValueError('No physical loom evidence is installed')
    if record.get('physical_acceptance')!='unmeasured':raise ValueError('No physical loom evidence is installed')
    return {'route_count':len(routes),'splice_count':len(plan['splices']),
            'finished_wire_m':math.fsum(row['finished_cut_target_mm'] for row in routes.values())/1000,
            'physical_acceptance':'unmeasured'}

def load():
    record=json.loads((HERE/'harness-routing.json').read_text());validate(record);return record
