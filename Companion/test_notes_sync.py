import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import tkinter as tk
import db
import notes_sync
from lua_parser import parse_saved_variables

class NotesSyncTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(db.SCHEMA)
        self.addCleanup(self.conn.close)

    def test_import_edit_preserves_date_and_ignores_stale_addon(self):
        record = {'guid': 'a', 'notes': {1: {'id': 'note', 'text': 'Original', 'created': 100}}}
        notes_sync.merge(self.conn, [record])
        notes_sync.save(self.conn, [], 'a', 'note', 'Edited')
        note = notes_sync.merge(self.conn, [record])['a'][0]
        self.assertEqual((note['text'], note['created']), ('Edited', 100))
        self.assertGreater(note['changedAt'], 100)

    def test_deletion_from_either_side_survives_old_saved_data(self):
        record = {'guid': 'a', 'notes': [{'id': 'n', 'text': 'Note', 'created': 100}]}
        notes_sync.merge(self.conn, [record])
        notes_sync.save(self.conn, [], 'a', 'n')
        self.assertEqual(notes_sync.merge(self.conn, [record])['a'], [])
        notes_sync.save(self.conn, [], 'a', None, 'New')
        note = notes_sync.load(self.conn)['a'][0]
        record['notesDeleted'] = {note['id']: note['changedAt'] + 1}
        self.assertEqual(notes_sync.merge(self.conn, [record])['a'], [])

    def test_publish_full_note_and_utf8_limit(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            with mock.patch.object(notes_sync.settings_sync, 'addon_dirs', return_value=[Path(folder)]):
                self.assertEqual(notes_sync.save(self.conn, [], 'a', None, 'First\nSecond'), 1)
            data = parse_saved_variables((Path(folder) / 'NotesSync.lua').read_text())['AltTrackingAssistantNotesSync']
            self.assertEqual(data['a']['notes'][0]['text'], 'First\nSecond')
        with self.assertRaises(ValueError): notes_sync.save(self.conn, [], 'a', None, 'é' * 501)

    def test_history_editor_edits_existing_entry(self):
        from history_ui import HistoryPanel
        root = tk.Tk()
        root.withdraw()
        self.addCleanup(root.destroy)
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            database = Path(directory) / 'test.db'
            original_connect = db.connect
            with mock.patch.object(db, 'connect', side_effect=lambda: original_connect(database)):
                conn = db.connect()
                notes_sync.merge(conn, [{'guid': 'a', 'notes': [{'id': 'n', 'text': 'Original', 'created': 100}]}])
                conn.close()
                panel = HistoryPanel(root)
                panel.show_character('a')
                panel.edit_note({'id': 'n', 'text': 'Original'})
                panel.editor.delete('1.0', 'end')
                panel.editor.insert('1.0', 'Updated')
                panel.save_note()
                conn = db.connect()
                notes = notes_sync.load(conn)['a']
                conn.close()
                self.assertEqual(len(notes), 1)
                self.assertEqual((notes[0]['text'], notes[0]['created']), ('Updated', 100))

    def test_collapsible_years_and_days_match_history(self):
        from history_ui import HistoryPanel
        from datetime import datetime
        root = tk.Tk()
        root.withdraw()
        self.addCleanup(root.destroy)
        notes = [{'id': 'one', 'text': 'First', 'created': datetime(2026, 10, 11, 12).timestamp()},
                 {'id': 'two', 'text': 'Second', 'created': datetime(2026, 10, 11, 11).timestamp()},
                 {'id': 'three', 'text': 'Older', 'created': datetime(2025, 5, 1, 12).timestamp()}]
        with mock.patch.object(notes_sync, 'load', return_value={'a': notes}):
            panel = HistoryPanel(root)
            panel.show_character('a')
            self.assertEqual(list(panel.groups), [('year', 2026), ('day', '2026-10-11'), ('year', 2025), ('day', '2025-05-01')])
            year, year_body, toggle_year = panel.groups[('year', 2026)]
            day, day_body, toggle_day = panel.groups[('day', '2026-10-11')]
            self.assertEqual(year.cget('text'), '[-] 2026  (2)')
            self.assertIn('Sunday, Oct 11  (2)', day.cget('text'))
            toggle_day()
            self.assertEqual(day_body.winfo_manager(), '')
            toggle_year()
            self.assertEqual(year_body.winfo_manager(), '')
            toggle_year()
            self.assertEqual(year_body.winfo_manager(), 'pack')
            self.assertEqual(day_body.winfo_manager(), '')
            panel.signature = None
            panel.refresh()
            self.assertTrue(panel.groups[('day', '2026-10-11')][0].cget('text').startswith('[+]'))
            controls = panel.winfo_children()[0]
            captions = [getattr(widget, 'caption', '') for widget in controls.winfo_children()]
            self.assertIn('Save', captions)
            self.assertNotIn('Add Note', captions)
