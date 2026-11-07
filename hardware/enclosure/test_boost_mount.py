"""Source geometry and terminal policy are required design inputs."""
import unittest
import boost_mount

class BoostMountTests(unittest.TestCase):
    def test_mounts_and_terminals_come_from_the_selected_source(self):
        data=boost_mount.geometry()
        self.assertEqual(data['mounts'],[{'xy':[2.794,20.32],'drill':2.5},{'xy':[2.54,2.54],'drill':2.5}])
        self.assertAlmostEqual(data['keepout_radius_mm'],2.016)
        self.assertEqual(len(data['outline']),8)
        self.assertGreater(len(data['through_pads']),10)
        self.assertEqual(len(boost_mount.PRODUCT_NAMES),7)
        self.assertEqual(boost_mount.envelope(6,90),{'size':[30,45,14],'z':6})
        self.assertEqual(boost_mount.envelope(9,0),{'size':[45,30,14],'z':9})
    def test_unreviewed_mount_height_orientation_or_terminal_fails(self):
        for z,angle in ((5,0),(9,45)):
            with self.subTest(z=z,angle=angle),self.assertRaises(ValueError):boost_mount.envelope(z,angle)
        part=boost_mount.definition();part['wire_terminals']['quantity']=1
        with self.assertRaises(ValueError):boost_mount.geometry(part)
        part=boost_mount.definition();part['terminal_bindings']['OUT']='X1.1'
        with self.assertRaises(ValueError):boost_mount.geometry(part)
if __name__=='__main__':unittest.main()
