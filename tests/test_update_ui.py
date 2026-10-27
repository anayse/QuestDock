"""Update controls use disposable saves and never contact the network."""
from unittest.mock import Mock,patch
from tests import test_desktop_shell


class UpdateUITests(test_desktop_shell.ShellTests):
    def test_update_dialog_is_borderless(self):
        self.a.update_settings()
        self.a.root.update()
        self.assertTrue(self.a.dialog.overrideredirect())
        self.assertIsNone(self.a.root.grab_current())

    def test_automatic_update_is_opt_in(self):
        self.a.check_updates=Mock()
        self.a.automatic_update()
        self.a.check_updates.assert_not_called()
        self.a.settings['auto_update']=True
        self.a.automatic_update()
        self.a.check_updates.assert_called_once_with(silent=True)

    def test_result_delivery_and_source_mode_install(self):
        a=self.a
        a.update_busy=True
        a.update_result.put(('ready',({'version':'1.1.0'},None)))
        a.poll_update(True)
        self.assertFalse(a.update_busy)
        self.assertIn('1.1.0',a.update_status.get())
        with patch('questdock.update_ui.subprocess.Popen') as launch:
            a.install_ready_update()
            launch.assert_not_called()
        self.assertIn('源码',a.update_status.get())

    def test_missing_repository_never_starts_worker(self):
        self.a.settings['update_repository']=''
        with patch('questdock.update_ui.threading.Thread') as worker:
            self.a.check_updates()
            worker.assert_not_called()
        self.assertFalse(self.a.update_busy)
