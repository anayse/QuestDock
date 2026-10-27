"""Monotonic countdown with paused restart semantics; independent of Tk."""
import time

class FocusTimer:
    def __init__(self,task_id,title,seconds=1500,remaining=None,running=True,clock=time.monotonic):
        self.task_id=task_id;self.title=title;self.total=seconds
        self.left=float(seconds if remaining is None else remaining)
        self.running=running;self.clock=clock;self.anchor=clock()
    def remaining(self):
        return max(0,self.left-(self.clock()-self.anchor if self.running else 0))
    def pause(self):
        self.left=self.remaining();self.running=False
    def resume(self):
        if not self.running and self.left>0:self.anchor=self.clock();self.running=True
    def snapshot(self):
        return dict(task_id=self.task_id,title=self.title,seconds=self.total,remaining=self.remaining())
    @classmethod
    def restore(cls,state,clock=time.monotonic):
        return cls(state['task_id'],state['title'],state['seconds'],state['remaining'],False,clock)
