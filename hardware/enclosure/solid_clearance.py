"""Exact solid distance with conservative axis-aligned bounding-box pruning.

Each box contains its whole solid. Its distance is therefore a lower bound on
solid distance. A solid can be skipped only when that bound cannot improve the
already computed exact minimum. No name, material or component is exempted.
"""

import math


def bounds(shape):
    # FreeCAD's display triangulation can understate circular extents. Use
    # the actual curves and source shape tolerances for conservative pruning.
    # No fallback to display-mesh bounds is permitted.
    return shape.optimalBoundingBox(False,True)


def box_distance(a,b):
    return math.sqrt(sum(max(0,getattr(a,axis+'Min')-getattr(b,axis+'Max'),
                              getattr(b,axis+'Min')-getattr(a,axis+'Max'))**2
                         for axis in 'XYZ'))


def _distance(shape, fixed):
    """Return the exact minimum distance to all supplied fixed shapes."""
    shape_bounds=bounds(shape)
    candidates=sorted((box_distance(shape_bounds,other_bounds),i,other)
                      for i,(other,other_bounds) in enumerate(fixed))
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


def distance(shape, obstacles):
    """Return the exact minimum distance to the current supplied shapes."""
    return _distance(shape, ((other,bounds(other)) for other in obstacles))


class FixedObstacles:
    """Own snapshots for repeated queries against one fixed assembly pose.

    Copy the source solids so later source placement changes cannot invalidate
    the stored curve bounds. Moving-solid bounds and exact distances are still
    computed for each query. No caller-supplied bounds or mesh fallback enter.
    """
    def __init__(self, obstacles):
        shapes=tuple(shape.copy() for shape in obstacles)
        if not shapes:
            raise ValueError('Distance requires at least one obstacle')
        self._fixed=tuple((shape,bounds(shape)) for shape in shapes)

    def distance(self, shape):
        return _distance(shape,self._fixed)


def translation_clearance(shape,obstacle,vector,required,minimum_interval_mm=.001):
    """Certify every point of a finite translation using exact solid distances.

    Solid distance is1-Lipschitz in translation distance. A midpoint distance
    minus the largest displacement within its interval bounds the ENTIRE
    interval. Whole-solid bounding boxes may only prove a pair clear. Neither
    an empty box region nor unresolved sampling may establish a collision or
    a pass. Unresolved intervals fail closed at the numerical resolution.
    """
    import FreeCAD as App
    from types import SimpleNamespace
    if (len(vector)!=3 or not all(math.isfinite(v) for v in vector)
            or not math.isfinite(required) or required<=0
            or not math.isfinite(minimum_interval_mm) or minimum_interval_mm<=0):
        raise ValueError('Continuous translation requires a finite vector and positive clearance/resolution')
    if shape.isNull() or obstacle.isNull() or not shape.isValid() or not obstacle.isValid():
        raise ValueError('Continuous translation requires valid actual solids')
    length=math.sqrt(sum(v*v for v in vector))
    if length<=0:raise ValueError('Continuous translation needs positive travel')
    source=bounds(shape);target=bounds(obstacle);values={};evaluations=0;lower_bounds=[];pruned=0
    def swept_bounds(a,b):
        record={}
        for axis,v in zip('XYZ',vector):
            record[axis+'Min']=getattr(source,axis+'Min')+min(a*v,b*v)
            record[axis+'Max']=getattr(source,axis+'Max')+max(a*v,b*v)
        return SimpleNamespace(**record)
    def exact(t):
        nonlocal evaluations
        if t not in values:
            moved=shape.copy();moved.translate(App.Vector(*(t*v for v in vector)))
            value=moved.distToShape(obstacle)[0]
            if not math.isfinite(value) or value<0:raise ValueError('Invalid native translation distance')
            values[t]=value;evaluations+=1
        return values[t]
    # A whole-motion box can prove separation without constructing a sweep.
    lower=box_distance(swept_bounds(0,1),target)
    if lower>required+1e-7:return {'lower_bound_mm':lower,'exact_evaluations':0,'box_proofs':1}
    for t in (0.,1.):
        d=exact(t)
        if d<=required:raise ValueError('Translation clearance fails at fraction '+str(t)+': '+str(d)+'mm')
    intervals=[(0.,1.)]
    while intervals:
        a,b=intervals.pop();lower=box_distance(swept_bounds(a,b),target)
        if lower>required+1e-7:lower_bounds.append(lower);pruned+=1;continue
        middle=(a+b)/2;displacement=length*(b-a)/2;d=exact(middle)
        if d<=required:raise ValueError('Translation clearance fails at fraction '+str(middle)+': '+str(d)+'mm')
        lower=d-displacement
        if lower>required+1e-7:lower_bounds.append(lower);continue
        if length*(b-a)<=minimum_interval_mm:
            raise ValueError('Translation interval remains unproved at '+str((a,b))+': lower bound '+str(lower)+'mm')
        intervals.extend(((middle,b),(a,middle)))
    return {'lower_bound_mm':min(lower_bounds),'exact_evaluations':evaluations,'box_proofs':pruned}


def native_translation_regressions():
    """Intentional geometry tests; these are not assembly evidence."""
    import FreeCAD as App
    import Part
    moving=Part.makeBox(1,1,1,App.Vector(0,0,5));side=Part.makeBox(1,1,1,App.Vector(1.5,0,-.215))
    result=translation_clearance(moving,side,(0,0,-10),.2)
    if result['lower_bound_mm']<=.2:raise ValueError('Clear continuous motion was not certified')
    thin=Part.makeBox(.02,.02,.02,App.Vector(.49,.49,-.215))
    try:translation_clearance(moving,thin,(0,0,-10),.2)
    except ValueError as error:
        if 'clearance fails' not in str(error):raise
    else:raise ValueError('Thin obstacle between initial/end/midpoint poses was missed')
    # Two separated legs have a wide empty centre. An enclosing box would
    # falsely block the object in that centre for every withdrawal position.
    left=Part.makeBox(1,1,1,App.Vector(0,0,5));right=Part.makeBox(1,1,1,App.Vector(4,0,5))
    empty=Part.makeCompound([left,right]);centre=Part.makeBox(1,1,1,App.Vector(2,0,0))
    result=translation_clearance(empty,centre,(0,0,-10),.2)
    if result['lower_bound_mm']<=.2:raise ValueError('Actual separated solids were replaced by a filled bounding box')
    return {'scope':'synthetic native regression only','clear_motion':'pass','thin_collision_rejected':'pass','empty_box_region':'pass'}
