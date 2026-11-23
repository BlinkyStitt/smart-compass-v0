"""Keep stale fit outputs out of a new Rev A delivery."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import print_package


class PrintPackageTests(unittest.TestCase):
    def test_stale_fit_stops_before_copying_or_slicing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fit = root / 'fit'
            fit.mkdir()
            (fit / 'routed-fit.json').write_text(json.dumps({'inputs': {'old': 'revision'}}))
            destination = root / 'package'
            with patch.object(print_package, 'package_inputs', return_value={'new': 'revision'}), \
                    patch.object(print_package, 'fit_inputs', return_value={'new': 'revision'}), \
                    patch.object(print_package, 'slice_projects') as slice_projects:
                with self.assertRaisesRegex(ValueError, 'routed-fit inputs differ'):
                    print_package.build(fit, destination)
            slice_projects.assert_not_called()
            self.assertFalse(destination.exists())


if __name__ == '__main__':
    unittest.main()
