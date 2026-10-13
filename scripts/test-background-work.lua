-- Run from the addon root with Lua.
local ATA = {}
local scripts, timers = {}, {}
local clock, combat = 0, false
function CreateFrame()
    return {RegisterEvent = function() end,
        SetScript = function(_, name, fn) scripts[name] = fn end}
end
function GetTime() return clock end
function InCombatLockdown() return combat end
function UnitGUID() return "player" end
C_Timer = {After = function(delay, fn) timers[#timers + 1] = {delay, fn} end}
assert(loadfile("Features/Midnight.lua"))("ATA", ATA)
local scans = 0
ATA.ScanCurrentCharacter = function() scans = scans + 1; return true, {level10Date = 1} end
scripts.OnEvent(nil, "BAG_UPDATE_DELAYED")
scripts.OnEvent(nil, "TRADE_SKILL_LIST_UPDATE")
assert(#timers == 1)
clock = 2; timers[1][2]()
assert(scans == 1)
scripts.OnEvent(nil, "BAG_UPDATE_DELAYED")
assert(timers[2][1] == 15)
combat = true; clock = 17; timers[2][2]()
assert(scans == 1 and timers[3][1] == 5)
combat = false; clock = 22; timers[3][2]()
assert(scans == 2)

timers = {}
assert(loadfile("Features/QuestLog.lua"))("ATA", ATA)
ATA.db = {characters = {player = {guid = "player"}}}
ATA.ScanQuestLog = function() scans = scans + 1 end
scripts.OnEvent(nil, "PLAYER_ENTERING_WORLD")
timers[1][2]()
local before = scans
scripts.OnEvent(nil, "QUEST_DATA_LOAD_RESULT", 999)
assert(#timers == 1)
scripts.OnEvent(nil, "QUEST_LOG_UPDATE")
scripts.OnEvent(nil, "QUEST_LOG_UPDATE")
assert(#timers == 2 and timers[2][1] == 2)
combat = true; timers[2][2]()
assert(scans == before and timers[3][1] == 5)
combat = false; timers[3][2]()
assert(scans == before + 1)
print("Background scan throttling and combat deferral checks passed.")
