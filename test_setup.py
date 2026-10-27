import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import zipfile
from setup_launcher import extract_payload,install_to,PAYLOAD_FILES


class SetupTests(unittest.TestCase):
    def test_payload_rejects_missing_and_traversal_files(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            root=Path(tmp);archive=root/'payload.zip';dest=root/'out'
            for names in (['QuestDock.exe'],list(PAYLOAD_FILES)+['../outside.txt']):
                with zipfile.ZipFile(archive,'w') as z:
                    for name in names:z.writestr(name,b'test')
                with self.assertRaises(ValueError):extract_payload(archive,dest)
                self.assertFalse(dest.exists())

    def test_installer_uses_selected_directory_and_cleans_payload(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            root=Path(tmp);archive=root/'payload.zip';dest=root/'payload';dest.mkdir()
            with zipfile.ZipFile(archive,'w') as z:
                for name in PAYLOAD_FILES:z.writestr(name,b'test')
            from contextlib import nullcontext
            with patch('setup_launcher.tempfile.TemporaryDirectory',return_value=nullcontext(str(dest))),patch('setup_launcher.subprocess.run',return_value=SimpleNamespace(returncode=0,stderr=b'')) as run:
                install_to(r'D:\My Apps\QuestDock',archive)
                command=run.call_args.args[0]
                self.assertEqual(command[-2:],['-InstallDirectory',r'D:\My Apps\QuestDock'])
                self.assertEqual(set(p.name for p in dest.iterdir()),PAYLOAD_FILES)
                self.assertTrue(run.call_args.kwargs['capture_output'])
                run.return_value=SimpleNamespace(returncode=1,stderr=b'access denied')
                with self.assertRaises(RuntimeError):install_to(r'D:\My Apps\QuestDock',archive)
