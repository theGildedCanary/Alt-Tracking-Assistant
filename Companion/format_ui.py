from widgets import Button, Section
"""Formatting page of the Settings tab: every visual option of the Companion roster."""

import copy
import tkinter as tk
from tkinter import colorchooser, ttk
from tkinter import font as tkfont

import roster_format as rf

COLOR_LABELS = [
    ("text", "Cell text"),
    ("background", "Grid background"),
    ("stripe", "Alternate row background"),
    ("gridLine", "Grid lines"),
    ("separator", "Frozen column line"),
    ("headerBg", "Column header background"),
    ("baseTitle", "Column titles"),
    ("trackerTitle", "Tracker titles"),
    ("mainName", "Main character name"),
    ("mainMark", "Main marker"),
    ("factionText", "Faction letter"),
    ("genderText", "Gender letter"),
    ("classText", "Class text (on class color)"),
]
ALIGN_LABELS = {"w": "Left", "center": "Center", "e": "Right"}
CLASS_NAMES = {
    "DEATHKNIGHT": "Death Knight", "DEMONHUNTER": "Demon Hunter", "DRUID": "Druid", "EVOKER": "Evoker",
    "HUNTER": "Hunter", "MAGE": "Mage", "MONK": "Monk", "PALADIN": "Paladin", "PRIEST": "Priest",
    "ROGUE": "Rogue", "SHAMAN": "Shaman", "WARLOCK": "Warlock", "WARRIOR": "Warrior",
}
EXPANSION_NAMES = {
    "darkmoonFaire": "Darkmoon Faire", "classic": "Classic", "cataclysm": "Cataclysm",
    "mistsOfPandaria": "Mists of Pandaria", "warlordsOfDraenor": "Warlords of Draenor", "legion": "Legion",
    "battleForAzeroth": "Battle for Azeroth", "shadowlands": "Shadowlands", "dragonflight": "Dragonflight",
    "theWarWithin": "The War Within", "midnight": "Midnight",
}


def _contrast(color):
    r, g, b = (int(color[i : i + 2], 16) for i in (1, 3, 5))
    return "#000000" if (r * 299 + g * 587 + b * 114) / 1000 > 140 else "#ffffff"


