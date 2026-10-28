"""QuestDock desktop shell: a custom-drawn, borderless mission interface."""
import tkinter as tk
from tkinter import ttk
import math
import datetime
import traceback
import tkinter.font as tkfont
from collections import OrderedDict
import time
from questdock.focus_timer import FocusTimer
from questdock.desktop_shell import DesktopShell
from questdock.compact_ui import CompactUI
from questdock.activity import ActivityUI
from questdock.task_types import TypeUI
from questdock.update_ui import UpdateUI
from questdock.version import DISPLAY_VERSION
from questdock.slim_scrollbar import SlimScrollbar
from questdock.step_rewards import pay_steps, unpaid_steps
from questdock.app import App as Core, TYPES, task

INK='#0d1019'
SURFACE='#141925'
CARD='#191f2e'
LINE='#292f42'
TEXT='#eef0fa'
SECOND='#9aa4bd'
DIM='#8791a9'
VIOLET='#ac9cff'
MINT='#83dfc2'
GOLD='#edc583'
COLORS=dict(zip(TYPES,[MINT,'#9cbaff',VIOLET,GOLD]))
FONT='Microsoft YaHei UI'

def rounded(c,x,y,w,h,r=12,**kw):
    return c.create_polygon(x+r,y,x+w-r,y,x+w,y,x+w,y+r,x+w,y+h-r,x+w,y+h,x+w-r,y+h,x+r,y+h,x,y+h,x,y+h-r,x,y+r,x,y,smooth=True,**kw)

