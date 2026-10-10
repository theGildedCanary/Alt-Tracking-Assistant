"""Customizable look of the Companion roster. Stored in the app database and never sent to the addon."""

import copy
import re

import theme
from layout import LAYOUT

HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
ALIGNS = ("w", "center", "e")

BASE_COLUMNS = [
    {"key": "acct", "title": "ACCT", "align": "center", "vertical": True, "frozen": True, "visible": True},
    {"key": "realm", "title": "Realm", "align": "center", "vertical": True, "frozen": True, "visible": True},
    {"key": "fact", "title": "Fact", "align": "center", "vertical": True, "frozen": True, "visible": True},
    {"key": "lvl", "title": "Lvl", "align": "center", "vertical": False, "frozen": True, "visible": True},
    {"key": "dob", "title": "DOB", "align": "center", "vertical": False, "frozen": True, "visible": True},
    {"key": "name", "title": "Name", "align": "center", "vertical": False, "frozen": True, "visible": True},
    {"key": "race", "title": "Race", "align": "center", "vertical": False, "frozen": False, "visible": True},
    {"key": "gender", "title": "Gender", "align": "center", "vertical": True, "frozen": False, "visible": True},
    {"key": "cm", "title": "CM", "align": "center", "vertical": False, "frozen": False, "visible": True},
    {"key": "class", "title": "Class", "align": "center", "vertical": False, "frozen": False, "visible": True},
    {"key": "primary", "title": "Prof 1", "align": "center", "vertical": False, "frozen": False, "visible": True},
    {"key": "secondary", "title": "Prof 2", "align": "center", "vertical": False, "frozen": False, "visible": True},
    {"key": "archaeology", "title": "Arch.", "align": "center", "vertical": True, "frozen": False, "visible": True},
    {"key": "fishing", "title": "Fish.", "align": "center", "vertical": True, "frozen": False, "visible": True},
    {"key": "cooking", "title": "Cook.", "align": "center", "vertical": True, "frozen": False, "visible": True},
]

