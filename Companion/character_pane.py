"""Roster character details, including locally saved notes and quest tracking."""
import tkinter as tk
from tkinter import ttk
import db
import theme
from professions_ui import ScrollArea
from widgets import Button, WoWScrollbar, style_main_tabs
from info_format import render_info


class CharacterPane(ttk.Frame):
    def __init__(self, parent, close, on_quests=None):
        super().__init__(parent)
        self.guid = None
        self.drafts = {}
        self.source = ''
        self.editing = False
        conn = db.connect()
        try:
            self.saved_notes = db.get_json(conn, 'character_notes') or {}
        finally:
            conn.close()
        header = ttk.Frame(self, padding=8)
        header.pack(fill='x')
        self.name = tk.StringVar()
        ttk.Label(header, textvariable=self.name, font=('Montserrat', 12, 'bold')).pack(side='left')
        Button(header, text='Close', command=close).pack(side='right')
        tabs = ttk.Notebook(self)
        self.tabs = tabs
        tabs.pack(fill='both', expand=True)
        info = ttk.Frame(tabs, padding=12)
        tabs.add(info, text='Info')
        quests = ScrollArea(tabs)
        tabs.add(quests, text='To Do')
        self.quest_page = str(quests)
        if on_quests:
            tabs.bind('<<NotebookTabChanged>>', lambda _: on_quests() if self.quest_visible() else None, add='+')
        style_main_tabs(tabs, point_size=7, user_icon=True, fit_labels=True)
        self.inner, self.canvas = quests.inner, quests.canvas
        ttk.Label(info, text='Character information').pack(anchor='w', pady=(0, 8))
        self.syntax_help = ttk.Label(info, text='Syntax: # Heading · **bold** · *italic* · - list · | table |', wraplength=440)
        area = ttk.Frame(info)
        self.info_area = area
        area.pack(fill='both', expand=True)
        self.notes = tk.Text(area, width=36, height=12, wrap='word', font=('Montserrat', 9),
                             background=theme.PANEL, foreground=theme.TEXT, insertbackground=theme.GOLD,
                             selectbackground=theme.GOLD_DARK, highlightthickness=0)
        bar = WoWScrollbar(area, command=self.notes.yview)
        bar.pack(side='right', fill='y')
        self.notes.configure(yscrollcommand=bar.set)
        self.notes.pack(fill='both', expand=True)
        controls = ttk.Frame(info)
        controls.pack(fill='x', pady=8)
        self.status = tk.StringVar()
        ttk.Label(controls, textvariable=self.status).pack(side='left')
        self.save_button = Button(controls, text='Save Info', command=self.save_notes, state='disabled')
        self.save_button.pack(side='right')
        Button(controls, text='Edit Info', command=self.edit_info).pack(side='right', padx=6)
        self.notes.configure(state='disabled')

    def show_character(self, guid, record):
        self.name.set(f"{record.get('level') or '?'} - {record.get('name', 'Character')}")
        if guid == self.guid:
            return
        if self.guid:
            self.drafts[self.guid] = self.notes.get('1.0', 'end-1c') if self.editing else self.source
        self.guid = guid
        self.source = self.drafts.get(guid, self.saved_notes.get(guid, ''))
        self.editing = False
        self.save_button.configure(state='disabled')
        self.syntax_help.pack_forget()
        render_info(self.notes, self.source)
        self.status.set('')

    def save_notes(self):
        if not self.guid:
            return
        text = self.notes.get('1.0', 'end-1c') if self.editing else self.source
        conn = db.connect()
        try:
            stored = db.get_json(conn, 'character_notes') or {}
            stored[self.guid] = text
            db.set_json(conn, 'character_notes', stored)
            self.saved_notes = stored
        finally:
            conn.close()
        self.drafts[self.guid] = text
        self.source = text
        self.editing = False
        self.syntax_help.pack_forget()
        render_info(self.notes, text)
        self.save_button.configure(state='disabled')
        self.status.set('Info saved.')

    def edit_info(self):
        if not self.guid or self.editing:
            return
        self.notes.configure(state='normal')
        self.notes.delete('1.0', 'end')
        for tag in self.notes.tag_names():
            if tag != 'sel':
                self.notes.tag_delete(tag)
        self.notes.insert('1.0', self.source)
        self.editing = True
        self.syntax_help.pack(before=self.info_area, anchor='w', pady=(0, 8))
        self.save_button.configure(state='normal')
        self.status.set('Editing info')
        self.notes.focus_set()

    def quest_visible(self):
        return self.tabs.select() == self.quest_page
