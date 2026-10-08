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
    },
}

local watchedQuests = {}
for _, expansion in pairs(ATA.trackerDefinitions) do
    for _, check in ipairs(expansion.checks) do
        for _, questID in ipairs(check.questIDs or {}) do
            watchedQuests[questID] = true
        end
    end
end

function ATA:ScanCurrentCharacter()
    local guid = UnitGUID("player")
    if not guid or guid == "" then
        return false, "The current character GUID is unavailable."
    end

    if not C_QuestLog or not C_QuestLog.IsQuestFlaggedCompleted then
        return false, "The quest completion API is unavailable."
    end

    local itemCount = C_Item and C_Item.GetItemCount or GetItemCount
    local progress = {}
    for expansionKey, expansion in pairs(self.trackerDefinitions) do
        progress[expansionKey] = {}
        for _, check in ipairs(expansion.checks) do
            local completed = false
            for _, questID in ipairs(check.questIDs or {}) do
                local questCompleted = C_QuestLog.IsQuestFlaggedCompleted(questID)
                if type(questCompleted) ~= "boolean" then
                    return false, "Quest completion could not be read for quest " .. questID .. "."
                end
                if questCompleted then
                    completed = true
                    break
                end
            end

            if check.itemID then
                if not itemCount then
                    return false, "The item count API is unavailable."
                end
                local count = itemCount(check.itemID, true, false, true, true)
                if type(count) ~= "number" then
                    return false, "Item count could not be read for item " .. check.itemID .. "."
                end
                completed = count > 0
            end
            progress[expansionKey][check.id] = completed
        end
    end

    local record = self.db.characters[guid] or {}
    record.guid = guid
    record.name = UnitName("player") or record.name or "Unknown"
    record.realm = GetRealmName() or record.realm or "Unknown"
    record.race = select(1, UnitRace("player")) or record.race
    local className, classFile = UnitClass("player")
    record.class = className or record.class
    record.classFile = classFile or record.classFile
    record.faction = UnitFactionGroup("player") or record.faction
    record.level = UnitLevel("player") or record.level
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
scanFrame:RegisterEvent("QUEST_TURNED_IN")
scanFrame:RegisterEvent("BAG_UPDATE_DELAYED")
scanFrame:RegisterEvent("PLAYERBANKSLOTS_CHANGED")
scanFrame:RegisterEvent("BANKFRAME_OPENED")
scanFrame:SetScript("OnEvent", function(_, event, questID)
    if event == "QUEST_TURNED_IN" and not watchedQuests[questID] then
        return
    end

    local success, message = ATA:ScanCurrentCharacter()
    if not success then
        print("|cffff4444Alt Tracking Assistant:|r " .. message)
    elseif ATA.UpdateReport then
        ATA:UpdateReport()
    end
end)
