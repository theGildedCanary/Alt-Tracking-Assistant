"""Fixed spreadsheet column layout so column positions never shift between exports.

Expansions follow the addon's window order (Darkmoon Faire first, Classic last). Trackers within an expansion follow the addon's definition order.
Trackers not listed here are appended after all of these, so existing columns never move.
"""

LAYOUT = [
    ("darkmoonFaire", ["silasSecretStash"]),
    ("midnight", ["introSkip", "craftersNeeded", "valNaigtalSkip", "coilIsleSkip"]),
    ("theWarWithin", ["introSkip", "craftingToOrder", "undermine", "delveBelt", "reshiiWraps"]),
    (
        "dragonflight",
        [
            "introSkip",
            "fiveSparks",
            "forbiddenReach",
            "suffusionCamp",
            "zaralekCaverns",
            "emeraldDream",
            "elegantCanvasBrush",
        ],
    ),
    (
        "shadowlands",
        ["covenantID", "activeCovenantID", "renownByCovenant", "korthia", "zerethMortis", "helswornChest"],
    ),
    ("battleForAzeroth", ["intro", "footholds", "nazjatar", "mechagon", "cloak", "taptaf"]),
    (
        "legion",
        [
            "chromieDeathIntro",
            "artifacts",
            "classHall",
            "suramar",
            "helarjarWorldQuests",
            "brokenShore",
            "championsOfLegionfall",
            "argus",
            "worthItsWeight",
        ],
    ),
    (
        "warlordsOfDraenor",
        ["garrisonLevel", "tanaan", "mageTower", "stables", "bank", "tradingPost", "mining", "herbGarden"],
    ),
    ("mistsOfPandaria", ["isleOfThunder", "sunsongRanch"]),
    ("cataclysm", ["moltenFront", "vashjir", "twilightHighlands"]),
    ("classic", ["aq40"]),
]

# Old saved values the addon no longer defines for that expansion.
IGNORED = {("dragonflight", "silasSecretStash")}
