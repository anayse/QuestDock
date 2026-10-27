"""Desktop interaction regressions with disposable saves."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import app
import json
from test_fixtures import sample_data
from premium import App


class ShellTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        app.DATA = Path(self.tmp.name) / 'save.json'
        app.DATA.write_text(json.dumps(sample_data()),encoding='utf-8')
        self.a = App()
        self.a.root.update()
        self.a.cancel_hide()

    def tearDown(self):
        self.a.quit()
        self.tmp.cleanup()

    def test_hidden_left_uses_negative_coordinates_and_reveals(self):
        a = self.a
        a.ball_anchor = (0, 180)
        a.dock_side = 'left'
        a.orb_hover = False
        a.hide_ball()
        a.root.update_idletasks()
        self.assertEqual(a.ball.winfo_x(), -40)
        self.assertEqual(a.ball_anchor, (0, 180))
        a.reveal_ball()
        a.root.update_idletasks()
        self.assertEqual(a.ball.winfo_x(), 0)

    def test_slider_entire_range_without_redraw_or_save(self):
        a = self.a
        before = a.draw_count
        a.save = Mock()
        a.orb_hover = False
        for value in (1, 50, 100):
            a.opacity.set(value)
            a.set_opacity(value)
            self.assertAlmostEqual(a.root.attributes('-alpha'), value / 100)
            self.assertAlmostEqual(a.ball.attributes('-alpha'), value / 100)
            self.assertEqual(a.opacity_readout.get(), f'{value}%')
        self.assertEqual(a.draw_count, before)
        a.save.assert_not_called()

    def test_drag_coalesced_and_last_position_flushed(self):
        a = self.a
        a.ball_press(SimpleNamespace(x_root=0, y_root=180))
        a.position_ball = Mock()
        for x in range(50, 150):
            a.ball_drag(SimpleNamespace(x_root=x, y_root=250))
        a.position_ball.assert_not_called()
        self.assertIsNotNone(a.move_job)
        a.ball_release()
        self.assertEqual(a.ball_anchor, (149, 250))
        self.assertIsNone(a.move_job)
        self.assertEqual(a.settings['ball_x'], 149)

    def test_lock_prevents_ball_move_and_panel_toggle(self):
        a = self.a
        a.settings['position_locked'] = True
        before = a.ball_anchor
        a.ball_press(SimpleNamespace(x_root=0, y_root=180))
        a.ball_drag(SimpleNamespace(x_root=200, y_root=250))
        a.ball_release()
        self.assertEqual(a.ball_anchor, before)
        self.assertEqual(a.root.state(), 'withdrawn')

    def test_panel_lock_and_recovery(self):
        a = self.a
        a.toggle_panel()
        a.root.update()
        a.toggle_position_lock()
        position = (a.settings['panel_x'], a.settings['panel_y'])
        a.root.geometry('+300+300')
        a.root.update()
        self.assertEqual((a.root.winfo_x(), a.root.winfo_y()), position)
        a.opacity.set(1)
        a.set_opacity(1)
        a.recover_display()
        a.root.update()
        self.assertFalse(a.settings['position_locked'])
        self.assertEqual(a.opacity.get(), 95)
        self.assertEqual((a.root.winfo_width(), a.root.winfo_height()), (380, 600))

    def test_small_panel_keeps_footer_and_content_separate(self):
        a = self.a
        a.toggle_panel()
        a.root.geometry('360x460')
        a.root.update()
        a.draw()
        a.root.update_idletasks()
        self.assertGreater(a.footer.winfo_y(), a.content_bottom)
        self.assertGreater(a.opacity_slider.winfo_width(), 70)
        a.opacity_slider.change(0)
        self.assertEqual(a.opacity.get(),1)
        a.opacity_slider.change(101)
        self.assertEqual(a.opacity.get(),100)


if __name__ == '__main__':
    unittest.main()
