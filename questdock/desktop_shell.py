"""Small desktop entry, edge docking and low-cost live display controls."""
import tkinter as tk
from PIL import ImageTk
from questdock.orb_art import artwork
from questdock.layered_orb import LayeredOrb
from questdock.desktop_geometry import clamp_position, dock_position, nearest_edge, work_area

BALL_SIZE=56

class DesktopShell:
    def configure_desktop(self):
        self.root.minsize(360,460)
        self.root.geometry(f"{self.settings.get('panel_width',380)}x{self.settings.get('panel_height',600)}")
        self.root.resizable(not self.settings.get('position_locked',False),not self.settings.get('position_locked',False))
        self.root.bind('<Configure>',self.panel_configured,add='+')
        self.root.bind_all('<Control-Shift-R>',lambda e:self.recover_display())
        self.schedule_hide()

    def create_ball(self):
        if self.settings.get('desktop_layout_version')!=2:
            self.settings.update(panel_width=380,panel_height=600,desktop_layout_version=2)
        self.area=work_area(self.root)
        self.hide_job=None;self.move_job=None;self.pending_move=None;self.lock_job=None
        self.orb_hover=False;self.orb_hidden=False;self.dragged=False;self.dragging_ball=False;self.menu_open=False
        self.dock_side=self.settings.get('dock_side')
        if self.dock_side not in ('left','right','top','bottom'):self.dock_side=None
        self.ball=tk.Toplevel(self.root);self.ball.overrideredirect(True)
        self.ball.configure(bg='#ff00ff');self.ball.attributes('-transparentcolor','#ff00ff');self.ball.attributes('-topmost',True)
        x,y=clamp_position(self.settings.get('ball_x',self.area[0]),self.settings.get('ball_y',180),BALL_SIZE,BALL_SIZE,self.area)
        if 'dock_side' not in self.settings:self.dock_side=nearest_edge(x,y,BALL_SIZE,self.area,32)
        if self.dock_side:x,y=dock_position(self.dock_side,x,y,BALL_SIZE,self.area)
        self.ball_anchor=(x,y)
        self.ball.geometry(f'{BALL_SIZE}x{BALL_SIZE}{x:+d}{y:+d}')
        self.orb=tk.Canvas(self.ball,width=BALL_SIZE,height=BALL_SIZE,bg='#ff00ff',highlightthickness=0,cursor='hand2')
        self.ball.bind('<ButtonPress-1>',self.ball_press);self.ball.bind('<B1-Motion>',self.ball_drag);self.ball.bind('<ButtonRelease-1>',self.ball_release)
        self.ball.bind('<Enter>',self.orb_enter);self.ball.bind('<Leave>',self.orb_leave)
        self.ball_menu=tk.Menu(self.ball,tearoff=False,bg='#141925',fg='#eef0fa',activebackground='#332d50')
        self.ball_menu.add_command(label='展开 / 收起',command=self.toggle_panel)
        self.ball_menu.add_command(label='桌面设置',command=self.open_desktop_settings)
        self.ball_menu.add_command(label='锁定 / 解锁位置',command=self.toggle_position_lock)
        self.ball_menu.add_command(label='恢复默认显示',command=self.recover_display)
        self.ball_menu.add_separator();self.ball_menu.add_command(label='退出 QuestDock',command=self.quit)
        self.ball.bind('<Button-3>',self.popup_ball_menu)
        self.layered_orb=LayeredOrb(self.ball)
        self.ball.bind('<Map>',lambda e:self.root.after_idle(self.paint_ball))
        self.paint_ball()

    def paint_ball(self,hover=False):
        c=self.orb;c.delete('all')
        planned=[t for t in self.data['tasks'] if t.get('planned_date')==self.data['date']]
        daily=planned
        done=sum(t['progress']>=t['target'] for t in daily)
        ready=any(not t['claimed'] and t['progress']>=t['target'] for t in self.data['tasks'])
        self.orb_state=(round(20*done/max(1,len(daily))),ready,hover)
        art=artwork(BALL_SIZE,*self.orb_state)
        self.orb_image=ImageTk.PhotoImage(art,master=self.ball)
        c.create_image(0,0,image=self.orb_image,anchor='nw')
        self.orb_clock_item=c.create_text(28,41,text=self.focus_time_text() if self.focus else f'{done}/{len(daily)}',fill='#f2d5a4' if self.focus else '#d5d9ef',font=('Segoe UI',8,'bold'))
        self.refresh_orb_surface()

    def refresh_orb_surface(self):
        if not hasattr(self,'layered_orb') or not self.ball.winfo_ismapped():return
        text=self.orb.itemcget(self.orb_clock_item,'text')
        alpha=max(.85,self.opacity.get()/100) if self.orb_hover else self.opacity.get()/100
        self.layered_orb.present(*self.orb_state,text,alpha)

    def cancel_hide(self):
        if self.hide_job:self.root.after_cancel(self.hide_job);self.hide_job=None

    def schedule_hide(self):
        self.cancel_hide()
        if self.dock_side and self.settings.get('edge_hide',True) and not self.menu_open and not self.dragging_ball:
            self.hide_job=self.root.after(900,self.hide_ball)

    def hide_ball(self):
        self.hide_job=None
        if self.orb_hover or self.dragging_ball or self.menu_open or not self.dock_side or not self.settings.get('edge_hide',True):return
        x,y=dock_position(self.dock_side,*self.ball_anchor,BALL_SIZE,self.area,True,16)
        # Tk '-N' means distance from the RIGHT/BOTTOM, not absolute negative.
        self.position_ball(x,y);self.orb_hidden=True

    def position_ball(self,x,y):
        # wm geometry '+-N' denotes an absolute negative offset in Tk.
        self.ball.geometry(f'+{int(x)}+{int(y)}')

    def reveal_ball(self):
        self.cancel_hide()
        self.position_ball(*self.ball_anchor);self.orb_hidden=False

    def orb_enter(self,e=None):
        self.orb_hover=True;self.reveal_ball()
        self.ball.attributes('-alpha',max(.85,self.opacity.get()/100))
        self.paint_ball(True)

    def orb_leave(self,e=None):
        px,py=self.ball.winfo_pointerxy();x,y=self.ball.winfo_x(),self.ball.winfo_y()
        if x<=px<x+BALL_SIZE and y<=py<y+BALL_SIZE:return
        self.orb_hover=False;self.ball.attributes('-alpha',self.opacity.get()/100)
        self.paint_ball(False)
        self.schedule_hide()

    def popup_ball_menu(self,e):
        self.menu_open=True;self.reveal_ball()
        try:self.ball_menu.tk_popup(e.x_root,e.y_root)
        finally:
            try:self.ball_menu.grab_release()
            except tk.TclError:pass
            self.menu_open=False;self.schedule_hide()

    def ball_press(self,e):
        self.reveal_ball();self.dragging_ball=True;self.dragged=False
        self.area=work_area(self.root)
        self.drag_start=(e.x_root,e.y_root,*self.ball_anchor)

    def queue_ball_move(self,x,y):
        self.pending_move=(x,y)
        if self.move_job is None:self.move_job=self.root.after(16,self.flush_ball_move)

    def flush_ball_move(self):
        self.move_job=None
        if self.pending_move:
            self.ball_anchor=self.pending_move;self.pending_move=None;self.position_ball(*self.ball_anchor)

    def ball_drag(self,e):
        sx,sy,x,y=self.drag_start;dx=e.x_root-sx;dy=e.y_root-sy
        if abs(dx)+abs(dy)>5:self.dragged=True
        if self.settings.get('position_locked',False):return
        if self.dragged:
            self.dock_side=None;self.queue_ball_move(*clamp_position(x+dx,y+dy,BALL_SIZE,BALL_SIZE,self.area))

    def ball_release(self,e=None):
        if self.move_job:self.root.after_cancel(self.move_job);self.move_job=None
        self.flush_ball_move();self.dragging_ball=False
        if self.settings.get('position_locked',False) and self.dragged:self.schedule_hide();return
        if self.dragged:
            self.dock_side=nearest_edge(*self.ball_anchor,BALL_SIZE,self.area,32)
            if self.dock_side:self.ball_anchor=dock_position(self.dock_side,*self.ball_anchor,BALL_SIZE,self.area)
            self.position_ball(*self.ball_anchor)
            self.settings.update(ball_x=self.ball_anchor[0],ball_y=self.ball_anchor[1],dock_side=self.dock_side)
            self.save();self.schedule_hide()
        else:self.toggle_panel()

    def toggle_panel(self):
        if self.root.state()=='normal':self.collapse();return
        previous_day=self.data['date'];self.reset_day()
        if previous_day!=self.data['date']:self.render()
        self.reveal_ball();self.area=work_area(self.root)
        width=min(max(360,self.settings.get('panel_width',380)),self.area[2]-self.area[0]-12)
        height=min(max(460,self.settings.get('panel_height',600)),self.area[3]-self.area[1]-46)
        x=self.settings.get('panel_x',self.ball_anchor[0]+BALL_SIZE+8)
        y=self.settings.get('panel_y',self.ball_anchor[1])
        if 'panel_x' not in self.settings and x+width>self.area[2]:x=self.ball_anchor[0]-width-8
        x,y=clamp_position(x,y,width,height+32,self.area)
        self.settings.update(panel_x=x,panel_y=y,panel_width=width,panel_height=height)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        self.root.attributes('-alpha',self.opacity.get()/100)
        self.root.deiconify();self.root.lift();self.root.focus_force();self.panel_visible=True;self.schedule_hide()

    def collapse(self):
        if self.dialog and self.dialog.winfo_exists():self.dialog.lift();self.dialog.focus_force();return
        self.panel_visible=False;self.remember_panel();self.save();self.root.withdraw();self.schedule_hide()

    def remember_panel(self):
        if self.root.state()=='normal':
            self.settings.update(panel_x=self.root.winfo_x(),panel_y=self.root.winfo_y(),panel_width=self.root.winfo_width(),panel_height=self.root.winfo_height())

    def panel_configured(self,e):
        if e.widget!=self.root or self.root.state()!='normal':return
        if self.settings.get('position_locked',False):
            target=(self.settings.get('panel_x',self.root.winfo_x()),self.settings.get('panel_y',self.root.winfo_y()))
            if (self.root.winfo_x(),self.root.winfo_y())!=target and self.lock_job is None:self.lock_job=self.root.after_idle(self.restore_panel_position)
        else:self.remember_panel()

    def restore_panel_position(self):
        self.lock_job=None
        if self.settings.get('position_locked',False):self.root.geometry(f"+{self.settings['panel_x']}+{self.settings['panel_y']}")

    def toggle_position_lock(self):
        self.remember_panel();locked=not self.settings.get('position_locked',False)
        self.settings['position_locked']=locked;self.root.resizable(not locked,not locked)
        self.save();self.request_draw()
        if hasattr(self,'lock_button'):self.lock_button.configure(text='解锁位置' if locked else '锁定位置')

    def recover_display(self):
        self.settings.update(position_locked=False,panel_width=380,panel_height=600)
        self.settings.pop('panel_x',None);self.settings.pop('panel_y',None)
        self.root.resizable(True,True);self.opacity.set(95);self.set_opacity(95);self.save()
        if self.root.state()=='normal':self.root.withdraw()
        self.toggle_panel();self.request_draw()

    def open_desktop_settings(self):
        if self.root.state()!='normal':self.toggle_panel()
        self.root.attributes('-alpha',max(.85,self.opacity.get()/100))
        self.show_settings=True;self.draw()

    def set_opacity(self,value):
        percent=max(1,min(100,round(float(value))))
        self.settings['opacity']=percent
        self.root.attributes('-alpha',percent/100)
        self.ball.attributes('-alpha',max(.85,percent/100) if self.orb_hover else percent/100)
        if hasattr(self,'opacity_readout'):self.opacity_readout.set(f'{percent}%')
        self.refresh_orb_surface()

    def slide_opacity(self,x):
        value=round(1+99*max(0,min(1,(x-40)/max(1,self.w-80))))
        self.opacity.set(value);self.set_opacity(value)

    def canvas_configured(self,e):
        size=(e.width,e.height)
        if size!=getattr(self,'canvas_size',None):self.canvas_size=size;self.request_draw()
