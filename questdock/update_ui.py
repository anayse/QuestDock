"""Background update checks, verified staging, explicit restart to install."""
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk
import urllib.error
from questdock.updater import repository,check_release,download_release
from questdock.version import VERSION,DISPLAY_VERSION,DEFAULT_UPDATE_REPOSITORY


class UpdateUI:
    def start_update_service(self):
        self.update_busy=False;self.update_result=queue.Queue();self.update_ready=None
        self.update_status=tk.StringVar(value='当前版本 '+DISPLAY_VERSION)
        self.root.after(8000,self.automatic_update)

    def automatic_update(self):
        if self.settings.get('auto_update',False):self.check_updates(silent=True)
        self.root.after(6*60*60*1000,self.automatic_update)

    def update_settings(self):
        result=self.modal('版本与更新',f'QuestDock {DISPLAY_VERSION} · 正式版',420)
        if not result:return
        dialog,body=result
        tk.Label(body,text='GitHub 发布仓库',bg='#141925',fg='#9aa4bd').pack(anchor='w',pady=(8,4))
        entry=ttk.Entry(body);entry.insert(0,self.settings.get('update_repository',DEFAULT_UPDATE_REPOSITORY));entry.pack(fill='x')
        tk.Label(body,text='填写 owner/repository 或完整 GitHub 地址；支持公开仓库。',bg='#141925',fg='#8791a9',wraplength=350,justify='left').pack(anchor='w',pady=6)
        enabled=tk.BooleanVar(value=self.settings.get('auto_update',False))
        tk.Checkbutton(body,text='自动检查并下载新版（每 6 小时）',variable=enabled,bg='#141925',fg='#eef0fa',activebackground='#141925',activeforeground='#eef0fa',selectcolor='#292f42').pack(anchor='w',pady=5)
        tk.Label(body,text='下载后点击“安装并重启”完成更新，任务存档保留。',bg='#141925',fg='#8791a9',wraplength=350,justify='left').pack(anchor='w',pady=4)
        tk.Label(body,textvariable=self.update_status,bg='#141925',fg='#edc583',wraplength=350,justify='left').pack(anchor='w',pady=10)
        def save(check=False):
            if self.update_busy:self.update_status.set('正在检查或下载，请稍后修改设置。');return
            try:repo=repository(entry.get()) if entry.get().strip() else ''
            except ValueError as exc:self.update_status.set(str(exc));return
            if enabled.get() and not repo:self.update_status.set('请先填写发布仓库。');return
            if repo!=self.settings.get('update_repository',DEFAULT_UPDATE_REPOSITORY):self.update_ready=None
            self.settings.update(update_repository=repo,auto_update=enabled.get());self.save()
            self.update_status.set('设置已保存。' if repo else '尚未配置发布仓库，联网更新暂不可用。')
            if check or enabled.get():self.check_updates()
        self.form_button(dialog.action_bar,'保存',save,False).pack(side='left')
        self.form_button(dialog.action_bar,'检查更新',lambda:save(True),False).pack(side='left',padx=6)
        self.form_button(dialog.action_bar,'安装并重启',self.install_ready_update).pack(side='right')

    def check_updates(self,silent=False):
        if self.update_busy:return
        repo=self.settings.get('update_repository',DEFAULT_UPDATE_REPOSITORY)
        if not repo:self.update_status.set('尚未配置 GitHub 发布仓库。');return
        self.update_busy=True;self.update_ready=None;self.update_status.set('正在检查更新…')
        from questdock.app import DATA
        folder=DATA.parent/'updates'
        def worker():
            try:
                release=check_release(repo)
                if release is None:self.update_result.put(('current',None));return
                self.update_result.put(('progress','发现 V'+release['version']+'，正在下载并校验…'))
                staged=download_release(release,folder)
                self.update_result.put(('ready',(release,staged)))
            except urllib.error.HTTPError as exc:
                message={404:'仓库尚无正式 Release，或仓库不是公开仓库。',403:'GitHub 暂时限制请求，请稍后重试。'}.get(exc.code,f'GitHub 返回 HTTP {exc.code}。')
                self.update_result.put(('error',message))
            except Exception as exc:self.update_result.put(('error','更新失败：'+str(exc)))
        threading.Thread(target=worker,daemon=True,name='QuestDock-update').start()
        self.root.after(150,lambda:self.poll_update(silent))

    def poll_update(self,silent):
        try:kind,value=self.update_result.get_nowait()
        except queue.Empty:
            if not self.closing:self.root.after(150,lambda:self.poll_update(silent))
            return
        if kind=='progress':
            self.update_status.set(value);self.root.after(150,lambda:self.poll_update(silent));return
        self.update_busy=False
        if kind=='ready':
            self.update_ready=value;self.update_status.set('V'+value[0]['version']+' 已下载并校验，可安装并重启。')
            self.toast('新版已准备好，请在设置 → 版本与更新中安装')
        elif kind=='current':self.update_status.set('当前已是最新正式版：'+DISPLAY_VERSION)
        else:self.update_status.set(value)
        if not silent and kind=='error':self.toast(value)

    def install_ready_update(self):
        if not self.update_ready:self.update_status.set('请先检查并下载新版。');return
        if not getattr(sys,'frozen',False):self.update_status.set('源码运行模式不覆盖 Python；请使用发布版 EXE 更新。');return
        release,source=self.update_ready
        if self.dialog and self.dialog.winfo_exists():self.dialog.destroy()
        def install():
            self.save()
            if self.save_error:self.toast('存档未保存成功，已取消重启');return
            try:
                script=source.parent/'update_install.ps1'
                shutil.copyfile(Path(__file__).parent/'resources'/'update_install.ps1',script)
                startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
                subprocess.Popen(['powershell.exe','-NoProfile','-NonInteractive','-WindowStyle','Hidden','-ExecutionPolicy','Bypass','-File',str(script),'-Source',str(source),'-Target',sys.executable,'-Sha256',release['sha256'],'-AppProcessId',str(os.getpid()),'-Version',release['version']],startupinfo=startup,creationflags=subprocess.CREATE_NO_WINDOW)
            except OSError as exc:self.toast('无法启动更新：'+str(exc));return
            self.quit()
        self.confirm('安装并重启',f"将从 {DISPLAY_VERSION} 更新至 V{release['version']}。当前任务会保存，旧程序保留为 QuestDock.previous.exe。",install)
