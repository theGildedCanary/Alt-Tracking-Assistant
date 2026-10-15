local _, ATA = ...

-- Unity's activity variants, rather than the similarly numbered dungeon quests.
local unityQuestIDs = {93766, 93767, 93769, 93889, 93890, 93891, 93892, 93909, 93910, 93911, 93912, 93913, 94457, 95842, 95843}
local function repairUnityAssignment(todo)
    if (todo.title or todo.text) ~= "Unity vs Void" or #(todo.questIDs or {}) ~= 9 then return end
    for index, id in ipairs(todo.questIDs) do if id ~= 93744 + index then return end end
    todo.questIDs = {}
    for index, id in ipairs(unityQuestIDs) do todo.questIDs[index] = id end
    todo.questID = unityQuestIDs[1]
    todo.changedAt = math.max(GetServerTime(), (todo.changedAt or 0) + 1)
end

local function questReset(record, id, fallback)
    for _, todo in ipairs(record.todos or {}) do
        for _, questID in ipairs(todo.questIDs or (todo.questID and {todo.questID}) or {}) do
            if questID == id and todo.resetMode and todo.resetMode ~= "Auto" then
                return todo.resetMode, todo.resetDays
            end
        end
    end
    return fallback
end

local function completionBoundary(record, id, reset, now)
    local mode, days = questReset(record, id, reset)
    if days or mode == "Custom" then return ATA:NextTodoReset(mode, now, days) end
    local seconds = mode == "Daily" and GetQuestResetTime()
        or mode == "Weekly" and C_DateAndTime and C_DateAndTime.GetSecondsUntilWeeklyReset
            and C_DateAndTime.GetSecondsUntilWeeklyReset()
    local limit = mode == "Daily" and 86400 or 604800
    return type(seconds) == "number" and seconds > 0 and seconds <= limit and now + seconds or nil
end

function ATA:RecordQuestTurnIn(record, id)
    self:SyncTodoAssignments(record)
    local tracked = ((_G.AltTrackingAssistantQuestSync or {})[record.guid] or {})[tostring(id)]
    for _, todo in ipairs(record.todos or {}) do
        for _, questID in ipairs(todo.questIDs or (todo.questID and {todo.questID}) or {}) do
            if questID == id then tracked = true end
        end
    end
    if not tracked then return end
    record.questLog = record.questLog or {}
    record.questLog.quests = record.questLog.quests or {}
    local data = record.questLog.quests[tostring(id)] or {}
    local now = GetServerTime()
    data.status, data.pickedUp, data.readyToTurnIn = "Completed", false, false
    data.scannedAt = now
    data.completedUntil = completionBoundary(record, id, data.reset or "Unknown", now)
    record.questLog.quests[tostring(id)] = data
end

function ATA:ScanQuestLog(record)
    local assignments = _G.AltTrackingAssistantQuestSync or {}
    local selected = assignments[record.guid]
    selected = type(selected) == "table" and selected or {}
    self:SyncTodoAssignments(record)
    local ids = {}
    for key in pairs(selected) do if tonumber(key) then ids[key] = true end end
    for _, todo in ipairs(record.todos) do
        for _, id in ipairs(todo.questIDs or (todo.questID and {todo.questID}) or {}) do ids[tostring(id)] = true end
    end
    local now = GetServerTime()
    local previous = record.questLog or {}
    local quests = {}
    for key in pairs(ids) do
        local id = tonumber(key)
        if id and id > 0 then
            local ok, value = pcall(function()
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
            -- Repeatable quests can clear their completion flag after turn-in.
            -- Keep observed completion through its original reset, across scans/logins.
            local retained = old.status == "Completed" and old.completedUntil and now < old.completedUntil
            completed = completed or retained
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
            local snapshot = {
                title = title or old.title, reset = reset, pickedUp = pickedUp,
                readyToTurnIn = ready, started = started, objectivesKnown = objectives ~= nil,
                status = status,
                scannedAt = now,
                completedUntil = completed and (retained and old.completedUntil or completionBoundary(record, id, reset, now)) or nil,
            }
            if not title and not old.title and not self.questDataRequested[id] then
                self.questDataRequested[id] = true
                if C_QuestLog.RequestLoadQuestByID then pcall(C_QuestLog.RequestLoadQuestByID, id) end
            end
            return snapshot
            end)
            if ok then
                quests[tostring(id)] = value
            else
                quests[tostring(id)] = {status="Scan failed", scannedAt=now, error=tostring(value)}
                print("|cffff4444Alt Tracking Assistant:|r Quest " .. id .. " scan failed: " .. tostring(value))
            end
        end
    end
    local daily = GetQuestResetTime()
    local weekly = C_DateAndTime and C_DateAndTime.GetSecondsUntilWeeklyReset and C_DateAndTime.GetSecondsUntilWeeklyReset()
    local achievements, items = {}, {}
    for _, todo in ipairs(record.todos) do
        if todo.achievementID and GetAchievementInfo then
            local _, title, _, completed, _, _, _, _, _, _, _, _, earned = GetAchievementInfo(todo.achievementID)
            achievements[tostring(todo.achievementID)] = {title=title, status=(earned == true or earned == nil and completed) and "Completed" or "Pending", scannedAt=now}
        elseif todo.itemID and C_Item and C_Item.GetItemCount then
            local count = C_Item.GetItemCount(todo.itemID, true, false, true, false)
            items[tostring(todo.itemID)] = {title=C_Item.GetItemNameByID(todo.itemID), status=count > 0 and "Completed" or "Pending", scannedAt=now}
        end
    end
    record.questLog = { quests = quests, achievements=achievements, items=items, scannedAt = now,
        nextDailyReset = type(daily) == "number" and daily > 0 and daily <= 86400 and now + daily or nil,
        nextWeeklyReset = type(weekly) == "number" and weekly > 0 and weekly <= 604800 and now + weekly or nil,
    }
