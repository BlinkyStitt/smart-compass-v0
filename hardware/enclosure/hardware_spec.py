"""Selected fastener dimensions, pocket allowances, and installed envelopes."""
import math

import json
import os
from pathlib import Path
from types import MappingProxyType

def _freeze(value):
    if isinstance(value,dict):
        return MappingProxyType({key:_freeze(item) for key,item in value.items()})
    return value


_SPEC = _freeze(json.loads((Path(os.environ.get('SC_CAD_DIR',Path(__file__).resolve().parent))/'component-inventory.json').read_text())['hardware'])
NUTS = _SPEC['nuts']
ALLOWANCE_FLATS = _SPEC['pocket_allowance']['total_flats']
ALLOWANCE_THICKNESS = _SPEC['pocket_allowance']['thickness']
WASHERS = _SPEC['washers']
SOFT_WASHER = _SPEC['soft_front_washer']


def nut_dimensions(size, pocket=False):
    nut = NUTS[size]
    return (round(nut['flats']+(ALLOWANCE_FLATS if pocket else 0),3),
            round(nut['thickness']+(ALLOWANCE_THICKNESS if pocket else 0),3))


def hexagon(x,y,flats):
    radius = flats/math.sqrt(3)
    return [(x+radius*math.cos(math.pi/6+j*math.tau/6),
             y+radius*math.sin(math.pi/6+j*math.tau/6)) for j in range(6)]


def body_bolt_length(p):
    """Finish the stock screw to the measured clamp stack and a short lead."""
    return (p['case_depth']+WASHERS['M3_front']['thickness']-p['rear_thickness']
            +WASHERS['M3']['thickness']+NUTS['M3']['thickness']+p['body_bolt_tip_projection'])


def stations(p):
    """Screw seat Z, direction, length and optional nut seat; washers at each seat."""
    from geometry import mounting_points, necklace_anchors, rear_mounting_points
    result=[]
    for i,(x,y) in enumerate(mounting_points(p)):
        result.append((f'Body{i}','M3',x,y,p['case_depth']+WASHERS['M3_front']['thickness'],-1,body_bolt_length(p),None))
    for i,side in enumerate((-1,1)):
        x,y=necklace_anchors(p,side)[2]
        result.append((f'Anchor{i}','M3',x,y,p['rear_thickness']-.55,1,12,p['rear_thickness']+p['necklace_link_thickness']+3.5))
    for i,(x,y) in enumerate(rear_mounting_points(p)):
        result.append((f'Rear{i}','M3',x,y,-.55,1,10,5.5))
    for i,(x,y) in enumerate([(x,y) for x in (-95,95) for y in (-30,30)]):
        for j,offset in enumerate((-11,11)):
            result.append((f'Vent{i}{j}','M2',x,y+offset,-p['structural_wall']-1.5-WASHERS['M2']['thickness'],1,8,2.5))
    for i,(dx,dy) in enumerate([(dx,dy) for dx in (-22.86,22.86) for dy in (-13.97,13.97)]):
        result.append((f'Sparkle{i}','M2',p['sparkle_x']-dx,p['sparkle_y']-dy,p['rear_thickness']+4+1.6+WASHERS['M2']['thickness'],-1,6,2.5))
    for i,x in enumerate((25,71)):
        result.append((f'Hatch{i}','M2',x,54,-p['structural_wall']-.35-WASHERS['M2']['thickness'],1,8,2.5))
    return result


def add_envelopes(b):
    import FreeCAD as App
    import Part
    from geometry import mounting_points
    def add(name,shape,variant,explosion_offset):
        obj=b.doc.addObject('Part::Feature',name)
        obj.Shape=shape
        b.add(obj,'Electronics',variant+' - nominal hardware envelope',(.65,.65,.68))
        obj.addProperty('App::PropertyString','HardwareVariant').HardwareVariant=variant
        obj.addProperty('App::PropertyFloat','ExplosionOffsetM').ExplosionOffsetM=explosion_offset
        return obj
    def washer(name,size,x,y,z,offset):
        w=WASHERS[size]
        shape=Part.makeCylinder(w['od']/2,w['thickness'],App.Vector(x,y,z)).cut(Part.makeCylinder(w['id']/2,w['thickness'],App.Vector(x,y,z)))
        add(name,shape,f'DIN 125 {size} washer',offset)
    def nut(name,size,x,y,z,offset,angle=0):
        flats,t=nut_dimensions(size)
        pts=[App.Vector(a,c,z) for a,c in hexagon(0,0,flats)]
        shape=Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(App.Vector(0,0,t))
        shape.rotate(App.Vector(),App.Vector(0,0,1),angle)
        shape.translate(App.Vector(x,y,0))
        shape=shape.cut(Part.makeCylinder(int(size[1:])/2,t,App.Vector(x,y,z)))
        add(name,shape,NUTS[size]['variant'],offset)
    for name,size,x,y,seat,direction,length,nut_z in stations(b.p):
        diameter=int(size[1:]); h=diameter; head=5.5 if size=='M3' else 3.8
        chamfer=b.p['body_bolt_tip_chamfer'] if name.startswith('Body') else 0
        shaft=Part.makeCylinder(diameter/2,length-chamfer,App.Vector(x,y,seat),App.Vector(0,0,direction))
        if chamfer:
            lead=Part.makeCone(diameter/2,diameter/2-chamfer,chamfer,App.Vector(x,y,seat+direction*(length-chamfer)),App.Vector(0,0,direction))
            shaft=shaft.fuse(lead)
        cap=Part.makeCylinder(head/2,h,App.Vector(x,y,seat),App.Vector(0,0,-direction))
        add(name+'Screw',shaft.fuse(cap),f'DIN 912 {size} x {length:g}'+(' - finish and deburr tip' if name.startswith('Body') else ''),.42 if name.startswith('Body') else -.23)
        washer(name+'Washer','M3_front' if name.startswith('Body') else size,x,y,seat-WASHERS['M3_front' if name.startswith('Body') else size]['thickness'] if direction==-1 else seat,.39 if name.startswith('Body') else -.20)
        # Top body washer lies BELOW the screw seat; rear washers lie ABOVE.
        if nut_z is not None:
            angle=math.degrees(math.atan2(y,x))+90 if size=='M3' else 0
            nut(name+'Nut',size,x,y,nut_z,0 if size=='M3' else -.10,angle)
    for i,(x,y) in enumerate(mounting_points(b.p)):
        bottom=b.p['rear_thickness']
        soft=SOFT_WASHER
        soft_z=b.p['front_plane_z']+b.p['front_acrylic_thickness']
        envelope=Part.makeCylinder(soft['od']/2,soft['compressed_thickness'],App.Vector(x,y,soft_z)).cut(
            Part.makeCylinder(soft['id']/2,soft['compressed_thickness'],App.Vector(x,y,soft_z)))
        add(f'FrontSoftWasher{i}',envelope,'Custom silicone front retention washer, compressed envelope',.37)
        washer(f'BodyRearWasher{i}','M3',x,y,bottom-.55,-.17)
        nut(f'BodyRearNut{i}','M3',x,y,bottom-.55-2.4,-.20)