class FormatPanel(ttk.Frame):
    """Edits a roster format dict and reports each change through on_change(fmt)."""

    def __init__(self, parent, on_change, fmt):
        super().__init__(parent, padding=12)
        self.on_change = on_change
        self.fmt = fmt
        self._pending = None
        self._build()

    def load(self, fmt):
        self.fmt = copy.deepcopy(fmt)
        self._build()

    def _changed(self):
        if self._pending:
            self.after_cancel(self._pending)
        self._pending = self.after(250, self._emit)

    def _emit(self):
        self._pending = None
        self.on_change(copy.deepcopy(self.fmt))

    def _set(self, path, value):
        target = self.fmt
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        self._changed()

    def _get(self, path):
        target = self.fmt
        for key in path:
            target = target[key]
        return target

    def _check(self, parent, text, path):
        var = tk.BooleanVar(value=self._get(path))
        button = ttk.Checkbutton(parent, text=text, variable=var, command=lambda: self._set(path, var.get()))
        button._var = var
        return button

    def _number(self, parent, path, low, high, width=5):
        var = tk.StringVar(value=str(self._get(path)))

        def write(*_):
            try:
                self._set(path, max(low, min(high, int(var.get()))))
            except ValueError:
                pass

        var.trace_add("write", write)
        box = ttk.Spinbox(parent, from_=low, to=high, textvariable=var, width=width)
        box._var = var
        return box

    def _entry(self, parent, path, width=6):
        var = tk.StringVar(value=self._get(path))
        var.trace_add("write", lambda *_: self._set(path, var.get()))
        box = ttk.Entry(parent, textvariable=var, width=width)
        box._var = var
        return box

    def _main_marker_controls(self, parent):
        frame = ttk.Frame(parent)
        self._entry(frame, ("mainMark",)).pack(side="left")
        self._check(frame, "Italicize", ("italicMainRows",)).pack(
            side="left", padx=(8, 0)
        )
        return frame

    def _color(self, parent, path):
        frame = ttk.Frame(parent)
        current = self._get(path)
        value = tk.StringVar(value=current.upper())

        entry = ttk.Entry(frame, textvariable=value, width=9)
        entry.pack(side="left")

        button = tk.Button(
            frame,
            text="Pick",
            width=4,
            bg=current,
            fg=_contrast(current),
            activebackground=current,
            relief="groove",
        )
        button.pack(side="left", padx=(4, 0))

        def apply_color(color):
            color = color.lower()
            value.set(color.upper())
            button.configure(
                bg=color,
                fg=_contrast(color),
                activebackground=color,
            )
            self._set(path, color)

        def commit(event=None):
            color = value.get().strip()
            if rf.HEX.fullmatch(color):
                apply_color(color)
            else:
                value.set(self._get(path).upper())

        def pick():
            _, chosen = colorchooser.askcolor(
                color=self._get(path),
                parent=self,
                title="Choose a color",
            )
            if chosen:
                apply_color(chosen)

        entry.bind("<Return>", commit)
        entry.bind("<FocusOut>", commit)
        button.configure(command=pick)
        return frame

    def _section(self, title):
        box = Section(self, text=title, padding=10)
        box.pack(fill="x", pady=(0, 12))
        return box

    def _labelled_grid(self, box, items, per_row=2):
        """items: (label, widget_factory) pairs laid out in label/widget column pairs."""
        for index, (label, factory) in enumerate(items):
            row, column = divmod(index, per_row)
            ttk.Label(box, text=label).grid(row=row, column=column * 2, sticky="w", padx=(0, 8), pady=3)
            factory(box).grid(row=row, column=column * 2 + 1, sticky="w", padx=(0, 28), pady=3)

    def _build(self):
        for child in self.winfo_children():
            child.destroy()

        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 10))
        ttk.Label(top, text="Changes here apply to the Roster immediately and are not sent to the addon.").pack(
            side="left"
        )
        Button(top, text="Reset to defaults", command=self._reset).pack(side="right")

        families = sorted({f for f in tkfont.families(self) if not f.startswith("@")}, key=str.lower)
        if self.fmt["font"]["family"] not in families:
            families.append(self.fmt["font"]["family"])

        box = self._section("Font")
        family_var = tk.StringVar(value=self.fmt["font"]["family"])
        family = ttk.Combobox(box, values=families, textvariable=family_var, width=30)
        family.bind("<<ComboboxSelected>>", lambda _: self._set(("font", "family"), family_var.get()))
        family.bind("<FocusOut>", lambda _: self._set(("font", "family"), family_var.get()))
        family._var = family_var
        self._labelled_grid(
            box,
            [
                ("Font family", lambda p: family),
                ("Cell text size", lambda p: self._number(p, ("font", "bodySize"), 6, 24)),
                ("Title text size", lambda p: self._number(p, ("font", "titleSize"), 5, 20)),
                ("Title letter spacing (px)", lambda p: self._number(p, ("font", "titleSpacing"), 0, 10)),
                ("Date letter spacing (px)", lambda p: self._number(p, ("font", "dateSpacing"), 0, 10)),
            ],
        )
        flags = ttk.Frame(box)
        flags.grid(row=3, column=0, columnspan=4, sticky="w", pady=(6, 0))
        for text, path in (
            ("Bold cell text", ("font", "bold")),
            ("Bold titles", ("font", "titleBold")),
        ):
            self._check(flags, text, path).pack(side="left", padx=(0, 18))

        box = self._section("Layout")
        self._labelled_grid(
            box,
            [
                ("Row height (px)", lambda p: self._number(p, ("rowHeight",), 16, 60)),
                ("Completed tracker mark", lambda p: self._entry(p, ("mark",))),
                ("Main character marker", lambda p: self._main_marker_controls(p)),
            ],
        )
        flags = ttk.Frame(box)
        flags.grid(row=2, column=0, columnspan=4, sticky="w", pady=(6, 0))
        self._check(flags, "Alternate row shading", ("stripes",)).pack(side="left", padx=(0, 18))
        self._check(flags, "Vertical tracker titles", ("trackerTitlesVertical",)).pack(side="left", padx=(0, 18))

        box = self._section("Colors")
        self._labelled_grid(
            box, [(label, lambda p, k=key: self._color(p, ("colors", k))) for key, label in COLOR_LABELS]
        )

        box = self._section("Faction, gender, class and covenant")
        self._labelled_grid(
            box,
            [
                ("Alliance", lambda p: self._color(p, ("factionColors", "Alliance"))),
                ("Horde", lambda p: self._color(p, ("factionColors", "Horde"))),
                ("Male", lambda p: self._color(p, ("genderColors", "M"))),
                ("Female", lambda p: self._color(p, ("genderColors", "F"))),
            ],
        )
        ttk.Separator(box).grid(row=2, column=0, columnspan=4, sticky="ew", pady=8)
        class_frame = ttk.Frame(box)
        class_frame.grid(row=3, column=0, columnspan=4, sticky="w", pady=(6, 0))
        self._labelled_grid(
            class_frame,
            [
                (CLASS_NAMES.get(key, key.title()), lambda p, k=key: self._color(p, ("classColors", k)))
                for key in self.fmt["classColors"]
            ],
            per_row=3,
        )

        ttk.Separator(box).grid(row=4, column=0, columnspan=4, sticky="ew", pady=8)
        covenant_frame = ttk.Frame(box)
        covenant_frame.grid(row=5, column=0, columnspan=4, sticky="w")
        self._labelled_grid(covenant_frame, [
            (name, lambda p, key=key: self._color(p, ("covenantColors", key)))
            for key, name in (("1", "Kyrian"), ("2", "Venthyr"), ("3", "Night Fae"), ("4", "Necrolord"))
        ])

        self.expansions_box = self._section("Expansion tracker colors (header and completed cell shade / text)")
        self._build_expansions()

    def _build_expansions(self):
        box = self.expansions_box
        for child in box.winfo_children():
            child.destroy()
        for column, heading in enumerate(("Expansion", "Shade", "Text")):
            ttk.Label(box, text=heading).grid(row=0, column=column, sticky="w", padx=6)
        for index, expansion in enumerate(self.fmt["expansionOrder"]):
            row = index + 1
            ttk.Label(box, text=EXPANSION_NAMES.get(expansion, expansion)).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=2)
            self._color(box, ("expansionShade", expansion)).grid(row=row, column=1, padx=(0, 8), pady=2)
            self._color(box, ("expansionAccent", expansion)).grid(row=row, column=2, pady=2)
    def _build_columns(self):
        box = self.columns_box
        for child in box.winfo_children():
            child.destroy()
        for column, heading in enumerate(("", "Show", "Title", "Align", "Vertical", "Frozen", "Order")):
            ttk.Label(box, text=heading, font=(tkfont.nametofont("TkDefaultFont").actual("family"), 9, "bold")).grid(
                row=0, column=column, padx=6, sticky="w"
            )
        for index, spec in enumerate(self.fmt["columns"]):
            row = index + 1
            ttk.Label(box, text=spec["key"].upper()).grid(row=row, column=0, sticky="w", padx=6)
            self._check(box, "", ("columns", index, "visible")).grid(row=row, column=1)
            self._entry(box, ("columns", index, "title"), width=12).grid(row=row, column=2, padx=6, pady=2)
            align_var = tk.StringVar(value=ALIGN_LABELS[spec["align"]])
            align = ttk.Combobox(box, values=list(ALIGN_LABELS.values()), textvariable=align_var, state="readonly", width=8)
            align.bind(
                "<<ComboboxSelected>>",
                lambda _, i=index, v=align_var: self._set(
                    ("columns", i, "align"), next(k for k, label in ALIGN_LABELS.items() if label == v.get())
                ),
            )
            align._var = align_var
            align.grid(row=row, column=3, padx=6)
            self._check(box, "", ("columns", index, "vertical")).grid(row=row, column=4)
            self._check(box, "", ("columns", index, "frozen")).grid(row=row, column=5)
            arrows = ttk.Frame(box)
            arrows.grid(row=row, column=6, padx=6)
            Button(arrows, text="\u25b2", width=3, command=lambda i=index: self._move(i, -1)).pack(side="left")
            Button(arrows, text="\u25bc", width=3, command=lambda i=index: self._move(i, 1)).pack(side="left")
        ttk.Label(
            box,
            text="Frozen columns stay in place while the tracker columns scroll. Tracker columns always follow these.",
        ).grid(row=len(self.fmt["columns"]) + 1, column=0, columnspan=7, sticky="w", pady=(8, 0))

    def _move(self, index, step):
        target = index + step
        columns = self.fmt["columns"]
        if not 0 <= target < len(columns):
            return
        columns[index], columns[target] = columns[target], columns[index]
        self._build_columns()
        self._changed()

    def _reset(self):
        current = rf.defaults()
        for key in current:
            if key not in {"columns", "mainHighlight", "professionHighlight", "expansionOrder", "expansionTitles", "expansionVisible", "trackerColumns"}:
                self.fmt[key] = current[key]
        self._build()
        self._changed()


