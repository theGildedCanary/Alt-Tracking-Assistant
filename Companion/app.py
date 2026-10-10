from widgets import Button, Section
"""Alt Tracking Assistant Companion: exports addon data to a spreadsheet (.xlsx or .csv)."""

import csv
import json
import os
import re
import sys
import threading
from datetime import datetime
from pathlib import Path

import db
import settings_sync
import roster_format
import theme
import window_position
from layout import IGNORED, LAYOUT
from lua_parser import LuaParseError, load_saved_variables

APP_NAME = "Alt Tracking Assistant Companion"
SHEET_NAME = "Alt Tracking Assistant"
SV_FILE = "AltTrackingAssistant.lua"
DEFAULT_WOW_DIRS = [
    r"C:\Program Files (x86)\World of Warcraft",
    r"C:\Program Files\World of Warcraft",
    r"D:\World of Warcraft",
]
CONFIG_PATH = Path(os.environ.get("APPDATA", Path.home())) / "AltTrackingAssistantCompanion" / "config.json"
BASE_COLUMNS = ["Name", "Realm", "Class", "Prof 1", "Prof 2", "Archaeology", "Fishing", "Cooking", "Race", "Faction", "Level", "Last Scanned"]
SKIPPED_PROGRESS_KEYS = {"voidStorageItems"}


def load_config():
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_config(config):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")


def find_saved_variable_files(wow_dir):
    """Every account's AltTrackingAssistant.lua under <wow_dir>/<flavor>/WTF/Account/*/SavedVariables."""
    root = Path(wow_dir)
    if not root.is_dir():
        return []
    found = list(root.glob(f"*/WTF/Account/*/SavedVariables/{SV_FILE}"))
    found += list(root.glob(f"WTF/Account/*/SavedVariables/{SV_FILE}"))
    return sorted(set(found))


def detect_wow_dir():
    for candidate in DEFAULT_WOW_DIRS:
        if find_saved_variable_files(candidate):
            return candidate
    return ""


def pretty(key):
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", str(key)).replace("_", " ").title()


def apply_overrides(progress, overrides):
    """Mirror the addon report: active manual overrides replace scanned values."""
    merged = {exp: dict(vals) for exp, vals in (progress or {}).items() if isinstance(vals, dict)}
    for expansion, checks in (overrides or {}).items():
        if not isinstance(checks, dict):
            continue
        for check_id, override in checks.items():
            if isinstance(override, dict) and override.get("active") is True:
                merged.setdefault(expansion, {})[check_id] = override.get("value", False)
    return merged


def column_name(expansion, key):
    return f"{pretty(expansion)}: {pretty(key)}"


def flatten_progress(progress):
    """Map "Expansion: Tracker" -> value, as a list of (expansion, key, name, value) in no fixed order."""
    flat = {}
    for expansion, values in (progress or {}).items():
        if not isinstance(values, dict):
            continue
        for key, value in values.items():
            if key in SKIPPED_PROGRESS_KEYS or (expansion, key) in IGNORED:
                continue
            if isinstance(value, dict):
                separator = " | " if (expansion, key) == ("shadowlands", "renownByCovenant") else ", "
                value = separator.join(f"{k}: {v}" for k, v in sorted(value.items(), key=lambda kv: str(kv[0])))
            elif isinstance(value, list):
                separator = " | " if (expansion, key) == ("shadowlands", "renownByCovenant") else ", "
                value = separator.join(str(v) for v in value)
            flat[(expansion, key)] = value
    return flat


def ordered_columns(flats):
    """Fixed layout first, then any trackers not in the layout (sorted) at the far right."""
    columns = [(exp, key) for exp, keys in LAYOUT for key in keys]
    known = set(columns)
    extras = sorted({k for flat in flats for k in flat} - known, key=lambda k: (str(k[0]), str(k[1])))
    return columns + extras

# Matches the addon's roster: class group, class order, then level (high to low), then name.
ROSTER_CLASS_ORDER = {
    "PALADIN": (1, 1),
    "WARRIOR": (1, 2),
    "DEATHKNIGHT": (1, 3),
    "HUNTER": (2, 1),
    "SHAMAN": (2, 2),
    "EVOKER": (2, 3),
    "DRUID": (3, 1),
    "ROGUE": (3, 2),
    "MONK": (3, 3),
    "DEMONHUNTER": (3, 4),
    "MAGE": (4, 1),
    "PRIEST": (4, 2),
    "WARLOCK": (4, 3),
}


