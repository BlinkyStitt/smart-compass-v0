"""Exact solid distance with conservative axis-aligned bounding-box pruning.

Each box contains its whole solid. Its distance is therefore a lower bound on
solid distance. A solid can be skipped only when that bound cannot improve the
already computed exact minimum. No name, material or component is exempted.
"""

import math


def box_distance(a,b):
    return math.sqrt(sum(max(0,getattr(a,axis+'Min')-getattr(b,axis+'Max'),
                              getattr(b,axis+'Min')-getattr(a,axis+'Max'))**2
                         for axis in 'XYZ'))


def distance(shape, obstacles):
    """Return the exact minimum distance to all supplied fixed shapes."""
    candidates=sorted((box_distance(shape.BoundBox,other.BoundBox),i,other)
                      for i,other in enumerate(obstacles))
    if not candidates:
        raise ValueError('Distance requires at least one obstacle')
    best=math.inf
    for lower,_,other in candidates:
        # Keep a numerical guard so rounded box values cannot hide a closer
        # solid at equality. Exact geometry still supplies every reported min.
        if lower > best+1e-7:
            break
        exact=shape.distToShape(other)[0]
        if not math.isfinite(exact) or exact < 0:
            raise ValueError('Invalid native solid distance')
        best=min(best,exact)
        if best == 0:
            break
    return best
