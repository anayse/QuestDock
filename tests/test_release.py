"""Release contents remain complete without invoking PyInstaller in this test."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from tools import release
from installer.setup_launcher import PAYLOAD_FILES


class ReleaseContentsTests(unittest.TestCase):
    def test_license_and_language_navigation_files_are_distributed(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            root=Path(tmp).resolve()
            for folder in ('tools','build','dist','installer','docs'):(root/folder).mkdir()
            for name in ('README.md','README.en.md','CHANGELOG.md','LICENSE','NOTICE'):
                (root/name).write_text(name,encoding='utf-8')
            for name in ('install.ps1','install_paths.ps1','uninstall.ps1'):
                (root/'installer'/name).write_text(name,encoding='utf-8')
            (root/'docs'/'USER_GUIDE.md').write_text('Guide',encoding='utf-8')
            def fake_build(command,**kwargs):
                name=command[command.index('--name')+1]
                (root/'dist'/(name+'.exe')).write_bytes(b'MZ'+name.encode())
            with patch.object(release,'__file__',str(root/'tools'/'release.py')),patch.object(release.subprocess,'run',side_effect=fake_build),patch.object(release.sys,'argv',['release']),contextlib.redirect_stdout(io.StringIO()):
                release.main()
            target=root/'releases'/('v'+release.VERSION)
            with zipfile.ZipFile(target/('QuestDock-v'+release.VERSION+'-Windows.zip')) as archive:
                for name in ('README.md','README.en.md','LICENSE','NOTICE','docs/USER_GUIDE.md'):
                    self.assertIn(name,archive.namelist())
                self.assertNotIn('QuestDock.exe',archive.namelist())
            with zipfile.ZipFile(root/'build'/'setup-payload.zip') as archive:
                self.assertEqual(set(archive.namelist()),PAYLOAD_FILES)
                self.assertEqual(archive.read('LICENSE'),b'LICENSE')
