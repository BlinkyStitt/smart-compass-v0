"""Concrete narrow relief for the boost input pair.

The separate PETG clip prints on its flat tangent face with90degree X rotation.
Its curved foot bonds to the actual inner case wall with specified fitted1mm
3M VHB5952. Adhesion, lacing force, print strength and supplied fit are unmeasured.
"""
import math

PRINTED_PARTS=frozenset({'BoostInputRelief'})


def boost_input_pair(shell,p,d):
    import FreeCAD as App,Part
    def box(x0,x1,y0,y1,z0,z1):return Part.makeBox(x1-x0,y1-y0,z1-z0,App.Vector(x0,y0,z0))
    radius=d['side_radius']-p['strip_thickness']/2-1.5
    def ann(inner,outer,z0,z1):return Part.makeCylinder(outer,z1-z0,App.Vector(0,0,z0)).cut(Part.makeCylinder(inner,z1-z0,App.Vector(0,0,z0)))
    window=box(-94,-86,-13.7,-7.1,2.1,13.8)
    tape=ann(radius-1,radius,2.1,13.8).common(window).removeSplitter()
    foot=ann(radius-2.35,radius-1,2.1,13.8).common(window)
    stem=box(-90,-79.6,-13.7,-11.4,10.4,13.6)
    land=box(-80,-77.1,-13.7,-7.1,12,13.6)
    clip=foot.fuse(stem).fuse(land).cut(tape).removeSplitter()
    if not clip.isValid() or len(clip.Solids)!=1:raise ValueError('Boost input relief disconnected')
    if not tape.isValid() or len(tape.Solids)!=1:raise ValueError('Boost input relief pad disconnected')
    probe=ann(radius,radius+.02,2.2,13.7).common(box(-94,-86,-13.6,-7.2,2.2,13.7))
    if probe.cut(shell).Volume>1e-6:raise ValueError('Boost relief pad lacks complete source wall backing')
    outer=box(-79.05,-77.35,-14.2,-6.6,11.4,17.1)
    inner=box(-79.15,-77.25,-13.7,-7.1,11.9,16.6)
    loop=outer.cut(inner)
    knot=box(-81.2,-77.2,-6.8,-4.6,13.6,15.6)
    tie=loop.fuse(knot).removeSplitter()
    if not tie.isValid() or len(tie.Solids)!=1:raise ValueError('Boost input lacing disconnected')
    return {'products':{'BoostInputRelief':clip,'BoostInputReliefTape':tape,'BoostInputLacing':tie},
      'printed':sorted(PRINTED_PARTS),'rotation_deg':{'BoostInputRelief':{'axis':[1,0,0],'angle':90}},
      'wire_ids':['W006','W044'],'lacing':'Alpha Wire LC134 BK088;70mm blank, square knot; trim within the4x2.2x2mm knot space',
      'bond_area_target_mm2':(13.8-2.1)*radius*(math.asin(13.7/radius)-math.asin(7.1/radius)),
      'adhesive':'3M VHB5952; fitted1.0mm from nominal1.1mm. The derived curved bond area is a fabrication target, not a rated or qualified retention path.',
      'assembly':'Clean and qualify the specified case/clip bond. Seat the insulated input-positive and continuous negative lead in the two source-checked curves immediately outsideBOOST.X2.2/X2.1. Tie both to the bonded relief land; do not crush insulation or load the connector. Disconnect both clamps before rear removal. Inspect adhesive creep and tie retention before any wearing trial.',
      'physical_acceptance':'unmeasured'}


def verify_wire_capture(wires):
    """Check both actual max-OD input pipes pass inside the closed lacing loop.

    A collision-free route alone could miss the support. This section check
    requires one complete crossing for each selected conductor. It does not
    establish physical tie force, adhesive strength or retention.
    """
    import FreeCAD as App,Part
    from solid_clearance import bounds
    gate_x=-78.2;half=.01
    slab=Part.makeBox(2*half,400,100,App.Vector(gate_x-half,-200,-20))
    outer=Part.makeBox(2,7.6,5.7,App.Vector(-79.2,-14.2,11.4))
    inside=Part.makeBox(2.2,6.6,4.7,App.Vector(-79.3,-13.7,11.9))
    proof=[]
    for wid in ['W006','W044']:
        if wid not in wires:raise ValueError('Missing retained boost input conductor '+wid)
        sections=wires[wid].common(slab)
        selected=[s for s in sections.Solids if s.common(outer).Volume>1e-8]
        if len(selected)!=1:raise ValueError('Boost input wire does not cross its lacing gate exactly once '+wid)
        section=selected[0];bb=bounds(section)
        if not section.isValid() or bb.XMin>gate_x-half+1e-6 or bb.XMax<gate_x+half-1e-6 or section.cut(inside).Volume>1e-6:raise ValueError('Boost input wire leaves the retained lacing opening '+wid)
        proof.append({'wire':wid,'gate_x_mm':gate_x,'inside_y_mm':[-13.7,-7.1],'inside_z_mm':[11.9,16.6],'checked_section_volume_mm3':section.Volume,'physical_acceptance':'unmeasured'})
    return proof
