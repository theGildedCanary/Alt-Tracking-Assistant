local _, ATA = ...

ATA.trackerDefinitions = ATA.trackerDefinitions or {}
ATA.trackerDefinitions.battleForAzeroth = {
    name = "Battle for Azeroth",
    checks = {
        {
            id = "intro",
            label = "BFA Intro",
            questIDs = { 47189, 52131 },
        },
        {
            id = "footholds",
            label = "Footholds",
            type = "count",
            max = 3,
            questIDGroups = {
                { 51968, 51984 },
                { 51967, 51985 },
                { 51969, 51986 },
            },
        },
        {
            id = "nazjatar",
            label = "Nazjatar",
            questIDs = { 54972, 55053 },
        },
        {
            id = "mechagon",
            label = "Mechagon",
            questIDs = { 55736 },
        },
        {
            id = "cloak",
            label = "BFA Cloak",
            itemID = 169223,
        },
        {
            id = "taptaf",
            label = "Taptaf",
            questIDs = { 52061 },
        },
    },
}