end

ATA.questDataRequested = {}
local frame = CreateFrame("Frame")
for _, event in ipairs({"PLAYER_LOGIN", "PLAYER_ENTERING_WORLD", "QUEST_LOG_UPDATE", "QUEST_ACCEPTED", "QUEST_REMOVED", "QUEST_TURNED_IN", "QUEST_DATA_LOAD_RESULT", "ACHIEVEMENT_EARNED", "CRITERIA_UPDATE", "BAG_UPDATE_DELAYED", "ITEM_DATA_LOAD_RESULT"}) do
    frame:RegisterEvent(event)
end
local scheduled = false
local worldReady = false
local loginQueued = false
local function scanWhenSafe()
    if InCombatLockdown() then
        C_Timer.After(5, scanWhenSafe)
        return
    end
    local guid = UnitGUID("player")
    local record = ATA.db and ATA.db.characters[guid]
    if record then ATA:ScanQuestLog(record) end
    scheduled = false
end
frame:SetScript("OnEvent", function(_, event, initialLogin, reloadingUI)
    if event == "QUEST_TURNED_IN" then
        local record = ATA.db and ATA.db.characters[UnitGUID("player")]
        if record then ATA:RecordQuestTurnIn(record, initialLogin) end
    end
    -- Other addons request quest data too; only react to our own requests.
    if event == "QUEST_DATA_LOAD_RESULT" and not ATA.questDataRequested[initialLogin] then return end
    if event == "PLAYER_LOGIN" then
        ATA:RefreshCompanionTasks()
        return
    end
    if event == "PLAYER_ENTERING_WORLD" then
        if loginQueued or worldReady then return end
        loginQueued = true
        -- The main character scan also waits three seconds after entering the world.
        -- Run after it so new characters have a record and quest data can populate.
        C_Timer.After(4, function()
            worldReady = true
            local guid = UnitGUID("player")
            local record = ATA.db and ATA.db.characters[guid]
            if not record and ATA.ScanCurrentCharacter then
                ATA:ScanCurrentCharacter()
                record = ATA.db and ATA.db.characters[guid]
            end
            if record then ATA:ScanQuestLog(record) end
        end)
        return
    end
    if not worldReady or scheduled then return end
    scheduled = true
    C_Timer.After(2, scanWhenSafe)
end)

-- Manual reset days use ISO weekdays (Monday=1), at 11 a.m. fixed EDT.
function ATA:NextTodoReset(reset, now, days)
    if reset ~= "Daily" and reset ~= "Weekly" and reset ~= "Custom" then return nil end
    local boundary = math.floor((now - 54000) / 86400) * 86400 + 54000
    for offset=0,7 do
        local candidate = boundary + offset * 86400
        local day = (math.floor(candidate / 86400) + 3) % 7 + 1
        local selected = reset == "Daily" or reset == "Weekly" and #(days or {}) == 0 and day == 2
        if reset == "Custom" or reset == "Weekly" then for _, value in ipairs(days or {}) do if value == day then selected = true end end end
        if candidate > now and selected then return candidate end
    end
