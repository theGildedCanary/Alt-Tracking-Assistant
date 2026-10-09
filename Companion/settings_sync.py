"""Addon settings (character mains, tracked items) as edited in the app and handed back to the addon.

The addon only reads settings from its SavedVariables, so edits are written to AppSync.lua in the addon folder. The addon applies a revision once, at login/reload, and records it as appSyncRev.
"""

import copy
import time
from pathlib import Path

import db
from lua_parser import load_saved_variables

SYNC_FILE = "AppSync.lua"
PENDING_KEY = "pending_settings"

CHARACTER_MODES = [("single", "Single"), ("faction", "Faction"), ("class", "Class"), ("classFaction", "Class Faction")]
ARMOR_MODES = [("armor", "Single"), ("armorFaction", "Faction")]
FACTIONS = ["Alliance", "Horde"]
CLASS_ORDER = [
    ("PALADIN", "Paladin"),
    ("WARRIOR", "Warrior"),
    ("DEATHKNIGHT", "Death Knight"),
    ("HUNTER", "Hunter"),
    ("SHAMAN", "Shaman"),
    ("EVOKER", "Evoker"),
    ("DRUID", "Druid"),
    ("ROGUE", "Rogue"),
    ("MONK", "Monk"),
    ("DEMONHUNTER", "Demon Hunter"),
    ("MAGE", "Mage"),
    ("PRIEST", "Priest"),
    ("WARLOCK", "Warlock"),
]
ARMOR_TYPES = [
    ("plate", "Plate", {"PALADIN", "WARRIOR", "DEATHKNIGHT"}),
    ("mail", "Mail", {"HUNTER", "SHAMAN", "EVOKER"}),
    ("leather", "Leather", {"DRUID", "ROGUE", "MONK", "DEMONHUNTER"}),
    ("cloth", "Cloth", {"MAGE", "PRIEST", "WARLOCK"}),
]

# Tracker ids used by the addon's "tracked items" setting, in window order. Mirrors the addon's tracker definitions.
TRACKERS = [
    ("darkmoonFaire", "Darkmoon Faire", [("silasSecretStash", "Silas' Secret Stash")]),
    (
        "midnight",
        "Midnight",
        [
            ("introSkip", "Intro Skip"),
            ("craftersNeeded", "Crafters Needed"),
            ("valNaigtalSkip", "Val / Naigtal Skip"),
            ("coilIsleSkip", "Coiled Isle Skip"),
        ],
    ),
    (
        "theWarWithin",
        "The War Within",
        [
            ("introSkip", "Intro Skip"),
            ("craftingToOrder", "Crafting to Order"),
            ("undermine", "Undermine"),
            ("delveBelt", "Delve Belt"),
            ("reshiiWraps", "Reshii Wraps"),
        ],
    ),
    (
        "dragonflight",
        "Dragonflight",
        [
            ("introSkip", "Intro Skip"),
            ("fiveSparks", "5x Sparks"),
            ("forbiddenReach", "Forbidden Reach"),
            ("suffusionCamp", "Suffusion Camp"),
            ("zaralekCaverns", "Zaralek Caverns"),
            ("emeraldDream", "Emerald Dream"),
            ("elegantCanvasBrush", "Elegant Canvas Brush"),
        ],
    ),
    (
        "shadowlands",
        "Shadowlands",
        [
            ("covenant", "Covenant"),
            ("anima", "4k Anima"),
            ("renown", "Renown"),
            ("korthia", "Korthia"),
            ("zerethMortis", "Zereth Mortis"),
            ("helswornChest", "Helsworn Chest"),
        ],
    ),
    (
        "battleForAzeroth",
        "Battle for Azeroth",
        [
            ("intro", "BFA Intro"),
            ("footholds", "Footholds"),
            ("nazjatar", "Nazjatar"),
            ("mechagon", "Mechagon"),
            ("cloak", "BFA Cloak"),
            ("taptaf", "Taptaf"),
        ],
    ),
    (
        "legion",
        "Legion",
        [
            ("chromieDeathIntro", "Chromie Death Intro"),
            ("artifacts", "Artifacts"),
            ("classHall", "Class Hall"),
            ("suramar", "Suramar"),
            ("helarjarWorldQuests", "Helarjar Wqs"),
            ("brokenShore", "Broken Shore"),
            ("championsOfLegionfall", "Champions of Legionfall"),
            ("argus", "Argus"),
            ("worthItsWeight", "Worth Its Weight"),
        ],
    ),
    (
        "warlordsOfDraenor",
        "Warlords of Draenor",
        [
            ("garrisonLevel", "Garrison"),
            ("tanaan", "Tanaan Base"),
            ("mageTower", "Mage Portals"),
            ("stables", "Stables"),
            ("bank", "Bank / Storehouse"),
            ("tradingPost", "Trading Post"),
            ("mining", "Mining"),
            ("herbGarden", "Herb Garden"),
        ],
    ),
    ("mistsOfPandaria", "Mists of Pandaria", [("isleOfThunder", "Isle of Thunder"), ("sunsongRanch", "Sunsong Ranch")]),
    (
        "cataclysm",
        "Cataclysm",
        [("moltenFront", "Molten Front"), ("vashjir", "Vashj'ir"), ("twilightHighlands", "Twilight Highlands")],
    ),
    ("classic", "Classic", [("aq40", "AQ40")]),
]


