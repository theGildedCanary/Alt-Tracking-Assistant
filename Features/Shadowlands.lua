local _, ATA = ...

local covenants = {
    {
        id = 1,
        name = "Kyrian",
        icon = "Interface\\Icons\\Ability_Bastion_Covenant",
        color = { 181 / 255, 208 / 255, 241 / 255 },
    },
    {
        id = 3,
        name = "Night Fae",
        icon = "Interface\\Icons\\Ability_Ardenweald_Covenant",
        color = { 200 / 255, 188 / 255, 222 / 255 },
    },
    {
        id = 4,
        name = "Necrolord",
        icon = "Interface\\Icons\\Ability_Maldraxxus_Covenant",
        color = { 179 / 255, 225 / 255, 213 / 255 },
    },
    {
        id = 2,
        name = "Venthyr",
        icon = "Interface\\Icons\\Ability_Revendreth_Covenant",
        color = { 221 / 255, 185 / 255, 185 / 255 },
    },
}

ATA.shadowlandsCovenants = covenants
ATA.trackerDefinitions = ATA.trackerDefinitions or {}
ATA.trackerDefinitions.shadowlands = {
    name = "Shadowlands",
    watchAllQuestTurnIns = true,
    checks = {
        {
            id = "covenant",
            label = "Covenant",
            settingsLabel = "View Covenant",
            type = "select",
        },
        {
            id = "anima",
            label = "4k Anima",
            type = "count",
            max = 4,
        },
        {
            id = "renown",
            label = "Renown",
            type = "count",
            max = 80,
        },
        {
            id = "korthia",
            label = "Korthia",
            questIDs = { 63665, 63944 },
        },
        {
            id = "zerethMortis",
            label = "Zereth Mortis",
            questIDs = { 64957 },
        },
        {
            id = "helswornChest",
            label = "Helsworn Chest",
            questIDs = { 64256 },
        },
    },
    scan = function(previousProgress)
        local activeCovenantID = C_Covenants and C_Covenants.GetActiveCovenantID
            and C_Covenants.GetActiveCovenantID()
        local covenantID = previousProgress and previousProgress.covenantID
        if not covenantID or covenantID < 1 or covenantID > #covenants then
            covenantID = activeCovenantID
        end

        local renownByCovenant = {}
        for _, covenant in ipairs(covenants) do
            local previousRenown = previousProgress
                and previousProgress.renownByCovenant
                and previousProgress.renownByCovenant[covenant.id]
            if type(previousRenown) == "number" then
                renownByCovenant[covenant.id] = previousRenown
            end

            if C_CovenantSanctumUI and C_CovenantSanctumUI.GetRenownLevels then
                local levels = C_CovenantSanctumUI.GetRenownLevels(covenant.id)
                if type(levels) == "table" then
                    local currentLevel
                    for _, levelInfo in ipairs(levels) do
                        if type(levelInfo.level) == "number" and not levelInfo.locked then
                            currentLevel = math.max(currentLevel or 0, levelInfo.level)
                        end
                    end
                    if currentLevel then
                        renownByCovenant[covenant.id] = currentLevel
                    end
                end
            end
        end

        if type(activeCovenantID) == "number"
            and activeCovenantID > 0
            and C_CovenantSanctumUI
            and C_CovenantSanctumUI.GetRenownLevel
        then
            local activeRenown = C_CovenantSanctumUI.GetRenownLevel()
            if type(activeRenown) == "number" then
                renownByCovenant[activeCovenantID] = activeRenown
            end
        end

        local progress = {
            covenantID = covenantID,
            activeCovenantID = activeCovenantID,
            renownByCovenant = renownByCovenant,
        }

        for _, check in ipairs({
            { id = "korthia", questIDs = { 63665, 63944 } },
            { id = "zerethMortis", questIDs = { 64957 } },
            { id = "helswornChest", questIDs = { 64256 } },
        }) do
            progress[check.id] = false
            for _, questID in ipairs(check.questIDs) do
                local completed = C_QuestLog.IsQuestFlaggedCompleted(questID)
                if type(completed) ~= "boolean" then
                    return nil, "Quest completion could not be read for quest " .. questID .. "."
                end
                if completed then
                    progress[check.id] = true
                    break
                end
            end
        end

        return progress
    end,
    getProgress = function(savedProgress)
        local selectedCovenantID = savedProgress.covenantID
        local renownCovenantID = selectedCovenantID
        if not ATA:IsTrackerEnabled("shadowlands", "covenant") then
            renownCovenantID = savedProgress.activeCovenantID
        end
        local animaCount = 0
        for _, covenant in ipairs(covenants) do
            if (savedProgress.renownByCovenant or {})[covenant.id]
                and savedProgress.renownByCovenant[covenant.id] >= 60
            then
                animaCount = animaCount + 1
            end
        end

        return {
            covenant = selectedCovenantID,
            activeCovenantID = savedProgress.activeCovenantID,
            anima = animaCount,
            renown = renownCovenantID
                and (savedProgress.renownByCovenant or {})[renownCovenantID],
            korthia = savedProgress.korthia,
            zerethMortis = savedProgress.zerethMortis,
            helswornChest = savedProgress.helswornChest,
        }
    end,
}
