"""Finished wire-end insulation follows the selected real wire paths.

All finished diameters/overlaps are fabrication gauges, not manufacturer maxima.
This geometry does not qualify solder quality, recovery, adhesion or retention.
"""
import harness_route as route

ASSEMBLED_FINISH_LENGTH_MM=2
ASSEMBLED_FINISH_DIAMETER_MM=3


def prefix(points,radius,length,diameter):
    """Exact initial length of the actual rounded centreline, as a pipe."""
    import FreeCAD as App,Part
    edges=[];remaining=length
    for row in route.segments(points,radius):
        pts=[App.Vector(*p) for p in row['points']]
        edge=Part.makeLine(*pts) if row['kind']=='line' else Part.Arc(*pts).toShape()
        if remaining<edge.Length-1e-8:
            if row['kind']=='line':edge=Part.makeLine(pts[0],pts[0]+(pts[-1]-pts[0])*(remaining/edge.Length))
            else:edge=Part.Edge(edge.Curve,edge.FirstParameter,edge.FirstParameter+(edge.LastParameter-edge.FirstParameter)*remaining/edge.Length)
        edges.append(edge);remaining-=edge.Length
        if remaining<1e-7:break
    if remaining>1e-6:raise ValueError('Wire is shorter than its required insulation overlap')
    spine=Part.Wire(edges);axis=App.Vector(*route.unit(route.sub(points[1],points[0])))
    profile=Part.Wire(Part.makeCircle(diameter/2,App.Vector(*points[0]),axis))
    result=spine.makePipeShell([profile],True,False).removeSplitter()
    if not result.isValid() or len(result.Solids)!=1:raise ValueError('Invalid finished wire-end pipe')
    return result


def apply(physical,existing,wires,plan,record,name_for_joint):
    import FreeCAD as App,Part
    proof=[]
    for wid,row in record['routes'].items():
        for end,pin in enumerate(row['ends']):
            port=plan['ports'][pin];kind=port['kind']
            if kind in {'clamp','splice-exit','continuous-datum','existing-contact-lead'}:continue
            taped=kind in {'solder','formed-solder'}
            length=1 if taped else ASSEMBLED_FINISH_LENGTH_MM
            diameter=(1.2 if row['wire_group']=='signals' else 1.7) if taped else ASSEMBLED_FINISH_DIAMETER_MM
            points=row['points_mm'] if end==0 else list(reversed(row['points_mm']))
            outer=prefix(points,row['bend_radius_target_mm'],length,diameter)
            inner=prefix(points,row['bend_radius_target_mm'],length,row['maximum_od_mm'])
            # Permit only the intended own wire segment in the insulation.
            if outer.common(wires[wid].cut(inner)).Volume>1e-6:raise ValueError('End insulation meets a later section of its own wire '+wid+'/'+pin)
            cuff=outer.cut(wires[wid]).removeSplitter()
            if taped:
                key=name_for_joint('HarnessJoint',pin);point=App.Vector(*points[0]);axis=App.Vector(*port['axis'])
                cone=Part.makeCone(port['joint_diameter_target_mm']/2,diameter/2,.4,point-axis*.4,axis)
                physical[key]=physical[key].fuse(cone).fuse(cuff).cut(wires[wid]).removeSplitter()
                target=key
            elif kind=='lug-lap':
                target=port['joint_owner'];existing[target]=existing[target].fuse(cuff).removeSplitter()
            else:
                # Axial component leads use a coaxial split-strand solder lap:
                # fan all strands around the component lead, retain every
                #strand, overlap by the declared strip length, then recover
                #the sleeve onto2mm of intact wire jacket. The existing part
                #assembly gauge owns the internal lap; this owns its cuff.
                target='HarnessFinish'+wid+'_'+str(end)
                if pin.startswith('C_OUT.'):
                    point=App.Vector(*points[0]);axis=App.Vector(*port['axis'])
                    # Selected source lead plus its specified pitch-position
                    #variation occupies0.575mm radius in the source fixture.
                    internal=Part.makeCylinder(1.5,port['strip_mm'],point,-axis).cut(Part.makeCylinder(.575,port['strip_mm'],point,-axis))
                    cuff=cuff.fuse(internal).removeSplitter()
                physical[target]=cuff
            shape=physical[target] if target in physical else existing[target]
            if not shape.isValid() or not shape.Solids:raise ValueError('Invalid finished insulation '+target)
            proof.append({'wire':wid,'terminal':pin,'part':target,'jacket_overlap_target_mm':length,'finished_diameter_target_mm':diameter,
                          'finish':'Two-wrap3M5413 tape with a tapered transition' if taped else 'Selected RNF100 sleeve over the declared solder lap and intact jacket; finish to gauge',
                          'physical_acceptance':'unmeasured'})
    return proof
