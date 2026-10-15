"""Original EGL STL outline; no generated replacement for its walls."""
from collections import Counter, defaultdict
import math
from pathlib import Path
import re

SOURCE = Path(__file__).resolve().parent/'vendor/evilgeniuslabs-fibonacci256'


def source_vertices():
    text=(SOURCE/'Fibonacci256voronoi.stl').read_text()
    vertices=[tuple(map(float,values)) for values in re.findall(r'vertex\s+(\S+)\s+(\S+)\s+(\S+)',text)]
    if len(vertices)!=6732*3 or {v[2] for v in vertices}!={0.0,2.0}:
        raise ValueError('Expected original 6732-facet, 2 mm ASCII stencil STL')
    return vertices


def triangle_volume(triangles):
    """Stable double-precision volume; FreeCAD Mesh.Volume sums in floats."""
    return abs(math.fsum((a[0]*(b[1]*c[2]-b[2]*c[1])+
        a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
        for a,b,c in triangles))


def source_volume():
    vertices=source_vertices()
    return triangle_volume(zip(vertices[::3],vertices[1::3],vertices[2::3]))


def polygons(p):
    """Extract closed bottom contours from the original ASCII OpenSCAD STL.

    Interior triangle edges cancel in pairs. The remaining boundary edges form
    the exact extrusion profile, including its original open perimeter cells.
    """
    vertices=source_vertices()
    edges=Counter()
    for triangle in zip(vertices[::3],vertices[1::3],vertices[2::3]):
        if all(v[2]==0 for v in triangle):
            for a,b in zip(triangle,triangle[1:]+triangle[:1]):
                edges[tuple(sorted((a[:2],b[:2])))]+=1
    adjacency=defaultdict(list)
    for (a,b),count in edges.items():
        if count==1:
            adjacency[a].append(b); adjacency[b].append(a)
        elif count!=2:
            raise ValueError('Non-manifold source bottom triangles')
    if not adjacency or any(len(v)!=2 for v in adjacency.values()):
        raise ValueError('Source bottom boundary is not closed')
    remaining=set(adjacency); result=[]
    angle=math.radians(p['map_rotation_deg']); c,s=math.cos(angle),math.sin(angle)
    while remaining:
        start=min(remaining); at=start; previous=None; polygon=[]
        while True:
            x,y=83-at[0],at[1]-83
            x*= -1 if p['map_mirror_x'] else 1
            y*= -1 if p['map_mirror_y'] else 1
            polygon.append((x*c-y*s,x*s+y*c))
            remaining.remove(at)
            following=next(v for v in adjacency[at] if v!=previous)
            previous,at=at,following
            if at==start: break
        result.append(polygon)
    if len(result)!=222: raise ValueError('Original STL must contain 222 closed contours')
    return result


def inside(polygon,point):
    """Ray crossing for the original non-convex outline and its holes."""
    x,y=point; result=False
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
            result=not result
    return result
