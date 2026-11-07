"""Current Narrow rear base; source owners supply compartment and control tools."""
import math


def native_blank(radius,rear_points,vent_points,battery,controls):
    import FreeCAD as App
    import Part
    if not math.isfinite(radius) or radius<=0 or len(rear_points)!=6 or len(vent_points)!=4:
        raise ValueError('Review the actual Narrow rear radius, six fasteners and four vents')
    shape=Part.makeCylinder(radius,2).cut(battery['rear_cutout'])
    shape=shape.cut(controls['rear_cutout']).fuse(controls['rear_addition'])
    for points,r in ((rear_points,1.7),(vent_points,3)):
        for x,y in points:
            if not all(math.isfinite(v) for v in (x,y)):raise ValueError('Rear opening datum must be finite')
            shape=shape.cut(Part.makeCylinder(r,3,App.Vector(x,y,-.5)))
    shape=shape.removeSplitter()
    if not shape.isValid() or len(shape.Solids)!=1:raise ValueError('Current Narrow rear base is invalid/disconnected')
    return shape
