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
from geometry import battery_centres, led_centres, mask_cells, mounting_points, necklace_anchors, optical_dimensions


def check():
    p = build.read_parameters(HERE / 'smart-compass.FCStd')
    doc = App.openDocument(str(HERE / 'smart-compass.FCStd'))
    doc.recompute()
    assert set(doc.InputStatus.ParameterKeys) == {k for k in p if not k.startswith('_')}, 'Saved parameter schema differs from the generator'
    b = SimpleNamespace(p=p, doc=doc, parts=list(doc.Manufactured.Group), hardware=list(doc.Electronics.Group), references=list(doc.Optics.Group))
    layout = json.loads((HERE / 'fibonacci256-layout.json').read_text())
    centres = led_centres(layout, p)
    cells = mask_cells(centres, p['mask_edge_radius'], p['mask_web'])
    build.check_model(b, centres, cells)
    wood_bottom = p['case_depth']-p['front_bezel_thickness']-p['acrylic_thickness']-p['wood_thickness']
    assert math.isclose(doc.WoodMask.Shape.BoundBox.ZMin, wood_bottom, abs_tol=1e-7), 'Master retained an exploded wood placement'
    assert math.isclose(doc.CellBaffle.Shape.BoundBox.ZMax, wood_bottom, abs_tol=1e-7), 'Master retained an exploded baffle placement'
    assert math.isclose(doc.FrontAcrylic.Shape.BoundBox.ZMin, wood_bottom+p['wood_thickness'], abs_tol=1e-7)
    assert math.isclose(doc.CircleBezel.Shape.BoundBox.ZMax, p['case_depth'], abs_tol=1e-7)
    for prefix in ('OpticalDeck','BarrelFrame','RearPlate'):
        quarters = [doc.getObject(prefix+f'Q{i}') for i in range(1,5)]
        assert all(q in b.parts for q in quarters), 'Quarter missing from manufactured parts'
        assert not App.GuiUp or not doc.getObject(prefix).Visibility, 'Unsplit construction copy visible'
    assert doc.FrontBezel in b.parts and len(doc.FrontBezel.Shape.Solids) == 1, 'Black acrylic border must be one connected sheet part'
    assert doc.FrontBezel.Material.startswith('Opaque black acrylic sheet')
    assert not any(doc.getObject(f'FrontBezelQ{i}') for i in range(1,5)), 'Black acrylic border must not have printed quarter seams'
    assert math.isclose(doc.FrontBezel.Shape.BoundBox.ZMin,p['case_depth']-p['front_bezel_thickness'],abs_tol=1e-7)
    assert math.isclose(doc.FrontBezel.Shape.BoundBox.ZMax,p['case_depth'],abs_tol=1e-7)
    border_circles = sorted({(round(edge.Curve.Center.x,6),round(edge.Curve.Center.y,6),round(edge.Curve.Radius,6)) for edge in doc.FrontBezel.Shape.Edges if hasattr(edge.Curve,'Radius')})
    assert doc.RearPlate not in b.parts and len(doc.RearPlate.Shape.Solids) == 1
    assert doc.RearPlate.Material.startswith('Printed PETG')
    assert math.isclose(doc.RearPlate.Shape.BoundBox.ZMin,0,abs_tol=1e-7)
    # Unreinforced skin is thin; integral ribs and bolt lands are thicker.
    assert doc.RearPlate.Shape.isInside(App.Vector(15,-95,p['rear_skin_thickness']/2),1e-7,True)
    assert not doc.RearPlate.Shape.isInside(App.Vector(15,-95,(p['rear_skin_thickness']+p['rear_thickness'])/2),1e-7,True)
    assert doc.RearPlate.Shape.isInside(App.Vector(40,-80,p['rear_skin_thickness']+p['rear_rib_height']/2),1e-7,True)
    assert doc.RearPlate.Shape.isInside(App.Vector(121,0,p['rear_thickness']-.1),1e-7,True)
    assert doc.CirclePCB.Shape.BoundBox.ZMin-doc.sparkleComponents.Shape.BoundBox.ZMax >= 1-1e-7, 'Sparkle needs at least 1 mm circle clearance'
    assert doc.InnerLEDs.EmissionDirection == 'Radially inward toward circle'
    assert doc.OuterLEDs.EmissionDirection == 'Radially outward'
    assert doc.HaloLEDs.EmissionDirection == 'Radially outward'
    assert len(doc.HaloLEDs.Shape.Solids) == p['halo_count']
    assert len(doc.InnerLEDs.Shape.Solids) == p['inner_count']
    assert len(doc.OuterLEDs.Shape.Solids) == p['outer_count']
    d = optical_dimensions(p)
    assert d['visible_mirror_width'] >= 20
    assert math.isclose(doc.FrontMirror.Shape.BoundBox.ZMin-doc.RearMirror.Shape.BoundBox.ZMax,d['mirror_separation'],abs_tol=1e-7)
    assert doc.EdgeDiffuserSeam.Shape.BoundBox.ZMin <= doc.OuterLEDs.Shape.BoundBox.ZMin
    assert doc.EdgeDiffuserSeam.Shape.BoundBox.ZMax >= doc.OuterLEDs.Shape.BoundBox.ZMax
    assert doc.EdgeDiffuserSeam.Material.startswith('Black LED-diffusing acrylic'), 'Curved outside wall must use black acrylic'
    assert math.isclose(doc.EdgeDiffuserOuter.Radius.Value-doc.EdgeDiffuserInner.Radius.Value,p['edge_diffuser_thickness'],abs_tol=1e-7)
    edge_template_width = math.tau*(doc.EdgeDiffuserOuter.Radius.Value+doc.EdgeDiffuserInner.Radius.Value)/2-1
    edge_template_height = doc.EdgeDiffuserSeam.Shape.BoundBox.ZLength
    if App.GuiUp:
        assert all(c < .06 for c in doc.EdgeDiffuserSeam.ViewObject.ShapeColor[:3]), 'Outside wall still displays a pale finish'
        assert doc.EdgeDiffuserSeam.ViewObject.Transparency == 0, 'Black CAD finish must not display the old transparent side cover'
    assert math.isclose(doc.OuterStripSeam.Shape.BoundBox.Center.z,doc.EdgeDiffuserSeam.Shape.BoundBox.Center.z,abs_tol=1e-7), 'Outer strip is not centered in the outside surface'
    assert math.isclose(doc.EdgeDiffuserSeam.Shape.BoundBox.ZMin,p['rear_thickness'],abs_tol=1e-7)
    assert math.isclose(doc.EdgeDiffuserSeam.Shape.BoundBox.ZMax,p['case_depth']-p['front_bezel_thickness'],abs_tol=1e-7)
    assert not any(doc.getObject(name) for name in ('ButtonActuator0','SparkleUSBPowerPort','RadioPort','PowerSwitchPort')), 'Exposed side pegs or windows returned'
    # Rear skin stays closed except for covered vent/control/service passages.
    assert doc.RearPlate.Shape.isInside(App.Vector(0,-95,p['rear_skin_thickness']/2),1e-7,True)
    for i in range(4):
        membrane = doc.getObject(f'VentMembrane{i}')
        hole = doc.getObject(f'VentHole{i}')
        assert math.isclose(membrane.Shape.BoundBox.ZMax,0,abs_tol=1e-7)
        assert membrane.Shape.BoundBox.XLength > hole.Shape.BoundBox.XLength+4
        assert doc.getObject(f'VentGuard{i}') in b.parts
    for side in (-1,1):
        (x,y),primary,secondary = necklace_anchors(p,side)
        link = doc.getObject('NecklaceLink'+str(0 if side==-1 else 1))
        assert math.isclose(link.Shape.BoundBox.ZLength,p['necklace_link_thickness'],abs_tol=1e-7)
        assert len(link.Shape.Solids) == 1
        screw_path = Part.makeLine(App.Vector(*secondary,-4),App.Vector(*secondary,p['rear_thickness']+p['necklace_link_thickness']+6.1))
        assert not any(screw_path.common(obj.Shape).Length > 1e-7 for obj in b.parts), 'Independent necklace anchor screw is blocked'
        eye_path = Part.makeLine(App.Vector(x,62,-3),App.Vector(x,62,p['rear_thickness']+p['necklace_link_thickness']+.1))
        assert not any(eye_path.common(obj.Shape).Length > 1e-7 for obj in b.parts), 'A cover blocks a necklace eye'
    for x,y in mounting_points(p):
        bolt_path = Part.makeLine(App.Vector(x,y,-4),App.Vector(x,y,p['case_depth']+1))
        assert not any(bolt_path.common(obj.Shape).Length > 1e-7 for obj in b.parts), 'A cover blocks a body bolt'
        nut_space = Part.makeCylinder(4,6,App.Vector(x,y,-6))
        assert not any(nut_space.common(obj.Shape).Volume > .05 for obj in b.parts), 'No rear nut/tool clearance'
    # The saved centre must stay open for the full visible mirror annulus.
    for r in (p['mirror_view_inner_radius']+.1,p['mirror_view_outer_radius']-.1):
        for i in range(12):
            a = i*math.tau/12
            point = App.Vector(r*math.cos(a),r*math.sin(a),p['case_depth']-p['front_bezel_thickness']/2)
            assert not any(obj.Shape.isInside(point,1e-7,True) for obj in b.parts), 'Mirror view is masked by a manufactured part'
    wood_z = p['case_depth']-p['front_bezel_thickness']-p['acrylic_thickness']-p['wood_thickness']/2
    for x, y in centres:
        assert not doc.WoodMask.Shape.isInside(App.Vector(x,y,wood_z), 1e-7, True), 'LED centre blocked by native wood'
    assert doc.CellBaffle.Shape.common(doc.CircleLEDs.Shape).Volume < 1e-7, 'Retention feet touch an LED body'
    # Check room for each tongue to move inward far enough to release its bead.
    # This is geometric clearance, not a flex/strength simulation.
    for i in range(3):
        angle = math.radians(120*i)
        released = doc.getObject(f'CircleClip{i}').Shape.copy()
        released.translate(App.Vector(-p['circle_clip_release_travel']*math.cos(angle),-p['circle_clip_release_travel']*math.sin(angle),0))
        for obj in (doc.OpticalFrame,doc.CirclePCB,doc.CellBaffle,doc.WoodMask,doc.FrontAcrylic):
            assert not released.common(obj.Shape).Solids, 'No snap release clearance: '+obj.Name
    assert len(doc.BoardMounts.Shape.Solids) == 16, 'Missing board rail/standoff/power-board support'
    assert doc.BoardMounts not in b.parts, 'Mounts must be integral with the rear'
    for i,(x,y) in enumerate(battery_centres(p)):
        cell = doc.getObject(f'BatteryEnvelope{i}')
        assert math.isclose(cell.Shape.BoundBox.ZLength,p['battery_height'],abs_tol=1e-7)
        assert math.isclose(cell.Shape.BoundBox.Center.x,x,abs_tol=1e-7)
        assert math.isclose(cell.Shape.BoundBox.Center.y,y,abs_tol=1e-7)
        assert doc.RearPlate.Shape.common(cell.Shape).Volume < 1e-7
    assert doc.powerComponents.Shape.BoundBox.ZMax < p['mirror_back_z']-p['strip_wall']-.5
    # GUI triangulation can shrink a circular bounding box. Compare laser
    # radii with exact BRep circles, not the display mesh's approximate bounds.
    front_mirror_radii = sorted({edge.Curve.Radius for edge in doc.FrontMirror.Shape.Edges if hasattr(edge.Curve,'Radius')})
    assert len(front_mirror_radii) == 2
    # A native expression must follow a sheet edit after recompute.
    doc.Parameters.set('B' + str(doc.InputStatus.ParameterKeys.index('battery_height')+2), '=' + str(p['battery_height']-1) + ' mm')
    doc.recompute()
    assert math.isclose(doc.BatteryEnvelope0.Shape.BoundBox.ZLength, p['battery_height']-1, abs_tol=1e-7)
    App.closeDocument(doc.Name)  # Do not save this test edit.
    ns = {'s':'http://www.w3.org/2000/svg'}
    wood = ET.parse(HERE / 'exports/wood-fibonacci-mask.svg')
    assert len(wood.findall('.//s:polygon',ns)) == 256
    assert len(wood.findall('.//s:circle',ns)) == 1
    for node, cell in zip(wood.findall('.//s:polygon',ns)[:256], cells):
        points = [tuple(map(float, pair.split(','))) for pair in node.attrib['points'].split()]
        assert len(points) == len(cell)
        assert all(math.dist(a,b) < 1e-5 for a,b in zip(points,cell)), 'Laser contour differs from native cell'
    acrylic = ET.parse(HERE / 'exports/front-acrylic.svg')
    assert len(acrylic.findall('.//s:circle',ns)) == 1
    for filename in ('circle-alignment-overlay.svg','assembly-section.svg','front-mirror.svg','rear-mirror.svg','edge-diffuser.svg'):
        ET.parse(HERE / 'exports' / filename)
    edge_template = ET.parse(HERE/'exports/edge-diffuser.svg').getroot()
    assert math.isclose(float(edge_template.attrib['width'].removesuffix('mm')),edge_template_width,abs_tol=1e-5)
    assert math.isclose(float(edge_template.attrib['height'].removesuffix('mm')),edge_template_height,abs_tol=1e-5)
    front_mirror = ET.parse(HERE/'exports/front-mirror.svg')
    radii = [float(c.attrib['r']) for c in front_mirror.findall('.//s:circle',ns)]
    assert len(radii)==2 and math.isclose(min(radii),p['mirror_inner_radius'])
    assert all(math.isclose(a,b,abs_tol=1e-5) for a,b in zip(sorted(radii),front_mirror_radii)), 'Laser radii differ from exact native mirror circles'
    border = ET.parse(HERE/'exports/outer-black-acrylic.svg')
    cut_circles = sorted((float(c.attrib['cx']),float(c.attrib['cy']),float(c.attrib['r'])) for c in border.findall('.//s:circle',ns))
    assert len(cut_circles) == 8 and cut_circles == border_circles, 'Black acrylic cut paths differ from native outline or six bolt holes'
    assert not (HERE/'exports/rear-clear-acrylic.svg').exists(), 'Superseded acrylic rear laser file remains'
    assembly = Part.read(str(HERE / 'exports/smart-compass.step'))
    assert assembly.isValid() and len(assembly.Solids) >= 256+p['halo_count']+p['inner_count']+p['outer_count']
    manifest = json.loads((HERE/'exports/parts.json').read_text())
    assert not next(v['printed'] for v in manifest['volumes'] if v['name']=='FrontBezel'), 'Black acrylic border cannot be a printed part'
    assert not any(name.startswith('FrontBezel') for name in manifest['stl_files']), 'Superseded printed border STL remains'
    assert all(v['printed'] for v in manifest['volumes'] if v['name'].startswith('RearPlateQ'))
    assert len([name for name in manifest['stl_files'] if name.startswith('RearPlateQ')]) == 4, 'Missing printed rear quarter'
    assert not any(name.startswith(('BoardMounts','BatteryStrapSlots','HatchStandoff')) for name in manifest['stl_files']), 'Integral support exported twice'
    assert len([name for name in manifest['stl_files'] if name.startswith('NecklaceLink')]) == 2
    assert set(manifest['stl_files']) == {f.name for f in (HERE/'exports').glob('*.stl')}
    for filename in manifest['stl_files']:
        file = HERE/'exports'/filename
        mesh = Mesh.Mesh(str(file))
        assert mesh.isSolid(), 'STL is not closed: ' + file.name
        assert math.isclose(mesh.BoundBox.ZMin,0,abs_tol=1e-5), 'STL is not on bed: '+filename
        assert mesh.BoundBox.XLength+2*p['print_margin'] <= p['print_bed_x']
        assert mesh.BoundBox.YLength+2*p['print_margin'] <= p['print_bed_y']
    for changes in ({'battery_count':3}, {'battery_spacing':30}, {'rear_skin_thickness':2}, {'rear_rib_height':4}, {'necklace_link_thickness':3}, {'battery_width':500}, {'battery_x':200}, {'battery_height':24}, {'inner_count':72.5}, {'assumed_efficiency':0}, {'mask_web':-1}, {'mirror_view_outer_radius':100}, {'inner_count':72}, {'case_depth':p['case_depth']-3}, {'edge_diffuser_radius':121}, {'edge_diffuser_thickness':4}, {'halo_count':60}, {'halo_count':80}, {'edge_bottom_z':30.5}, {'vent_patch_radius':4}, {'circle_clip_release_travel':.5}):
        try:
            build.validate_parameters(dict(p, **changes))
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid parameters accepted: ' + repr(changes))
    print('CAD CHECK PASS: saved native geometry, clear radial light paths, mirror gap, 256 apertures, sheet expression, laser contours, STEP, closed bed-sized STL meshes and invalid-fit rejection', flush=True)
