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
import inventory
import baffle
from hardware_spec import nut_dimensions, stations
from geometry import battery_centres, cavity_diffusers, led_centres, pixel_regions, mounting_points, necklace_anchors, optical_dimensions, rear_mounting_points, ring_radius, ring_locating_angles, ring_movement_limit, ring_led_clearances, outside_front_overlap, top_light_shields, baffle_bottom


def check():
    p = build.load_parameters()
    doc = App.openDocument(str(HERE / 'smart-compass.FCStd'))
    doc.recompute()
    assert set(doc.InputStatus.ParameterKeys) == {k for k in p if not k.startswith('_')}, 'Saved parameter schema differs from the generator'
    b = SimpleNamespace(p=p, doc=doc, parts=list(doc.Manufactured.Group), hardware=list(doc.Electronics.Group), references=list(doc.Optics.Group))
    layout = json.loads((HERE / 'fibonacci256-layout.json').read_text())
    centres = led_centres(layout, p)
    cells = pixel_regions(centres,p['circle_diameter']/2)
    build.check_model(b, centres, cells)
    baffle_z = baffle_bottom(p)
    assert math.isclose(doc.FibonacciBaffle.Shape.BoundBox.ZMin, baffle_z, abs_tol=1e-7), 'Master retained an exploded baffle placement'
    assert doc.getObject('CellBaffle') is None, 'A second full cell grid remains in the model'
    led_top = doc.CircleLEDs.Shape.BoundBox.ZMax
    assert .5-1e-7 <= baffle_z-led_top <= .8+1e-7, 'Printed baffle leaves an excessive LED gap or touches LEDs'
    assert math.isclose(doc.FibonacciBaffle.Shape.BoundBox.ZLength,p['baffle_thickness'],abs_tol=1e-7)
    original_stencil=Mesh.Mesh(str(HERE/'vendor/evilgeniuslabs-fibonacci256/Fibonacci256voronoi.stl'))
    stencil_volume=baffle.source_volume()
    assert math.isclose(doc.FibonacciBaffle.Shape.Volume,stencil_volume,abs_tol=.05), 'Original stencil volume changed'
    assert len(doc.FibonacciBaffle.Shape.Solids)==1
    for i in range(3):
        foot = doc.getObject(f'CircleRimFoot{i}')
        assert foot in b.parts and len(foot.Shape.Solids) == 1
        assert math.isclose(foot.Shape.BoundBox.ZMin,p['circle_back_z']+p['circle_pcb_thickness'],abs_tol=1e-7)
        assert math.isclose(foot.Shape.BoundBox.ZMax,baffle_z,abs_tol=1e-7)
        assert foot.Shape.common(doc.CircleLEDs.Shape).Volume < 1e-7, 'Rim spacer touches an LED body'
        # The source photograph shows rotated 5050 packages. A circumscribed
        # circle checks every possible package rotation around each centre.
        for x,y in centres:
            point=Part.Vertex(App.Vector(x,y,p['circle_back_z']+p['circle_pcb_thickness']+p['led_height']/2))
            assert point.distToShape(foot.Shape)[0]>=5/math.sqrt(2), 'Rim spacer enters a rotated 5050 package envelope'
        tops = [f for f in foot.Shape.Faces if f.BoundBox.ZLength < 1e-7 and abs(f.BoundBox.ZMin-baffle_z) < 1e-7]
        bases = [f for f in doc.FibonacciBaffle.Shape.Faces if f.BoundBox.ZLength < 1e-7 and abs(f.BoundBox.ZMin-baffle_z) < 1e-7]
        assert sum(top.common(base).Area for top in tops for base in bases) >= 1.5, 'Rim spacer misses the original baffle walls'
    assert math.isclose(doc.FrontSheet.Shape.BoundBox.ZMin,p['front_plane_z'],abs_tol=1e-7)
    assert math.isclose(doc.FrontSheet.Shape.BoundBox.ZLength,p['front_acrylic_thickness'],abs_tol=1e-7)
    assert math.isclose(p['front_plane_z']-doc.FibonacciBaffle.Shape.BoundBox.ZMax,p['baffle_to_sheet_gap'],abs_tol=1e-7)
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
    for i,(x,y) in enumerate(mounting_points(p)):
        sheet_land=Part.makeCylinder(4,.01,App.Vector(x,y,p['front_plane_z']-.01)).cut(Part.makeCylinder(3.5,.01,App.Vector(x,y,p['front_plane_z']-.01)))
        assert doc.OpticalDeck.Shape.common(sheet_land).Volume/.01 >= 8, 'Trimmed sheet land lost its bearing area'
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
        band = doc.getObject(name+'Ring')
        assert band in b.parts and band.Material.startswith('Prusament PETG Ultraglow Green')
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
    assert doc.EdgeDiffuser.Shape.BoundBox.ZMin <= doc.OuterLEDs.Shape.BoundBox.ZMin
    assert doc.EdgeDiffuser.Shape.BoundBox.ZMax >= doc.OuterLEDs.Shape.BoundBox.ZMax
    assert doc.EdgeDiffuser.Material.startswith('Prusament PETG Ultraglow Green')
    assert math.isclose(doc.EdgeDiffuserOuter.Radius.Value-doc.EdgeDiffuserInner.Radius.Value,p['edge_diffuser_thickness'],abs_tol=1e-7)
    if App.GuiUp:
        assert all(math.isclose(c,t,abs_tol=1e-6) for c,t in zip(doc.EdgeDiffuser.ViewObject.ShapeColor[:3],build.DIFFUSER_TINT)), 'Outside acrylic diffuser needs the shared dark tint'
        assert doc.EdgeDiffuser.Visibility, 'Outside acrylic diffuser is hidden'
        assert doc.EdgeDiffuser.ViewObject.Transparency == build.DIFFUSER_TRANSPARENCY, 'Black acrylic diffuser must show LEDs through its translucent CAD display'
    assert math.isclose(doc.OuterStripSeam.Shape.BoundBox.Center.z,doc.EdgeDiffuser.Shape.BoundBox.Center.z,abs_tol=1e-7), 'Outer strip is not centered in the outside surface'
    assert math.isclose(doc.EdgeDiffuser.Shape.BoundBox.ZMin,p['edge_bottom_z'],abs_tol=1e-7)
    assert math.isclose(doc.EdgeDiffuser.Shape.BoundBox.ZMax,p['front_plane_z']-p['ring_front_clearance'],abs_tol=1e-7)
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
    for i,(dx,dy) in enumerate([(dx,dy) for dx in (-22.86,22.86) for dy in (-13.97,13.97)]):
        x,y=p['sparkle_x']-dx,p['sparkle_y']-dy
        assert doc.RearPlate.Shape.isInside(App.Vector(x,y,p['rear_skin_thickness']/2),1e-7,True), 'Controller mount opens rear skin'
        assert doc.getObject(f'Sparkle{i}Screw') in b.hardware
        assert doc.getObject(f'Sparkle{i}Washer') in b.hardware
        assert doc.getObject(f'Sparkle{i}Nut') in b.hardware
        assert doc.getObject(f'SparklePocket{i}Nut').LengthFwd.Value == 1.9
        assert doc.RearPlate.Shape.common(doc.getObject(f'Sparkle{i}Nut').Shape).Volume < 1e-7
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
        assert math.isclose(gap,p['ring_seat_play'],abs_tol=1e-7)
        assert math.isclose(cuff.Shape.BoundBox.ZLength,p['ring_cuff_height'],abs_tol=1e-7)
        assert min(ring_led_clearances(p).values())-ring_movement_limit(p,p['ring_radial_error_budget'])+1e-7 >= .5
        assert dim['bottom']+p['ring_cuff_height'] > dim['bottom']+.8
    for name,dim in top_light_shields(p).items():
        shield=doc.getObject(name+'LightShield')
        assert shield.Material.startswith('tesa 7160 black PET')
        assert math.isclose(shield.Shape.BoundBox.ZMin,dim['bottom'],abs_tol=1e-7)
        assert math.isclose(shield.Shape.BoundBox.ZLength,p['light_shield_thickness'],abs_tol=1e-7)
        assert not doc.FrontSheet.Shape.common(shield.Shape).Volume > 1e-7
    motion=ring_movement_limit(p)
    clearance_motion=ring_movement_limit(p,p['ring_radial_error_budget'])
    for name,led_name,phase in (('HaloRing','HaloLEDs',30),('InnerRing','InnerLEDs',30),('EdgeDiffuser','OuterLEDs',0)):
        original=doc.getObject(name).Shape
        shield_name='OuterLightShield' if name=='EdgeDiffuser' else name.removesuffix('Ring')+'LightShield'
        for station in range(int(p['ring_station_count'])*2):
            a=math.radians(phase+station*180/p['ring_station_count'])
            # A larger translation must meet a rigid locator at both lift limits.
            for lift in (0,.8):
                beyond=original.copy();beyond.translate(App.Vector((motion+.01)*math.cos(a),(motion+.01)*math.sin(a),lift))
                assert beyond.common(doc.OpticalFrame.Shape).Volume>1e-6, 'Ring escapes its movement limit: '+name
            offset=App.Vector(clearance_motion*math.cos(a),clearance_motion*math.sin(a),0)
            moved=original.copy();moved.translate(offset)
            if name == 'EdgeDiffuser':
                # A complete annular band must stay below the real sheet, even
                # when the outside edge projects beyond its nominal outline.
                stop=Part.makeCylinder(p['edge_diffuser_radius']+1.5,.1,App.Vector(0,0,p['front_plane_z']+.1)).cut(
                    Part.makeCylinder(p['edge_diffuser_radius'],.1,App.Vector(0,0,p['front_plane_z']+.1)))
                stop.translate(offset)
                assert outside_front_overlap(p) >= 1.5
                assert abs(stop.common(doc.FrontSheet.Shape).Volume-stop.Volume)<1e-6, 'Moved outside ring loses continuous sheet retention'
            # Include even positions excluded by the pad width. This checks a
            # conservative superset of every reachable optical clearance.
            assert moved.distToShape(doc.getObject(led_name).Shape)[0] >= .5, 'Moved ring loses LED clearance: '+name
            for lift in (0,.2,.4,.6,.8):
                film=doc.getObject(shield_name).Shape.copy();film.translate(offset+App.Vector(0,0,lift))
                assert film.common(doc.OpticalFrame.Shape).Volume<1e-7, 'Moved shield catches frame: '+name
    # Outside stops must provide the same 1.2 mm axial retention as cavity cuffs.
    contact_radius=p['edge_diffuser_radius']-p['ring_seat_play']
    for angle in ring_locating_angles(p,0):
        a=math.radians(angle)
        for height in (p['ring_cuff_height']-.01,p['ring_cuff_height']+.02):
            point=App.Vector((contact_radius-.001)*math.cos(a),(contact_radius-.001)*math.sin(a),p['edge_bottom_z']+height)
            assert doc.BarrelFrame.Shape.isInside(point,1e-7,True)==(height<p['ring_cuff_height']), 'Outside locating height differs from cuff input'
    assert math.isclose(doc.RearMirrorBlank.Base.Radius.Value,ring_radius(p['inner_count'],p)+p['strip_thickness']/2-p['mirror_fit_clearance'],abs_tol=1e-7)
    for side in (-1,1):
        (x,y),primary,secondary = necklace_anchors(p,side)
        link = doc.getObject('NecklaceLink'+str(0 if side==-1 else 1))
        assert math.isclose(link.Shape.BoundBox.ZLength,p['necklace_link_thickness'],abs_tol=1e-7)
        assert len(link.Shape.Solids) == 1
        screw_path = Part.makeLine(App.Vector(*secondary,-4),App.Vector(*secondary,p['rear_thickness']+p['necklace_link_thickness']+6.1))
        assert not any(screw_path.common(obj.Shape).Length > 1e-7 for obj in b.parts), 'Independent necklace anchor screw is blocked'
        eye_path = Part.makeLine(App.Vector(x,64,-3),App.Vector(x,64,p['rear_thickness']+p['necklace_link_thickness']+.1))
        assert not any(eye_path.common(obj.Shape).Length > 1e-7 for obj in b.parts), 'A cover blocks a necklace eye'
    for x,y in mounting_points(p):
        bolt_path = Part.makeLine(App.Vector(x,y,-4),App.Vector(x,y,p['case_depth']+1))
        assert not any(bolt_path.common(obj.Shape).Length > 1e-7 for obj in b.parts), 'A cover blocks a body bolt'
        nut_space = Part.makeCylinder(4,6,App.Vector(x,y,-6))
        assert not any(nut_space.common(obj.Shape).Volume > .05 for obj in b.parts), 'No rear nut/tool clearance'
    for name,size,x,y,seat,direction,length,nut_z in stations(p):
        screw=doc.getObject(name+'Screw')
        washer=doc.getObject(name+'Washer')
        assert screw in b.hardware and washer in b.hardware
        assert len(screw.Shape.Solids)==1 and len(washer.Shape.Solids)==1
        if nut_z is None:
            rear_nut=doc.getObject('BodyRearNut'+name.removeprefix('Body'))
            assert math.isclose(rear_nut.Shape.BoundBox.ZMin-screw.Shape.BoundBox.ZMin,p['body_bolt_tip_projection'],abs_tol=1e-7), 'Body screw projection differs from measured stack'
            tip=screw.Shape.BoundBox.ZMin
            assert not screw.Shape.isInside(App.Vector(x+1.49,y,tip+.01),1e-7,True), 'Finished body screw lacks its tip chamfer'
            assert screw.Shape.isInside(App.Vector(x+1.49,y,tip+p['body_bolt_tip_chamfer']+.01),1e-7,True), 'Tip finish removed full nut engagement'
            continue
        nut=doc.getObject(name+'Nut')
        target=doc.BarrelFrame if size=='M3' else doc.RearPlate
        # Axial capture remains above and below each nut away from the bore.
        if size=='M3':
            a=math.atan2(y,x)+math.pi/2
            for displacement in (0,1,2,3,4,6,8,10):
                moved=nut.Shape.copy()
                moved.translate(App.Vector(-math.sin(a)*displacement,math.cos(a)*displacement,0))
                assert moved.common(target.Shape).Volume<1e-7, 'M3 nut loading path blocked: '+name
            pocket=doc.getObject(('AnchorPocket'+name[-1] if name.startswith('Anchor') else 'RearMountPocket'+name[-1])+'Nut')
            assert math.isclose(pocket.LengthFwd.Value,2.7,abs_tol=1e-7)
            for z in (nut_z-.3,nut_z+nut_dimensions(size)[1]+.3):
                assert target.Shape.isInside(App.Vector(x+2*math.cos(a),y+2*math.sin(a),z),1e-7,True), 'M3 nut lacks axial capture: '+name
    assert nut_dimensions('M3',True)==(5.9,2.7)
    assert nut_dimensions('M2',True)==(4.4,1.9)
    for i in range(2):
        link = doc.getObject(f'NecklaceLink{i}')
        clearance = doc.getObject(f'NecklaceClearanceBlank{i}')
        assert link.TypeId == 'Part::Fillet' and clearance.Shape.isValid()
        assert clearance.Shape.Volume > link.Shape.Volume
        assert link.Shape.cut(clearance.Shape).Volume < 1e-6, 'Bracket escapes its 0.4 mm clearance outline'
        for boss in [doc.getObject(f'HatchStandoff{j}') for j in range(2)]+[doc.getObject(f'VentMount{j}{k}') for j in range(4) for k in range(2)]:
            assert clearance.Shape.common(boss.Shape).Volume < 1e-6, 'Bracket clearance cuts a protected nut boss'
    # The foot windows stay above the unchanged skin and below board bearing faces.
    for key in ('blackpill','gps','imu','radio','sense','power'):
        for side in (-1,1):
            for j in (0,1):
                side_name='Right' if side==1 else 'Left'
                relief=doc.getObject(f'{key}FootRelief{side_name}{j}')
                assert math.isclose(relief.Shape.BoundBox.ZMin,p['rear_skin_thickness'],abs_tol=1e-7)
                assert relief.Shape.BoundBox.ZMax < p['rear_thickness']+4
                foot=doc.getObject(f'{key}OpenFoot{side_name}')
                assert relief.Shape.common(foot.Shape).Volume<1e-7, 'Board foot relief is blocked'
    # Washer access leaves all ten service nut standoffs present.
    for name,x,y in service_points:
        assert doc.getObject(name) is not None
        assert doc.RearPlate.Shape.isInside(App.Vector(x+1.6,y,4.5),1e-7,True)
    # The saved centre must stay open for the full visible mirror annulus.
    for r in (p['mirror_view_inner_radius']+.1,p['mirror_view_outer_radius']-.1):
        for i in range(12):
            a = i*math.tau/12
            point = App.Vector(r*math.cos(a),r*math.sin(a),p['front_plane_z']-.05)
            assert not any(obj.Shape.isInside(point,1e-7,True) for obj in b.parts), 'Mirror view is masked by a manufactured part'
    baffle_mid = baffle_bottom(p)+p['baffle_thickness']/2
    for x, y in centres:
        assert not doc.FibonacciBaffle.Shape.isInside(App.Vector(x,y,baffle_mid), 1e-7, True), 'LED centre blocked by original native baffle'
    for x,y in centres:
        ray = Part.makeLine(App.Vector(x,y,led_top),App.Vector(x,y,doc.FrontSheet.Shape.BoundBox.ZMin))
        assert all(ray.common(obj.Shape).Length < 1e-7 for obj in b.parts if obj.Name != 'FrontSheet'), 'Opaque part blocks a circle pixel'
    # Front service sequence: lift sheet, grid/spacers, sleeves and rear mirror.
    # Check actual translated solids through the complete axial exit path.
    for name in ('HaloRing','InnerRing','EdgeDiffuser','RearMirror','FibonacciBaffle','CirclePCB'):
        shape=doc.getObject(name).Shape
        if name in ('HaloRing','InnerRing','EdgeDiffuser'):
            shield_name='OuterLightShield' if name=='EdgeDiffuser' else name.removesuffix('Ring')+'LightShield'
            shape=Part.makeCompound([shape,doc.getObject(shield_name).Shape])
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
    sample_shapes['FitFibonacciBaffle.stl']=doc.FibonacciBaffle.Shape.copy()
    sample_shapes['FitOptics.stl']=build.optical_fit_sample(doc.OpticalDeck.Shape)
    sample_shapes['FitService.stl']=build.service_fit_sample(doc.RearPlate.Shape)
    sample_shapes['FitController.stl']=build.controller_fit_sample(doc.RearPlate.Shape,p)
    for name,parent in (('FitRingHalo','HaloRing'),('FitRingInner','InnerRing'),('FitRingOutside','EdgeDiffuser')):
        sample_shapes[name+'.stl']=build.ring_fit_sample(doc.getObject(parent).Shape)
    sample_shapes['FitSuspensionBracket.stl']=doc.NecklaceLink1.Shape.copy()
    sample_shapes['FitSuspensionBracketLeft.stl']=doc.NecklaceLink0.Shape.copy()
    for name,parent in (('FitSuspensionFrame','BarrelFrame'),('FitSuspensionRear','RearPlate')):
        sample_shapes[name+'.stl']=doc.getObject(parent).Shape.common(Part.makeBox(40,50,25,App.Vector(70,35,0)))
    assert all(shape.isValid() and len(shape.Solids)==1 for shape in sample_shapes.values())
    # A native expression must follow a sheet edit after recompute.
    doc.Parameters.set('B' + str(doc.InputStatus.ParameterKeys.index('battery_height')+2), '=' + str(p['battery_height']-1) + ' mm')
    doc.recompute()
    assert math.isclose(doc.BatteryEnvelope0.Shape.BoundBox.ZLength, p['battery_height']-1, abs_tol=1e-7)
    App.closeDocument(doc.Name)  # Do not save this test edit.
    ns = {'s':'http://www.w3.org/2000/svg'}
    assert not (HERE/'exports/wood-fibonacci-mask.svg').exists(), 'Retired plywood cut file remains'
    acrylic = ET.parse(HERE / 'exports/front-sheet.svg')
    assert len(acrylic.findall('.//s:circle',ns))==7, 'One outline and six locating holes'
    for filename in ('circle-alignment-overlay.svg','assembly-section.svg','front-coating.svg','rear-mirror.svg','fit-sheet.svg','soft-front-washer.svg','halo-light-shield.svg','inner-light-shield.svg','outer-light-shield.svg'):
        ET.parse(HERE/'exports'/filename)
    for name,dim in top_light_shields(p).items():
        cut=ET.parse(HERE/'exports'/(name.lower()+'-light-shield.svg'))
        circles=cut.findall('.//s:circle',ns)
        assert len(circles)==2 and not cut.findall('.//s:polygon',ns)
        assert [float(circle.attrib['r']) for circle in circles] == [round(dim['outer'],6),round(dim['inner'],6)]
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
    assert not any((HERE/'exports'/name).exists() for name in ('edge-diffuser.svg','halo-ring-diffuser.svg','inner-ring-diffuser.svg'))
    assembly = Part.read(str(HERE / 'exports/smart-compass.step'))
    assert assembly.isValid() and len(assembly.Solids) >= 256+p['halo_count']+p['inner_count']+p['outer_count']
    manifest = json.loads((HERE/'exports/parts.json').read_text())
    assert 'FibonacciBaffle.stl' in manifest['stl_files'] and 'CellBaffle.stl' not in manifest['stl_files'], 'Superseded divider grid exported for printing'
    assert all(f'CircleRimFoot{i}.stl' in manifest['stl_files'] for i in range(3))
    print_spec=json.loads((HERE/'print-spec.json').read_text())
    component_spec=json.loads((HERE/'component-inventory.json').read_text())
    for material_name,material in print_spec['ring_materials'].items():
        variant_rows=inventory.resolve(component_spec,manifest['volumes'],p,material)
        variant=manifest['material_variants'][material_name]
        assert variant_rows==variant['components'], 'Material-specific component ledger differs from source inventory'
        assert inventory.totals(variant_rows)==variant['mass_estimate'], 'Material-specific mass totals differ from component ledger'
    rows=manifest['material_variants'][print_spec['default_ring_material']]['components']
    assert rows==manifest['components'], 'Exported component ledger differs from source inventory'
    assert inventory.totals(rows)==manifest['mass_estimate'], 'Complete mass totals differ from component ledger'
    assert manifest['mass_estimate']['complete_pendant']['nominal_g'] > 700
    assert not next(v['printed'] for v in manifest['volumes'] if v['name']=='FrontSheet')
    for name in ('HaloLightShield','InnerLightShield','OuterLightShield'):
        assert not next(v['printed'] for v in manifest['volumes'] if v['name']==name)
        assert any(row.get('cad_part')==name for row in rows)
    assert len(manifest['stl_files'])==17, 'Unexpected printed assembly part count'
    assert all(name+'.stl' in manifest['stl_files'] for name in ('OpticalDeck','BarrelFrame','RearPlate'))
    assert not any('Q1' in name or name.startswith(('SeamStraps','CircleBezel','FrontBezel')) for name in manifest['stl_files'])
    assert not any(name.startswith(('BoardMounts','BatteryStrapSlots','HatchStandoff')) for name in manifest['stl_files']), 'Integral support exported twice'
    assert {'HaloRing.stl','InnerRing.stl','EdgeDiffuser.stl'} <= set(manifest['stl_files'])
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
            if filename!='FitFibonacciBaffle.stl' and not filename.startswith('FitSuspensionBracket'):
                assert max(mesh.BoundBox.XLength,mesh.BoundBox.YLength)<60, 'Fit sample is no longer small'
        if filename in ('FibonacciBaffle.stl','FitFibonacciBaffle.stl'):
            vertices,triangles=mesh.Topology
            points=[(v.x,v.y,v.z) for v in vertices]
            measured=baffle.triangle_volume(tuple(points[i] for i in triangle) for triangle in triangles)
            assert math.isclose(measured,stencil_volume,abs_tol=.05), 'Printed stencil differs from original STL'
            assert math.isclose(mesh.BoundBox.XLength,original_stencil.BoundBox.XLength,abs_tol=1e-4)
            assert math.isclose(mesh.BoundBox.YLength,original_stencil.BoundBox.YLength,abs_tol=1e-4)
            assert math.isclose(mesh.BoundBox.ZLength,2,abs_tol=1e-5)
        assert math.isclose(mesh.BoundBox.ZMin,0,abs_tol=1e-5), 'STL is not on bed: '+filename
        assert mesh.BoundBox.XLength+2*p['print_margin'] <= p['print_bed_x']
        assert mesh.BoundBox.YLength+2*p['print_margin'] <= p['print_bed_y']
    for changes in ({'body_bolt_tip_projection':0}, {'body_bolt_stock_length':35}, {'body_bolt_tip_chamfer':.4}, {'ring_station_count':3}, {'ring_station_count':6}, {'ring_station_count':6.5}, {'ring_seat_play':.3}, {'ring_seat_play':.4}, {'mirror_fit_clearance':.8}, {'structural_wall':1.2}, {'baffle_thickness':1}, {'baffle_thickness':4.8}, {'external_port_diameter':18}, {'external_port_x':200}, {'battery_mass_g':0}, {'ring_diffuser_thickness':3}, {'ring_diffuser_led_gap':.1}, {'ring_bottom_clearance':.5}, {'battery_count':3}, {'battery_spacing':30}, {'rear_skin_thickness':2}, {'rear_rib_height':4}, {'necklace_link_thickness':3}, {'battery_width':500}, {'battery_x':200}, {'battery_height':p['circle_back_z']-p['rear_thickness']-4}, {'inner_count':72.5}, {'assumed_efficiency':0}, {'mirror_view_outer_radius':100}, {'inner_count':72}, {'front_plane_z':p['front_plane_z']-3}, {'edge_diffuser_radius':121}, {'edge_diffuser_thickness':1.2}, {'edge_diffuser_thickness':4}, {'halo_count':60}, {'halo_count':80}, {'edge_bottom_z':30.5}, {'vent_patch_radius':4}):
        try:
            build.validate_parameters(dict(p, **changes))
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid parameters accepted: ' + repr(changes))
    print('CAD CHECK PASS: saved native geometry, original printed EGL baffle, spacer contact and LED clearance, clear circle/radial light paths, mirror gap, 256 unobstructed centres, sheet expression, laser contours, STEP, closed bed-sized STL meshes and invalid-fit rejection', flush=True)
