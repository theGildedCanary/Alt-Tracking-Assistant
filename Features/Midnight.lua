local _, ATA = ...

ATA.trackerDefinitions = ATA.trackerDefinitions or {}
ATA.trackerDefinitions.midnight = {
    name = "Midnight",
    checks = {
        {
            id = "introSkip",
            label = "Intro Skip",
            questIDs = { 94993, 95008 },
        },
        {
            id = "craftersNeeded",
            label = "Crafters Needed",
            questIDs = { 93723 },
        },
        {
            id = "valNaigtalSkip",
            label = "Val / Naigtal Skip",
            questIDs = { 97071, 97072 },
        },
        {
            id = "coilIsleSkip",
            label = "Coiled Isle Skip",
            questIDs = { 93012 },
        },
    },
}

local watchedQuests = {}
local watchAllQuestTurnIns = false
for _, expansion in pairs(ATA.trackerDefinitions) do
    watchAllQuestTurnIns = watchAllQuestTurnIns or expansion.watchAllQuestTurnIns == true
    for _, check in ipairs(expansion.checks) do
        for _, questID in ipairs(check.questIDs or {}) do
            watchedQuests[questID] = true
        end
        for _, questGroup in ipairs(check.questIDGroups or {}) do
            for _, questID in ipairs(questGroup) do
                watchedQuests[questID] = true
            end
        end
        for _, classQuestIDs in pairs(check.questIDsByClass or {}) do
            for _, questID in ipairs(classQuestIDs) do
                watchedQuests[questID] = true
            end
        end
    end
end

local function GetLevelTenAchievementDate()
    if not GetAchievementInfo then
        return nil
    end

    local achievementID, _, _, _, month, day, year = GetAchievementInfo(6)
    if achievementID ~= 6
        or type(year) ~= "number"
        or type(month) ~= "number"
        or type(day) ~= "number"
        or year < 1
        or month < 1
        or month > 12
        or day < 1
        or day > 31
    then
        return nil
    end

    local fullYear = year < 100 and year + 2000 or year
    return time({ year = fullYear, month = month, day = day, hour = 12 })
end

local function GetVoidStorageItemIDs()
    if not GetVoidItemInfo
        or not CanUseVoidStorage
        or not CanUseVoidStorage()
        or not C_PlayerInteractionManager
        or not C_PlayerInteractionManager.IsInteractingWithNpcOfType
        or not Enum
        or not Enum.PlayerInteractionType
        or not Enum.PlayerInteractionType.VoidStorageBanker
        or not C_PlayerInteractionManager.IsInteractingWithNpcOfType(
            Enum.PlayerInteractionType.VoidStorageBanker
        )
    then
        return nil
    end

    local itemIDs = {}
    for tab = 1, 2 do
        for slot = 1, 80 do
            local itemID = GetVoidItemInfo(tab, slot)
            if itemID then
                itemIDs[itemID] = true
            end
        end
    end
    return itemIDs
end

