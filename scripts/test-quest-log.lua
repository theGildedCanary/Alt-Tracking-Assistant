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
            SetScript = function(_, _, fn) callbacks.event = fn end}
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
assert(record.questLog.quests["42"].status == "Not picked up")
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
assert(unselected.questLog == nil)
AltTrackingAssistantQuestSync.a = {["43"] = true}
infoAvailable, titleAvailable = false, false
ATA:ScanQuestLog(record)
ATA:ScanQuestLog(record)
assert(requests == 1)
assert(record.questLog.quests["43"].reset == "Unknown")
assert(record.questLog.quests["42"] == nil)
ATA.db = {characters = {a = record}}
assert(events.QUEST_ACCEPTED and events.QUEST_REMOVED and events.QUEST_DATA_LOAD_RESULT)
callbacks.event()
assert(callbacks.timer)
callbacks.timer()
function GetQuestResetTime() return 1700000000 end
ATA:ScanQuestLog(record)
assert(record.questLog.nextDailyReset == nil)
print("Quest Log addon behavior checks passed.")
