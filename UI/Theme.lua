local _, ATA = ...

ATA.UI = ATA.UI or {}
ATA.UI.theme = {
    colors = {
        text = { 0.92, 0.90, 0.84, 1 },
        mutedText = { 0.65, 0.63, 0.58, 1 },
        panel = { 36 / 255, 33 / 255, 27 / 255, 1 },
        panelBorder = { 0.34, 0.31, 0.24, 1 },
        divider = { 0.24, 0.22, 0.17, 1 },
        gold = { 0.94, 0.70, 0.25, 1 },
        goldDark = { 0.50, 0.32, 0.10, 1 },
        control = { 0.10, 0.09, 0.07, 1 },
        controlHover = { 0.18, 0.15, 0.09, 1 },
        scrollTrack = { 0.055, 0.050, 0.040, 1 },
        tabGlow = { 0.94, 0.70, 0.25, 1 },
        professionProgress = { 0.35, 0.60, 1, 1 },
        rosterRow = { 0.14, 0.13, 0.105, 1 },
        rosterSelected = { 0.25, 0.20, 0.11, 1 },
        rosterHover = { 0.94, 0.70, 0.25, 0.10 },
        classFallback = { 0.46, 0.52, 0.58, 1 },
        completed = { 0.30, 0.92, 0.20, 1 },
        incomplete = { 0.68, 0.73, 0.80, 1 },
        expansions = {
            darkmoonFaire = { 53 / 255, 1 / 255, 33 / 255, 1 },
            classic = { 70 / 255, 20 / 255, 59 / 255, 1 },
            burningCrusade = { 0.34, 0.10, 0.47, 1 },
            wrath = { 0.20, 0.39, 0.10, 1 },
            cataclysm = { 69 / 255, 55 / 255, 19 / 255, 1 },
            mistsOfPandaria = { 0 / 255, 75 / 255, 62 / 255, 1 },
            warlordsOfDraenor = { 70 / 255, 25 / 255, 20 / 255, 1 },
            legion = { 10 / 255, 51 / 255, 20 / 255, 1 },
            battleForAzeroth = { 24 / 255, 24 / 255, 84 / 255, 1 },
            shadowlands = { 28 / 255, 72 / 255, 142 / 255, 1 },
            dragonflight = { 4 / 255, 64 / 255, 74 / 255, 1 },
            theWarWithin = { 121 / 255, 45 / 255, 11 / 255, 1 },
            midnight = { 51 / 255, 30 / 255, 83 / 255, 1 },
        },
        progress = {
            battleForAzeroth = { 137 / 255, 174 / 255, 254 / 255, 1 },
            darkmoonFaire = { 251 / 255, 132 / 255, 184 / 255, 1 },
            legion = { 76 / 255, 255 / 255, 109 / 255, 1 },
            warlordsOfDraenor = { 254 / 255, 90 / 255, 75 / 255, 1 },
            mistsOfPandaria = { 75 / 255, 254 / 255, 192 / 255, 1 },
            cataclysm = { 254 / 255, 249 / 255, 135 / 255, 1 },
            classic = { 254 / 255, 135 / 255, 213 / 255, 1 },
            shadowlands = { 79 / 255, 207 / 255, 254 / 255, 1 },
            dragonflight = { 32 / 255, 252 / 255, 250 / 255, 1 },
            theWarWithin = { 248 / 255, 149 / 255, 4 / 255, 1 },
            midnight = { 236 / 255, 143 / 255, 248 / 255, 1 },
        },
    },
}

-- A shared Blizzard slider for each of ATA's ScrollFrames. The 16px arrow
-- buttons extend above and below the slider; callers reserve that space.
function ATA.UI.CreateBlizzardScrollBar(parent, scroll, name, step)
    local bar = CreateFrame("Slider", name, parent, "UIPanelScrollBarTemplate")
    bar:SetScript("OnValueChanged", nil)
    bar:SetWidth(16)
    bar:SetMinMaxValues(0, 0)
    bar:SetValueStep(1)
    bar.scrollStep = step
    bar:SetValue(0)
    bar:Hide()

    local updating = false
    local up = bar.ScrollUpButton or _G[name .. "ScrollUpButton"]
    local down = bar.ScrollDownButton or _G[name .. "ScrollDownButton"]
    local function Update()
        if updating then return end
        updating = true
        local maximum = math.max(0, scroll:GetVerticalScrollRange())
        local value = math.max(0, math.min(maximum, scroll:GetVerticalScroll()))
        if scroll:GetVerticalScroll() ~= value then scroll:SetVerticalScroll(value) end
        bar:SetMinMaxValues(0, maximum)
        bar:SetValue(value)
        bar:SetShown(maximum > 0 and scroll:IsShown())
        if up then up:SetEnabled(value > 0) end
        if down then down:SetEnabled(value < maximum) end
        updating = false
    end
    bar:SetScript("OnValueChanged", function(_, value)
        if not updating then
            scroll:SetVerticalScroll(value)
            Update()
        end
    end)
    local function Move(delta)
        scroll:SetVerticalScroll(math.max(0, math.min(scroll:GetVerticalScrollRange(), scroll:GetVerticalScroll() + delta)))
        Update()
    end
    scroll:EnableMouseWheel(true)
    scroll:SetScript("OnMouseWheel", function(_, delta) Move(-delta * step) end)
    scroll:HookScript("OnVerticalScroll", Update)
    scroll:HookScript("OnScrollRangeChanged", Update)
    scroll:HookScript("OnSizeChanged", Update)
    scroll:HookScript("OnShow", Update)
    scroll:HookScript("OnHide", function() bar:Hide() end)
    bar.Update = Update
    return bar, Update
end