def roster_sort_key(record):
    group, order = ROSTER_CLASS_ORDER.get(record.get("classFile"), (5, 99))
    level = record.get("level") or 0
    label = f"{record.get('name') or 'Unknown'} — {record.get('realm') or 'Unknown Realm'}"
    return (group, order, -level, label)

def account_label(path):
    """Account number from the WTF account folder name, e.g. ...\\Account\\394558216#2\\SavedVariables -> "2"."""
    folder = Path(path).parent.parent.name
    return folder.rsplit("#", 1)[1] if "#" in folder else folder


def collect_sources(paths):
    """Merge characters from several SavedVariables files, keeping the most recently scanned record.

    Returns ({guid: record}, set of guids picked as mains in the addon).
    """
    merged = {}
    mains = set()
    for path in paths:
        addon_db = load_saved_variables(path).get("AltTrackingAssistantDB") or {}
        mains |= db.main_guids(addon_db.get("settings"))
        for guid, record in (addon_db.get("characters") or {}).items():
            if not isinstance(record, dict):
                continue
            current = merged.get(guid)
            if current is None or (record.get("lastScanned") or 0) >= (current.get("lastScanned") or 0):
                merged[guid] = {**record, "account": account_label(path)}
    return merged, mains


def collect_characters(paths):
    merged, _ = collect_sources(paths)
    return sorted(merged.values(), key=roster_sort_key)


def sync_database(paths):
    """Copy the addon data into the local database and return every stored character in roster order."""
    conn = db.connect()
    try:
        if paths:
            merged, mains = collect_sources(paths)
            settings, _ = settings_sync.effective_settings(conn, paths)
            mains = db.main_guids({"characterMains": settings["characterMains"]})
            characters = {
                guid: {**record, "progress": apply_overrides(record.get("progress"), record.get("manualOverrides"))}
                for guid, record in merged.items()
            }
            db.sync_characters(conn, characters, mains)
        return sorted(db.load_characters(conn), key=roster_sort_key)
    finally:
        conn.close()


def load_settings(paths):
    """Settings to edit in the app (pending app edits, else the addon's) and whether edits await a /reload."""
    conn = db.connect()
    try:
        return settings_sync.effective_settings(conn, paths)
    finally:
        conn.close()


def save_settings(paths, settings):
    conn = db.connect()
    try:
        return settings_sync.save_settings(conn, paths, settings)
    finally:
        conn.close()


def realm_initials(realm):
    words = re.findall(r"[A-Za-z0-9]+", realm or "")
    if len(words) > 1:
        return "".join(w[0] for w in words).upper()
    return words[0] if words else ""


RACE_SHORT = {"Lightforged Draenei": "Lightforged", "Zandalari Troll": "Zandalari"}
GENDERS = {1: "M", 2: "F"}
COVENANT_NAMES = {1: "Kyrian", 2: "Venthyr", 3: "Night Fae", 4: "Necrolord"}
HIDDEN_TRACKERS = {("shadowlands", "covenantID")}
TRACKER_TITLES = {
    ("shadowlands", "activeCovenantID"): "Covenant",
    ("shadowlands", "renownByCovenant"): "Renown",
}
CENTERED_TRACKERS = set(TRACKER_TITLES)
TRACKER_MAXIMUMS = {
    ("shadowlands", "anima"): 4,
    ("battleForAzeroth", "footholds"): 3,
    ("legion", "artifacts"): 3,
    ("warlordsOfDraenor", "garrisonLevel"): 3,
}
ARTIFACT_MAXIMUMS_BY_CLASS = {
    "DEMONHUNTER": 2,
    "DRUID": 4,
}
GROUP_TITLES = {"darkmoonFaire": "DMF", "mistsOfPandaria": "MOP", "classic": ""}


def load_format():
    conn = db.connect()
    try:
        return roster_format.normalize(db.get_json(conn, "roster_format"))
    finally:
        conn.close()


def save_format(fmt):
    conn = db.connect()
    try:
        db.set_json(conn, "roster_format", fmt)
    finally:
        conn.close()


def _cell_acct(record, fmt):
    from grid import Cell

    return Cell(record.get("account") or "", fg=fmt["colors"]["text"])


