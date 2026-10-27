"""Arrowless, quiet scrollbar matching the main task list."""
import tkinter as tk


class SlimScrollbar(tk.Canvas):
    def __init__(self,parent,command):
        super().__init__(parent,width=8,bg='#141925',highlightthickness=0,bd=0)
        self.command=command;self.first=0.;self.last=1.;self.drag_offset=0
        self.bind('<Configure>',lambda e:self.paint())
        self.bind('<Button-1>',self.press);self.bind('<B1-Motion>',self.drag)
        self.bind('<Enter>',lambda e:self.paint(True));self.bind('<Leave>',lambda e:self.paint())

    def bounds(self):
        h=max(1,self.winfo_height());size=max(22,h*(self.last-self.first))
        top=(h-size)*self.first/max(.0001,1-(self.last-self.first))
        return top,min(h,size)

    def set(self,first,last):self.first=float(first);self.last=float(last);self.paint()

    def paint(self,hover=False):
        self.delete('all')
        if self.last-self.first>=.999:return
        top,size=self.bounds()
        self.create_line(4,top+3,4,top+size-3,fill='#ac9cff' if hover else '#595670',width=3,capstyle='round')

    def press(self,e):
        top,size=self.bounds();self.drag_offset=e.y-top if top<=e.y<=top+size else size/2
        self.drag(e)

    def drag(self,e):
        if self.last-self.first>=.999:return
        top,size=self.bounds();fraction=(e.y-self.drag_offset)/max(1,self.winfo_height()-size)
        self.command('moveto',max(0,min(1,fraction))*(1-self.last+self.first))
