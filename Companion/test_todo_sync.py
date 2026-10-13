import sqlite3
from unittest import mock
import unittest
from datetime import datetime
import db
import quest_log as model
import settings_sync
from lua_parser import parse_saved_variables

class TodoSyncTests(unittest.TestCase):
    def test_custom_weekdays_reset_at_fixed_est(self):
        now = datetime(2026, 10, 11, 12, tzinfo=model.EDT).timestamp()
        task = model.new_task('Monday and Wednesday', reset='Custom', reset_days=[1, 3])
        model.set_status(task, 'Completed', {}, now)
        expected = datetime(2026, 10, 12, 11, tzinfo=model.EDT).timestamp()
        self.assertEqual(task['resetAt'], expected)
        self.assertTrue(model.apply_resets({'a': [task]}, {}, expected))
        self.assertEqual(task['status'], 'Pending')
        self.assertEqual(task['resetAt'], datetime(2026, 10, 14, 11, tzinfo=model.EDT).timestamp())

    def test_indexed_addon_arrays_and_deleted_task_stays_deleted(self):
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        conn.executescript(db.SCHEMA)
        self.addCleanup(conn.close)
        record = {'guid': 'a', 'todos': {1: {'id': 'legacy', 'text': 'Task', 'done': True, 'created': 100,
                                          'resetDays': {1: 2}}}}
        state, _ = model.merge_addon(conn, [record])
        self.assertEqual(state['a'][0]['status'], 'Completed')
        self.assertEqual(state['a'][0]['resetDays'], [2])
        model.save(conn, [], {'a': []})
        self.assertEqual(model.merge_addon(conn, [record])[0]['a'], [])

    def test_full_task_metadata_is_lua_table(self):
        task = model.new_task('Weekly task', reset='Custom', reset_days=[2, 5])
        parsed = parse_saved_variables('Sync=' + settings_sync._lua_value({'_tasks': [task]}))['Sync']
        self.assertEqual(parsed['_tasks'][0]['resetDays'], [2, 5])
        self.assertIsNone(parsed['_tasks'][0]['questID'])

    def test_startup_sync_imports_addon_tasks(self):
        import app
        from unittest import mock
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        conn.executescript(db.SCHEMA)
        record = {'guid': 'a', 'name': 'Test', 'todos': [{'id': 'startup', 'text': 'Task', 'created': 100}]}
        with mock.patch.object(app.db, 'connect', return_value=conn), \
             mock.patch.object(app, 'collect_sources', return_value=({'a': record}, [])), \
             mock.patch.object(app.settings_sync, 'effective_settings', return_value=({'characterMains': {}}, False)), \
             mock.patch.object(app.db, 'sync_characters'), \
             mock.patch.object(app.db, 'load_characters', return_value=[]), \
             mock.patch.object(app.quest_log, 'merge_addon', wraps=model.merge_addon) as merge:
            self.assertEqual(app.sync_database(['test.lua']), [])
            merge.assert_called_once()

    def test_reset_days_classify_frequency_and_keep_selected_weekday(self):
        weekly = model.new_task('Wednesday', 42, reset_days=[3])
        daily = model.new_task('Daily', reset_days=list(range(1, 8)))
        permanent = model.new_task('No reset', reset_days=[])
        self.assertEqual(model.task_reset(weekly, {}), 'Weekly')
        self.assertEqual(model.task_reset(daily, {}), 'Daily')
        self.assertEqual(model.task_reset(permanent, {}), 'None')
        monday = datetime(2026, 10, 12, 12, tzinfo=model.EDT).timestamp()
        boundary = model.next_reset('Weekly', monday, weekly['resetDays'])
        self.assertEqual(boundary, datetime(2026, 10, 14, 11, tzinfo=model.EDT).timestamp())

    def test_remove_assignment_and_delete_everywhere(self):
        import tkinter as tk
        from tkinter import ttk
        from quest_log_ui import QuestLogTab
        root = tk.Tk()
        root.withdraw()
        self.addCleanup(root.destroy)
        source = model.new_task('Shared quest', 42)
        state = {'a': [source], 'b': []}
        model.assign_characters(state, source, {'a', 'b'})
        tab = QuestLogTab(root, state)
        tab.load([{'guid': 'a', 'name': 'A'}, {'guid': 'b', 'name': 'B'}])
        def click(parent, caption):
            for child in parent.winfo_children():
                if getattr(child, 'caption', '') == caption:
                    child.invoke()
                    return True
                if click(child, caption): return True
            return False
        tab.selected = 'a'
        popup = tab.delete_task(tab.state['a'][0])
        self.assertTrue(click(popup, 'Remove from character'))
        self.assertEqual(tab.state['a'], [])
        self.assertEqual(len(tab.state['b']), 1)
        model.assign_characters(tab.state, tab.state['b'][0], {'a', 'b'})
        popup = tab.delete_task(tab.state['a'][0])
        self.assertTrue(click(popup, 'Delete to do'))
        self.assertEqual(tab.state, {'a': [], 'b': []})

    def test_compact_heading_markers(self):
        self.assertEqual(model.task_caption(model.new_task('Weekly quest', 42, reset_days=[2], priority='High'), {}), '[1] Weekly quest [W]')
        self.assertEqual(model.task_caption(model.new_task('Daily task', reset_days=list(range(1,8)), priority='Low'), {}), '[3] Daily task [D]')
        self.assertEqual(model.task_caption(model.new_task('Task'), {}), '[2] Task')

    def test_quest_grid_checkbox_does_not_highlight_selected_row(self):
        from quest_log_grid import build_grid
        import theme
        task = model.new_task('Manual task', reset='Weekly')
        records = {'a': {'name': 'Character', 'level': 90, 'classFile': 'DRUID'}}
        before = build_grid({'a': [task]}, records, selected='a')[1][0]
        model.set_status(task, 'Completed', records['a'])
        after = build_grid({'a': [task]}, records, selected='a')[1][0]
        self.assertEqual([cell.bg for cell in before], [cell.bg for cell in after])
        self.assertEqual(after[1].bg, theme.CLASS_COLORS['DRUID'])
        self.assertTrue(all(cell.bg == '' for cell in after[2:]))
        self.assertTrue(after[-1].checked)

    def test_scheduled_daily_reset_is_not_postponed_by_metadata_edit(self):
        before = datetime(2026, 10, 11, 10, tzinfo=model.EDT).timestamp()
        boundary = datetime(2026, 10, 11, 11, tzinfo=model.EDT).timestamp()
        task = model.new_task('Daily task', reset='Daily')
        model.set_status(task, 'Completed', {}, before)
        task.update(title='Edited title', changedAt=boundary+60)
        self.assertTrue(model.apply_resets({'a':[task]}, {}, boundary+60))
        self.assertEqual(task['status'], 'Pending')
        self.assertFalse(task['done'])
        self.assertEqual(task['resetAt'], boundary+86400)
        self.assertFalse(model.apply_resets({'a':[task]}, {}, boundary+61))

    def test_open_panel_resets_without_savedvariables_refresh(self):
        import tkinter as tk
        from quest_log_ui import QuestLogTab
        root=tk.Tk(); root.withdraw()
        self.addCleanup(root.destroy)
        before=datetime(2026,10,12,10,tzinfo=model.EDT).timestamp()
        boundary=datetime(2026,10,12,11,tzinfo=model.EDT).timestamp()
        task=model.new_task('Daily',reset='Daily')
        model.set_status(task,'Completed',{},before)
        saved=[]
        tab=QuestLogTab(root,{'a':[task]},on_save=lambda state:saved.append(state))
        with mock.patch.object(model.time,'time',return_value=before):
            tab.load([{'guid':'a','name':'A'}]); tab.open_character('a')
        children=tuple(tab.details.inner.winfo_children())
        with mock.patch.object(model.time,'time',return_value=boundary):
            self.assertTrue(tab.apply_due_resets(boundary))
        self.assertEqual(saved[-1]['a'][0]['status'],'Pending')
        self.assertFalse(tab._status_widgets[0][1].get())
        self.assertEqual(tuple(tab.details.inner.winfo_children()),children)

    def test_old_est_deadline_migrates_and_resets_overdue_task(self):
        now=datetime(2026,10,12,11,30,tzinfo=model.EDT).timestamp()
        old_deadline=datetime(2026,10,12,12,tzinfo=model.EDT).timestamp()
        task={'id':'old','title':'Patron Orders','reset':'Daily','status':'Completed','done':True,
              'changedAt':now-86400,'resetAt':old_deadline,'resetSchedule':'11amEST'}
        self.assertTrue(model.apply_resets({'a':[task]}, {}, now))
        self.assertEqual(task['status'],'Pending')
        self.assertEqual(task['resetSchedule'],'11amEDT')
        self.assertEqual(task['resetAt'],datetime(2026,10,13,11,tzinfo=model.EDT).timestamp())
