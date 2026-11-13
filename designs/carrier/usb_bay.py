"""Mount the USB-C inlet and regulator inside the removable rear cover."""

import FreeCAD as App
import Part

from native import box, cylinder, require_solid
from seals import require_material, rounded_box

PORT_X = 25.5
PORT_Y = 10.6
PORT_Z = -12.12
# The socket nose extends 1.40 mm beyond the 1.20 mm PCB.
# The drawing locates the mating axis 4.61 - 2.56 mm above the PCB.
INLET_EDGE_Y = PORT_Y + .53 + 1.40
INLET_BOTTOM_Z = PORT_Z - (4.61 - 2.56) - 1.20


def port_profile(width, height, radius, first, last):
    # Build in XY and rotate the face into the XZ plane. Positive depth is +Y.
    shape = rounded_box(-width / 2, -height / 2, width / 2, height / 2,
                        radius, -last, -first)
    shape.rotate(App.Vector(), App.Vector(1, 0, 0), 90)
    shape.translate(App.Vector(PORT_X, PORT_Y, PORT_Z))
    return shape


def power_bay(rear):
    outer = rounded_box(7, PORT_Y, 62, 75, 3, -21, 1.3)
    interior = rounded_box(9, PORT_Y + 1.8, 60, 73, 1.3, -18.8, 3)
    # Retain the rear ribs and the foundations of the carrier and retainer
    # bosses above the bay. Open two windows for installation from inside.
    inlet_access = rounded_box(10, PORT_Y + 1.8, 41, 45.1, 1.3, -2, 5.4)
    buck_access = rounded_box(10, 50.8, 59, 72.65, 1.5, -2, 5.4)
    rear = rear.cut(inlet_access).cut(buck_access)
    bay = outer.cut(interior)
    panel_opening = port_profile(9.12, 3.34, 1.43, -.1, 1.9)
    gasket_pocket = port_profile(11, 5.5, 1.6, 1.2, 1.91)
    bay = bay.cut(panel_opening).cut(gasket_pocket)
    gasket_land = port_profile(10.64, 4.86, 1.6, 1.15, 1.2).cut(
        port_profile(9.12, 3.34, 1.43, 1.14, 1.21)
    )
    require_material("USB-C gasket land", gasket_land, bay)

    # Blind pilots for two inlet screws and four stock regulator mounts.
    # The port face transfers plug load to the reinforced cover.
    inlet_mounts = [(PORT_X - 12, INLET_EDGE_Y + 29), (PORT_X + 12, INLET_EDGE_Y + 2)]
    buck_mounts = [(x, y) for x in (16.22, 51.78) for y in (54.38, 69.62)]
    mounts = Part.makeCompound([
        cylinder(2.6, -19.1, top, xy)
        for points, top in ((inlet_mounts, INLET_BOTTOM_Z), (buck_mounts, -17.4))
        for xy in points
    ])
    holes = Part.makeCompound([
        cylinder(.8, -19.4, top + .1, xy)
        for points, top in ((inlet_mounts, INLET_BOTTOM_Z), (buck_mounts, -17.4))
        for xy in points
    ])
    rear = rear.fuse(bay).fuse(mounts).cut(holes).removeSplitter()
    require_solid("Rear cover with internal USB-C bay", rear)

    # Envelopes exclude the supported undersides and allow space at the
    # regulator's ends for wires soldered flat at the bench.
    boards = {
        "USBPDInlet": box((
            [11.5, INLET_EDGE_Y, INLET_BOTTOM_Z],
            [39.5, INLET_EDGE_Y + 31, INLET_BOTTOM_Z + 5.85],
        )),
        "USBPortNose": port_profile(8.94, 3.16, 1.40, .53, 1.73),
        "USBPDRegulator": box(([11, 50.8, -17.4], [58, 72.6, -7.1])),
        "USBPlugInsertion": box(([13.5, PORT_Y - 20, -17.5], [37.5, PORT_Y, -6.5])),
    }
    cable = box(([PORT_X - 2, -88, PORT_Z - 2], [PORT_X + 2, PORT_Y - 20, PORT_Z + 2]))
    install_paths = {
        "Inlet PCB installation": box((
            [11.5, INLET_EDGE_Y + 1.3, INLET_BOTTOM_Z],
            [39.5, INLET_EDGE_Y + 32.3, 8],
        )),
        "USB-C nose installation": box((
            [PORT_X - 4.47, PORT_Y + 1.83, PORT_Z - 1.58],
            [PORT_X + 4.47, PORT_Y + 3.03, 8],
        )),
        "USB-C nose seating": port_profile(8.94, 3.16, 1.40, .53, 3.03),
        "Regulator PCB installation": box(([13.68, 51.83, -17.4], [54.32, 72.15, 8])),
    }
    return rear, boards, cable, install_paths
