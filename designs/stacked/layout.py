"""Compact layout in millimetres. Shared assets remain owned by design one."""

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "hardware/enclosure"))
import antenna
import latch_mount
import imu_mount
import boost_mount
import capacitor_mount
import gps_mount
import sparkle_mount
import blackpill_mount
import radio_mount


def electronics_census(p):
    names=[entry.get('name') for entry in p['electronics']]
    expected={'SparkleMotion','BlackPill','GPS','IMU','Radio','Boost5V','PowerLatch','BulkCapacitor'}
    if len(names)!=len(expected) or set(names)!=expected:
        raise ValueError('Use the complete selected source-module set; BatterySense/pouch/generic shelves are obsolete')


def reject_legacy_cell_parameters(p):
    if any(key.startswith('battery_') for key in p) or {'runtime_hours','example_total_current_a','example_output_voltage','assumed_efficiency'}.intersection(p):
        raise ValueError('Use the shared selected cell; remove legacy pack/runtime fields')


def parameters():
    p = json.loads((HERE / "parameters.json").read_text())
    reject_legacy_cell_parameters(p)
    electronics_census(p)
    for entry in p['electronics']:
        if entry['name']=='PowerLatch':
            if set(entry)!={'name','centre','source_fixture'} or entry['source_fixture']!='latch':
                raise ValueError('Latch size/Z are now owned by the source fixture; remove obsolete fields and regenerate')
            entry.update(latch_mount.envelope())
        if entry['name']=='IMU':
            if set(entry)!={'name','centre','source_fixture','pcb_bottom_z_mm','rotation_deg'} or entry['source_fixture']!='imu':
                raise ValueError('IMU size/Z are source-fixture derived; remove obsolete fields and regenerate')
            entry.update(imu_mount.envelope(entry['pcb_bottom_z_mm'],entry['rotation_deg']))
        if entry['name']=='Boost5V':
            if set(entry)!={'name','centre','source_fixture','pcb_bottom_z_mm','rotation_deg'} or entry['source_fixture']!='boost':
                raise ValueError('PowerBoost size/Z are source-fixture derived; remove obsolete fields and regenerate')
            entry.update(boost_mount.envelope(entry['pcb_bottom_z_mm'],entry['rotation_deg']))
        if entry['name']=='BulkCapacitor':
            if set(entry)!={'name','centre','source_fixture'} or entry['source_fixture']!='capacitor':
                raise ValueError('Capacitor size/Z are source-holder derived; remove obsolete fields and regenerate')
            entry.update(capacitor_mount.envelope('narrow'))
        if entry['name'] in ('GPS','SparkleMotion','BlackPill','Radio'):
            expected={'GPS':'gps','SparkleMotion':'sparkle','BlackPill':'blackpill','Radio':'radio'}[entry['name']]
            if set(entry)!={'name','mount_datum','source_fixture','pcb_bottom_z_mm','rotation_deg'} or entry['source_fixture']!=expected:
                raise ValueError(entry['name']+' dimensions/centre/Z are source-fixture derived; use mount_datum and remove obsolete fields')
            if expected in ('gps','blackpill','radio'):
                factory={'gps':gps_mount,'blackpill':blackpill_mount,'radio':radio_mount}[expected]
                entry.update(factory.envelope(entry['pcb_bottom_z_mm'],entry['rotation_deg']))
                entry['centre']=list(entry['mount_datum'])
            else:
                bounds=sparkle_mount.envelope(entry['pcb_bottom_z_mm'],entry['rotation_deg'])
                entry.update(size=[bounds[axis][1]-bounds[axis][0] for axis in ('x','y','z')],z=bounds['z'][0],
                             centre=[entry['mount_datum'][i]+sum(bounds[axis])/2 for i,axis in enumerate(('x','y'))])
    acrylic = json.loads((ROOT / "hardware/enclosure/acrylic-optics.json").read_text())[
        "materials"
    ]
    for face, material in (("front", "two_way_mirror"), ("rear", "black_mirror")):
        for quantity in ("reflectance", "transmission"):
            p[face + "_" + quantity] = acrylic[material][quantity]
    p["rear_external_reflectance"] = acrylic["black_mirror"]["reverse_reflectance"]
    return p


def dimensions(p):
    baffle_z = (
        p["circle_back_z"]
        + p["circle_pcb_thickness"]
        + p["led_height"]
        + p["led_baffle_gap"]
    )
    rear_bottom = baffle_z + p["baffle_thickness"] + p["stencil_mirror_gap"]
    rear_z = rear_bottom + p["rear_black_acrylic_thickness"]
    source_z = rear_z  # Thin-sheet equivalent source at the cavity-facing coating.
    front_z = rear_z + p["mirror_gap"]
    pitch_radius = (
        p["inner_count"] * 1000 / p["strip_density"] + p["ring_seam_gap"]
    ) / math.tau
    inner_outer = (
        pitch_radius
        - p["strip_thickness"] / 2
        - p["ring_led_depth"]
        - p["ring_diffuser_led_gap"]
    )
    side_radius = (
        p["side_count"] * 1000 / p["strip_density"] + p["ring_seam_gap"]
    ) / math.tau
    case_radius = p["case_diameter"] / 2
    suspension_scale = (case_radius - 3.6) / math.hypot(55, 73)
    return {
        "case_radius": case_radius,
        "shell_inner_radius": case_radius - 9,
        "board_support_outer_radius": case_radius - 6.7,
        "rear_fastener_radius": case_radius - 10,
        "front_fastener_radius": (case_radius + p["mirror_radius"]) / 2,
        "mirror_seat_radius": p["mirror_radius"] + 0.3,
        "mirror_lip_radius": p["mirror_radius"] - 0.6,
        "inner_foot_radius": p["mirror_radius"] - 0.1,
        "suspension_x": 55 * suspension_scale,
        "suspension_y": 73 * suspension_scale,
        "baffle_z": baffle_z,
        "source_z": source_z,
        "rear_bottom": rear_bottom,
        "rear_z": rear_z,
        "front_z": front_z,
        "depth": front_z + p["front_mirror_thickness"] + p["bezel_thickness"],
        "pitch_radius": pitch_radius,
        "side_radius": side_radius,
        "side_height": p["side_rows"] * p["strip_width"],
        "side_row_z": [
            p["side_bottom_z"] + (row + 0.5) * p["strip_width"]
            for row in range(p["side_rows"])
        ],
        "inner_outer": inner_outer,
        "wall_radius": inner_outer - p["ring_diffuser_thickness"],
        "ring_z": (rear_z + front_z) / 2,
    }