def _cell_realm(record, fmt):
    from grid import Cell

    return Cell(realm_initials(record.get("realm")), fg=fmt["colors"]["text"])


def _cell_fact(record, fmt):
    from grid import Cell

    faction = record.get("faction")
    if faction not in fmt["factionColors"]:
        return Cell(faction or "", fg=fmt["colors"]["text"])
    return Cell(faction[0], fg=fmt["colors"]["factionText"], bg=fmt["factionColors"][faction])


def _cell_lvl(record, fmt):
    from grid import Cell

    level = record.get("level")
    return Cell(str(level) if level is not None else "", fg=fmt["colors"]["text"])


def _cell_dob(record, fmt):
    from grid import Cell

    born = record.get("level10Date")
    text = datetime.fromtimestamp(born).strftime("%m/%d/%Y") if born else ""
    return Cell(text, fg=fmt["colors"]["text"], spacing=fmt["font"]["dateSpacing"])


def _cell_name(record, fmt):
    from grid import Cell

    colors = fmt["colors"]
    return Cell(record.get("name") or "", fg=colors["mainName"] if fmt["mainHighlight"] and record.get("isMain") else colors["text"])


def _cell_race(record, fmt):
    from grid import Cell

    return Cell(RACE_SHORT.get(record.get("race"), record.get("race") or ""), fg=fmt["colors"]["text"])


def _cell_gender(record, fmt):
    from grid import Cell

    letter = GENDERS.get(record.get("bodyType"))
    if not letter:
        return Cell()
    return Cell(letter, fg=fmt["colors"]["genderText"], bg=fmt["genderColors"][letter])


def _cell_cm(record, fmt):
    from grid import Cell

    if not record.get("isMain"):
        return Cell()
    return Cell(fmt["mainMark"], fg=fmt["colors"]["mainMark"])


def _cell_class(record, fmt):
    from grid import Cell

    name = record.get("class") or ""
    color = fmt["classColors"].get(record.get("classFile"), "")
    if fmt["classBackground"]:
        return Cell(name, fg=fmt["colors"]["classText"], bg=color)
    return Cell(name, fg=color or fmt["colors"]["text"])


def profession_value(record, slot):
    profession = (record.get("professions") or {}).get(slot)
    if not isinstance(profession, dict):
        return ""
    if slot in {"primary", "secondary"}:
        return profession.get("name") or ""
    return "x"


def _profession_builder(slot):
    def build(record, fmt):
        from grid import Cell
        return Cell(profession_value(record, slot), fg=fmt["colors"]["text"])
    return build


BASE_BUILDERS = {
    "acct": _cell_acct,
    "realm": _cell_realm,
    "fact": _cell_fact,
    "lvl": _cell_lvl,
    "dob": _cell_dob,
    "name": _cell_name,
    "race": _cell_race,
    "gender": _cell_gender,
    "cm": _cell_cm,
    "class": _cell_class,
    **{slot: _profession_builder(slot) for slot in ("primary", "secondary", "archaeology", "fishing", "cooking")},
}


