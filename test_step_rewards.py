import datetime as dt
from unittest.mock import patch
from test_desktop_shell import ShellTests
from step_rewards import unpaid_steps


class StepRewardTests(ShellTests):
    def test_each_step_pays_once_and_final_claim_cannot_pay_again(self):
        a=self.a;t=a.data['tasks'][1]
        for i in range(1,4):
            a.advance(t,1)
            self.assertEqual(a.data['coins'],i*t['reward'])
            self.assertEqual(a.data['earned'],i*t['reward'])
        self.assertTrue(t['claimed']);a.claim(t)
        self.assertEqual(a.data['coins'],90)
        a.undo_progress();self.assertEqual(t['progress'],2)
        a.advance(t,1);self.assertEqual(a.data['coins'],90)

    def test_decrement_repeat_and_restart_keep_reward_watermark(self):
        import json,app
        a=self.a;t=a.data['tasks'][1]
        a.advance(t,1);a.advance(t,-1);a.advance(t,1)
        self.assertEqual(a.data['coins'],30)
        saved=json.loads(app.DATA.read_text(encoding='utf-8'))
        self.assertEqual(saved['tasks'][1]['rewarded_steps'],1)
        self.assertEqual(unpaid_steps(saved['tasks'][1]),0)

    def test_daily_reset_allows_next_days_step_reward(self):
        a=self.a;t=a.data['tasks'][1];a.advance(t,1)
        tomorrow=(dt.date.fromisoformat(a.data['date'])+dt.timedelta(days=1)).isoformat()
        with patch('app.today',return_value=tomorrow):
            a.reset_day();a.advance(t,1)
        self.assertEqual(a.data['coins'],60);self.assertEqual(t['rewarded_steps'],1)

    def test_legacy_paid_progress_is_not_paid_again(self):
        a=self.a;t=a.data['tasks'][1]
        t.pop('rewarded_steps');t.update(progress=3,claimed=True)
        a.claim(t);self.assertEqual(a.data['coins'],0)
        self.assertEqual(unpaid_steps(t),0)

    def test_legacy_unpaid_progress_settles_once(self):
        a=self.a;t=a.data['tasks'][1]
        t.pop('rewarded_steps');t['progress']=2
        a.advance(t,1);self.assertEqual(a.data['coins'],90)
        a.claim(t);self.assertEqual(a.data['coins'],90)
