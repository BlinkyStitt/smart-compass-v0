"""Specified round-wire routes with tangent circular bends and raw cut lengths.

Bend radii and assembly positions are fabrication targets. This module does not
claim a supplier bend guarantee or a measured finished harness.
"""
import math

EPS=1e-7

def add(a,b):return [x+y for x,y in zip(a,b)]
def sub(a,b):return [x-y for x,y in zip(a,b)]
def mul(a,k):return [x*k for x in a]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def norm(a):return math.sqrt(dot(a,a))
def unit(a):
    n=norm(a)
    if n<EPS:raise ValueError('Zero route segment')
    return mul(a,1/n)

def segments(points,radius):
    if isinstance(radius,bool) or not isinstance(radius,(int,float)) or not math.isfinite(radius) or radius<=0:raise ValueError('Invalid bend radius')
    if len(points)<2 or any(len(p)!=3 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in p) for p in points):raise ValueError('Invalid route points')
    directions=[unit(sub(b,a)) for a,b in zip(points,points[1:])]
    corners={}
    for i,(a,b) in enumerate(zip(directions,directions[1:]),1):
        c=max(-1,min(1,dot(a,b)))
        if c>1-EPS:continue
        if c< -1+EPS:raise ValueError('Reversing route')
        angle=math.acos(c);trim=radius*math.tan(angle/2)
        centre=add(points[i],mul(unit(sub(b,a)),radius/math.cos(angle/2)))
        start=sub(points[i],mul(a,trim));end=add(points[i],mul(b,trim))
        mid=add(centre,mul(unit(add(sub(start,centre),sub(end,centre))),radius))
        corners[i]=(trim,start,mid,end,angle)
    out=[];current=points[0]
    for i in range(len(points)-1):
        available=norm(sub(points[i+1],points[i]))
        used=corners.get(i,(0,))[0]+corners.get(i+1,(0,))[0]
        if used>available+EPS:raise ValueError('Insufficient straight length between bends')
        end=corners[i+1][1] if i+1 in corners else points[i+1]
        if norm(sub(current,end))>EPS:out.append({'kind':'line','points':[current,end],'length_mm':norm(sub(current,end))})
        if i+1 in corners:
            _,start,mid,end,angle=corners[i+1]
            out.append({'kind':'arc','points':[start,mid,end],'length_mm':radius*angle,'radius_mm':radius})
        current=end
    return out

def native(points,radius,diameter):
    import FreeCAD as App,Part
    if diameter<=0:raise ValueError('Invalid wire diameter')
    parts=segments(points,radius);edges=[]
    for row in parts:
        pts=[App.Vector(*p) for p in row['points']]
        edges.append(Part.makeLine(*pts) if row['kind']=='line' else Part.Arc(*pts).toShape())
    spine=Part.Wire(edges);axis=App.Vector(*unit(sub(points[1],points[0])))
    profile=Part.Wire([Part.makeCircle(diameter/2,App.Vector(*points[0]),axis)])
    body=spine.makePipeShell([profile],True,False).removeSplitter()
    if not body.isValid() or len(body.Solids)!=1:raise ValueError('Invalid routed wire solid')
    length=math.fsum(p['length_mm'] for p in parts)
    if abs(spine.Length-length)>1e-6:raise ValueError('Native route length differs from analytic route')
    return body,length

def cut_record(wire,points,radius):
    length=math.fsum(p['length_mm'] for p in segments(points,radius))
    cut=length+math.fsum(wire.get('insertion_ends_mm',wire['strip_ends_mm']))+wire.get('existing_segment_cut_mm',0)
    return {**wire,'points_mm':points,'bend_radius_target_mm':radius,'insulated_length_mm':length,
            'finished_cut_target_mm':cut,'blank_cut_target_mm':cut+wire['blank_trim_allowance_mm'],
            'physical_acceptance':'unmeasured'}
