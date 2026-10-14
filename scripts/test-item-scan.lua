-- Run from the addon root with Lua 5.1.
local ATA = {db = {characters = {}}}
function CreateFrame()
    return {RegisterEvent = function() end, SetScript = function() end}
end
function UnitGUID() return "player" end
function UnitName() return "Test" end
function GetRealmName() return "Test" end
function UnitRace() return "Human" end
function UnitSex() return 2 end
function UnitClass() return "Warrior", "WARRIOR" end
function UnitFactionGroup() return "Alliance" end
function UnitLevel() return 90 end
function time() return 100 end
C_QuestLog = {IsQuestFlaggedCompleted = function() return false end}
ATA.IsTrackerEnabled = function() return true end
ATA.ScanProfessions = function() end
ATA.ScanQuestLog = function() end
assert(loadfile("Features/Midnight.lua"))("ATA", ATA)
ATA.trackerDefinitions = {items = {checks = {
    {id = "personal", itemID = 1, includeAccountBank = false},
    {id = "warband", itemID = 2},
    {id = "artifacts", itemIDsByClass = {WARRIOR = {3, 4}}},
}}}
local calls = {}
local function count(id, bank, charges, reagent, account)
    calls[id] = {bank, charges, reagent, account}
    return id == 4 and 0 or 1
end
GetItemCount = function() error("Legacy API must not be used when C_Item is available") end
C_Item = {GetItemCount = count}
local ok, record = ATA:ScanCurrentCharacter()
assert(ok and record.progress.items.personal and record.progress.items.warband)
assert(record.progress.items.artifacts == 1)
assert(calls[1][4] == false and calls[2][4] == true)
assert(calls[3][2] == true and calls[3][4] == true)
C_Item, GetItemCount = nil, count
assert(ATA:ScanCurrentCharacter())
GetItemCount = nil
local success, message = ATA:ScanCurrentCharacter()
assert(not success and message == "The item count API is unavailable.")
print("Current and legacy item APIs, bank scope, and artifact scans passed.")
