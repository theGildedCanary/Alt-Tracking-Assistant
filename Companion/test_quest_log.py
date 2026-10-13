import json
import sqlite3
import tempfile
import tkinter as tk
from tkinter import ttk
import unittest
from pathlib import Path

import db
import quest_log as model
from quest_log_ui import QuestLogTab
from quest_log_grid import build_grid, INDICATORS
import theme
from types import SimpleNamespace
from datetime import datetime, timezone
from unittest import mock


class QuestLogTests(unittest.TestCase):
    def record(self):
        return {'guid': 'a', 'name': 'Test', 'realm': 'Realm', 'questLog': {
            'scannedAt': 100, 'nextDailyReset': 200, 'nextWeeklyReset': 500,
            'quests': {'42': {'title': 'Daily quest', 'reset': 'Daily', 'status': 'In progress', 'pickedUp': True, 'started': True}}}}

    def test_quest_states_and_expired_snapshot(self):
        task = model.new_task('', 42)
        record = self.record()
        self.assertEqual(model.task_reset(task, record), 'Daily')
        self.assertEqual(model.task_status(task, record, 150), 'In progress')
        record['questLog']['quests']['42']['status'] = 'Completed'
        self.assertEqual(model.task_status(task, record, 150), 'Completed')
        self.assertEqual(model.task_status(task, record, model.next_reset('Daily', 100)), 'Awaiting new scan')
        self.assertEqual(model.task_status(task, {}, 150), 'Awaiting scan')
        record['questLog']['quests']['42']['reset'] = 'None'
        self.assertEqual(model.task_status(task, record, 1000), 'Completed')

    def test_manual_resets_survive_restart_and_keep_nonrecurring(self):
        record = self.record()
        daily = model.new_task('Daily task', reset='Daily', notes='First\nSecond', priority='High')
        weekly = model.new_task('Weekly task', reset='Weekly')
        once = model.new_task('Once')
        for task in (daily, weekly, once):
            model.set_status(task, 'Completed', record, 150)
        state = json.loads(json.dumps({'a': [daily, weekly, once]}))
        self.assertTrue(model.apply_resets(state, {'a': record}, model.next_reset('Daily', 150) + 1))
        self.assertEqual([t['status'] for t in state['a']], ['Pending', 'Completed', 'Completed'])
        self.assertEqual(state['a'][0]['notes'], 'First\nSecond')
        self.assertTrue(model.apply_resets(state, {'a': record}, model.next_reset('Weekly', 150) + 1))
        self.assertEqual(state['a'][1]['status'], 'Pending')

    def test_late_snapshot_and_status_after_stale_reset(self):
        task = model.new_task('Task', reset='Daily')
        model.set_status(task, 'Completed', {}, 150)
        state = {'a': [task]}
        record = self.record()
        record['questLog']['nextDailyReset'] = 86600
        after_reset = model.next_reset('Daily', 150) + 1
        self.assertTrue(model.apply_resets(state, {'a': record}, after_reset))
        self.assertEqual(task['status'], 'Pending')
        model.set_status(task, 'Completed', self.record(), after_reset)
        self.assertEqual(task['resetAt'], model.next_reset('Daily', after_reset))
        self.assertFalse(model.apply_resets(state, {'a': record}, after_reset + 1))

    def test_database_migration_and_newer_quest_snapshot(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            path = Path(folder) / 'db.sqlite'
            conn = sqlite3.connect(path)
            conn.execute("CREATE TABLE characters (guid TEXT PRIMARY KEY, name TEXT, realm TEXT, class_name TEXT, class_file TEXT, race TEXT, faction TEXT, level INTEGER, level10_date INTEGER, last_scanned INTEGER, is_main INTEGER, progress_json TEXT)")
            conn.close()
            conn = db.connect(path)
            try:
                record = self.record()
                record['lastScanned'] = 100
                db.sync_characters(conn, {'a': record}, set())
                updated = self.record()
                updated['lastScanned'] = 100
                updated['questLog']['scannedAt'] = 200
                updated['questLog']['quests']['42']['status'] = 'Completed'
                db.sync_characters(conn, {'a': updated}, set())
                db.sync_characters(conn, {'a': record}, set())
                self.assertEqual(db.load_characters(conn)[0]['questLog']['quests']['42']['status'], 'Completed')
                model.save(conn, [], {'a': [model.new_task('Test')]})
                self.assertEqual(model.load(conn)['a'][0]['title'], 'Test')
            finally:
                conn.close()

    def test_opt_in_and_separate_sync_file(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root = Path(directory)
            sv = root / 'WTF' / 'Account' / '123' / 'SavedVariables' / 'AltTrackingAssistant.lua'
            addon = root / 'Interface' / 'AddOns' / 'AltTrackingAssistant'
            addon.mkdir(parents=True)
            (addon / 'AppSync.lua').write_text('existing settings')
            task = model.new_task('Quoted "quest"', 42)
            self.assertEqual(model.publish([sv], {'a': [task], 'b': []}), 1)
            content = (addon / 'QuestSync.lua').read_text()
            self.assertIn('["42"] = true', content)
            self.assertIn('["_tasks"] = {', content)
            self.assertIn('["_deleted"] = {}', content)
            self.assertEqual((addon / 'AppSync.lua').read_text(), 'existing settings')
            model.publish([sv], {})
            self.assertNotIn('42', (addon / 'QuestSync.lua').read_text())

    def test_invalid_quest_ids(self):
        for value in ('0', '-1', '1.2', 'abc', '2147483648', True):
            with self.assertRaises(ValueError):
                model.new_task('', value)

    def test_character_selection_detail_status_and_deletion(self):
        root = tk.Tk()
        root.withdraw()
        self.addCleanup(root.destroy)
        saved = []
        tab = QuestLogTab(root, on_save=lambda state: saved.append(state) or 1)
        tab.load([self.record(), {'guid': 'b', 'name': 'Other', 'realm': 'Realm'}])
        self.assertEqual(tab.row_guids, [])
        self.assertFalse(tab.panel_open)
        tab.choice.set(next(label for label, guid in tab.choices.items() if guid == 'a'))
        tab.add_character()
        self.assertEqual(tab.row_guids, ['a'])
        self.assertIsNone(tab.selected)
        self.assertFalse(tab.panel_open)
        tab.select_character(SimpleNamespace(x=10, y=10))
        self.assertEqual(tab.selected, 'a')
        self.assertTrue(tab.panel_open)
        task = model.new_task('Detailed task', reset='Weekly', notes='Steps', priority='High')
        tab.state['a'].append(task)
        tab.commit()
        tab.change_status(task, 'Completed')
        self.assertEqual(saved[-1]['a'][0]['status'], 'Completed')
        self.assertEqual(tab.rows[0][2].text, '1/1')
        tab.set_theme('Light Mode')
        tab.close_details()
        self.assertFalse(tab.panel_open)
        self.assertEqual(len(tab.split.panes()), 1)
        tab.load([self.record()])
        self.assertFalse(tab.panel_open)
        tab.open_character('a')
        popup = tab.delete_task(task)
        def choose(widget):
            for child in widget.winfo_children():
                if getattr(child, 'caption', '') == 'Remove from character':
                    child.invoke()
                    return True
                if choose(child): return True
            return False
        choose(popup)
        self.assertEqual(saved[-1]['a'], [])
        tab.remove_character()
        self.assertEqual(saved[-1], {})

    def test_vertical_quest_columns_and_four_states(self):
        task = model.new_task('', 42)
        record = self.record()
        for status in INDICATORS:
            record['questLog']['quests']['42']['status'] = status
            columns, rows, guids = build_grid({'a': [task], 'b': []}, {'a': record}, now=150)
            self.assertEqual(guids, ['a', 'b'])
            index = next(i for i, c in enumerate(columns) if c.title == 'Daily quest')
            self.assertTrue(columns[index].vertical)
            self.assertEqual(columns[index].group, 'Dailies')
            displayed_status = 'Not picked up' if status == 'Pending' else status
            self.assertEqual(rows[0][index].text, INDICATORS[displayed_status][0])
            self.assertEqual(rows[0][index].checked,
                             displayed_status == 'Completed' if displayed_status in ('Picked up', 'In progress', 'Completed') else None)
            self.assertEqual(rows[1][index].text, '—')
        _, rows, _ = build_grid({'a': [task]}, {'a': record}, now=model.next_reset('Daily', 100))
        self.assertEqual(rows[0][index].text, '?')

    def test_brown_panels_and_editor_in_all_themes(self):
        root = tk.Tk()
        root.withdraw()
        self.addCleanup(root.destroy)
        tab = QuestLogTab(root, {'a': []}, mode='Light Mode')
        tab.load([self.record()])
        tab.open_character('a')
        tab.editor(False)
        editor = next(w for w in tab.winfo_children() if isinstance(w, tk.Toplevel))
        def descendants(widget):
            for child in widget.winfo_children():
                yield child
                yield from descendants(child)
        text = next(w for w in descendants(editor) if isinstance(w, tk.Text))
        self.assertEqual(text.cget('background'), theme.PANEL)
        self.assertEqual(tab.list.body.cget('background'), theme.PANEL)
        self.assertEqual(tab.details.canvas.cget('background'), theme.PANEL)
        self.assertEqual(ttk.Style(root).lookup('Quest.TEntry', 'fieldbackground'), theme.PANEL)

    def test_explicit_reset_overrides_and_nicknames(self):
        record = self.record()
        record['questLog']['quests']['42']['title'] = 'Midnight: World Tour'
        task = model.new_task('World Tour', 42, reset='Weekly')
        self.assertEqual(model.task_reset(task, record), 'Weekly')
        columns, _, _ = build_grid({'a': [task]}, {'a': record}, now=150)
        column = next(c for c in columns if c.title == 'World Tour')
        self.assertEqual(column.group, 'Weeklies')
        task['resetMode'] = 'None'
        self.assertEqual(model.task_reset(task, record), 'None')
        record['questLog']['quests']['42']['status'] = 'Completed'
        self.assertEqual(model.task_status(task, record, 9999999), 'Completed')
        task['resetMode'] = 'Auto'
        self.assertEqual(model.task_reset(task, record), 'Daily')

    def test_fixed_edt_reset_boundaries(self):
        def stamp(value):
            return datetime.fromisoformat(value).replace(tzinfo=model.EDT).timestamp()
        monday = stamp('2026-10-12T10:59:59')
        self.assertEqual(model.next_reset('Daily', monday), stamp('2026-10-12T11:00:00'))
        self.assertEqual(model.next_reset('Weekly', monday), stamp('2026-10-13T11:00:00'))
        tuesday_reset = stamp('2026-10-13T11:00:00')
        self.assertEqual(model.next_reset('Weekly', tuesday_reset), stamp('2026-10-20T11:00:00'))
        self.assertEqual(model.next_reset('Daily', tuesday_reset), stamp('2026-10-14T11:00:00'))
        for date in ('2026-07-01T10:00:00', '2026-12-01T10:00:00'):
            self.assertEqual(datetime.fromtimestamp(model.next_reset('Daily', stamp(date)), timezone.utc).hour, 15)
        self.assertIsNone(model.next_reset('None', monday))

    def test_editor_reset_nickname_and_hidden_ids(self):
        root = tk.Tk()
        root.withdraw()
        self.addCleanup(root.destroy)
        record = self.record()
        record['guid'] = 'Player-12345'
        record['questLog']['quests']['42']['title'] = 'Midnight: World Tour'
        tab = QuestLogTab(root)
        tab.load([record, {**record, 'guid': 'Player-98765'}])
        self.assertEqual(len(tab.choices), 2)
        self.assertTrue(all('Player-' not in label for label in tab.choices))
        tab.choice.set(next(iter(tab.choices)))
        tab.add_character()
        tab.open_character('Player-12345')
        tab.editor(True)
        dialog = next(w for w in tab.winfo_children() if isinstance(w, tk.Toplevel))
        def descendants(widget):
            for child in widget.winfo_children():
                yield child
                yield from descendants(child)
        entries = [w for w in descendants(dialog) if isinstance(w, ttk.Entry) and not isinstance(w, ttk.Combobox)]
        entries[0].insert(0, '42')
        entries[1].insert(0, 'World Tour')
        self.assertFalse(any(isinstance(w, ttk.Combobox) and 'Auto' in w.cget('values') for w in descendants(dialog)))
        next(w for w in descendants(dialog) if getattr(w, '_reset_day', None) == 2).invoke()
        next(w for w in descendants(dialog) if getattr(w, 'caption', '') == 'Save').invoke()
        task = tab.state['Player-12345'][0]
        self.assertEqual(task['resetMode'], 'Weekly')
        self.assertEqual(task['title'], 'World Tour')
        labels = [w.cget('text') for w in descendants(tab.details.inner) if isinstance(w, ttk.Label)]
        self.assertIn('[2] World Tour [W]', labels)
        self.assertFalse(any('ID 42' in label or label == 'Quest 42' for label in labels))
        self.assertTrue(any(c.title == 'World Tour' and c.group == 'Weeklies' for c in tab.columns))

    def test_shared_assignments_preserve_character_progress(self):
        source = model.new_task('World Tour', 42, reset='Weekly', notes='Visit every zone', priority='High')
        existing = model.new_task('Local label', 42, reset='Weekly')
        existing['status'] = 'Completed'
        state = {'a': [source], 'b': [existing], 'c': []}
        model.assign_characters(state, source, {'a', 'b', 'c', 'not-added'}, now=150)
        self.assertEqual(set(state), {'a', 'b', 'c'})
        self.assertEqual(state['b'], [existing])
        self.assertEqual(existing['status'], 'Completed')
        added = state['c'][0]
        self.assertEqual((added['title'], added['notes'], added['resetMode'], added['priority']),
                         ('World Tour', 'Visit every zone', 'Weekly', 'High'))
        self.assertEqual(added['status'], 'Pending')
        self.assertNotEqual(added['id'], source['id'])
        model.assign_characters(state, source, {'b', 'c'}, now=151)
        self.assertEqual(state['a'], [])
        self.assertEqual(len(state['b']), 1)
        self.assertEqual(len(state['c']), 1)
        self.assertEqual(model.assigned_characters(state, added), {'b', 'c'})

    def test_shared_manual_tasks_have_independent_progress_and_identity(self):
        source = model.new_task('Collect supplies', reset='Daily', notes='Herbs\nOre', priority='High')
        model.set_status(source, 'Completed', {}, now=150)
        unrelated = model.new_task('Collect supplies', reset='Daily')
        state = {'a': [source], 'b': [unrelated], 'c': []}
        model.assign_characters(state, source, {'a', 'b'}, now=151)
        added = state['b'][1]
        self.assertEqual(source['status'], 'Completed')
        self.assertEqual(added['status'], 'Pending')
        self.assertNotIn('resetAt', added)
        self.assertEqual(model.assignment_key(added), model.assignment_key(source))
        self.assertNotEqual(model.assignment_key(unrelated), model.assignment_key(source))
        added['notes'] = 'Local steps'
        self.assertEqual(source['notes'], 'Herbs\nOre')
        restored = json.loads(json.dumps(state))
        model.assign_characters(restored, restored['b'][1], {'b', 'c'}, now=152)
        self.assertEqual(restored['a'], [])
        self.assertEqual(len(restored['b']), 2)
        self.assertEqual(restored['c'][0]['status'], 'Pending')
        self.assertEqual(model.assigned_characters(restored, restored['c'][0]), {'b', 'c'})

    def test_assignment_popup_edits_settings_for_all_assigned_characters(self):
        root = tk.Tk()
        root.withdraw()
        self.addCleanup(root.destroy)
        task = model.new_task('World Tour', 42, reset='Weekly')
        state = {'a': [task], 'b': []}
        model.assign_characters(state, task, {'a', 'b'})
        tab = QuestLogTab(root, state)
        tab.load([self.record(), {'guid': 'b', 'name': 'Other'}])
        popup = tab.assignment_popup(tab.state['a'][0])
        def descendants(widget):
            for child in widget.winfo_children():
                yield child
                yield from descendants(child)
        widgets = list(descendants(popup))
        entry = next(w for w in widgets if isinstance(w, ttk.Entry) and not isinstance(w, ttk.Combobox))
        entry.delete(0, 'end')
        entry.insert(0, 'Tour')
        combos = [w for w in widgets if isinstance(w, ttk.Combobox)]
        combos[0].set('High')
        for toggle in widgets:
            if getattr(toggle, '_reset_day', None) and not toggle.instate(['selected']): toggle.invoke()
        next(w for w in widgets if getattr(w, 'caption', '') == 'Save').invoke()
        for tasks in tab.state.values():
            self.assertEqual(tasks[0]['title'], 'Tour')
            self.assertEqual(tasks[0]['resetMode'], 'Daily')
            self.assertEqual(tasks[0]['priority'], 'High')
            self.assertEqual(tasks[0]['questID'], 42)

    def test_assignment_popup_save_cancel_and_header_click(self):
        root = tk.Tk()
        root.withdraw()
        self.addCleanup(root.destroy)
        task = model.new_task('World Tour', 42, reset='Weekly')
        saved = []
        tab = QuestLogTab(root, {'a': [task], 'b': []}, on_save=lambda state: saved.append(state) or 1)
        tab.load([self.record(), {'guid': 'b', 'name': 'Other', 'realm': 'Realm'},
                  {'guid': 'unadded', 'name': 'Unadded', 'realm': 'Realm'}])
        def descendants(widget):
            for child in widget.winfo_children():
                yield child
                yield from descendants(child)
        popup = tab.assignment_popup(tab.state['a'][0])
        toggles = [w for w in descendants(popup) if isinstance(w, ttk.Checkbutton) and hasattr(w, '_quest_class')]
        self.assertEqual(len(toggles), 2)
        self.assertTrue(toggles[0].instate(['selected']))
        self.assertFalse(toggles[1].instate(['selected']))
        toggles[1].invoke()
        next(w for w in descendants(popup) if getattr(w, 'caption', '') == 'Cancel').invoke()
        self.assertEqual(tab.state['b'], [])
        # This weekly quest is the first scrolling column.
        tab.select_quest_heading(SimpleNamespace(x=10, y=tab.list.band_height + 5))
        popup = next(w for w in tab.winfo_children() if isinstance(w, tk.Toplevel))
        toggles = [w for w in descendants(popup) if isinstance(w, ttk.Checkbutton) and hasattr(w, '_quest_class')]
        toggles[1].invoke()
        next(w for w in descendants(popup) if getattr(w, 'caption', '') == 'Save').invoke()
        self.assertEqual(saved[-1]['b'][0]['title'], 'World Tour')
        self.assertFalse(tab.panel_open)
        tab.open_character('b')
        title = next(w for w in descendants(tab.details.inner) if isinstance(w, ttk.Label) and w.cget('text') == '[2] World Tour [W]')
        title.event_generate('<Button-1>')
        popup = next(w for w in tab.winfo_children() if isinstance(w, tk.Toplevel))
        self.assertEqual(popup.cget('background'), theme.PANEL)
        toggles = [w for w in descendants(popup) if isinstance(w, ttk.Checkbutton) and hasattr(w, '_quest_class')]
        toggles[0].invoke()
        next(w for w in descendants(popup) if getattr(w, 'caption', '') == 'Save').invoke()
        self.assertEqual(saved[-1]['a'], [])
        self.assertEqual(len(saved[-1]['b']), 1)

    def test_spreadsheet_todos_require_a_reset_schedule(self):
        daily = model.new_task('Daily task', reset='Daily')
        weekly = model.new_task('Weekly task', reset='Weekly')
        custom = model.new_task('Scheduled task', reset_days=[1, 4])
        casual = model.new_task('Casual task')
        casual.update(status='Completed', resetAt=9999999999)
        invalid = dict(model.new_task('Empty schedule'), reset='Custom', resetDays=[])
        state = {'a': [daily, weekly, custom, casual, invalid],
                 'b': [dict(weekly, reset='None')], 'c': [casual]}
        model.set_status(daily, 'Completed', {}, now=150)
        columns, rows, _ = build_grid(state, {}, now=151)
        todo_columns = [i for i, column in enumerate(columns) if column.group == 'To dos']
        self.assertEqual({columns[i].title for i in todo_columns},
                         {'Daily task', 'Weekly task', 'Scheduled task'})
        self.assertEqual([row[2].text for row in rows], ['1/3', '0/0', '0/0'])
        self.assertTrue(all(rows[1][i].checked is None for i in todo_columns))
        self.assertEqual(len(state['a']), 5)

    def test_shared_todo_columns_names_and_group_colors(self):
        source = model.new_task('Gather materials', reset='Weekly')
        quest = model.new_task('Weekly quest', 42, reset='Weekly')
        daily = model.new_task('Daily quest', 43, reset='Daily')
        other = model.new_task('One time quest', 44, reset='None')
        state = {'a': [source, quest, daily, other], 'b': [], 'c': []}
        model.assign_characters(state, source, {'a', 'b'}, now=150)
        model.set_status(source, 'Completed', {}, now=150)
        columns, rows, _ = build_grid(state, {'a': self.record(), 'b': {'name': 'Other', 'realm': 'Hidden'}}, now=151)
        self.assertEqual(rows[0][1].text, '? - Test')
        self.assertEqual(rows[1][1].text, '? - Other')
        matches = [i for i, c in enumerate(columns) if c.title == 'Gather materials']
        self.assertEqual(len(matches), 1)
        index = matches[0]
        self.assertEqual(columns[index].group, 'To dos')
        self.assertEqual([row[index].checked for row in rows], [True, False, None])
        self.assertEqual(rows[2][index].text, '—')
        group_colors = {c.group: c.bg for c in columns if c.group}
        self.assertEqual(len(set(group_colors.values())), 4)
        self.assertNotIn('#ffffff', group_colors.values())

    def test_popups_center_instead_of_restoring_saved_positions(self):
        root = tk.Tk()
        root.withdraw()
        self.addCleanup(root.destroy)
        saved = []
        assignment_position = {'normal_rect': [40, 60, 560, 500], 'monitor_bounds': [0, 0, 1920, 1080], 'maximized': False}
        moved_position = {**assignment_position, 'normal_rect': [100, 120, 620, 560]}
        tab = QuestLogTab(root, {'a': [model.new_task('Task')]},
                          popup_positions={'assignments': assignment_position},
                          on_position_save=lambda positions: saved.append(positions))
        with mock.patch('quest_log_ui.window_position.center_popup') as center, \
             mock.patch('quest_log_ui.window_position.capture', return_value=moved_position):
            dialog = tab.assignment_popup(tab.state['a'][0])
            center.assert_called_with(dialog)
            tab.close_popup(dialog)
            self.assertEqual(saved[-1]['assignments'], moved_position)
            dialog = tab.assignment_popup(tab.state['a'][0])
            center.assert_called_with(dialog)
            tab.close_popup(dialog)
            tab.open_character('a')
            tab.editor(False)
            dialog = next(w for w in tab.winfo_children() if isinstance(w, tk.Toplevel))
            center.assert_called_with(dialog)
            tab.close_popup(dialog)
            self.assertEqual(set(saved[-1]), {'assignments', 'task_editor'})

    def test_todo_cell_toggles_only_clicked_character_without_opening_panel(self):
        root = tk.Tk()
        root.withdraw()
        self.addCleanup(root.destroy)
        source = model.new_task('Gather materials', reset='Weekly')
        state = {'a': [source], 'b': [], 'c': []}
        model.assign_characters(state, source, {'a', 'b'})
        saved = []
        tab = QuestLogTab(root, state, on_save=lambda value: saved.append(value) or 1)
        tab.load([self.record(), {'guid': 'b', 'name': 'Other'}, {'guid': 'c', 'name': 'Unassigned'}])
        offset = 0
        for column in tab.columns:
            if column.frozen:
                continue
            if getattr(column, 'task_key', None) == model.assignment_key(source):
                break
            offset += column.width
        # Use canvas coordinates so this also exercises the scroll-aware hit test.
        x = offset + column.width / 2 - tab.list.body.canvasx(0)
        y = tab.list.style.row_height / 2 - tab.list.body.canvasy(0)
        tab.toggle_todo_cell(SimpleNamespace(x=x, y=y))
        self.assertEqual(tab.state['a'][0]['status'], 'Completed')
        self.assertEqual(tab.state['b'][0]['status'], 'Pending')
        self.assertFalse(tab.panel_open)
        self.assertTrue(saved)
        tab.toggle_todo_cell(SimpleNamespace(x=x, y=y))
        self.assertEqual(tab.state['a'][0]['status'], 'Pending')
        tab.toggle_todo_cell(SimpleNamespace(x=x, y=y + 2*tab.list.style.row_height))
        self.assertEqual(tab.state['c'], [])

    def test_panel_completion_keeps_existing_widgets_and_scroll_position(self):
        root = tk.Tk()
        root.withdraw()
        self.addCleanup(root.destroy)
        saved = []
        tab = QuestLogTab(root, {'a': [model.new_task('Gather materials')]},
                          on_save=lambda state: saved.append(state) or 1)
        tab.load([self.record()])
        tab.open_character('a')
        task, variable, label = tab._status_widgets[0]
        children = tuple(tab.details.inner.winfo_children())
        view = tab.details.canvas.yview()
        with mock.patch.object(tab, 'load') as reload:
            tab.change_status(task, 'Completed')
            reload.assert_not_called()
        self.assertTrue(variable.get())
        self.assertEqual(label.cget('text'), '[2] Gather materials')
        self.assertEqual(saved[-1]['a'][0]['status'], 'Completed')
        tab.render_details()
        self.assertEqual(tuple(tab.details.inner.winfo_children()), children)
        self.assertEqual(tab.details.canvas.yview(), view)
        tab.change_status(task, 'Pending')
        self.assertFalse(variable.get())
        self.assertEqual(label.cget('text'), '[2] Gather materials')

    def test_character_order_persists_and_names_have_level_and_class_background(self):
        root = tk.Tk()
        root.withdraw()
        self.addCleanup(root.destroy)
        saved = []
        tab = QuestLogTab(root, {'a': [], 'b': []}, on_save=lambda state: saved.append(state) or 1)
        tab.load([{'guid': 'a', 'name': 'Mage', 'level': 90, 'classFile': 'MAGE'},
                  {'guid': 'b', 'name': 'Druid', 'level': 80, 'classFile': 'DRUID'}])
        popup = tab.order_characters_popup()
        def descendants(widget):
            for child in widget.winfo_children():
                yield child
                yield from descendants(child)
        widgets = list(descendants(popup))
        next(w for w in widgets if getattr(w, 'caption', '') == '▼').invoke()
        next(w for w in widgets if getattr(w, 'caption', '') == 'Save').invoke()
        self.assertEqual(list(saved[-1]), ['b', 'a'])
        self.assertEqual(tab.row_guids, ['b', 'a'])
        _, rows, _ = build_grid(tab.state, tab.records)
        self.assertEqual(rows[0][1].text, '80 - Druid')
        self.assertEqual(rows[0][1].bg, theme.CLASS_COLORS['DRUID'])
        self.assertTrue(rows[0][0].removable)
        self.assertEqual(rows[0][0].bg, theme.PANEL)

    def test_manual_header_assigns_added_characters(self):
        root = tk.Tk()
        root.withdraw()
        self.addCleanup(root.destroy)
        task = model.new_task('Gather materials', reset='Weekly')
        tab = QuestLogTab(root, {'a': [task], 'b': []})
        tab.load([self.record(), {'guid': 'b', 'name': 'Other'}])
        offset = 0
        for column in tab.columns:
            if column.frozen:
                continue
            if getattr(column, 'task_key', None) == model.assignment_key(task):
                break
            offset += column.width
        with mock.patch.object(tab, 'assignment_popup') as popup:
            tab.select_quest_heading(SimpleNamespace(x=offset + 5, y=tab.list.band_height + 5))
            popup.assert_called_once_with(tab.state['a'][0], 'Gather materials')


if __name__ == '__main__':
    unittest.main()
