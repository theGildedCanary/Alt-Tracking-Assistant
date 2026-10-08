local _, ATA = ...

ATA.trackerDefinitions = ATA.trackerDefinitions or {}
ATA.trackerDefinitions.mistsOfPandaria = {
    name = "Mists of Pandaria",
    checks = {
        {
            id = "isleOfThunder",
            label = "Isle of Thunder",
            questIDs = { 32681, 32680 },
        },
        {
            id = "sunsongRanch",
            label = "Sunsong Ranch",
            questIDs = { 30256 },
        },
    },
}
