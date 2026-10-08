local _, ATA = ...

ATA.trackerDefinitions = ATA.trackerDefinitions or {}
ATA.trackerDefinitions.darkmoonFaire = {
    name = "Darkmoon Faire",
    checks = {
        {
            id = "silasSecretStash",
            label = "Silas' Secret Stash",
            questIDs = { 38934 },
            itemID = 127148,
            retainCompletion = true,
            legacyProgress = {
                expansionKey = "dragonflight",
                checkID = "silasSecretStash",
            },
        },
    },
}
