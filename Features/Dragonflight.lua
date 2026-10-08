local _, ATA = ...

ATA.trackerDefinitions = ATA.trackerDefinitions or {}
ATA.trackerDefinitions.dragonflight = {
    name = "Dragonflight",
    checks = {
        {
            id = "introSkip",
            label = "Intro Skip",
            questIDs = { 66221, 72293 },
        },
        {
            id = "fiveSparks",
            label = "5x Sparks",
            questIDs = { 70900 },
        },
        {
            id = "forbiddenReach",
            label = "Forbidden Reach",
            questIDs = { 73076 },
        },
        {
            id = "suffusionCamp",
            label = "Suffusion Camp",
            questIDs = { 75887 },
        },
        {
            id = "zaralekCaverns",
            label = "Zaralek Caverns",
            questIDs = { 75643 },
        },
        {
            id = "emeraldDream",
            label = "Emerald Dream",
            questIDs = { 77283 },
        },
        {
            id = "elegantCanvasBrush",
            label = "Elegant Canvas Brush",
            achievementID = 16301,
        },
    },
}
