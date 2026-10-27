"""Build an immutable versioned release directory."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
import argparse
from questdock.version import VERSION,DISPLAY_VERSION


def main():
    from questdock.app import initial
    if initial()['tasks']:raise SystemExit('公开发行版必须从空任务列表开始，已取消打包。')
    root=Path(__file__).resolve().parents[1]
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=root/'releases',help='Output parent directory; existing versions are never overwritten.')
    args=parser.parse_args()
    target=args.output_dir.resolve()/('v'+VERSION)
    if target.exists():raise SystemExit('该版本目录已存在，禁止覆盖。请增加版本号。')
    subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--onefile','--windowed','--paths',str(root),'--specpath','build','--icon',str(root/'assets/questdock.ico'),'--add-data',str(root/'questdock/resources/update_install.ps1')+';questdock/resources','--name','QuestDock','questdock/launcher.py'],cwd=root,check=True)
    payload=root/'build'/'setup-payload.zip'
    with zipfile.ZipFile(payload,'w',zipfile.ZIP_DEFLATED) as archive:
        archive.write(root/'dist'/'QuestDock.exe','QuestDock.exe')
        for name in ('install.ps1','install_paths.ps1','uninstall.ps1'):archive.write(root/'installer'/name,name)
        for name in ('LICENSE','NOTICE'):archive.write(root/name,name)
        archive.writestr('version.json',json.dumps({'version':VERSION,'display_version':DISPLAY_VERSION}))
    subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--onefile','--windowed','--paths',str(root),'--specpath','build','--icon',str(root/'assets/questdock.ico'),'--add-data',str(payload)+';.','--name','QuestDock-Setup','installer/setup_launcher.py'],cwd=root,check=True)
    target.mkdir(parents=True)
    shutil.copy2(root/'dist'/'QuestDock-Setup.exe',target/'QuestDock-Setup.exe')
    # A .bin asset is exclusively for the updater; public EXEs are installers.
    shutil.copy2(root/'dist'/'QuestDock.exe',target/'QuestDock-update.bin')
    for name in ('README.md','README.en.md','CHANGELOG.md','LICENSE','NOTICE'):shutil.copy2(root/name,target/name)
    shutil.copytree(root/'docs',target/'docs')
    zip_path=target/('QuestDock-v'+VERSION+'-Windows.zip')
    with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as archive:
        for name in ('QuestDock-Setup.exe','README.md','README.en.md','CHANGELOG.md','LICENSE','NOTICE'):archive.write(target/name,name)
        for path in sorted((target/'docs').rglob('*')):
            if path.is_file():archive.write(path,path.relative_to(target))
    files=[target/'QuestDock-Setup.exe',target/'QuestDock-update.bin',zip_path]
    (target/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in files),encoding='utf-8')
    print(target)


if __name__=='__main__':main()
