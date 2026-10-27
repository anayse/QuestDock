"""Disposable visual QA with sample data, independent of user progress."""
from pathlib import Path
import sys
from questdock import app
from questdock import premium
from tests.test_fixtures import sample_data
app.DATA=Path(__file__).resolve().parents[1]/'test-output'/'premium-preview.json'
a=premium.App()
a.data=sample_data()
a.focus=None
a.settings=a.data.setdefault('settings',{})
a.data['coins']=240;a.data['earned']=340
a.data['tasks'][1]['progress']=2
a.data['tasks'][0]['tracked']=True
a.change_opacity(100)
a.toggle_panel()
a.root.overrideredirect('--framed-qa' not in sys.argv)
a.root.title('QuestDock Visual QA')
if '--review' in sys.argv:
    original_modal=a.modal
    def review_modal(*args,**kwargs):
        result=original_modal(*args,**kwargs)
        if result:result[0].overrideredirect(False)
        return result
    a.modal=review_modal
if '--calendar' in sys.argv:
    import datetime
    now=datetime.date.today()
    a.data['activity_started']=(now-datetime.timedelta(days=140)).isoformat()
    a.data['daily_activity']={(now-datetime.timedelta(days=i)).isoformat():{str(j):'演示任务 '+str(j+1) for j in range((i*7%5) if i%3 else 0)} for i in range(140)}
    a.switch('日历')
if '--picker' in sys.argv:
    def show_picker():
        a.edit_calendar_range()
        a.open_date_picker(0)
    a.root.after(400,show_picker)
if '--types' in sys.argv:a.root.after(400,a.type_settings)
if '--form' in sys.argv:a.root.after(400,a.edit)
if '--focus' in sys.argv:
    a.focus=None
    a.toggle_today(a.data['tasks'][0]);a.toggle_today(a.data['tasks'][6])
    a.filter('今日');a.start_focus(a.data['tasks'][0])
a.root.after(300000,a.quit)
a.root.mainloop()
