import ctypes
from types import SimpleNamespace
from unittest.mock import Mock
from tests.test_desktop_shell import ShellTests
from questdock.orb_art import artwork


class VisualControlsTests(ShellTests):
    def test_orb_has_soft_alpha_and_native_surface(self):
        alpha=artwork(84,10,False,False).getchannel('A')
        self.assertTrue(any(0<a<255 for a in alpha.tobytes()))
        self.assertEqual(alpha.getpixel((0,0)),0)
        self.assertIsNotNone(self.a.layered_orb.pixels)
        self.assertFalse(self.a.orb.winfo_ismapped())
        self.a.orb_hover=False
        self.a.opacity.set(1);self.a.set_opacity(1)
        self.assertEqual(self.a.layered_orb.last_alpha,3)
        self.a.orb_enter()
        self.assertGreaterEqual(self.a.layered_orb.last_alpha,216)

    def test_slider_drag_does_not_save_or_redraw_panel(self):
        a=self.a;a.toggle_panel();a.root.update()
        slider=a.opacity_slider;slider.commit=Mock()
        before=a.draw_count
        slider.pointer(SimpleNamespace(x=10))
        self.assertEqual(a.opacity.get(),1)
        slider.pointer(SimpleNamespace(x=slider.winfo_width()-10))
        self.assertEqual(a.opacity.get(),100)
        slider.commit.assert_not_called()
        self.assertEqual(a.draw_count,before)
        slider.event_generate('<ButtonRelease-1>');slider.commit.assert_called_once()

    def test_native_repaints_release_gdi_objects(self):
        kernel=ctypes.WinDLL('kernel32');user=ctypes.WinDLL('user32')
        kernel.GetCurrentProcess.restype=ctypes.c_void_p
        user.GetGuiResources.argtypes=[ctypes.c_void_p,ctypes.c_uint]
        process=kernel.GetCurrentProcess()
        before=user.GetGuiResources(process,0)
        for _ in range(100):self.a.refresh_orb_surface()
        self.assertLessEqual(user.GetGuiResources(process,0),before+2)
