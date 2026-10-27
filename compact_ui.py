"""Work-sized panel: persistent native opacity slider, short chrome, virtual rows."""
import tkinter as tk
from styled_slider import OpacitySlider
from ui_icons import icon, level_progress
from version import DISPLAY_VERSION
from PIL import ImageTk

INK='#0d1019';SURFACE='#141925';CARD='#191f2e';LINE='#292f42'
TEXT='#eef0fa';SECOND='#9aa4bd';DIM='#8791a9';VIOLET='#ac9cff';MINT='#83dfc2';GOLD='#edc583'
FONT='Microsoft YaHei UI'
TYPES=['每日任务','剧情任务','科研','支线探索']
COLORS=dict(zip(TYPES,[MINT,'#9cbaff',VIOLET,GOLD]))

class CompactUI:
    def ensure_footer(self):
        if hasattr(self,'footer'):return
        self.footer=tk.Frame(self.canvas,bg=INK)
        tk.Label(self.footer,text='不透明度',bg=INK,fg=SECOND,font=(FONT,9)).pack(side='left',padx=(4,3))
        self.opacity_readout=tk.StringVar(value=f'{round(self.opacity.get())}%')
        self.lock_button=tk.Button(self.footer,text='解锁位置' if self.settings.get('position_locked') else '锁定位置',command=self.toggle_position_lock,bg=CARD,fg=TEXT,relief='flat',font=(FONT,9),cursor='hand2',padx=7,pady=5)
        self.lock_button.pack(side='right',padx=(5,2))
        tk.Label(self.footer,textvariable=self.opacity_readout,bg=INK,fg=VIOLET,font=(FONT,9),width=4).pack(side='right')
        self.opacity_slider=OpacitySlider(self.footer,self.opacity,self.set_opacity,self.save)
        self.opacity_slider.pack(side='left',fill='x',expand=True)
        self.footer.bind('<Enter>',lambda e:self.root.attributes('-alpha',max(.8,self.opacity.get()/100)))
        self.footer.bind('<Leave>',lambda e:self.root.attributes('-alpha',self.opacity.get()/100))

    def summary(self):
        if getattr(self,'summary_cache',None) is None:
            tasks=self.data['tasks'];planned=[t for t in tasks if t.get('planned_date')==self.data['date']]
            selected=planned
            self.summary_cache=(sum(t['progress']>=t['target'] for t in selected),len(selected),sum(not t['claimed'] and t['progress']>=t['target'] for t in tasks))
        return self.summary_cache

    def draw(self):
        if self.draw_job is not None:
            self.root.after_cancel(self.draw_job);self.draw_job=None
        if hasattr(self,'calendar_range_frame'):self.calendar_range_frame.place_forget()
        self.draw_count+=1
        c=self.canvas;c.delete('all');self.hits=[];self.button_visuals={}
        w=max(360,c.winfo_width());h=max(460,c.winfo_height());self.w=w;self.h=h
        self.ensure_footer();self.footer.place(x=10,y=h-47,width=w-20,height=35)
        self.lock_button.configure(text='解锁位置' if self.settings.get('position_locked') else '锁定位置')
        top=210 if self.tab=='任务' else 117
        bottom=h-(111 if self.focus else 63)
        self.content_top=top;self.content_bottom=bottom
        rows=[] if self.tab=='日历' else self.get_rows();row_height={'任务':132,'商店':116,'背包':100,'记录':78,'日历':78}[self.tab]
        self.max_scroll=max(0,len(rows)*row_height-(bottom-top)+8)
        self.scroll=max(0,min(self.scroll,self.max_scroll))
        start=int(self.scroll//row_height);end=min(len(rows),int((self.scroll+bottom-top)//row_height)+2)
        for i in range(start,end):
            y=top+i*row_height-self.scroll;item=rows[i]
            if self.tab=='任务':self.task_card(item,y,w)
            elif self.tab=='商店':self.shop_card(item,y,w,i)
            elif self.tab=='背包':self.bag_card(item,y,w,i)
            else:
                self.rect(12,y,w-24,68,SURFACE,r=9);self.text(24,y+10,item.replace('◈','代币'),9,SECOND,width=w-48)
        self.hits=[(k,x,max(y,top),xx,min(yy,bottom),fn) for k,x,y,xx,yy,fn in self.hits if y>=top and yy<=bottom]
        if not rows and self.tab!='日历':
            self.text(w/2,top+42,'◇',26,VIOLET,anchor='center')
            self.text(w/2,top+84,'暂无匹配内容',12,TEXT,anchor='center')
            self.text(w/2,top+115,'在全部任务中点“今日”，挑选今天要做的事。' if self.kind=='今日' and self.tab=='任务' else '可切换分类，或添加新的任务与奖励。',9,SECOND,anchor='center',width=w-40)
        if self.max_scroll:
            track=bottom-top-12;thumb=max(24,track*(bottom-top)/(len(rows)*row_height))
            self.rect(w-6,top+6+(track-thumb)*self.scroll/self.max_scroll,3,thumb,'#595670',r=1)
            self.hit('scrollbar',w-11,top,11,bottom-top,lambda:None)
        c.create_rectangle(0,0,w,top-5,fill=INK,outline='')
        self.text(14,12,'◇',17,VIOLET);self.text(39,15,'QUESTDOCK',10,TEXT,'bold')
        balance=self.text(w-122,24,str(self.data['coins']),10,GOLD,anchor='e')
        self.fixed_icon('coin',self.canvas.bbox(balance)[0]-11,24,14)
        self.button(w-110,9,30,28,'',self.toggle_settings,key='settings',quiet=True)
        self.fixed_icon('gear',w-95,23,18)
        self.button(w-76,9,28,28,'—',self.collapse,key='hide',quiet=True)
        self.button(w-42,9,28,28,'×',self.quit,key='quit',quiet=True)
        for i,(tab,label) in enumerate([('任务','任务'),('商店','商店'),('背包','背包'),('日历','日历'),('记录','记录')]):
            width=(w-24)/5;x=12+i*width
            self.text(x+width/2,56,label,10,TEXT if tab==self.tab else DIM,anchor='center')
            if tab==self.tab:self.rect(x+18,73,width-36,2,VIOLET,r=1)
            self.hit('nav'+tab,x,42,width,34,lambda t=tab:self.switch(t))
        if self.tab=='任务':self.mission_header(w)
        else:
            self.search.place_forget();self.search_hint.place_forget()
            self.text(14,89,{'商店':'给努力一个奖励','背包':'已兑换奖励券','记录':'领奖、兑换与专注流水','日历':self.data['date']+' · 每日完成日历'}[self.tab],10,SECOND)
            if self.tab=='商店':self.button(w-92,83,78,28,'＋ 商品',self.product,key='new-product')
        if self.tab=='日历':self.draw_calendar(w,bottom)
        c.create_rectangle(0,bottom,w,h,fill=INK,outline='')
        self.focus_clock_item=None
        if self.focus:
            self.rect(12,h-106,w-24,43,'#24233a',r=8)
            self.text(22,h-101,self.fit_text(self.focus.title,w-185,8),8,SECOND)
            self.focus_clock_item=self.text(22,h-83,self.focus_time_text(),11,GOLD,'bold')
            self.button(w-144,h-99,60,28,'暂停' if self.focus.running else '继续',self.toggle_focus,key='focus-pause')
            self.button(w-76,h-99,52,28,'结束',self.stop_focus,key='focus-stop')
        self.text(14,h-59,'保存失败 · 点击重试' if self.save_error else '1% 近透明  ·  100% 不透明',7,GOLD if self.save_error else DIM,anchor='w')
        if self.save_error:self.hit('retry-save',12,h-69,185,21,lambda:(self.save(),self.draw()))
        self.text(w-14,h-59,'Ctrl+Q 退出',7,DIM,anchor='e')
        if self.toast_text:
            y=bottom-42;self.hit('toast-shield',12,y,w-24,38,lambda:None)
            self.rect(12,y,w-24,38,'#292b46',VIOLET,9)
            self.text(24,y+19,self.fit_text(self.toast_text,w-(108 if self.undo_record else 48),9),9,TEXT,anchor='w')
            if self.undo_record:self.button(w-78,y+4,54,28,'撤销',self.undo_progress,key='undo')
        if self.show_settings:self.settings_panel(w,h)
        if not self.settings.get('position_locked',False):
            self.text(w-5,h-4,'◢',8,DIM,anchor='se')
            self.hit('resize',w-13,h-13,13,13,lambda:None)

    def fixed_icon(self,name,x,y,size):
        if not hasattr(self,'icon_images'):self.icon_images={}
        key=(name,size)
        if key not in self.icon_images:self.icon_images[key]=ImageTk.PhotoImage(icon(name,size),master=self.root)
        return self.canvas.create_image(x,y,image=self.icon_images[key])

    def mission_header(self,w):
        done,total,ready=self.summary()
        level,xp,required=level_progress(self.data['earned'])
        # Two identical columns for progress; actions have their own column.
        bar_x=62;bar_width=w-256;value_x=w-122
        for y,label,value,ratio in [
            (91,'今日',f'{done}/{total}',done/max(1,total)),
            (119,f'Lv.{level}',f'{xp}/{required} XP',xp/required),
        ]:
            self.text(14,y,label,8,SECOND,anchor='w')
            self.rect(bar_x,y-2,bar_width,4,LINE,r=2)
            if ratio:self.rect(bar_x,y-2,bar_width*ratio,4,VIOLET,r=2)
            self.text(value_x,y,value,8,SECOND,anchor='e')
        self.fixed_icon('info',w-110,119,12)
        self.hit('level-info',12,108,w-112,22,self.explain_level)
        self.button(w-96,79,82,26,'＋ 新任务',self.edit,key='new-task',primary=True)
        if ready:self.button(w-96,109,82,24,f'领取 {ready} 项',self.claim_all,key='claim-all',color=GOLD)
        if not self.show_settings:
            self.search.place(x=14,y=140,width=w-122,height=27)
            if not self.search_var.get() and self.root.focus_get()!=self.search:
                self.search_hint.place(x=21,y=144,width=w-140,height=19);self.search_hint.lift()
            else:self.search_hint.place_forget()
        else:self.search.place_forget();self.search_hint.place_forget()
        self.button(w-100,140,86,27,'隐藏完成' if not self.active_only else '✓ 隐藏完成',self.toggle_active,key='active-filter',color=MINT if self.active_only else SECOND)
        self.button(14,176,56,26,'今日',lambda:self.filter('今日'),key='filter今日',color=VIOLET if self.kind=='今日' else DIM)
        self.button(76,176,56,26,'全部',lambda:self.filter('全部'),key='filter全部',color=VIOLET if self.kind=='全部' else DIM)
        self.button(138,176,w-152,26,self.fit_text(self.kind if self.kind not in ('今日','全部') else '选择任务类型 ▾',w-174,9),self.type_filter_menu,key='type-filter',color=VIOLET if self.kind not in ('今日','全部') else DIM)

    def explain_level(self):
        level,xp,required=level_progress(self.data['earned'])
        result=self.modal('等级与经验',f'当前 Lv.{level} · {xp}/{required} XP，距离下一级还需 {required-xp} XP。',300)
        if not result:return
        dialog,body=result
        tk.Label(body,text='每次获得任务奖励，1 代币 = 1 XP。\n每累计 200 XP 升一级。\n兑换商品只扣代币，不扣经验，也不会降级。\n专注计时本身不增加经验。',bg=SURFACE,fg=SECOND,font=(FONT,10),justify='left',wraplength=360).pack(anchor='w',pady=10)
        self.form_button(dialog.action_bar,'知道了',dialog.destroy).pack(side='right')

    def type_filter_menu(self):
        if hasattr(self,'type_menu'):self.type_menu.destroy()
        menu=tk.Menu(self.root,tearoff=False,bg=SURFACE,fg=TEXT,activebackground=LINE);self.type_menu=menu
        for name in self.type_names():menu.add_command(label=name,command=lambda n=name:self.filter(n))
        try:menu.tk_popup(self.canvas.winfo_rootx()+138,self.canvas.winfo_rooty()+202)
        finally:menu.grab_release()

    def task_card(self,t,y,w):
        key=t['id'];color=COLORS.get(t['kind'],VIOLET);complete=t['claimed']
        self.rect(12,y,w-24,123,CARD,LINE,10)
        self.text(24,y+9,t['kind']+(' · 已追踪' if t.get('tracked') else ''),8,color)
        if complete:self.text(w-24,y+9,'已结算',8,MINT,anchor='ne')
        else:
            label=self.text(w-24,y+9,str(t['reward'])+('/次' if t['target']>1 else ''),8,GOLD,anchor='ne')
            self.fixed_icon('coin',self.canvas.bbox(label)[0]-10,y+16,14)
        self.text(24,y+28,self.fit_text(t['title'],w-48,11,'bold'),11,SECOND if complete else TEXT,'bold')
        self.text(24,y+51,self.fit_text(t['desc'],w-48,8),8,DIM)
        self.rect(24,y+76,w-116,3,LINE,r=1)
        ratio=min(1,t['progress']/max(1,t['target']))
        if ratio:self.rect(24,y+76,(w-116)*ratio,3,color,r=1)
        self.text(w-24,y+76,f'{t["progress"]}/{t["target"]}',8,SECOND,anchor='e')
        if complete:
            self.text(24,y+100,'✓ 奖励已结算',9,MINT)
            self.button(w-76,y+90,52,26,'移除',lambda:self.delete(t),key='delete'+key)
        else:
            planned=t.get('planned_date')==self.data['date']
            self.button(22,y+90,48,26,'✓ 今日' if planned else '＋ 今日',lambda:self.toggle_today(t),key='today'+key,color=MINT if planned else DIM)
            self.button(76,y+90,42,26,'追踪',lambda:self.pin_task(t),key='track'+key,color=VIOLET if t.get('tracked') else DIM)
            self.button(124,y+90,42,26,'详情',lambda:self.edit(t),key='edit'+key)
            self.button(w-121,y+90,27,26,'−',lambda:self.advance(t,-1),key='minus'+key)
            self.button(w-88,y+90,64,26,'领奖' if ratio>=1 else '＋ 进度',lambda:self.claim(t) if ratio>=1 else self.advance(t,1),key=('claim' if ratio>=1 else 'plus')+key,primary=ratio>=1)

    def shop_card(self,p,y,w,i):
        self.rect(12,y,w-24,106,CARD,LINE,10)
        self.text(24,y+13,self.fit_text(p['name'],w-48,11,'bold'),11,TEXT,'bold')
        self.fixed_icon('coin',31,y+47,14)
        self.text(44,y+39,f'{p["cost"]} 代币',10,GOLD)
        self.button(22,y+68,50,26,'编辑',lambda:self.product(p),key='product-edit'+p['id'])
        self.button(78,y+68,50,26,'下架',lambda:self.remove_product(p),key='remove'+p['id'])
        self.button(w-104,y+68,80,26,'兑换奖励',lambda:self.buy(p),key='buy'+p['id'],primary=self.data['coins']>=p['cost'])

    def bag_card(self,p,y,w,i):
        self.rect(12,y,w-24,90,CARD,LINE,10)
        self.text(24,y+12,self.fit_text(p['name'],w-48,11,'bold'),11,TEXT,'bold')
        self.text(24,y+53,p['date']+' · '+('已用' if p['used'] else '待使用'),8,DIM)
        if not p['used']:self.button(w-104,y+48,80,28,'使用奖励',lambda:self.use(p),key='use'+str(i),primary=True)

    def settings_panel(self,w,h):
        self.hits=[];self.search.place_forget();self.search_hint.place_forget()
        self.rect(10,79,w-20,min(310,h-149),SURFACE,LINE,12)
        self.text(24,94,'设置 · '+DISPLAY_VERSION,13,TEXT,'bold')
        self.button(w-58,89,30,28,'×',self.toggle_settings,key='close-settings')
        options=[('位置锁定',self.settings.get('position_locked',False),self.toggle_position_lock,'lock'),('贴边自动收起',self.settings.get('edge_hide',True),self.toggle_edge_hide,'edge'),('任务面板置顶',bool(self.root.attributes('-topmost')),self.toggle_pin,'pin')]
        for i,(label,enabled,action,key) in enumerate(options):
            y=139+i*45;self.text(24,y,label,10,SECOND)
            self.button(w-102,y-5,76,28,'已开启' if enabled else '已关闭',action,key=key,color=MINT if enabled else DIM)
        self.button(24,276,w-48,30,'管理任务类型 / 自动加入今日',self.type_settings,key='manage-types')

        self.button(24,314,w-48,28,'版本与自动更新',self.update_settings,key='updates')
        self.button(24,350,w-48,26,'恢复默认显示与尺寸',self.recover_display,key='recover')
        self.button(w-42,9,28,28,'×',self.quit,key='quit-settings',quiet=True)

    def toggle_edge_hide(self):
        self.settings['edge_hide']=not self.settings.get('edge_hide',True)
        if self.settings['edge_hide']:self.schedule_hide()
        else:self.reveal_ball()
        self.save();self.request_draw()
