import tkinter as tk
import unittest
from unittest import mock
import app
import roster_format
import theme
from quest_log_ui import QuestLogTab

class ActionNeededTests(unittest.TestCase):
    def test_only_name_is_highlighted_and_unchecking_restores_format(self):
        fmt = roster_format.normalize({})
        record = {'name': 'Character', 'isMain': True}
        usual = app._cell_name(record, fmt)
        marked = app._cell_name({**record, 'actionNeeded': True}, fmt)
        self.assertEqual((marked.bg, marked.fg), (theme.ACTION_NEEDED_BG, theme.TEXT))
        restored = app._cell_name({**record, 'actionNeeded': False}, fmt)
        self.assertEqual(restored, usual)

    def test_checkbox_is_per_character_and_survives_refresh(self):
        root = tk.Tk()
        root.withdraw()
        self.addCleanup(root.destroy)
        saved = mock.Mock()
        task = {'id': 't', 'title': 'Task', 'status': 'Completed', 'changedAt': 100}
        tab = QuestLogTab(root, {'a': [task], 'b': []}, on_action_needed=saved)
        records = [{'guid': 'a', 'name': 'A'}, {'guid': 'b', 'name': 'B'}]
        tab.load(records)
        tab.open_character('a')
        tab.action_needed_var.set(True)
        tab.toggle_action_needed()
        saved.assert_called_with('a', True)
        self.assertEqual(tab.action_needed, {'a': True})
        self.assertEqual(tab.state['a'][0]['status'], 'Completed')
        tab.load(records)
        self.assertTrue(tab.action_needed_var.get())
        tab.open_character('b')
        self.assertFalse(tab.action_needed_var.get())
        tab.open_character('a')
        tab.action_needed_var.set(False)
        tab.toggle_action_needed()
        self.assertEqual(tab.action_needed, {})
