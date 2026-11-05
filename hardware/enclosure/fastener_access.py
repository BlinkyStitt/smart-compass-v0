"""Nominal captive-nut insertion and vertical drop before fitting electronics."""
import math
from hardware_spec import hexagon,nut_dimensions


def entry_dimensions(size='M2',length=8):
    if size!='M2' or length not in (8,9,12):raise ValueError('Use a reviewed M2 entry length')
    flats,height=nut_dimensions(size);pflat,ph=nut_dimensions(size,pocket=True)
    return {'length':length,'width':2*pflat/math.sqrt(3),'height':ph,
            'travel':length-flats/math.sqrt(3)-.1,'nut_height':height}


def _hull(points):
    points=sorted(set(points))
    def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    lower=[];upper=[]
    for p in points:
        while len(lower)>1 and cross(lower[-2],lower[-1],p)<=0:lower.pop()
        lower.append(p)
    for p in reversed(points):
        while len(upper)>1 and cross(upper[-2],upper[-1],p)<=0:upper.pop()
        upper.append(p)
    return lower[:-1]+upper[:-1]


def native_tools(x,y,z,axis,length=8):
    import FreeCAD as App
    import Part
    if tuple(axis) not in ((1,0),(-1,0),(0,1),(0,-1)):raise ValueError('Use a reviewed cardinal nut-entry direction')
    data=entry_dimensions(length=length);dx,dy=axis;flats,height=nut_dimensions('M2')
    w,l=(data['length'],data['width']) if dx else (data['width'],data['length'])
    entry=Part.makeBox(w,l,data['height'],App.Vector(x+dx*length/2-w/2,y+dy*length/2-l/2,z))
    vertices=hexagon(x,y,flats);travel=data['travel']
    end=[(a+dx*travel,b+dy*travel) for a,b in vertices]
    def prism(points,h):
        pts=[App.Vector(a,b,z) for a,b in points]
        return Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(App.Vector(0,0,h))
    # Sweep the actual outer nut profile. Include lowering it into the open
    # slot before sliding it under the pocket roof. Fit boards/screws later.
    horizontal=prism(_hull(vertices+end),height)
    drop=prism(end,height+10)
    return entry,horizontal.fuse(drop).removeSplitter()


def native_check_paths(paths,rear,count):
    if not isinstance(paths,list) or len(paths)!=count:raise ValueError('Complete nut insertion/drop paths are required')
    for path in paths:
        if not path.isValid() or len(path.Solids)!=1:raise ValueError('Nut insertion path is invalid or detached')
        volume=path.common(rear).Volume
        if volume>1e-6:raise ValueError('Nut insertion or vertical drop is blocked: '+str(volume))
