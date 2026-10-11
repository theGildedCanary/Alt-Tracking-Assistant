"""Editable dated notes shared with the addon's Notes / History section."""
import tkinter as tk
from tkinter import ttk
from datetime import datetime
import db
import notes_sync
import theme
from professions_ui import ScrollArea
from widgets import Button, IconButton, WoWScrollbar

class HistoryPanel(ttk.Frame):
    def __init__(self, parent, paths=lambda: []):
        super().__init__(parent, padding=12)
        self.paths = paths
        self.guid = None
        self.note_id = None
        self.signature = None
        self.collapsed = {}
        self.groups = {}
        style = ttk.Style(self)
        style.configure('History.Icon.TButton', padding=0, anchor='center')
        root = self.winfo_toplevel()
        if hasattr(root, '_ata_theme_images'):
            images = root._ata_theme_images
            if 'History.compactButton' not in style.element_names():
                style.element_create('History.compactButton', 'image', images[2],
                                     ('pressed', images[4]), ('active', images[3]),
                                     border=3, width=1, height=1, sticky='nsew')
            style.layout('History.Icon.TButton', [('History.compactButton', {
                'sticky': 'nsew', 'children': [('Button.label', {'sticky': ''})]})])
        controls = ttk.Frame(self)
        controls.pack(fill='x', pady=(0, 8))
        Button(controls, text='Save', command=self.save_note).pack(side='left', padx=6)
        self.status = tk.StringVar()
        ttk.Label(controls, textvariable=self.status, wraplength=350).pack(side='left', padx=6)
        area = ttk.Frame(self)
        area.pack(fill='x', pady=(0, 10))
        self.editor = tk.Text(area, height=5, width=36, wrap='word', font=('Montserrat', 9),
                              background=theme.PANEL, foreground=theme.TEXT, insertbackground=theme.GOLD,
                              selectbackground=theme.GOLD_DARK, highlightbackground=theme.GOLD_DARK,
                              highlightcolor=theme.GOLD, highlightthickness=1)
        scrollbar = WoWScrollbar(area, command=self.editor.yview)
        scrollbar.pack(side='right', fill='y')
        self.editor.configure(yscrollcommand=scrollbar.set)
        self.editor.pack(fill='both', expand=True)
        self.history = ScrollArea(self)
        self.history.pack(fill='both', expand=True)

    def show_character(self, guid):
        if guid != self.guid:
            self.guid = guid
            self.new_note()
        self.refresh()

    def new_note(self):
        self.note_id = None
        self.editor.delete('1.0', 'end')
        self.status.set('')

    def edit_note(self, note):
        self.note_id = note['id']
        self.editor.delete('1.0', 'end')
        self.editor.insert('1.0', note.get('text', ''))
        self.status.set('Editing note')
        self.editor.focus_set()

    def save_note(self):
        if not self.guid:
            return
        conn = db.connect()
        try:
            count = notes_sync.save(conn, self.paths(), self.guid, self.note_id, self.editor.get('1.0', 'end-1c'))
        except (ValueError, OSError) as exc:
            self.status.set(str(exc))
            return
        finally:
            conn.close()
        self.new_note()
        self.status.set('Saved. Reload WoW to apply.' if count else 'Saved locally.')
        self.refresh()

    def delete_note(self, note):
        guid = self.guid
        dialog = tk.Toplevel(self)
        dialog.title('Delete note')
        dialog.configure(background=theme.PANEL)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        frame = ttk.Frame(dialog, padding=16)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Delete this note from Notes / History?').pack(pady=(0, 12))
        def confirm():
            conn = db.connect()
            try:
                count = notes_sync.save(conn, self.paths(), guid, note['id'])
            except OSError as exc:
                self.status.set(str(exc))
                return
            finally:
                conn.close()
            dialog.destroy()
            if self.note_id == note['id']:
                self.new_note()
            self.status.set('Deleted. Reload WoW to apply.' if count else 'Deleted locally.')
            self.refresh()
        Button(frame, text='Delete', command=confirm).pack(side='right')
        Button(frame, text='Cancel', command=dialog.destroy).pack(side='right', padx=6)
        dialog.bind('<Escape>', lambda _: dialog.destroy())
        return dialog

    def refresh(self):
        conn = db.connect()
        try:
            notes = notes_sync.load(conn).get(self.guid, [])
        finally:
            conn.close()
        signature = (self.guid, repr(notes))
        if signature == self.signature:
            return
        self.signature = signature
        for child in self.history.inner.winfo_children():
            child.destroy()
        if not notes:
            ttk.Label(self.history.inner, text='No history notes yet.').pack(anchor='w', pady=6)
        self.groups = {}
        years = {}
        for note in sorted(notes, key=lambda item: item.get('created', 0), reverse=True):
            date = datetime.fromtimestamp(note.get('created', 0))
            years.setdefault(date.year, {}).setdefault(date.date(), []).append(note)
        for year, days in years.items():
            year_body = self.make_group(self.history.inner, ('year', year),
                                        f'{year}  ({sum(len(items) for items in days.values())})', bold=True)
            for date, items in days.items():
                day_body = self.make_group(year_body, ('day', date.isoformat()),
                                           f'{date:%A, %b %d}  ({len(items)})', indent=16)
                for note in items:
                    card = ttk.Frame(day_body, padding=(0, 8))
                    card.pack(fill='x', padx=(16, 0))
                    body = ttk.Frame(card)
                    body.pack(fill='x')
                    actions = ttk.Frame(body)
                    actions.pack(side='left', anchor='n', padx=(0, 6))
                    for icon, caption, action in (
                            ('pencil', 'Edit', lambda item=note: self.edit_note(item)),
                            ('x', 'Delete', lambda item=note: self.delete_note(item))):
                        square = ttk.Frame(actions, width=18, height=18)
                        square.pack(side='left', padx=(0, 3))
                        square.pack_propagate(False)
                        IconButton(square, icon=icon, text=caption, pixel_size=10, style='History.Icon.TButton',
                                   command=action).pack(fill='both', expand=True)
                    label = ttk.Label(body, text=note.get('text', ''), wraplength=450, justify='left')
                    label.pack(side='left', anchor='n', fill='x', expand=True)
                    body.bind('<Configure>', lambda event, target=label: target.configure(wraplength=max(100, event.width - 48)))

    def make_group(self, parent, key, caption, bold=False, indent=0):
        group = ttk.Frame(parent)
        group.pack(fill='x', padx=(indent, 0), pady=3)
        state_key = (self.guid, *key)
        label = ttk.Label(group, foreground=theme.GOLD if bold else theme.TEXT,
                          font=('Montserrat', 9, 'bold') if bold else ('Montserrat', 9),
                          cursor='hand2', takefocus=True)
        label.pack(fill='x')
        body = ttk.Frame(group)
        def update():
            closed = self.collapsed.get(state_key, False)
            label.configure(text=('[+] ' if closed else '[-] ') + caption)
            body.pack_forget() if closed else body.pack(fill='x')
        def toggle(_=None):
            self.collapsed[state_key] = not self.collapsed.get(state_key, False)
            update()
            return 'break'
        for event in ('<Button-1>', '<Return>', '<space>'):
            label.bind(event, toggle)
        self.groups[key] = (label, body, toggle)
        update()
        return body
