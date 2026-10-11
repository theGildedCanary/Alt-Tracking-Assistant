"""Roster character details, including locally saved notes and quest tracking."""
import tkinter as tk
import re
from tkinter import ttk
import db
import theme
from professions_ui import ScrollArea
from widgets import Button, IconButton, WoWScrollbar, style_main_tabs, caption_image
from info_format import render_info, HEADER_IMAGES, header_name, set_header


class CharacterPane(ttk.Frame):
    def __init__(self, parent, close, on_quests=None, note_paths=lambda: []):
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
        from history_ui import HistoryPanel
        self.history_page = HistoryPanel(tabs, paths=note_paths)
        tabs.add(self.history_page, text='Notes')
        if on_quests:
            tabs.bind('<<NotebookTabChanged>>', lambda _: on_quests() if self.quest_visible() else None, add='+')
        style_main_tabs(tabs, point_size=7, user_icon=True, fit_labels=True)
        self.inner, self.canvas = quests.inner, quests.canvas
        info_heading = ttk.Frame(info)
        info_heading.pack(fill='x', pady=(0, 8))
        self.info_heading_image = caption_image(info_heading, 'CHARACTER INFORMATION', theme.GOLD, point_size=9)
        ttk.Label(info_heading, image=self.info_heading_image).pack(side='left')
        style = ttk.Style(self)
        style.configure('Info.TButton', padding=0)
        root = self.winfo_toplevel()
        if hasattr(root, '_ata_theme_images'):
            images = root._ata_theme_images
            if 'Info.compactButton' not in style.element_names():
                style.element_create('Info.compactButton', 'image', images[2],
                                     ('pressed', images[4]), ('active', images[3]),
                                     border=3, width=1, height=1, sticky='nsew')
            style.layout('Info.TButton', [('Info.compactButton', {
                'sticky': 'nsew', 'children': [('Button.label', {'sticky': ''})]})])
        size = self.info_heading_image.height()
        info_square = ttk.Frame(info_heading, width=size, height=size)
        info_square.pack(side='left', padx=(8, 0))
        info_square.pack_propagate(False)
        IconButton(info_square, icon='info', pixel_size=max(8, size-6), style='Info.TButton',
                   command=self.show_html_help).pack(fill='both', expand=True)
        self.header_controls = ttk.Frame(info)
        ttk.Label(self.header_controls, text='Image header').pack(side='left', padx=(0, 8))
        self.header_choice = tk.StringVar(value='None')
        self.header_picker = ttk.Combobox(self.header_controls, state='readonly', textvariable=self.header_choice,
                                         width=22, values=('None', *sorted(HEADER_IMAGES)))
        self.header_picker.pack(side='left')
        self.header_picker.bind('<<ComboboxSelected>>', self.choose_header)
        Button(self.header_controls, text='Text Color', command=self.choose_color).pack(side='left', padx=(12, 0))
        self.text_color = theme.GOLD
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
        self._resize_job = None
        self._info_width = None
        def resize(event):
            if event.width == self._info_width:
                return
            self._info_width = event.width
            if self._resize_job:
                self.after_cancel(self._resize_job)
            self._resize_job = self.after(80, self.resize_info)
        self.notes.bind('<Configure>', resize)
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
        self.history_page.show_character(guid)
        if guid == self.guid:
            return
        if self.guid:
            self.drafts[self.guid] = self.notes.get('1.0', 'end-1c') if self.editing else self.source
        self.guid = guid
        self.source = self.drafts.get(guid, self.saved_notes.get(guid, ''))
        self.editing = False
        self.save_button.configure(state='disabled')
        self.header_controls.pack_forget()
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
        self.header_controls.pack_forget()
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
        self.header_choice.set(header_name(self.source))
        self.header_controls.pack(before=self.info_area, fill='x', pady=(0, 8))
        self.save_button.configure(state='normal')
        self.status.set('Editing info')
        self.notes.focus_set()

    def quest_visible(self):
        return self.tabs.select() == self.quest_page

    def choose_color(self):
        if not self.editing:
            return
        from color_picker import ColorPicker, normalize_hex
        selection = self.notes.tag_ranges('sel')
        start, end = (str(selection[0]), str(selection[1])) if selection else (self.notes.index('insert'), self.notes.index('insert'))
        initial = self.text_color
        replace_hex = False
        try:
            initial = normalize_hex(self.notes.get(start, end))
            replace_hex = True
        except ValueError:
            # A caret inside an existing CSS color edits that value directly.
            source = self.notes.get('1.0', 'end-1c')
            offset = len(self.notes.get('1.0', start))
            for match in re.finditer(r'color\s*:\s*(#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3})\b', source):
                if match.start(1) <= offset <= match.end(1) and not selection:
                    start, end = f'1.0+{match.start(1)}c', f'1.0+{match.end(1)}c'
                    initial, replace_hex = normalize_hex(match.group(1)), True
                    break
        self.notes.mark_set('color_start', start)
        self.notes.mark_gravity('color_start', 'left')
        self.notes.mark_set('color_end', end)
        self.notes.mark_gravity('color_end', 'right')
        def apply(color):
            self.text_color = color
            start, end = self.notes.index('color_start'), self.notes.index('color_end')
            selected = self.notes.get(start, end)
            self.notes.delete(start, end)
            opening = f'<span style="color: {color}">'
            self.notes.insert(start, color if replace_hex else opening + selected + '</span>')
            self.notes.mark_set('insert', start if replace_hex else f'{start}+{len(opening)+len(selected)}c')
            self.notes.focus_set()
        ColorPicker(self.notes, initial, apply)

    def choose_header(self, event=None):
        if not self.editing:
            return
        source = set_header(self.notes.get('1.0', 'end-1c'), self.header_choice.get())
        self.notes.delete('1.0', 'end')
        self.notes.insert('1.0', source)


    def resize_info(self):
        self._resize_job = None
        if not self.editing and self.guid:
            position = self.notes.yview()[0]
            render_info(self.notes, self.source)
            self.notes.yview_moveto(position)

    def show_html_help(self):
        from html_help import show_help
        show_help(self)
