"""Native CAD macros must exit without a save-confirmation dialog."""
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

class NativeMacroExitTests(unittest.TestCase):
    def test_native_macros_close_unsaved_documents_on_success_and_failure(self):
        for macro in ('designs/stacked/Run.FCMacro',):
            for fails in (False, True):
                with self.subTest(macro=macro, fails=fails), tempfile.TemporaryDirectory() as tmp:
                    documents = {'saved-model': object(), 'temporary-export': object()}
                    exited = []
                    def build(*args):
                        if fails:
                            raise RuntimeError('native build failed')
                    def quit_application():
                        self.assertFalse(documents, 'Unsaved documents would open a modal save prompt')
                        exited.append(True)
                    app = SimpleNamespace(Version=lambda: ['1', '1', '4'],
                                          listDocuments=lambda: documents,
                                          closeDocument=lambda name: documents.pop(name))
                    qt = SimpleNamespace(QTimer=SimpleNamespace(singleShot=lambda delay, fn: fn()),
                                         QCoreApplication=SimpleNamespace(quit=quit_application))
                    modules = {'FreeCAD': app, 'PySide': SimpleNamespace(QtCore=qt),
                               'build': SimpleNamespace(build=build), 'native': SimpleNamespace(build=build)}
                    result = Path(tmp)/'result.json'
                    env = {'SC_CAD_DIR': tmp, 'SC_CAD_STAGE': 'build', 'SC_CAD_RESULT': str(result),
                           'STACKED_SOURCE': str(Path(tmp)/'designs/stacked'),
                           'STACKED_OUTPUT': tmp, 'STACKED_RESULT': str(result)}
                    with patch.dict(sys.modules, modules), patch.dict(os.environ, env), \
                            patch.object(sys, 'path', list(sys.path)), patch('traceback.print_exc'):
                        exec(compile((Path(__file__).resolve().parents[2]/macro).read_text(), macro, 'exec'), {})
                    self.assertEqual(exited, [True])
                    self.assertEqual(result.exists(), not fails)


