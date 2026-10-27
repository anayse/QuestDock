from questdock.activity import snapshot_daily
from questdock.task_types import DEFAULT_NAMES, migrate_types, sync_today, is_daily
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json, os, uuid, datetime
from pathlib import Path

BG='#101522'; PANEL='#1b2335'; FG='#edf2ff'; MUTED='#9aaac5'; GOLD='#ffd078'; ACCENT='#73e2c0'
TYPES=DEFAULT_NAMES
DATA=Path(os.getenv('APPDATA',str(Path.home())))/'QuestDock'/'save.json'
def today(): return datetime.date.today().isoformat()
def task(title,kind,desc,target=1,reward=20):
    return dict(id=uuid.uuid4().hex,title=title,kind=kind,desc=desc,target=target,reward=reward,progress=0,claimed=False,rewarded_steps=0)
def initial():
    return dict(date=today(),coins=0,earned=0,tasks=[],
        shop=[dict(id=uuid.uuid4().hex,name='游戏预算 · 10 元',cost=100),dict(id=uuid.uuid4().hex,name='休息券 · 30 分钟',cost=40),dict(id=uuid.uuid4().hex,name='自由娱乐 · 1 小时',cost=70)],bag=[],history=[])

class App:
    def __init__(self):
        self.root=tk.Tk(); self.root.title('QuestDock · 人生任务栏'); self.root.geometry('430x800+24+60'); self.root.minsize(360,420); self.root.configure(bg=BG)
        self.root.withdraw()
        self.root.attributes('-topmost',True); self.kind='全部'; self.tab='任务'; self.collapsed=False
        self.data=initial()
        if DATA.exists():
            try:
                self.data=json.loads(DATA.read_text(encoding='utf-8'))
                assert all(k in self.data for k in ['tasks','coins','shop','bag','history','date','earned'])
            except Exception:
                from questdock.notices import show_notice
                show_notice('存档读取失败','存档无法读取。为保护原数据，程序将退出。',self.root); self.root.destroy(); raise SystemExit
        migrate_types(self.data)
        self.settings=self.data.setdefault('settings',{})
        self.opacity=tk.DoubleVar(value=self.settings.get('opacity',95))
        self.create_ball()
        self.root.protocol('WM_DELETE_WINDOW',self.root.withdraw)
        self.reset_day(); self.render(); self.set_opacity(self.opacity.get()); self.root.after(30000,self.tick)
    def create_ball(self):
        self.ball=tk.Toplevel(self.root); self.ball.overrideredirect(True)
        self.ball.attributes('-topmost',True)
        self.ball.configure(bg='#ff00ff'); self.ball.attributes('-transparentcolor','#ff00ff')
        x=max(0,min(self.settings.get('ball_x',24),self.root.winfo_screenwidth()-72))
        y=max(0,min(self.settings.get('ball_y',160),self.root.winfo_screenheight()-72))
        self.ball.geometry(f'72x72+{x}+{y}')
        c=tk.Canvas(self.ball,width=72,height=72,bg='#ff00ff',highlightthickness=0,cursor='hand2'); c.pack()
        c.create_oval(4,4,68,68,fill=PANEL,outline=ACCENT,width=3)
        c.create_text(36,29,text='◈',font=('Microsoft YaHei UI',21),fill=GOLD)
        c.create_text(36,51,text='任务',font=('Microsoft YaHei UI',9),fill=FG)
        c.bind('<ButtonPress-1>',self.ball_press); c.bind('<B1-Motion>',self.ball_drag); c.bind('<ButtonRelease-1>',self.ball_release)
        self.ball_menu=tk.Menu(self.ball,tearoff=False)
        self.ball_menu.add_command(label='展开 / 隐藏任务栏',command=self.toggle_panel)
        for percent in [50,70,85,100]:
            self.ball_menu.add_command(label=f'透明度 {percent}%',command=lambda p=percent:self.change_opacity(p))
        self.ball_menu.add_separator(); self.ball_menu.add_command(label='退出 QuestDock',command=self.quit)
        c.bind('<Button-3>',lambda e:self.ball_menu.tk_popup(e.x_root,e.y_root))
    def ball_press(self,e):
        self.drag_start=(e.x_root,e.y_root,self.ball.winfo_x(),self.ball.winfo_y()); self.dragged=False
    def ball_drag(self,e):
        sx,sy,x,y=self.drag_start; dx=e.x_root-sx; dy=e.y_root-sy
        if abs(dx)+abs(dy)>5:self.dragged=True
        if self.dragged:
            x=max(0,min(x+dx,self.root.winfo_screenwidth()-72)); y=max(0,min(y+dy,self.root.winfo_screenheight()-72))
            self.ball.geometry(f'+{x}+{y}')
    def ball_release(self,e):
        if self.dragged:
            self.settings.update(ball_x=self.ball.winfo_x(),ball_y=self.ball.winfo_y()); self.save()
        else:self.toggle_panel()
    def toggle_panel(self):
        if self.root.state()!='withdrawn':self.root.withdraw();return
        self.root.update_idletasks()
        width=max(430,self.root.winfo_width()); height=min(800,self.root.winfo_screenheight()-80)
        x=self.ball.winfo_x()+80
        if x+width>self.root.winfo_screenwidth():x=self.ball.winfo_x()-width-8
        y=max(0,min(self.ball.winfo_y(),self.root.winfo_screenheight()-height-60))
        self.root.geometry(f'{width}x{height}+{max(0,x)}+{y}'); self.root.deiconify(); self.root.lift()
    def set_opacity(self,value):
        percent=max(50,min(100,float(value)))
        self.root.attributes('-alpha',percent/100); self.ball.attributes('-alpha',percent/100)
        self.settings['opacity']=percent
    def change_opacity(self,value):
        self.opacity.set(value); self.set_opacity(value); self.save()
    def quit(self):
        self.save(); self.root.destroy()
    def save(self):
        sync_today(self.data)
        snapshot_daily(self.data)
        payload=json.dumps(self.data,ensure_ascii=False,indent=2)
        if getattr(self,'_saved_payload',None)==payload:return
        DATA.parent.mkdir(parents=True,exist_ok=True)
        if DATA.exists():
            previous=DATA.read_text(encoding='utf-8')
            if previous==payload:self._saved_payload=payload;return
            try:json.loads(previous)
            except (ValueError,UnicodeError):pass
            else:
                backup_tmp=DATA.with_suffix('.bak.tmp')
                backup_tmp.write_text(previous,encoding='utf-8')
                backup_tmp.replace(DATA.with_suffix('.bak'))
        temp=DATA.with_suffix('.tmp');temp.write_text(payload,encoding='utf-8');temp.replace(DATA)
        self._saved_payload=payload
    def reset_day(self):
        snapshot_daily(self.data)
        if self.data['date']!=today():
            for t in self.data['tasks']:
                if is_daily(self.data,t): t.update(progress=0,claimed=False,rewarded_steps=0)
            self.data['date']=today(); self.save()
        sync_today(self.data)
    def tick(self):
        if self.data['date']!=today(): self.reset_day(); self.render()
        self.root.after(30000,self.tick)
    def label(self,p,text,size=11,color=FG,**kw):
        w=tk.Label(p,text=text,font=('Microsoft YaHei UI',size),bg=p['bg'],fg=color,**kw); w.pack(anchor='w',pady=3); return w
    def button(self,p,text,cmd,color=ACCENT):
        w=tk.Button(p,text=text,command=cmd,bg=PANEL,fg=color,activebackground='#303e58',activeforeground=FG,relief='flat',font=('Microsoft YaHei UI',10),cursor='hand2',padx=10,pady=6); w.pack(side='left',padx=3,pady=4); return w
    def render(self):
        for w in self.root.winfo_children():
            if not isinstance(w,tk.Toplevel):w.destroy()
        head=tk.Frame(self.root,bg=BG,padx=16,pady=10); head.pack(fill='x')
        self.label(head,'QUEST DOCK  /  人生冒险',14,ACCENT)
        self.label(head,f"Lv.{1+self.data['earned']//200}   冒险者     ◈ {self.data['coins']} 代币",13,GOLD)
        tools=tk.Frame(head,bg=BG); tools.pack(fill='x')
        self.button(tools,'收回悬浮球',self.collapse)
        self.pin=tk.BooleanVar(value=bool(self.root.attributes('-topmost')))
        tk.Checkbutton(tools,text='置顶',variable=self.pin,command=lambda:self.root.attributes('-topmost',self.pin.get()),bg=BG,fg=FG,selectcolor=PANEL).pack(side='left')
        slider=tk.Scale(tools,from_=50,to=100,orient='horizontal',length=110,label='透明度 %',showvalue=True,bg=BG,fg=FG,highlightthickness=0,command=self.set_opacity,variable=self.opacity)
        slider.pack(side='right'); slider.bind('<ButtonRelease-1>',lambda e:self.save()); slider.bind('<KeyRelease>',lambda e:self.save())
        if self.collapsed:return
        nav=tk.Frame(self.root,bg=BG);nav.pack(fill='x',padx=12)
        for name in ['任务','商店','背包','记录']:self.button(nav,name,lambda n=name:self.switch(n),GOLD if name==self.tab else MUTED)
        if self.tab=='任务':
            filters=tk.Frame(self.root,bg=BG);filters.pack(fill='x',padx=16)
            box=ttk.Combobox(filters,values=['全部']+TYPES,state='readonly',width=13);box.set(self.kind);box.pack(side='left');box.bind('<<ComboboxSelected>>',lambda e:self.filter(box.get()))
            self.button(filters,'＋ 发布任务',self.edit)
            self.label(filters,'',1)
        outer=tk.Frame(self.root,bg=BG);outer.pack(fill='both',expand=True)
        canvas=tk.Canvas(outer,bg=BG,highlightthickness=0);bar=ttk.Scrollbar(outer,command=canvas.yview);bar.pack(side='right',fill='y');canvas.pack(side='left',fill='both',expand=True);canvas.configure(yscrollcommand=bar.set)
        body=tk.Frame(canvas,bg=BG);window=canvas.create_window((0,0),window=body,anchor='nw');body.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')));canvas.bind('<Configure>',lambda e:canvas.itemconfigure(window,width=e.width))
        canvas.bind_all('<MouseWheel>',lambda e:canvas.yview_scroll(int(-e.delta/120),'units'))
        if self.tab=='任务':
            self.label(body,'  每日委托按精力选做，跨日自动重置。',10,MUTED)
            for t in self.data['tasks']:
                if self.kind!='全部' and t['kind']!=self.kind:continue
                card=self.card(body);self.label(card,t['kind']+'   /   '+('已领取' if t['claimed'] else '进行中'),9,ACCENT);self.label(card,t['title'],13,wraplength=330,justify='left');self.label(card,t['desc'],10,MUTED,wraplength=330,justify='left')
                ttk.Progressbar(card,maximum=t['target'],value=t['progress']).pack(fill='x',pady=8)
                self.label(card,f"{t['progress']} / {t['target']}                       奖励 ◈ {t['reward']}",10,GOLD)
                row=tk.Frame(card,bg=PANEL);row.pack(fill='x')
                if not t['claimed']:
                    self.button(row,'−',lambda x=t:self.advance(x,-1));self.button(row,'＋ 进度',lambda x=t:self.advance(x,1))
                    if t['progress']>=t['target']:self.button(row,'领取',lambda x=t:self.claim(x),GOLD)
                    self.button(row,'编辑',lambda x=t:self.edit(x))
                self.button(row,'删除',lambda x=t:self.delete(x),MUTED)
        elif self.tab=='商店':
            self.button(body,'＋ 新增商品',self.product)
            self.label(body,'  兑换为自我奖励券，不涉及真实付款。',10,MUTED)
            for p in self.data['shop']:
                card=self.card(body);self.label(card,p['name'],13);self.label(card,f"◈ {p['cost']} 代币",11,GOLD);self.button(card,'兑换',lambda x=p:self.buy(x));self.button(card,'下架',lambda x=p:self.remove_product(x),MUTED)
        elif self.tab=='背包':
            self.label(body,'  兑换的奖励券 · 使用后保留记录',10,MUTED)
            for p in reversed(self.data['bag']):
                card=self.card(body);self.label(card,p['name'],13);self.label(card,p['date']+' · '+('已使用' if p['used'] else '待使用'),10,MUTED)
                if not p['used']:self.button(card,'使用奖励券',lambda x=p:self.use(x))
        else:
            for line in reversed(self.data['history']):self.label(self.card(body),line,10,MUTED,wraplength=330,justify='left')
    def card(self,parent):
        f=tk.Frame(parent,bg=PANEL,padx=14,pady=10);f.pack(fill='x',padx=14,pady=6);return f
    def switch(self,n):self.tab=n;self.render()
    def filter(self,n):self.kind=n;self.render()
    def collapse(self):
        self.root.withdraw()
    def log(self,s):self.data['history'].append(datetime.datetime.now().strftime('%m-%d %H:%M')+'  '+s)
    def commit(self):self.save();self.render()
    def advance(self,t,n):self.reset_day();t['progress']=max(0,min(t['target'],t['progress']+n));self.commit()
    def claim(self,t):
        self.reset_day()
        if t['claimed'] or t['progress']<t['target']:return
        amount=0 if t.get('rewarded_steps',0)>=t['target'] else t['reward']
        t['rewarded_steps']=t['target'];t['claimed']=True;self.data['coins']+=amount;self.data['earned']+=amount;self.log(f"完成 {t['title']} +{amount} 代币");self.commit()
    def delete(self,t):
        if messagebox.askyesno('删除任务','确定删除此任务？已获得代币不受影响。',parent=self.root):self.data['tasks'].remove(t);self.commit()
    def edit(self,t=None):
        d=tk.Toplevel(self.root);d.title('编辑任务' if t else '发布任务');d.configure(bg=BG);d.geometry('400x520');d.transient(self.root);d.grab_set()
        fields={}
        for key,title,default in [('title','任务标题',''),('kind','任务类型',TYPES[0]),('reward','奖励代币',20),('target','目标进度（次数 / 阶段）',1),('desc','任务说明','')]:
            self.label(d,title)
            w=ttk.Combobox(d,values=TYPES,state='readonly') if key=='kind' else tk.Text(d,height=5,width=40) if key=='desc' else ttk.Entry(d)
            value=str(t[key] if t else default)
            if key=='kind':w.set(value)
            elif key=='desc':w.insert('1.0',value)
            else:w.insert(0,value)
            w.pack(fill='x',padx=16,pady=4);fields[key]=w
        def submit():
            try:
                title=fields['title'].get().strip();target=int(fields['target'].get());reward=int(fields['reward'].get());assert title and target>0 and reward>=0
            except Exception:messagebox.showerror('输入无效','请填写标题；目标为正整数，奖励为非负整数。',parent=d);return
            values=dict(title=title,kind=fields['kind'].get(),reward=reward,target=target,desc=fields['desc'].get('1.0','end').strip())
            if t:t.update(values);t['progress']=min(t['progress'],target)
            else:self.data['tasks'].append(task(**values))
            d.destroy();self.commit()
        self.button(d,'保存任务',submit)
    def product(self):
        name=simpledialog.askstring('新增商品','商品名称（例如：休息 30 分钟）',parent=self.root)
        if not name or not name.strip():return
        cost=simpledialog.askinteger('商品价格','需要多少代币？',minvalue=1,parent=self.root)
        if cost is not None:self.data['shop'].append(dict(id=uuid.uuid4().hex,name=name.strip(),cost=cost));self.commit()
    def remove_product(self,p):
        if messagebox.askyesno('下架商品','确定下架此商品？',parent=self.root):self.data['shop'].remove(p);self.commit()
    def buy(self,p):
        if self.data['coins']<p['cost']:messagebox.showinfo('代币不足','完成任务领取更多代币。',parent=self.root);return
        if not messagebox.askyesno('兑换商品',f"花费 {p['cost']} 代币兑换 {p['name']}？",parent=self.root):return
        self.data['coins']-=p['cost'];self.data['bag'].append(dict(name=p['name'],date=today(),used=False));self.log(f"兑换 {p['name']} -{p['cost']} ◈");self.commit()
    def use(self,p):
        if messagebox.askyesno('使用奖励','现在使用这张奖励券？',parent=self.root):p['used']=True;self.log('使用 '+p['name']);self.commit()

if __name__=='__main__':
    from questdock.launcher import main
    main()
