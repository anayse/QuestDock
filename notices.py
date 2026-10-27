"""Borderless notices for startup errors and duplicate launches."""
import tkinter as tk


def show_notice(title,message,parent=None):
    owned=parent is None
    root=tk.Tk() if owned else parent
    if owned:root.withdraw()
    dialog=tk.Toplevel(root);dialog.overrideredirect(True)
    dialog.configure(bg='#292f42');dialog.attributes('-topmost',True)
    frame=tk.Frame(dialog,bg='#141925',padx=20,pady=16);frame.pack(fill='both',expand=True,padx=1,pady=1)
    tk.Label(frame,text=title,bg='#141925',fg='#eef0fa',font=('Microsoft YaHei UI',14,'bold')).pack(anchor='w')
    tk.Label(frame,text=message,bg='#141925',fg='#9aa4bd',font=('Microsoft YaHei UI',10),wraplength=360,justify='left').pack(anchor='w',pady=16)
    tk.Button(frame,text='关闭',command=dialog.destroy,bg='#ac9cff',fg='#0d1019',relief='flat',padx=18,pady=7).pack(anchor='e')
    dialog.update_idletasks()
    x=max(0,(dialog.winfo_screenwidth()-dialog.winfo_reqwidth())//2)
    y=max(0,(dialog.winfo_screenheight()-dialog.winfo_reqheight())//2)
    dialog.geometry(f'+{x}+{y}')
    for key in ('<Escape>','<Alt-F4>','<Control-q>'):dialog.bind(key,lambda e:dialog.destroy())
    dialog.focus_force();root.wait_window(dialog)
    if owned:root.destroy()
