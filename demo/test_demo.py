"""Acceptance checks for CAD metadata, LED registration and mirror reference."""
import json
import math
from pathlib import Path
import struct
import sys
import unittest

from reference import reference, cases
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'hardware/enclosure'))


class DemoTests(unittest.TestCase):
    def test_unfolded_spacing_and_attenuation(self):
        optics={'front_z':.0367,'rear_z':.0255,'halo_radius':.089,'inner_radius':.109}
        for count in range(12):
            depth=(count+.25)*.0112
            weight,bounces,group=reference([.099,0,.0367],[.01,0,-depth],optics)
            self.assertEqual(bounces,count)
            self.assertEqual(group,2)
            self.assertAlmostEqual(weight,.25*.94**((count+1)//2)*.65**(count//2))
        self.assertEqual(reference([.099,0,.0367],[0,0,-1],optics),[0,0,0])
        self.assertEqual(reference([0,0,.0367],[1,0,-1],optics),[0,0,0])
        self.assertEqual(reference([.099,0,.0367],[1,0,0],optics),[0,0,0])
        self.assertEqual(reference([.099,0,.0367],[1,0,1],optics),[0,0,0])

    def test_reflection_limit_and_energy_cutoff(self):
        optics={'front_z':.0367,'rear_z':.0255,'halo_radius':.089,'inner_radius':.109}
        for count in (31,32):
            self.assertEqual(reference([.099,0,.0367],[.01,0,-(count+.2)*.0112],optics,.99,.01)[1],count)
        self.assertEqual(reference([.099,0,.0367],[.01,0,-33.2*.0112],optics,.99,.01),[0,0,0])
        self.assertEqual(reference([.099,0,.0367],[.01,0,-.025],optics,1,0),[0,0,0])
        self.assertGreater(len(cases(optics)),100)

    def test_material_models_share_geometry_and_have_distinct_responses(self):
        path=ROOT/'hardware/enclosure/exports'
        metadata=json.loads((path/'scene.json').read_text())
        spec=json.loads((ROOT/'hardware/enclosure/print-spec.json').read_text())
        self.assertEqual(metadata['ring_materials'],spec['ring_materials'])
        binaries=[]; colours=[]
        for name in ('amulet.glb','amulet-silver.glb'):
            data=(path/name).read_bytes()
            size=struct.unpack_from('<I',data,12)[0]
            document=json.loads(data[20:20+size])
            binaries.append(data[28+size:])
            rings=[m['pbrMetallicRoughness']['baseColorFactor'] for m in document['materials'] if m['name'] in ('HaloRing','InnerRing','EdgeDiffuser')]
            self.assertEqual(len(rings),3)
            colours.append(rings)
        self.assertEqual(binaries[0],binaries[1])
        self.assertNotEqual(colours[0],colours[1])
        silver=metadata['ring_materials']['silver']['render']
        self.assertEqual(silver['stored_emission'],0)
        self.assertEqual(silver['prompt_green'],0)
        self.assertEqual(len(set(silver['absorption_per_mm'])),1)

    def test_metadata_and_glb(self):
        path=ROOT/'hardware/enclosure/exports'
        m=json.loads((path/'scene.json').read_text())
        self.assertEqual(m['units'],'metres')
        self.assertEqual(m['axes'],{'right':'+X','up':'+Y','front':'+Z'})
        self.assertEqual(len(m['leds']),494)
        self.assertAlmostEqual(m['dimensions_m']['diameter'],.250)
        self.assertAlmostEqual(m['optics']['separation'],.0112)
        self.assertAlmostEqual(m['optics']['front_z']-m['optics']['rear_z'],.0112)
        parameters=json.loads((path/'parts.json').read_text())['parameters_for_inventory']
        self.assertEqual(m['optics']['ring_wall_mm'],[
            parameters['ring_diffuser_thickness'],parameters['ring_diffuser_thickness'],
            parameters['edge_diffuser_thickness']])
        for group,count in enumerate((256,64,84,90)):
            leds=[led for led in m['leds'] if led['group']==group]
            self.assertEqual([led['index'] for led in leds],list(range(count)))
            for led in leds:
                direction=led['direction']
                self.assertAlmostEqual(sum(v*v for v in direction),1)
                x,y,_=led['position_m']
                if group==0:
                    self.assertEqual(direction,[0,0,1])
                else:
                    self.assertAlmostEqual(direction[2],0)
                    radial=(x*direction[0]+y*direction[1])/math.hypot(x,y)
                    self.assertAlmostEqual(radial,-1 if group==2 else 1)
        data=(path/'amulet.glb').read_bytes()
        self.assertEqual(struct.unpack_from('<III',data),(0x46546c67,2,len(data)))
        size,kind=struct.unpack_from('<II',data,12)
        self.assertEqual(kind,0x4e4f534a)
        glb=json.loads(data[20:20+size])
        def values(index,dimensions):
            accessor=glb['accessors'][index]
            view=glb['bufferViews'][accessor['bufferView']]
            start=28+size+view.get('byteOffset',0)+accessor.get('byteOffset',0)
            self.assertEqual(accessor['componentType'],5126)
            return [struct.unpack_from('<'+'f'*dimensions,data,start+i*dimensions*4) for i in range(accessor['count'])]
        packages=next(mesh for mesh in glb['meshes'] if mesh['name']=='CircleLEDs')['primitives'][0]['attributes']
        positions=values(packages['POSITION'],3)
        identities=values(packages['COLOR_0'],4)
        self.assertEqual(len(positions),len(identities))
        indices={round(colour[0]*255) for colour in identities}
        self.assertEqual(indices,set(range(256)))
        for offset in range(0,len(positions),3):
            index=round(identities[offset][0]*255)
            self.assertTrue(all(round(colour[0]*255)==index for colour in identities[offset:offset+3]))
            x,y,_=m['leds'][index]['position_m']
            self.assertTrue(all(abs(point[0]-x)<.00251 and abs(point[1]-y)<.00251 for point in positions[offset:offset+3]),'Package colour index differs from the published board map')
        self.assertEqual({node['name'] for node in glb['nodes']},{part['name'] for part in m['parts']})
        # All 256 optical regions are clipped by the original CAD baffle.
        self.assertEqual(sum(part['role']=='cell' for part in m['parts']),256)
        design=m['design']
        self.assertEqual(len(design['fasteners_m']),6)
        self.assertAlmostEqual(design['sheet_thickness_m'],.003)
        self.assertEqual(design['printed_part_count'],17)
        self.assertTrue({'HaloLightShield','InnerLightShield','OuterLightShield'} <= {part['name'] for part in m['parts']})
        inventory=json.loads((path/'parts.json').read_text())
        quantities={row['id']:row['installed_quantity'] for row in inventory['components']}
        expected=sum(quantities[key] for key in ('body_screws','anchor_screws','rear_screws','service_screws','sparkle_mount_hardware',
                     'M3_nuts','M2_nuts','M3_washers','M3_front_washers','M2_washers','soft_front_washers'))
        hardware=[part for part in m['parts'] if part['role']=='hardware']
        self.assertEqual(len(hardware),expected)
        self.assertTrue(all(math.isfinite(part['explosion_offset_m']) for part in hardware))
        self.assertEqual(design['mass_estimate'],inventory['mass_estimate'])
        volumes={part['name']:part['volume_cm3'] for part in m['parts']}
        self.assertAlmostEqual(sum(volumes[n] for n in ('FrontCentre','FrontMirrorCoating','FrontRim')),design['front_sheet_volume_cm3'])
        self.assertFalse(any(n.startswith('Proposal') for n in volumes))



if __name__=='__main__':
    unittest.main()
