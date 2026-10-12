import tkinter as tk
from tkinter import ttk
import unittest
from unittest import mock
import quest_log as model
from quest_log_grid import build_grid
from quest_log_ui import QuestLogTab

class MultiQuestTests(unittest.TestCase):
    def test_ids_parse_and_any_completed_variant(self):
        task=model.new_task('Rotating weekly', '42, 43 44;42', reset='Weekly')
        self.assertEqual(model.quest_ids(task),[42,43,44])
        record={'questLog':{'scannedAt':100,'quests':{'42':{'status':'Not picked up','reset':'Weekly','scannedAt':100},'43':{'status':'Completed','reset':'Weekly','scannedAt':100}}}}
        self.assertEqual(model.task_status(task,record,150),'Completed')
        self.assertEqual(model.task_status(task,record,model.next_reset('Weekly',100)),'Awaiting new scan')
        for value in ('', '42,wrong', '0,42', True):
            with self.assertRaises(ValueError):model.new_task('Invalid',value)

    def test_overlapping_groups_have_independent_columns(self):
        a=model.new_task('Weekly',[42,43],reset='Weekly')
        b=model.new_task('Weekly',[42,44],reset='Weekly')
        columns,rows,_=build_grid({'a':[a,b]}, {'a':{'name':'A'}},now=150)
        quests=[c for c in columns if getattr(c,'quest_id',None)]
        self.assertEqual(len(quests),2)
        self.assertNotEqual(quests[0].task_key,quests[1].task_key)

    def test_click_editor_changes_ids_for_all_assignments(self):
        root=tk.Tk();root.withdraw();self.addCleanup(root.destroy)
        task=model.new_task('Weekly',42,reset='Weekly')
        state={'a':[task],'b':[]};model.assign_characters(state,task,{'a','b'})
        tab=QuestLogTab(root,state)
        tab.load([{'guid':'a','name':'A'},{'guid':'b','name':'B'}])
        popup=tab.assignment_popup(tab.state['a'][0])
        def descendants(parent):
            for child in parent.winfo_children():
                yield child
                yield from descendants(child)
        widgets=list(descendants(popup))
        entries=[w for w in widgets if isinstance(w,ttk.Entry) and not isinstance(w,ttk.Combobox)]
        entries[1].delete(0,'end');entries[1].insert(0,'43, 44')
        next(w for w in widgets if getattr(w,'caption','')=='Save').invoke()
        for tasks in tab.state.values():
            self.assertEqual(tasks[0]['questID'],43)
            self.assertEqual(tasks[0]['questIDs'],[43,44])
        root.update_idletasks()

    def test_assignment_footer_stays_visible_at_small_saved_size(self):
        root=tk.Tk();self.addCleanup(root.destroy)
        tab=QuestLogTab(root,{'a':[model.new_task('Weekly','42,43',reset='Weekly')]})
        tab.load([{'guid':'a','name':'A'}])
        popup=tab.assignment_popup(tab.state['a'][0])
        popup.geometry('520x620')
        root.update()
        def descendants(parent):
            for child in parent.winfo_children():
                yield child
                yield from descendants(child)
        for caption in ('Save','Cancel'):
            button=next(w for w in descendants(popup) if getattr(w,'caption','')==caption)
            top=button.winfo_rooty()-popup.winfo_rooty()
            self.assertTrue(button.winfo_ismapped())
            self.assertGreaterEqual(top,0)
            self.assertLessEqual(top+button.winfo_height(),popup.winfo_height())
        popup.destroy()
