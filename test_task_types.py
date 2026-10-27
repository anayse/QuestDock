import datetime as dt
import unittest
from unittest.mock import patch
import app
from test_fixtures import sample_data
from task_types import migrate_types,update_type,sync_today,is_daily
from test_desktop_shell import ShellTests


class TypeModelTests(unittest.TestCase):
    def test_legacy_migration_and_rename_preserve_reset(self):
        data=sample_data();task=data['tasks'][0];task['kind']='每日委托'
        migrate_types(data);self.assertEqual(task['kind'],'每日任务')
        update_type(data,'每日任务','习惯',True)
        self.assertEqual(task['kind'],'习惯');self.assertTrue(is_daily(data,task))
        self.assertEqual(task['planned_date'],data['date'])

    def test_custom_auto_today_does_not_reset_and_manual_selection_survives(self):
        data=app.initial();migrate_types(data)
        update_type(data,None,'实验',True)
        task=app.task('实验任务','实验','');data['tasks'].append(task);sync_today(data)
        self.assertEqual(task['planned_date'],data['date']);self.assertFalse(is_daily(data,task))
        update_type(data,'实验','实验',False);self.assertIsNone(task['planned_date'])
        task.update(planned_date=data['date'],planned_source='manual')
        sync_today(data);self.assertEqual(task['planned_date'],data['date'])
        with self.assertRaises(ValueError):update_type(data,None,'科研',True)


class TodayAndPickerTests(ShellTests):
    def test_today_exclusion_is_honored_until_next_day(self):
        a=self.a;t=a.data['tasks'][0]
        self.assertEqual(t['planned_date'],a.data['date'])
        a.toggle_today(t);a.save();self.assertIsNone(t['planned_date'])
        tomorrow=(dt.date.fromisoformat(a.data['date'])+dt.timedelta(days=1)).isoformat()
        with patch('app.today',return_value=tomorrow):a.reset_day()
        self.assertEqual(t['planned_date'],tomorrow)

    def test_empty_today_orb_has_no_daily_fallback(self):
        a=self.a
        for t in a.data['tasks']:
            if t.get('planned_date')==a.data['date']:a.toggle_today(t)
        a.paint_ball()
        self.assertEqual(a.orb.itemcget(a.orb_clock_item,'text'),'0/0')

    def test_popup_calendar_selects_leap_day_without_text_input(self):
        a=self.a;a.toggle_panel();a.edit_calendar_range();a.root.update()
        value=a.calendar_values[0];value.set('2024-02-01')
        a.open_date_picker(0);a.root.update();picker=a.date_picker
        self.assertTrue(picker.overrideredirect())
        self.assertIn(29,picker.day_buttons)
        picker.day_buttons[29].invoke()
        self.assertEqual(value.get(),'2024-02-29');self.assertFalse(picker.winfo_exists())

    def test_type_management_dialog(self):
        a=self.a;a.toggle_panel();a.type_settings();a.root.update()
        self.assertTrue(a.dialog.winfo_exists());a.dialog.destroy()
        a.edit_type('科研');a.root.update();self.assertTrue(a.dialog.winfo_exists())
