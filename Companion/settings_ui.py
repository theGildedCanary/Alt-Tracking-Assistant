"""Settings tab: Main Selection, Tracking and Formatting pages, chosen from a list on the left."""

import copy
import tkinter as tk
from tkinter import ttk

import settings_sync as ss
from format_ui import FormatPanel, RosterPanel
from platform_support import wheel_units

NONE_LABEL = "(none)"
COLUMNS = 4


class ScrollFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner = ttk.Frame(self.canvas, padding=12)
        window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda _: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(window, width=e.width))
        self.bind_all("<MouseWheel>", self._on_wheel, add="+")

    def _on_wheel(self, event):
        if self.winfo_ismapped() and str(event.widget).startswith(str(self.canvas)):
            self.canvas.yview_scroll(wheel_units(event.delta), "units")


PAGES = ("Main Selection", "Tracking", "Roster", "Formatting")


class SettingsTab(ttk.Frame):
    def __init__(
            self, parent, on_save, on_revert, on_format_change, fmt,
            on_theme_change, ui_theme,
            on_tracking_change=None,
    ):
        super().__init__(parent)
        self.on_save = on_save
        self.on_revert = on_revert
        self.on_tracking_change = on_tracking_change
        self.characters = []
        self.settings = ss.normalize({})
        self.dirty = False
        self.loaded = False
        self.baseline = copy.deepcopy(self.settings)
        self.conflicts = []
        self.status = tk.StringVar()

        nav = ttk.Frame(self, padding=(8, 8))
        nav.pack(side="left", fill="y")
        ttk.Separator(self, orient="vertical").pack(side="left", fill="y")
        content = ttk.Frame(self)
        content.pack(side="left", fill="both", expand=True)

        self.bar = ttk.Frame(content, padding=(8, 6))
        ttk.Button(self.bar, text="Save to addon", command=self._save).pack(side="left")
        ttk.Button(self.bar, text="Revert", command=self._revert).pack(side="left", padx=6)
        ttk.Label(self.bar, textvariable=self.status).pack(side="left", padx=10)

        self.holder = ttk.Frame(content)
        self.holder.pack(side="bottom", fill="both", expand=True)
        self.pages = {}
        for name in PAGES:
            self.pages[name] = ScrollFrame(self.holder)
        fmt = copy.deepcopy(fmt)
        self.roster_panel = RosterPanel(self.pages["Roster"].inner, on_format_change, fmt)
        self.roster_panel.pack(fill="both", expand=True)
        self.format_panel = FormatPanel(self.pages["Formatting"].inner, on_format_change, fmt)
        self.format_panel.pack(fill="both", expand=True)

        self.page_var = tk.StringVar(value=PAGES[0])
        for name in PAGES:
            ttk.Radiobutton(
                nav, text=name, value=name, variable=self.page_var, style="Toolbutton", width=16,
                command=self._show_page,
            ).pack(fill="x", pady=2)

        ttk.Separator(nav).pack(fill="x", pady=(16, 8))
        ttk.Label(nav, text="Appearance").pack(anchor="w")

        self.ui_theme_var = tk.StringVar(value=ui_theme)
        theme_picker = ttk.Combobox(
            nav,
            textvariable=self.ui_theme_var,
            values=("Light Mode", "Dark Mode"),
            state="readonly",
            width=14,
        )
        theme_picker.pack(fill="x", pady=(4, 0))
        theme_picker.bind(
            "<<ComboboxSelected>>",
            lambda _: on_theme_change(self.ui_theme_var.get()),
        )
        
        self._show_page()

    def _show_page(self):
        name = self.page_var.get()
        for page in self.pages.values():
            page.pack_forget()
        self.pages[name].pack(fill="both", expand=True)
        if name != "Main Selection":
            self.bar.pack_forget()
        else:
            self.bar.pack(fill="x", before=self.holder)

        if name == "Formatting":
            self.format_panel._build_expansions()
        self.update_idletasks()
        canvas = self.pages[ name ].canvas
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.yview_moveto(0)

    def load(self, characters, settings, pending):
        """Show settings from the addon. Unsaved edits are kept when new data arrives."""
        self.characters = characters
        if self.dirty and self.loaded:
            self.settings, conflicts = ss.merge_refresh(self.baseline, self.settings, settings)
            self.conflicts = sorted(set(self.conflicts + conflicts))
        else:
            self.settings = copy.deepcopy(settings)
            self.conflicts = []
        self.baseline = copy.deepcopy(settings)
        self.loaded = True
        if self.conflicts:
            self.status.set("Addon settings changed too. Your edits were kept; Save to use them or Revert to use addon settings.")
        elif self.dirty:
            self.status.set("Unsaved changes kept; updated addon settings imported.")
        else:
            self.status.set("Saved changes are waiting for /reload in game." if pending else "")
        self._build()

    def _revert(self):
        self.dirty = False
        self.loaded = False
        self.status.set("Changes discarded.")
        self.on_revert()

    def _save(self):
        try:
            count = self.on_save(self.settings)
        except OSError as error:
            self.status.set(f"Could not save: {error}")
            return
        self.dirty = False
        self.baseline = copy.deepcopy(self.settings)
        self.conflicts = []
        if count:
            self.status.set("Saved. Type /reload in game (or log out) to apply the changes.")
        else:
            self.status.set("Saved in the app, but the addon folder was not found.")

    def _touch(self):
        self.dirty = True
        self.status.set("Unsaved changes.")
        if self.on_tracking_change:
            self.on_tracking_change()

    def _labels(self, slot_classes, faction):
        entries = []
        for record in self.characters:
            if slot_classes and record.get("classFile") not in slot_classes:
                continue
            if faction and record.get("faction") != faction:
                continue
            entries.append((f"{record.get('name') or 'Unknown'} - {record.get('realm') or 'Unknown Realm'}", record["guid"]))
        return sorted(entries, key=lambda e: e[0].lower())

    def _section(self, page, title):
        box = ttk.LabelFrame(self.pages[page].inner, text=title, padding=10)
        box.pack(fill="x", pady=(0, 12))
        return box

    def _build(self):
        for page in ("Main Selection", "Tracking"):
            for child in self.pages[page].inner.winfo_children():
                child.destroy()
        expansion_page = ttk.LabelFrame(self.pages["Tracking"].inner, text="Expansions", padding=10)
        expansion_page.pack(fill="both", expand=True)
        self.tracking_pages = {"Expansions": expansion_page}
        mains = self.settings["characterMains"]
        known = {r["guid"]: f"{r.get('name') or 'Unknown'} - {r.get('realm') or 'Unknown Realm'}" for r in self.characters}

        box = self._section("Main Selection", "Character Mains")
        self._mode_picker(box, "Main mode:", ss.CHARACTER_MODES, "characterMode", row=0)
        true_row = ttk.Frame(box)
        true_row.grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 2))
        enabled = tk.BooleanVar(value=mains["trueMainEnabled"])

        def toggle_true_main():
            mains["trueMainEnabled"] = enabled.get()
            self._touch()

        ttk.Checkbutton(true_row, text="True main:", variable=enabled, command=toggle_true_main).pack(side="left")
        self._picker(true_row, "trueMain", self._labels(None, None), known).pack(side="left", padx=8)

        slots_frame = ttk.Frame(box)
        slots_frame.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self._slot_grid(slots_frame, ss.character_slots(mains["characterMode"]), known)

        box = self._section("Main Selection", "Armor Mains")
        self._mode_picker(box, "Armor mode:", ss.ARMOR_MODES, "armorMode", row=0)
        slots_frame = ttk.Frame(box)
        slots_frame.grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self._slot_grid(slots_frame, ss.armor_slots(mains["armorMode"]), known)

        box = self.tracking_pages["Expansions"]
        footer = ttk.Frame(box, padding=(0, 12, 0, 0))
        footer.pack(side="bottom", fill="x")
        actions = ttk.Frame(footer)
        actions.pack(side="right", anchor="e")
        ttk.Button(actions, text="Save to addon", command=self._save).pack(side="left", padx=(0, 6))
        ttk.Button(actions, text="Revert", command=self._revert).pack(side="left")
        ttk.Label(footer, textvariable=self.status, wraplength=480).pack(side="left", fill="x", expand=True, padx=(0, 12))
        options = ttk.Frame(box)
        options.pack(side="top", fill="both", expand=True)
        box = options
        for exp_key, exp_title, checks in ss.TRACKERS:
            ttk.Label(box, text=exp_title, font=("TkDefaultFont", 9, "bold")).pack(anchor="w", pady=(6, 2))
            row = ttk.Frame(box)
            row.pack(fill="x")
            for index, (check_id, label) in enumerate(checks):
                current = self.settings["trackedItems"].get(exp_key, {}).get(check_id, True)
                var = tk.BooleanVar(value=current)

                def toggle(exp=exp_key, check=check_id, var=var):
                    self.settings["trackedItems"].setdefault(exp, {})[check] = var.get()
                    self._touch()

                ttk.Checkbutton(row, text=label, variable=var, command=toggle).grid(
                    row=index // COLUMNS, column=index % COLUMNS, sticky="w", padx=(0, 18), pady=1
                )

    def _mode_picker(self, parent, caption, modes, field, row):
        mains = self.settings["characterMains"]
        ttk.Label(parent, text=caption).grid(row=row, column=0, sticky="w")
        labels = [label for _, label in modes]
        current = next((label for mode, label in modes if mode == mains[field]), labels[0])
        box = ttk.Combobox(parent, values=labels, state="readonly", width=16)
        box.set(current)
        box.grid(row=row, column=1, sticky="w", padx=8)

        def changed(_):
            mains[field] = next(mode for mode, label in modes if label == box.get())
            self._touch()
            self._build()

        box.bind("<<ComboboxSelected>>", changed)

    def _picker(self, parent, slot_id, entries, known):
        selections = self.settings["characterMains"]["selections"]
        labels = [NONE_LABEL] + [label for label, _ in entries]
        guid_for = dict(entries)
        selected = selections.get(slot_id)
        box = ttk.Combobox(parent, values=labels, state="readonly", width=34)
        box.set(known.get(selected, NONE_LABEL) if selected in known else (NONE_LABEL if not selected else "(unknown character)"))

        def changed(_):
            guid = guid_for.get(box.get())
            if guid:
                selections[slot_id] = guid
            else:
                selections.pop(slot_id, None)
            self._touch()

        box.bind("<<ComboboxSelected>>", changed)
        return box

    def _slot_grid(self, parent, slots, known):
        for row, (slot_id, label, classes, faction) in enumerate(slots):
            ttk.Label(parent, text=label, width=18).grid(row=row, column=0, sticky="w", pady=1)
            self._picker(parent, slot_id, self._labels(classes, faction), known).grid(row=row, column=1, sticky="w")
