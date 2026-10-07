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

    ATA.db = AltTrackingAssistantDB
end)
