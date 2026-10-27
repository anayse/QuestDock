"""Saved task types and daily planning rules, independent of display names."""
DEFAULT_NAMES=['每日任务','剧情任务','科研','支线探索']
RENAMES={'每日委托':'每日任务','剧情作业':'剧情任务','科研主线':'科研'}


def migrate_types(data):
    if 'task_types' not in data:
        for task in data['tasks']:task['kind']=RENAMES.get(task['kind'],task['kind'])
        names=list(dict.fromkeys(DEFAULT_NAMES+[t['kind'] for t in data['tasks']]))
        data['task_types']=[dict(name=name,auto_today=name==DEFAULT_NAMES[0],reset_daily=name==DEFAULT_NAMES[0]) for name in names]
    return data['task_types']


def is_daily(data,task):
    return any(t['name']==task['kind'] and t.get('reset_daily',False) for t in migrate_types(data))


def sync_today(data):
    types={t['name']:t for t in migrate_types(data)}
    for task in data['tasks']:
        automatic=types.get(task['kind'],{}).get('auto_today',False)
        if automatic and task.get('today_excluded')!=data['date']:
            if task.get('planned_date')!=data['date']:
                task.update(planned_date=data['date'],planned_source='auto')
        elif not automatic and task.get('planned_source')=='auto':
            task.update(planned_date=None,planned_source=None)


def update_type(data,old,name,automatic):
    name=name.strip()
    if not name or len(name)>20 or name in ('全部','今日'):
        raise ValueError('类型名称须为 1–20 个字，不能使用“全部”或“今日”。')
    types=migrate_types(data)
    if any(t['name']==name and t['name']!=old for t in types):raise ValueError('已有同名类型。')
    item=next((t for t in types if t['name']==old),None) if old else None
    if old and item is None:raise ValueError('该类型已不存在，请重新打开设置。')
    if item:
        item.update(name=name,auto_today=bool(automatic))
        for task in data['tasks']:
            if task['kind']==old:task['kind']=name
    else:types.append(dict(name=name,auto_today=bool(automatic),reset_daily=False))
    sync_today(data)


class TypeUI:
    def type_names(self):return [t['name'] for t in migrate_types(self.data)]

    def type_settings(self):
        import tkinter as tk
        result=self.modal('任务类型','自动加入今日与每日重置是独立规则；改名不会改变重置规则。',450)
        if not result:return
        dialog,body=result
        for item in migrate_types(self.data):
            row=tk.Frame(body,bg='#141925');row.pack(fill='x',pady=6)
            label=item['name']+'  ·  '+('自动加入今日' if item['auto_today'] else '手动加入今日')
            if item.get('reset_daily'):label+='\n每日重置进度'
            tk.Label(row,text=label,bg='#141925',fg='#eef0fa',anchor='w',justify='left',wraplength=250).pack(side='left')
            self.form_button(row,'修改',lambda old=item['name']:(dialog.destroy(),self.edit_type(old)),False).pack(side='right')
        self.form_button(dialog.action_bar,'＋ 添加类型',lambda:(dialog.destroy(),self.edit_type())).pack(side='right')

    def edit_type(self,old=None):
        import tkinter as tk
        from tkinter import ttk
        item=next((t for t in migrate_types(self.data) if t['name']==old),{})
        result=self.modal('修改任务类型' if old else '添加任务类型','开启后，该类型的任务会自动进入今日列表。',320)
        if not result:return
        dialog,body=result
        entry=ttk.Entry(body);entry.insert(0,old or '');entry.pack(fill='x',pady=8)
        auto=tk.BooleanVar(value=item.get('auto_today',False))
        tk.Checkbutton(body,text='自动加入今日任务',variable=auto,bg='#141925',fg='#eef0fa',selectcolor='#292f42',activebackground='#141925',activeforeground='#eef0fa').pack(anchor='w',pady=8)
        error=tk.StringVar();tk.Label(body,textvariable=error,bg='#141925',fg='#edc583',wraplength=350).pack(anchor='w')
        def save():
            try:update_type(self.data,old,entry.get(),auto.get())
            except ValueError as exc:error.set(str(exc));return
            if self.kind==old:self.kind=entry.get().strip()
            dialog.destroy();self.commit();self.type_settings()
        self.form_button(dialog.action_bar,'保存类型',save).pack(side='right')
        dialog.bind('<Control-Return>',lambda e:save());entry.focus_set()
