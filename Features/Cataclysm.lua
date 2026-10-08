local _, ATA = ...

ATA.trackerDefinitions = ATA.trackerDefinitions or {}
ATA.trackerDefinitions.cataclysm = {
    name = "Cataclysm",
    checks = {
        {
            id = "moltenFront",
            label = "Molten Front",
            questIDs = { 29201 },
        },
        {
            id = "vashjir",
            label = "Vashj'ir",
            questIDs = { 25587 },
        },
        {
            id = "twilightHighlands",
            label = "Twilight Highlands",
            questIDs = { 27545, 26840 },
        },
    },
}
