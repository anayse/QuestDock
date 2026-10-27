import hashlib
import io
import tempfile
import unittest
from pathlib import Path
from updater import repository,version_tuple,select_release,download_release
from version import VERSION


class UpdateTests(unittest.TestCase):
    def release(self,tag=None,body=b'MZtest application'):
        if tag is None:tag='v'+str(version_tuple(VERSION)[0]+1)+'.0.0'
        return dict(tag_name=tag,draft=False,prerelease=False,assets=[dict(name='QuestDock.exe',size=len(body),digest='sha256:'+hashlib.sha256(body).hexdigest(),browser_download_url='https://github.com/anayse/QuestDock/releases/download/'+tag+'/QuestDock.exe')])

    def test_semantic_versions_and_repository_validation(self):
        self.assertEqual(version_tuple('V1.0'),(1,0,0))
        self.assertGreater(version_tuple('1.10.0'),version_tuple('1.9.9'))
        self.assertEqual(repository('https://github.com/anayse/QuestDock.git'),'anayse/QuestDock')
        for value in ('https://evil.example/a/b','../bad','a/..','a/b?token=secret'):
            with self.assertRaises(ValueError):repository(value)

    def test_older_current_and_prerelease_are_ignored(self):
        for tag in ('v0.9.0','v1.0','v1.0.0','v'+VERSION):
            self.assertIsNone(select_release(self.release(tag),'anayse/QuestDock'))
        release=self.release();release['prerelease']=True
        self.assertIsNone(select_release(release,'anayse/QuestDock'))

    def test_unknown_source_missing_digest_and_oversize_are_rejected(self):
        for field,value in [('digest',None),('size',999999999),('browser_download_url','https://evil.example/file.exe')]:
            data=self.release();data['assets'][0][field]=value
            with self.assertRaises(ValueError):select_release(data,'anayse/QuestDock')

    def test_verified_download_and_failure_do_not_replace_cached_exe(self):
        good=b'MZtest application'
        release=select_release(self.release(body=good),'anayse/QuestDock')
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            path=download_release(release,folder,opener=lambda *a,**kw:io.BytesIO(good))
            self.assertEqual(path.read_bytes(),good)
            for bad in (b'MZwrong same size!',b'MZtoo big'*100,b''):
                with self.assertRaises(ValueError):download_release(release,folder,opener=lambda *a,**kw:io.BytesIO(bad))
                self.assertEqual(path.read_bytes(),good)
                self.assertFalse((path.parent/'QuestDock.download').exists())

    def test_non_executable_even_with_matching_hash_is_rejected(self):
        body=b'not an executable'
        release=select_release(self.release(body=body),'anayse/QuestDock')
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            with self.assertRaises(ValueError):download_release(release,folder,opener=lambda *a,**kw:io.BytesIO(body))

    def test_windows_installer_preserves_backup_and_rejects_bad_checksum(self):
        import os,subprocess
        if os.name!='nt':self.skipTest('Windows updater')
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            folder=Path(folder);source=folder/'new.exe';target=folder/'QuestDock.exe'
            source.write_bytes(b'MZnew');target.write_bytes(b'MZold')
            def install(checksum):
                return subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(Path(__file__).with_name('update_install.ps1')),'-Source',str(source),'-Target',str(target),'-Sha256',checksum,'-AppProcessId','2147483647','-SkipLaunch'],capture_output=True)
            self.assertNotEqual(install('0'*64).returncode,0)
            self.assertEqual(target.read_bytes(),b'MZold')
            result=install(hashlib.sha256(source.read_bytes()).hexdigest())
            self.assertEqual(result.returncode,0,(result.stderr.decode(errors='replace'),(folder/'update-error.log').read_text(encoding='utf-8-sig') if (folder/'update-error.log').exists() else ''))
            self.assertEqual(target.read_bytes(),b'MZnew')
            self.assertEqual((folder/'QuestDock.previous.exe').read_bytes(),b'MZold')
