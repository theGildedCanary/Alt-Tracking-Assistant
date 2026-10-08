local _, ATA = ...

local function UpdateButtonPosition(button)
    local angle = math.rad(ATA.db.settings.minimapAngle or 220)
    local radius = (Minimap:GetWidth() / 2) + 4
    button:ClearAllPoints()
    button:SetPoint("CENTER", Minimap, "CENTER", math.cos(angle) * radius, math.sin(angle) * radius)
end

local function CreateMinimapButton()
    local button = CreateFrame("Button", "AltTrackingAssistantMinimapButton", Minimap)
    button:SetSize(34, 34)
    button:SetFrameStrata("MEDIUM")
    button:SetFrameLevel(8)
    button:EnableMouse(true)
    button:SetMovable(true)
    button:RegisterForClicks("LeftButtonUp")
    button:RegisterForDrag("LeftButton")

    local icon = button:CreateTexture(nil, "BACKGROUND")
    icon:SetTexture("Interface\\AddOns\\AltTrackingAssistant\\Media\\ATAIcon.png")
    icon:SetSize(34, 34)
    icon:SetPoint("CENTER")

    local iconMask = button:CreateMaskTexture(nil, "BACKGROUND")
    iconMask:SetTexture("Interface\\CharacterFrame\\TempPortraitAlphaMask")
    iconMask:SetAllPoints(icon)
    icon:AddMaskTexture(iconMask)

    local highlight = button:CreateTexture(nil, "HIGHLIGHT")
    highlight:SetTexture("Interface\\Minimap\\UI-Minimap-ZoomButton-Highlight")
    highlight:SetBlendMode("ADD")
    highlight:SetSize(36, 36)
    highlight:SetPoint("CENTER")

    button:SetScript("OnEnter", function(self)
        GameTooltip:SetOwner(self, "ANCHOR_LEFT")
        GameTooltip:AddLine("Alt Tracking Assistant")
        GameTooltip:AddLine("Left-click to open the report", 1, 1, 1)
        GameTooltip:AddLine("Drag to move this button", 1, 1, 1)
        GameTooltip:Show()
    end)
    button:SetScript("OnLeave", function()
        GameTooltip:Hide()
    end)
    button:SetScript("OnClick", function(self)
        if self.wasDragged then
            self.wasDragged = false
            return
        end
        ATA:ToggleReport()
    end)
    button:SetScript("OnDragStart", function(self)
        self.wasDragged = true
    end)
    button:SetScript("OnUpdate", function(self)
        if not self.wasDragged then
            return
        end
        local cursorX, cursorY = GetCursorPosition()
        local centerX, centerY = Minimap:GetCenter()
        local scale = UIParent:GetEffectiveScale()
        cursorX, cursorY = cursorX / scale, cursorY / scale
        local angle = math.atan2(cursorY - centerY, cursorX - centerX)
        ATA.db.settings.minimapAngle = math.deg(angle)
        UpdateButtonPosition(self)
    end)
    button:SetScript("OnDragStop", function(self)
        C_Timer.After(0.1, function()
            self.wasDragged = false
        end)
    end)

    UpdateButtonPosition(button)
    return button
end

local initFrame = CreateFrame("Frame")
initFrame:RegisterEvent("PLAYER_LOGIN")
initFrame:SetScript("OnEvent", function()
    ATA.minimapButton = CreateMinimapButton()
end)
