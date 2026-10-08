local _, ATA = ...

local expansionOrder = {
    "midnight",
    "theWarWithin",
    "dragonflight",
    "shadowlands",
}

local characterMainModes = {
    { id = "single", label = "Single" },
    { id = "faction", label = "Faction" },
    { id = "class", label = "Class" },
    { id = "classFaction", label = "Class Faction" },
}
local armorMainModes = {
    { id = "armor", label = "Single" },
    { id = "armorFaction", label = "Faction" },
}
local factions = {
    { id = "Alliance", label = "Alliance" },
    { id = "Horde", label = "Horde" },
}
local rosterClassOrder = {
    "PALADIN",
    "WARRIOR",
    "DEATHKNIGHT",
    "HUNTER",
    "SHAMAN",
    "EVOKER",
    "DRUID",
    "ROGUE",
    "MONK",
    "DEMONHUNTER",
    "MAGE",
    "PRIEST",
    "WARLOCK",
}
local armorTypes = {
    { id = "plate", label = "Plate", firstClass = 1, lastClass = 3 },
    { id = "mail", label = "Mail", firstClass = 4, lastClass = 6 },
    { id = "leather", label = "Leather", firstClass = 7, lastClass = 10 },
    { id = "cloth", label = "Cloth", firstClass = 11, lastClass = 13 },
}
local armorClassFiles = {
    plate = { PALADIN = true, WARRIOR = true, DEATHKNIGHT = true },
    mail = { HUNTER = true, SHAMAN = true, EVOKER = true },
    leather = { DRUID = true, ROGUE = true, MONK = true, DEMONHUNTER = true },
    cloth = { MAGE = true, PRIEST = true, WARLOCK = true },
}
local openCharacterMainMenu

local function GetCharacterMainSettings()
    local settings = ATA.db and ATA.db.settings
    if not settings then
        return nil
    end

    local characterMains = settings.characterMains
    if not characterMains then
        characterMains = {
            characterMode = "single",
            armorMode = "armor",
            selections = {},
        }
        settings.characterMains = characterMains
    end

    characterMains.selections = characterMains.selections or {}
    for _, armorType in ipairs(armorTypes) do
        local key = settings.armorMains and settings.armorMains[armorType.id]
        if key and not characterMains.selections["armor:" .. armorType.id] then
            characterMains.selections["armor:" .. armorType.id] = key
        end
    end

    if not characterMains.characterMode then
        local legacyMode = characterMains.mode
        if legacyMode == "faction" or legacyMode == "class" or legacyMode == "classFaction" then
            characterMains.characterMode = legacyMode
        else
            characterMains.characterMode = "single"
        end
    end
    if not characterMains.armorMode then
        characterMains.armorMode = characterMains.mode == "armorFaction" and "armorFaction" or "armor"
    end
    characterMains.mode = nil

    local function NormalizeMode(field, modes)
        for _, mode in ipairs(modes) do
            if characterMains[field] == mode.id then
                return
            end
        end
        characterMains[field] = modes[1].id
    end
    NormalizeMode("characterMode", characterMainModes)
    NormalizeMode("armorMode", armorMainModes)
    return characterMains
end

