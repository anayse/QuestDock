"""Daily completion snapshots, independent of reward collection."""
import datetime as dt
from questdock.task_types import is_daily


def snapshot_daily(data):
    day = data['date']
    data.setdefault('activity_started', day)
    entries = data.setdefault('daily_activity', {}).setdefault(day, {})
    for task in data['tasks']:
        if not is_daily(data,task):
            continue
        if task['claimed'] or task['progress'] >= task['target']:
            entries[task['id']] = task['title']
        else:
            entries.pop(task['id'], None)


def calendar_days(today, offset=0, weeks=20):
    end = today + dt.timedelta(days=6-today.weekday(), weeks=-weeks*offset)
    start = end-dt.timedelta(days=weeks*7-1)
    return [start+dt.timedelta(days=i) for i in range(weeks*7)]


def parse_date(value):
    value=value.strip().replace('年','-').replace('月','-').replace('日','').replace('/','-')
    try:
        year,month,day=map(int,value.split('-'))
        return dt.date(year,month,day)
    except (ValueError,TypeError):
        raise ValueError('请输入有效日期，例如 2026-10-01 或 2026年10月1日') from None


def date_range(mode, today, offset=0, start=None, end=None):
    if mode=='自定义':
        first,last=parse_date(start),parse_date(end)
        if first>last:raise ValueError('开始日期不能晚于结束日期')
        return first,last
    if mode=='周':
        first=today-dt.timedelta(days=today.weekday(),weeks=offset)
        return first,first+dt.timedelta(days=6)
    index=today.year*12+today.month-1-offset
    year,month=divmod(index,12)
    import calendar
    return dt.date(year,month+1,1),dt.date(year,month+1,calendar.monthrange(year,month+1)[1])


