"""Settings tab: character mains, expansion tracking toggles and (later) formatting."""

import copy
import tkinter as tk
from tkinter import ttk

import settings_sync as ss

NONE_LABEL = "(none)"
COLUMNS = 4


class SettingsTab(ttk.Frame):
    def __init__(self, parent, on_save, on_revert):
        super().__init__(parent)
        self.on_save = on_save
        self.on_revert = on_revert
        self.characters = []
        self.settings = ss.normalize({})
        self.dirty = False
        self.loaded = False
        self.status = tk.StringVar()

        bar = ttk.Frame(self, padding=(8, 6))
        bar.pack(fill="x")
        ttk.Button(bar, text="Save to addon", command=self._save).pack(side="left")
        ttk.Button(bar, text="Revert", command=self._revert).pack(side="left", padx=6)
        ttk.Label(bar, textvariable=self.status).pack(side="left", padx=10)

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(body, highlightthickness=0)
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=self.canvas.yview)
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
            self.canvas.yview_scroll(-3 * (event.delta // 120 or (1 if event.delta > 0 else -1)), "units")

    def load(self, characters, settings, pending):
        """Show settings from the addon. Unsaved edits are kept when new data arrives."""
        self.characters = characters
        if self.dirty and self.loaded:
            return
        self.settings = copy.deepcopy(settings)
        self.loaded = True
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
        if count:
            self.status.set("Saved. Type /reload in game (or log out) to apply the changes.")
        else:
            self.status.set("Saved in the app, but the addon folder was not found.")

    def _touch(self):
        self.dirty = True
        self.status.set("Unsaved changes.")

    def _labels(self, slot_classes, faction):
        entries = []
        for record in self.characters:
            if slot_classes and record.get("classFile") not in slot_classes:
                continue
            if faction and record.get("faction") != faction:
                continue
            entries.append((f"{record.get('name') or 'Unknown'} - {record.get('realm') or 'Unknown Realm'}", record["guid"]))
        return sorted(entries, key=lambda e: e[0].lower())

    def _section(self, title):
        box = ttk.LabelFrame(self.inner, text=title, padding=10)
        box.pack(fill="x", pady=(0, 12))
        return box

    def _build(self):
        for child in self.inner.winfo_children():
            child.destroy()
        mains = self.settings["characterMains"]
        known = {r["guid"]: f"{r.get('name') or 'Unknown'} - {r.get('realm') or 'Unknown Realm'}" for r in self.characters}

        box = self._section("Character Mains")
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

        box = self._section("Armor Mains")
        self._mode_picker(box, "Armor mode:", ss.ARMOR_MODES, "armorMode", row=0)
        slots_frame = ttk.Frame(box)
        slots_frame.grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self._slot_grid(slots_frame, ss.armor_slots(mains["armorMode"]), known)

        box = self._section("Expansion Tracking")
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

        box = self._section("Formatting")
        ttk.Label(box, text="Formatting options will be added here.").pack(anchor="w")

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