def build_roster_grid(characters, fmt, settings=None, profession_tracking=None):
    """Columns and cells for the spreadsheet-style roster view, styled by the roster format settings."""
    from grid import Cell, Column

    colors = fmt["colors"]
    from professions_ui import normalize_state, profession_key
    tracked_professions = {entry["guid"]: set(entry["professions"])
                           for entry in normalize_state(profession_tracking)}
    flats = [flatten_progress(c.get("progress")) for c in characters]
    tracked_items = settings_sync.normalize(settings)["trackedItems"]
    setting_keys = {
        ("shadowlands", "activeCovenantID"): "covenant",
        ("shadowlands", "renownByCovenant"): "renown",
    }
    tracker_specs = {(expansion, spec["key"]): spec
                     for expansion, specs in fmt["trackerColumns"].items() for spec in specs}
    tracker_rank = {(expansion, spec["key"]): index
                    for expansion, specs in fmt["trackerColumns"].items() for index, spec in enumerate(specs)}
    tracker_columns = [
        (expansion, key) for expansion, key in ordered_columns(flats)
        if tracker_specs.get((expansion, key), {}).get("visible", True)
        and fmt["expansionVisible"].get(expansion, True)
        and (expansion, key) not in HIDDEN_TRACKERS
        and tracked_items.get(expansion, {}).get(setting_keys.get((expansion, key), key), True)
    ]

    expansion_rank = {key: index for index, key in enumerate(fmt["expansionOrder"])}
    tracker_columns.sort(key=lambda item: (expansion_rank.get(item[0], len(expansion_rank)),
                                          tracker_rank.get(item, len(tracker_rank))))

    columns = []
    rows = [[] for _ in characters]
    for spec in fmt["columns"]:
        if not spec["visible"]:
            continue
        columns.append(
            Column(
                spec["title"], 44, frozen=spec["frozen"], align=spec["align"], vertical=spec["vertical"],
                bg=colors["headerBg"], fg=colors["baseTitle"], title_fg=colors["baseTitle"],
            )
        )
        for row, record in zip(rows, characters):
            cell = BASE_BUILDERS[spec["key"]](record, fmt)
            if fmt["professionHighlight"] and spec["key"] in {"primary", "secondary", "archaeology", "fishing", "cooking"}:
                profession = (record.get("professions") or {}).get(spec["key"])
                if isinstance(profession, dict) and cell.text and profession_key(spec["key"], profession) in tracked_professions.get(record.get("guid"), set()):
                    cell.bg, cell.fg = theme.GOLD, "#000000"
            row.append(cell)

    for expansion, key in tracker_columns:
        shade = fmt["expansionShade"].get(expansion, colors["headerBg"])
        accent = fmt["expansionAccent"].get(expansion, colors["baseTitle"])
        cells = []
        for record, flat in zip(characters, flats):
            value = flat.get((expansion, key))
            if (expansion, key) == ("shadowlands", "renownByCovenant"):
                renown = (record.get("progress") or {}).get("shadowlands", {}).get(key)
                if isinstance(renown, (dict, list)):
                    entries = sorted(renown.items(), key=lambda item: str(item[0])) if isinstance(renown, dict) else enumerate(renown, 1)
                    runs = []
                    for covenant_id, level in entries:
                        if runs:
                            runs.append((" | ", accent))
                        text = f"{covenant_id}: {level}" if isinstance(renown, dict) else str(level)
                        runs.append((text, fmt["covenantColors"].get(str(covenant_id), accent)))
                    cells.append(Cell("".join(text for text, _ in runs), fg=accent, text_runs=tuple(runs)))
                    continue
            if (expansion, key) == ("shadowlands", "activeCovenantID"):
                cells.append(Cell(COVENANT_NAMES.get(value, ""), fg=fmt["covenantColors"].get(str(value), accent)))
                continue
            if (expansion, key) == ("classic", "aq40"):
                has_progress = isinstance(value, (int, float)) and value > 0
                cells.append(Cell("x", fg=accent, bg=shade) if has_progress else Cell())
                continue
            if value is True:
                cells.append(Cell(fmt["mark"], fg=accent, bg=shade))
            elif value is None or value is False or value == "":
                cells.append(Cell())
            else:
                maximum = TRACKER_MAXIMUMS.get((expansion, key))
                if (expansion, key) == ("legion", "artifacts"):
                    maximum = ARTIFACT_MAXIMUMS_BY_CLASS.get(record.get("classFile"), maximum)
                if isinstance(value, (int, float)) and maximum is not None:
                    text = f"{value:g} / {maximum:g}"
                else:
                    text = str(value)
                highlight_maximum = maximum
                if expansion == "shadowlands" and key in {"renown", "renownByCovenant"}:
                    highlight_maximum = 80
                complete = (
                    isinstance(value, (int, float))
                    and highlight_maximum is not None
                    and value >= highlight_maximum
                )
                cells.append(Cell(text, fg=accent, bg=shade if complete else ""))
        longest = max((len(c.text) for c in cells), default=0)
        columns.append(
            Column(
                tracker_specs.get((expansion, key), {}).get("title", TRACKER_TITLES.get((expansion, key), pretty(key))), 44,
                group=fmt["expansionTitles"].get(expansion, GROUP_TITLES.get(expansion, pretty(expansion))),
                group_key=expansion, bg=shade, fg=accent,
                align="center" if longest <= 8 or (expansion, key) in CENTERED_TRACKERS else "w",
                vertical=fmt["trackerTitlesVertical"], title_fg=colors["trackerTitle"],
                separator_before=(expansion, key) == tracker_columns[0],
            )
        )
        for row, cell in zip(rows, cells):
            row.append(cell)

    for record, row in zip(characters, rows):
        bold = fmt["font"]["bold"] or (fmt["mainHighlight"] and record.get("isMain"))
        for cell in row:
            cell.bold = bool(bold)
            cell.italic = bool(fmt["italicMainRows"] and record.get("isMain"))

    return columns, rows