local function GetAvailableClasses()
    local classNames = {}
    if GetNumClasses and GetClassInfo then
        for classID = 1, GetNumClasses() do
            local className, classFile = GetClassInfo(classID)
            if className and classFile then
                classNames[classFile] = className
            end
        end
    end

    local result = {}
    local seen = {}
    for _, classFile in ipairs(rosterClassOrder) do
        if classNames[classFile] then
            result[#result + 1] = { id = classFile, name = classNames[classFile] }
            seen[classFile] = true
        end
    end
    for classFile, className in pairs(classNames) do
        if not seen[classFile] then
            result[#result + 1] = { id = classFile, name = className }
        end
    end

    if #result == 0 then
        for _, classFile in ipairs(rosterClassOrder) do
            result[#result + 1] = {
                id = classFile,
                name = LOCALIZED_CLASS_NAMES_MALE and LOCALIZED_CLASS_NAMES_MALE[classFile] or classFile,
            }
        end
    end
    return result
end

local function BuildCharacterMainSlots(modeID, modeGroup)
    local slots = {}
    if modeGroup == "armor" then
        for _, armorType in ipairs(armorTypes) do
            if modeID == "armorFaction" then
                for _, faction in ipairs(factions) do
                    slots[#slots + 1] = {
                        id = "armorFaction:" .. armorType.id .. ":" .. faction.id,
                        label = faction.label,
                        classFiles = armorClassFiles[armorType.id],
                        factionID = faction.id,
                    }
                end
            else
                slots[#slots + 1] = {
                    id = "armor:" .. armorType.id,
                    label = armorType.label,
                    classFiles = armorClassFiles[armorType.id],
                }
            end
        end
    elseif modeID == "single" then
        slots[1] = { id = "single", label = "Main" }
    elseif modeID == "faction" then
        for _, faction in ipairs(factions) do
            slots[#slots + 1] = {
                id = "faction:" .. faction.id,
                label = faction.label,
                factionID = faction.id,
            }
        end
    else
        for _, classInfo in ipairs(GetAvailableClasses()) do
            if modeID == "class" then
                slots[#slots + 1] = {
                    id = "class:" .. classInfo.id,
                    label = classInfo.name,
                    classFile = classInfo.id,
                }
            elseif modeID == "classFaction" then
                for _, faction in ipairs(factions) do
                    slots[#slots + 1] = {
                        id = "classFaction:" .. classInfo.id .. ":" .. faction.id,
                        label = classInfo.name .. " - " .. faction.id:sub(1, 1),
                        classFile = classInfo.id,
                        factionID = faction.id,
                    }
                end
            end
        end
    end
    return slots
end

local function GetCachedCharacters(slot)
    local characters = {}
    local seen = {}
    for key, record in pairs((ATA.db and ATA.db.characters) or {}) do
        characters[#characters + 1] = {
            key = key,
            label = (record.name or "Unknown") .. " - " .. (record.realm or "Unknown Realm"),
            classFile = record.classFile,
            faction = record.faction,
        }
        seen[key] = true
    end

    local currentKey = UnitGUID("player")
    if currentKey and not seen[currentKey] then
        local _, classFile = UnitClass("player")
        characters[#characters + 1] = {
            key = currentKey,
            label = (UnitName("player") or "Unknown") .. " - " .. (GetRealmName() or "Unknown Realm"),
            classFile = classFile,
            faction = UnitFactionGroup("player"),
        }
    end

    local allowedClassFiles = slot and slot.classFiles
    if slot and slot.classFile then
        allowedClassFiles = { [slot.classFile] = true }
    end
    for index = #characters, 1, -1 do
        local character = characters[index]
        local matchesClass = not allowedClassFiles or allowedClassFiles[character.classFile]
        local matchesFaction = not slot or not slot.factionID or character.faction == slot.factionID
        if not matchesClass or not matchesFaction then
            table.remove(characters, index)
        end
    end

    table.sort(characters, function(left, right)
        return left.label:lower() < right.label:lower()
    end)
    return characters
end

function ATA:GetCharacterMainMode(modeGroup)
    local settings = GetCharacterMainSettings()
    local field = modeGroup == "armor" and "armorMode" or "characterMode"
    local fallback = modeGroup == "armor" and "armor" or "single"
    return settings and settings[field] or fallback
end

function ATA:GetCharacterMainSlots(modeGroup, modeID)
    return BuildCharacterMainSlots(modeID or self:GetCharacterMainMode(modeGroup), modeGroup)
end

function ATA:IsCharacterMain(characterKey)
    if not characterKey then
        return false
    end
    local settings = GetCharacterMainSettings()
    if not settings then
        return false
    end
    for _, modeGroup in ipairs({ "character", "armor" }) do
        local field = modeGroup == "armor" and "armorMode" or "characterMode"
        for _, slot in ipairs(BuildCharacterMainSlots(settings[field], modeGroup)) do
            if settings.selections[slot.id] == characterKey then
                return true
            end
        end
    end
    return false
end

function ATA:IsArmorMain(characterKey)
    if not characterKey then
        return false
    end
    local settings = GetCharacterMainSettings()
    if not settings then
        return false
    end
    for _, slot in ipairs(BuildCharacterMainSlots(settings.armorMode, "armor")) do
        if settings.selections[slot.id] == characterKey then
            return true
        end
    end
    return false
end

function ATA:SetCharacterMainMode(modeGroup, modeID)
    local settings = GetCharacterMainSettings()
    if not settings then
        error("Alt Tracking Assistant settings are not initialized.")
    end
    local modes = modeGroup == "armor" and armorMainModes or characterMainModes
    local validMode = false
    for _, mode in ipairs(modes) do
        if mode.id == modeID then
            validMode = true
            break
        end
    end
    if not validMode then
        error("Invalid character main mode: " .. tostring(modeID))
    end
    local field = modeGroup == "armor" and "armorMode" or "characterMode"
    settings[field] = modeID
    if self.UpdateReport then
        self:UpdateReport()
    end
end

function ATA:SetCharacterMain(slotID, characterKey)
    local settings = GetCharacterMainSettings()
    if not settings then
        error("Alt Tracking Assistant settings are not initialized.")
    end
    settings.selections[slotID] = characterKey
    if self.UpdateReport then
        self:UpdateReport()
    end
end

function ATA:GetManualOverride(characterKey, expansionKey, checkID)
    local record = characterKey and self.db and self.db.characters[characterKey]
    local override = record
        and record.manualOverrides
        and record.manualOverrides[expansionKey]
        and record.manualOverrides[expansionKey][checkID]
    return override and override.active == true or false, override and override.value == true or false
end

function ATA:SetManualOverride(characterKey, expansionKey, checkID, active, value)
    if type(characterKey) ~= "string" or not self.db then
        error("A valid character and initialized settings are required for manual overrides.")
    end
    if type(active) ~= "boolean" or type(value) ~= "boolean" then
        error("Manual override active state and value must be booleans.")
    end

    local expansion = self.trackerDefinitions[expansionKey]
    local validCheck = false
    if expansion then
        for _, check in ipairs(expansion.checks) do
            if check.id == checkID and check.type ~= "count" and check.type ~= "select" then
                validCheck = true
                break
            end
        end
    end
    if not validCheck then
        error("Invalid boolean tracker for manual override: " .. tostring(expansionKey) .. "/" .. tostring(checkID))
    end

    local record = self.db.characters[characterKey]
    if not record and characterKey == UnitGUID("player") then
        local success, result = self:ScanCurrentCharacter()
        if not success then
            error("Unable to initialize current character before setting a manual override: " .. result)
        end
        record = result
    end
    if not record then
        error("Cannot set a manual override for an uncached character.")
    end

    record.manualOverrides = record.manualOverrides or {}
    record.manualOverrides[expansionKey] = record.manualOverrides[expansionKey] or {}
    record.manualOverrides[expansionKey][checkID] = {
        active = active,
        value = value,
    }
    if self.UpdateReport then
        self:UpdateReport()
    end
end

local function CreateBackdrop(parent, expansionKey)
    local frame = CreateFrame("Frame", nil, parent, "BackdropTemplate")
    frame:SetBackdrop({
        bgFile = "Interface\\Buttons\\WHITE8X8",
        edgeFile = "Interface\\Buttons\\WHITE8X8",
        edgeSize = 1,
        insets = { left = 1, right = 1, top = 1, bottom = 1 },
    })
    frame:SetBackdropColor(unpack(ATA.UI.theme.colors.panel))
    frame:SetBackdropBorderColor(
        unpack(expansionKey and ATA.UI.theme.colors.expansions[expansionKey] or ATA.UI.theme.colors.gold)
    )
    return frame
end

local function CreateCharacterDropdown(parent, slot, options)
    options = options or {}
    local row = CreateFrame("Frame", nil, parent)
    row:SetHeight(options.height or (options.labelAbove and 58 or 30))

    local label
    if not options.hideLabel then
        label = row:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
        label:SetText(slot.label)
        label:SetWordWrap(false)
        if options.labelAbove then
            label:SetPoint("TOP", row, "TOP", 0, -2)
            label:SetPoint("LEFT", row, "LEFT", 2, 0)
            label:SetPoint("RIGHT", row, "RIGHT", -2, 0)
            label:SetJustifyH("CENTER")
        else
            label:SetPoint("LEFT", row, "LEFT", 4, 0)
            label:SetWidth(options.labelWidth or 96)
        end
    end

    local button = CreateFrame("Button", nil, row, "BackdropTemplate")
    button:SetHeight(26)
    if options.labelAbove then
        button:SetPoint("BOTTOMLEFT", row, "BOTTOMLEFT", 2, 0)
        button:SetPoint("BOTTOMRIGHT", row, "BOTTOMRIGHT", -2, 0)
    elseif options.hideLabel then
        button:SetPoint("LEFT", row, "LEFT", 2, 0)
        button:SetPoint("RIGHT", row, "RIGHT", -2, 0)
    else
        button:SetPoint("LEFT", row, "LEFT", (options.labelWidth or 96) + 8, 0)
        button:SetPoint("RIGHT", row, "RIGHT", -2, 0)
    end
    button:SetBackdrop({
        bgFile = "Interface\\Buttons\\WHITE8X8",
        edgeFile = "Interface\\Buttons\\WHITE8X8",
        edgeSize = 1,
        insets = { left = 1, right = 1, top = 1, bottom = 1 },
    })
    button:SetBackdropColor(unpack(ATA.UI.theme.colors.panel))
    button:SetBackdropBorderColor(unpack(ATA.UI.theme.colors.gold))

    local selectedText = button:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
    selectedText:SetPoint("LEFT", button, "LEFT", 7, 0)
    selectedText:SetPoint("RIGHT", button, "RIGHT", -18, 0)
    selectedText:SetJustifyH("LEFT")
    selectedText:SetWordWrap(false)
    selectedText:SetNonSpaceWrap(false)

    local arrow = button:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
    arrow:SetPoint("RIGHT", button, "RIGHT", -6, 0)
    arrow:SetText("v")
    arrow:SetTextColor(unpack(ATA.UI.theme.colors.gold))

    local menu = CreateBackdrop(parent)
    menu:SetFrameStrata("DIALOG")
    menu:SetFrameLevel(parent:GetFrameLevel() + 50)
    menu:SetSize(210, 116)
    menu:SetPoint("TOPLEFT", button, "BOTTOMLEFT", 0, -2)
    menu:SetScript("OnHide", function()
        if openCharacterMainMenu == menu then
            openCharacterMainMenu = nil
        end
    end)
    menu:Hide()

    local scroll = CreateFrame("ScrollFrame", nil, menu)
    scroll:SetPoint("TOPLEFT", menu, "TOPLEFT", 3, -3)
    scroll:SetPoint("BOTTOMRIGHT", menu, "BOTTOMRIGHT", -3, 3)
    scroll:EnableMouseWheel(true)

    local choices = CreateFrame("Frame", nil, scroll)
    choices:SetSize(204, 1)
    scroll:SetScrollChild(choices)
    scroll:SetScript("OnMouseWheel", function(self, delta)
        local maximum = self:GetVerticalScrollRange()
        self:SetVerticalScroll(math.max(0, math.min(maximum, self:GetVerticalScroll() - delta * 28)))
    end)

    local optionRows = {}
    local function Refresh()
        local settings = GetCharacterMainSettings()
        local selectedKey = settings and settings.selections[slot.id]
        local selectedLabel = "Unassigned"
        for _, character in ipairs(GetCachedCharacters(slot)) do
            if character.key == selectedKey then
                selectedLabel = character.label
                break
            end
        end
        if selectedKey and selectedLabel == "Unassigned" then
            selectedLabel = "Unavailable character"
        end
        selectedText:SetText(selectedLabel)
    end

    button:SetScript("OnClick", function()
        if menu:IsShown() then
            menu:Hide()
            return
        end
        if openCharacterMainMenu and openCharacterMainMenu:IsShown() then
            openCharacterMainMenu:Hide()
        end
        openCharacterMainMenu = menu

        local characters = GetCachedCharacters(slot)
        table.insert(characters, 1, { key = nil, label = "Unassigned" })
        choices:SetHeight(math.max(1, #characters * 28))
        for index, character in ipairs(characters) do
            local option = optionRows[index]
            if not option then
                option = CreateFrame("Button", nil, choices)
                option:SetHeight(28)
                option.label = option:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
                option.label:SetPoint("LEFT", option, "LEFT", 6, 0)
                option.label:SetPoint("RIGHT", option, "RIGHT", -6, 0)
                option.label:SetJustifyH("LEFT")
                option.label:SetWordWrap(false)
                option:SetScript("OnEnter", function(self)
                    self.label:SetTextColor(1, 1, 1)
                end)
                option:SetScript("OnLeave", function(self)
                    self.label:SetTextColor(unpack(ATA.UI.theme.colors.text))
                end)
                optionRows[index] = option
            end
            option:ClearAllPoints()
            option:SetPoint("TOPLEFT", choices, "TOPLEFT", 0, -((index - 1) * 28))
            option:SetPoint("RIGHT", choices, "RIGHT", 0, 0)
            option.label:SetText(character.label)
            local selectedCharacterKey = character.key
            option:SetScript("OnClick", function()
                ATA:SetCharacterMain(slot.id, selectedCharacterKey)
                menu:Hide()
                Refresh()
            end)
            option:Show()
        end
        for index = #characters + 1, #optionRows do
            optionRows[index]:Hide()
        end
        scroll:SetVerticalScroll(0)
        menu:Show()
    end)

    row.Refresh = Refresh
    Refresh()
    return row
end

local function CreateModeCheckbox(parent, modeGroup, mode, x, y, width)
    local button = CreateFrame("Button", nil, parent)
    button:SetSize(width, 26)
    button:SetPoint("TOPLEFT", parent, "TOPLEFT", x, -y)

    local box = CreateBackdrop(button)
    box:SetSize(16, 16)
    box:SetPoint("LEFT", button, "LEFT", 0, 0)

    local checkmark = box:CreateTexture(nil, "ARTWORK")
    checkmark:SetSize(12, 12)
    checkmark:SetPoint("CENTER")
    checkmark:SetTexture("Interface\\Buttons\\UI-CheckBox-Check")
    checkmark:SetVertexColor(unpack(ATA.UI.theme.colors.gold))

    local label = button:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
    label:SetPoint("LEFT", box, "RIGHT", 6, 0)
    label:SetPoint("RIGHT", button, "RIGHT", -2, 0)
    label:SetJustifyH("LEFT")
    label:SetText(mode.label)

    button.Refresh = function()
        checkmark:SetShown(ATA:GetCharacterMainMode(modeGroup) == mode.id)
    end
    button:SetScript("OnClick", function()
        ATA:SetCharacterMainMode(modeGroup, mode.id)
        if parent.RefreshLayout then
            parent:RefreshLayout()
        end
    end)
    button:Refresh()
    return button
end

local function CreateTrackerCheckbox(parent, expansionKey, check)
    local button = CreateFrame("Button", nil, parent)
    button:SetHeight(26)

    local box = CreateBackdrop(button)
    box:SetSize(18, 18)
    box:SetPoint("LEFT", button, "LEFT", 5, 0)

    local checkmark = box:CreateTexture(nil, "ARTWORK")
    checkmark:SetSize(14, 14)
    checkmark:SetPoint("CENTER")
    checkmark:SetTexture("Interface\\Buttons\\UI-CheckBox-Check")
    checkmark:SetVertexColor(unpack(ATA.UI.theme.colors.gold))

    local label = button:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
    label:SetPoint("LEFT", box, "RIGHT", 8, 0)
    label:SetPoint("RIGHT", button, "RIGHT", -8, 0)
    label:SetJustifyH("LEFT")
    label:SetText(check.settingsLabel or check.label)

    button:SetScript("OnEnter", function()
        label:SetTextColor(1, 1, 1)
    end)
    button:SetScript("OnLeave", function()
        label:SetTextColor(unpack(ATA.UI.theme.colors.text))
    end)
    button:SetScript("OnClick", function()
        ATA:SetTrackerEnabled(expansionKey, check.id, not ATA:IsTrackerEnabled(expansionKey, check.id))
        button:Refresh()
    end)

    button.Refresh = function()
        checkmark:SetShown(ATA:IsTrackerEnabled(expansionKey, check.id))
    end
    button:Refresh()
    return button
end

local function CreateScrollPage(parent)
    local scroll = CreateFrame("ScrollFrame", nil, parent, "UIPanelScrollFrameTemplate")
    scroll:SetPoint("TOPLEFT", parent, "TOPLEFT", 12, -12)
    scroll:SetPoint("BOTTOMRIGHT", parent, "BOTTOMRIGHT", -30, 12)
    local content = CreateFrame("Frame", nil, scroll)
    content:SetPoint("TOPLEFT", scroll, "TOPLEFT")
    content:SetWidth(1)
    scroll:SetScrollChild(content)
    scroll:HookScript("OnSizeChanged", function(self, width)
        content:SetWidth(math.max(1, width - 24))
    end)
    return scroll, content
end

local function CreateClassMainsPage(parent)
    local page = CreateFrame("Frame", nil, parent)
    page:SetAllPoints()
    local scroll, content = CreateScrollPage(page)
    scroll:ClearAllPoints()
    scroll:SetPoint("TOPLEFT", page, "TOPLEFT", 12, -48)
    scroll:SetPoint("BOTTOMRIGHT", page, "BOTTOMRIGHT", -30, 12)
    local controls = {}
    local currentSignature

    local function RefreshLayout()
        for _, control in ipairs(controls) do
            control:Hide()
        end
        controls = {}
        for _, header in pairs(page.tableHeaders) do
            header:Hide()
        end

        local mode = ATA:GetCharacterMainMode("character")
        local slots = BuildCharacterMainSlots(mode, "character")
        local width = math.max(1, content:GetWidth())
        local height = 48
        local function AddControl(control)
            controls[#controls + 1] = control
            control:Show()
        end

        local modeButtons = page.modeButtons
        local buttonWidth = math.max(100, (page:GetWidth() - 36) / #characterMainModes)
        for index in ipairs(characterMainModes) do
            local button = modeButtons[index]
            button:ClearAllPoints()
            button:SetPoint("TOPLEFT", page, "TOPLEFT", 18 + ((index - 1) * buttonWidth), -14)
            button:SetWidth(buttonWidth - 4)
            button:Refresh()
        end

        if mode == "single" then
            local selector = page.selectors.single
            if not selector then
                selector = CreateCharacterDropdown(content, slots[1], { labelAbove = true })
                page.selectors.single = selector
            end
            selector:ClearAllPoints()
            selector:SetWidth(math.min(320, width * 0.55))
            selector:SetPoint("TOP", content, "TOP", 0, -12)
            selector:Refresh()
            AddControl(selector)
            height = 84
        elseif mode == "faction" then
            local colWidth = width / 2
            for index, slot in ipairs(slots) do
                local selector = page.selectors[slot.id]
                if not selector then
                    selector = CreateCharacterDropdown(content, slot, { labelAbove = true })
                    page.selectors[slot.id] = selector
                end
                selector:ClearAllPoints()
                selector:SetWidth(colWidth - 12)
                selector:SetPoint("TOPLEFT", content, "TOPLEFT", 4 + ((index - 1) * colWidth), -12)
                selector:Refresh()
                AddControl(selector)
            end
            height = 84
        elseif mode == "class" then
            local classList = GetAvailableClasses()
            local colWidth = width / 4
            local groupY = 12
            local slotByClass = {}
            for _, slot in ipairs(slots) do
                slotByClass[slot.classFile] = slot
            end
            for _, armorType in ipairs(armorTypes) do
                local groupClasses = {}
                for index = armorType.firstClass, math.min(armorType.lastClass, #classList) do
                    groupClasses[#groupClasses + 1] = classList[index]
                end
                local offset = (4 - #groupClasses) * colWidth / 2
                for index, classInfo in ipairs(groupClasses) do
                    local slot = slotByClass[classInfo.id]
                    if slot then
                        local selector = page.selectors[slot.id]
                        if not selector then
                            selector = CreateCharacterDropdown(content, slot, { labelAbove = true })
                            page.selectors[slot.id] = selector
                        end
                        selector:ClearAllPoints()
                        selector:SetWidth(colWidth - 10)
                        selector:SetPoint(
                            "TOPLEFT",
                            content,
                            "TOPLEFT",
                            offset + ((index - 1) * colWidth) + 4,
                            -groupY
                        )
                        selector:Refresh()
                        AddControl(selector)
                    end
                end
                groupY = groupY + 68
                height = groupY + 8
            end
        else
            local classList = GetAvailableClasses()
            local headers = {
                { label = "Class", width = width * 0.38 },
                { label = "Alliance", width = width * 0.29 },
                { label = "Horde", width = width * 0.29 },
            }
            local x = 8
            for _, header in ipairs(headers) do
                local text = page.tableHeaders[header.label]
                text:ClearAllPoints()
                text:SetPoint("TOPLEFT", content, "TOPLEFT", x, -10)
                text:SetWidth(header.width)
                text:Show()
                x = x + header.width
            end
            local rowY = 36
            for _, classInfo in ipairs(classList) do
                local name = page.classLabels[classInfo.id]
                if not name then
                    name = content:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
                    page.classLabels[classInfo.id] = name
                end
                name:ClearAllPoints()
                name:SetPoint("TOPLEFT", content, "TOPLEFT", 8, -rowY)
                name:SetWidth(headers[1].width - 8)
                name:SetText(classInfo.name)
                name:Show()

                for factionIndex, faction in ipairs(factions) do
                    local slotID = "classFaction:" .. classInfo.id .. ":" .. faction.id
                    local slot = {
                        id = slotID,
                        label = classInfo.name .. " - " .. faction.id:sub(1, 1),
                        classFile = classInfo.id,
                        factionID = faction.id,
                    }
                    local selector = page.selectors[slotID]
                    if not selector then
                        selector = CreateCharacterDropdown(content, slot, { hideLabel = true, height = 30 })
                        page.selectors[slotID] = selector
                    end
                    selector:ClearAllPoints()
                    selector:SetPoint(
                        "TOPLEFT",
                        content,
                        "TOPLEFT",
                        headers[1].width + 8 + ((factionIndex - 1) * headers[2].width),
                        -(rowY - 1)
                    )
                    selector:SetWidth(headers[2].width - 8)
                    selector:Refresh()
                    AddControl(selector)
                end
                rowY = rowY + 34
            end
            height = rowY + 8
        end

        currentSignature = mode .. ":" .. width
        content:SetHeight(height)
    end

    page.modeButtons = {}
    for _, mode in ipairs(characterMainModes) do
        page.modeButtons[#page.modeButtons + 1] = CreateModeCheckbox(page, "character", mode, 18, 14, 132)
    end
    page.selectors = {}
    page.tableHeaders = {}
    page.classLabels = {}
    for _, label in ipairs({ "Class", "Alliance", "Horde" }) do
        local header = content:CreateFontString(nil, "OVERLAY", "GameFontNormal")
        header:SetText(label)
        page.tableHeaders[label] = header
    end
    page.RefreshControls = function()
        local mode = ATA:GetCharacterMainMode("character")
        local signature = mode .. ":" .. content:GetWidth()
        if signature ~= currentSignature then
            RefreshLayout()
        else
            for _, control in ipairs(controls) do
                if control.Refresh then
                    control:Refresh()
                end
            end
        end
        for _, button in ipairs(page.modeButtons) do
            button:Refresh()
        end
    end
    page.RefreshLayout = page.RefreshControls
    content:SetScript("OnSizeChanged", function()
        page.RefreshControls()
    end)
    page:SetScript("OnSizeChanged", function()
        page.RefreshControls()
    end)
    RefreshLayout()
    return page
end

local function CreateArmorMainsPage(parent)
    local page = CreateFrame("Frame", nil, parent)
    page:SetAllPoints()
    local scroll, content = CreateScrollPage(page)
    scroll:ClearAllPoints()
    scroll:SetPoint("TOPLEFT", page, "TOPLEFT", 12, -38)
    scroll:SetPoint("BOTTOMRIGHT", page, "BOTTOMRIGHT", -30, 12)
    page.headings = {}
    page.selectors = {}
    local controls = {}
    local signature
    local slots = BuildCharacterMainSlots(ATA:GetCharacterMainMode("armor"), "armor")

    local function RefreshLayout()
        for _, control in ipairs(controls) do
            control:Hide()
        end
        controls = {}
        local mode = ATA:GetCharacterMainMode("armor")
        slots = BuildCharacterMainSlots(mode, "armor")
        local width = content:GetWidth()
        local columnWidth = width / 4
        for index, armorType in ipairs(armorTypes) do
            local x = (index - 1) * columnWidth
            local heading = page.headings[armorType.id]
            heading:ClearAllPoints()
            heading:SetPoint("TOP", content, "TOPLEFT", x + (columnWidth / 2), -22)
            heading:SetWidth(columnWidth - 8)
            heading:Show()

            if mode == "armor" then
                local slot = slots[index]
                local selector = page.selectors[slot.id]
                if not selector then
                    selector = CreateCharacterDropdown(content, slot, { hideLabel = true, height = 30 })
                    page.selectors[slot.id] = selector
                end
                selector:ClearAllPoints()
                selector:SetPoint("TOPLEFT", content, "TOPLEFT", x + 4, -52)
                selector:SetWidth(columnWidth - 8)
                selector:Refresh()
                selector:Show()
                controls[#controls + 1] = selector
            else
                for factionIndex, faction in ipairs(factions) do
                    local slot = slots[((index - 1) * 2) + factionIndex]
                    local selector = page.selectors[slot.id]
                    if not selector then
                        selector = CreateCharacterDropdown(content, slot, { labelAbove = true, height = 54 })
                        page.selectors[slot.id] = selector
                    end
                    selector:ClearAllPoints()
                    selector:SetPoint("TOPLEFT", content, "TOPLEFT", x + 3, -(50 + ((factionIndex - 1) * 62)))
                    selector:SetWidth(columnWidth - 6)
                    selector:Refresh()
                    selector:Show()
                    controls[#controls + 1] = selector
                end
            end
        end
        signature = mode .. ":" .. width
        content:SetHeight(mode == "armor" and 100 or 180)
    end

    local modeButtons = {}
    local function RefreshModes()
        for index, mode in ipairs(armorMainModes) do
            local button = modeButtons[index]
            button:Refresh()
        end
        local mode = ATA:GetCharacterMainMode("armor")
        if signature ~= mode .. ":" .. content:GetWidth() then
            RefreshLayout()
        else
            for _, control in ipairs(controls) do
                if control.Refresh then
                    control:Refresh()
                end
            end
        end
    end
    page.RefreshLayout = RefreshModes

    for index, mode in ipairs(armorMainModes) do
        modeButtons[index] = CreateModeCheckbox(page, "armor", mode, 1, 1, 120)
    end
    for _, armorType in ipairs(armorTypes) do
        local heading = content:CreateFontString(nil, "OVERLAY", "GameFontNormal")
        heading:SetText(armorType.label)
        heading:SetTextColor(unpack(ATA.UI.theme.colors.gold))
        page.headings[armorType.id] = heading
    end
    local function LayoutModeButtons()
        local buttonWidth = 120
        local startX = math.max(0, (page:GetWidth() - (#modeButtons * buttonWidth)) / 2)
        for index, button in ipairs(modeButtons) do
            button:ClearAllPoints()
            button:SetPoint("TOPLEFT", page, "TOPLEFT", startX + ((index - 1) * buttonWidth), -4)
        end
    end
    page.RefreshControls = RefreshModes
    content:SetScript("OnSizeChanged", RefreshModes)
    page:SetScript("OnSizeChanged", LayoutModeButtons)
    LayoutModeButtons()
    RefreshLayout()
    return page
end

local function CreateMainsPage(parent)
    local page = CreateFrame("Frame")
    page.name = "Mains"

    local tabs = CreateFrame("Frame", nil, page)
    tabs:SetPoint("TOPLEFT", page, "TOPLEFT", 16, -12)
    tabs:SetPoint("TOPRIGHT", page, "TOPRIGHT", -16, 0)
    tabs:SetHeight(34)

    local classPage = CreateClassMainsPage(page)
    classPage:SetPoint("TOPLEFT", tabs, "BOTTOMLEFT", 0, -4)
    classPage:SetPoint("BOTTOMRIGHT", page, "BOTTOMRIGHT")

    local armorPage = CreateArmorMainsPage(page)
    armorPage:SetPoint("TOPLEFT", tabs, "BOTTOMLEFT", 0, -4)
    armorPage:SetPoint("BOTTOMRIGHT", page, "BOTTOMRIGHT")
    armorPage:Hide()

    local function SetActiveTab(tabID)
        local isClass = tabID == "class"
        classPage:SetShown(isClass)
        armorPage:SetShown(not isClass)
        classPage:RefreshControls()
        armorPage:RefreshControls()
        for _, tab in ipairs(tabs.buttons) do
            tab:SetEnabled(tab.id ~= tabID)
        end
    end
    tabs.buttons = {}
    for index, tabInfo in ipairs({
        { id = "class", label = "Class Mains" },
        { id = "armor", label = "Armor Mains" },
    }) do
        local button = CreateFrame("Button", nil, tabs, "UIPanelButtonTemplate")
        button:SetSize(140, 26)
        button:SetPoint("LEFT", tabs, "LEFT", (index - 1) * 146, 0)
        button:SetText(tabInfo.label)
        button.id = tabInfo.id
        button:SetScript("OnClick", function()
            SetActiveTab(tabInfo.id)
        end)
        tabs.buttons[index] = button
    end
    SetActiveTab("class")

    page.RefreshControls = function()
        classPage:RefreshControls()
        armorPage:RefreshControls()
    end
    return page
end

local function CreateExpansionsPage(parent)
    local page = CreateFrame("Frame")
    page.name = "Expansions"
    local tabs = CreateFrame("Frame", nil, page)
    tabs:SetPoint("TOPLEFT", page, "TOPLEFT", 12, -8)
    tabs:SetPoint("TOPRIGHT", page, "TOPRIGHT", -12, 0)
    tabs:SetHeight(30)

    local visibilityScroll, visibilityContent = CreateScrollPage(page)
    visibilityScroll:ClearAllPoints()
    visibilityScroll:SetPoint("TOPLEFT", page, "TOPLEFT", 12, -44)
    visibilityScroll:SetPoint("BOTTOMRIGHT", page, "BOTTOMRIGHT", -30, 12)

    local overrideScroll, overrideContent = CreateScrollPage(page)
    overrideScroll:ClearAllPoints()
    overrideScroll:SetPoint("TOPLEFT", page, "TOPLEFT", 12, -44)
    overrideScroll:SetPoint("BOTTOMRIGHT", page, "BOTTOMRIGHT", -30, 12)
    overrideScroll:Hide()

    local visibilityControls = {}
    local visibilityLayoutWidth
    local visibilityYOffset = 0
    local function LayoutVisibility()
        local width = math.max(1, visibilityContent:GetWidth())
        visibilityYOffset = 0
        for _, expansionKey in ipairs(expansionOrder) do
            local expansion = ATA.trackerDefinitions[expansionKey]
            if expansion then
                local section = page.sections[expansionKey]
                local rows = math.ceil(#expansion.checks / 3)
                section:SetSize(width - 8, 42 + (rows * 30))
                section:ClearAllPoints()
                section:SetPoint("TOPLEFT", visibilityContent, "TOPLEFT", 0, -visibilityYOffset)
                local colWidth = (width - 24) / 3
                for index in ipairs(expansion.checks) do
                    local control = section.controls[index]
                    local column = (index - 1) % 3
                    local row = math.floor((index - 1) / 3)
                    control:ClearAllPoints()
                    control:SetPoint(
                        "TOPLEFT",
                        section,
                        "TOPLEFT",
                        8 + (column * colWidth),
                        -(36 + (row * 30))
                    )
                    control:SetWidth(colWidth - 6)
                end
                visibilityYOffset = visibilityYOffset + section:GetHeight() + 10
            end
        end
        visibilityContent:SetHeight(visibilityYOffset)
    end

    page.sections = {}
    for _, expansionKey in ipairs(expansionOrder) do
        local expansion = ATA.trackerDefinitions[expansionKey]
        if expansion then
            local section = CreateBackdrop(visibilityContent, expansionKey)
            local heading = section:CreateFontString(nil, "OVERLAY", "GameFontNormal")
            heading:SetPoint("TOPLEFT", section, "TOPLEFT", 12, -10)
            heading:SetText(expansion.name)
            heading:SetTextColor(unpack(ATA.UI.theme.colors.progress[expansionKey]))

            section.controls = {}
            for _, check in ipairs(expansion.checks) do
                local control = CreateTrackerCheckbox(section, expansionKey, check)
                section.controls[#section.controls + 1] = control
                visibilityControls[#visibilityControls + 1] = control
            end
            page.sections[expansionKey] = section
        end
    end
    visibilityContent:SetScript("OnSizeChanged", function(_, newWidth)
        if newWidth ~= visibilityLayoutWidth then
            visibilityLayoutWidth = newWidth
            LayoutVisibility()
        end
    end)

    local manualRows = {}
    local manualSections = {}
    local selectedCharacterKey
    local description = overrideContent:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
    description:SetPoint("TOPLEFT", overrideContent, "TOPLEFT", 8, -6)
    description:SetText("Activate an override to replace the scan with True or False. Counts and selections are not overridable.")

    local characterLabel = overrideContent:CreateFontString(nil, "OVERLAY", "GameFontNormal")
    characterLabel:SetPoint("TOPLEFT", overrideContent, "TOPLEFT", 8, -32)
    characterLabel:SetText("Character")

    local characterButton = CreateFrame("Button", nil, overrideContent, "UIPanelButtonTemplate")
    characterButton:SetPoint("TOPLEFT", characterLabel, "TOPRIGHT", 10, 4)
    characterButton:SetSize(240, 26)
    local characterMenu = CreateBackdrop(page)
    characterMenu:SetFrameStrata("DIALOG")
    characterMenu:SetFrameLevel(page:GetFrameLevel() + 50)
    characterMenu:SetSize(240, 160)
    characterMenu:SetPoint("TOPLEFT", characterButton, "BOTTOMLEFT", 0, -2)
    characterMenu:Hide()

    local characterMenuScroll = CreateFrame("ScrollFrame", nil, characterMenu)
    characterMenuScroll:SetPoint("TOPLEFT", characterMenu, "TOPLEFT", 3, -3)
    characterMenuScroll:SetPoint("BOTTOMRIGHT", characterMenu, "BOTTOMRIGHT", -3, 3)
    characterMenuScroll:EnableMouseWheel(true)
    local characterChoices = CreateFrame("Frame", nil, characterMenuScroll)
    characterChoices:SetSize(234, 1)
    characterMenuScroll:SetScrollChild(characterChoices)
    characterMenuScroll:SetScript("OnMouseWheel", function(self, delta)
        local maximum = self:GetVerticalScrollRange()
        self:SetVerticalScroll(math.max(0, math.min(maximum, self:GetVerticalScroll() - delta * 28)))
    end)
    local characterOptionRows = {}

    local function RefreshManualOverrides()
        local characters = GetCachedCharacters()
        local validSelection = false
        for _, character in ipairs(characters) do
            if character.key == selectedCharacterKey then
                validSelection = true
                characterButton:SetText(character.label)
                break
            end
        end
        if not validSelection then
            selectedCharacterKey = characters[1] and characters[1].key
            characterButton:SetText(characters[1] and characters[1].label or "No characters found")
        end
        characterButton:SetEnabled(#characters > 0)
        for _, row in ipairs(manualRows) do
            row:Refresh()
        end
    end

    characterButton:SetScript("OnClick", function()
        if characterMenu:IsShown() then
            characterMenu:Hide()
            return
        end
        if openCharacterMainMenu and openCharacterMainMenu:IsShown() then
            openCharacterMainMenu:Hide()
        end
        openCharacterMainMenu = characterMenu
        local characters = GetCachedCharacters()
        characterChoices:SetHeight(math.max(1, #characters * 28))
        for index, character in ipairs(characters) do
            local option = characterOptionRows[index]
            if not option then
                option = CreateFrame("Button", nil, characterChoices)
                option:SetHeight(28)
                option.label = option:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
                option.label:SetPoint("LEFT", option, "LEFT", 6, 0)
                option.label:SetPoint("RIGHT", option, "RIGHT", -6, 0)
                option.label:SetJustifyH("LEFT")
                option.label:SetWordWrap(false)
                characterOptionRows[index] = option
            end
            option:ClearAllPoints()
            option:SetPoint("TOPLEFT", characterChoices, "TOPLEFT", 0, -((index - 1) * 28))
            option:SetPoint("RIGHT", characterChoices, "RIGHT", 0, 0)
            option.label:SetText(character.label)
            local key = character.key
            option:SetScript("OnClick", function()
                selectedCharacterKey = key
                characterMenu:Hide()
                RefreshManualOverrides()
            end)
            option:Show()
        end
        for index = #characters + 1, #characterOptionRows do
            characterOptionRows[index]:Hide()
        end
        characterMenuScroll:SetVerticalScroll(0)
        characterMenu:Show()
    end)
    characterMenu:SetScript("OnHide", function()
        if openCharacterMainMenu == characterMenu then
            openCharacterMainMenu = nil
        end
    end)

    local function CreateManualOverrideRow(parentFrame, expansionKey, check)
        local row = CreateFrame("Frame", nil, parentFrame)
        row:SetHeight(30)
        local label = row:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
        label:SetPoint("LEFT", row, "LEFT", 8, 0)
        label:SetPoint("RIGHT", row, "RIGHT", -268, 0)
        label:SetJustifyH("LEFT")
        label:SetWordWrap(false)
        label:SetText(check.settingsLabel or check.label)

        local valueButton = CreateFrame("Button", nil, row, "UIPanelButtonTemplate")
        valueButton:SetPoint("RIGHT", row, "RIGHT", -4, 0)
        valueButton:SetSize(126, 24)
        local activeButton = CreateFrame("Button", nil, row, "UIPanelButtonTemplate")
        activeButton:SetPoint("RIGHT", valueButton, "LEFT", -6, 0)
        activeButton:SetSize(132, 24)

        local function GetValue()
            local active, value = ATA:GetManualOverride(selectedCharacterKey, expansionKey, check.id)
            return active, value
        end
        row.Refresh = function()
            local active, value = GetValue()
            activeButton:SetText(active and "Override: Active" or "Override: Inactive")
            valueButton:SetText(value and "Complete: True" or "Complete: False")
            activeButton:SetEnabled(selectedCharacterKey ~= nil)
            valueButton:SetEnabled(selectedCharacterKey ~= nil)
        end
        activeButton:SetScript("OnClick", function()
            local active, value = GetValue()
            ATA:SetManualOverride(selectedCharacterKey, expansionKey, check.id, not active, value)
            row:Refresh()
        end)
        valueButton:SetScript("OnClick", function()
            local active, value = GetValue()
            ATA:SetManualOverride(selectedCharacterKey, expansionKey, check.id, active, not value)
            row:Refresh()
        end)
        row:Refresh()
        return row
    end

    for _, expansionKey in ipairs(expansionOrder) do
        local expansion = ATA.trackerDefinitions[expansionKey]
        if expansion then
            local section = CreateBackdrop(overrideContent, expansionKey)
            local heading = section:CreateFontString(nil, "OVERLAY", "GameFontNormal")
            heading:SetPoint("TOPLEFT", section, "TOPLEFT", 12, -10)
            heading:SetText(expansion.name)
            heading:SetTextColor(unpack(ATA.UI.theme.colors.progress[expansionKey]))
            section.rows = {}
            for _, check in ipairs(expansion.checks) do
                if check.type ~= "count" and check.type ~= "select" then
                    local row = CreateManualOverrideRow(section, expansionKey, check)
                    section.rows[#section.rows + 1] = row
                    manualRows[#manualRows + 1] = row
                end
            end
            manualSections[expansionKey] = section
        end
    end

    local manualLayoutWidth
    local function LayoutManualOverrides()
        local width = overrideContent:GetWidth()
        if width <= 32 then
            return
        end
        local yOffset = 58
        for _, expansionKey in ipairs(expansionOrder) do
            local section = manualSections[expansionKey]
            if section then
                section:SetSize(width - 8, 38 + (#section.rows * 34))
                section:ClearAllPoints()
                section:SetPoint("TOPLEFT", overrideContent, "TOPLEFT", 0, -yOffset)
                for index, row in ipairs(section.rows) do
                    row:ClearAllPoints()
                    row:SetPoint("TOPLEFT", section, "TOPLEFT", 4, -(32 + ((index - 1) * 34)))
                    row:SetWidth(width - 24)
                end
                yOffset = yOffset + section:GetHeight() + 10
            end
        end
        overrideContent:SetHeight(yOffset)
        RefreshManualOverrides()
    end
    overrideScroll:HookScript("OnShow", LayoutManualOverrides)
    overrideContent:SetScript("OnSizeChanged", function(_, newWidth)
        if newWidth ~= manualLayoutWidth then
            manualLayoutWidth = newWidth
            LayoutManualOverrides()
        end
    end)

    local function SetActiveTab(tabID)
        local showVisibility = tabID == "visibility"
        visibilityScroll:SetShown(showVisibility)
        overrideScroll:SetShown(not showVisibility)
        for _, tab in ipairs(tabs.buttons) do
            tab:SetEnabled(tab.id ~= tabID)
        end
        if showVisibility then
            LayoutVisibility()
        else
            LayoutManualOverrides()
        end
    end
    tabs.buttons = {}
    for index, tabInfo in ipairs({
        { id = "visibility", label = "Tracker Visibility" },
        { id = "overrides", label = "Manual Overrides" },
    }) do
        local tabID = tabInfo.id
        local button = CreateFrame("Button", nil, tabs, "UIPanelButtonTemplate")
        button:SetSize(150, 26)
        button:SetPoint("LEFT", tabs, "LEFT", (index - 1) * 156, 0)
        button:SetText(tabInfo.label)
        button.id = tabID
        button:SetScript("OnClick", function()
            SetActiveTab(tabID)
        end)
        tabs.buttons[index] = button
    end
    SetActiveTab("visibility")
    selectedCharacterKey = UnitGUID("player")

    page.RefreshControls = function()
        LayoutVisibility()
        for _, control in ipairs(visibilityControls) do
            control:Refresh()
        end
        RefreshManualOverrides()
    end
    return page
end

local function CreateOverviewPage()
    local page = CreateFrame("Frame")
    page.name = "Alt Tracking Assistant"

    local title = page:CreateFontString(nil, "ARTWORK", "GameFontNormalLarge")
    title:SetPoint("TOPLEFT", page, "TOPLEFT", 18, -20)
    title:SetText("Alt Tracking Assistant")

    local description = page:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
    description:SetPoint("TOPLEFT", title, "BOTTOMLEFT", 0, -10)
    description:SetPoint("RIGHT", page, "RIGHT", -24, 0)
    description:SetJustifyH("LEFT")
    description:SetText("Track progression across your characters, compare cached alts, and keep your roster checklist up to date.")

    local dashboardButton = CreateFrame("Button", nil, page, "UIPanelButtonTemplate")
    dashboardButton:SetSize(180, 32)
    dashboardButton:SetPoint("TOPLEFT", description, "BOTTOMLEFT", 0, -22)
    dashboardButton:SetText("Open Dashboard")
    dashboardButton:SetScript("OnClick", function()
        ATA:ToggleReport()
    end)

    local thanks = CreateBackdrop(page)
    thanks:SetPoint("TOPLEFT", dashboardButton, "BOTTOMLEFT", 0, -28)
    thanks:SetPoint("RIGHT", page, "RIGHT", -24, 0)
    thanks:SetHeight(94)

    local thanksTitle = thanks:CreateFontString(nil, "OVERLAY", "GameFontNormal")
    thanksTitle:SetPoint("TOPLEFT", thanks, "TOPLEFT", 12, -12)
    thanksTitle:SetText("Thank you for testing")
    thanksTitle:SetTextColor(unpack(ATA.UI.theme.colors.gold))

    local thanksText = thanks:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
    thanksText:SetPoint("TOPLEFT", thanksTitle, "BOTTOMLEFT", 0, -8)
    thanksText:SetPoint("RIGHT", thanks, "RIGHT", -12, 0)
    thanksText:SetJustifyH("LEFT")
    thanksText:SetText("Your feedback helps improve Alt Tracking Assistant. Thank you for trying the addon and reporting issues.")
    return page
end

local function RegisterOptionsCategory(panel, name, parentCategory)
    panel.name = name
    if parentCategory and Settings and Settings.RegisterCanvasLayoutSubcategory then
        local category = Settings.RegisterCanvasLayoutSubcategory(parentCategory, panel, name)
        Settings.RegisterAddOnCategory(category)
        return category
    end

    if Settings and Settings.RegisterCanvasLayoutCategory and Settings.RegisterAddOnCategory then
        local category = Settings.RegisterCanvasLayoutCategory(panel, name)
        Settings.RegisterAddOnCategory(category)
        return category
    end

    if InterfaceOptions_AddCategory then
        if parentCategory then
            panel.parent = parentCategory.name
        end
        InterfaceOptions_AddCategory(panel)
        return panel
    end

    error("World of Warcraft does not provide an AddOn Options registration API.")
end

local function CreateOptionsPages()
    local overviewPage = CreateOverviewPage()
    local mainsPage = CreateMainsPage()
    local expansionsPage = CreateExpansionsPage()
    local overviewCategory = RegisterOptionsCategory(overviewPage, "Alt Tracking Assistant")
    RegisterOptionsCategory(mainsPage, "Mains", overviewCategory)
    RegisterOptionsCategory(expansionsPage, "Expansions", overviewCategory)

    local refreshElapsed = 0
    local refreshFrame = CreateFrame("Frame")
    refreshFrame:SetScript("OnUpdate", function(_, elapsed)
        refreshElapsed = refreshElapsed + elapsed
        if refreshElapsed >= 0.25 then
            refreshElapsed = 0
            mainsPage:RefreshControls()
            expansionsPage:RefreshControls()
        end
    end)
end

function ATA:IsTrackerEnabled(expansionKey, checkID)
    local settings = self.db and self.db.settings
    local trackedItems = settings and settings.trackedItems
    local expansionSettings = trackedItems and trackedItems[expansionKey]
    local enabled = expansionSettings and expansionSettings[checkID]
    if enabled == nil then
        return true
    end
    return enabled == true
end

function ATA:SetTrackerEnabled(expansionKey, checkID, enabled)
    if not self.db or not self.db.settings then
        error("Alt Tracking Assistant settings are not initialized.")
    end

    local trackedItems = self.db.settings.trackedItems
    if not trackedItems then
        trackedItems = {}
        self.db.settings.trackedItems = trackedItems
    end

    local expansionSettings = trackedItems[expansionKey]
    if not expansionSettings then
        expansionSettings = {}
        trackedItems[expansionKey] = expansionSettings
    end
    expansionSettings[checkID] = enabled == true

    if self.UpdateReport then
        self:UpdateReport()
    end
end

CreateOptionsPages()
