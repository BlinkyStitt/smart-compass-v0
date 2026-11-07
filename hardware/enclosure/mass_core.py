"""Installed mass arithmetic and a conditional uniform-part balance model."""
import math

WORN_LIMIT_G=1133.980925
MARGIN_TARGET_G=50
GRAMS_PER_LB=453.59237


def finite_positive(value,name):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<=0:
        raise ValueError(name+' must be finite and positive')
    return value


def installed(row):
    quantity=finite_positive(row['installed_quantity'],row['id']+' quantity')
    values=[row['mass_range_g_per_unit'][0],row['mass_g_per_unit'],row['mass_range_g_per_unit'][1]]
    for value in values:finite_positive(value,row['id']+' mass')
    if values!=sorted(values):raise ValueError('Unordered mass bounds: '+row['id'])
    return [quantity*v for v in values]


def totals(rows):
    if not rows or len({r['id'] for r in rows})!=len(rows):raise ValueError('Missing or duplicate inventory rows')
    if any(r['group'] not in ('pendant','necklace','tool') for r in rows):raise ValueError('Unsupported installed group; regenerate the one-cell inventory')
    def selected(group):
        masses=[installed(r) for r in rows if r['group'] in group]
        values=[math.fsum(r[i] for r in masses) for i in range(3)]
        return {'nominal_g':values[1],'range_g':[values[0],values[2]]}
    result={'complete_pendant':selected({'pendant'}),'necklace':selected({'necklace'}),'total_worn':selected({'pendant','necklace'})}
    upper=result['total_worn']['range_g'][1]
    result.update(upper_worn_g=upper,limit_g=WORN_LIMIT_G,margin_g=WORN_LIMIT_G-upper,
                  ceiling_pass=upper<=WORN_LIMIT_G,margin_target_g=MARGIN_TARGET_G,
                  margin_target_pass=WORN_LIMIT_G-upper>=MARGIN_TARGET_G,
                  basis='Complete installed one-cell estimate. Sum independent low/high allowances without rounding; these are not confidence intervals. Exclude tools, charger, spares, retail stock and removed print supports. Physical mass is unmeasured.')
    return result


def coordinate_extreme(items,axis,minimum):
    # A linear-fractional mass ratio reaches its extrema at interval endpoints.
    # At a candidate coordinate t, choose the mass endpoint that minimizes (or
    # maximizes) sum m*(x-t). Bisect its unique root; all denominators are >0.
    low=min(position[axis] for position,_,_ in items)
    high=max(position[axis] for position,_,_ in items)
    for _ in range(100):
        mid=(low+high)/2
        terms=[]
        for position,a,b in items:
            delta=position[axis]-mid
            mass=(b if delta<0 else a) if minimum else (b if delta>0 else a)
            terms.append(mass*delta)
        if math.fsum(terms)>0:low=mid
        else:high=mid
    return (low+high)/2


def balance(rows,anchor_points):
    if len(anchor_points)!=2 or any(len(p)!=3 or any(not math.isfinite(v) for v in p) for p in anchor_points):
        raise ValueError('Balance requires two finite installed XYZ suspension datums')
    if abs(anchor_points[0][1]-anchor_points[1][1])>1e-8 or abs(anchor_points[0][2]-anchor_points[1][2])>1e-8:
        raise ValueError('The two-point balance model requires a level suspension axis')
    selected=[r for r in rows if r['group']=='pendant']
    if not selected:raise ValueError('No pendant masses')
    items=[];nominal=[]
    for row in selected:
        position=row.get('mass_centre_mm')
        if not isinstance(position,list) or len(position)!=3 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in position):
            raise ValueError('Missing installed mass centre: '+row['id'])
        a,m,b=installed(row);items.append((position,a,b));nominal.append((position,m))
    mass=math.fsum(m for _,m in nominal)
    cg=[math.fsum(p[i]*m for p,m in nominal)/mass for i in range(3)]
    ranges=[[coordinate_extreme(items,i,True),coordinate_extreme(items,i,False)] for i in range(3)]
    anchor=[(a+b)/2 for a,b in zip(*anchor_points)]
    drop=anchor[1]-cg[1]
    min_drop=anchor[1]-ranges[1][1]
    xs=sorted(p[0] for p in anchor_points)
    if xs[0]==xs[1]:raise ValueError('Suspension anchors have no lateral span')
    lateral=math.fsum(m*(p[0]-anchor[0]) for p,m in nominal)
    foreaft=math.fsum(m*(p[2]-anchor[2]) for p,m in nominal)
    angles=[math.degrees(math.atan2(z-anchor[2],anchor[1]-y)) for z in ranges[2] for y in ranges[1]] if min_drop>0 else None
    return {'pendant_mass_g':mass,'centre_mm':cg,'centre_mass_allowance_range_mm':ranges,
            'suspension_midpoint_mm':anchor,'centre_below_suspension_mm':drop,
            'minimum_model_drop_mm':min_drop,'lateral_moment_g_mm':lateral,'fore_aft_moment_g_mm':foreaft,
            'nominal_tilt_deg':math.degrees(math.atan2(cg[2]-anchor[2],drop)) if drop>0 else None,
            'tilt_mass_allowance_range_deg':[min(angles),max(angles)] if angles else None,
            'left_right_load_fraction':[(xs[1]-cg[0])/(xs[1]-xs[0]),(cg[0]-xs[0])/(xs[1]-xs[0])],
            'positive_two_point_support_for_mass_range':xs[0]<ranges[0][0]<=ranges[0][1]<xs[1] and min_drop>0,
            'basis':'Uniform CAD-part and declared stock mass-centre model. Numeric ranges vary mass allowances at fixed specified positions; they do not bound supplied component mass distribution, infill asymmetry, placement error, strap twist, walking or physical wearing angle. Necklace mass enters worn mass, not pendant CG. Physical balance is unmeasured.'}
