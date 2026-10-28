"""Isolated lifecycle checks; never accesses the user's save."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from questdock import app
from questdock import premium
import json
from tests.test_fixtures import sample_data

class DesktopTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        app.DATA=Path(self.tmp.name)/'save.json'
        app.DATA.write_text(json.dumps(sample_data()),encoding='utf-8')
        self.a=premium.App();self.a.root.update()
    def tearDown(self):
        self.a.quit();self.tmp.cleanup()
    def test_exit_even_when_save_fails(self):
        a=self.a
        def fail():raise OSError('simulated write failure')
        a.save=fail
        a.quit()
        self.assertTrue(a.closing)
        self.assertFalse(a.root.tk.call('info','commands','.'))
    def test_exit_shortcut_from_open_dialog(self):
        a=self.a;a.toggle_panel();a.root.update();a.edit();a.root.update()
        self.assertIsNone(a.root.grab_current())
        a.dialog.event_generate('<Control-q>');a.root.update()
        self.assertTrue(a.closing)
    def test_menu_releases_grab_even_on_error(self):
        from unittest.mock import Mock
        a=self.a
        a.ball_menu.tk_popup=Mock(side_effect=RuntimeError('popup failure'))
        a.ball_menu.grab_release=Mock()
        with self.assertRaises(RuntimeError):a.popup_ball_menu(SimpleNamespace(x_root=0,y_root=0))
        a.ball_menu.grab_release.assert_called_once()
    def test_shell_and_render(self):
        a=self.a
        self.assertEqual(a.root.state(),'withdrawn')
        a.toggle_panel();a.root.update()
        self.assertEqual(a.root.state(),'normal')
        for tab in ['任务','商店','背包','记录']:
            a.switch(tab);a.root.update();self.assertTrue(a.canvas.find_all())
        a.toggle_settings();a.slide_opacity(250)
        self.assertGreaterEqual(a.opacity.get(),50)
        a.change_opacity(80);self.assertAlmostEqual(a.ball.attributes('-alpha'),.8)
        a.collapse();self.assertEqual(a.root.state(),'withdrawn')
    def test_task_reward_daily_and_reload(self):
        a=self.a;t=a.data['tasks'][0];a.pin_task(t)
        a.advance(t,1);a.claim(t);a.claim(t)
        self.assertEqual(a.data['coins'],20)
        a.data['date']='2000-01-01';a.reset_day()
        self.assertFalse(t['claimed']);self.assertEqual(t['progress'],0)
        self.assertTrue(t['tracked']);self.assertEqual(a.data['coins'],20)
        a.change_opacity(75)
        import json
        saved=json.loads(app.DATA.read_text(encoding='utf-8'))
        self.assertEqual(saved['settings']['opacity'],75)
        self.assertEqual(saved['coins'],20)
    def test_shop_confirmation_and_bag(self):
        a=self.a;p=a.data['shop'][0]
        a.buy(p);self.assertEqual(len(a.data['bag']),0)
        a.data['coins']=150
        a.confirm=lambda title,desc,action:action()
        a.buy(p);self.assertEqual(a.data['coins'],50)
        a.use(a.data['bag'][0]);a.use(a.data['bag'][0])
        self.assertTrue(a.data['bag'][0]['used'])
        self.assertEqual(len(a.data['history']),2)
    def test_forms_and_drag(self):
        a=self.a;a.toggle_panel();a.root.update()
        a.edit();a.root.update();self.assertTrue(a.dialog.winfo_exists());a.dialog.destroy()
        a.product();a.root.update();self.assertTrue(a.dialog.winfo_exists());a.dialog.destroy()
        a.collapse();a.ball_press(SimpleNamespace(x_root=50,y_root=200))
        a.ball_drag(SimpleNamespace(x_root=100,y_root=260));a.root.update();a.ball_release(None)
        self.assertEqual(a.root.state(),'withdrawn')

    def test_search_filter_and_focus(self):
        a=self.a;a.settings['reduce_motion']=True;a.toggle_panel();a.root.update()
        a.focus_search();a.search.focus_force();a.root.update()
        a.search_var.set('测试任务 2');a.flush_draw();a.root.update()
        self.assertEqual([t['title'] for t in a.get_rows()],['测试任务 2'])
        self.assertEqual(a.root.focus_get(),a.search)
        a.search_var.set('');a.flush_draw()
        t=a.data['tasks'][0];t['claimed']=True;a.render();a.toggle_active()
        self.assertNotIn(t,a.get_rows())
        a.toggle_settings();a.root.update();self.assertFalse(a.search.winfo_ismapped())

    def test_hover_does_not_rebuild_canvas(self):
        a=self.a;a.draw();before=a.draw_count;items=a.canvas.find_all()
        hit=next(h for h in a.hits if h[0]=='new-task')
        for _ in range(250):
            a.motion(SimpleNamespace(x=hit[1]+2,y=hit[2]+2));a.clear_hover()
        self.assertEqual(a.draw_count,before)
        self.assertEqual(a.canvas.find_all(),items)

    def test_large_list_is_virtualized_and_coalesced(self):
        a=self.a
        a.data['tasks']=[app.task(f'任务 {i}',app.TYPES[0],'测试描述') for i in range(2000)]
        a.render();self.assertLess(len(a.canvas.find_all()),250)
        a.scroll=a.max_scroll;a.draw();self.assertLess(len(a.canvas.find_all()),250)
        self.assertTrue(any('任务 1999'==a.canvas.itemcget(i,'text') for i in a.canvas.find_all() if a.canvas.type(i)=='text'))
        for _ in range(100):a.request_draw()
        callbacks=a.root.tk.splitlist(a.root.tk.call('after','info'))
        self.assertEqual(callbacks.count(a.draw_job),1)

    def test_save_backup_and_unchanged_write(self):
        import json
        a=self.a;a.save();a.data['coins']=77;a.save()
        backup=json.loads(app.DATA.with_suffix('.bak').read_text(encoding='utf-8'))
        self.assertEqual(backup['coins'],0)
        timestamp=app.DATA.stat().st_mtime_ns;a.save()
        self.assertEqual(app.DATA.stat().st_mtime_ns,timestamp)

    def test_failed_save_feedback_then_retry(self):
        from unittest.mock import patch
        a=self.a
        with patch.object(app.App,'save',side_effect=OSError('disk full')):a.save()
        self.assertTrue(a.save_error)
        a.save();self.assertFalse(a.save_error)

    def test_single_instance_lock_across_processes(self):
        import subprocess,sys
        from questdock.launcher import acquire_lock
        path=Path(self.tmp.name)/'instance.lock'
        lock=acquire_lock(path);self.assertIsNotNone(lock)
        code="from pathlib import Path; from questdock.launcher import acquire_lock; import sys; lock=acquire_lock(Path(sys.argv[1])); print('blocked' if lock is None else 'acquired')"
        result=subprocess.run([sys.executable,'-c',code,str(path)],capture_output=True,text=True,check=True)
        self.assertEqual(result.stdout.strip(),'blocked')
        lock.close()
        result=subprocess.run([sys.executable,'-c',code,str(path)],capture_output=True,text=True,check=True)
        self.assertEqual(result.stdout.strip(),'acquired')

    def test_progress_undo_and_claim_boundary(self):
        a=self.a;t=a.data['tasks'][0]
        a.advance(t,1);self.assertIsNotNone(a.undo_record)
        a.undo_progress();self.assertEqual(t['progress'],0)
        self.assertEqual(a.data['coins'],0)
        a.advance(t,1);a.claim(t);a.undo_progress()
        self.assertEqual(a.data['coins'],20);self.assertTrue(t['claimed'])
        self.assertIsNone(a.undo_record)

    def test_undo_does_not_restore_yesterday_progress(self):
        a=self.a;t=a.data['tasks'][1]
        a.advance(t,1);a.undo_record['date']='2000-01-01'
        a.undo_progress();self.assertEqual(t['progress'],1)
        self.assertIsNone(a.undo_record)

    def test_claim_all_is_filtered_independent_and_idempotent(self):
        a=self.a;a.confirm=lambda title,desc,action:action()
        daily=a.data['tasks'][0];story=a.data['tasks'][6]
        daily['progress']=daily['target'];story['progress']=story['target']
        a.kind=app.TYPES[2];a.search_value='nonmatching'
        a.claim_all();a.claim_all()
        self.assertEqual(a.data['coins'],daily['reward']+story['reward'])
        self.assertEqual(len(a.data['history']),2)

    def test_claim_confirmation_revalidates_progress(self):
        a=self.a;t=a.data['tasks'][0];t['progress']=t['target']
        actions=[];a.confirm=lambda title,desc,action:actions.append(action)
        a.claim_all();t['progress']=0;actions[0]()
        self.assertEqual(a.data['coins'],0);self.assertFalse(t['claimed'])

    def test_product_edit_keeps_existing_ticket(self):
        a=self.a;p=a.data['shop'][0]
        a.data['bag'].append(dict(name=p['name'],date=app.today(),used=False))
        old_name=p['name'];a.toggle_panel();a.root.update();a.product(p);a.root.update()
        def descendants(w):
            for child in w.winfo_children():
                yield child
                yield from descendants(child)
        entries=[w for w in descendants(a.dialog) if w.winfo_class()=='TEntry']
        entries[0].delete(0,'end');entries[0].insert(0,'新的休息券')
        entries[1].delete(0,'end');entries[1].insert(0,'25')
        button=next(w for w in descendants(a.dialog) if w.winfo_class()=='Button' and w.cget('text')=='保存修改')
        button.invoke()
        self.assertEqual(p['cost'],25);self.assertEqual(p['name'],'新的休息券')
        self.assertEqual(a.data['bag'][0]['name'],old_name)
        saved=json.loads(app.DATA.read_text(encoding='utf-8'))
        self.assertEqual(saved['shop'][0]['cost'],25)

    def test_all_reward_forms_accept_keyboard_after_click(self):
        import tkinter as tk
        a=self.a;a.toggle_panel();a.root.update()
        def descendants(w):
            for child in w.winfo_children():
                yield child
                yield from descendants(child)
        settled=dict(a.data['tasks'][0],claimed=True,progress=1)
        cases=[('new task',lambda:a.edit()),('task',lambda:a.edit(a.data['tasks'][0])),
               ('settled task',lambda:a.edit(settled)),('new product',lambda:a.product()),
               ('product',lambda:a.product(a.data['shop'][0]))]
        for label,open_form in cases:
            with self.subTest(form=label):
                open_form();a.root.update()
                self.addCleanup(a.dialog.destroy)
                field=[w for w in descendants(a.dialog) if w.winfo_class()=='TEntry'][1]
                # Simulate returning from another window; insert() bypasses keyboard routing.
                other=tk.Tk();other.update();other.focus_force();a.root.update()
                self.addCleanup(other.destroy)
                field.event_generate('<ButtonPress-1>',x=15,y=15)
                field.event_generate('<ButtonRelease-1>',x=15,y=15);a.root.update()
                self.assertEqual(a.root.focus_get(),field)
                field.event_generate('<Control-a>');field.event_generate('<KeyPress-7>');field.event_generate('<KeyPress-5>');a.root.update()
                self.assertEqual(field.get(),'75')
                field.event_generate('<KeyPress-BackSpace>');a.root.update()
                self.assertEqual(field.get(),'7')
                self.doCleanups();a.root.update()

    def test_edit_reward_preserves_paid_steps_and_saves(self):
        a=self.a;t=a.data['tasks'][0]
        t.update(target=3,progress=1,rewarded_steps=1,reward=20,claimed=False)
        a.data['coins']=20;a.data['earned']=20
        a.toggle_panel();a.root.update();a.edit(t);a.root.update()
        def descendants(w):
            for child in w.winfo_children():
                yield child
                yield from descendants(child)
        entries=[w for w in descendants(a.dialog) if w.winfo_class()=='TEntry']
        entries[1].delete(0,'end');entries[1].insert(0,'35')
        next(w for w in descendants(a.dialog) if w.winfo_class()=='Button' and w.cget('text')=='保存任务').invoke()
        self.assertEqual(t['reward'],35)
        self.assertEqual(t['rewarded_steps'],1)
        self.assertEqual(a.data['coins'],20);self.assertEqual(a.data['earned'],20)
        saved=json.loads(app.DATA.read_text(encoding='utf-8'))
        self.assertEqual(saved['tasks'][0]['reward'],35)
        a.advance(t,1)
        self.assertEqual(a.data['coins'],55);self.assertEqual(a.data['earned'],55)

    def test_completed_task_keeps_edit_entry(self):
        a=self.a;t=a.data['tasks'][0]
        t.update(progress=t['target'],claimed=True)
        a.toggle_panel();a.root.update();a.draw()
        hit=next(h for h in a.hits if h[0]=='edit'+t['id'])
        hit[-1]()
        a.root.update()
        self.assertEqual(a.dialog.title(),'编辑任务')

    def test_title_fits_pixel_budget(self):
        a=self.a
        for text in ['宽字符标题'*20,'W'*100,'short']:
            fitted=a.fit_text(text,200,12,'bold')
            self.assertLessEqual(a.font_cache[(12,'bold')].measure(fitted),200)

    def test_confirmation_cannot_claim_across_midnight(self):
        from unittest.mock import patch
        a=self.a;t=a.data['tasks'][0];t['progress']=t['target']
        actions=[];a.confirm=lambda title,desc,action:actions.append(action)
        a.claim_all()
        with patch('questdock.app.today',return_value='2099-01-01'):actions[0]()
        self.assertEqual(a.data['coins'],0);self.assertFalse(t['claimed']);self.assertEqual(t['progress'],0)

    def test_save_action_stays_visible_in_short_dialog(self):
        a=self.a;a.toggle_panel();a.root.update();a.edit();a.root.update()
        d=a.dialog;d.geometry('440x300');a.root.update()
        bar=d.action_bar
        self.assertTrue(bar.winfo_ismapped())
        self.assertLessEqual(bar.winfo_rooty()+bar.winfo_height(),d.winfo_rooty()+d.winfo_height())
        self.assertGreater(bar.winfo_height(),20)

    def test_today_plan_supports_all_types_and_rolls_over(self):
        from unittest.mock import patch
        a=self.a;daily=a.data['tasks'][0];story=a.data['tasks'][6]
        a.toggle_today(story);a.filter('今日')
        self.assertEqual(len(a.get_rows()),7)
        a.toggle_today(story);self.assertEqual(len(a.get_rows()),6)
        a.toggle_today(story)
        with patch('questdock.app.today',return_value='2099-01-01'):a.reset_day()
        self.assertEqual(len(a.get_rows()),6);self.assertIn(story,a.data['tasks'])

    def test_focus_tick_only_updates_clock_and_never_rewards_task(self):
        from unittest.mock import patch
        from questdock.focus_timer import FocusTimer
        a=self.a;t=a.data['tasks'][0];a.start_focus(t)
        now=[100.];a.focus=FocusTimer(t['id'],t['title'],60,clock=lambda:now[0])
        a.last_focus_tick=100.;a.focus_checkpoint=100.
        a.render();before=a.draw_count
        now[0]=101.
        with patch('questdock.premium.time.monotonic',return_value=101.):a.focus_tick()
        self.assertEqual(a.draw_count,before)
        a.focus.left=1;a.focus.anchor=101.;a.last_focus_tick=101.;now[0]=102.
        with patch('questdock.premium.time.monotonic',return_value=102.):a.focus_tick()
        self.assertIsNone(a.focus);self.assertEqual(t['progress'],0);self.assertEqual(a.data['coins'],0)
        self.assertTrue(any('完成专注' in line for line in a.data['history']))

    def test_focus_long_suspend_pauses_without_counting_gap(self):
        from unittest.mock import patch
        from questdock.focus_timer import FocusTimer
        a=self.a;now=[100.];a.focus=FocusTimer('1','Study',60,clock=lambda:now[0]);a.last_focus_tick=105.
        now[0]=200.
        with patch('questdock.premium.time.monotonic',return_value=200.):a.focus_tick()
        self.assertFalse(a.focus.running);self.assertEqual(a.focus.remaining(),55)

    def test_focus_survives_restart_as_paused(self):
        a=self.a;a.start_focus(a.data['tasks'][0]);a.quit()
        self.a=premium.App();self.a.root.update()
        self.assertIsNotNone(self.a.focus);self.assertFalse(self.a.focus.running)
        self.assertIsNone(self.a.focus_job)

if __name__=='__main__':unittest.main()