def build_table(characters):
    flats = [flatten_progress(apply_overrides(c.get("progress"), c.get("manualOverrides"))) for c in characters]
    columns = ordered_columns(flats)
    rows = []
    for record, flat in zip(characters, flats):
        scanned = record.get("lastScanned")
        row = [
            record.get("name", ""),
            record.get("realm", ""),
            record.get("class", ""),
            *[profession_value(record, slot) for slot in ("primary", "secondary", "archaeology", "fishing", "cooking")],
            record.get("race", ""),
            record.get("faction", ""),
            record.get("level", ""),
            datetime.fromtimestamp(scanned).strftime("%Y-%m-%d %H:%M") if scanned else "",
        ]
        row += [flat.get(column, "") for column in columns]
        rows.append(row)
    return BASE_COLUMNS + [column_name(*column) for column in columns], rows

def write_spreadsheet(path, header, rows):
    path = Path(path)
    if path.suffix.lower() not in {".xlsx", ".csv"}:
        raise ValueError("Choose a local .xlsx or .csv file to export to.")
    if path.suffix.lower() == ".csv":
        with open(path, "w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle)
            writer.writerow(header)
            writer.writerows(rows)
        return

    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Font
    from openpyxl.utils import get_column_letter

    if path.exists():
        workbook = load_workbook(path)
        if SHEET_NAME in workbook.sheetnames:
            index = workbook.sheetnames.index(SHEET_NAME)
            del workbook[SHEET_NAME]
            sheet = workbook.create_sheet(SHEET_NAME, index)
        else:
            sheet = workbook.create_sheet(SHEET_NAME)
    else:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = SHEET_NAME

    sheet.append(header)
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for row in rows:
        sheet.append(row)
    sheet.freeze_panes = "C2"
    for column, title in enumerate(header, start=1):
        width = max([len(str(title))] + [len(str(r[column - 1])) for r in rows]) + 2
        sheet.column_dimensions[get_column_letter(column)].width = min(width, 40)
    try:
        workbook.save(path)
    except PermissionError:
        raise PermissionError(f"Cannot write {path}. Close it in Excel and try again.")


def export(paths, output):
    """Export to a local file. Returns the number of characters exported."""
    if not output or str(output).lower().startswith(("http://", "https://")):
        raise ValueError("Choose a local .xlsx or .csv file to export to.")
    characters = collect_characters(paths)
    if not characters:
        raise ValueError("No characters found in the addon data. Log in with the addon enabled first.")
    header, rows = build_table(characters)
    write_spreadsheet(output, header, rows)
    return len(characters)


def run_gui():
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    config = load_config()
    root = tk.Tk()
    root.title(APP_NAME)
    icon_path = Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "ATAIcon.ico"
    try:
        root.iconbitmap(default=str(icon_path))
    except tk.TclError:
        pass
    root.geometry("1280x760")
    ui_theme_var = tk.StringVar(value=config.get("ui_theme", "WoW Mode"))
    theme.apply_ui_theme(root, ui_theme_var.get())

    import grid as grid_module
    from tkinter import font as tkfont

    for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont", "TkCaptionFont", "TkFixedFont"):
        tkfont.nametofont(name).configure(family=grid_module.FAMILY)

    wow_var = tk.StringVar(value=config.get("wow_dir") or detect_wow_dir())
    out_var = tk.StringVar(value=config.get("output", ""))
    auto_var = tk.BooleanVar(value=config.get("auto_export", False))
    status_var = tk.StringVar(value="Ready.")
    files = []

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)
    roster_tab = ttk.Frame(notebook)
    notebook.add(roster_tab, text="Roster")
    from professions_ui import ProfessionsTab, STATE_KEY, normalize_state
    conn = db.connect()
    try:
        profession_dashboard_state = normalize_state(db.get_json(conn, STATE_KEY))
    finally:
        conn.close()

    def save_profession_dashboard(state):
        conn = db.connect()
        try:
            db.set_json(conn, STATE_KEY, state)
        finally:
            conn.close()

        profession_dashboard_state[:] = state
        render_roster()

    professions_tab = ProfessionsTab(notebook, profession_dashboard_state,
                                    save_profession_dashboard, ui_theme_var.get())
    notebook.add(professions_tab, text="Professions")
    from settings_ui import SettingsTab

    def save_and_reload(settings):
        count = save_settings(list(files), settings)
        reload_roster()
        return count

    format_state = {"fmt": load_format(), "characters": []}
    professions_tab.set_format(format_state["fmt"])

    def change_format(fmt):
        format_state["fmt"] = roster_format.normalize(fmt)
        save_format(format_state["fmt"])
        professions_tab.set_format(format_state["fmt"])
        render_roster()

    def change_ui_theme(mode):
        ui_theme_var.set(mode)
        theme.apply_ui_theme(root, mode)

        colors = theme.UI_THEMES[mode]
        for page in settings_tab.pages.values():
            page.canvas.configure(background=colors["background"])
        professions_tab.set_theme(mode)

        persist()
    
    settings_tab = SettingsTab(
        notebook,
        save_and_reload,
        lambda: reload_roster(),
        change_format,
        format_state["fmt"],
        change_ui_theme,
        ui_theme_var.get(),
        on_tracking_change=lambda: render_roster(),
    )

    for page in settings_tab.pages.values():
        page.canvas.configure(
            background=theme.UI_THEMES[ui_theme_var.get()]["background"]
        )
    notebook.add(settings_tab, text="Settings")
    frame = ttk.Frame(notebook, padding=12)
    notebook.add(frame, text="Export")
    frame.columnconfigure(1, weight=1)

    def persist():
        save_config(
            {
                "wow_dir": wow_var.get(),
                "output": out_var.get(),
                "auto_export": auto_var.get(),
                "ui_theme": ui_theme_var.get(),
                "window_position": config.get("window_position"),
            }
        )

    def refresh_files(*_):
        files[:] = find_saved_variable_files(wow_var.get())
        listbox.delete(0, "end")
        for f in files:
            listbox.insert("end", str(f))
        status_var.set(f"Found {len(files)} addon data file(s)." if files else "No addon data found in that folder.")

    def browse_wow():
        chosen = filedialog.askdirectory(title="Select World of Warcraft folder", initialdir=wow_var.get() or None)
        if chosen:
            wow_var.set(os.path.normpath(chosen))
            persist()
            refresh_files()

    def browse_output():
        chosen = filedialog.asksaveasfilename(
            title="Choose spreadsheet (existing file or new)",
            defaultextension=".xlsx",
            filetypes=[("Excel workbook", "*.xlsx"), ("CSV", "*.csv")],
            confirmoverwrite=False,
            initialfile=Path(out_var.get()).name if out_var.get() else "AltTracking.xlsx",
        )
        if chosen:
            out_var.set(os.path.normpath(chosen))
            persist()

    def run_in_background(work, done):
        result = {}

        def target():
            try:
                result["value"] = work()
            except Exception as error:  # surfaced to the user in the UI
                result["error"] = error

        thread = threading.Thread(target=target, daemon=True)
        thread.start()

        def check():
            if thread.is_alive():
                root.after(100, check)
            else:
                done(result.get("value"), result.get("error"))

        check()

    def do_export(silent=False):
        if not files:
            refresh_files()
        output = out_var.get().strip()
        problem = None
        if not files:
            problem = "Select the WoW folder that contains the addon data."
        elif not output:
            problem = "Choose the spreadsheet file to export to."
        elif output.lower().startswith(("http://", "https://")) or Path(output).suffix.lower() not in {".xlsx", ".csv"}:
            problem = "Choose a local .xlsx or .csv file to export to."
        if problem:
            status_var.set(problem)
            if not silent:
                messagebox.showwarning(APP_NAME, problem)
            return
        persist()
        status_var.set("Exporting...")
        paths = list(files)

        def finished(count, error):
            if error:
                status_var.set(f"Export failed: {error}")
                if not silent:
                    messagebox.showerror(APP_NAME, str(error))
            else:
                status_var.set(f"Exported {count} characters at {datetime.now():%H:%M:%S}.")
        run_in_background(lambda: export(paths, output), finished)

    from grid import RosterGrid

    roster_status = tk.StringVar()
    toolbar = ttk.Frame(roster_tab, padding=(8, 6))
    toolbar.pack(fill="x")
    Button(toolbar, text="Refresh", command=lambda: reload_roster()).pack(side="left")
    ttk.Label(toolbar, textvariable=roster_status).pack(side="left", padx=10)
    roster_grid = RosterGrid(roster_tab)
    roster_grid.pack(fill="both", expand=True)

    def render_roster():
        fmt = format_state["fmt"]
        mains = db.main_guids(settings_tab.settings)
        for character in format_state["characters"]:
            character["isMain"] = character["guid"] in mains
        columns, rows = build_roster_grid(format_state["characters"], fmt, settings_tab.settings, profession_dashboard_state)
        roster_grid.set_data(columns, rows, grid_module.style_from_format(fmt))

    def reload_roster():
        try:
            characters = sync_database(list(files))
            settings, pending = load_settings(list(files)) if files else (settings_sync.normalize({}), False)
        except (OSError, LuaParseError, ValueError) as error:
            roster_status.set(f"Could not read addon data: {error}")
            return
        format_state["characters"] = characters
        professions_tab.load(characters)
        settings_tab.load(characters, settings, pending)
        render_roster()
        roster_status.set(f"{len(characters)} characters  ·  updated {datetime.now():%H:%M:%S}")

    row = 0
    ttk.Label(frame, text="WoW folder:").grid(row=row, column=0, sticky="w", pady=4)
    ttk.Entry(frame, textvariable=wow_var).grid(row=row, column=1, sticky="ew", padx=6)
    Button(frame, text="Browse...", command=browse_wow).grid(row=row, column=2)

    row += 1
    ttk.Label(frame, text="Local file (.xlsx or .csv):").grid(row=row, column=0, sticky="w", pady=4)
    ttk.Entry(frame, textvariable=out_var).grid(row=row, column=1, sticky="ew", padx=6)
    Button(frame, text="Browse...", command=browse_output).grid(row=row, column=2)

    row += 1
    ttk.Label(frame, text="Addon data files found:").grid(row=row, column=0, columnspan=3, sticky="w", pady=(10, 2))
    row += 1
    listbox = tk.Listbox(frame, height=8)
    listbox.grid(row=row, column=0, columnspan=3, sticky="nsew")
    frame.rowconfigure(row, weight=1)

    row += 1
    buttons = ttk.Frame(frame)
    buttons.grid(row=row, column=0, columnspan=3, sticky="ew", pady=10)
    Button(buttons, text="Rescan", command=lambda: (refresh_files(), reload_roster())).pack(side="left")
    Button(buttons, text="Export now", command=do_export).pack(side="left", padx=6)
    ttk.Checkbutton(
        buttons, text="Auto-export when the addon data changes", variable=auto_var, command=persist
    ).pack(side="left", padx=10)

    row += 1
    ttk.Label(frame, textvariable=status_var, wraplength=640).grid(row=row, column=0, columnspan=3, sticky="w")

    refresh_files()
    reload_roster()

    last_seen = {str(f): (f.stat().st_mtime_ns, f.stat().st_size) for f in files if f.exists()}

    def poll():
        if files:
            current = {str(f): (f.stat().st_mtime_ns, f.stat().st_size) for f in files if f.exists()}
            if current != last_seen:
                reload_roster()
                if auto_var.get():
                    do_export(silent=True)
            last_seen.clear()
            last_seen.update(current)
        root.after(5000, poll)

    def close_app():
        saved_position = window_position.capture(root)
        if saved_position is not None:
            config["window_position"] = saved_position

        try:
            persist()
        finally:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", close_app)

    # Finish creating the native window before restoring its placement.
    root.update_idletasks()
    window_position.restore(root, config.get("window_position"))

    poll()
    root.mainloop()


def main(argv):
    # Headless: python app.py --export <wow_dir> <output.xlsx|csv>
    if len(argv) == 4 and argv[1] == "--export":
        paths = find_saved_variable_files(argv[2])
        if not paths:
            print("No addon data found.", file=sys.stderr)
            return 1
        try:
            count = export(paths, argv[3])
        except (OSError, ValueError) as error:
            print(str(error), file=sys.stderr)
            return 1
        print(f"Exported {count} characters to {argv[3]}")
        return 0
    run_gui()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