function ATA:ScanCurrentCharacter()
    local guid = UnitGUID("player")
    if not guid or guid == "" then
        return false, "The current character GUID is unavailable."
    end

    if not C_QuestLog or not C_QuestLog.IsQuestFlaggedCompleted then
        return false, "The quest completion API is unavailable."
    end

    local itemCount = GetItemCount
    local progress = {}
    local previousRecord = self.db.characters[guid]
    local _, playerClassFile = UnitClass("player")
    local currentVoidStorageItems = GetVoidStorageItemIDs()
    for expansionKey, expansion in pairs(self.trackerDefinitions) do
        if expansion.scan then
            local expansionProgress, scanError = expansion.scan(
                previousRecord and previousRecord.progress and previousRecord.progress[expansionKey]
            )
            if not expansionProgress then
                return false, scanError
            end
            progress[expansionKey] = expansionProgress
        else
            progress[expansionKey] = {}
            for _, check in ipairs(expansion.checks) do
                local previousProgress = previousRecord
                    and previousRecord.progress
                    and previousRecord.progress[expansionKey]
                local completed = check.retainCompletion
                    and previousProgress
                    and previousProgress[check.id] == true
                    or false
                if not completed and check.legacyProgress then
                    local legacyProgress = previousRecord
                        and previousRecord.progress
                        and previousRecord.progress[check.legacyProgress.expansionKey]
                    completed = legacyProgress
                        and legacyProgress[check.legacyProgress.checkID] == true
                        or false
                end
                local questIDs = check.questIDs
                if check.questIDsByClass then
                    questIDs = check.questIDsByClass[playerClassFile] or {}
                end
                for _, questID in ipairs(questIDs or {}) do
                    local questCompleted = C_QuestLog.IsQuestFlaggedCompleted(questID)
                    if type(questCompleted) ~= "boolean" then
                        return false, "Quest completion could not be read for quest " .. questID .. "."
                    end
                    if questCompleted then
                        completed = true
                        break
                    end
                end
                if check.itemIDsByClass then
                    if not itemCount then
                        return false, "The item count API is unavailable."
                    end
                    local artifactItemIDs = check.itemIDsByClass[playerClassFile] or {}
                    local previousExpansionProgress = previousRecord
                        and previousRecord.progress
                        and previousRecord.progress[expansionKey]
                    local voidStorageItems = currentVoidStorageItems
                        or (previousExpansionProgress and previousExpansionProgress.voidStorageItems)
                        or {}
                    progress[expansionKey].voidStorageItems = voidStorageItems
                    local artifactCount = 0
                    for _, itemID in ipairs(artifactItemIDs) do
                        local count = itemCount(itemID, true, true, true, true)
                        if type(count) ~= "number" then
                            return false, "Item count could not be read for item " .. itemID .. "."
                        end
                        if count > 0 or voidStorageItems[itemID] then
                            artifactCount = artifactCount + 1
                        end
                    end
                    progress[expansionKey][check.id] = artifactCount
                end

                if not completed and check.achievementID then
                    if not GetAchievementInfo then
                        return false, "The achievement information API is unavailable."
                    end
                    local achievementID, _, _, _, _, _, _, _, _, _, _, _, wasEarnedByMe =
                        GetAchievementInfo(check.achievementID)
                    if achievementID ~= check.achievementID or type(wasEarnedByMe) ~= "boolean" then
                        return false, "Achievement completion could not be read for achievement "
                            .. check.achievementID
                            .. "."
                    end
                    completed = wasEarnedByMe
                end

                if not completed and check.itemID then
                    if not itemCount then
                        return false, "The item count API is unavailable."
                    end
                    local count = itemCount(check.itemID, true, false, true, true)
                    if type(count) ~= "number" then
                        return false, "Item count could not be read for item " .. check.itemID .. "."
                    end
                    completed = count > 0
                end
                if not check.itemIDsByClass then
                    progress[expansionKey][check.id] = check.type == "count" and 0 or completed
                end
                if check.questIDGroups then
                    local completedGroups = 0
                    for _, questGroup in ipairs(check.questIDGroups) do
                        local groupCompleted = false
                        for _, questID in ipairs(questGroup) do
                            local questCompleted = C_QuestLog.IsQuestFlaggedCompleted(questID)
                            if type(questCompleted) ~= "boolean" then
                                return false, "Quest completion could not be read for quest " .. questID .. "."
                            end
                            groupCompleted = groupCompleted or questCompleted
                        end
                        if groupCompleted then
                            completedGroups = completedGroups + 1
                        end
                    end
                    progress[expansionKey][check.id] = completedGroups
                end
            end
        end
    end

    local record = previousRecord or {}
    record.guid = guid
    record.name = UnitName("player") or record.name or "Unknown"
    record.realm = GetRealmName() or record.realm or "Unknown"
    record.race = select(1, UnitRace("player")) or record.race
    local className, classFile = UnitClass("player")
    record.class = className or record.class
    record.classFile = classFile or record.classFile
    record.faction = UnitFactionGroup("player") or record.faction
    record.level = UnitLevel("player") or record.level
    record.level10Date = GetLevelTenAchievementDate() or record.level10Date
    record.lastScanned = time()
    record.progress = record.progress or {}
    for expansionKey, expansionProgress in pairs(progress) do
        record.progress[expansionKey] = expansionProgress
    end
    self.db.characters[guid] = record

    return true, record
end

local scanFrame = CreateFrame("Frame")
scanFrame:RegisterEvent("PLAYER_LOGIN")
scanFrame:RegisterEvent("PLAYER_ENTERING_WORLD")
scanFrame:RegisterEvent("ACHIEVEMENT_EARNED")
scanFrame:RegisterEvent("COVENANT_CHOSEN")
scanFrame:RegisterEvent("QUEST_TURNED_IN")
scanFrame:RegisterEvent("BAG_UPDATE_DELAYED")
scanFrame:RegisterEvent("PLAYERBANKSLOTS_CHANGED")
scanFrame:RegisterEvent("PLAYER_ACCOUNT_BANK_TAB_SLOTS_CHANGED")
scanFrame:RegisterEvent("PLAYER_EQUIPMENT_CHANGED")
scanFrame:RegisterEvent("BANKFRAME_OPENED")
scanFrame:RegisterEvent("PLAYER_INTERACTION_MANAGER_FRAME_SHOW")
scanFrame:RegisterEvent("VOID_TRANSFER_DONE")
scanFrame:RegisterEvent("VOID_STORAGE_UPDATE")
scanFrame:RegisterEvent("VOID_STORAGE_CONTENTS_UPDATE")
scanFrame:SetScript("OnEvent", function(_, event, questID)
    if event == "QUEST_TURNED_IN" and not watchedQuests[questID] and not watchAllQuestTurnIns then
        return
    end

    local success, message = ATA:ScanCurrentCharacter()
    if not success then
        print("|cffff4444Alt Tracking Assistant:|r " .. message)
        return
    end

    if event == "QUEST_TURNED_IN" then
        local record = message
        for expansionKey, expansion in pairs(ATA.trackerDefinitions) do
            for _, check in ipairs(expansion.checks) do
                if check.retainCompletion then
                    for _, trackedQuestID in ipairs(check.questIDs or {}) do
                        if trackedQuestID == questID then
                            record.progress[expansionKey][check.id] = true
                            break
                        end
                    end
                end
            end
        end
    end

    if ATA.UpdateReport then
        ATA:UpdateReport()
    end

    if event == "PLAYER_ENTERING_WORLD" and not message.level10Date and C_Timer and C_Timer.After then
        local scannedGUID = message.guid
        C_Timer.After(10, function()
            if UnitGUID("player") ~= scannedGUID then
                return
            end

            local retrySuccess, retryResult = ATA:ScanCurrentCharacter()
            if not retrySuccess then
                print("|cffff4444Alt Tracking Assistant:|r " .. retryResult)
                return
            end
            if ATA.UpdateReport then
                ATA:UpdateReport()
            end
        end)
    end
end)
