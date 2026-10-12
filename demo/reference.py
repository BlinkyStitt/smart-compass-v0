"""Independent unfolded-mirror reference for GPU reflection acceptance.

Reflecting a ray at parallel planes is equivalent to continuing it through
unfolded copies of the cavity. Each copy is one mirror separation deep.
"""
import math


def reference(point, direction, optics, front_r=.65, front_t=.25, rear_r=.94):
    norm = math.sqrt(sum(v*v for v in direction))
    dx,dy,dz = [v/norm for v in direction]
    x,y,_ = point
    low, high = optics['halo_radius'], optics['inner_radius']
    if dz >= -.00001 or not low < math.hypot(x,y) < high:
        return [0,0,0]
    a = dx*dx+dy*dy
    if a<1e-10:
        return [0,0,0]
    roots=[]
    for group,radius in ((1,low),(2,high)):
        b=2*(x*dx+y*dy)
        c=x*x+y*y-radius*radius
        discriminant=b*b-4*a*c
        if discriminant>=0:
            for t in ((-b-math.sqrt(discriminant))/(2*a),(-b+math.sqrt(discriminant))/(2*a)):
                if t>1e-7:
                    roots.append((t,group))
    if not roots:
        return [0,0,0]
    travel,group=min(roots)
    depth=travel*-dz
    gap=optics['front_z']-optics['rear_z']
    reflections=math.floor(depth/gap)
    weight=front_t*rear_r**((reflections+1)//2)*front_r**(reflections//2)
    if reflections>32 or weight<.001:
        return [0,0,0]
    return [weight,reflections,group]


def cases(optics):
    middle=(optics['halo_radius']+optics['inner_radius'])/2
    z=optics['front_z']
    samples=[]
    # Construct exact path depths away from the discontinuity at a plane.
    for group in (1,2):
        radial=middle-optics['halo_radius'] if group==1 else optics['inner_radius']-middle
        for reflections in (0,1,2,3,7,13,22,31,32,33):
            depth=(reflections+.35)*(z-optics['rear_z'])
            direction=[(-1 if group==1 else 1)*radial,0,-depth]
            point=[middle,0,z]
            for reflectance,transmission in ((.65,.25),(.999,.001),(.99,.01),(0,1),(1,0)):
                samples.append({'point':point,'direction':direction,'reflectance':reflectance,'transmission':transmission,
                                'expected':reference(point,direction,optics,reflectance,transmission)})
    for point,direction in (([middle,0,z],[0,0,-1]),([0,0,z],[.5,0,-1]),([middle,0,z],[1,0,0]),([middle,0,z],[1,0,1]),([.13,0,z],[-.2,0,-1])):
        samples.append({'point':point,'direction':direction,'reflectance':.65,'transmission':.25,'expected':reference(point,direction,optics)})
    return samples
