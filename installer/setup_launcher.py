"""Interactive installer. The runtime is extracted only after Install is clicked."""
import os
from pathlib import Path
import queue
import subprocess
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog,ttk
import zipfile
from questdock.version import DISPLAY_VERSION

PAYLOAD_FILES={'QuestDock.exe','install.ps1','install_paths.ps1','uninstall.ps1','version.json','LICENSE','NOTICE'}


def extract_payload(archive,destination):
    with zipfile.ZipFile(archive) as bundle:
        if set(bundle.namelist())!=PAYLOAD_FILES or len(bundle.namelist())!=len(PAYLOAD_FILES):
            raise ValueError('安装包内容不完整，请重新下载。')
        if any(i.file_size>250*1024*1024 for i in bundle.infolist()):
            raise ValueError('安装包文件大小异常。')
        bundle.extractall(destination)


def default_directory():
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows\CurrentVersion\Uninstall\QuestDock') as key:
            value,_=winreg.QueryValueEx(key,'InstallLocation')
            if value:return value
    except OSError:pass
    return str(Path(os.environ['LOCALAPPDATA'])/'Programs'/'QuestDock')


def install_to(directory,archive):
    with tempfile.TemporaryDirectory(prefix='QuestDock-setup-') as folder:
        extract_payload(archive,folder)
        command=[str(Path(os.environ['SystemRoot'])/'System32'/'WindowsPowerShell'/'v1.0'/'powershell.exe'),
                 '-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(Path(folder)/'install.ps1'),
                 '-InstallDirectory',directory]
        result=subprocess.run(command,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode:
            detail=result.stderr.decode('utf-8',errors='replace').strip()
            raise RuntimeError('安装失败，请确认已退出 QuestDock，且所选目录可写。\n'+detail[-800:])


def main():
    root=tk.Tk();root.title('QuestDock '+DISPLAY_VERSION+' 安装');root.geometry('600x310');root.resizable(False,False)
    root.configure(bg='#141925')
    style=ttk.Style(root);style.theme_use('clam')
    style.configure('TEntry',fieldbackground='#20283a',foreground='#eef0fa',padding=8)
    style.configure('TButton',padding=(14,8),font=('Microsoft YaHei UI',10))
    body=tk.Frame(root,bg='#141925',padx=26,pady=22);body.pack(fill='both',expand=True)
    def label(text,size=10,color='#9aa4bd'):
        widget=tk.Label(body,text=text,bg='#141925',fg=color,font=('Microsoft YaHei UI',size),anchor='w',justify='left')
        widget.pack(anchor='w',pady=(0,10));return widget
    label('安装 QuestDock '+DISPLAY_VERSION,18,'#eef0fa')
    label('选择安装位置；你的任务存档会保留。')
    label('安装位置',10,'#eef0fa')
    row=tk.Frame(body,bg='#141925');row.pack(fill='x')
    directory=tk.StringVar(value=default_directory())
    entry=ttk.Entry(row,textvariable=directory);entry.pack(side='left',fill='x',expand=True)
    def browse():
        parent=filedialog.askdirectory(parent=root,title='选择安装位置',initialdir=str(Path(directory.get()).parent),mustexist=False)
        if parent:directory.set(str(Path(parent) if Path(parent).name.lower()=='questdock' else Path(parent)/'QuestDock'))
    browse_button=ttk.Button(row,text='浏览…',command=browse);browse_button.pack(side='right',padx=(10,0))
    status=label('点击“安装”后才会写入程序文件。');status.configure(wraplength=540)
    status.pack_configure(pady=(14,0))
    buttons=tk.Frame(body,bg='#141925');buttons.pack(side='bottom',fill='x')
    state={'busy':False,'done':False};results=queue.Queue()
    def close():
        if not state['busy']:root.destroy()
    cancel=ttk.Button(buttons,text='取消',command=close);cancel.pack(side='right')
    def poll():
        try:failure=results.get_nowait()
        except queue.Empty:root.after(100,poll);return
        state['busy']=False;cancel.configure(state='normal')
        if failure:
            status.configure(text=failure,fg='#f3a6a6');entry.configure(state='normal');browse_button.configure(state='normal');submit.configure(state='normal')
        else:
            state['done']=True;status.configure(text='安装完成，可从桌面或开始菜单打开 QuestDock。',fg='#83dfc2')
            cancel.configure(text='完成')
    def install():
        path=directory.get().strip()
        if not path:status.configure(text='请选择安装位置。',fg='#f3a6a6');return
        state['busy']=True
        for control in (entry,browse_button,submit,cancel):control.configure(state='disabled')
        status.configure(text='正在安装，请稍候…',fg='#9aa4bd')
        def worker():
            try:install_to(path,Path(__file__).with_name('setup-payload.zip'));results.put(None)
            except Exception as exc:results.put(str(exc))
        threading.Thread(target=worker,daemon=True).start();root.after(100,poll)
    submit=ttk.Button(buttons,text='安装',command=install);submit.pack(side='right',padx=10)
    root.protocol('WM_DELETE_WINDOW',close);root.mainloop()


if __name__=='__main__':main()