EXPANSION_TITLES = {key: re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", key).title() for key, _ in LAYOUT}
EXPANSION_TITLES.update(darkmoonFaire="DMF", mistsOfPandaria="MOP", classic="")

TRACKER_COLUMNS = {
    expansion: [{"key": key, "title": {"activeCovenantID": "Covenant", "renownByCovenant": "Renown"}.get(
        key, re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", key).title()), "visible": True}
        for key in keys if (expansion, key) != ("shadowlands", "covenantID")]
    for expansion, keys in LAYOUT
}

DEFAULTS = {
    "font": {"family": "Montserrat", "bodySize": 9, "titleSize": 7, "bold": True, "titleBold": True,
             "titleSpacing": 2, "dateSpacing": 1},
    "rowHeight": 24,
    "stripes": True,
    "boldMainRows": True,
    "mainHighlight": True,
    "professionHighlight": True,
    "expansionOrder": [expansion for expansion, _ in LAYOUT],
    "expansionTitles": EXPANSION_TITLES,
    "expansionVisible": {expansion: True for expansion, _ in LAYOUT},
    "italicMainRows": True,
    "trackerTitlesVertical": True,
    "classBackground": True,
    "mark": "X",
    "mainMark": "\u2605",
    "colors": {
        "text": theme.TEXT,
        "background": theme.PANEL,
        "stripe": theme.PANEL_ALT,
        "gridLine": theme.DIVIDER,
        "separator": theme.GOLD,
        "headerBg": "#1E213E",
        "baseTitle": theme.GOLD,
        "trackerTitle": "#ffffff",
        "mainName": theme.GOLD,
        "mainMark": theme.GOLD,
        "factionText": "#000000",
        "genderText": "#2b2b2b",
        "classText": "#000000",
        "professionProgress": "#331E53",
    },
    "factionColors": dict(theme.FACTION_COLORS),
    "genderColors": {"M": "#8fb3e0", "F": "#eba0bd"},
    "classColors": dict(theme.CLASS_COLORS),
    "covenantColors": {"1": "#A9D6F5", "2": "#F2AAAA", "3": "#D2B5F0", "4": "#B4DFA9"},
    "expansionShade": dict(theme.EXPANSION_COLORS),
    "expansionAccent": dict(theme.EXPANSION_ACCENTS),
    "columns": BASE_COLUMNS,
    "trackerColumns": TRACKER_COLUMNS,
}

COLOR_GROUPS = ("colors", "factionColors", "genderColors", "classColors", "covenantColors", "expansionShade", "expansionAccent")


def defaults():
    return copy.deepcopy(DEFAULTS)


def _int(value, default, low, high):
    try:
        return max(low, min(high, int(value)))
    except (TypeError, ValueError):
        return default


def _bool(value, default):
    return value if isinstance(value, bool) else default


def _text(value, default, limit):
    if isinstance(value, str) and value.strip():
        return value.strip()[:limit]
    return default


def normalize(raw):
    """Merge stored settings over the defaults, dropping anything invalid."""
    raw = raw if isinstance(raw, dict) else {}
    fmt = defaults()

    raw_font = raw.get("font") if isinstance(raw.get("font"), dict) else {}
    font = fmt["font"]
    font["family"] = _text(raw_font.get("family"), font["family"], 64)
    font["bodySize"] = _int(raw_font.get("bodySize"), font["bodySize"], 6, 24)
    font["titleSize"] = _int(raw_font.get("titleSize"), font["titleSize"], 5, 20)
    font["titleSpacing"] = _int(raw_font.get("titleSpacing"), font["titleSpacing"], 0, 10)
    font["dateSpacing"] = _int(raw_font.get("dateSpacing"), font["dateSpacing"], 0, 10)
    font["bold"] = _bool(raw_font.get("bold"), font["bold"])
    font["titleBold"] = _bool(raw_font.get("titleBold"), font["titleBold"])

    fmt["rowHeight"] = _int(raw.get("rowHeight"), fmt["rowHeight"], 16, 60)
    for key in ("stripes", "boldMainRows", "italicMainRows", "trackerTitlesVertical", "classBackground"):
        fmt[key] = _bool(raw.get(key), fmt[key])
    fmt["mainHighlight"] = _bool(raw.get("mainHighlight"), fmt["boldMainRows"])
    fmt["professionHighlight"] = _bool(raw.get("professionHighlight"), True)
    order = raw.get("expansionOrder")
    order = order if isinstance(order, list) else []
    fmt["expansionOrder"] = list(dict.fromkeys([key for key in order if isinstance(key, str) and key in fmt["expansionShade"]] + fmt["expansionOrder"]))
    titles = raw.get("expansionTitles")
    titles = titles if isinstance(titles, dict) else {}
    visible = raw.get("expansionVisible")
    visible = visible if isinstance(visible, dict) else {}
    for key in fmt["expansionOrder"]:
        title = titles.get(key)
        if isinstance(title, str):
            fmt["expansionTitles"][key] = title.strip()[:64]
        fmt["expansionVisible"][key] = _bool(visible.get(key), True)
    fmt["mark"] = _text(raw.get("mark"), fmt["mark"], 3)
    fmt["mainMark"] = _text(raw.get("mainMark"), fmt["mainMark"], 3)

    for group in COLOR_GROUPS:
        stored = raw.get(group) if isinstance(raw.get(group), dict) else {}
        for key, default in fmt[group].items():
            value = stored.get(key)
            if isinstance(value, str) and HEX.match(value):
                fmt[group][key] = value.lower()

    stored_trackers = raw.get("trackerColumns")
    stored_trackers = stored_trackers if isinstance(stored_trackers, dict) else {}
    for expansion, tracker_defaults in TRACKER_COLUMNS.items():
        known_trackers = {spec["key"]: spec for spec in tracker_defaults}
        stored = stored_trackers.get(expansion)
        stored = stored if isinstance(stored, list) else []
        columns, seen = [], set()
        for item in stored:
            if not isinstance(item, dict):
                continue
            key = item.get("key")
            if not isinstance(key, str) or key not in known_trackers or key in seen:
                continue
            seen.add(key)
            spec = dict(known_trackers[key])
            spec["title"] = _text(item.get("title"), spec["title"], 64)
            spec["visible"] = _bool(item.get("visible"), True)
            columns.append(spec)
        columns.extend(dict(spec) for spec in tracker_defaults if spec["key"] not in seen)
        fmt["trackerColumns"][expansion] = columns

    known = {c["key"]: c for c in BASE_COLUMNS}
    columns, seen = [], set()
    for item in raw.get("columns") if isinstance(raw.get("columns"), list) else []:
        if not isinstance(item, dict) or item.get("key") not in known or item["key"] in seen:
            continue
        seen.add(item["key"])
        column = dict(known[item["key"]])
        column["title"] = _text(item.get("title"), column["title"], 24)
        if (column["key"], column["title"]) in {("primary", "Primary"), ("secondary", "Secondary")}:
            column["title"] = known[column["key"]]["title"]
        column["align"] = item.get("align") if item.get("align") in ALIGNS else column["align"]
        for flag in ("vertical", "frozen", "visible"):
            column[flag] = _bool(item.get(flag), column[flag])
        columns.append(column)
    # Insert new columns beside their default predecessor while preserving saved formatting/order.
    for index, default in enumerate(BASE_COLUMNS):
        if default["key"] in seen:
            continue
        previous = {c["key"] for c in BASE_COLUMNS[:index]}
        position = next((i + 1 for i in range(len(columns) - 1, -1, -1) if columns[i]["key"] in previous), 0)
        columns.insert(position, dict(default))
    fmt["columns"] = columns
    return fmt
