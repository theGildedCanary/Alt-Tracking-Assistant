from widgets import Button, Section
"""Character-specific profession dashboard, backed by GUID selections."""

import copy
import sqlite3
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont

import db
import theme
import roster_format
from profession_art import NativeProfessionBar

STATE_KEY = "profession_dashboard"
SLOTS = ("primary", "secondary", "archaeology", "fishing", "cooking")
EXPANSIONS = ("Midnight", "Khaz Algar", "Dragon Isles", "Shadowlands", "Kul Tiran",
              "Legion", "Draenor", "Pandaria", "Cataclysm", "Northrend", "Outland", "Classic")
PROFESSION_GROUPS = {
    "Primary": {171: "Alchemy", 164: "Blacksmithing", 333: "Enchanting", 202: "Engineering",
                773: "Inscription", 755: "Jewelcrafting", 165: "Leatherworking", 197: "Tailoring"},
    "Secondary": {182: "Herbalism", 186: "Mining", 393: "Skinning"},
    "Tertiary": {794: "Archaeology", 185: "Cooking", 356: "Fishing"},
}


def profession_group(slot, profession):
    for group, professions in PROFESSION_GROUPS.items():
        if str(profession.get("skillLineID")) in {str(key) for key in professions} or profession.get("name") in professions.values():
            return group
    return "Tertiary" if slot in ("archaeology", "cooking", "fishing") else "Primary"


def normalize_state(raw):
    result, seen = [], set()
    for entry in raw if isinstance(raw, list) else []:
        if not isinstance(entry, dict) or not isinstance(entry.get("guid"), str) or entry["guid"] in seen:
            continue
        selected = entry.get("professions")
        selected = selected if isinstance(selected, list) else []
        result.append({"guid": entry["guid"], "professions": list(dict.fromkeys(
            value for value in selected if isinstance(value, str)))})
        seen.add(entry["guid"])
    return result


def profession_key(slot, profession):
    return str(profession.get("skillLineID") or slot)


def learned_professions(record):
    professions = record.get("professions")
    professions = professions if isinstance(professions, dict) else {}
    return [(slot, value) for slot in SLOTS if isinstance((value := professions.get(slot)), dict)
            and isinstance(value.get("name"), str) and value["name"]]


def progress_tiers(slot, profession):
    values = profession.get("expansions")
    values = values if isinstance(values, list) else []
    tiers = [tier for tier in values if isinstance(tier, dict)
             and isinstance(tier.get("maxSkillLevel"), (int, float)) and tier["maxSkillLevel"] > 0]
    maximum = profession.get("maxSkillLevel")
    if not tiers and slot == "archaeology" and isinstance(maximum, (int, float)) and maximum > 0:
        tiers = [{"name": "Overall skill", "skillLevel": profession.get("skillLevel", 0),
                  "maxSkillLevel": profession["maxSkillLevel"]}]

    def order(tier):
        name = tier.get("name") if isinstance(tier.get("name"), str) else ""
        if "Zandalari" in name:
            return 4
        return next((index for index, title in enumerate(EXPANSIONS) if title in name), len(EXPANSIONS))
    return sorted(tiers, key=order)


class ScrollArea(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner = ttk.Frame(self.canvas)
        window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda _: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfigure(window, width=event.width))
        self.bind_all("<MouseWheel>", self._wheel, add="+")

    def _wheel(self, event):
        if self.winfo_ismapped() and str(event.widget).startswith(str(self)):
            self.canvas.yview_scroll(-3 if event.delta > 0 else 3, "units")


