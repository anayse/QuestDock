"""Small canvas slider with the same colors as the task panel."""
import tkinter as tk
from PIL import Image, ImageDraw, ImageTk


class OpacitySlider(tk.Canvas):
    def __init__(self, parent, variable, command, commit):
        super().__init__(parent, height=30, width=120, bg='#0d1019',
                         highlightthickness=0, bd=0, takefocus=True, cursor='hand2')
        self.variable=variable;self.command=command;self.commit=commit
        self.hover=False;self.focused=False
        self.trace=variable.trace_add('write',lambda *args:self.paint())
        self.bind('<Configure>',lambda e:self.paint())
        self.bind('<Button-1>',self.pointer)
        self.bind('<B1-Motion>',self.pointer)
        self.bind('<ButtonRelease-1>',lambda e:self.commit())
        self.bind('<Enter>',lambda e:self.set_hover(True))
        self.bind('<Leave>',lambda e:self.set_hover(False))
        self.bind('<FocusIn>',lambda e:self.set_focus(True))
        self.bind('<FocusOut>',lambda e:self.set_focus(False))
        for key,step in [('Left',-1),('Down',-1),('Right',1),('Up',1),('Prior',10),('Next',-10)]:
            self.bind('<'+key+'>',lambda e,s=step:self.change(self.variable.get()+s))
        self.bind('<Home>',lambda e:self.change(1))
        self.bind('<End>',lambda e:self.change(100))
        self.bind('<Destroy>',self.cleanup)

    def cleanup(self,e):
        if e.widget==self:self.variable.trace_remove('write',self.trace)

    def set_hover(self,value):self.hover=value;self.paint()
    def set_focus(self,value):self.focused=value;self.paint()

    def change(self,value):
        self.variable.set(max(1,min(100,round(value))))
        self.command(self.variable.get());self.commit();return 'break'

    def pointer(self,e):
        self.focus_set()
        value=1+99*(e.x-10)/max(1,self.winfo_width()-20)
        self.variable.set(max(1,min(100,round(value))))
        self.command(self.variable.get());return 'break'

    def paint(self):
        self.delete('all');w=max(24,self.winfo_width());y=15
        x=10+(w-20)*(max(1,min(100,self.variable.get()))-1)/99
        scale=4
        art=Image.new('RGB',(w*scale,30*scale),'#0d1019');draw=ImageDraw.Draw(art)
        def rounded(box,r,fill):draw.rounded_rectangle(tuple(round(v*scale) for v in box),radius=r*scale,fill=fill)
        rounded((10,y-2,w-10,y+2),2,'#2b3148')
        if x>10:rounded((10,y-2,x,y+2),2,'#a99bf5')
        if self.hover or self.focused:draw.ellipse(tuple(round(v*scale) for v in (x-9,y-9,x+9,y+9)),fill='#302b49')
        draw.ellipse(tuple(round(v*scale) for v in (x-5,y-5,x+5,y+5)),fill='#ddd6ff',outline='#a99bf5',width=scale)
        self.image=ImageTk.PhotoImage(art.resize((w,30),Image.Resampling.LANCZOS),master=self)
        self.create_image(0,0,image=self.image,anchor='nw')
