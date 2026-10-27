import datetime as dt
import unittest
from unittest.mock import patch
from questdock.activity import snapshot_daily, calendar_days, date_range, parse_date
from tests.test_desktop_shell import ShellTests


class DailyTests(ShellTests):
    def test_midnight_preserves_history_and_resets_only_daily(self):
        a=self.a
        daily=a.data['tasks'][0];story=a.data['tasks'][6]
        daily['progress']=daily['target'];story['progress']=1
        old=a.data['date'];a.save()
        tomorrow=(dt.date.fromisoformat(old)+dt.timedelta(days=1)).isoformat()
        with patch('questdock.app.today',return_value=tomorrow):a.reset_day()
        self.assertEqual(daily['progress'],0)
        self.assertFalse(daily['claimed'])
        self.assertEqual(story['progress'],1)
        self.assertIn(daily['id'],a.data['daily_activity'][old])
        self.assertEqual(a.data['daily_activity'][tomorrow],{})

    def test_reward_does_not_double_count_and_undo_removes_completion(self):
        a=self.a;t=a.data['tasks'][0]
        a.advance(t,1)
        self.assertEqual(len(a.data['daily_activity'][a.data['date']]),1)
        a.undo_progress()
        self.assertEqual(len(a.data['daily_activity'][a.data['date']]),0)
        a.advance(t,1);a.claim(t);a.claim(t)
        self.assertEqual(len(a.data['daily_activity'][a.data['date']]),1)

    def test_calendar_borderless_and_small_window(self):
        a=self.a;a.toggle_panel();a.root.geometry('360x460');a.root.update()
        self.assertTrue(a.root.overrideredirect())
        a.switch('日历');a.root.update()
        self.assertTrue(any(h[0].startswith('day') for h in a.hits))
        a.move_calendar(1);self.assertEqual(a.calendar_offset,1)
        a.move_calendar(-1);self.assertEqual(a.calendar_offset,0)
        self.assertTrue(any(h[0]=='quit' for h in a.hits))

    def test_calendar_modes_and_bounded_custom_pages(self):
        a=self.a;a.toggle_panel();a.root.geometry('360x460');a.root.update();a.switch('日历')
        a.set_calendar_mode('周')
        self.assertEqual(len([h for h in a.hits if h[0].startswith('day')]),7)
        a.apply_calendar_range('2024年2月29日','2024年2月29日')
        self.assertEqual(len([h for h in a.hits if h[0].startswith('day')]),1)
        a.apply_calendar_range('2020-01-01','2030-12-31')
        self.assertLessEqual(len([h for h in a.hits if h[0].startswith('day')]),140)
        a.move_calendar(-1);self.assertEqual(a.calendar_page,1)
        self.assertEqual(a.settings['calendar_start'],'2020-01-01')
        a.move_calendar(1);self.assertEqual(a.calendar_page,0)
        a.edit_calendar_range();a.root.update()
        self.assertTrue(a.calendar_range_frame.winfo_ismapped())
        self.assertIsNone(a.dialog)


class CalendarTests(unittest.TestCase):
    def test_week_month_and_leap_boundaries(self):
        self.assertEqual(date_range('周',dt.date(2025,1,1)),(dt.date(2024,12,30),dt.date(2025,1,5)))
        self.assertEqual(date_range('月',dt.date(2024,3,12),1),(dt.date(2024,2,1),dt.date(2024,2,29)))
        self.assertEqual(date_range('月',dt.date(2024,12,12),-1),(dt.date(2025,1,1),dt.date(2025,1,31)))

    def test_custom_validation_and_inclusive_single_day(self):
        self.assertEqual(parse_date('2026年2月3日'),dt.date(2026,2,3))
        self.assertEqual(date_range('自定义',None,start='2026-2-3',end='2026-2-3'),(dt.date(2026,2,3),)*2)
        for start,end in [('2026-02-30','2026-03-01'),('2026-03-01','2026-02-01'),('oops','2026-03-01')]:
            with self.assertRaises(ValueError):date_range('自定义',None,start=start,end=end)

    def test_grid_crosses_year_and_leap_day(self):
        days=calendar_days(dt.date(2024,3,1))
        self.assertEqual(len(days),140)
        self.assertEqual(days[0].weekday(),0)
        self.assertIn(dt.date(2024,2,29),days)
        self.assertEqual(calendar_days(dt.date(2024,3,1),1)[-1]+dt.timedelta(days=1),days[0])
