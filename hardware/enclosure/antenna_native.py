"""FreeCAD solids and distance checks for the two fixed antenna installations."""

import math
import json

import FreeCAD as App
import Part

import antenna
import radio_mount
import branch_fuses
import blackpill_mount
import gps_mount
import sparkle_mount
import imu_mount
import boost_mount
import latch_mount
import capacitor_mount
import battery_access
import control_fixture


def path(route):
    x, y, z = route.feed
    r, s = route.bend, route.direction
    start = App.Vector(x, y, route.top-r)
    middle = App.Vector(x, y+s*r*(1-math.sqrt(.5)), route.top-r+r*math.sqrt(.5))
    end = App.Vector(*route.point(0))
    return Part.Wire([Part.makeLine(App.Vector(x, y, z), start),
                      Part.Arc(start, middle, end).toShape(),
                      Part.makeLine(end, App.Vector(*route.point(route.straight)))])


def wire(route):
    try:
        profile = Part.Wire(Part.makeCircle(route.radius, App.Vector(*route.feed)))
        return path(route).makePipeShell([profile], True, False)
    except Exception as exc:
        raise ValueError(route.design + ' antenna: invalid RadioAntenna solid') from exc


def feed_relief(route, height):
    """Only Radio PCB/component checks may use this sourced-pad neighbourhood."""
    x, y, z = route.feed
    return Part.makeCylinder(route.relief, height + 2, App.Vector(x, y, z-1))


def restraints(route, bottom):
    """Integral open saddles with transverse slots for removable nonmetal ties."""
    result = []
    for distance in route.restraints:
        x, y, z = route.point(distance)
        # Keep the walls below even the lowest permitted wire centre. A taut
        # tie must bear on insulation, rather than bridge above it on plastic.
        block = Part.makeBox(6, 6, z - route.tolerance - bottom, App.Vector(x-3, y-3, bottom))
        groove = Part.makeCylinder(route.envelope, 8, App.Vector(x, y-4, z), App.Vector(0, 1, 0))
        slot = Part.makeBox(8, 2.8, 1.2, App.Vector(x-4, y-1.4, z-3.2))
        result.append(block.cut(groove).cut(slot))
    return result


def retention_windows(route):
    # Narrow along-wire windows only. All other supporting plastic is checked.
    return Part.makeCompound([Part.makeBox(6.01, 6.01, 4.5,
                                          App.Vector(x-3.005, y-3.005, z-3.5))
                              for x, y, z in map(route.point, route.restraints)])


def reserved_shapes(p, compact):
    result = []
    for name, lo, hi, gap in antenna.reservations(p, compact):
        shape = Part.makeBox(*(b-a for a, b in zip(lo, hi)), App.Vector(*lo))
        result.append((name, shape, gap))
    # Full removable peripheral seal envelope, absent from the older solids.
    inner = p['case_diameter']/2 - (10 if compact else 13)
    seal = Part.makeCylinder(inner+1, 2).cut(Part.makeCylinder(inner, 2))
    result.append(('Rear perimeter seal reservation', seal, .5))
    return result


def check(p, objects, compact=False):
    route = antenna.validate(p, compact)
    centreline = path(route)
    if abs(centreline.Length-route.length) > 1e-6:
        raise ValueError(route.design + ' antenna: native centreline is not 78 mm')
    windows = retention_windows(route)
    support = 'RadioCarrier'
    radio_names = {'RadioPCB','RadioLoadedReservation','RadioUnderboardReservation'}
    envelope=radio_mount.envelope(route.feed[2],0 if compact else 180)
    height=envelope['size'][2]-(route.feed[2]-envelope['z'])
    pad = feed_relief(route, height)
    gaps = {}
    for obj in objects:
        if obj.Name == 'RadioAntenna':
            continue
        shape = obj.Shape
        material = getattr(obj, 'Material', '')
        plastic = 'PETG' in material or obj.Name == support
        required = route.plastic_gap if plastic else route.metal_gap
        if obj.Name in radio_names:
            shape = shape.cut(pad)
        if obj.Name == support:
            shape = shape.cut(windows)
        distance = centreline.distToShape(shape)[0] - route.envelope
        if distance < required - 1e-6:
            raise ValueError(f'{route.design} antenna: {obj.Name} clearance {distance:.3f} < {required:g} mm')
        gaps[obj.Name] = distance
    for name, shape, required in reserved_shapes(p, compact):
        distance = centreline.distToShape(shape)[0] - route.envelope
        if distance < required - 1e-6:
            raise ValueError(f'{route.design} antenna: {name} clearance {distance:.3f} < {required:g} mm')
        gaps[name] = distance
    return gaps


