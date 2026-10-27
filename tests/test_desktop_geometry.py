import unittest
from unittest.mock import Mock, patch

from questdock.desktop_geometry import clamp_position, dock_position, nearest_edge, work_area


class DesktopGeometryTests(unittest.TestCase):
    def test_clamps_all_sides_and_preserves_interior(self):
        area = (0, 0, 1920, 1040)
        self.assertEqual(clamp_position(-10, -20, 60, 60, area), (0, 0))
        self.assertEqual(clamp_position(2000, 1200, 60, 60, area), (1860, 980))
        self.assertEqual(clamp_position(300, 400, 60, 60, area), (300, 400))

    def test_clamp_handles_negative_work_area_and_oversized_window(self):
        area = (-1920, 40, 0, 1080)
        self.assertEqual(clamp_position(-2000, 10, 60, 60, area), (-1920, 40))
        self.assertEqual(clamp_position(20, 1100, 60, 60, area), (-60, 1020))
        self.assertEqual(clamp_position(0, 0, 3000, 2000, area), (-1920, 40))

    def test_edge_threshold_and_corner_priority(self):
        area = (0, 0, 1000, 800)
        self.assertEqual(nearest_edge(35, 300, 60, area), 'left')
        self.assertIsNone(nearest_edge(37, 300, 60, area))
        self.assertEqual(nearest_edge(904, 300, 60, area), 'right')
        self.assertEqual(nearest_edge(400, 20, 60, area), 'top')
        self.assertEqual(nearest_edge(400, 730, 60, area), 'bottom')
        self.assertEqual(nearest_edge(0, 0, 60, area), 'left')

    def test_reveal_positions_keep_ball_inside_work_area(self):
        area = (30, 20, 1030, 780)
        self.assertEqual(dock_position('left', 600, 200, 60, area), (30, 200))
        self.assertEqual(dock_position('right', 600, 200, 60, area), (970, 200))
        self.assertEqual(dock_position('top', 600, 200, 60, area), (600, 20))
        self.assertEqual(dock_position('bottom', 600, 200, 60, area), (600, 720))

    def test_hidden_positions_leave_exact_peek_and_clamp_other_axis(self):
        area = (-1000, 40, 0, 800)
        self.assertEqual(dock_position('left', -300, 0, 60, area, True, 12), (-1048, 40))
        self.assertEqual(dock_position('right', -300, 900, 60, area, True, 12), (-12, 740))
        self.assertEqual(dock_position('top', 30, 100, 60, area, True, 12), (-60, -8))
        self.assertEqual(dock_position('bottom', -1100, 100, 60, area, True, 12), (-1000, 788))

    def test_hide_reveal_round_trip_preserves_anchor(self):
        area = (0, 0, 1200, 900)
        hidden = dock_position('left', 0, 300, 60, area, True)
        self.assertEqual(dock_position('left', *hidden, 60, area), (0, 300))

    def test_invalid_area_or_edge_rejected(self):
        with self.assertRaises(ValueError):clamp_position(0, 0, 60, 60, (0, 0, 0, 0))
        with self.assertRaises(ValueError):dock_position('middle', 0, 0, 60, (0, 0, 800, 600))

    def test_work_area_uses_native_converted_result(self):
        root = Mock()
        root.winfo_screenwidth.return_value = 1280
        root.winfo_screenheight.return_value = 720
        root.winfo_id.return_value = 123
        with patch('questdock.desktop_geometry.os.name', 'nt'), patch('questdock.desktop_geometry._windows_work_area', return_value=(0, 0, 1280, 680)) as native:
            self.assertEqual(work_area(root), (0, 0, 1280, 680))
            native.assert_called_once_with(123)

    def test_work_area_api_failure_uses_tk_fallback(self):
        root = Mock()
        root.winfo_screenwidth.return_value = 1280
        root.winfo_screenheight.return_value = 720
        with patch('questdock.desktop_geometry.os.name', 'nt'), patch('questdock.desktop_geometry._windows_work_area', side_effect=OSError('unavailable')):
            self.assertEqual(work_area(root), (0, 0, 1280, 720))


if __name__ == '__main__':
    unittest.main()
