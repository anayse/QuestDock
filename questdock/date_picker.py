"""Dark popup calendar; dates are selected rather than typed."""
import calendar
import datetime as dt
import tkinter as tk
from tkinter import ttk


class DatePicker(tk.Toplevel):
    def __init__(self,parent,selected,on_select,anchor=None):
        super().__init__(parent)
        self.title('选择日期');self.overrideredirect(True);self.configure(bg='#141925',highlightbackground='#363d55',highlightthickness=1);self.resizable(False,False)
        self.transient(parent);self.attributes('-topmost',True)
        self.selected=selected;self.on_select=on_select
        self.year=tk.StringVar(value=str(selected.year));self.month=tk.StringVar(value=str(selected.month))
        top=tk.Frame(self,bg='#141925');top.pack(fill='x',padx=12,pady=12)
        self.button(top,'‹',lambda:self.move(-1)).pack(side='left')
        year=ttk.Combobox(top,textvariable=self.year,values=list(range(1,10000)),width=6,state='readonly');year.pack(side='left',padx=4)
        month=ttk.Combobox(top,textvariable=self.month,values=list(range(1,13)),width=3,state='readonly');month.pack(side='left',padx=4)
        year.bind('<<ComboboxSelected>>',lambda e:self.render());month.bind('<<ComboboxSelected>>',lambda e:self.render())
        self.button(top,'›',lambda:self.move(1)).pack(side='left')
        self.grid_frame=tk.Frame(self,bg='#141925');self.grid_frame.pack(padx=12)
        footer=tk.Frame(self,bg='#141925');footer.pack(fill='x',padx=12,pady=12)
        self.button(footer,'选今天',lambda:self.choose(dt.date.today())).pack(side='left')
        self.button(footer,'取消',self.destroy).pack(side='right')
        self.bind('<Escape>',lambda e:(self.destroy(),'break')[-1])
        self.render();self.update_idletasks()
        anchor=anchor or parent
        x=max(0,min(anchor.winfo_rootx(),self.winfo_screenwidth()-self.winfo_reqwidth()-10))
        y=anchor.winfo_rooty()+anchor.winfo_height()+4
        if y+self.winfo_reqheight()>self.winfo_screenheight()-40:y=max(0,anchor.winfo_rooty()-self.winfo_reqheight()-4)
        self.owner=parent.winfo_toplevel()
        def outside(e):
            if not self.winfo_exists():return
            if not (self.winfo_rootx()<=e.x_root<self.winfo_rootx()+self.winfo_width() and self.winfo_rooty()<=e.y_root<self.winfo_rooty()+self.winfo_height()):self.destroy()
        self.outside_binding=self.owner.bind('<ButtonPress-1>',outside,add='+')
        self.geometry(f'+{x}+{y}')
        self.after_idle(self.show_above_owner)

    def show_above_owner(self):
        if self.winfo_exists():self.lift();self.focus_force()

    def destroy(self):
        if getattr(self,'outside_binding',None):
            self.owner.unbind('<ButtonPress-1>',self.outside_binding);self.outside_binding=None
        super().destroy()

    def button(self,parent,text,command,selected=False):
        return tk.Button(parent,text=text,command=command,bg='#ac9cff' if selected else '#202638',fg='#0d1019' if selected else '#eef0fa',activebackground='#39344e',activeforeground='#eef0fa',relief='flat',bd=0,font=('Microsoft YaHei UI',10),padx=7,pady=5)

    def move(self,delta):
        value=(int(self.year.get())-1)*12+int(self.month.get())-1+delta
        if not 0<=value<9999*12:return
        year,month=divmod(value,12);self.year.set(str(year+1));self.month.set(str(month+1));self.render()

    def choose(self,day):self.on_select(day);self.destroy()

    def render(self):
        for child in self.grid_frame.winfo_children():child.destroy()
        for col,label in enumerate('一二三四五六日'):
            tk.Label(self.grid_frame,text=label,bg='#141925',fg='#9aa4bd',width=3).grid(row=0,column=col,pady=4)
        year,month=int(self.year.get()),int(self.month.get())
        self.day_buttons={}
        for row,week in enumerate(calendar.monthcalendar(year,month),1):
            for col,day in enumerate(week):
                if not day:continue
                date=dt.date(year,month,day)
                button=self.button(self.grid_frame,str(day),lambda d=date:self.choose(d),date==self.selected)
                button.grid(row=row,column=col,padx=2,pady=2,sticky='nsew');self.day_buttons[day]=button
