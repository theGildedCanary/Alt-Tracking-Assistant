"""Colors shared by the companion app, taken from the addon's UI/Theme.lua."""


def _hex(r, g, b):
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


TEXT = "#eee9dd"
MUTED_TEXT = "#b7b0a0"
PANEL = "#24211b"
PANEL_ALT = "#2b271f"
PANEL_BORDER = _hex(0.74, 0.53, 0.19)
DIVIDER = "#514737"
GOLD = _hex(0.94, 0.70, 0.25)
GOLD_DARK = _hex(0.50, 0.32, 0.10)
COMPLETED = _hex(0.30, 0.92, 0.20)
MUTED_YELLOW = "#8a7a2c"

FACTION_COLORS = {"Alliance": "#5b8fe0", "Horde": "#d9473f"}

CLASS_COLORS = {
    "DEATHKNIGHT": "#C41E3A",
    "DEMONHUNTER": "#A330C9",
    "DRUID": "#FF7C0A",
    "EVOKER": "#33937F",
    "HUNTER": "#AAD372",
    "MAGE": "#3FC7EB",
    "MONK": "#00FF98",
    "PALADIN": "#F48CBA",
    "PRIEST": "#FFFFFF",
    "ROGUE": "#FFF468",
    "SHAMAN": "#0070DD",
    "WARLOCK": "#8788EE",
    "WARRIOR": "#C69B6D",
}

# Dark header/background shade for each expansion's columns.
EXPANSION_COLORS = {
    "darkmoonFaire": _hex(53 / 255, 1 / 255, 33 / 255),
    "classic": _hex(70 / 255, 20 / 255, 59 / 255),
    "cataclysm": _hex(69 / 255, 55 / 255, 19 / 255),
    "mistsOfPandaria": _hex(0, 75 / 255, 62 / 255),
    "warlordsOfDraenor": _hex(70 / 255, 25 / 255, 20 / 255),
    "legion": _hex(10 / 255, 51 / 255, 20 / 255),
    "battleForAzeroth": _hex(24 / 255, 24 / 255, 84 / 255),
    "shadowlands": _hex(28 / 255, 72 / 255, 142 / 255),
    "dragonflight": _hex(4 / 255, 64 / 255, 74 / 255),
    "theWarWithin": _hex(121 / 255, 45 / 255, 11 / 255),
    "midnight": _hex(51 / 255, 30 / 255, 83 / 255),
}

# Bright accent for each expansion's text and completed marks.
EXPANSION_ACCENTS = {
    "battleForAzeroth": _hex(137 / 255, 174 / 255, 254 / 255),
    "darkmoonFaire": _hex(251 / 255, 132 / 255, 184 / 255),
    "legion": _hex(76 / 255, 1, 109 / 255),
    "warlordsOfDraenor": _hex(254 / 255, 90 / 255, 75 / 255),
    "mistsOfPandaria": _hex(75 / 255, 254 / 255, 192 / 255),
    "cataclysm": _hex(254 / 255, 249 / 255, 135 / 255),
    "classic": _hex(254 / 255, 135 / 255, 213 / 255),
    "shadowlands": _hex(79 / 255, 207 / 255, 254 / 255),
    "dragonflight": _hex(32 / 255, 252 / 255, 250 / 255),
    "theWarWithin": _hex(248 / 255, 149 / 255, 4 / 255),
    "midnight": _hex(236 / 255, 143 / 255, 248 / 255),
}

# Settings UI Dark and Light modes.
UI_THEMES = {
    "Light Mode": {
        "background": "#f2f2f2",
        "text": "#202020",
        "control": "#ffffff",
        "hover": "#e2e8f0",
        "selected": "#cce4ff",
        "border": "#b8b8b8",
        "disabled": "#777777",
    },
    "Dark Mode": {
        "background": "#171510",
        "text": TEXT,
        "control": PANEL,
        "hover": "#353025",
        "selected": "#55452b",
        "border": "#66563c",
        "disabled": "#8c8578",
    },
}
UI_THEMES["WoW Mode"] = dict(UI_THEMES["Dark Mode"])


def _art_styles(root, style, enabled):
    """Use the addon's tab art and subdued red action controls in ttk."""
    from pathlib import Path
    from PIL import Image, ImageTk, ImageDraw

    if not hasattr(root, "_ata_theme_images"):
        assets = Path(__file__).resolve().parent / "assets" / "theme"
        images = [ImageTk.PhotoImage(Image.open(assets / name), master=root)
                  for name in ("TabInactive.png", "TabActive.png")]
        for base in ((95, 10, 8), (125, 20, 12), (60, 8, 7), (43, 39, 32)):
            image = Image.new("RGBA", (128, 32))
            draw = ImageDraw.Draw(image)
            for y in range(32):
                shade = .65 + .45 * (1-y/31)
                draw.line((0, y, 127, y), fill=tuple(round(c*shade) for c in base))
            draw.rounded_rectangle((1, 1, 126, 30), radius=4, outline="#796447", width=1)
            draw.rounded_rectangle((3, 3, 124, 28), radius=3, outline="#241b13", width=1)
            mask = Image.new("L", image.size)
            ImageDraw.Draw(mask).rounded_rectangle((1, 1, 126, 30), radius=4, fill=255)
            image.putalpha(mask)
            images.append(ImageTk.PhotoImage(image, master=root))
        root._ata_theme_images = images
        style.element_create("ATA.tab", "image", images[0], ("selected", images[1]), border=6, sticky="nsew")
        style.element_create("ATA.button", "image", images[2], ("disabled", images[5]),
                             ("pressed", images[4]), ("active", images[3]), border=6, width=12, height=12, sticky="nsew")
    if not hasattr(root, "_ata_original_layouts"):
        root._ata_original_layouts = {name: style.layout(name) for name in ("TNotebook.Tab", "TButton")}
    for name, element, content in (("TNotebook.Tab", "ATA.tab", "Notebook.label"),
                                    ("TButton", "ATA.button", "Button.label")):
        if enabled:
            style.layout(name, [(element, {"sticky": "nsew", "children": [(content, {"sticky": "nsew"})]})])
            style.configure(name, padding=(14, 8), foreground=GOLD)
            style.map(name, foreground=[("disabled", "#8c8578"), ("selected", GOLD), ("!selected", MUTED_TEXT)] if name == "TNotebook.Tab"
                      else [("disabled", "#8c8578"), ("!disabled", GOLD)])
        else:
            style.layout(name, root._ata_original_layouts[name])
            style.configure(name, padding=(8, 4))

