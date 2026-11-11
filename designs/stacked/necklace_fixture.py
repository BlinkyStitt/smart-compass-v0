"""Direct strap returns through the two shell-integral suspension eyelets."""
import json
from pathlib import Path

PART_NAMES = frozenset(f'NecklaceAttachmentReturn{i}' for i in range(2))


def definition(source):
    spec = json.loads(Path(source).read_text())
    if spec['revision'] != 'narrow-direct-necklace-2':
        raise ValueError('Select the direct strap attachment')
    return {
        'tape': spec,
        'folded_width_mm': max(spec['tape']['width_mm']) / 2,
        'folded_thickness_mm': 2 * max(spec['tape']['thickness_mm']),
        'anchor_z_mm': 8.1,
    }


def native_shapes(shell, d, spec):
    import FreeCAD as App
    import Part
    import harness_route as geo

    posts, ports, probes, frames, returns = [], [], [], [], {}
    width, thick, z = (spec[key] for key in ('folded_width_mm', 'folded_thickness_mm', 'anchor_z_mm'))
    overlap = spec['tape']['seams']['main_end_overlap_mm']
    join = 17
    for i, side in enumerate((-1, 1)):
        rotation = -37 if side == 1 else 37
        datum = App.Vector(side * d['suspension_x'], d['suspension_y'], 0)

        def place(shape):
            shape.rotate(App.Vector(), App.Vector(0, 0, 1), rotation)
            shape.translate(datum)
            return shape

        posts.append(place(Part.makeBox(9, 4, 11, App.Vector(-4.5, 0, 2))))
        probes.append(place(Part.makeBox(7.8, 2.8, 6, App.Vector(-3.9, .2, 5))))
        # Radius on the strap-facing passage corners. Retain the original
        # full post section and do not extend the cut into the optical band.
        r = .5
        for x in (-6, 6):
            port = Part.makeBox(3 - 2*r, 13, 7, App.Vector(x-1.5+r,-3,z-3.5))
            port = port.fuse(Part.makeBox(3,13,7-2*r,App.Vector(x-1.5,-3,z-3.5+r)))
            for u in (x-1.5+r, x+1.5-r):
                for v in (z-3.5+r, z+3.5-r):
                    port = port.fuse(Part.makeCylinder(r,13,App.Vector(u,-3,v),App.Vector(0,1,0)))
            ports.append(place(port.removeSplitter()))

        # Each main end turns directly around the eyelet. The width is
        # folded only in this attachment region and its single sewn overlap.
        points = [[-thick/2,join,z],[-thick/2,14,z],[-6,8,z],[-6,-1,z],
                  [6,-1,z],[6,8,z],[thick/2,14,z],[thick/2,join,z]]
        edges = []
        for segment in geo.segments(points, 1.3):
            ps = [App.Vector(*point) for point in segment['points']]
            edges.append(Part.makeLine(*ps) if segment['kind'] == 'line' else Part.Arc(*ps).toShape())
        path = Part.Wire(edges)
        corners = [App.Vector(x,join,z+y*width/2) for x,y in
                   [(-thick,-1),(0,-1),(0,1),(-thick,1),(-thick,-1)]]
        bend = path.makePipeShell([Part.makePolygon(corners)], True, False)
        seam = Part.makeBox(2*thick,overlap+.05,width,App.Vector(-thick,join-.05,z-width/2))
        fitted = place(bend.fuse(seam).removeSplitter())
        if not fitted.isValid() or len(fitted.Solids) != 1:
            raise ValueError('Direct strap return is invalid or disconnected')
        returns[f'NecklaceAttachmentReturn{i}'] = fitted
        entry = App.Vector(0,join+overlap,z)
        entry = App.Rotation(App.Vector(0,0,1),rotation).multVec(entry) + datum
        frames.append({'side':side,'anchor_z_mm':z,'main_end_stock_mm':path.Length+2*overlap,
                       'main_overlap_mm':overlap,'free_span_entry_mm':list(entry)})

    # Preserve the curved shell topology; same-domain refinement can
    # invalidate its original curved board-seat faces in FreeCAD 1.1.
    case = shell.fuse(Part.makeCompound(posts)).cut(Part.makeCompound(ports))
    if not case.isValid() or len(case.Solids) != 1:
        raise ValueError('Direct eyelet cuts split the case')
    case.check(True)
    for probe in probes:
        if probe.cut(case).Volume > 1e-6:
            raise ValueError('Suspension post cross-section lost')
    for name, fitted in returns.items():
        if fitted.common(case).Volume > 1e-5:
            raise ValueError('Direct strap return intersects its eyelet: ' + name)
    remaining = spec['tape']['tape']['main_cut_target_mm'] - sum(f['main_end_stock_mm'] for f in frames)
    if remaining <= 0:
        raise ValueError('Direct returns exceed selected strap stock')
    return {'case':case,'products':returns,'frames':frames,'free_main_span_target_mm':remaining,
            'service_condition':'Lay the loose strap above the supported pendant during cell service.',
            'physical_acceptance':'unmeasured'}
