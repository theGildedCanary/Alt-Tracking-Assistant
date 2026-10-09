"""Alt Tracking Assistant Companion: exports addon data to a spreadsheet (.xlsx or .csv)."""

import csv
import json
import os
import re
import sys
import threading
from datetime import datetime
from pathlib import Path

import gsheets
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
BASE_COLUMNS = ["Name", "Realm", "Class", "Race", "Faction", "Level", "Last Scanned"]
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
                value = ", ".join(f"{k}: {v}" for k, v in sorted(value.items(), key=lambda kv: str(kv[0])))
            elif isinstance(value, list):
                value = ", ".join(str(v) for v in value)
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

def collect_characters(paths):
    """Merge characters from several SavedVariables files, keeping the most recently scanned record."""
    merged = {}
    for path in paths:
        db = load_saved_variables(path).get("AltTrackingAssistantDB") or {}
        for guid, record in (db.get("characters") or {}).items():
            if not isinstance(record, dict):
                continue
            current = merged.get(guid)
            if current is None or (record.get("lastScanned") or 0) >= (current.get("lastScanned") or 0):
                merged[guid] = record
    return sorted(merged.values(), key=roster_sort_key)


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


def export(paths, output=None, sheet_url=None, interactive=True):
    """Export to a Google Sheet and/or a local file. Returns the number of characters exported."""
    characters = collect_characters(paths)
    if not characters:
        raise ValueError("No characters found in the addon data. Log in with the addon enabled first.")
    header, rows = build_table(characters)
    if sheet_url:
        gsheets.write_to_sheet(sheet_url, header, rows, interactive=interactive)
    if output:
        write_spreadsheet(output, header, rows)
    return len(characters)


def run_gui():
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    config = load_config()
    root = tk.Tk()
    root.title(APP_NAME)
    root.geometry("700x470")

    wow_var = tk.StringVar(value=config.get("wow_dir") or detect_wow_dir())
    out_var = tk.StringVar(value=config.get("output", ""))
    mode_var = tk.StringVar(value=config.get("mode", "sheet"))
    url_var = tk.StringVar(value=config.get("sheet_url", ""))
    account_var = tk.StringVar()
    auto_var = tk.BooleanVar(value=config.get("auto_export", False))
    status_var = tk.StringVar(value="Ready.")
    files = []

    frame = ttk.Frame(root, padding=12)
    frame.pack(fill="both", expand=True)
    frame.columnconfigure(1, weight=1)

    def persist():
        save_config(
            {
                "wow_dir": wow_var.get(),
                "output": out_var.get(),
                "mode": mode_var.get(),
                "sheet_url": url_var.get(),
                "auto_export": auto_var.get(),
            }
        )

    def refresh_account():
        account_var.set("Signed in to Google." if gsheets.is_signed_in() else "Not signed in.")

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

    def sign_in():
        status_var.set("Complete the sign-in in your browser...")

        def finished(_, error):
            refresh_account()
            status_var.set(f"Sign-in failed: {error}" if error else "Signed in to Google.")
            if error:
                messagebox.showerror(APP_NAME, str(error))

        run_in_background(gsheets.get_credentials, finished)

    def sign_out():
        gsheets.sign_out()
        refresh_account()

    def do_export(silent=False):
        if not files:
            refresh_files()
        sheet_mode = mode_var.get() == "sheet"
        url = url_var.get().strip() if sheet_mode else None
        output = None if sheet_mode else out_var.get().strip()
        problem = None
        if not files:
            problem = "Select the WoW folder that contains the addon data."
        elif sheet_mode and not url:
            problem = "Paste the link to your Google Sheet."
        elif not sheet_mode and not output:
            problem = "Choose the spreadsheet file to export to."
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
            refresh_account()

        run_in_background(lambda: export(paths, output, url, interactive=not silent), finished)

    row = 0
    ttk.Label(frame, text="WoW folder:").grid(row=row, column=0, sticky="w", pady=4)
    ttk.Entry(frame, textvariable=wow_var).grid(row=row, column=1, sticky="ew", padx=6)
    ttk.Button(frame, text="Browse...", command=browse_wow).grid(row=row, column=2)

    row += 1
    ttk.Radiobutton(frame, text="Google Sheet:", variable=mode_var, value="sheet", command=persist).grid(
        row=row, column=0, sticky="w", pady=4
    )
    ttk.Entry(frame, textvariable=url_var).grid(row=row, column=1, columnspan=2, sticky="ew", padx=6)

    row += 1
    google = ttk.Frame(frame)
    google.grid(row=row, column=1, columnspan=2, sticky="w", padx=6)
    ttk.Button(google, text="Sign in with Google", command=sign_in).pack(side="left")
    ttk.Button(google, text="Sign out", command=sign_out).pack(side="left", padx=6)
    ttk.Label(google, textvariable=account_var).pack(side="left", padx=6)

    row += 1
    ttk.Radiobutton(frame, text="Local file:", variable=mode_var, value="file", command=persist).grid(
        row=row, column=0, sticky="w", pady=4
    )
    ttk.Entry(frame, textvariable=out_var).grid(row=row, column=1, sticky="ew", padx=6)
    ttk.Button(frame, text="Browse...", command=browse_output).grid(row=row, column=2)

    row += 1
    ttk.Label(frame, text="Addon data files found:").grid(row=row, column=0, columnspan=3, sticky="w", pady=(10, 2))
    row += 1
    listbox = tk.Listbox(frame, height=8)
    listbox.grid(row=row, column=0, columnspan=3, sticky="nsew")
    frame.rowconfigure(row, weight=1)

    row += 1
    buttons = ttk.Frame(frame)
    buttons.grid(row=row, column=0, columnspan=3, sticky="ew", pady=10)
    ttk.Button(buttons, text="Rescan", command=refresh_files).pack(side="left")
    ttk.Button(buttons, text="Export now", command=do_export).pack(side="left", padx=6)
    ttk.Checkbutton(
        buttons, text="Auto-export when the addon data changes", variable=auto_var, command=persist
    ).pack(side="left", padx=10)

    row += 1
    ttk.Label(frame, textvariable=status_var, wraplength=640).grid(row=row, column=0, columnspan=3, sticky="w")

    refresh_files()
    refresh_account()

    last_seen = {}

    def poll():
        if auto_var.get() and files:
            current = {str(f): f.stat().st_mtime for f in files if f.exists()}
            if last_seen and current != last_seen:
                do_export(silent=True)
            last_seen.clear()
            last_seen.update(current)
        root.after(5000, poll)

    poll()
    root.mainloop()


def main(argv):
    # Headless: python app.py --export <wow_dir> <output.xlsx|csv|google-sheet-url>
    if len(argv) == 4 and argv[1] == "--export":
        paths = find_saved_variable_files(argv[2])
        if not paths:
            print("No addon data found.", file=sys.stderr)
            return 1
        is_url = argv[3].startswith("http")
        count = export(paths, None if is_url else argv[3], argv[3] if is_url else None)
        print(f"Exported {count} characters to {argv[3]}")
        return 0
    run_gui()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