class ActivityUI:
    def calendar_mode(self):
        mode=self.settings.get('calendar_mode','月')
        return mode if mode in ('周','月','自定义') else '月'

    def set_calendar_mode(self, mode):
        if mode=='自定义':self.edit_calendar_range();return
        self.settings['calendar_mode']=mode
        self.calendar_offset=0;self.calendar_page=0;self.calendar_selected=None
        self.save();self.draw()

    def current_calendar_range(self):
        today=dt.date.fromisoformat(self.data['date'])
        return date_range(self.calendar_mode(),today,getattr(self,'calendar_offset',0),
                          self.settings.get('calendar_start',today.isoformat()),
                          self.settings.get('calendar_end',today.isoformat()))

    def apply_calendar_range(self, start, end):
        first,last=date_range('自定义',None,start=start,end=end)
        self.settings.update(calendar_mode='自定义',calendar_start=first.isoformat(),calendar_end=last.isoformat())
        self.calendar_offset=0;self.calendar_page=0;self.calendar_selected=None
        if hasattr(self,'calendar_values'):
            self.calendar_values[0].set(first.isoformat());self.calendar_values[1].set(last.isoformat())
        self.save();self.draw()

    def edit_calendar_range(self):
        first,last=self.current_calendar_range()
        self.tab='日历';self.show_settings=False
        self.apply_calendar_range(first.isoformat(),last.isoformat())

    def ensure_calendar_fields(self):
        import tkinter as tk
        from questdock.date_picker import DatePicker
        if hasattr(self,'calendar_range_frame'):return
        frame=tk.Frame(self.canvas,bg='#0d1019');self.calendar_range_frame=frame
        first,last=self.current_calendar_range()
        self.calendar_values=[tk.StringVar(value=first.isoformat()),tk.StringVar(value=last.isoformat())]
        self.calendar_fields=[]
        def pick(index):
            if hasattr(self,'date_picker') and self.date_picker.winfo_exists():self.date_picker.destroy()
            value=self.calendar_values[index]
            self.date_picker=DatePicker(self.root,parse_date(value.get()),lambda day:value.set(day.isoformat()),anchor=self.calendar_fields[index])
        self.open_date_picker=pick
        for i,value in enumerate(self.calendar_values):
            field=tk.Button(frame,textvariable=value,command=lambda n=i:pick(n),bg='#191f2e',fg='#eef0fa',activebackground='#30364b',activeforeground='#eef0fa',relief='flat',bd=0,font=('Segoe UI',9),cursor='hand2')
            field.grid(row=0,column=i*2,sticky='nsew');self.calendar_fields.append(field)
            frame.columnconfigure(i*2,weight=1)
            if i==0:tk.Label(frame,text='至',bg='#0d1019',fg='#9aa4bd').grid(row=0,column=1,padx=3)
        def apply():
            try:self.apply_calendar_range(*(v.get() for v in self.calendar_values))
            except ValueError as exc:self.toast(str(exc))
        tk.Button(frame,text='应用',command=apply,bg='#2b2740',fg='#ac9cff',relief='flat',bd=0,font=('Microsoft YaHei UI',9),cursor='hand2').grid(row=0,column=3,padx=(6,0),ipadx=5,sticky='ns')
        frame.rowconfigure(0,weight=1)

    def move_calendar(self, delta):
        if self.calendar_mode()=='自定义':
            first,last=self.current_calendar_range()
            last_page=((last-first).days+first.weekday())//140
            self.calendar_page=max(0,min(last_page,getattr(self,'calendar_page',0)-delta))
        else:
            offset=getattr(self,'calendar_offset',0)+delta
            try:date_range(self.calendar_mode(),dt.date.fromisoformat(self.data['date']),offset)
            except (ValueError,OverflowError):return
            self.calendar_offset=offset
        self.calendar_selected=None;self.draw()

    def select_calendar(self, day):
        self.calendar_selected=day;self.draw()

    def draw_calendar(self, w, bottom):
        today=dt.date.fromisoformat(self.data['date']);mode=self.calendar_mode()
        first,last=self.current_calendar_range()
        history=self.data.get('daily_activity',{});started=self.data.get('activity_started',self.data['date'])
        for i,label in enumerate(('周','月','自定义')):
            self.button(16+i*74,119,68,26,label,lambda m=label:self.set_calendar_mode(m),key='calendar-mode'+label,color='#83dfc2' if mode==label else '#9aa4bd')
        self.button(w-90,119,32,26,'‹',lambda:self.move_calendar(1),key='calendar-prev')
        self.button(w-52,119,32,26,'›',lambda:self.move_calendar(-1),key='calendar-next')
        if mode=='自定义':
            self.ensure_calendar_fields()
            if not self.show_settings:self.calendar_range_frame.place(x=14,y=151,width=w-28,height=25)
        else:self.text(16,155,f'{first:%Y.%m.%d} — {last:%Y.%m.%d}',9,'#eef0fa')
        counts=[len(v) for k,v in history.items() if first.isoformat()<=k<=last.isoformat()]
        self.text(16,177,f'区间完成 {sum(counts)} 项  ·  活跃 {sum(n>0 for n in counts)} 天',8,'#83dfc2')
        colors=['#202839','#175642','#23885d','#39b979','#83dfb0']
        custom=mode=='自定义'
        if custom:
            start=first-dt.timedelta(days=first.weekday())
            page=getattr(self,'calendar_page',0)
            page_start=start+dt.timedelta(days=page*140)
            length=min(140,(last-page_start).days+1)
            days=[page_start+dt.timedelta(days=i) for i in range(length)]
            cell=min(17,(w-54)/20);grid_bottom=218+7*cell
            pages=((last-first).days+first.weekday())//140+1
            self.text(w-16,177,f'{page+1}/{pages} 页',8,'#9aa4bd',anchor='ne')
            for row,label in [(0,'一'),(2,'三'),(4,'五'),(6,'日')]:self.text(14,220+row*cell,label,7,'#8791a9')
        else:
            days=[first+dt.timedelta(days=i) for i in range((last-first).days+1)]
            cell=(w-32)/7
            rows=1 if mode=='周' else (first.weekday()+len(days)+6)//7
            row_height=min(34,max(18,(bottom-285)/rows))
            grid_bottom=218+rows*row_height
            for i,label in enumerate('一二三四五六日'):self.text(16+i*cell+cell/2,200,label,8,'#9aa4bd',anchor='n')
        for i,day in enumerate(days):
            if day<first or day>last:continue
            key=day.isoformat();count=len(history.get(key,{}))
            if custom:x=36+(i//7)*cell;y=218+(i%7)*cell;cw=cell-3;ch=cell-3
            else:
                index=i+first.weekday();x=16+(index%7)*cell;y=218+(index//7)*row_height;cw=cell-4;ch=row_height-3
            known=started<=key<=self.data['date']
            outline='#ac9cff' if key==getattr(self,'calendar_selected',None) else ('#65718a' if day==today else '')
            self.canvas.create_rectangle(x,y,x+cw,y+ch,fill=colors[min(4,count)] if known else '#101522',outline=outline)
            if not custom:self.text(x+cw/2,y+ch/2,str(day.day),8,'#eef0fa' if known else '#69748a',anchor='center')
            self.hit('day'+key,x,y,cw,ch,lambda d=key:self.select_calendar(d))
        y=grid_bottom+10
        for i,color in enumerate(colors):self.rect(16+i*14,y,10,10,color,r=2)
        self.text(94,y,'少 → 多 · 每日任务完成数量',7,'#8791a9')
        selected=getattr(self,'calendar_selected',None)
        visible_first=max(first,days[0]);visible_last=min(last,days[-1])
        if not selected or not visible_first.isoformat()<=selected<=visible_last.isoformat():
            selected=(today if visible_first<=today<=visible_last else visible_first).isoformat()
        entries=history.get(selected,{})
        y+=25
        label=f'{selected}  ·  {len(entries)} 项完成'
        if selected<started:label=f'{selected}  ·  尚未开始记录'
        elif selected>self.data['date']:label=f'{selected}  ·  尚未到来'
        self.text(16,y,label,10,'#eef0fa','bold')
        available=max(0,int((bottom-y-35)/21));titles=list(entries.values())
        for i,title in enumerate(titles[:available]):self.text(18,y+25+i*21,self.fit_text('✓ '+title,w-36,9),9,'#83dfc2')
        if len(titles)>available:self.text(18,bottom-12,f'另有 {len(titles)-available} 项完成',8,'#9aa4bd')
        elif not titles and y+35<bottom:self.text(18,y+25,'点击日期查看记录 · 达到目标即计入',8,'#8791a9')
