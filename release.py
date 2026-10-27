"""Build an immutable versioned release directory."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from version import VERSION,DISPLAY_VERSION


def main():
    from app import initial
    if initial()['tasks']:raise SystemExit('公开发行版必须从空任务列表开始，已取消打包。')
    root=Path(__file__).resolve().parent
    target=root/'releases'/('v'+VERSION)
    if target.exists():raise SystemExit('该版本目录已存在，禁止覆盖。请增加版本号。')
    subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--onefile','--windowed','--icon','assets/questdock.ico','--add-data','update_install.ps1;.','--name','QuestDock','launcher.py'],cwd=root,check=True)
    target.mkdir(parents=True)
    for name in ('QuestDock.exe','Install.cmd','install.ps1','uninstall.ps1','README.md','CHANGELOG.md'):
        source=root/'dist'/name if name.endswith('.exe') else root/name
        shutil.copy2(source,target/name)
    (target/'version.json').write_text(json.dumps({'version':VERSION,'display_version':DISPLAY_VERSION},indent=2),encoding='utf-8')
    # The ZIP contains only installable files, never source or user data.
    zip_path=Path(shutil.make_archive(str(root/'releases'/('QuestDock-v'+VERSION+'-Windows')),'zip',target))
    checksum=hashlib.sha256((target/'QuestDock.exe').read_bytes()).hexdigest()
    (target/'SHA256SUMS.txt').write_text(checksum+'  QuestDock.exe\n'+hashlib.sha256(zip_path.read_bytes()).hexdigest()+'  '+zip_path.name+'\n',encoding='utf-8')
    shutil.move(str(zip_path),str(target/zip_path.name))
    print(target)


if __name__=='__main__':main()
