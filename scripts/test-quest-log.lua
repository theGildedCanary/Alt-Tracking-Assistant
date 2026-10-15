-- Run from the addon root with Lua 5.1 (or a Lua 5.1 host).
local ATA = {}
local events, callbacks = {}, {}
local now, onQuest, completed, frequency = 100, true, false, 1
local infoAvailable, titleAvailable = true, true
local requests = 0
local fulfilled, ready = 0, false
function time() return now end
function GetServerTime() return now end
function UnitGUID() return "a" end
function InCombatLockdown() return false end
function GetQuestResetTime() return 100 end
C_DateAndTime = {GetSecondsUntilWeeklyReset = function() return 400 end}
Enum = {QuestFrequency = {Daily = 1, Weekly = 2}}
C_QuestLog = {
    GetLogIndexForQuestID = function() return infoAvailable and 1 or nil end,
    GetInfo = function() return {frequency = frequency} end,
    GetTitleForQuestID = function() return titleAvailable and "Test quest" or nil end,
    IsOnQuest = function() return onQuest end,
    IsQuestFlaggedCompleted = function() return completed end,
    IsComplete = function() return ready end,
    GetQuestObjectives = function() return {{numFulfilled = fulfilled, numRequired = 5, finished = false}} end,
    RequestLoadQuestByID = function() requests = requests + 1 end,
}
function CreateFrame()
    return {RegisterEvent = function(_, event) events[event] = true end,
            SetScript = function(_, name, fn) callbacks[name] = fn end}
end
C_Timer = {After = function(_, fn) callbacks.timer = fn end}
assert(loadfile("Features/QuestLog.lua"))("AltTrackingAssistant", ATA)
AltTrackingAssistantQuestSync = {a = {["42"] = true}, b = {}}
local record = {guid = "a"}
ATA:ScanQuestLog(record)
assert(record.questLog.quests["42"].status == "Picked up")
assert(record.questLog.quests["42"].started == false)
fulfilled = 1
ATA:ScanQuestLog(record)
assert(record.questLog.quests["42"].status == "In progress")
assert(record.questLog.quests["42"].pickedUp == true)
assert(record.questLog.quests["42"].readyToTurnIn == false)
fulfilled, ready = 5, true
ATA:ScanQuestLog(record)
assert(record.questLog.quests["42"].readyToTurnIn == true)
assert(record.questLog.quests["42"].reset == "Daily")
assert(record.questLog.nextDailyReset == 200)
assert(record.questLog.nextWeeklyReset == 500)
onQuest, completed, infoAvailable = false, true, false
ATA:ScanQuestLog(record)
assert(record.questLog.quests["42"].status == "Completed")
assert(record.questLog.quests["42"].reset == "Daily")
completed = false
ATA:ScanQuestLog(record)
assert(record.questLog.quests["42"].status == "Completed")
assert(record.questLog.quests["42"].completedUntil == 200)
now = 200
ATA:ScanQuestLog(record)
assert(record.questLog.quests["42"].status == "Not picked up")
now = 100
infoAvailable, frequency = true, 2
ATA:ScanQuestLog(record)
assert(record.questLog.quests["42"].reset == "Weekly")
frequency = 0
ATA:ScanQuestLog(record)
assert(record.questLog.quests["42"].reset == "None")
local manualOnly = {guid = "b"}
ATA:ScanQuestLog(manualOnly)
assert(manualOnly.questLog.nextDailyReset == 200)
assert(next(manualOnly.questLog.quests) == nil)
local unselected = {guid = "c"}
ATA:ScanQuestLog(unselected)
assert(unselected.questLog.nextDailyReset == 200)
assert(next(unselected.questLog.quests) == nil)
AltTrackingAssistantQuestSync.a = {["43"] = true}
infoAvailable, titleAvailable = false, false
ATA:ScanQuestLog(record)
ATA:ScanQuestLog(record)
assert(requests == 1)
assert(record.questLog.quests["43"].reset == "Unknown")
assert(record.questLog.quests["42"] == nil)
ATA.db = {characters = {a = record}}
assert(events.QUEST_ACCEPTED and events.QUEST_REMOVED and events.QUEST_DATA_LOAD_RESULT)
callbacks.OnEvent(nil, "PLAYER_ENTERING_WORLD")
assert(callbacks.timer)
callbacks.timer()
callbacks.OnEvent(nil, "QUEST_LOG_UPDATE")
assert(callbacks.timer)
callbacks.timer()
function GetQuestResetTime() return 1700000000 end
ATA:ScanQuestLog(record)
assert(record.questLog.nextDailyReset == nil)

-- Any tracked variant records its turn-in immediately, even before a delayed
-- scan runs; cleared API flags and subsequent scans must not erase it.
local weekly = {guid="a", todos={{id="weekly", changedAt=1, questID=42, questIDs={42,43}, resetMode="Weekly"}}}
ATA.db.characters.a = weekly
AltTrackingAssistantQuestSync.a = {}
callbacks.OnEvent(nil, "QUEST_TURNED_IN", 43)
assert(weekly.questLog.quests["43"].status == "Completed")
assert(weekly.questLog.quests["43"].completedUntil == 500)
callbacks.timer()
assert(ATA:TodoState(weekly, weekly.todos[1]) == true)
now = 499
ATA:ScanQuestLog(weekly)
assert(weekly.questLog.quests["43"].completedUntil == 500)
assert(ATA:TodoState(weekly, weekly.todos[1]) == true)
now = 500
ATA:ScanQuestLog(weekly)
assert(ATA:TodoState(weekly, weekly.todos[1]) == false)
callbacks.OnEvent(nil, "QUEST_TURNED_IN", 999)
assert(weekly.questLog.quests["999"] == nil)

-- Repair only the specific mistaken Unity assignment, preserving its schedule.
local unity = {guid="b", todos={{id="unity", changedAt=1, title="Unity vs Void", questID=93745,
    questIDs={93745,93746,93747,93748,93749,93750,93751,93752,93753}, resetMode="Weekly", resetDays={2}}}}
ATA:ScanQuestLog(unity)
assert(unity.todos[1].questID == 93766)
assert(unity.questLog.quests["93767"])
assert(unity.questLog.quests["93745"] == nil)
assert(unity.todos[1].resetDays[1] == 2)
print("Quest Log addon behavior checks passed.")
