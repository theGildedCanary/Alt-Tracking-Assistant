local addonName, ATA = ...

ATA.name = addonName

local eventFrame = CreateFrame("Frame")
eventFrame:RegisterEvent("ADDON_LOADED")

eventFrame:SetScript("OnEvent", function(_, event, loadedAddon)
    if event ~= "ADDON_LOADED" or loadedAddon ~= addonName then
        return
    end

    AltTrackingAssistantDB = AltTrackingAssistantDB or {}
    AltTrackingAssistantDB.characters = AltTrackingAssistantDB.characters or {}
    AltTrackingAssistantDB.settings = AltTrackingAssistantDB.settings or {}
    AltTrackingAssistantDB.settings.armorMains = AltTrackingAssistantDB.settings.armorMains or {}

    ATA.db = AltTrackingAssistantDB

    -- Settings edited in the Companion app arrive through AppSync.lua and are applied once per revision.
    local sync = _G.AltTrackingAssistantAppSync
    local settings = AltTrackingAssistantDB.settings
    if type(sync) == "table" and type(sync.rev) == "number" and sync.rev > (AltTrackingAssistantDB.appSyncRev or 0) then
        if type(sync.characterMains) == "table" then
            settings.characterMains = sync.characterMains
            settings.armorMains = {}
        end
        if type(sync.trackedItems) == "table" then
            settings.trackedItems = sync.trackedItems
        end
        AltTrackingAssistantDB.appSyncRev = sync.rev
    end
end)
