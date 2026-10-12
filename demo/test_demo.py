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

    def test_metadata_and_glb(self):
        path=ROOT/'hardware/enclosure/exports'
        m=json.loads((path/'scene.json').read_text())
        self.assertEqual(m['units'],'metres')
        self.assertEqual(m['axes'],{'right':'+X','up':'+Y','front':'+Z'})
        self.assertEqual(len(m['leds']),494)
        self.assertAlmostEqual(m['dimensions_m']['diameter'],.250)
        self.assertAlmostEqual(m['optics']['separation'],.0112)
        self.assertAlmostEqual(m['optics']['front_z']-m['optics']['rear_z'],.0112)
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
        self.assertEqual({node['name'] for node in glb['nodes']},{part['name'] for part in m['parts']})
        # All 256 light contours derive from the one CAD wood grid.
        self.assertEqual(sum(part['role']=='cell' for part in m['parts']),256)
        proposal=m['proposal']
        self.assertEqual(len(proposal['fasteners_m']),6)
        self.assertAlmostEqual(proposal['sheet_thickness_m'],.0015)
        self.assertAlmostEqual(proposal['mechanical_g'],sum(proposal[k] for k in ('printed_petg_g','acrylic_g','wood_g')))
        old=json.loads((path/'parts.json').read_text())
        volumes={part['name']:part['volume_cm3'] for part in m['parts']}
        removed=sum(volumes[name] for name in ('FrontAcrylic','FrontMirror','FrontBezel','EdgeDiffuserSeam'))
        added=sum(volumes[name] for name in ('ProposalCentre','ProposalMirror','ProposalRim','ProposalEdge'))
        expected=old['mass_estimate']['acrylic_g']+(added-removed)*1.19
        self.assertAlmostEqual(proposal['acrylic_g'],expected,places=3)
        self.assertAlmostEqual(proposal['wood_to_sheet_gap_m'],.0001)
        self.assertAlmostEqual(proposal['wood_to_led_gap_m'],.0002)


if __name__=='__main__':
    unittest.main()
