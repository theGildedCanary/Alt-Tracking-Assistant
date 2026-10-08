local _, ATA = ...

ATA.trackerDefinitions = ATA.trackerDefinitions or {}
ATA.trackerDefinitions.theWarWithin = {
    name = "The War Within",
    checks = {
        {
            id = "introSkip",
            label = "Intro Skip",
            questIDs = { 83543 },
        },
        {
            id = "craftingToOrder",
            label = "Crafting to Order",
            questIDs = { 84260 },
        },
        {
            id = "undermine",
            label = "Undermine",
            questIDs = { 83151 },
        },
        {
            id = "delveBelt",
            label = "Delve Belt",
            questIDs = { 91009 },
        },
        {
            id = "reshiiWraps",
            label = "Reshii Wraps",
            itemID = 235499,
        },
    },
}