def removal(p, fixed, carriers, case_depth_mm, compact=False):
    """Continuous -Z withdrawal: swept wire surfaces plus conservative carrier boxes.

    Rear cover and its seals are released first on the compact design. On the
    original, electronics, seals and rear plate move together. No live harness
    may bridge the moving assembly: disconnect it with the rear supported.
    """
    route = antenna.installation(p, compact)
    if not isinstance(carriers,dict) or set(carriers)!=radio_mount.CHECK_NAMES:
        raise ValueError(route.design+' antenna removal requires every actual radio product/reference')
    for name,shape in carriers.items():
        if not shape.isValid() or len(shape.Solids)!=1:raise ValueError('Invalid radio removal solid: '+name)
    # All bridging harnesses are unplugged; the remaining fixed wiring must
    # stay in the reservation throughout withdrawal as well as when assembled.
    fixed = list(fixed) + [(name, shape) for name, shape, _ in reserved_shapes(p, compact)
                           if 'harness' in name]
    if not math.isfinite(case_depth_mm) or case_depth_mm<=0:raise ValueError('Use the actual resolved body depth for withdrawal')
    travel = case_depth_mm + route.top + 10
    centreline = path(route)
    end = centreline.copy()
    end.translate(App.Vector(0, 0, -travel))
    # The vertical feed edge sweeps into itself; its extremities suffice.
    sweep = Part.makeCompound([centreline, end] + [edge.extrude(App.Vector(0, 0, -travel))
                              for edge in centreline.Edges if edge.BoundBox.YLength > 1e-7])
    failures=[];wire_gaps={}
    for name, shape in fixed:
        distance = sweep.distToShape(shape)[0] - route.envelope
        wire_gaps[name]=distance
        if distance < route.plastic_gap - 1e-6:
            failures.append({'part':name,'stage':'wire','clearance_mm':distance,'required_mm':route.plastic_gap})
    # Continuous exact-solid distance bounds avoid filling the empty regions
    # of the branched carrier. Every actual source product remains required.
    from solid_clearance import translation_clearance
    required=battery_access.definition()['removal']['noncontact_clearance_mm']
    certified={}
    for moving_name,carrier in carriers.items():
        certified[moving_name]={}
        for name,shape in fixed:
            try:
                certified[moving_name][name]=translation_clearance(carrier,shape,(0,0,-travel),required)
            except ValueError as error:
                failures.append({'part':name,'moving':moving_name,'stage':'radio/restraint carrier','detail':str(error)})
    if failures:
        raise ValueError(route.design+' antenna removal: '+json.dumps(failures,allow_nan=False))
    return {'scope':'continuous source-solid translation','travel_mm':travel,'required_gap_mm':required,'required_wire_gap_mm':route.plastic_gap,'wire_gaps_mm':wire_gaps,'certified_pairs':certified}


def radio_products(doc):
    result={}
    for name in radio_mount.CHECK_NAMES:
        obj=doc.getObject(name)
        if obj is None or not hasattr(obj,'Shape') or obj.Shape.isNull():raise ValueError('Missing actual radio service product: '+name)
        result[name]=obj.Shape
    return result


