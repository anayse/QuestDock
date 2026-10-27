"""Repeatable renderer benchmark with isolated data, without user save access."""
import json
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
from questdock import app
from questdock.premium import App

def run():
    with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
        app.DATA=Path(folder)/'save.json'
        a=App();a.root.update()
        a.data['tasks']=[app.task(f'任务 {i}',app.TYPES[0],'性能验证') for i in range(2000)]
        a.render()
        hit=next(h for h in a.hits if h[0]=='new-task');before=a.draw_count
        start=time.perf_counter()
        for _ in range(500):
            a.motion(SimpleNamespace(x=hit[1]+2,y=hit[2]+2));a.clear_hover()
        hover_ms=(time.perf_counter()-start)*1000
        hover_draws=a.draw_count-before
        start=time.perf_counter()
        for i in range(100):a.scroll=a.max_scroll*i/99;a.draw()
        result={'tasks':2000,'pointer_transitions':1000,'pointer_total_ms':round(hover_ms,2),'pointer_full_redraws':hover_draws,'scroll_draw_average_ms':round((time.perf_counter()-start)*10,2),'canvas_items_at_end':len(a.canvas.find_all()),'periodic_idle_animation':False}
        a.quit()
    Path('test-output').mkdir(exist_ok=True)
    Path('test-output/performance.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':run()