class RosterPanel(FormatPanel):
    """Roster behavior and columns, sharing state with the Formatting page."""

    def _build(self):
        for child in self.winfo_children():
            child.destroy()
        box = self._section("Highlights")
        self._check(box, "Profession Highlight", ("professionHighlight",)).pack(anchor="w")
        self._check(box, "Main Highlight", ("mainHighlight",)).pack(anchor="w", pady=(6, 0))
        self._check(box, "Italicize main character rows", ("italicMainRows",)).pack(anchor="w", pady=(6, 0))
        ttk.Label(box, text="Profession Highlight colors tracked professions gold. Main Highlight colors main names gold and bolds their rows.", wraplength=650).pack(anchor="w", pady=(8, 0))
        self.columns_box = self._section("Columns (order, titles, alignment)")
        self._build_columns()

        self.expansions_box = self._section("Expansions")
        self._build_expansions()
        self.trackers_box = self._section("Expansion trackers")
        self._build_trackers()

    def _build_expansions(self):
        box = self.expansions_box
        for child in box.winfo_children():
            child.destroy()
        for column, heading in enumerate(("Expansion", "Show", "Roster name", "Order")):
            ttk.Label(box, text=heading).grid(row=0, column=column, sticky="w", padx=6)
        for index, expansion in enumerate(self.fmt["expansionOrder"]):
            row = index + 1
            ttk.Label(box, text=EXPANSION_NAMES.get(expansion, expansion)).grid(row=row, column=0, sticky="w", padx=6, pady=2)
            self._check(box, "", ("expansionVisible", expansion)).grid(row=row, column=1, padx=6)
            self._entry(box, ("expansionTitles", expansion), width=28).grid(row=row, column=2, padx=6, pady=2)
            arrows = ttk.Frame(box)
            arrows.grid(row=row, column=3, padx=6)
            for step, label in ((-1, "\u25b2"), (1, "\u25bc")):
                Button(arrows, text=label, width=3, command=lambda i=index, s=step: self._move_expansion(i, s)).pack(side="left")

    def _move_expansion(self, index, step):
        order = self.fmt["expansionOrder"]
        target = index + step
        if 0 <= target < len(order):
            order[index], order[target] = order[target], order[index]
            self._build_expansions()
            self._build_trackers()
            self._changed()

    def _build_trackers(self):
        for child in self.trackers_box.winfo_children():
            child.destroy()
        ttk.Label(self.trackers_box, text="Rename, show or hide, and reorder trackers within each expansion.").pack(anchor="w", pady=(0, 8))
        self.tracker_boxes = {}
        for expansion in self.fmt["expansionOrder"]:
            box = Section(self.trackers_box, text=EXPANSION_NAMES.get(expansion, expansion), padding=8)
            box.pack(fill="x", pady=(0, 8))
            self.tracker_boxes[expansion] = box
            self._build_tracker_group(expansion)

    def _build_tracker_group(self, expansion):
        box = self.tracker_boxes[expansion]
        for child in box.winfo_children():
            child.destroy()
        for column, heading in enumerate(("Tracker", "Show", "Roster name", "Order")):
            ttk.Label(box, text=heading).grid(row=0, column=column, sticky="w", padx=6)
        specs = self.fmt["trackerColumns"][expansion]
        for index, spec in enumerate(specs):
            row = index + 1
            default = next(item for item in rf.TRACKER_COLUMNS[expansion] if item["key"] == spec["key"])
            ttk.Label(box, text=default["title"]).grid(row=row, column=0, sticky="w", padx=6, pady=2)
            self._check(box, "", ("trackerColumns", expansion, index, "visible")).grid(row=row, column=1, padx=6)
            self._entry(box, ("trackerColumns", expansion, index, "title"), width=28).grid(row=row, column=2, padx=6, pady=2)
            arrows = ttk.Frame(box)
            arrows.grid(row=row, column=3, padx=6)
            for step, label in ((-1, "\u25b2"), (1, "\u25bc")):
                Button(arrows, text=label, width=3,
                           state="normal" if 0 <= index + step < len(specs) else "disabled",
                           command=lambda e=expansion, i=index, s=step: self._move_tracker(e, i, s)).pack(side="left")

    def _move_tracker(self, expansion, index, step):
        specs = self.fmt["trackerColumns"][expansion]
        target = index + step
        if 0 <= target < len(specs):
            specs[index], specs[target] = specs[target], specs[index]
            self._build_tracker_group(expansion)
            self._changed()