class App(UpdateUI,TypeUI,ActivityUI,CompactUI,DesktopShell,Core):
    def __init__(self):
        self.hover=None; self.hits=[]; self.scroll=0; self.filter_index=0
        self.show_settings=False; self.toast_text=''; self.toast_job=None
        self.animation=None; self.panel_visible=False; self.pulse_phase=0
        self.dialog=None; self.active_only=False
        self.closing=False
        self.draw_job=None;self.button_visuals={};self.rows_cache=None;self.save_error=False
        self.draw_count=0;self.search_value=''
        self.undo_record=None;self.font_cache={};self.glyph_cache={};self.fit_cache=OrderedDict()
        self.focus=None;self.focus_job=None;self.focus_clock_item=None;self.last_focus_tick=0;self.focus_checkpoint=0;self.focus_restored=False
        super().__init__()
        # Custom chrome keeps explicit close, collapse and keyboard exits.
        self.root.overrideredirect(True)
        self.root.title('QuestDock '+DISPLAY_VERSION)
        self.root.configure(bg=INK)
        self.root.bind('<Escape>',lambda e:self.collapse())
        self.root.bind('<Control-n>',lambda e:self.edit())
        self.root.bind('<Control-f>',self.focus_search)
        self.root.bind('<Control-z>',self.undo_shortcut)
        for key,direction in [('Next',1),('Prior',-1),('Home','home'),('End','end')]:
            self.root.bind('<'+key+'>',lambda e,d=direction:self.keyboard_scroll(e,d))
        self.root.protocol('WM_DELETE_WINDOW',self.quit)
        self.root.bind_all('<Control-q>',lambda e:self.quit())
        self.root.bind_all('<Alt-F4>',lambda e:self.quit())
        self.root.attributes('-topmost',self.settings.get('pinned',True))
        self.setup_style()
        self.configure_desktop()
        if self.data.get('focus_session'):
            try:self.focus=FocusTimer.restore(self.data['focus_session'])
            except (KeyError,TypeError,ValueError):self.data.pop('focus_session',None)
            self.render()
        self.focus_restored=True
        self.start_update_service()
        # Idle desktop: no perpetual animation timer.

    def save(self):
        if self.focus:self.data['focus_session']=self.focus.snapshot()
        elif self.focus_restored:self.data.pop('focus_session',None)
        try:
            super().save();self.save_error=False
        except OSError:
            self.save_error=True
            try:
                from questdock.app import DATA
                DATA.with_name('save-error.log').write_text(traceback.format_exc(),encoding='utf-8')
            except OSError:pass
            if hasattr(self,'canvas'):
                self.toast('保存失败：进度暂留内存，请检查磁盘后点击重试。')

    def request_draw(self):
        if not self.closing and self.draw_job is None:
            self.draw_job=self.root.after(16,self.flush_draw)

    def flush_draw(self):
        self.draw_job=None
        if not self.closing:self.draw()

    def focus_search(self,e=None):
        self.tab='任务';self.show_settings=False;self.draw()
        self.search.focus_set();self.search.selection_range(0,'end')
        return 'break'

    def search_changed(self,*args):
        self.search_value=self.search_var.get().strip().casefold()
        self.rows_cache=None;self.scroll=0;self.request_draw()

    def toggle_active(self):
        self.active_only=not self.active_only
        self.settings['active_only']=self.active_only
        self.rows_cache=None;self.scroll=0;self.save();self.draw()

    def get_rows(self):
        key=(self.tab,self.kind,self.active_only,self.search_value,self.data['date'])
        if self.rows_cache is not None and self.rows_cache[0]==key:return self.rows_cache[1]
        if self.tab=='任务':
            rows=[t for t in self.data['tasks'] if (self.kind=='全部' or t['kind']==self.kind or (self.kind=='今日' and t.get('planned_date')==self.data['date'])) and (not self.active_only or not t['claimed']) and (not self.search_value or self.search_value in (t['title']+' '+t['desc']).casefold())]
            rows.sort(key=lambda t:(t['claimed'],not t.get('tracked',False)))
        elif self.tab=='商店':rows=list(self.data['shop'])
        elif self.tab=='背包':rows=list(reversed(self.data['bag']))
        else:rows=list(reversed(self.data['history']))
        self.rows_cache=(key,rows);return rows

    def toggle_today(self,t):
        self.reset_day()
        removing=t.get('planned_date')==self.data['date']
        t.update(planned_date=None if removing else self.data['date'],planned_source='manual',today_excluded=self.data['date'] if removing else None)
        self.commit()

    def start_focus(self,t,minutes=25):
        if self.focus:
            self.toast('已有专注计时，请先暂停或结束当前这一段。');return
        self.focus=FocusTimer(t['id'],t['title'],minutes*60)
        self.last_focus_tick=time.monotonic();self.focus_checkpoint=self.last_focus_tick
        self.save();self.render();self.schedule_focus()

    def schedule_focus(self):
        if self.focus and self.focus.running and self.focus_job is None:
            self.focus_job=self.root.after(1000,self.focus_tick)

    def focus_tick(self):
        self.focus_job=None
        if not self.focus or not self.focus.running:return
        now=time.monotonic()
        # A long scheduling gap (sleep or a blocked UI) is not focused work.
        if now-self.last_focus_tick>15:
            self.focus.left=max(0,self.focus.left-(self.last_focus_tick-self.focus.anchor))
            self.focus.running=False;self.save();self.render();self.toast('检测到计时中断，已暂停专注，可手动继续。');return
        self.last_focus_tick=now
        if self.focus.remaining()<=0:self.finish_focus(True);return
        if self.focus_clock_item and self.canvas.type(self.focus_clock_item):
            self.canvas.itemconfigure(self.focus_clock_item,text=self.focus_time_text())
        if hasattr(self,'orb_clock_item') and self.orb.type(self.orb_clock_item):
            self.orb.itemconfigure(self.orb_clock_item,text=self.focus_time_text())
            self.refresh_orb_surface()
        if now-self.focus_checkpoint>=60:self.save();self.focus_checkpoint=now
        self.schedule_focus()

    def focus_time_text(self):
        seconds=math.ceil(self.focus.remaining()) if self.focus else 0
        return f'{seconds//60:02d}:{seconds%60:02d}'

    def toggle_focus(self):
        if not self.focus:return
        if self.focus.running:
            self.focus.pause()
            if self.focus_job:self.root.after_cancel(self.focus_job);self.focus_job=None
        else:
            self.focus.resume();self.last_focus_tick=time.monotonic();self.focus_checkpoint=self.last_focus_tick;self.schedule_focus()
        self.save();self.render()

    def finish_focus(self,completed=False):
        if not self.focus:return
        timer=self.focus
        elapsed=max(0,int(timer.total-timer.remaining()))
        if self.focus_job:self.root.after_cancel(self.focus_job);self.focus_job=None
        self.focus=None
        self.log(f"{'完成' if completed else '结束'}专注 · {timer.title} · {elapsed//60}分{elapsed%60}秒")
        self.commit();self.toast('专注完成！按实际完成情况推进任务。' if completed else '专注记录已保存')
        if completed:self.root.bell()

    def stop_focus(self):
        self.confirm('结束本次专注','记录已专注的时间；不会自动完成任务或发放代币。',self.finish_focus)

    def setup_style(self):
        s=ttk.Style(self.root); s.theme_use('clam')
        s.configure('TEntry',fieldbackground=CARD,foreground=TEXT,bordercolor=LINE,padding=9,insertcolor=TEXT)
        s.configure('TCombobox',fieldbackground=CARD,background=LINE,foreground=TEXT,arrowcolor=SECOND,bordercolor=LINE,lightcolor=LINE,darkcolor=LINE,padding=8)
        s.configure('Vertical.TScrollbar',background=LINE,troughcolor=SURFACE,bordercolor=SURFACE,lightcolor=LINE,darkcolor=LINE,arrowcolor=SECOND)
        s.layout('Vertical.TScrollbar',[('Vertical.Scrollbar.trough',{'sticky':'ns','children':[('Vertical.Scrollbar.thumb',{'expand':'1','sticky':'nswe'})]})])
        s.configure('Vertical.TScrollbar',width=6,borderwidth=0,arrowsize=0)
        s.map('TCombobox',fieldbackground=[('readonly',CARD)],foreground=[('readonly',TEXT)])
        self.root.option_add('*TCombobox*Listbox.background',CARD)
        self.root.option_add('*TCombobox*Listbox.foreground',TEXT)
        self.root.option_add('*TCombobox*Listbox.selectBackground','#383457')




        # Retained as a single visual update; no background scheduling.





    def quit(self):
        if self.closing:return
        self.closing=True
        if self.focus:self.focus.pause()
        self.remember_panel()
        try:
            self.save()
        except Exception:
            # Updates are saved on each action. A final save failure must not
            # trap the user in an always-on-top window.
            try:
                from questdock.app import DATA
                DATA.with_name('exit-error.log').write_text(traceback.format_exc(),encoding='utf-8')
            except Exception:pass
        finally:
            try:
                grab=self.root.grab_current()
                if grab:grab.grab_release()
                for job in self.root.tk.splitlist(self.root.tk.call('after','info')):
                    self.root.after_cancel(job)
            except tk.TclError:pass
            finally:self.root.destroy()


    def render(self):
        self.rows_cache=None;self.summary_cache=None
        if not hasattr(self,'canvas'):
            self.canvas=tk.Canvas(self.root,bg=INK,highlightthickness=0)
            self.canvas.pack(fill='both',expand=True)
            self.canvas.bind('<Configure>',self.canvas_configured)
            self.canvas.bind('<Motion>',self.motion)
            self.canvas.bind('<Leave>',lambda e:self.clear_hover())
            self.canvas.bind('<ButtonPress-1>',self.press)
            self.canvas.bind('<B1-Motion>',self.drag)
            self.canvas.bind('<ButtonRelease-1>',self.release)
            self.root.bind('<MouseWheel>',self.wheel)
            self.search_var=tk.StringVar()
            self.search=tk.Entry(self.canvas,textvariable=self.search_var,bg=SURFACE,fg=TEXT,insertbackground=VIOLET,relief='flat',font=(FONT,9),highlightthickness=1,highlightbackground=LINE,highlightcolor=VIOLET)
            self.search_hint=tk.Label(self.canvas,text='搜索任务或描述…  Ctrl+F',bg=SURFACE,fg=DIM,font=(FONT,9),anchor='w',cursor='xterm')
            self.search_hint.bind('<Button-1>',self.focus_search)
            self.search.bind('<FocusIn>',lambda e:self.request_draw())
            self.search.bind('<FocusOut>',lambda e:self.request_draw())
            self.search_var.trace_add('write',self.search_changed)
            self.active_only=self.settings.get('active_only',False)
        self.paint_ball();self.draw()

    def commit(self):
        self.save();self.rows_cache=None;self.summary_cache=None
        self.paint_ball();self.request_draw()

    def text(self,x,y,value,size=10,color=TEXT,weight='normal',anchor='nw',width=None):
        kw=dict(text=value,fill=color,font=(FONT,size,weight),anchor=anchor)
        if width:kw['width']=width
        return self.canvas.create_text(x,y,**kw)

    def fit_text(self,value,width,size=10,weight='normal'):
        value=value.replace('\n',' ')
        key=(size,weight)
        cache_key=(value,width,size,weight)
        if cache_key in self.fit_cache:
            self.fit_cache.move_to_end(cache_key);return self.fit_cache[cache_key]
        if key not in self.font_cache:self.font_cache[key]=tkfont.Font(root=self.root,family=FONT,size=size,weight=weight)
        font=self.font_cache[key]
        glyphs=self.glyph_cache.setdefault(key,{})
        for char in set(value+'…'):
            if char not in glyphs:glyphs[char]=font.measure(char)
        if sum(glyphs[char] for char in value)<=width:result=value
        else:
            used=glyphs['…'];count=0
            for char in value:
                if used+glyphs[char]>width:break
                used+=glyphs[char];count+=1
            result=value[:count]+'…'
            # Verify only the clipped result; ordinary scrolling uses cached
            # glyph widths and avoids repeated native font-measurement calls.
            while count and font.measure(result)>width:
                count-=1;result=value[:count]+'…'
        self.fit_cache[cache_key]=result
        if len(self.fit_cache)>1024:self.fit_cache.popitem(last=False)
        return result

    def rect(self,x,y,w,h,fill=CARD,outline='',r=12):
        return rounded(self.canvas,x,y,w,h,r,fill=fill,outline=outline)

    def hit(self,key,x,y,w,h,fn):self.hits.append((key,x,y,x+w,y+h,fn))

    def button(self,x,y,w,h,label,fn,key=None,primary=False,quiet=False,color=None):
        key=key or label
        hovered=self.hover==key
        bg=('#bfb2ff' if hovered else VIOLET) if primary else ('#30364b' if hovered else ('#1b2030' if not quiet else INK))
        shape=self.rect(x,y,w,h,bg,r=8)
        base=VIOLET if primary else ('#1b2030' if not quiet else INK)
        over='#bfb2ff' if primary else '#30364b'
        self.button_visuals[key]=(shape,base,over)
        self.text(x+w/2,y+h/2,label,10,color or (INK if primary else SECOND),weight='bold' if primary else 'normal',anchor='center')
        self.hit(key,x,y,w,h,fn)

    def motion(self,e):
        hit=next((h for h in reversed(self.hits) if h[1]<=e.x<=h[3] and h[2]<=e.y<=h[4]),None)
        key=hit[0] if hit else None
        self.canvas.configure(cursor='hand2' if hit else 'arrow')
        if key!=self.hover:self.update_hover(key)

    def update_hover(self,key):
        previous=self.button_visuals.get(self.hover)
        if previous:self.canvas.itemconfigure(previous[0],fill=previous[1])
        self.hover=key
        current=self.button_visuals.get(key)
        if current:self.canvas.itemconfigure(current[0],fill=current[2])

    def clear_hover(self):
        self.update_hover(None)

    def press(self,e):
        self.pressed=next((h for h in reversed(self.hits) if h[1]<=e.x<=h[3] and h[2]<=e.y<=h[4]),None)
        self.panel_drag=(e.x_root,e.y_root,self.root.winfo_x(),self.root.winfo_y()) if e.y<40 and not self.pressed and not self.settings.get('position_locked',False) else None
        if self.pressed and self.pressed[0]=='opacity':self.slide_opacity(e.x)
        if self.pressed and self.pressed[0]=='scrollbar':self.drag_scroll(e.y)

    def drag(self,e):
        if getattr(self,'pressed',None) and self.pressed[0]=='resize':
            if not self.settings.get('position_locked',False):self.root.geometry(f'{max(360,e.x)}x{max(460,e.y)}')
            return
        if getattr(self,'pressed',None) and self.pressed[0]=='opacity':self.slide_opacity(e.x);return
        if getattr(self,'pressed',None) and self.pressed[0]=='scrollbar':self.drag_scroll(e.y);return
        if getattr(self,'panel_drag',None):
            sx,sy,x,y=self.panel_drag
            self.root.geometry(f'+{max(0,min(self.root.winfo_screenwidth()-100,x+e.x_root-sx))}+{max(0,min(self.root.winfo_screenheight()-70,y+e.y_root-sy))}')

    def release(self,e):
        h=getattr(self,'pressed',None);self.pressed=None;self.panel_drag=None
        if h and h[0]=='opacity':self.save();return
        if h and h[0]=='scrollbar':return
        if h and h[1]<=e.x<=h[3] and h[2]<=e.y<=h[4]:h[5]()

    def wheel(self,e):
        if self.show_settings:return
        # Only scroll the mission viewport, never an editor or the header.
        if e.widget.winfo_toplevel()!=self.root:return
        if self.root.winfo_pointery()-self.canvas.winfo_rooty()<self.content_top:return
        self.scroll=max(0,min(self.max_scroll,self.scroll-e.delta/120*52));self.request_draw()

    def keyboard_scroll(self,e,direction):
        if e.widget not in (self.root,self.canvas) or self.show_settings:return
        if direction=='home':self.scroll=0
        elif direction=='end':self.scroll=self.max_scroll
        else:self.scroll=max(0,min(self.max_scroll,self.scroll+direction*(self.content_bottom-self.content_top-16)))
        self.request_draw();return 'break'

    def drag_scroll(self,y):
        self.scroll=max(0,min(1,(y-self.content_top)/(self.content_bottom-self.content_top)))*self.max_scroll
        self.request_draw()

    def switch(self,n):
        self.tab=n;self.scroll=0;self.show_settings=False;self.draw()

    def filter(self,n):
        self.kind=n;self.scroll=0;self.draw()

    def pin_task(self,t):
        t['tracked']=not t.get('tracked',False);self.rows_cache=None;self.save();self.draw()






    def toggle_settings(self):self.show_settings=not self.show_settings;self.draw()



    def toggle_pin(self):
        value=not bool(self.root.attributes('-topmost'));self.root.attributes('-topmost',value)
        self.settings['pinned']=value;self.save();self.draw()

    def toggle_motion(self):
        self.settings['reduce_motion']=not self.settings.get('reduce_motion',False);self.save();self.draw()

    def toast(self,text,undo=None):
        if self.toast_job:self.root.after_cancel(self.toast_job)
        self.undo_record=undo
        self.toast_text=text;self.draw();self.toast_job=self.root.after(10000 if undo else 3200,self.clear_toast)

    def clear_toast(self):self.toast_text='';self.undo_record=None;self.toast_job=None;self.draw()

    def undo_shortcut(self,e):
        if e.widget not in (self.root,self.canvas):return
        self.undo_progress();return 'break'

    def undo_progress(self):
        record=self.undo_record
        if not record:return
        self.reset_day()
        t=next((t for t in self.data['tasks'] if t['id']==record['id']),None)
        if t is None or (t['claimed'] and t['target']==1) or t['progress']!=record['after'] or t['target']!=record['target'] or self.data['date']!=record['date']:
            self.toast('任务状态已变化，本次操作不能撤销。');return
        t['progress']=record['before']
        if t['target']>1:t['claimed']=t['progress']>=t['target']
        self.undo_record=None;self.commit();self.toast('已撤销进度；已发代币保留，重复进度不再发奖' if t['target']>1 else '已撤销刚才的进度调整')

    def claim_all(self):
        self.reset_day()
        ready=[t for t in self.data['tasks'] if not t['claimed'] and t['progress']>=t['target']]
        if not ready:self.toast('目前没有可领取的奖励');return
        ids={t['id'] for t in ready};date=self.data['date']
        def action():
            self.reset_day()
            # A confirmation left open across midnight must not claim a new day.
            if self.data['date']!=date:self.toast('日期已变化，请重新确认领取');return
            pending=[t for t in self.data['tasks'] if t['id'] in ids and not t['claimed'] and t['progress']>=t['target']]
            total=0
            for t in pending:
                if t['target']>1:
                    count,amount=pay_steps(self.data,t)
                else:
                    amount=0 if t.get('rewarded_steps',0)>=t['target'] else t['reward']
                    t['rewarded_steps']=t['target'];self.data['coins']+=amount;self.data['earned']+=amount
                total+=amount;t['claimed']=True;self.log(f"完成 {t['title']} +{amount} 代币")
            self.undo_record=None
            self.commit();self.toast(f'已领取 {len(pending)} 项奖励 · +{total} 代币')
        self.confirm('领取全部已完成任务奖励',f"共 {len(ready)} 项任务，合计 {sum(unpaid_steps(t)*t['reward'] if t['target']>1 else t['reward'] for t in ready)} 代币。包含所有分类，不受当前搜索与筛选限制。",action)

    def claim(self,t):
        self.reset_day()
        if t['claimed'] or t['progress']<t['target']:return
        if t['target']>1:
            count,amount=pay_steps(self.data,t);self.log(f"完成 {t['title']} +{amount} 代币");self.commit();self.toast(f'已结算 +{amount} 代币')
        else:
            before=self.data['coins'];super().claim(t);self.toast(f"✓  任务完成    + {self.data['coins']-before} 代币")

    def advance(self,t,n):
        self.reset_day()
        if t['claimed']:return
        before=t['progress'];after=max(0,min(t['target'],before+n))
        if before==after:return
        t['progress']=after;amount=0
        if t['target']>1:
            if after>before:
                count,amount=pay_steps(self.data,t)
                if count:self.log(f"推进 {t['title']} · {after}/{t['target']} +{amount} 代币")
            else:t['claimed']=after>=t['target']
        self.commit()
        record=dict(id=t['id'],before=before,after=after,target=t['target'],date=self.data['date'])
        self.toast(f'进度 {after}/{t["target"]} · +{amount} 代币' if t['target']>1 else ('目标已达成，可领取奖励' if after==t['target'] else f'进度已更新 · {after}/{t["target"]}'),undo=record)

    def modal(self,title,subtitle='',height=320):
        if self.dialog and self.dialog.winfo_exists():self.dialog.lift();return None
        d=tk.Toplevel(self.root);self.dialog=d;d.title(title);d.overrideredirect(True);d.configure(bg=LINE)
        d.attributes('-topmost',True);d.transient(self.root)
        x=max(0,min(self.root.winfo_x()+30,self.root.winfo_screenwidth()-440));y=max(0,min(self.root.winfo_y()+100,self.root.winfo_screenheight()-height-40))
        height=min(height,self.root.winfo_screenheight()-80)
        d.geometry(f'440x{height}+{x}+{y}');d.minsize(380,240)
        shell=tk.Frame(d,bg=SURFACE,padx=20,pady=16);shell.pack(fill='both',expand=True,padx=1,pady=1)
        header=tk.Frame(shell,bg=SURFACE);header.pack(fill='x')
        tk.Label(header,text=title,font=(FONT,16,'bold'),bg=SURFACE,fg=TEXT).pack(side='left')
        self.form_button(header,'×',d.destroy,False).pack(side='right')
        def drag_start(e):d.drag_origin=(e.x_root,e.y_root,d.winfo_x(),d.winfo_y())
        def drag_move(e):
            sx,sy,x,y=d.drag_origin;d.geometry(f'+{max(0,x+e.x_root-sx)}+{max(0,y+e.y_root-sy)}')
        for handle in [header]+[child for child in header.winfo_children() if isinstance(child,tk.Label)]:
            handle.bind('<ButtonPress-1>',drag_start);handle.bind('<B1-Motion>',drag_move)
        if subtitle:tk.Label(shell,text=subtitle,font=(FONT,9),fg=SECOND,bg=SURFACE,wraplength=380,justify='left').pack(anchor='w',pady=(10,12))
        d.action_bar=tk.Frame(shell,bg=SURFACE)
        d.action_bar.pack(side='bottom',fill='x',pady=(10,0))
        area=tk.Frame(shell,bg=SURFACE);area.pack(fill='both',expand=True)
        canvas=tk.Canvas(area,bg=SURFACE,highlightthickness=0)
        scrollbar=SlimScrollbar(area,command=canvas.yview);scrollbar.pack(side='right',fill='y')
        canvas.pack(side='left',fill='both',expand=True);canvas.configure(yscrollcommand=scrollbar.set)
        body=tk.Frame(canvas,bg=SURFACE,padx=2,pady=2)
        window=canvas.create_window((0,0),window=body,anchor='nw')
        body.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>',lambda e:canvas.itemconfigure(window,width=e.width))
        def wheel(e):
            if not isinstance(e.widget,(tk.Text,ttk.Combobox)) and body.winfo_reqheight()>canvas.winfo_height():
                canvas.yview_scroll(-int(e.delta/120),'units');return 'break'
        d.bind('<MouseWheel>',wheel)
        def reveal_focus(e):
            widget=e.widget
            if widget.winfo_class() not in ('TEntry','TCombobox','Text','Button'):return
            parent=widget
            while parent is not None and parent!=body:parent=getattr(parent,'master',None)
            if parent is None:return
            y=widget.winfo_rooty()-body.winfo_rooty();top=canvas.canvasy(0)
            total=max(1,body.winfo_reqheight());visible=canvas.winfo_height()
            if y<top:canvas.yview_moveto(max(0,y-8)/total)
            elif y+widget.winfo_height()>top+visible:
                canvas.yview_moveto(max(0,y+widget.winfo_height()-visible+8)/total)
        d.bind('<FocusIn>',reveal_focus)
        # Do not capture all app input: the orb and emergency exit stay usable.
        d.bind('<Escape>',lambda e:(d.destroy(),'break')[-1])
        d.protocol('WM_DELETE_WINDOW',d.destroy)
        d.lift();d.focus_set();return d,body

    def form_button(self,p,label,fn,primary=True):
        return tk.Button(p,text=label,command=fn,font=(FONT,10,'bold'),bg=VIOLET if primary else CARD,fg=INK if primary else SECOND,activebackground='#c2b8ff' if primary else LINE,activeforeground=INK if primary else TEXT,relief='flat',bd=0,padx=14,pady=8,cursor='hand2')

    def confirm(self,title,desc,action):
        result=self.modal(title,desc,250)
        if not result:return
        d,body=result
        row=d.action_bar
        def proceed():d.destroy();action()
        self.form_button(row,'确认',proceed).pack(side='right')
        self.form_button(row,'取消',d.destroy,False).pack(side='right',padx=12)

    def delete(self,t):
        def action():self.data['tasks'].remove(t);self.commit();self.toast('任务已移除')
        self.confirm('移除任务',f"移除「{t['title']}」？已经领取的代币会保留。",action)

    def edit(self,t=None):
        result=self.modal('编辑任务' if t else '开启一段新冒险','奖励修改仅影响之后获得的奖励，已领取的代币和经验保持不变。' if t else '把大目标拆成可推进的小步骤。',590)
        if not result:return
        d,body=result;fields={}
        for key,label,default in [('title','任务标题',''),('reward','奖励代币 / 次（目标为 1 时完成后领取）',20),('target','目标次数 / 阶段',1),('kind','任务类型',self.type_names()[0]),('desc','任务描述','')]:
            tk.Label(body,text=label,font=(FONT,9),bg=SURFACE,fg=SECOND).pack(anchor='w',pady=(7,4))
            value=str(t[key] if t else default)
            if key=='kind':
                widget=ttk.Combobox(body,values=self.type_names(),state='readonly',font=(FONT,10));widget.set(value)
            elif key=='desc':
                widget=tk.Text(body,height=3,bg=CARD,fg=TEXT,insertbackground=TEXT,relief='flat',font=(FONT,10),padx=10,pady=7,wrap='word');widget.insert('1.0',value)
            else:
                widget=ttk.Entry(body,font=(FONT,10));widget.insert(0,value)
            widget.pack(fill='x');fields[key]=widget
        error=tk.Label(body,text='',bg=SURFACE,fg=GOLD,font=(FONT,9));error.pack(anchor='w',pady=5)
        def submit():
            try:
                title=fields['title'].get().strip();target=int(fields['target'].get());reward=int(fields['reward'].get())
                if not title or target<1 or reward<0:raise ValueError
            except ValueError:error.configure(text='请填写标题；目标为正整数，奖励为非负整数。');return
            values=dict(title=title,kind=fields['kind'].get(),target=target,reward=reward,desc=fields['desc'].get('1.0','end').strip())
            if t:
                t.setdefault('rewarded_steps',t['target'] if t['claimed'] else 0)
                t.update(values);t['progress']=min(t['progress'],target)
                t['claimed']=t['claimed'] and t['progress']>=target
            else:self.data['tasks'].append(task(**values))
            d.destroy();self.commit();self.toast('任务已更新' if t else '新任务已加入冒险日志')
            return True
        row=d.action_bar
        self.form_button(row,'保存任务',submit).pack(side='right')
        d.bind('<Control-Return>',lambda e:submit())
        if t:
            def remove():d.destroy();self.delete(t)
            self.form_button(row,'删除任务',remove,False).pack(side='left')
            def focus():
                if submit():self.start_focus(t)
            self.form_button(row,'保存并专注',focus,False).pack(side='left',padx=6)
        fields['title'].focus_set()

    def product(self,p=None):
        result=self.modal('编辑商品与价格' if p else '添加一个小期待','编辑仅影响之后的兑换，背包中的奖励券保持不变。' if p else '奖励由你定义，代币由努力积累。',355)
        if not result:return
        d,body=result
        tk.Label(body,text='商品名称',bg=SURFACE,fg=SECOND,font=(FONT,9)).pack(anchor='w')
        name=ttk.Entry(body,font=(FONT,11));name.pack(fill='x',pady=(6,12))
        if p:name.insert(0,p['name'])
        tk.Label(body,text='兑换价格 · 代币',bg=SURFACE,fg=SECOND,font=(FONT,9)).pack(anchor='w')
        cost=ttk.Entry(body,font=(FONT,11));cost.insert(0,str(p['cost'] if p else 50));cost.pack(fill='x',pady=6)
        error=tk.Label(body,text='',bg=SURFACE,fg=GOLD,font=(FONT,9));error.pack(anchor='w')
        def submit():
            import uuid
            try:
                price=int(cost.get())
                if price<1 or not name.get().strip():raise ValueError
            except ValueError:error.configure(text='请输入商品名称和正整数价格。');return
            if p:p.update(name=name.get().strip(),cost=price)
            else:self.data['shop'].append(dict(id=uuid.uuid4().hex,name=name.get().strip(),cost=price))
            d.destroy();self.commit();self.toast('奖励已更新' if p else '新的奖励已上架')
        self.form_button(d.action_bar,'保存修改' if p else '添加到商店',submit).pack(side='right')
        d.bind('<Control-Return>',lambda e:submit())

    def remove_product(self,p):
        def action():self.data['shop'].remove(p);self.commit()
        self.confirm('下架奖励',f"下架「{p['name']}」？已兑换的奖励券仍会保留。",action)

    def buy(self,p):
        if self.data['coins']<p['cost']:self.toast(f"还差 {p['cost']-self.data['coins']} 代币，再推进一点点。");return
        def action():
            from questdock.app import today
            self.data['coins']-=p['cost'];self.data['bag'].append(dict(name=p['name'],date=today(),used=False))
            self.log(f"兑换 {p['name']} -{p['cost']} 代币");self.commit();self.toast('兑换成功，奖励券已放入背包')
        self.confirm('犒劳一下自己',f"花费 {p['cost']} 代币兑换「{p['name']}」。奖励券将保存在背包中。",action)

    def use(self,p):
        if p['used']:return
        def action():p['used']=True;self.log('使用 '+p['name']);self.commit();self.toast('奖励券已使用，享受这段属于你的时间。')
        self.confirm('享受你的奖励',f"现在使用「{p['name']}」？",action)

if __name__=='__main__':
    from questdock.launcher import main
    main()