def character_slots(mode):
    """Selection slots for a character-main mode: (slot id, label, allowed class files or None, faction or None)."""
    if mode == "single":
        return [("single", "Main", None, None)]
    if mode == "faction":
        return [(f"faction:{f}", f, None, f) for f in FACTIONS]
    if mode == "class":
        return [(f"class:{c}", name, {c}, None) for c, name in CLASS_ORDER]
    slots = []
    for c, name in CLASS_ORDER:
        for f in FACTIONS:
            slots.append((f"classFaction:{c}:{f}", f"{name} - {f[0]}", {c}, f))
    return slots


def armor_slots(mode):
    slots = []
    for armor_id, label, classes in ARMOR_TYPES:
        if mode == "armorFaction":
            for f in FACTIONS:
                slots.append((f"armorFaction:{armor_id}:{f}", f"{label} - {f}", classes, f))
        else:
            slots.append((f"armor:{armor_id}", label, classes, None))
    return slots


def _as_dict(value):
    return value if isinstance(value, dict) else {}


def normalize(settings):
    """Plain, fully-populated copy of the settings the app edits."""
    mains = copy.deepcopy(_as_dict(_as_dict(settings).get("characterMains")))
    mains["selections"] = _as_dict(mains.get("selections"))
    if mains.get("characterMode") not in {m for m, _ in CHARACTER_MODES}:
        mains["characterMode"] = "single"
    if mains.get("armorMode") not in {m for m, _ in ARMOR_MODES}:
        mains["armorMode"] = "armor"
    mains["trueMainEnabled"] = mains.get("trueMainEnabled") is True
    tracked = {
        str(exp): {str(k): v is True for k, v in _as_dict(values).items()}
        for exp, values in _as_dict(_as_dict(settings).get("trackedItems")).items()
    }
    return {"characterMains": mains, "trackedItems": tracked}


def read_addon_settings(paths):
    """Settings and applied app revision from the most recently written SavedVariables file."""
    paths = [Path(p) for p in paths]
    if not paths:
        return normalize({}), 0
    newest = max(paths, key=lambda p: p.stat().st_mtime)
    addon_db = load_saved_variables(newest).get("AltTrackingAssistantDB") or {}
    revision = addon_db.get("appSyncRev")
    return normalize(addon_db.get("settings")), revision if isinstance(revision, (int, float)) else 0


def effective_settings(conn, paths):
    """(settings, pending). Pending app edits win until the addon reports it applied them."""
    settings, applied = read_addon_settings(paths)
    pending = db.get_json(conn, PENDING_KEY)
    if isinstance(pending, dict) and pending.get("rev", 0) > applied:
        return normalize(pending), True
    if pending:
        db.set_json(conn, PENDING_KEY, None)
    return settings, False


def _lua_value(value, indent=0):
    pad = "    " * (indent + 1)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, dict):
        if not value:
            return "{}"
        lines = [f"{pad}[{_lua_value(str(k))}] = {_lua_value(v, indent + 1)}," for k, v in value.items()]
        return "{\n" + "\n".join(lines) + "\n" + "    " * indent + "}"
    text = str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{text}"'


def addon_dirs(paths):
    """AddOns/AltTrackingAssistant folders next to each SavedVariables file's WTF folder."""
    found = []
    for path in paths:
        parents = Path(path).parents
        if len(parents) > 4:
            folder = parents[4] / "Interface" / "AddOns" / "AltTrackingAssistant"
            if folder.is_dir() and folder not in found:
                found.append(folder)
    return found


def save_settings(conn, paths, settings):
    """Remember the edits and write AppSync.lua for the addon. Returns the number of addon folders written."""
    settings = normalize(settings)
    revision = int(time.time())
    db.set_json(conn, PENDING_KEY, {**settings, "rev": revision})
    content = (
        "-- Written by the Alt Tracking Assistant Companion app. Do not edit by hand.\n"
        "AltTrackingAssistantAppSync = {\n"
        f"    rev = {revision},\n"
        f"    characterMains = {_lua_value(settings['characterMains'], 1)},\n"
        f"    trackedItems = {_lua_value(settings['trackedItems'], 1)},\n"
        "}\n"
    )
    folders = addon_dirs(paths)
    for folder in folders:
        (folder / SYNC_FILE).write_text(content, encoding="utf-8")
    return len(folders)
