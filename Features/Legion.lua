local _, ATA = ...

ATA.trackerDefinitions = ATA.trackerDefinitions or {}
ATA.trackerDefinitions.legion = {
    name = "Legion",
    checks = {
        {
            id = "chromieDeathIntro",
            label = "Chromie Death Intro",
            questIDs = { 47543 },
        },
        {
            id = "artifacts",
            label = "Artifacts",
            type = "count",
            max = 3,
            maxByClass = {
                DEMONHUNTER = 2,
                DRUID = 4,
            },
            itemIDsByClass = {
                DEATHKNIGHT = { 128402, 128292, 128403 },
                DEMONHUNTER = { 127829, 128832 },
                DRUID = { 128858, 128860, 128821, 128306 },
                HUNTER = { 128861, 128826, 128808 },
                MAGE = { 127857, 128820, 128862 },
                MONK = { 128938, 128937, 128940 },
                PALADIN = { 128823, 128866, 120978 },
                PRIEST = { 128868, 128825, 128827 },
                ROGUE = { 128870, 128872, 128476 },
                SHAMAN = { 128935, 128819, 128911 },
                WARLOCK = { 128942, 128943, 128941 },
                WARRIOR = { 128910, 128908, 128289 },
            },
        },
        {
            id = "classHall",
            label = "Class Hall",
            questIDsByClass = {
                DEATHKNIGHT = { 43264 },
                DEMONHUNTER = { 42670, 42671 },
                DRUID = { 42583 },
                HUNTER = { 42519 },
                MAGE = { 42663 },
                MONK = { 42187 },
                PALADIN = { 39696 },
                PRIEST = { 43270 },
                ROGUE = { 42139 },
                SHAMAN = { 42383 },
                WARLOCK = { 42608 },
                WARRIOR = { 42598 },
            },
        },
        {
            id = "suramar",
            label = "Suramar",
            questIDs = { 42229 },
        },
        {
            id = "helarjarWorldQuests",
            label = "Helarjar Wqs",
            questIDs = { 44721 },
        },
        {
            id = "brokenShore",
            label = "Broken Shore",
            questIDs = { 46734 },
        },
        {
            id = "championsOfLegionfall",
            label = "Champions of Legionfall",
            questIDs = { 47137 },
        },
        {
            id = "argus",
            label = "Argus",
            questIDs = { 48440 },
        },
        {
            id = "worthItsWeight",
            label = "Worth Its Weight",
            questIDs = { 41176 },
            retainCompletion = true,
        },
    },
}
