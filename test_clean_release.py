"""Fresh installs are empty; existing saves remain usable across upgrades."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import app
from premium import App


class CleanReleaseTests(unittest.TestCase):
    def test_fresh_install_and_restart_are_empty(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            with patch.object(app,'DATA',Path(folder)/'save.json'):
                for _ in range(2):
                    a=App()
                    try:
                        a.toggle_panel();a.root.update()
                        self.assertEqual(a.data['tasks'],[])
                        self.assertEqual(a.data['coins'],0)
                        self.assertEqual(a.data['earned'],0)
                        self.assertTrue(any(h[0]=='new-task' for h in a.hits))
                    finally:a.quit()

    def test_existing_save_preserves_task_rewards_and_settings(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            path=Path(folder)/'save.json'
            data=app.initial()
            t=app.task('自定义已有任务',app.TYPES[1],'我的记录',3,25)
            t.update(progress=2,rewarded_steps=2)
            data.update(tasks=[t],coins=37,earned=50,settings={'opacity':80},history=['已有记录'])
            path.write_text(json.dumps(data),encoding='utf-8')
            with patch.object(app,'DATA',path):
                for _ in range(2):
                    a=App()
                    try:
                        self.assertEqual(len(a.data['tasks']),1)
                        for key in ('id','title','desc','progress','rewarded_steps'):
                            self.assertEqual(a.data['tasks'][0][key],t[key])
                        self.assertEqual((a.data['coins'],a.data['earned']),(37,50))
                        self.assertEqual(a.settings['opacity'],80)
                        self.assertIn('已有记录',a.data['history'])
                    finally:a.quit()