class SpacedHeading(tk.Canvas):
    """Clickable, keyboard-accessible heading with two-point letter spacing."""
    def __init__(self, parent, font, colors, command=None):
        super().__init__(parent, width=1, height=font.metrics("linespace") + 18, highlightthickness=1 if command else 0,
                         highlightbackground=colors["border"], highlightcolor=colors["text"],
                         bg=colors["control"], takefocus=bool(command), cursor="hand2" if command else "")
        self.font, self.colors, self.command = font, colors, command
        self.text = ""
        self.bind("<Configure>", lambda _: self.draw())
        if command:
            self.bind("<Button-1>", lambda _: (self.focus_set(), self.invoke()))
            self.bind("<Return>", lambda _: self.invoke())
            self.bind("<space>", lambda _: self.invoke())
            self.bind("<Enter>", lambda _: self.configure(bg=colors["hover"]))
            self.bind("<Leave>", lambda _: self.configure(bg=colors["control"]))

    def invoke(self):
        if self.command:
            self.command()

    def set_text(self, text):
        self.text = text.upper()
        self.draw()

    def draw(self):
        self.delete("all")
        if self.colors["background"] != theme.UI_THEMES["Light Mode"]["background"]:
            from pathlib import Path
            from PIL import Image, ImageTk, ImageDraw
            width, height = max(1, self.winfo_width()), int(self.cget("height"))
            if not hasattr(self, "_panel_texture"):
                with Image.open(Path(theme.__file__).parent / "assets" / "theme" / "PanelBackground.png") as image:
                    self._panel_texture = Image.blend(image.convert("RGB"), Image.new("RGB", image.size, theme.PANEL), .55)
            panel = Image.new("RGBA", (width, height))
            for x in range(0, width, 256):
                panel.paste(self._panel_texture, (x, 0))
            mask = Image.new("L", panel.size)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, width-1, height-1), radius=5, fill=255)
            panel.putalpha(mask)
            ImageDraw.Draw(panel).rounded_rectangle((0, 0, width-1, height-1), radius=5, outline=self.colors["border"])
            self._panel_photo = ImageTk.PhotoImage(panel, master=self)
            self.create_image(0, 0, anchor="nw", image=self._panel_photo)
        spacing = self.winfo_fpixels("2p")
        length = sum(self.font.measure(ch) for ch in self.text) + spacing * max(0, len(self.text) - 1)
        x = max(8, (self.winfo_width() - length) / 2)
        for char in self.text:
            width = self.font.measure(char)
            self.create_text(x + width / 2, int(self.cget("height")) / 2,
                             text=char, fill=theme.GOLD if self.colors["background"] != theme.UI_THEMES["Light Mode"]["background"] else self.colors["text"], font=self.font)
            x += width + spacing


