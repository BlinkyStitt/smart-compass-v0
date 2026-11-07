"""Same-scale source dimension diagram; no optical or physical rendering claim."""
import math


def comparison(wide,narrow,parts):
    d=parts['dimensions_mm'];lo=d['closed_minimum_mm'];hi=d['closed_maximum_mm']
    values=[wide['diameter'],wide['body_depth'],narrow['diameter'],narrow['body_depth'],d['diameter'],d['body_depth'],d['closed_depth'],*lo,*hi]
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in values):raise ValueError('Finite source dimensions are required')
    if min(values[:7])<=0:raise ValueError('Positive source dimensions are required')
    if len(lo)!=3 or len(hi)!=3 or any(a>=b for a,b in zip(lo,hi)):raise ValueError('Ordered actual closed bounds are required')
    if abs(narrow['diameter']*1000-d['diameter'])>1e-6 or abs(narrow['body_depth']*1000-d['body_depth'])>1e-6 or abs(hi[2]-lo[2]-d['closed_depth'])>1e-6:raise ValueError('Narrow scene and installed dimension records disagree')
    scale=2;cy=350;items=[]
    for name,x,side,diam,depth in [('Wide archive',300,620,wide['diameter']*1000,wide['body_depth']*1000),('Narrow active',1030,1290,d['diameter'],d['body_depth'])]:
        radius=diam*scale/2
        items.append(f'<text x="{x}" y="35" text-anchor="middle" font-size="25">{name}</text><circle cx="{x}" cy="{cy}" r="{radius}" fill="#dce4e9" stroke="#283740" stroke-width="2"/><rect x="{side}" y="{cy-radius}" width="{depth*scale}" height="{diam*scale}" fill="#dce4e9" stroke="#283740" stroke-width="2"/><text x="{x}" y="{cy+radius+35}" text-anchor="middle">{diam:g}mm diameter</text><text x="{side+depth*scale/2}" y="{cy+radius+65}" text-anchor="middle">{depth:g}mm body</text>')
    items.append(f'<rect x="{1030+lo[0]*scale}" y="{cy-hi[1]*scale}" width="{(hi[0]-lo[0])*scale}" height="{(hi[1]-lo[1])*scale}" fill="none" stroke="#2163a4" stroke-dasharray="6 4" stroke-width="2"/>')
    x=1290+lo[2]*scale;y=cy-hi[1]*scale
    items.append(f'<rect x="{x}" y="{y}" width="{(hi[2]-lo[2])*scale}" height="{(hi[1]-lo[1])*scale}" fill="none" stroke="#2163a4" stroke-dasharray="6 4" stroke-width="2"/><text x="1330" y="685" text-anchor="middle">{d['closed_depth']:.3f}mm closed depth</text>')
    return '<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="800" viewBox="0 0 1500 800"><title>Source body and closed dimensions at the same scale</title><rect width="1500" height="800" fill="#f6f8fa"/><g font-family="sans-serif" font-size="20" fill="#1d2a33">'+''.join(items)+'<text x="750" y="740" text-anchor="middle">Front and side use2pixels/mm. Grey: source body envelope. Blue: actual narrow closed CAD bounds.</text><text x="750" y="775" text-anchor="middle">Dimension diagram. See the fitted CAD views below. Free necklace span and physical fit are unmeasured.</text></g></svg>'
