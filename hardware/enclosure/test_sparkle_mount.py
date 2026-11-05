"""Keep the selected connector rework, real mount pattern and full loaded bound."""
import copy
import unittest

import sparkle_mount


class SparkleMountTests(unittest.TestCase):
    def test_source_mounts_and_protruding_usb_are_reserved(self):
        data=sparkle_mount.geometry()
        self.assertEqual(data['mount_xy_mm'],[[2.54,2.54],[48.26,30.48],[2.54,30.48],[48.26,2.54]])
        self.assertEqual(data['terminals']['INPUT']['pad'],'X7.PWR')
        self.assertEqual(data['loaded_bounds_mm'],{'x':[-1,50.8],'y':[0,33.147],'z':[-2.1,15]})
        self.assertEqual(sparkle_mount.envelope(6),{'x':[-25.4,26.4],'y':[-16.637,16.51],'z':[3.9,21]})
        self.assertEqual(len(sparkle_mount.PRODUCT_NAMES),9)

    def test_fitted_variant_cannot_keep_jack_or_remove_input_protection(self):
        for key,value in [('SPARKLE.remove',[]),('SPARKLE.remove',['X7','D2']),('SPARKLE.retain',['D2'])]:
            design=copy.deepcopy(sparkle_mount.definition());design['module_rework'][key]=value
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'only the reviewed X7'):sparkle_mount.geometry(design)

    def test_unreviewed_pose_is_rejected(self):
        for z,rotation in ((6,0),(8,180),(9,0)):
            with self.assertRaisesRegex(ValueError,'post height'):sparkle_mount.envelope(z,rotation)


if __name__=='__main__':unittest.main()
