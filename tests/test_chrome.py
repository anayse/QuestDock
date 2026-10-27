from tests.test_desktop_shell import ShellTests
from questdock.ui_icons import level_progress,icon


class ChromeTests(ShellTests):
    def test_all_editor_and_confirmation_chrome_is_borderless(self):
        a=self.a;a.toggle_panel()
        for action in (a.edit,a.product,a.type_settings,a.explain_level):
            action();a.root.update()
            self.assertTrue(a.dialog.overrideredirect())
            self.assertIsNone(a.root.grab_current())
            a.dialog.destroy()
        a.confirm('测试','测试',lambda:None);a.root.update()
        self.assertTrue(a.dialog.overrideredirect())

    def test_calendar_dropdown_dismisses_and_fields_do_not_overlap(self):
        a=self.a;a.toggle_panel();a.root.geometry('360x460');a.root.update()
        a.edit_calendar_range();a.root.update()
        a.open_date_picker(0);a.root.update();picker=a.date_picker
        self.assertTrue(picker.overrideredirect())
        self.assertIsNone(a.dialog)
        a.canvas.event_generate('<ButtonPress-1>',x=10,y=10);a.root.update()
        self.assertFalse(picker.winfo_exists())

    def test_icons_keep_dimensions_and_level_tracks_earned(self):
        a=self.a;a.toggle_panel();a.root.update()
        cached=a.icon_images[('coin',14)]
        for amount in (0,9,999,12345):
            a.data['coins']=amount;a.draw()
            self.assertIs(a.icon_images[('coin',14)],cached)
            self.assertEqual(cached.width(),14)
        self.assertEqual(icon('gear',18).size,(18,18))
        self.assertEqual(level_progress(0),(1,0,200))
        self.assertEqual(level_progress(199),(1,199,200))
        self.assertEqual(level_progress(200),(2,0,200))
        self.assertEqual(level_progress(450),(3,50,200))
