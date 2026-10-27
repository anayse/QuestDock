import unittest
from focus_timer import FocusTimer

class FocusTimerTests(unittest.TestCase):
    def setUp(self):self.now=100.;self.clock=lambda:self.now
    def test_pause_resume_does_not_count_paused_time(self):
        t=FocusTimer('1','Study',60,clock=self.clock)
        self.now+=10;self.assertEqual(t.remaining(),50)
        t.pause();self.now+=100;self.assertEqual(t.remaining(),50)
        t.resume();self.now+=20;self.assertEqual(t.remaining(),30)
    def test_restored_timer_is_paused(self):
        t=FocusTimer('1','Study',60,clock=self.clock);self.now+=15
        snapshot=t.snapshot();self.now+=1000
        restored=FocusTimer.restore(snapshot,clock=self.clock)
        self.assertFalse(restored.running);self.assertEqual(restored.remaining(),45)
    def test_completion_clamps_to_zero(self):
        t=FocusTimer('1','Study',60,clock=self.clock);self.now+=100
        self.assertEqual(t.remaining(),0)

if __name__=='__main__':unittest.main()