def validate(p):
    reject_legacy_cell_parameters(p)
    electronics_census(p)
    if not isinstance(p["side_rows"], int) or p["side_rows"] < 1:
        raise ValueError("Side band needs a positive whole number of strips")
    antenna.validate(p, compact=True)
    d = dimensions(p)
    if not math.isfinite(p["side_axial_scatter_mm"]) or p["side_axial_scatter_mm"] <= 0:
        raise ValueError("Side diffuser needs a finite positive axial scatter scale")
    if (
        p["side_bottom_z"] < 14
        or p["side_bottom_z"] + d["side_height"] > d["rear_bottom"] - 1.8
    ):
        raise ValueError("Side strips block the suspension slots or mirror frame seat")
    if not p["circle_diameter"] < p["case_diameter"] < 250:
        raise ValueError("Body must fit the 166 mm board and remain below 250 mm")
    if d["wall_radius"] - p["circle_diameter"] / 2 < 0.5:
        raise ValueError("Inner ring blocks the full Fibonacci source")
    if not math.isfinite(p["mirror_gap"]) or p["mirror_gap"] - p["strip_width"] < 2:
        raise ValueError("Strip needs clearance between both mirror planes")
    if d["pitch_radius"] + p["strip_thickness"] / 2 + 1.8 >= p["case_diameter"] / 2:
        raise ValueError("Insufficient inner-ring carrier wall")
    if p["front_aperture_radius"] <= d["wall_radius"]:
        raise ValueError("Bezel blocks the inward diffuser")
    if (
        p["mirror_radius"] <= d["wall_radius"]
        or p["mirror_radius"] >= p["case_diameter"] / 2 - 2
    ):
        raise ValueError("Mirror does not fit its seat")
    if (
        d["mirror_seat_radius"]
        - d["pitch_radius"]
        - p["strip_thickness"] / 2
        < 0.1
    ):
        raise ValueError("Mirror seat blocks the inner strip")
    if d["mirror_lip_radius"] <= d["inner_outer"]:
        raise ValueError("Mirror lip blocks the inner diffuser")
    side_face = d["side_radius"] + p["strip_thickness"] / 2 + p["ring_led_depth"]
    if p["case_diameter"] / 2 - p["side_diffuser_thickness"] - side_face < 1:
        raise ValueError("Side diffuser blocks its LED packages")
    for side in ("front", "rear"):
        r, t = p[side + "_reflectance"], p[side + "_transmission"]
        if min(r, t) < 0 or r + t > 1:
            raise ValueError("Mirror reflection plus transmission must be at most one")
    for e in p["electronics"]:
        if e['name']=='BulkCapacitor' and any(e.get(key)!=value for key,value in capacitor_mount.envelope('narrow').items()):
            raise ValueError('Resolved capacitor dimensions differ from the source holder')
        if e['name']=='PowerLatch' and any(e.get(key)!=value for key,value in latch_mount.envelope().items()):
            raise ValueError('Resolved latch dimensions differ from the single source fixture')
        for name,factory in (('IMU',imu_mount),('Boost5V',boost_mount)):
            if e['name']==name and any(e.get(key)!=value for key,value in factory.envelope(e['pcb_bottom_z_mm'],e['rotation_deg']).items()):
                raise ValueError(name+' resolved dimensions differ from the selected source fixture')
        if e['name'] in ('GPS','BlackPill','Radio'):
            factory={'GPS':gps_mount,'BlackPill':blackpill_mount,'Radio':radio_mount}[e['name']]
            expected=factory.envelope(e['pcb_bottom_z_mm'],e['rotation_deg'])
            if e['centre']!=e['mount_datum'] or any(e.get(key)!=value for key,value in expected.items()):
                raise ValueError(e['name']+' resolved geometry differs from the source fixture')
        if e['name']=='SparkleMotion':
            bounds=sparkle_mount.envelope(e['pcb_bottom_z_mm'],e['rotation_deg'])
            size=[bounds[axis][1]-bounds[axis][0] for axis in ('x','y','z')]
            centre=[e['mount_datum'][i]+sum(bounds[axis])/2 for i,axis in enumerate(('x','y'))]
            if e['size']!=size or e['centre']!=centre or e['z']!=bounds['z'][0]:raise ValueError('Sparkle resolved geometry differs from its source datum')
        x, y = e["centre"]
        w, l, h = e["size"]
        if (
            max(
                math.hypot(x + sx * w / 2, y + sy * l / 2)
                for sx in (-1, 1)
                for sy in (-1, 1)
            )
            > d["shell_inner_radius"]-.25
        ):
            raise ValueError(e["name"] + " exceeds the electronics bay")
        if e["z"] + h > p["circle_back_z"] - 2:
            raise ValueError(e["name"] + " blocks the board support")
    return d
