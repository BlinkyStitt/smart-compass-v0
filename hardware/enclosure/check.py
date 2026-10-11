"""Check the delivered native model and exports inside FreeCAD's Python runtime."""
import json
import math
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import xml.etree.ElementTree as ET

import FreeCAD as App
import Mesh
import Part

HERE = Path(os.environ.get('SC_CAD_DIR', Path(__file__).resolve().parent))
sys.path.insert(0, str(HERE))
import build
from geometry import led_centres, mask_cells


def check():
    p = build.read_parameters(HERE / 'smart-compass.FCStd')
    doc = App.openDocument(str(HERE / 'smart-compass.FCStd'))
    doc.recompute()
    b = SimpleNamespace(p=p, doc=doc, parts=list(doc.Manufactured.Group), hardware=list(doc.Electronics.Group), references=list(doc.Optics.Group))
    layout = json.loads((HERE / 'fibonacci256-layout.json').read_text())
    centres = led_centres(layout, p)
    cells = mask_cells(centres, p['mask_edge_radius'], p['mask_web'])
    build.check_model(b, centres, cells)
    wood_bottom = p['case_depth']-p['front_bezel_thickness']-p['acrylic_thickness']-p['wood_thickness']
    assert math.isclose(doc.WoodMask.Shape.BoundBox.ZMin, wood_bottom, abs_tol=1e-7), 'Master retained an exploded wood placement'
    assert math.isclose(doc.CellBaffle.Shape.BoundBox.ZMax, wood_bottom, abs_tol=1e-7), 'Master retained an exploded baffle placement'
    assert math.isclose(doc.FrontAcrylic.Shape.BoundBox.ZMin, wood_bottom+p['wood_thickness'], abs_tol=1e-7)
    assert math.isclose(doc.FrontBezel.Shape.BoundBox.ZMax, p['case_depth'], abs_tol=1e-7)
    wood_z = p['case_depth']-p['front_bezel_thickness']-p['acrylic_thickness']-p['wood_thickness']/2
    for x, y in centres:
        assert not doc.WoodMask.Shape.isInside(App.Vector(x,y,wood_z), 1e-7, True), 'LED centre blocked by native wood'
    assert doc.CellBaffle.Shape.common(doc.CircleLEDs.Shape).Volume < 1e-7, 'Retention feet touch an LED body'
    assert len(doc.BoardMounts.Shape.Solids) == 14, 'Missing board rail/standoff'
    assert math.isclose(doc.BatteryEnvelope.Shape.BoundBox.ZLength, p['battery_height'], abs_tol=1e-7)
    # A native expression must follow a sheet edit after recompute.
    doc.Parameters.set('B' + str(doc.InputStatus.ParameterKeys.index('battery_height')+2), '=' + str(p['battery_height']-1) + ' mm')
    doc.recompute()
    assert math.isclose(doc.BatteryEnvelope.Shape.BoundBox.ZLength, p['battery_height']-1, abs_tol=1e-7)
    App.closeDocument(doc.Name)  # Do not save this test edit.
    ns = {'s':'http://www.w3.org/2000/svg'}
    wood = ET.parse(HERE / 'exports/wood-fibonacci-mask.svg')
    assert len(wood.findall('.//s:polygon',ns)) == 272
    assert len(wood.findall('.//s:circle',ns)) == 7
    for node, cell in zip(wood.findall('.//s:polygon',ns)[:256], cells):
        points = [tuple(map(float, pair.split(','))) for pair in node.attrib['points'].split()]
        assert len(points) == len(cell)
        assert all(math.dist(a,b) < 1e-5 for a,b in zip(points,cell)), 'Laser contour differs from native cell'
    acrylic = ET.parse(HERE / 'exports/front-acrylic.svg')
    assert len(acrylic.findall('.//s:circle',ns)) == 7
    for filename in ('circle-alignment-overlay.svg','assembly-section.svg'):
        ET.parse(HERE / 'exports' / filename)
    assembly = Part.read(str(HERE / 'exports/smart-compass.step'))
    assert assembly.isValid() and len(assembly.Solids) > 400
    files = list((HERE / 'exports').glob('*.stl'))
    assert len(files) == 6
    for file in files:
        mesh = Mesh.Mesh(str(file))
        assert mesh.isSolid(), 'STL is not closed: ' + file.name
    for changes in ({'battery_width':500}, {'battery_x':200}, {'inner_count':72.5}, {'assumed_efficiency':0}, {'mask_web':-1}):
        try:
            build.validate_parameters(dict(p, **changes))
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid parameters accepted: ' + repr(changes))
    print('CAD CHECK PASS: reopened native geometry, 256 clear LED centres, sheet expression, laser contours, STEP, six closed STL meshes and invalid-fit rejection', flush=True)