def apply_ui_theme(root, mode):
    from tkinter import ttk

    colors = UI_THEMES.get(mode, UI_THEMES["Light Mode"])
    style = ttk.Style(root)

    # "clam" lets us control colors consistently on Windows.
    if style.theme_use() != "clam":
        style.theme_use("clam")

    root.configure(background=colors["background"])

    style.configure(
        ".",
        background=colors["background"],
        foreground=colors["text"],
    )

    style.configure(
        "TLabel",
        background=colors["background"],
        foreground=colors["text"],
    )

    style.configure(
        "TLabelframe",
        background=colors["background"],
        foreground=colors["text"],
    )

    style.configure(
        "TLabelframe.Label",
        background=colors["background"],
        foreground=colors["text"],
    )

    for widget_style in ("TButton", "Toolbutton", "TNotebook.Tab"):
        style.configure(
            widget_style,
            background=colors["control"],
            foreground=colors["text"],
        )
        style.map(
            widget_style,
            background=[
                ("selected", colors["selected"]),
                ("active", colors["hover"]),
            ],
            foreground=[("disabled", colors["disabled"])],
        )

    for widget_style in ("TCheckbutton", "TRadiobutton"):
        style.map(
            widget_style,
            background=[("active", colors["hover"])],
            foreground=[("disabled", colors["disabled"])],
            indicatorbackground=[
                ("selected", colors["selected"]),
                ("!selected", colors["control"]),
            ],
        )

    for widget_style in ("TEntry", "TCombobox", "TSpinbox"):
        style.configure(
            widget_style,
            padding=(round(root.winfo_fpixels("2p")), 1, 1, 1),
            fieldbackground=colors["control"],
            foreground=colors["text"],
            insertcolor=colors["text"],
            arrowcolor=colors["text"],
        )
        style.map(
            widget_style,
            fieldbackground=[("readonly", colors["control"])],
            foreground=[
                ("disabled", colors["disabled"]),
                ("readonly", colors["text"]),
            ],
        )

    style.configure(
        "TScrollbar",
        background=colors["control"],
        troughcolor=colors["background"],
        arrowcolor=colors["text"],
    )
    style.configure("TSeparator", background=colors["border"])
    style.configure("TNotebook", background=colors["background"], borderwidth=0)
    style.configure("TLabelframe", bordercolor=colors["border"], relief="flat")
    style.configure("TLabelframe.Label", foreground=GOLD if mode != "Light Mode" else colors["text"])
    _art_styles(root, style, mode != "Light Mode")
    style.configure("Order.TButton", padding=6, width=0)
    root._ata_colors = colors
    root._ata_caption_color = GOLD if mode != "Light Mode" else "#000000"
    _radio_indicators(root, style)
    def refresh(widget):
        if hasattr(widget, "refresh_art"):
            widget.refresh_art()
        for child in widget.winfo_children():
            refresh(child)
    refresh(root)


def _radio_indicators(root, style):
    from PIL import Image, ImageDraw, ImageTk
    if not hasattr(root, "_ata_radio_images"):
        size = max(14, round(root.winfo_fpixels("10p")))
        images = []
        for selected in (False, True):
            image = Image.new("RGBA", (size*3, size*3))
            draw = ImageDraw.Draw(image)
            draw.ellipse((3, 3, size*3-4, size*3-4), fill="#13120e", outline="#716c60", width=3)
            draw.ellipse((6, 6, size*3-7, size*3-7), outline="#34312a", width=3)
            if selected:
                draw.ellipse((size, size, size*2-1, size*2-1), fill=GOLD, outline="#fae1a0", width=2)
            images.append(ImageTk.PhotoImage(image.resize((size, size), Image.Resampling.LANCZOS), master=root))
        root._ata_radio_images = images
        style.element_create("ATA.indicator", "image", images[0], ("selected", images[1]), sticky="")
        def replace(layout):
            return [("ATA.indicator" if name.endswith(".indicator") else name,
                     {key: replace(value) if key == "children" else value for key, value in options.items()})
                    for name, options in layout]
        for name in ("TCheckbutton", "TRadiobutton"):
            style.layout(name, replace(style.layout(name)))
