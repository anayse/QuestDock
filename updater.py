"""GitHub Releases checks and verified downloads; never touches user saves."""
import hashlib
import json
import re
import urllib.request
from pathlib import Path
from version import VERSION


MAX_DOWNLOAD=250*1024*1024


def version_tuple(value):
    match=re.fullmatch(r'[vV]?(\d+)\.(\d+)(?:\.(\d+))?',value)
    if not match:raise ValueError('版本号须为 v1.0 或 v1.0.0；仅支持正式版。')
    return tuple(int(n or 0) for n in match.groups())


def repository(value):
    value=value.strip().removeprefix('https://github.com/').rstrip('/').removesuffix('.git')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+',value):
        raise ValueError('请输入 GitHub 仓库地址或 owner/repository。')
    if value.split('/')[1] in ('.','..'):raise ValueError('仓库名无效。')
    return value


def request(url):
    return urllib.request.Request(url,headers={'User-Agent':f'QuestDock/{VERSION}','Accept':'application/vnd.github+json'})


def select_release(data,repo,current=VERSION):
    if data.get('draft') or data.get('prerelease'):return None
    tag=data.get('tag_name','')
    if version_tuple(tag)<=version_tuple(current):return None
    asset=next((a for a in data.get('assets',[]) if a.get('name')=='QuestDock.exe'),None)
    if not asset:raise ValueError('新版尚未上传 QuestDock.exe。')
    digest=asset.get('digest') or ''
    if not re.fullmatch(r'sha256:[0-9a-fA-F]{64}',digest):
        raise ValueError('新版缺少 SHA-256 校验信息，暂不下载。')
    url=asset.get('browser_download_url','')
    if not url.startswith(f'https://github.com/{repo}/releases/download/'):
        raise ValueError('下载地址与当前仓库不匹配。')
    size=asset.get('size',0)
    if not isinstance(size,int) or not 0<size<=MAX_DOWNLOAD:raise ValueError('安装包大小无效。')
    return dict(version=tag.lstrip('vV'),url=url,sha256=digest[7:].lower(),size=size,notes=str(data.get('body') or '')[:4000])


def check_release(repo,opener=urllib.request.urlopen):
    repo=repository(repo)
    with opener(request(f'https://api.github.com/repos/{repo}/releases/latest'),timeout=15) as response:
        raw=response.read(1024*1024+1)
    if len(raw)>1024*1024:raise ValueError('更新信息过大。')
    return select_release(json.loads(raw),repo)


def download_release(release,folder,opener=urllib.request.urlopen):
    folder=Path(folder)/('v'+release['version']);folder.mkdir(parents=True,exist_ok=True)
    target=folder/'QuestDock.exe';temporary=folder/'QuestDock.download'
    digest=hashlib.sha256();size=0;signature=b''
    try:
        with opener(request(release['url']),timeout=30) as response,temporary.open('wb') as output:
            while True:
                chunk=response.read(128*1024)
                if not chunk:break
                if not signature:signature=chunk[:2]
                size+=len(chunk)
                if size>release['size'] or size>MAX_DOWNLOAD:raise ValueError('下载大小超出发布信息。')
                digest.update(chunk);output.write(chunk)
        if size!=release['size'] or digest.hexdigest()!=release['sha256'] or signature!=b'MZ':
            raise ValueError('更新包校验失败，已取消更新。')
        temporary.replace(target)
        return target
    finally:
        if temporary.exists():temporary.unlink()
