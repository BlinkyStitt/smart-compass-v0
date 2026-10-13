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
from geometry import battery_centres, cavity_diffusers, led_centres, mask_cells, mounting_points, necklace_anchors, optical_dimensions, rear_mounting_points, ring_radius, wood_bottom


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
    wood_z = wood_bottom(p)
    assert math.isclose(doc.WoodMask.Shape.BoundBox.ZMin, wood_z, abs_tol=1e-7), 'Master retained an exploded wood placement'
    assert doc.getObject('CellBaffle') is None, 'A second full cell grid remains in the model'
    led_top = doc.CircleLEDs.Shape.BoundBox.ZMax
    assert .5-1e-7 <= wood_z-led_top <= .8+1e-7, 'Wood grid leaves an excessive light-leak gap or touches LEDs'
    assert math.isclose(doc.WoodMask.Shape.BoundBox.ZLength,p['wood_thickness'],abs_tol=1e-7)
    for i in range(3):
        foot = doc.getObject(f'CircleRimFoot{i}')
        assert foot in b.parts and len(foot.Shape.Solids) == 1
        assert math.isclose(foot.Shape.BoundBox.ZMin,p['circle_back_z']+p['circle_pcb_thickness'],abs_tol=1e-7)
        assert math.isclose(foot.Shape.BoundBox.ZMax,wood_z,abs_tol=1e-7)
        assert foot.Shape.common(doc.CircleLEDs.Shape).Volume < 1e-7, 'Rim spacer touches an LED body'
        tops = [f for f in foot.Shape.Faces if f.BoundBox.ZLength < 1e-7 and abs(f.BoundBox.ZMin-wood_z) < 1e-7]
        bases = [f for f in doc.WoodMask.Shape.Faces if f.BoundBox.ZLength < 1e-7 and abs(f.BoundBox.ZMin-wood_z) < 1e-7]
        assert sum(top.common(base).Area for top in tops for base in bases) >= 1.5, 'Rim spacer misses the wood grid rim'
    assert math.isclose(doc.FrontSheet.Shape.BoundBox.ZMin,p['front_plane_z'],abs_tol=1e-7)
    assert math.isclose(doc.FrontSheet.Shape.BoundBox.ZLength,p['acrylic_thickness'],abs_tol=1e-7)
    assert math.isclose(p['front_plane_z']-doc.WoodMask.Shape.BoundBox.ZMax,p['wood_to_sheet_gap'],abs_tol=1e-7)
    for name in ('OpticalDeck','BarrelFrame','RearPlate','FrontSheet'):
        obj=doc.getObject(name)
        assert obj in b.parts and len(obj.Shape.Solids)==1
    # Whole circular products remain full-size single solids, never arc segments.
    for name in ('OpticalDeck','BarrelFrame','RearPlate'):
        assert min(doc.getObject(name).Shape.BoundBox.XLength,doc.getObject(name).Shape.BoundBox.YLength)>230
    joint=p['mirror_back_z']-p['strip_wall']
    for x,y in mounting_points(p):
        for name,z,sign in (('OpticalDeck',joint,1),('BarrelFrame',joint,-1)):
            shape=doc.getObject(name).Shape
            assert not shape.isInside(App.Vector(x+1.85,y,z+sign*.05),1e-7,True), 'Bore entry is square: '+name
            assert shape.isInside(App.Vector(x+1.85,y,z+sign*.6),1e-7,True), 'Lead-in removed the nominal bore land: '+name
        assert not doc.OpticalDeck.Shape.isInside(App.Vector(x+2.98,y,p['case_depth']-.02),1e-7,True), 'Collar tip lacks lead-in'
        assert not doc.OpticalDeck.Shape.isInside(App.Vector(x+1.8,y,p['case_depth']-.02),1e-7,True), 'Top bore lacks lead-in'
        land=Part.makeCylinder(2.80,.01,App.Vector(x,y,p['case_depth']-.02)).cut(Part.makeCylinder(1.90,.01,App.Vector(x,y,p['case_depth']-.02)))
        assert abs(doc.OpticalDeck.Shape.common(land).Volume-land.Volume)<1e-7, 'Front washer stop must retain a continuous broad bearing land'
        assert doc.OpticalDeck.Shape.isInside(App.Vector(x+2.3,y,p['case_depth']-.01),1e-7,True), 'Collar lacks flat washer stop'
    for x,y in rear_mounting_points(p):
        assert not doc.RearPlate.Shape.isInside(App.Vector(x+1.85,y,.05),1e-7,True), 'Rear screw entry lacks lead-in'
        assert doc.RearPlate.Shape.isInside(App.Vector(x+1.85,y,.6),1e-7,True)
    assert not any(doc.getObject(n) for n in ('SeamStraps','CircleBezel','FrontBezel','FrontAcrylic','FrontMirror'))
    assert not any(doc.getObject(prefix+f'Q{i}') for prefix in ('OpticalDeck','BarrelFrame','RearPlate') for i in range(1,5))
    for i,(x,y) in enumerate(mounting_points(p)):
        assert math.isclose(doc.getObject(f'FrontStop{i}').Shape.BoundBox.ZMax,p['case_depth'],abs_tol=1e-7)
        assert not doc.FrontSheet.Shape.isInside(App.Vector(x+3.1,y,p['front_plane_z']+.5),1e-7,True)
        # The rear can pass the optical-stack nuts without releasing them.
        assert doc.RearPlate.Shape.common(Part.makeCylinder(4,4,App.Vector(x,y,-1))).Volume<1e-7
    for x,y in rear_mounting_points(p):
        ray=Part.makeLine(App.Vector(x,y,-4),App.Vector(x,y,10))
        assert not any(ray.common(obj.Shape).Length>1e-7 for obj in b.parts), 'Rear screw path blocked'
    assert doc.RearPlate in b.parts and len(doc.RearPlate.Shape.Solids) == 1
    assert doc.RearPlate.Material.startswith('Printed PETG')
    assert math.isclose(doc.RearPlate.Shape.BoundBox.ZMin,0,abs_tol=1e-7)
    # Unreinforced skin is thin; integral ribs and bolt lands are thicker.
    assert doc.RearPlate.Shape.isInside(App.Vector(15,-95,p['rear_skin_thickness']/2),1e-7,True)
    assert not doc.RearPlate.Shape.isInside(App.Vector(15,-95,(p['rear_skin_thickness']+p['rear_thickness'])/2),1e-7,True)
    assert doc.RearPlate.Shape.isInside(App.Vector(40,-80,p['rear_skin_thickness']+p['rear_rib_height']/2),1e-7,True)
    assert doc.RearPlate.Shape.isInside(App.Vector(121,0,p['rear_thickness']-.1),1e-7,True)
    port_x,port_y = p['external_port_x'],p['external_port_y']
    assert not doc.RearPlate.Shape.isInside(App.Vector(port_x,port_y,p['rear_thickness']/2),1e-7,True), 'External power entry is blocked'
    assert doc.RearPlate.Shape.isInside(App.Vector(port_x+p['external_port_diameter']/2+1,port_y,p['rear_thickness']-.1),1e-7,True), 'External power entry needs its reinforced sealing land'
    assert doc.ExternalPowerBlank in b.hardware, 'Unused battery entry needs a modeled blanking plug'
    assert doc.CirclePCB.Shape.BoundBox.ZMin-doc.sparkleComponents.Shape.BoundBox.ZMax >= 1-1e-7, 'Sparkle needs at least 1 mm circle clearance'
    assert doc.InnerLEDs.EmissionDirection == 'Radially inward toward circle'
    assert doc.OuterLEDs.EmissionDirection == 'Radially outward'
    assert doc.HaloLEDs.EmissionDirection == 'Radially outward'
    assert len(doc.HaloLEDs.Shape.Solids) == p['halo_count']
    assert len(doc.InnerLEDs.Shape.Solids) == p['inner_count']
    assert len(doc.OuterLEDs.Shape.Solids) == p['outer_count']
    d = optical_dimensions(p)
    assert d['visible_mirror_width'] >= 20
    assert d['diffuser_gap'] >= 18
    for name,dim in cavity_diffusers(p).items():
        band = doc.getObject(name+'Diffuser')
        assert band in b.parts and band.Material.startswith('Diffusing acrylic')
        if App.GuiUp:
            assert band.Visibility, 'Curved acrylic diffuser is hidden: '+name
            assert band.ViewObject.Transparency == build.DIFFUSER_TRANSPARENCY, 'Curved acrylic diffuser needs the translucent CAD display: '+name
            assert all(math.isclose(c,t,abs_tol=1e-6) for c,t in zip(band.ViewObject.ShapeColor[:3],build.DIFFUSER_TINT)), 'Curved acrylic diffuser needs the shared dark tint: '+name
        radii = sorted({edge.Curve.Radius for edge in band.Shape.Edges if hasattr(edge.Curve,'Radius')})
        assert len(radii)==2 and math.isclose(radii[0],dim['inner']) and math.isclose(radii[1],dim['outer'])
        assert math.isclose(band.Shape.BoundBox.ZMin,dim['bottom'])
        assert math.isclose(band.Shape.BoundBox.ZLength,dim['height'])
        leds = doc.getObject(name+'LEDs')
        assert band.Shape.BoundBox.ZMin < leds.Shape.BoundBox.ZMin
        assert band.Shape.BoundBox.ZMax > leds.Shape.BoundBox.ZMax
    assert math.isclose(doc.FrontSheet.Shape.BoundBox.ZMin-doc.RearMirror.Shape.BoundBox.ZMax,d['mirror_separation'],abs_tol=1e-7)
    assert doc.EdgeDiffuserSeam.Shape.BoundBox.ZMin <= doc.OuterLEDs.Shape.BoundBox.ZMin
    assert doc.EdgeDiffuserSeam.Shape.BoundBox.ZMax >= doc.OuterLEDs.Shape.BoundBox.ZMax
    assert doc.EdgeDiffuserSeam.Material.startswith('Black LED-diffusing acrylic'), 'Curved outside wall must use black acrylic'
    assert math.isclose(doc.EdgeDiffuserOuter.Radius.Value-doc.EdgeDiffuserInner.Radius.Value,p['edge_diffuser_thickness'],abs_tol=1e-7)
    edge_template_width = math.tau*(doc.EdgeDiffuserOuter.Radius.Value+doc.EdgeDiffuserInner.Radius.Value)/2-1
    edge_template_height = doc.EdgeDiffuserSeam.Shape.BoundBox.ZLength
    if App.GuiUp:
        assert all(math.isclose(c,t,abs_tol=1e-6) for c,t in zip(doc.EdgeDiffuserSeam.ViewObject.ShapeColor[:3],build.DIFFUSER_TINT)), 'Outside acrylic diffuser needs the shared dark tint'
        assert doc.EdgeDiffuserSeam.Visibility, 'Outside acrylic diffuser is hidden'
        assert doc.EdgeDiffuserSeam.ViewObject.Transparency == build.DIFFUSER_TRANSPARENCY, 'Black acrylic diffuser must show LEDs through its translucent CAD display'
    assert math.isclose(doc.OuterStripSeam.Shape.BoundBox.Center.z,doc.EdgeDiffuserSeam.Shape.BoundBox.Center.z,abs_tol=1e-7), 'Outer strip is not centered in the outside surface'
    assert math.isclose(doc.EdgeDiffuserSeam.Shape.BoundBox.ZMin,p['edge_bottom_z'],abs_tol=1e-7)
    assert math.isclose(doc.EdgeDiffuserSeam.Shape.BoundBox.ZMax,p['front_plane_z'],abs_tol=1e-7)
    assert not any(doc.getObject(name) for name in ('ButtonActuator0','SparkleUSBPowerPort','RadioPort','PowerSwitchPort')), 'Exposed side pegs or windows returned'
    # Rear skin stays closed except for covered vent/control/service passages.
    assert doc.RearPlate.Shape.isInside(App.Vector(0,-95,p['rear_skin_thickness']/2),1e-7,True)
    for i in range(4):
        membrane = doc.getObject(f'VentMembrane{i}')
        hole = doc.getObject(f'VentHole{i}')
        assert math.isclose(membrane.Shape.BoundBox.ZMax,0,abs_tol=1e-7)
        assert membrane.Shape.BoundBox.XLength > hole.Shape.BoundBox.XLength+4
        assert doc.getObject(f'VentGuard{i}') in b.parts
    # Model actual nominal M2 nuts, screw passages and their insertion sweeps.
    service_points=[('HatchStandoff'+str(i),x,54) for i,x in enumerate((25,71))]
    service_points += [(f'VentMount{i}{j}',x,y+offset) for i,(x,y) in enumerate([(x,y) for x in (-95,95) for y in (-30,30)]) for j,offset in enumerate((-11,11))]
    for name,x,y in service_points:
        radius=4/math.sqrt(3)  # nominal M2: 4 mm across flats, 1.6 mm thick
        points=[App.Vector(x+radius*math.cos(math.pi/6+j*math.tau/6),y+radius*math.sin(math.pi/6+j*math.tau/6),2.5) for j in range(6)]
        nut=Part.Face(Part.makePolygon(points+[points[0]])).extrude(App.Vector(0,0,1.6))
        assert doc.RearPlate.Shape.common(nut).Volume<1e-7, 'M2 nut does not fit: '+name
        for offset in (0,1,2,3,4,5,6,8):
            moved=nut.copy()
            moved.translate(App.Vector(0,offset,0))
            assert doc.RearPlate.Shape.common(moved).Volume<1e-7, 'M2 nut insertion blocked: '+name
        ray=Part.makeLine(App.Vector(x,y,-6),App.Vector(x,y,7))
        assert not any(ray.common(obj.Shape).Length>1e-7 for obj in b.parts), 'M2 service screw path blocked: '+name
        # Both axial faces trap the nut; no printed thread or friction-only insert.
        assert doc.RearPlate.Shape.isInside(App.Vector(x+1.6,y,2.2),1e-7,True)
        assert doc.RearPlate.Shape.isInside(App.Vector(x+1.6,y,4.5),1e-7,True)
    for i in range(4):
        guard=doc.getObject(f'VentGuard{i}')
        for drop in (.1,1,4,8):
            moved=guard.Shape.copy()
            moved.translate(App.Vector(0,0,-drop))
            assert moved.common(doc.RearPlate.Shape).Volume<1e-7, 'Vent guard cannot lift off'
        membrane=doc.getObject(f'VentMembrane{i}')
        assert membrane.Shape.common(guard.Shape).Volume<1e-7, 'Guard contacts membrane'
    for name,part in [('DeckTopMark','OpticalDeck'),('BarrelTopMark','BarrelFrame'),('RearTopMark','RearPlate')]:
        assert doc.getObject(name).Shape.common(doc.getObject(part).Shape).Volume<1e-7, 'TOP mark was not engraved'
    assert math.isclose(doc.Barrel.Base.Radius.Value-doc.Barrel.Tool.Radius.Value,p['structural_wall'],abs_tol=1e-7)
    for name,dim in cavity_diffusers(p).items():
        cuff=doc.getObject(name+'CuffBlank0')
        gap=dim['inner']-cuff.Base.Radius.Value if name=='Halo' else cuff.Tool.Radius.Value-dim['outer']
        assert math.isclose(gap,p['sleeve_fit_clearance'],abs_tol=1e-7)
    assert math.isclose(doc.RearMirrorBlank.Base.Radius.Value,ring_radius(p['inner_count'],p)+p['strip_thickness']/2-p['mirror_fit_clearance'],abs_tol=1e-7)
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
            point = App.Vector(r*math.cos(a),r*math.sin(a),p['front_plane_z']-.05)
            assert not any(obj.Shape.isInside(point,1e-7,True) for obj in b.parts), 'Mirror view is masked by a manufactured part'
    wood_mid = wood_bottom(p)+p['wood_thickness']/2
    for x, y in centres:
        assert not doc.WoodMask.Shape.isInside(App.Vector(x,y,wood_mid), 1e-7, True), 'LED centre blocked by native wood'
    for x,y in centres:
        ray = Part.makeLine(App.Vector(x,y,led_top),App.Vector(x,y,doc.FrontSheet.Shape.BoundBox.ZMin))
        assert all(ray.common(obj.Shape).Length < 1e-7 for obj in b.parts if obj.Name != 'FrontSheet'), 'Opaque part blocks a circle pixel'
    # Front service sequence: lift sheet, grid/spacers, sleeves and rear mirror.
    # Check actual translated solids through the complete axial exit path.
    for name in ('HaloDiffuser','InnerDiffuser','RearMirror','WoodMask','CirclePCB'):
        shape=doc.getObject(name).Shape
        for lift in (.1,.5,1,2,4,8,16,32):
            lifted=shape.copy()
            lifted.translate(App.Vector(0,0,lift))
            assert lifted.common(doc.OpticalFrame.Shape).Volume<1e-6, 'Frame blocks front removal: '+name
    for drop in (.1,.5,1,2,4,8,16,32):
        moved=doc.RearPlate.Shape.copy()
        moved.translate(App.Vector(0,0,-drop))
        assert moved.common(doc.OpticalFrame.Shape).Volume<1e-6, 'Frame blocks rear removal'
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
    sheet_circles=sorted({(round(e.Curve.Center.x,6),round(e.Curve.Center.y,6),round(e.Curve.Radius,6)) for e in doc.FrontSheet.Shape.Edges if hasattr(e.Curve,'Radius')})
    mirror_outline=Part.makeCompound([e.copy() for f in doc.RearMirror.Shape.Faces if f.BoundBox.ZLength<1e-7 and abs(f.BoundBox.ZMin-p['mirror_back_z'])<1e-7 for e in f.Edges])
    sample_shapes={name:build.fit_sample(doc.getObject(parent).Shape,p) for name,parent in
                   (('FitDeck.stl','OpticalDeck'),('FitBarrel.stl','BarrelFrame'),('FitRear.stl','RearPlate'))}
    sample_shapes['FitOptics.stl']=build.optical_fit_sample(doc.OpticalDeck.Shape)
    sample_shapes['FitService.stl']=build.service_fit_sample(doc.RearPlate.Shape)
    assert all(shape.isValid() and len(shape.Solids)==1 for shape in sample_shapes.values())
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
    acrylic = ET.parse(HERE / 'exports/front-sheet.svg')
    assert len(acrylic.findall('.//s:circle',ns))==7, 'One outline and six locating holes'
    for filename in ('circle-alignment-overlay.svg','assembly-section.svg','front-coating.svg','rear-mirror.svg','edge-diffuser.svg','fit-sheet.svg'):
        ET.parse(HERE/'exports'/filename)
    edge_template = ET.parse(HERE/'exports/edge-diffuser.svg').getroot()
    assert math.isclose(float(edge_template.attrib['width'].removesuffix('mm')),edge_template_width,abs_tol=1e-5)
    assert math.isclose(float(edge_template.attrib['height'].removesuffix('mm')),edge_template_height,abs_tol=1e-5)
    cut_circles=sorted((float(c.attrib['cx']),float(c.attrib['cy']),float(c.attrib['r'])) for c in acrylic.findall('.//s:circle',ns))
    assert cut_circles==sheet_circles, 'Front cut paths differ from native outline/locating holes'
    fit_holes=ET.parse(HERE/'exports/fit-sheet.svg').findall('.//s:circle',ns)
    assert len(fit_holes)==1 and float(fit_holes[0].attrib['r'])==min(c[2] for c in sheet_circles), 'Fit sheet hole differs from actual front'
    for polygon in ET.parse(HERE/'exports/rear-mirror.svg').findall('.//s:polygon',ns):
        points=[tuple(map(float,pair.split(','))) for pair in polygon.attrib['points'].split()]
        for a,b in zip(points,points[1:]+points[:1]):
            mid=Part.Vertex(App.Vector((a[0]+b[0])/2,(a[1]+b[1])/2,p['mirror_back_z']))
            assert mid.distToShape(mirror_outline)[0] <= .021, 'Laser mirror path exceeds chord tolerance'
    assert not (HERE/'exports/rear-clear-acrylic.svg').exists(), 'Superseded acrylic rear laser file remains'
    for name,dim in cavity_diffusers(p).items():
        template = ET.parse(HERE/'exports'/(name.lower()+'-ring-diffuser.svg')).getroot()
        width = math.tau*(dim['inner']+dim['outer'])/2-p['ring_diffuser_seam_gap']
        assert math.isclose(float(template.attrib['width'].removesuffix('mm')),width,abs_tol=1e-5)
        assert math.isclose(float(template.attrib['height'].removesuffix('mm')),dim['height'],abs_tol=1e-5)
    assembly = Part.read(str(HERE / 'exports/smart-compass.step'))
    assert assembly.isValid() and len(assembly.Solids) >= 256+p['halo_count']+p['inner_count']+p['outer_count']
    manifest = json.loads((HERE/'exports/parts.json').read_text())
    assert 'CellBaffle.stl' not in manifest['stl_files'], 'Superseded divider grid exported for printing'
    assert all(f'CircleRimFoot{i}.stl' in manifest['stl_files'] for i in range(3))
    mass = manifest['mass_estimate']
    wood_volume = next(v['volume_cm3'] for v in manifest['volumes'] if v['name']=='WoodMask')
    assert math.isclose(mass['wood_g'],round(wood_volume*p['wood_density_g_cm3'],1),abs_tol=1e-7)
    assert abs(mass['mechanical_subset_g']-sum(mass[k] for k in ('printed_petg_g','acrylic_g','wood_g'))) <= .2
    assert not next(v['printed'] for v in manifest['volumes'] if v['name']=='FrontSheet')
    assert len(manifest['stl_files'])==13, 'Unexpected printed assembly part count'
    assert all(name+'.stl' in manifest['stl_files'] for name in ('OpticalDeck','BarrelFrame','RearPlate'))
    assert not any('Q1' in name or name.startswith(('SeamStraps','CircleBezel','FrontBezel')) for name in manifest['stl_files'])
    assert not any(name.startswith(('BoardMounts','BatteryStrapSlots','HatchStandoff')) for name in manifest['stl_files']), 'Integral support exported twice'
    assert not any('Diffuser' in name for name in manifest['stl_files']), 'Acrylic diffuser cannot be a printed part'
    assert len([name for name in manifest['stl_files'] if name.startswith('NecklaceLink')]) == 2
    assert {sample['file'] for sample in manifest['fit_samples']} == set(sample_shapes)
    all_meshes=set(manifest['stl_files']) | set(sample_shapes)
    assert all_meshes == {f.name for f in (HERE/'exports').glob('*.stl')}
    for filename in sorted(all_meshes):
        file = HERE/'exports'/filename
        mesh = Mesh.Mesh(str(file))
        assert mesh.isSolid(), 'STL is not closed: ' + file.name
        if filename in sample_shapes:
            assert abs(abs(mesh.Volume)-sample_shapes[filename].Volume)<8, 'Fit STL differs from native cut'
            assert max(mesh.BoundBox.XLength,mesh.BoundBox.YLength)<60, 'Fit sample is no longer small'
        assert math.isclose(mesh.BoundBox.ZMin,0,abs_tol=1e-5), 'STL is not on bed: '+filename
        assert mesh.BoundBox.XLength+2*p['print_margin'] <= p['print_bed_x']
        assert mesh.BoundBox.YLength+2*p['print_margin'] <= p['print_bed_y']
    for changes in ({'sleeve_fit_clearance':.4}, {'mirror_fit_clearance':.8}, {'structural_wall':1.2}, {'wood_thickness':2}, {'wood_thickness':4.8}, {'wood_density_g_cm3':0}, {'external_port_diameter':18}, {'external_port_x':200}, {'battery_mass_g':0}, {'ring_diffuser_thickness':3}, {'ring_diffuser_led_gap':.1}, {'ring_diffuser_end_gap':.5}, {'ring_diffuser_seam_gap':5}, {'battery_count':3}, {'battery_spacing':30}, {'rear_skin_thickness':2}, {'rear_rib_height':4}, {'necklace_link_thickness':3}, {'battery_width':500}, {'battery_x':200}, {'battery_height':24}, {'inner_count':72.5}, {'assumed_efficiency':0}, {'mask_web':-1}, {'mirror_view_outer_radius':100}, {'inner_count':72}, {'front_plane_z':p['front_plane_z']-3}, {'edge_diffuser_radius':121}, {'edge_diffuser_thickness':4}, {'halo_count':60}, {'halo_count':80}, {'edge_bottom_z':30.5}, {'vent_patch_radius':4}):
        try:
            build.validate_parameters(dict(p, **changes))
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid parameters accepted: ' + repr(changes))
    print('CAD CHECK PASS: saved native geometry, single wood grid, spacer contact and LED clearance, clear circle/radial light paths, mirror gap, 256 apertures, sheet expression, laser contours, STEP, closed bed-sized STL meshes and invalid-fit rejection', flush=True)