class ProfessionsTab(ttk.Frame):
    def __init__(self, parent, state=None, on_save=None, ui_theme="Light Mode", fmt=None):
        super().__init__(parent, padding=10)
        self.state = normalize_state(state)
        self.on_save = on_save
        self.records = {}
        self.expanded = set()
        self.mode = ui_theme
        self.fmt = roster_format.normalize(fmt)
        self._make_fonts()
        self.status = tk.StringVar()
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)
        sidebar = ttk.Frame(self, width=310)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        sidebar.grid_propagate(False)
        sidebar.columnconfigure(0, weight=1)
        sidebar.rowconfigure(5, weight=1)
        ttk.Label(sidebar, text="Add character").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))
        self.choice = tk.StringVar()
        self.picker = ttk.Combobox(sidebar, textvariable=self.choice, state="readonly", width=30)
        self.picker.grid(row=1, column=0, sticky="ew")
        self.add_button = Button(sidebar, text="Add", command=self.add_character)
        self.add_button.grid(row=1, column=1, padx=(6, 0))
        ttk.Label(sidebar, textvariable=self.status, wraplength=300).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=6)
        ttk.Separator(sidebar).grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        self.sidebar = ScrollArea(sidebar)
        self.sidebar.grid(row=5, column=0, columnspan=2, sticky="nsew")
        ttk.Separator(self, orient="vertical").grid(row=0, column=1, sticky="ns", padx=(0, 10))
        self.details = ScrollArea(self)
        self.details.grid(row=0, column=2, sticky="nsew")
        self.set_theme(ui_theme)

    def set_theme(self, mode):
        self.mode = mode
        colors = theme.UI_THEMES[mode]
        self._style_checkboxes(colors)
        for area in (self.sidebar, self.details):
            area.canvas.configure(background=colors["background"])
        self.render()

    def _style_checkboxes(self, colors):
        size = max(16, round(self.winfo_fpixels("12p")))
        label_gap = round(self.winfo_fpixels("5p"))
        gold = theme.GOLD
        self.checkbox_images = []
        for checked in (False, True):
            image = tk.PhotoImage(master=self, width=size + label_gap, height=size)
            image.put(colors["background"], to=(1, 1, size - 1, size - 1))
            for rectangle in ((1, 1, size - 1, 2), (1, size - 2, size - 1, size - 1),
                              (1, 1, 2, size - 1), (size - 2, 1, size - 1, size - 1)):
                image.put(gold, to=rectangle)
            if checked:
                # Draw a tick rather than the platform's filled square or X.
                points = ((.25, .50), (.43, .68), (.76, .30))
                for start, end in zip(points, points[1:]):
                    x1, y1 = (round(value * size) for value in start)
                    x2, y2 = (round(value * size) for value in end)
                    steps = max(abs(x2 - x1), abs(y2 - y1))
                    for step in range(steps + 1):
                        x = round(x1 + (x2 - x1) * step / steps)
                        y = round(y1 + (y2 - y1) * step / steps)
                        image.put(gold, to=(x, y, x + 1, y + 2))
            self.checkbox_images.append(image)
        style = ttk.Style(self)
        element = f"ProfessionGold{self.checkbox_images[0]}.indicator"
        style.element_create(element, "image", self.checkbox_images[0],
                             ("selected", self.checkbox_images[1]), sticky="")
        layout = copy.deepcopy(style.layout("TCheckbutton"))
        def replace(items):
            for index, (name, options) in enumerate(items):
                if name.endswith(".indicator"):
                    items[index] = (element, options)
                if "children" in options:
                    replace(options["children"])
        replace(layout)
        style.layout("Professions.TCheckbutton", layout)

    def _make_fonts(self):
        settings = self.fmt["font"]
        family = settings["family"]
        if family not in tkfont.families(self):
            family = tkfont.nametofont("TkDefaultFont").actual("family")
        self.body_font = tkfont.Font(root=self, family=family, size=settings["bodySize"],
                                     weight="bold" if settings["bold"] else "normal")
        self.title_font = tkfont.Font(root=self, family=family, size=settings["titleSize"],
                                      weight="bold" if settings["titleBold"] else "normal")
        style = ttk.Style(self)
        style.configure("Professions.TLabel", font=self.body_font)
        style.configure("Professions.TCheckbutton", font=self.body_font)
        style.configure("Professions.TButton", font=self.title_font)
        style.configure("Professions.TLabelframe.Label", font=self.title_font)

    def set_format(self, fmt):
        self.fmt = roster_format.normalize(fmt)
        self._make_fonts()
        self.render()

    def _apply_fonts(self, widget):
        for child in widget.winfo_children():
            if isinstance(child, ttk.Label):
                child.configure(style="Professions.TLabel")
            elif isinstance(child, ttk.Checkbutton):
                child.configure(style="Professions.TCheckbutton")
            elif isinstance(child, ttk.Button):
                child.configure(style="Order.TButton" if getattr(child, "square", False) else "TButton")
            elif isinstance(child, ttk.Combobox):
                child.configure(font=self.body_font)
            elif isinstance(child, tk.Label):
                child.configure(font=self.title_font)
            self._apply_fonts(child)

    def load(self, characters):
        self.records = {record["guid"]: record for record in characters if isinstance(record.get("guid"), str)}
        self.render()

    def _save_state(self, state):
        state = normalize_state(state)
        try:
            if self.on_save:
                self.on_save(state)
        except (OSError, ValueError, sqlite3.Error) as error:
            self.status.set(f"Could not save: {error}")
            self.render()
            return
        self.state = state
        self.status.set("")
        self.render()

    def add_character(self):
        guid = self.choices.get(self.choice.get())
        if guid and not any(entry["guid"] == guid for entry in self.state):
            self._save_state(self.state + [{"guid": guid, "professions": []}])

    def remove_character(self, guid):
        self.expanded = {key for key in self.expanded if key[0] != guid}
        self._save_state([entry for entry in self.state if entry["guid"] != guid])

    def select_profession(self, guid, key, selected):
        if not selected:
            self.expanded.discard((guid, key))
        state = copy.deepcopy(self.state)
        for entry in state:
            if entry["guid"] == guid:
                entry["professions"] = [value for value in entry["professions"] if value != key]
                if selected:
                    entry["professions"].append(key)
        self._save_state(state)

    def render(self):
        colors = theme.UI_THEMES[self.mode]
        added = {entry["guid"] for entry in self.state}
        self.choices = {}
        for guid, record in self.records.items():
            if guid in added:
                continue
            label = f"{record.get('name') or 'Unknown'} - {record.get('realm') or 'Unknown realm'}"
            unique_label, suffix = label, 2
            while unique_label in self.choices:
                unique_label = f"{label} ({suffix})"
                suffix += 1
            self.choices[unique_label] = guid
        labels = sorted(self.choices, key=str.casefold)
        self.picker.configure(values=labels)
        if self.choice.get() not in self.choices:
            self.choice.set(labels[0] if labels else "")
        self.add_button.configure(state="normal" if labels else "disabled")
        for area in (self.sidebar, self.details):
            for child in area.inner.winfo_children():
                child.destroy()
        selected = {group: [] for group in PROFESSION_GROUPS}
        for entry in self.state:
            guid = entry["guid"]
            record = self.records.get(guid)
            name = (record.get("name") or "Unknown") if record else "Character unavailable"
            header = tk.Frame(self.sidebar.inner, bg=colors["selected"])
            header.pack(fill="x", pady=(0, 4))
            Button(header, text="x", width=3, command=lambda guid=guid: self.remove_character(guid)).pack(side="right", padx=4)
            character_heading = SpacedHeading(header, self.title_font, {**colors, "control": colors["selected"]})
            character_heading.set_text(name)
            character_heading.pack(side="left", fill="x", expand=True, padx=6, pady=2)
            if not record:
                ttk.Label(self.sidebar.inner, text="Not in the current roster.").pack(anchor="w", pady=(0, 10))
                continue
            professions = learned_professions(record)
            if not professions:
                ttk.Label(self.sidebar.inner, text="No recorded professions. Rescan in game.").pack(anchor="w", pady=(0, 10))
            for slot, profession in professions:
                key = profession_key(slot, profession)
                var = tk.BooleanVar(value=key in entry["professions"])
                ttk.Checkbutton(self.sidebar.inner, text=profession["name"], variable=var,
                    command=lambda guid=guid, key=key, var=var: self.select_profession(guid, key, var.get())).pack(anchor="w", padx=10, pady=2)
                if var.get():
                    selected[profession_group(slot, profession)].append((guid, key, name, slot, profession))
            ttk.Separator(self.sidebar.inner).pack(fill="x", pady=10)
        if not any(selected.values()):
            message = ("Choose a character from the roster using the selector on the left and click Add. "
                       "Then check the professions beneath that character’s name to track their expansion progress." if not self.state else
                       "No professions are currently being tracked. Check a profession beneath an added character’s name on the left to start tracking.")
            ttk.Label(self.details.inner, text=message,
                      wraplength=500).pack(anchor="w", padx=12, pady=12)
        else:
            for group, cards in selected.items():
                section = Section(self.details.inner, text=group, padding=10, style="Professions.TLabelframe")
                section.pack(fill="x", pady=(0, 12))
                for args in cards:
                    self._card(section, *args)
                if not cards:
                    ttk.Label(section, text=f"No {group.lower()} professions are currently being tracked.").pack(anchor="w")
        self._apply_fonts(self)

    def _card(self, parent, guid, key, name, slot, profession):
        card = ttk.Frame(parent, padding=(0, 0, 0, 10))
        card.pack(fill="x")
        identity = (guid, key)
        body = ttk.Frame(card, padding=(10, 6))
        def toggle():
            if identity in self.expanded:
                self.expanded.remove(identity)
            else:
                self.expanded.add(identity)
            show()
        heading = SpacedHeading(card, self.title_font, theme.UI_THEMES[self.mode], toggle)
        heading.pack(fill="x")
        def show():
            opened = identity in self.expanded
            heading.set_text(("-  " if opened else "+  ") + profession["name"] + " - " + name)
            if opened:
                body.pack(fill="x")
            else:
                body.pack_forget()
        for tier in progress_tiers(slot, profession):
            height = max(26, self.body_font.metrics("linespace") + 12)
            bar = NativeProfessionBar(body, profession, tier, height, self.body_font,
                                      theme.UI_THEMES[self.mode]["background"])
            bar.pack(fill="x", pady=4)
        if not body.winfo_children():
            ttk.Label(body, text="Expansion progress is not recorded yet. Open this profession in game, rescan, then /reload.",
                      wraplength=500).pack(anchor="w")
        show()
