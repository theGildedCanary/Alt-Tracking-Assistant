local _, ATA = ...

function ATA:ScanQuestLog(record)
    local assignments = _G.AltTrackingAssistantQuestSync or {}
    local selected = assignments[record.guid]
    if type(selected) ~= "table" then return end
    local now = GetServerTime()
    local previous = record.questLog or {}
    local quests = {}
    for key in pairs(selected) do
        local id = tonumber(key)
        if id and id > 0 then
            local old = (previous.quests or {})[tostring(id)] or {}
            local index = C_QuestLog.GetLogIndexForQuestID(id)
            local info = index and index > 0 and C_QuestLog.GetInfo(index)
            local title = C_QuestLog.GetTitleForQuestID(id)
            local reset = old.reset or "Unknown"
            if info and info.frequency ~= nil then
                reset = info.frequency == Enum.QuestFrequency.Daily and "Daily"
                    or info.frequency == Enum.QuestFrequency.Weekly and "Weekly" or "None"
            end
            local pickedUp = C_QuestLog.IsOnQuest(id)
            local completed = C_QuestLog.IsQuestFlaggedCompleted(id)
            local ready = pickedUp and C_QuestLog.IsComplete(id) or false
            local started = ready
            local objectives = pickedUp and C_QuestLog.GetQuestObjectives(id) or nil
            for _, objective in ipairs(objectives or {}) do
                if objective.finished or (objective.numFulfilled or 0) > 0 then
                    started = true
                end
            end
            local status = "Not picked up"
            if completed then
                status = "Completed"
            elseif pickedUp then
                status = started and "In progress" or objectives and "Picked up" or "Awaiting objectives"
            end
            quests[tostring(id)] = {
                title = title or old.title, reset = reset, pickedUp = pickedUp,
                readyToTurnIn = ready, started = started, objectivesKnown = objectives ~= nil,
                status = status,
                scannedAt = now,
            }
            if not title and not old.title and not self.questDataRequested[id] then
                self.questDataRequested[id] = true
                C_QuestLog.RequestLoadQuestByID(id)
            end
        end
    end
    local daily = GetQuestResetTime()
    local weekly = C_DateAndTime and C_DateAndTime.GetSecondsUntilWeeklyReset and C_DateAndTime.GetSecondsUntilWeeklyReset()
    record.questLog = { quests = quests, scannedAt = now,
        nextDailyReset = type(daily) == "number" and daily > 0 and daily <= 86400 and now + daily or nil,
        nextWeeklyReset = type(weekly) == "number" and weekly > 0 and weekly <= 604800 and now + weekly or nil,
    }
end

ATA.questDataRequested = {}
local frame = CreateFrame("Frame")
for _, event in ipairs({"PLAYER_LOGIN", "QUEST_LOG_UPDATE", "QUEST_ACCEPTED", "QUEST_REMOVED", "QUEST_TURNED_IN", "QUEST_DATA_LOAD_RESULT"}) do
    frame:RegisterEvent(event)
end
local scheduled = false
frame:SetScript("OnEvent", function()
    if scheduled then return end
    scheduled = true
    C_Timer.After(0.5, function()
        scheduled = false
        local guid = UnitGUID("player")
        local record = ATA.db and ATA.db.characters[guid]
        if record then ATA:ScanQuestLog(record) end
    end)
end)
