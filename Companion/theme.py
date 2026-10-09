"""Colors shared by the companion app, taken from the addon's UI/Theme.lua."""


def _hex(r, g, b):
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


TEXT = _hex(0.92, 0.94, 0.98)
MUTED_TEXT = _hex(0.68, 0.73, 0.80)
PANEL = _hex(17 / 255, 22 / 255, 28 / 255)
PANEL_ALT = "#161d25"
PANEL_BORDER = _hex(0.74, 0.53, 0.19)
DIVIDER = _hex(0.27, 0.34, 0.40)
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
