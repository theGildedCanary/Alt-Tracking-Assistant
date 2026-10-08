local _, ATA = ...

ATA.trackerDefinitions = ATA.trackerDefinitions or {}
ATA.trackerDefinitions.classic = {
    name = "Classic",
    checks = {
        {
            id = "aq40",
            label = "AQ40",
            type = "reputation",
            factionID = 910,
            reputationMax = 42000,
        },
    },
}