end
function ATA:TodoState(record, todo)
    local now = GetServerTime()
    local log = record.questLog or {}
    local data = todo.questID and (log.quests or {})[tostring(todo.questID)]
        or todo.achievementID and (log.achievements or {})[tostring(todo.achievementID)]
        or todo.itemID and (log.items or {})[tostring(todo.itemID)]
    if todo.questIDs and #todo.questIDs > 1 then
        local best, score = nil, -1
        for _, id in ipairs(todo.questIDs) do
            local value = (log.quests or {})[tostring(id)]
            if value then
                local rank = value.status == "Completed" and 10 or value.pickedUp and 5 or 1
                if rank > score then best=value; score=rank end
            end
        end
        data = best
    end
    local automatic = todo.questID or todo.achievementID or todo.itemID
    local reset = todo.questID and ((todo.resetMode and todo.resetMode ~= "Auto") and todo.resetMode or data and data.reset or "Unknown") or todo.reset or "None"
    if automatic then
        local boundary = todo.resetDays and self:NextTodoReset(reset, data and data.scannedAt or log.scannedAt or now, todo.resetDays) or reset == "Daily" and log.nextDailyReset or reset == "Weekly" and log.nextWeeklyReset
        if not data or boundary and now >= boundary then return false, reset, "?" end
        return data.status == "Completed", reset, todo.questID and not data.pickedUp and data.status ~= "Completed" and "o" or nil
    end
    if todo.done == nil then
        todo.done = todo.status == "Completed" or todo.active == false
        todo.active = nil
    end
    local anchor = todo.changedAt or todo.created or record.lastScanned or 0
    local due = todo.resetSchedule == "11amEDT" and todo.resetAt or nil
    due = due or self:NextTodoReset(reset, anchor, todo.resetDays)
    todo.resetSchedule = "11amEDT"
    if due and now >= due then
        todo.done = false; todo.status = "Pending"; todo.changedAt = now
        due = self:NextTodoReset(reset, now, todo.resetDays)
    end
    todo.resetAt = due
    return todo.done, reset
end

function ATA:SyncTodoAssignments(record)
    local selected = (_G.AltTrackingAssistantQuestSync or {})[record.guid] or {}
    record.todos = record.todos or {}
    record.todoDeleted = record.todoDeleted or {}
    for id, stamp in pairs(selected._deleted or {}) do
        record.todoDeleted[id] = math.max(record.todoDeleted[id] or 0, stamp)
    end
    for _, incoming in ipairs(selected._tasks or {}) do
        local found
        for _, todo in ipairs(record.todos) do if todo.id == incoming.id then found = todo; break end end
        if (record.todoDeleted[incoming.id] or 0) < (incoming.changedAt or 0) then
            if not found then found = {}; table.insert(record.todos, found) end
            if (incoming.changedAt or 0) > (found.changedAt or -1) then
                for key, value in pairs(incoming) do found[key] = value end
                found.text = incoming.title
                found.done = incoming.status == "Completed"
            end
        end
    end
    for index = #record.todos, 1, -1 do
        local todo = record.todos[index]
        if (record.todoDeleted[todo.id] or 0) >= (todo.changedAt or todo.created or 0) then table.remove(record.todos, index) end
    end
    for _, todo in ipairs(record.todos) do repairUnityAssignment(todo) end
    -- Catch up missed resets before imported/saved tasks are shown, including
    -- login after the deadline and new assignments imported after login.
    for _, todo in ipairs(record.todos) do
        if not (todo.questID or todo.achievementID or todo.itemID) then self:TodoState(record, todo) end
    end
end

function ATA:RefreshCompanionTasks()
    for _, record in pairs(self.db and self.db.characters or {}) do
        self:SyncTodoAssignments(record)
        for _, todo in ipairs(record.todos or {}) do
            self:TodoState(record, todo)
        end
    end
end

-- Apply manual resets even when the Notes panel is closed and no quest events fire.
local resetElapsed = 0
frame:SetScript("OnUpdate", function(_, elapsed)
    resetElapsed = resetElapsed + elapsed
    if resetElapsed < 5 then return end
    resetElapsed = 0
    for _, record in pairs(ATA.db and ATA.db.characters or {}) do
        for _, todo in ipairs(record.todos or {}) do
            if not (todo.questID or todo.achievementID or todo.itemID) then ATA:TodoState(record, todo) end
        end
    end
end)
