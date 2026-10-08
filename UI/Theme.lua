local _, ATA = ...

ATA.UI = ATA.UI or {}
ATA.UI.theme = {
    colors = {
        text = { 0.92, 0.94, 0.98, 1 },
        mutedText = { 0.68, 0.73, 0.80, 1 },
        panel = { 17 / 255, 22 / 255, 28 / 255, 1 },
        panelBorder = { 0.74, 0.53, 0.19, 1 },
        divider = { 0.27, 0.34, 0.40, 1 },
        gold = { 0.94, 0.70, 0.25, 1 },
        goldDark = { 0.50, 0.32, 0.10, 1 },
        classFallback = { 0.46, 0.52, 0.58, 1 },
        completed = { 0.30, 0.92, 0.20, 1 },
        incomplete = { 0.68, 0.73, 0.80, 1 },
        expansions = {
            darkmoonFaire = { 53 / 255, 1 / 255, 33 / 255, 1 },
            classic = { 0.20, 0.27, 0.34, 1 },
            burningCrusade = { 0.34, 0.10, 0.47, 1 },
            wrath = { 0.20, 0.39, 0.10, 1 },
            cataclysm = { 0.48, 0.07, 0.18, 1 },
            mistsOfPandaria = { 0.54, 0.30, 0.06, 1 },
            warlordsOfDraenor = { 0.02, 0.34, 0.43, 1 },
            legion = { 26 / 255, 86 / 255, 34 / 255, 1 },
            battleForAzeroth = { 24 / 255, 24 / 255, 84 / 255, 1 },
            shadowlands = { 28 / 255, 72 / 255, 142 / 255, 1 },
            dragonflight = { 4 / 255, 64 / 255, 74 / 255, 1 },
            theWarWithin = { 121 / 255, 45 / 255, 11 / 255, 1 },
            midnight = { 51 / 255, 30 / 255, 83 / 255, 1 },
        },
        progress = {
            battleForAzeroth = { 137 / 255, 174 / 255, 254 / 255, 1 },
            darkmoonFaire = { 251 / 255, 132 / 255, 184 / 255, 1 },
            legion = { 76 / 255, 255 / 255, 109 / 255, 1 },
            shadowlands = { 79 / 255, 207 / 255, 254 / 255, 1 },
            dragonflight = { 32 / 255, 252 / 255, 250 / 255, 1 },
            theWarWithin = { 248 / 255, 149 / 255, 4 / 255, 1 },
            midnight = { 236 / 255, 143 / 255, 248 / 255, 1 },
        },
    },
}
