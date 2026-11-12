"""Verify catalog insulating washers on the existing Fibonacci board seats."""

import FreeCAD as App
import Part

# Keystone 3153, 0.312 x 0.098 x 0.047 inch.
OUTSIDE_RADIUS = .312 * 25.4 / 2
BORE_RADIUS = .098 * 25.4 / 2
THICKNESS = .047 * 25.4


def board_washers(baseline):
    pcb = baseline.getObject("FibonacciPCB").Shape
    z = pcb.BoundBox.ZMax
    clearances = {name: baseline.getObject(name).Shape for name in (
        "ElectronicsShell", "EGLStencil", "CircleLEDs", "InnerLEDs", "Side0LEDs",
        "Side1LEDs", "SideDiffuser", "InnerDiffuser", "RearCouplingMirror",
    )}
    shapes = {}
    bearing = []
    offset = BORE_RADIUS - 1.0  # Movement over the nominal 2 mm screw shaft.
    for index in range(3):
        centre = baseline.getObject(f"BoardClipScrew{index}").Shape.BoundBox.Center

        def tube(outer, inner, height, bottom):
            a = Part.makeCylinder(outer, height, App.Vector(centre.x, centre.y, bottom))
            b = Part.makeCylinder(inner, height + .2, App.Vector(centre.x, centre.y, bottom - .1))
            return a.cut(b)

        patch = tube(OUTSIDE_RADIUS - offset, BORE_RADIUS + offset, .02, z - .02)
        area = patch.common(pcb).Volume / .02
        if area < 4:
            raise ValueError(f"Fibonacci washer {index} loses edge bearing")
        worst = tube(OUTSIDE_RADIUS + offset, BORE_RADIUS - offset, THICKNESS, z)
        for name, shape in clearances.items():
            if worst.BoundBox.intersect(shape.BoundBox) and worst.common(shape).Volume > .001:
                raise ValueError(f"Fibonacci washer {index} enters {name}")
        shapes[f"FibonacciNylonWasher{index}"] = tube(OUTSIDE_RADIUS, BORE_RADIUS, THICKNESS, z)
        bearing.append(area)
    return shapes, bearing