def original_fixed(doc):
    # Classify actual products, never hidden construction tools. Rear screws and
    # washers are removed; their nuts and every body/anchor fastener stay fixed.
    owned=(branch_fuses.CHECK_NAMES|radio_mount.CHECK_NAMES|blackpill_mount.CHECK_NAMES|gps_mount.CHECK_NAMES|sparkle_mount.CHECK_NAMES
           |imu_mount.CHECK_NAMES|boost_mount.CHECK_NAMES|latch_mount.PRODUCT_NAMES|capacitor_mount.CHECK_NAMES
           |battery_access.PART_NAMES|control_fixture.PRODUCT_NAMES)
    fixed = []
    for group in (doc.Manufactured, doc.Electronics, doc.Hardware, doc.Optics):
        for obj in group.Group:
            name = obj.Name
            if name in owned:continue
            if name in {'RearPlate', 'ServiceCover', 'HatchGasket', 'ExternalPowerBlank', 'RadioAntenna'}:
                continue
            if name.startswith(('Vent', 'ControlMembrane', 'RearButton', 'BatteryEnvelope', 'BatteryHeadroom', 'Hatch', 'Sparkle')) or 'Components' in name:
                continue
            if name.startswith('Rear') and name.endswith(('Screw', 'Washer')):
                continue
            fixed.append((name, obj.Shape))
    return fixed


def regression_checks(p, case_depth_mm, compact=False):
    """Exercise the same native predicates against intentional boundary failures."""
    from types import SimpleNamespace
    from solid_clearance import native_translation_regressions
    native_translation_regressions()
    route = antenna.installation(p, compact)
    # The lowest permitted wire crown must stand proud of the saddle walls;
    # otherwise a tightened tie could leave the wire free to slide under it.
    for saddle in restraints(route, 2):
        assert saddle.BoundBox.ZMax < route.top-route.tolerance+route.radius, route.design + ': tie must bear on insulation'
    x, y, z = route.point(30)
    def obstacle(name, x, y, z):
        return SimpleNamespace(Name=name, Material='', Shape=Part.makeBox(.02,.02,.02,App.Vector(x-.01,y-.01,z-.01)))
    def rejects(action, name):
        try:
            action()
        except ValueError as exc:
            assert route.design in str(exc) and name in str(exc), str(exc)
        else:
            raise AssertionError(route.design + ': antenna regression missed ' + name)
    rejects(lambda: check(p, [obstacle('ThinScrew',x,y,z)], compact), 'ThinScrew')
    rejects(lambda: check(p, [obstacle('Tolerance',x+.65,y,z)], compact), 'Tolerance')
    radio_z=route.feed[2];rotation=0 if compact else 180
    xy=next(e for e in p['electronics'] if e['name']=='Radio')['mount_datum'] if compact else (p['radio_x'],p['radio_y'])
    actual=radio_mount.carrier_with_antenna(radio_mount.native_shapes(radio_z,rotation),route,xy)
    actual_carriers={name:actual[name].copy() for name in radio_mount.CHECK_NAMES}
    for shape in actual_carriers.values():shape.translate(App.Vector(*xy,0))
    lowered = obstacle('RemovalSeal',x,y,z-7.215)
    check(p, [lowered], compact)
    rejects(lambda: removal(p,[(lowered.Name,lowered.Shape)],actual_carriers,case_depth_mm,compact), 'RemovalSeal')
    fx, fy, fz = route.feed
    rejects(lambda: check(p, [obstacle('UnexpectedFeedMetal',fx,fy,fz+1)], compact), 'UnexpectedFeedMetal')
    # Contact permissions are local to the named part and bounded in space.
    radio = 'RadioPCB'
    allowed = obstacle(radio,fx,fy,fz+1)
    allowed.Shape = allowed.Shape.fuse(Part.makeBox(1,1,1,App.Vector(0,0,-10)))
    check(p, [allowed], compact)
    outside = obstacle(radio,x,y,z)
    rejects(lambda: check(p, [outside], compact), radio)
    support = 'RadioCarrier'
    rejects(lambda: check(p, [obstacle(support,x,y,z)], compact), support)
    # A support can touch the wire only inside its saddle windows.
    sx, sy, sz = route.point(route.restraints[0])
    retained = obstacle(support,sx,sy,sz)
    # Retain distant material so subtraction does not produce an empty shape.
    retained.Shape = retained.Shape.fuse(Part.makeBox(1,1,1,App.Vector(0,0,-10)))
    check(p, [retained], compact)
