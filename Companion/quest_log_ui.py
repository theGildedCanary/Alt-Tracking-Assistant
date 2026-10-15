from widgets import WoWScrollbar, bind_scroll_content
"""Quest Log character list and task detail panel."""
import copy
from datetime import datetime
import tkinter as tk
from tkinter import ttk

import quest_log as model
import theme
import window_position
from widgets import Button, IconButton, Section
from professions_ui import ScrollArea
from grid import RosterGrid, GridStyle
from quest_log_grid import build_grid


class QuestLogTab(ttk.Frame):
    def __init__(self, parent, state=None, on_save=None, on_refresh=None, mode="WoW Mode", popup_positions=None, on_position_save=None, action_needed=None, on_action_needed=None):
        super().__init__(parent, padding=10)
        self.action_needed = dict(action_needed or {})
        self.on_action_needed = on_action_needed or (lambda guid, needed: None)
        self.state = copy.deepcopy(state or {})
        self.on_save = on_save or (lambda state: None)
        self.records, self.choices = {}, {}
        self.selected = None
        self.popup_positions = copy.deepcopy(popup_positions or {})
        self.on_position_save = on_position_save or (lambda positions: None)
        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(0, 8))
        self.choice = tk.StringVar()
        self.picker = ttk.Combobox(bar, textvariable=self.choice, state="readonly", width=45)
        self.picker.pack(side="left")
        Button(bar, text="Add character", command=self.add_character).pack(side="left", padx=6)
        Button(bar, text="Refresh", command=on_refresh or (lambda: None)).pack(side="left")
        Button(bar, text="Order characters", command=self.order_characters_popup).pack(side='left', padx=6)
        Button(bar, text='Add quest', command=lambda: self.editor(True, global_add=True)).pack(side='left', padx=6)
        Button(bar, text='Add to do', command=lambda: self.editor(False, global_add=True)).pack(side='left')
        self.notice = tk.StringVar(value="Choose only the characters you want to track.")
        ttk.Label(self, textvariable=self.notice, wraplength=1050).pack(fill="x", pady=(0, 8))
        ttk.Label(self, text="○ Not picked up   ☐ To do pending / Picked up   ☑ Complete   ? Awaiting scan   — Not assigned",
                  wraplength=1100).pack(anchor='w', pady=(0, 8))
        ttk.Label(self, text='Click a quest heading or task name to choose its tracking characters.',
                  wraplength=1100).pack(anchor='w', pady=(0, 8))
        self.split = ttk.Panedwindow(self, orient="horizontal")
        self.split.pack(fill="both", expand=True)
        sidebar = ttk.Frame(self.split)
        self.split.add(sidebar, weight=3)
        self.list = RosterGrid(sidebar)
        self.list.pack(fill="both", expand=True)
        self.list.left.configure(cursor='')
        self.list.left.bind('<Button-1>', self.delete_character_cell)
        self.list.left.bind('<Return>', lambda _: self.open_character(self.selected))
        self.list.left.bind('<Escape>', lambda _: self.close_details())
        self.list.top.configure(cursor='hand2')
        self.list.top.bind('<Button-1>', self.select_quest_heading)
        self.list.body.bind('<Button-1>', self.toggle_todo_cell)
        self.details = ScrollArea(self.split)
        self.detail_split = self.split
        self.panel_open = False
        self.row_guids = []
        self.set_theme(mode)
        self.render()

    def set_theme(self, mode):
        self.colors = theme.UI_THEMES['WoW Mode']
        self.details.canvas.configure(background=self.colors['background'])
        style = ttk.Style(self)
        root = self.winfo_toplevel()
        if 'Quest.assignmentGap' not in style.element_names():
            root._quest_assignment_gap = tk.PhotoImage(master=root, width=round(self.winfo_fpixels('5p')), height=1)
            style.element_create('Quest.assignmentGap', 'image', root._quest_assignment_gap, sticky='')
        def space_indicator(layout):
            result = []
            for element, options in layout:
                options = dict(options)
                if 'children' in options:
                    options['children'] = space_indicator(options['children'])
                result.append((element, options))
                if element.endswith('indicator'):
                    result.append(('Quest.assignmentGap', {'side': 'left', 'sticky': ''}))
            return result
        style.layout('Quest.TCheckbutton', space_indicator(style.layout('TCheckbutton')))
        if 'Quest.completionIndicator' not in style.element_names():
            from PIL import Image, ImageDraw, ImageTk
            size = max(14, round(self.winfo_fpixels('10p')))
            images = []
            for selected in (False, True):
                image = Image.new('RGBA', (size * 3, size * 3))
                draw = ImageDraw.Draw(image)
                draw.rectangle((3, 3, size * 3 - 4, size * 3 - 4), fill=theme.PANEL, outline=theme.GOLD, width=3)
                if selected:
                    draw.line([(size * .6, size * 1.5), (size * 1.2, size * 2.1), (size * 2.4, size * .8)], fill=theme.GOLD, width=5)
                images.append(ImageTk.PhotoImage(image.resize((size, size), Image.Resampling.LANCZOS), master=root))
            root._quest_completion_images = images
            style.element_create('Quest.completionIndicator', 'image', images[0], ('selected', images[1]), sticky='')
        def square_indicator(layout):
            return [('Quest.completionIndicator' if name.endswith('indicator') else name,
                     {key: square_indicator(value) if key == 'children' else value for key, value in options.items()})
                    for name, options in layout]
        style.layout('Quest.Completion.TCheckbutton', square_indicator(style.layout('Quest.TCheckbutton')))
        style.configure('Quest.Completion.TCheckbutton', background=self.colors['background'], foreground=theme.TEXT)
        style.map('Quest.Completion.TCheckbutton', background=[('active', self.colors['hover'])])
        for name in ('TFrame', 'TLabel', 'TLabelframe', 'TEntry', 'TCombobox', 'TPanedwindow', 'TButton', 'TCheckbutton', 'Vertical.TScrollbar', 'Horizontal.TScrollbar'):
            style.configure('Quest.' + name, background=self.colors['background'],
                            foreground=theme.TEXT, fieldbackground=theme.PANEL,
                            troughcolor=theme.PANEL_ALT, arrowcolor=theme.GOLD, bordercolor=theme.DIVIDER)
            style.map('Quest.' + name, background=[('active', self.colors['hover'])],
                      fieldbackground=[('readonly', theme.PANEL)],
                      foreground=[('readonly', theme.TEXT), ('disabled', theme.MUTED_TEXT)])
        style.configure('Quest.Icon.TButton', padding=round(self.winfo_fpixels('3p')), width=0,
                        background=theme.PANEL, foreground=theme.GOLD)
        style.map('Quest.Icon.TButton', background=[('active', self.colors['hover'])])
        self.brown_widgets(self)

    def brown_widgets(self, widget):
        name = widget.winfo_class()
        if name == 'TScrollbar':
            widget.configure(style='Quest.' + str(widget.cget('orient')).title() + '.TScrollbar')
        elif name in ('TFrame', 'TLabel', 'TLabelframe', 'TEntry', 'TCombobox', 'TPanedwindow', 'TButton', 'TCheckbutton'):
            widget.configure(style='Quest.' + name)
            if getattr(widget, '_quest_completion', False):
                widget.configure(style='Quest.Completion.TCheckbutton')
            if hasattr(widget, '_quest_class'):
                class_style = widget._quest_class + '.Quest.TCheckbutton'
                color = theme.CLASS_COLORS.get(widget._quest_class, theme.TEXT)
                style = ttk.Style(self)
                style.configure(class_style, foreground=color, background=theme.PANEL)
                style.map(class_style, foreground=[('disabled', color), ('active', color)],
                          background=[('active', theme.PANEL)])
                widget.configure(style=class_style)
            if isinstance(widget, Button):
                widget.caption_color = theme.GOLD
                widget.refresh_art()
                if isinstance(widget, IconButton):
                    widget.configure(style='Quest.CompactIcon.TButton' if widget.pixel_size else 'Quest.Icon.TButton')
                    if widget.pixel_size:
                        compact_style = ttk.Style(self)
                        compact_style.configure('Quest.CompactIcon.TButton', padding=0, anchor='center')
                        root = self.winfo_toplevel()
                        if 'Quest.compactButton' not in compact_style.element_names() and hasattr(root, '_ata_theme_images'):
                            images = root._ata_theme_images
                            compact_style.element_create('Quest.compactButton', 'image', images[2],
                                                         ('pressed', images[4]), ('active', images[3]),
                                                         border=3, width=1, height=1, sticky='nsew')
                        compact_style.layout('Quest.CompactIcon.TButton', [('Quest.compactButton', {
                            'sticky': 'nsew', 'children': [('Button.label', {'sticky': ''})]})])
            if name == 'TCombobox':
                popup = self.tk.call('ttk::combobox::PopdownWindow', str(widget))
                self.tk.call(str(popup) + '.f.l', 'configure', '-background', theme.PANEL,
                             '-foreground', theme.TEXT, '-selectbackground', self.colors['selected'],
                             '-selectforeground', theme.TEXT)
        elif isinstance(widget, (tk.Canvas, tk.Text, tk.Toplevel)):
            widget.configure(background=theme.PANEL)
            if isinstance(widget, tk.Text):
                widget.configure(foreground=theme.TEXT, insertbackground=theme.TEXT,
                                 selectbackground=self.colors['selected'], selectforeground=theme.TEXT)
        for child in widget.winfo_children():
            self.brown_widgets(child)

    def remember_popup(self, dialog):
        saved = window_position.capture(dialog)
        kind = getattr(dialog, '_quest_popup_kind', None)
        if kind and saved and self.popup_positions.get(kind) != saved:
            self.popup_positions[kind] = saved
            self.on_position_save(copy.deepcopy(self.popup_positions))

    def close_popup(self, dialog):
        self.remember_popup(dialog)
        dialog.destroy()

    def prepare_popup(self, dialog, kind):
        dialog._quest_popup_kind = kind
        dialog.update_idletasks()
        window_position.center_popup(dialog)
        dialog.protocol('WM_DELETE_WINDOW', lambda: self.close_popup(dialog))
        dialog.bind('<Escape>', lambda _: self.close_popup(dialog))
        dialog.bind('<Configure>', lambda event: self.remember_popup(dialog)
                    if event.widget is dialog and dialog.winfo_ismapped() else None)

    def load(self, records):
        self.records = {r['guid']: r for r in records}
        self.choices = {}
        for record in records:
            if record['guid'] in self.state:
                continue
            label = f"{record.get('name')} — {record.get('realm')}"
            if label in self.choices:
                label += f" · Account {record.get('account') or 'Unknown'}"
            base, number = label, 2
            while label in self.choices:
                label = f'{base} ({number})'
                number += 1
            self.choices[label] = record['guid']
        self.picker.configure(values=list(self.choices))
        if self.choice.get() not in self.choices:
            self.choice.set(next(iter(self.choices), ""))
        if model.apply_resets(self.state, self.records):
            self.commit()
        self.render()

    def commit(self, refresh=True):
        try:
            count = self.on_save(copy.deepcopy(self.state))
            self.notice.set("Saved. Quest changes need /reload in WoW, then /reload or logout to save scans and Refresh here."
                            if count else "Saved locally. Select your WoW folder on Export to send quest IDs to the addon.")
        except OSError as error:
            self.notice.set(f"Saved locally; addon sync failed: {error}")
        if refresh:
            self.load(list(self.records.values()))
        else:
            self.render_list()

    def order_characters_popup(self):
        dialog = tk.Toplevel(self)
        dialog.title('Order Quest Log characters')
        dialog.transient(self.winfo_toplevel())
        dialog.geometry('420x440')
        dialog.grab_set()
        frame = ttk.Frame(dialog, padding=16)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Select a character and move them up or down.').pack(anchor='w', pady=(0, 10))
        order = list(self.state)
        area = ttk.Frame(frame)
        area.pack(fill='both', expand=True)
        listing = tk.Listbox(area, bg=theme.PANEL, fg=theme.TEXT, selectbackground=theme.GOLD_DARK,
                             selectforeground=theme.TEXT, highlightthickness=0, exportselection=False)
        scrollbar = WoWScrollbar(area, command=listing.yview)
        scrollbar.pack(side='right', fill='y')
        listing.configure(yscrollcommand=scrollbar.set)
        listing.pack(fill='both', expand=True)
        def refresh(index=0):
            listing.delete(0, 'end')
            for guid in order:
                record = self.records.get(guid, {})
                listing.insert('end', f"{record.get('name', 'Unavailable character')} - {record.get('level') or '?'}")
            if order:
                listing.selection_set(index)
                listing.see(index)
        def move(delta):
            selection = listing.curselection()
            if not selection:
                return
            index = selection[0]
            target = index + delta
            if 0 <= target < len(order):
                order[index], order[target] = order[target], order[index]
                refresh(target)
        controls = ttk.Frame(frame)
        controls.pack(fill='x', pady=(12, 0))
        Button(controls, text='▲', command=lambda: move(-1)).pack(side='left', padx=4)
        Button(controls, text='▼', command=lambda: move(1)).pack(side='left', padx=4)
        def save():
            self.state = {guid: self.state[guid] for guid in order}
            self.close_popup(dialog)
            self.commit()
        Button(controls, text='Save', command=save).pack(side='right', padx=4)
        Button(controls, text='Cancel', command=lambda: self.close_popup(dialog)).pack(side='right')
        refresh()
        self.brown_widgets(dialog)
        self.prepare_popup(dialog, 'character_order')
        return dialog

    def add_character(self):
        guid = self.choices.get(self.choice.get())
        if guid:
            self.state[guid] = []
            self.commit()

    def remove_character(self):
        if self.selected in self.state:
            del self.state[self.selected]
            self.close_details()
            self.commit()

    def delete_character_cell(self, event):
        x = self.list.left.canvasx(event.x)
        y = self.list.left.canvasy(event.y)
        row = int(y // self.list.style.row_height)
        center = self.list.style.row_height / 2
        if 3 <= x <= 19 and abs(y % self.list.style.row_height - center) <= 8 and 0 <= row < len(self.row_guids):
            guid = self.row_guids[row]
            del self.state[guid]
            if self.selected == guid:
                self.close_details()
            self.commit()

    def select_character(self, _=None):
        if _ is None:
            return
        self.list.left.focus_set()
        # Only the character-name column opens the side panel.
        columns = self.list._visible_data[0] if self.list._visible_data else []
        if not columns or self.list.left.canvasx(_.x) >= columns[0].width:
            return
        index = int(self.list.left.canvasy(_.y) // self.list.style.row_height)
        if 0 <= index < len(self.row_guids):
            self.open_character(self.row_guids[index])

    def open_character(self, guid):
        if guid not in self.state and guid not in self.records:
            return
        self.selected = guid
        if not self.panel_open:
            self.detail_split.add(self.details, weight=2)
            self.panel_open = True
        if hasattr(self.details, 'show_character'):
            self.render_details()
        else:
            self.render()

    def select_quest_heading(self, event):
        if event.y < self.list.band_height:
            return
        x = self.list.top.canvasx(event.x)
        offset = 0
        for column in self.columns:
            if column.frozen:
                continue
            if offset <= x < offset + column.width:
                quest_id = getattr(column, 'quest_id', None)
                task_key = getattr(column, 'task_key', None)
                if quest_id or task_key:
                    matches = [t for tasks in self.state.values() for t in tasks
                               if (model.assignment_key(t) == task_key if task_key else t.get('questID') == quest_id)]
                    if matches:
                        task = next((t for t in matches if t.get('title') == column.title), matches[0])
                        self.assignment_popup(task, column.title)
                        return
                return
            offset += column.width

    def assignment_popup(self, task, name=None):
        dialog = tk.Toplevel(self)
        dialog.title('Edit task and characters')
        dialog.transient(self.winfo_toplevel())
        dialog.geometry('560x720')
        dialog.minsize(520, 620)
        dialog.grab_set()
        dialog.bind('<Escape>', lambda _: dialog.destroy())
        frame = ttk.Frame(dialog, padding=16)
        frame.pack(fill='both', expand=True)
        name = name or next((model.task_name(task, self.records.get(guid, {}))
                             for guid, tasks in self.state.items() if task in tasks), model.task_name(task, {}))
        ttk.Label(frame, text=name, font=('Montserrat', 12, 'bold'), wraplength=470).pack(anchor='w', pady=(0, 8))
        editor = ttk.Frame(frame)
        editor.pack(fill='x', pady=(0, 10))
        editor.columnconfigure(1, weight=1)
        quest = bool(task.get('questID'))
        fields = {}
        for row, (key, label, value) in enumerate([
                ('title', 'Nickname' if quest else 'Title', task.get('title', '')),
                ('priority', 'Priority', task.get('priority', 'Normal'))]):
            fields[key] = tk.StringVar(value=value)
            ttk.Label(editor, text=label).grid(row=row, column=0, sticky='w', padx=(0, 10), pady=5)
            if key == 'title':
                widget = ttk.Entry(editor, textvariable=fields[key])
            else:
                values = (('Auto', 'None', 'Daily', 'Weekly') if quest else ('None', 'Daily', 'Weekly', 'Custom')) if key == 'reset' else ('Low', 'Normal', 'High')
                widget = ttk.Combobox(editor, textvariable=fields[key], state='readonly', values=values)
            widget.grid(row=row, column=1, sticky='ew', pady=5)
        if quest:
            fields['questIDs'] = tk.StringVar(value=', '.join(map(str, model.quest_ids(task))))
            ttk.Label(editor, text='Quest IDs').grid(row=2, column=0, sticky='w', padx=(0, 10), pady=5)
            ttk.Entry(editor, textvariable=fields['questIDs']).grid(row=2, column=1, sticky='ew', pady=5)
        reset_days = self.reset_day_selector(editor, task, row=5)
        ttk.Label(editor, text='Selected days reset at 11 a.m. EDT. Leave all unchecked for no reset.').grid(row=3, column=0, columnspan=2, pady=5)
        ttk.Label(editor, text='Notes / steps').grid(row=4, column=0, sticky='nw', padx=(0, 10))
        notes = tk.Text(editor, height=4, width=36, wrap='word')
        notes.grid(row=4, column=1, sticky='ew')
        notes.insert('1.0', task.get('notes', ''))
        error = tk.StringVar()
        ttk.Label(frame, textvariable=error, wraplength=470).pack(anchor='w')
        ttk.Label(frame, text='Select the characters tracking this task. Unchecking removes their assignment.',
                  wraplength=470).pack(anchor='w', pady=(0, 10))
        area = ttk.Frame(frame)
        area.pack(fill='both', expand=True)
        canvas = tk.Canvas(area, background=theme.PANEL, highlightthickness=0)
        scrollbar = WoWScrollbar(area, command=canvas.yview)
        scrollbar.pack(side='right', fill='y')
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side='left', fill='both', expand=True)
        inner = ttk.Frame(canvas)
        window = canvas.create_window(0, 0, window=inner, anchor='nw')
        bind_scroll_content(canvas, inner, window)
        def wheel(event):
            canvas.yview_scroll(-3 if event.delta > 0 else 3, 'units')
            return 'break'
        canvas.bind('<MouseWheel>', wheel)
        assigned = model.assigned_characters(self.state, task)
        selections, labels = {}, set()
        for guid in self.state:
            record = self.records.get(guid, {})
            label = f"{record.get('name', 'Unavailable character')} - {record.get('level') or '?'}"
            base, number = label, 2
            while label in labels:
                label = f"{base} · Account {record.get('account') or 'Unknown'} ({number})"
                number += 1
            labels.add(label)
            selections[guid] = tk.BooleanVar(value=guid in assigned)
            toggle = ttk.Checkbutton(inner, text=label, variable=selections[guid])
            toggle._quest_class = record.get('classFile') or 'Unknown'
            toggle.pack(anchor='w', fill='x', padx=8, pady=6)
            toggle.bind('<MouseWheel>', wheel)
        def save():
            try:
                updated = model.new_task(fields['title'].get(), fields['questIDs'].get() if quest else None, None,
                                         notes.get('1.0', 'end'), fields['priority'].get(), [day for day, value in reset_days.items() if value.get()])
            except ValueError as exc:
                error.set(str(exc))
                return
            for field in ('achievementID', 'itemID'):
                if task.get(field): updated[field] = task[field]
            key = model.assignment_key(task)
            model.assign_characters(self.state, task, [guid for guid, var in selections.items() if var.get()])
            for guid, tasks in self.state.items():
                for assigned_task in tasks:
                    if model.assignment_key(assigned_task) != key:
                        continue
                    changed_reset = assigned_task.get('reset') != updated.get('reset') or assigned_task.get('resetDays') != updated.get('resetDays')
                    for field in ('title', 'questID', 'questIDs', 'reset', 'resetMode', 'resetDays', 'priority', 'notes', 'changedAt'):
                        if field in updated:
                            assigned_task[field] = updated[field]
                    if not quest and changed_reset:
                        model.set_status(assigned_task, assigned_task.get('status', 'Pending'), self.records.get(guid, {}))
            self.close_popup(dialog)
            self.commit()
        controls = ttk.Frame(frame)
        controls.pack(side='bottom', fill='x', pady=(12, 0), before=frame.winfo_children()[0])
        Button(controls, text='Save', command=save).pack(side='right', padx=6)
        Button(controls, text='Cancel', command=lambda: self.close_popup(dialog)).pack(side='right')
        if quest:
            Button(controls, text='Delete', command=lambda: self.delete_quest(task, dialog)).pack(side='left')
        self.brown_widgets(dialog)
        self.prepare_popup(dialog, 'assignments')
        return dialog

    def close_details(self):
        if self.panel_open:
            self.detail_split.forget(self.details)
        self.panel_open = False
        self.selected = None
        self.render_list()

    def render_list(self):
        xview, yview = self.list.body.xview(), self.list.body.yview()
        self.columns, self.rows, self.row_guids = build_grid(self.state, self.records, self.selected)
        self.list.set_data(self.columns, self.rows, GridStyle())
        if xview:
            self.list.body.xview_moveto(xview[0])
        if yview:
            self.list.body.yview_moveto(yview[0])

    def render(self):
        self.render_list()
        self.render_details()
        self.brown_widgets(self)

    def render_details(self):
        if not self.panel_open:
            return
        if hasattr(self.details, 'show_character'):
            self.details.show_character(self.selected, self.records.get(self.selected, {}))
            if not self.details.quest_visible():
                return
        inner = self.details.inner
        record = self.records.get(self.selected, {})
        tasks = self.state.get(self.selected, [])
        signature = self.detail_signature()
        if getattr(self, '_detail_signature', None) == signature and inner.winfo_children():
            return
        self._detail_signature = signature
        self._status_widgets = []
        for child in inner.winfo_children():
            child.destroy()
        if self.selected not in self.state and self.selected not in self.records:
            ttk.Label(inner, text="Add a character, then click their name to open the Quest Log.", wraplength=430).pack(padx=12, pady=20)
            return
        record = self.records.get(self.selected, {})
        stamp = (record.get('questLog') or {}).get('scannedAt')
        text = f"Quest scan: {datetime.fromtimestamp(stamp):%b %d, %Y %H:%M}" if stamp else "Awaiting character scan in WoW."
        ttk.Label(inner, text=text).pack(anchor="w", padx=8)
        ttk.Label(inner, text='Click a quest or to do name to choose its characters.', wraplength=480).pack(anchor='w', padx=8, pady=4)
        actions = ttk.Frame(inner)
        actions.pack(fill="x", padx=8, pady=8)
        Button(actions, text="+ Quest", command=lambda: self.editor(True)).pack(side="left")
        Button(actions, text="+ Task", command=lambda: self.editor(False)).pack(side="left", padx=6)
        self.action_needed_var = tk.BooleanVar(value=bool(self.action_needed.get(self.selected)))
        ttk.Checkbutton(actions, text='Action Needed', variable=self.action_needed_var,
                        command=self.toggle_action_needed).pack(side='left', padx=(12, 0))
        tasks = self.state.get(self.selected, [])
        for title, automatic in (("Auto Tracking", True), ("To do list", False)):
            section = Section(inner, text=title, padding=8, colors=self.colors)
            section.pack(fill="x", padx=8, pady=6)
            group = [task for task in tasks if bool(model.is_automatic(task)) == automatic]
            if not group:
                ttk.Label(section, text="No tasks added.").pack(anchor="w")
            for task in group:
                card = ttk.Frame(section, padding=(0, 6))
                card.pack(fill="x")
                data = model.snapshot(task, record)
                name = model.task_name(task, record)
                status = model.task_status(task, record)
                heading = ttk.Frame(card)
                heading.pack(fill='x', pady=(0, 4))
                heading.columnconfigure(1, weight=1)
                var = tk.BooleanVar(value=status == 'Completed')
                checkbox = ttk.Checkbutton(heading, variable=var,
                                           command=lambda t=task, v=var: self.change_status(t, 'Completed' if v.get() else 'Pending'),
                                           state='disabled' if model.is_automatic(task) else 'normal')
                checkbox._quest_completion = True
                checkbox.grid(row=0, column=0, sticky='w', padx=(0, round(self.winfo_fpixels('3p'))))
                title = ttk.Label(heading, text=model.task_caption(task, record), wraplength=360, font=("Montserrat", 10, "bold"), cursor='hand2', takefocus=True)
                title.grid(row=0, column=1, sticky='w')
                buttons = ttk.Frame(heading)
                buttons.grid(row=0, column=2, sticky='ne', padx=(8, 0))
                from tkinter import font as tkfont
                line_height = tkfont.Font(root=self, font=('Montserrat', 10, 'bold')).metrics('linespace')
                for icon, caption, action in (
                        ('pencil', 'Edit', lambda t=task: self.editor(bool(t.get('questID')), t)),
                        ('user', 'Characters', lambda t=task: self.assignment_popup(t)),
                        ('x', 'Delete', lambda t=task: self.delete_task(t))):
                    square = ttk.Frame(buttons, width=line_height, height=line_height)
                    square.pack(side='left', padx=2)
                    square.pack_propagate(False)
                    IconButton(square, icon=icon, text=caption, pixel_size=max(8, line_height-6), command=action).pack(fill='both', expand=True)
                heading.bind('<Configure>', lambda event, label=title, actions=buttons: label.configure(wraplength=max(100, event.width - actions.winfo_reqwidth() - 12)))
                title.bind('<Button-1>', lambda _, t=task: self.assignment_popup(t))
                title.bind('<Return>', lambda _, t=task: self.assignment_popup(t))
                title.bind('<space>', lambda _, t=task: self.assignment_popup(t))
                self._status_widgets.append((task, var, title))
                if task.get('notes'):
                    ttk.Label(card, text=task['notes'], wraplength=480).pack(anchor="w", pady=4)
        self.brown_widgets(inner)

    def detail_signature(self):
        record = self.records.get(self.selected, {})
        tasks = self.state.get(self.selected, [])
        return (self.selected, repr(record), repr(tasks), repr(self.colors),
                tuple(model.task_status(task, record) for task in tasks))

    def update_status_widgets(self, guid):
        if guid != self.selected or not self.panel_open:
            return
        record = self.records.get(guid, {})
        for task, variable, label in getattr(self, '_status_widgets', []):
            if label.winfo_exists():
                status = model.task_status(task, record)
                variable.set(status == 'Completed')
                label.configure(text=model.task_caption(task, record))
        self._detail_signature = self.detail_signature()

    def toggle_todo_cell(self, event):
        row = int(self.list.body.canvasy(event.y) // self.list.style.row_height)
        if not 0 <= row < len(self.row_guids):
            return
        x = self.list.body.canvasx(event.x)
        offset = 0
        for column in self.columns:
            if column.frozen:
                continue
            if offset <= x < offset + column.width:
                key = getattr(column, 'task_key', None)
                if key is None:
                    return
                guid = self.row_guids[row]
                task = next((task for task in self.state[guid]
                             if not model.is_automatic(task) and model.assignment_key(task) == key), None)
                if task is not None:
                    record = self.records.get(guid, {})
                    status = 'Pending' if model.task_status(task, record) == 'Completed' else 'Completed'
                    model.set_status(task, status, record)
                    self.update_status_widgets(guid)
                    self.commit(refresh=False)
                return
            offset += column.width

    def change_status(self, task, status):
        model.set_status(task, status, self.records.get(self.selected, {}))
        self.update_status_widgets(self.selected)
        self.commit(refresh=False)

    def delete_quest(self, task, dialog):
        key = model.assignment_key(task)
        for tasks in self.state.values():
            tasks[:] = [item for item in tasks if model.assignment_key(item) != key]
        self.close_popup(dialog)
        self.commit()

    def delete_task(self, task):
        guid = self.selected
        dialog = tk.Toplevel(self)
        dialog.title('Remove or delete to do')
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        frame = ttk.Frame(dialog, padding=16)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Remove this assignment, or delete this to do from every character?', wraplength=360).pack(pady=(0, 12))
        def finish(everywhere):
            key = model.assignment_key(task)
            for character, tasks in self.state.items():
                if everywhere or character == guid:
                    tasks[:] = [item for item in tasks if model.assignment_key(item) != key]
            dialog.destroy()
            self.commit()
        Button(frame, text='Remove from character', command=lambda: finish(False)).pack(fill='x', pady=3)
        Button(frame, text='Delete to do', command=lambda: finish(True)).pack(fill='x', pady=3)
        Button(frame, text='Cancel', command=dialog.destroy).pack(fill='x', pady=3)
        self.brown_widgets(dialog)
        window_position.center_popup(dialog)
        return dialog

    def editor(self, quest, task=None, global_add=False):
        guid = self.selected
        dialog = tk.Toplevel(self)
        dialog.title("Edit task" if task else "Add quest" if quest else "Add to do")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.bind('<Escape>', lambda _: dialog.destroy())
        frame = ttk.Frame(dialog, padding=16)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)
        fields = {}
        rows = [("title", "Nickname" if quest else 'Title', task.get('title', '') if task else '')]
        if quest:
            rows.insert(0, ('questID', 'Quest IDs', ', '.join(map(str, model.quest_ids(task))) if task else ''))
        rows.append(('priority', 'Priority', task.get('priority', 'Normal') if task else 'Normal'))
        for row, (key, label, value) in enumerate(rows):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=5)
            fields[key] = tk.StringVar(value=value)
            if key in ('reset', 'priority'):
                widget = ttk.Combobox(frame, textvariable=fields[key], state='readonly', values=(('Auto', 'None', 'Daily', 'Weekly') if quest else ('None', 'Daily', 'Weekly', 'Custom')) if key == 'reset' else ('Low', 'Normal', 'High'))
            else:
                widget = ttk.Entry(frame, textvariable=fields[key], width=42)
            widget.grid(row=row, column=1, sticky="ew", pady=5)
        row = len(rows)
        reset_days = self.reset_day_selector(frame, task, row=row)
        row += 1
        ttk.Label(frame, text='Selected days reset at 11 a.m. EDT. Leave all unchecked for no reset.').grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        ttk.Label(frame, text="Notes / steps").grid(row=row, column=0, sticky='nw', pady=5)
        notes = tk.Text(frame, width=42, height=6, wrap='word')
        notes.grid(row=row, column=1, sticky='ew', pady=5)
        notes.insert('1.0', task.get('notes', '') if task else '')
        error = tk.StringVar()
        ttk.Label(frame, textvariable=error, wraplength=430).grid(row=row+1, column=0, columnspan=2)
        selections = {}
        if global_add:
            area = ScrollArea(frame)
            area.configure(height=160)
            area.grid(row=row+2, column=0, columnspan=2, sticky='nsew', pady=8)
            ttk.Label(area.inner, text='Assign to characters:').pack(anchor='w')
            for character in self.state:
                record = self.records.get(character, {})
                selections[character] = tk.BooleanVar(value=False)
                toggle = ttk.Checkbutton(area.inner,
                                         text=f"{record.get('name', 'Unavailable character')} - {record.get('level') or '?'}",
                                         variable=selections[character])
                toggle._quest_class = record.get('classFile') or 'Unknown'
                toggle.pack(anchor='w', pady=4)

        def save():
            try:
                updated = model.new_task(fields['title'].get(), fields['questID'].get().strip() if quest else None,
                                         None, notes.get('1.0', 'end'), fields['priority'].get(), [day for day, value in reset_days.items() if value.get()])
                targets = [character for character, value in selections.items() if value.get()] if global_add else [guid]
                if global_add and not targets:
                    raise ValueError('Select at least one tracked character. Add characters to the Quest Log first if needed.')
                if quest and any(t is not task and model.assignment_key(t) == model.assignment_key(updated) for character in targets for t in self.state.get(character, [])):
                    raise ValueError('This quest is already assigned to this character.')
            except ValueError as exc:
                error.set(str(exc))
                return
            if task:
                for field in ('achievementID', 'itemID'):
                    if task.get(field): updated[field] = task[field]
                same_reset = task.get('reset') == updated['reset'] and task.get('resetDays') == updated.get('resetDays')
                updated.update(id=task['id'], status=task.get('status', 'Pending'), changedAt=updated['changedAt'])
                if same_reset:
                    updated['resetAt'] = task.get('resetAt')
                task.update(updated)
                if not quest and not same_reset:
                    model.set_status(task, task['status'], self.records.get(guid, {}))
            elif global_add:
                for character in targets:
                    self.state[character].append(copy.deepcopy(updated))
            else:
                self.state.setdefault(guid, []).append(updated)
            self.close_popup(dialog)
            self.commit()
        controls = ttk.Frame(frame)
        controls.grid(row=row+3 if global_add else row+2, column=0, columnspan=2, sticky='e', pady=8)
        Button(controls, text="Save", command=save).pack(side='left', padx=6)
        Button(controls, text="Cancel", command=lambda: self.close_popup(dialog)).pack(side='left')
        if quest and task:
            Button(controls, text='Delete', command=lambda: self.delete_quest(task, dialog)).pack(side='left', padx=6)
        self.brown_widgets(dialog)
        self.prepare_popup(dialog, 'task_editor')

    def reset_day_selector(self, parent, task, row):
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, columnspan=2, sticky='w', pady=5)
        ttk.Label(frame, text='Reset:').pack(anchor='w')
        days = ttk.Frame(frame)
        days.pack(anchor='w')
        selected = (task or {}).get('resetDays')
        if selected is None:
            reset = model.task_reset(task, self.records.get(self.selected, {})) if task else 'None'
            selected = list(range(1, 8)) if reset == 'Daily' else [2] if reset == 'Weekly' else []
        values = {}
        for day, name in enumerate(('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'), 1):
            values[day] = tk.BooleanVar(value=day in selected)
            toggle = ttk.Checkbutton(days, text=name, variable=values[day])
            toggle._reset_day = day
            toggle.pack(side='left')
        return values

    def toggle_action_needed(self):
        guid = self.selected
        if not guid:
            return
        needed = self.action_needed_var.get()
        self.on_action_needed(guid, needed)
        if needed:
            self.action_needed[guid] = True
        else:
            self.action_needed.pop(guid, None)

    def apply_due_resets(self, now=None):
        if not model.apply_resets(self.state, self.records, now):
            return False
        self.update_status_widgets(self.selected)
        self.commit(refresh=False)
        return True
