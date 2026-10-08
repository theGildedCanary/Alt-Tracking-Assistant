local _, ATA = ...

ATA.trackerDefinitions = ATA.trackerDefinitions or {}
ATA.trackerDefinitions.warlordsOfDraenor = {
    name = "Warlords of Draenor",
    checks = {
        {
            id = "garrisonLevel",
            label = "Garrison",
            type = "count",
            max = 3,
            questIDGroups = {
                { 34586, 34378 },
                { 36592, 36567 },
                { 36615, 36614 },
            },
        },
        {
            id = "tanaan",
            label = "Tanaan Base",
            questIDs = { 38445, 37935 },
        },
        {
            id = "mageTower",
            label = "Mage Portals",
            garrisonBuildingID = 39,
            retainCompletion = true,
        },
        {
            id = "stables",
            label = "Stables",
            garrisonBuildingID = 67,
            retainCompletion = true,
        },
        {
            id = "bank",
            label = "Bank / Storehouse",
            garrisonBuildingID = 143,
            retainCompletion = true,
        },
        {
            id = "tradingPost",
            label = "Trading Post",
            garrisonBuildingID = 145,
            retainCompletion = true,
        },
        {
            id = "mining",
            label = "Mining",
            questIDs = { 34192, 35154 },
        },
        {
            id = "herbGarden",
            label = "Herb Garden",
            questIDs = { 36404, 34193 },
        },
    },
}
