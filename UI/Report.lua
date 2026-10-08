local _, ATA = ...

local reportFrame
local ROW_HEIGHT = 30
local ROSTER_ROW_HEIGHT = 42
local ROSTER_GROUP_GAP = 12
local TRUE_MAIN_ICON = "|TInterface\\GroupFrame\\UI-Group-LeaderIcon:14:14:0:0|t"
local ROSTER_CLASS_ORDER = {
    PALADIN = { group = 1, order = 1 },
    WARRIOR = { group = 1, order = 2 },
    DEATHKNIGHT = { group = 1, order = 3 },
    HUNTER = { group = 2, order = 1 },
    SHAMAN = { group = 2, order = 2 },
    EVOKER = { group = 2, order = 3 },
    DRUID = { group = 3, order = 1 },
    ROGUE = { group = 3, order = 2 },
    MONK = { group = 3, order = 3 },
    DEMONHUNTER = { group = 3, order = 4 },
    MAGE = { group = 4, order = 1 },
    PRIEST = { group = 4, order = 2 },
    WARLOCK = { group = 4, order = 3 },
}
local CLASS_ICON_COORDS = {
    WARRIOR = { 0, 0.25, 0, 0.25 },
    MAGE = { 0.25, 0.5, 0, 0.25 },
    ROGUE = { 0.5, 0.75, 0, 0.25 },
    DRUID = { 0.75, 1, 0, 0.25 },
    HUNTER = { 0, 0.25, 0.25, 0.5 },
    SHAMAN = { 0.25, 0.5, 0.25, 0.5 },
    PRIEST = { 0.5, 0.75, 0.25, 0.5 },
    WARLOCK = { 0.75, 1, 0.25, 0.5 },
    PALADIN = { 0, 0.25, 0.5, 0.75 },
    DEATHKNIGHT = { 0.25, 0.5, 0.5, 0.75 },
    MONK = { 0.5, 0.75, 0.5, 0.75 },
    DEMONHUNTER = { 0.75, 1, 0.5, 0.75 },
    EVOKER = { 0, 0.25, 0.75, 1 },
}

local function GetCharacterLabel(record)
    local name = record and record.name or "Unknown"
    local realm = record and record.realm
    if not realm or realm == "" then
        realm = "Unknown Realm"
    end
    return name .. " — " .. realm
end

local function GetCharacterEntries()
    local entries = {}
    local seen = {}

    for key, record in pairs(ATA.db.characters) do
        entries[#entries + 1] = {
            key = key,
            label = GetCharacterLabel(record),
            record = record,
            classFile = record.classFile,
            name = record.name or "Unknown",
            level = record.level,
            faction = record.faction,
        }
        seen[key] = true
    end

    local currentGUID = UnitGUID("player")
    if currentGUID and not seen[currentGUID] then
        local _, classFile = UnitClass("player")
        entries[#entries + 1] = {
            key = currentGUID,
            label = GetCharacterLabel({
                name = UnitName("player"),
                realm = GetRealmName(),
            }),
            classFile = classFile,
            name = UnitName("player") or "Unknown",
            level = UnitLevel("player"),
            faction = UnitFactionGroup("player"),
        }
    end

    table.sort(entries, function(left, right)
        local leftOrder = ROSTER_CLASS_ORDER[left.classFile] or { group = 5, order = 99 }
        local rightOrder = ROSTER_CLASS_ORDER[right.classFile] or { group = 5, order = 99 }
        if leftOrder.group ~= rightOrder.group then
            return leftOrder.group < rightOrder.group
        end
        if leftOrder.order ~= rightOrder.order then
            return leftOrder.order < rightOrder.order
        end
        local leftLevel = left.level or 0
        local rightLevel = right.level or 0
        if leftLevel ~= rightLevel then
            return leftLevel > rightLevel
        end
        return left.label < right.label
    end)

    return entries
end

local function GetSelectedCharacter(entries)
    local selectedKey = ATA.selectedCharacterKey or UnitGUID("player")
    for _, entry in ipairs(entries) do
        if entry.key == selectedKey then
            ATA.selectedCharacterKey = selectedKey
            return entry
        end
    end

    local selectedEntry = entries[1]
    ATA.selectedCharacterKey = selectedEntry and selectedEntry.key
    return selectedEntry
end

local function GetProgress(record, expansionKey)
    local definition = ATA.trackerDefinitions[expansionKey]
    local savedProgress = record and record.progress and record.progress[expansionKey]
    local total = 0
    for _, check in ipairs(definition.checks) do
        if ATA:IsTrackerEnabled(expansionKey, check.id) and check.type ~= "select" then
            total = total + 1
        end
    end
    local scannedProgress = savedProgress
        and (definition.getProgress and definition.getProgress(savedProgress) or savedProgress)
    local progress = {}
    for checkID, value in pairs(scannedProgress or {}) do
        progress[checkID] = value
    end
    local hasProgress = savedProgress ~= nil
    local overrides = record and record.manualOverrides and record.manualOverrides[expansionKey]
    for _, check in ipairs(definition.checks) do
        local override = overrides and overrides[check.id]
        if check.type ~= "count" and check.type ~= "select" and override and override.active == true then
            progress[check.id] = override.value == true
            hasProgress = true
        end
    end
    if not hasProgress then
        return nil, 0, total
    end

    local completed = 0
    for _, check in ipairs(definition.checks) do
        if ATA:IsTrackerEnabled(expansionKey, check.id) and check.type ~= "select" then
            local value = progress[check.id]
            if check.type == "count" then
                if type(value) == "number" then
                    completed = completed + math.max(0, math.min(1, value / check.max))
                end
            elseif value == true then
                completed = completed + 1
            end
        end
    end

    return progress, completed, total
end

local function GetClassColor(classFile)
    local color = classFile and RAID_CLASS_COLORS and RAID_CLASS_COLORS[classFile]
    if color then
        return color.r, color.g, color.b
    end
    return unpack(ATA.UI.theme.colors.classFallback)
end

local function CreateRoundedProgressBar(parent, height)
    local bar = CreateFrame("Frame", nil, parent)
    bar:SetHeight(height)

    local function CreateLayer(layerParent, drawLayer, red, green, blue, alpha)
        local layer = {
            body = layerParent:CreateTexture(nil, drawLayer),
            leftCap = layerParent:CreateTexture(nil, drawLayer),
            rightCap = layerParent:CreateTexture(nil, drawLayer),
        }
        layer.body:SetTexture("Interface\\Buttons\\WHITE8X8")
        layer.body:SetVertexColor(red, green, blue, alpha)
        layer.body:SetPoint("TOPLEFT", layerParent, "TOPLEFT", height / 2, 0)
        layer.body:SetPoint("BOTTOMLEFT", layerParent, "BOTTOMLEFT", height / 2, 0)
        layer.leftCap:SetTexture("Interface\\Buttons\\WHITE8X8")
        layer.rightCap:SetTexture("Interface\\Buttons\\WHITE8X8")
        layer.leftCap:SetVertexColor(red, green, blue, alpha)
        layer.rightCap:SetVertexColor(red, green, blue, alpha)

        for _, cap in ipairs({ layer.leftCap, layer.rightCap }) do
            cap:SetSize(height, height)
            local mask = layerParent:CreateMaskTexture(nil, drawLayer)
            mask:SetTexture("Interface\\CharacterFrame\\TempPortraitAlphaMask")
            mask:SetAllPoints(cap)
            cap:AddMaskTexture(mask)
        end

        layer.leftCap:SetPoint("LEFT", layerParent, "LEFT", 0, 0)
        layer.rightCap:SetPoint("RIGHT", layerParent, "RIGHT", 0, 0)
        return layer
    end

    local background = CreateLayer(bar, "ARTWORK", 0.015, 0.025, 0.035, 1)
    local fillContainer = CreateFrame("Frame", nil, bar)
    fillContainer:SetPoint("TOPLEFT", bar, "TOPLEFT")
    fillContainer:SetPoint("BOTTOMLEFT", bar, "BOTTOMLEFT")
    local fill = CreateLayer(fillContainer, "OVERLAY", 1, 1, 1, 1)
    bar.fill = fill

    function bar:SetValue(fraction, red, green, blue)
        local width = self:GetWidth()
        local fillWidth = math.max(0, math.min(width, width * fraction))
        background.body:SetWidth(math.max(0, width - height))
        background.leftCap:Show()
        background.rightCap:Show()
        fillContainer:SetWidth(fillWidth)
        fill.body:SetWidth(math.max(0, fillWidth - height))

        if fillWidth <= 0 then
            fill.leftCap:Hide()
            fill.rightCap:Hide()
            fill.body:SetWidth(0)
        elseif fillWidth < height then
            fill.leftCap:SetSize(fillWidth, fillWidth)
            fill.leftCap:ClearAllPoints()
            fill.leftCap:SetPoint("LEFT", fillContainer, "LEFT", 0, 0)
            fill.leftCap:Show()
            fill.rightCap:Hide()
            fill.body:SetWidth(0)
        else
            fill.leftCap:SetSize(height, height)
            fill.leftCap:ClearAllPoints()
            fill.leftCap:SetPoint("LEFT", fillContainer, "LEFT", 0, 0)
            fill.leftCap:Show()
            fill.rightCap:SetSize(height, height)
            fill.rightCap:Show()
        end
        fill.body:SetVertexColor(red, green, blue, 1)
        fill.leftCap:SetVertexColor(red, green, blue, 1)
        fill.rightCap:SetVertexColor(red, green, blue, 1)
    end

    return bar
end

local function CreateCard(parent, width, height)
    local card = CreateFrame("Frame", nil, parent, "BackdropTemplate")
    card:SetSize(width, height)
    card:SetBackdrop({
        bgFile = "Interface\\Buttons\\WHITE8X8",
        edgeFile = "Interface\\Buttons\\WHITE8X8",
        edgeSize = 1,
        insets = { left = 1, right = 1, top = 1, bottom = 1 },
    })
    card:SetBackdropColor(unpack(ATA.UI.theme.colors.panel))
    card:SetBackdropBorderColor(unpack(ATA.UI.theme.colors.panelBorder))
    return card
end

local function CreateThemedButton(parent, text, width, height)
    local button = CreateFrame("Button", nil, parent, "BackdropTemplate")
    button:SetSize(width, height)
    button:SetBackdrop({
        bgFile = "Interface\\Buttons\\WHITE8X8",
        edgeFile = "Interface\\Buttons\\WHITE8X8",
        edgeSize = 1,
        insets = { left = 1, right = 1, top = 1, bottom = 1 },
    })
    button:SetBackdropColor(0.12, 0.16, 0.20, 1)
    button:SetBackdropBorderColor(unpack(ATA.UI.theme.colors.goldDark))

    local label = button:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
    label:SetPoint("CENTER")
    label:SetText(text)
    label:SetTextColor(unpack(ATA.UI.theme.colors.gold))
    button.label = label

    button:SetScript("OnEnter", function(self)
        self:SetBackdropColor(0.20, 0.23, 0.25, 1)
        self:SetBackdropBorderColor(unpack(ATA.UI.theme.colors.gold))
    end)
    button:SetScript("OnLeave", function(self)
        self:SetBackdropColor(0.12, 0.16, 0.20, 1)
        self:SetBackdropBorderColor(unpack(ATA.UI.theme.colors.goldDark))
    end)
    return button
end

local function CreateExpansionCard(parent, anchor, expansionKey, options)
    local checks = ATA.trackerDefinitions[expansionKey].checks
    local mainCard = CreateCard(parent, 650, 296)
    mainCard:SetPoint("TOPLEFT", anchor, "BOTTOMLEFT", 0, -8)
    mainCard:SetBackdropColor(unpack(ATA.UI.theme.colors.panel))
    mainCard:SetBackdropBorderColor(unpack(ATA.UI.theme.colors.expansions[expansionKey]))
    mainCard:SetHeight(44)

    local sectionHeader = CreateFrame("Button", nil, mainCard)
    sectionHeader:SetPoint("TOPLEFT", mainCard, "TOPLEFT", 3, -3)
    sectionHeader:SetPoint("TOPRIGHT", mainCard, "TOPRIGHT", -3, -3)
    sectionHeader:SetHeight(56)

    local headerBackground = sectionHeader:CreateTexture(nil, "BACKGROUND")
    headerBackground:SetAllPoints()
    headerBackground:SetTexture("Interface\\Buttons\\WHITE8X8")
    headerBackground:SetVertexColor(unpack(ATA.UI.theme.colors.expansions[expansionKey]))

    local collapseIcon = sectionHeader:CreateTexture(nil, "ARTWORK")
    collapseIcon:SetSize(14, 14)
    collapseIcon:SetPoint("LEFT", sectionHeader, "LEFT", 12, 0)
    collapseIcon:SetTexture("Interface\\Buttons\\UI-MinusButton-Up")

    local sectionIcon = sectionHeader:CreateTexture(nil, "OVERLAY")
    local iconSize = options.iconSize or 56
    sectionIcon:SetSize(iconSize, iconSize)
    sectionIcon:SetPoint("LEFT", collapseIcon, "RIGHT", 8, 0)
    sectionIcon:SetTexture(options.icon)

    local sectionTitle = sectionHeader:CreateFontString(nil, "OVERLAY", "GameFontNormalLarge")
    sectionTitle:SetPoint("LEFT", sectionIcon, "RIGHT", 8, 10)
    sectionTitle:SetText(options.title)
    local titleFont, titleSize, titleFlags = sectionTitle:GetFont()
    sectionTitle:SetFont(titleFont, titleSize + 4, titleFlags)
    sectionTitle:SetTextColor(unpack(options.titleColor))

    local sectionSubtitle = sectionHeader:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
    sectionSubtitle:SetPoint("LEFT", sectionIcon, "RIGHT", 8, -10)
    sectionSubtitle:SetText(options.subtitle)
    sectionSubtitle:SetTextColor(
        options.subtitleColor[1],
        options.subtitleColor[2],
        options.subtitleColor[3],
        options.subtitleAlpha
    )

    local sectionProgressText = sectionHeader:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
    sectionProgressText:SetPoint("TOPRIGHT", sectionHeader, "TOPRIGHT", -12, -12)
    sectionProgressText:SetJustifyH("RIGHT")

    local sectionProgressBar = CreateRoundedProgressBar(sectionHeader, 8)
    sectionProgressBar:SetSize(150, 8)
    sectionProgressBar:SetPoint("TOPRIGHT", sectionHeader, "TOPRIGHT", -12, -32)

    local sectionBody = CreateFrame("Frame", nil, mainCard)
    sectionBody:SetPoint("TOPLEFT", sectionHeader, "BOTTOMLEFT", 0, 0)
    sectionBody:SetPoint("TOPRIGHT", sectionHeader, "BOTTOMRIGHT", 0, 0)

    local checkRows = {}
    local columnCount = 3
    local sectionWidth = 644
    local columnWidth = sectionWidth / columnCount
    local dividers = {}
    for column = 1, columnCount - 1 do
        local divider = sectionBody:CreateTexture(nil, "BACKGROUND")
        divider:SetTexture("Interface\\Buttons\\WHITE8X8")
        divider:SetVertexColor(unpack(ATA.UI.theme.colors.divider))
        divider:SetWidth(1)
        dividers[column] = divider
    end

    for _, check in ipairs(checks) do
        if check.type == "select" then
            local label = sectionBody:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
            label:SetPoint("TOPLEFT", sectionBody, "TOPLEFT", 16, -12)
            label:SetText(check.label .. ":")

            local button = CreateThemedButton(sectionBody, "Select Covenant", 170, 24)
            button:SetPoint("TOPRIGHT", sectionBody, "TOPRIGHT", -16, -9)
            button.label:ClearAllPoints()
            button.label:SetPoint("LEFT", button, "LEFT", 9, 0)
            button.label:SetPoint("RIGHT", button, "RIGHT", -22, 0)
            button.label:SetJustifyH("LEFT")

            local dropdownArrow = button:CreateFontString(nil, "OVERLAY", "GameFontNormal")
            dropdownArrow:SetPoint("RIGHT", button, "RIGHT", -8, 0)
            dropdownArrow:SetText("v")
            dropdownArrow:SetTextColor(unpack(ATA.UI.theme.colors.gold))

            local viewLabel = sectionBody:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
            viewLabel:SetPoint("RIGHT", button, "LEFT", -10, 0)
            viewLabel:SetText("View:")
            viewLabel:SetTextColor(unpack(ATA.UI.theme.colors.mutedText))

            local activeCovenantIcon = sectionBody:CreateTexture(nil, "ARTWORK")
            activeCovenantIcon:SetSize(24, 24)
            activeCovenantIcon:SetPoint("LEFT", label, "RIGHT", 8, 0)
            activeCovenantIcon:Hide()

            local activeCovenantText = sectionBody:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
            activeCovenantText:SetPoint("LEFT", activeCovenantIcon, "RIGHT", 6, 0)
            activeCovenantText:SetTextColor(unpack(ATA.UI.theme.colors.mutedText))

            local menu = CreateCard(mainCard, 170, 30)
            menu:SetFrameStrata("DIALOG")
            menu:SetFrameLevel(button:GetFrameLevel() + 10)
            menu:SetPoint("TOPLEFT", button, "BOTTOMLEFT", 0, -2)
            menu:Hide()
            menu.rows = {}

            button:SetScript("OnClick", function()
                if menu:IsShown() then
                    menu:Hide()
                    return
                end

                local choices = ATA.shadowlandsCovenants or {}
                menu:SetHeight(math.max(28, #choices * 28 + 4))
                for index, covenant in ipairs(choices) do
                    local option = menu.rows[index]
                    if not option then
                        option = CreateThemedButton(menu, "", 160, 26)
                        menu.rows[index] = option
                    end
                    option:ClearAllPoints()
                    option:SetPoint("TOPLEFT", menu, "TOPLEFT", 4, -((index - 1) * 28) - 3)
                    option:SetPoint("RIGHT", menu, "RIGHT", -4, 0)
                    option.label:SetText(covenant.name)
                    local selectedCovenantID = covenant.id
                    option:SetScript("OnClick", function()
                        menu:Hide()
                        if options.onCovenantChanged then
                            options.onCovenantChanged(selectedCovenantID)
                        end
                    end)
                    option:Show()
                end
                menu:Show()
            end)

            checkRows[check.id] = {
                type = "select",
                label = label,
                button = button,
                viewLabel = viewLabel,
                activeIcon = activeCovenantIcon,
                activeText = activeCovenantText,
            }
        else
            local label = sectionBody:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
            label:SetJustifyH("LEFT")
            label:SetText(check.label)

            if check.type == "count" then
                local value = sectionBody:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
                value:SetWidth(48)
                value:SetJustifyH("RIGHT")
                value:SetTextColor(unpack(ATA.UI.theme.colors.text))
                checkRows[check.id] = { type = "count", label = label, value = value, max = check.max }
            else
                local status = CreateFrame("Frame", nil, sectionBody, "BackdropTemplate")
                status:SetSize(18, 18)
                status:SetFrameLevel(sectionBody:GetFrameLevel() + 2)
                status:SetBackdrop({
                    bgFile = "Interface\\Buttons\\WHITE8X8",
                    edgeFile = "Interface\\Buttons\\WHITE8X8",
                    edgeSize = 1,
                    insets = { left = 1, right = 1, top = 1, bottom = 1 },
                })
                status:SetBackdropColor(unpack(ATA.UI.theme.colors.panel))
                status:SetBackdropBorderColor(unpack(ATA.UI.theme.colors.gold))

                local checkmark = status:CreateTexture(nil, "ARTWORK")
                checkmark:SetSize(14, 14)
                checkmark:SetPoint("CENTER")
                checkmark:SetTexture("Interface\\Buttons\\UI-CheckBox-Check")
                checkmark:SetVertexColor(unpack(ATA.UI.theme.colors.gold))

                local unknown = status:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
                unknown:SetPoint("CENTER")
                unknown:SetText("?")
                unknown:SetTextColor(unpack(ATA.UI.theme.colors.mutedText))
                checkRows[check.id] = {
                    type = "boolean",
                    label = label,
                    status = status,
                    checkmark = checkmark,
                    unknown = unknown,
                }
            end
        end
    end

    local collapsedCardHeight = 62
    local isExpanded = true
    local emptyMessage = sectionBody:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
    emptyMessage:SetPoint("TOPLEFT", sectionBody, "TOPLEFT", 16, -12)
    emptyMessage:SetText("No trackers enabled")
    emptyMessage:SetTextColor(unpack(ATA.UI.theme.colors.mutedText))
    emptyMessage:Hide()

    local function LayoutChecks()
        local covenantRowVisible = false
        local visibleCheckCount = 0
        local gridIndex = 0

        for _, check in ipairs(checks) do
            local row = checkRows[check.id]
            local enabled = ATA:IsTrackerEnabled(expansionKey, check.id)
            if check.type == "select" then
                covenantRowVisible = true
                row.label:SetShown(true)
                row.button:SetShown(enabled)
                row.viewLabel:SetShown(enabled)
                row.activeIcon:SetShown(row.activeIcon:GetTexture() ~= nil)
                row.activeText:SetShown(true)
                visibleCheckCount = visibleCheckCount + 1
            else
                row.label:SetShown(enabled)
                if row.type == "count" then
                    row.value:SetShown(enabled)
                else
                    row.status:SetShown(enabled)
                end
                if enabled then
                    gridIndex = gridIndex + 1
                    visibleCheckCount = visibleCheckCount + 1
                end
            end
        end

        for column, divider in ipairs(dividers) do
            local visible = gridIndex > 0
            divider:ClearAllPoints()
            divider:SetPoint(
                "TOPLEFT",
                sectionBody,
                "TOPLEFT",
                column * columnWidth,
                covenantRowVisible and (-ROW_HEIGHT - 6) or -6
            )
            divider:SetPoint("BOTTOMLEFT", sectionBody, "BOTTOMLEFT", column * columnWidth, 6)
            divider:SetShown(visible)
        end

        gridIndex = 0
        for _, check in ipairs(checks) do
            if ATA:IsTrackerEnabled(expansionKey, check.id) and check.type ~= "select" then
                gridIndex = gridIndex + 1
                local row = checkRows[check.id]
                local column = ((gridIndex - 1) % columnCount) + 1
                local gridRow = math.floor((gridIndex - 1) / columnCount)
                    + (covenantRowVisible and 1 or 0)
                local rowTop = -12 - (gridRow * ROW_HEIGHT)
                local columnLeft = (column - 1) * columnWidth
                row.label:ClearAllPoints()
                row.label:SetPoint("TOPLEFT", sectionBody, "TOPLEFT", columnLeft + 16, rowTop)
                row.label:SetWidth(columnWidth - (row.type == "count" and 82 or 58))
                if row.type == "count" then
                    row.value:ClearAllPoints()
                    row.value:SetPoint(
                        "TOPRIGHT",
                        sectionBody,
                        "TOPLEFT",
                        column * columnWidth - 10,
                        rowTop - 1
                    )
                else
                    row.status:ClearAllPoints()
                    row.status:SetPoint(
                        "TOPLEFT",
                        sectionBody,
                        "TOPLEFT",
                        (column * columnWidth) - 32,
                        rowTop - 3
                    )
                end
            elseif check.type == "select" then
                local row = checkRows[check.id]
                row.label:ClearAllPoints()
                row.label:SetPoint("TOPLEFT", sectionBody, "TOPLEFT", 16, -12)
                row.button:ClearAllPoints()
                row.button:SetPoint("TOPRIGHT", sectionBody, "TOPRIGHT", -16, -9)
                row.viewLabel:ClearAllPoints()
                row.viewLabel:SetPoint("RIGHT", row.button, "LEFT", -10, 0)
                row.activeIcon:ClearAllPoints()
                row.activeIcon:SetPoint("LEFT", row.label, "RIGHT", 8, 0)
                row.activeText:ClearAllPoints()
                row.activeText:SetPoint("LEFT", row.activeIcon, "RIGHT", 6, 0)
            end
        end

        emptyMessage:SetShown(visibleCheckCount == 0)
        local bodyHeight = visibleCheckCount == 0
            and 40
            or (20 + ((math.ceil(gridIndex / columnCount) + (covenantRowVisible and 1 or 0)) * ROW_HEIGHT))
        sectionBody:SetHeight(bodyHeight)
        local expandedCardHeight = collapsedCardHeight + bodyHeight
        mainCard:SetHeight(isExpanded and expandedCardHeight or collapsedCardHeight)
        if options.onHeightChanged then
            options.onHeightChanged()
        end
    end

    sectionHeader:SetScript("OnClick", function()
        isExpanded = not isExpanded
        sectionBody:SetShown(isExpanded)
        collapseIcon:SetTexture(isExpanded and "Interface\\Buttons\\UI-MinusButton-Up" or "Interface\\Buttons\\UI-PlusButton-Up")
        LayoutChecks()
    end)
    LayoutChecks()

    return {
        card = mainCard,
        checkRows = checkRows,
        updateVisibility = LayoutChecks,
        progressText = sectionProgressText,
        progressBar = sectionProgressBar,
        progressColor = options.progressColor,
    }
end

local function CreateRosterRow(parent)
    local row = CreateFrame("Button", nil, parent)
    row:SetHeight(ROSTER_ROW_HEIGHT)

    local background = row:CreateTexture(nil, "BACKGROUND")
    background:SetAllPoints()
    background:SetTexture("Interface\\Buttons\\WHITE8X8")
    background:SetVertexColor(0.08, 0.10, 0.13, 0.8)
    row.background = background

    local highlight = row:CreateTexture(nil, "HIGHLIGHT")
    highlight:SetAllPoints()
    highlight:SetTexture("Interface\\Buttons\\WHITE8X8")
    highlight:SetVertexColor(0.22, 0.25, 0.30, 0.55)

    local avatarBorder = row:CreateTexture(nil, "ARTWORK")
    avatarBorder:SetSize(30, 30)
    avatarBorder:SetPoint("LEFT", row, "LEFT", 3, 0)
    avatarBorder:SetTexture("Interface\\Buttons\\WHITE8X8")
    avatarBorder:SetVertexColor(unpack(ATA.UI.theme.colors.gold))
    local avatarBorderMask = row:CreateMaskTexture(nil, "ARTWORK")
    avatarBorderMask:SetTexture("Interface\\CharacterFrame\\TempPortraitAlphaMask")
    avatarBorderMask:SetAllPoints(avatarBorder)
    avatarBorder:AddMaskTexture(avatarBorderMask)

    local avatar = row:CreateTexture(nil, "OVERLAY")
    avatar:SetSize(26, 26)
    avatar:SetPoint("CENTER", avatarBorder, "CENTER")
    avatar:SetTexture("Interface\\Icons\\INV_Misc_QuestionMark")
    local avatarMask = row:CreateMaskTexture(nil, "OVERLAY")
    avatarMask:SetTexture("Interface\\CharacterFrame\\TempPortraitAlphaMask")
    avatarMask:SetAllPoints(avatar)
    avatar:AddMaskTexture(avatarMask)

    local name = row:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
    name:SetPoint("TOPLEFT", avatar, "TOPRIGHT", 7, -3)
    name:SetJustifyH("LEFT")
    name:SetWordWrap(false)

    local completion = row:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
    completion:SetPoint("TOPRIGHT", row, "TOPRIGHT", -7, -4)
    completion:SetJustifyH("RIGHT")
    name:SetPoint("RIGHT", completion, "LEFT", -5, 0)

    local progressBar = CreateRoundedProgressBar(row, 5)
    progressBar:SetPoint("BOTTOMLEFT", name, "BOTTOMLEFT", 0, -6)
    progressBar:SetPoint("BOTTOMRIGHT", row, "BOTTOMRIGHT", -7, 7)

    row.nameText = name
    row.completionText = completion
    row.avatarBorder = avatarBorder
    row.avatar = avatar
    row.progressBar = progressBar
    row:SetScript("OnClick", function(self)
        ATA.selectedCharacterKey = self.characterKey
        ATA:UpdateReport()
    end)
    return row
end

local function CreateReportFrame()
    local frame = CreateFrame("Frame", "AltTrackingAssistantReportFrame", UIParent, "BackdropTemplate")
    table.insert(UISpecialFrames, frame:GetName())
    frame:SetSize(980, 660)
    frame:SetPoint("CENTER")
    frame:SetBackdrop({
        bgFile = "Interface\\Buttons\\WHITE8X8",
        edgeFile = "Interface\\Buttons\\WHITE8X8",
        edgeSize = 2,
        insets = { left = 2, right = 2, top = 2, bottom = 2 },
    })
    frame:SetBackdropColor(unpack(ATA.UI.theme.colors.panel))
    frame:SetBackdropBorderColor(unpack(ATA.UI.theme.colors.gold))
    frame:SetMovable(true)
    frame:EnableMouse(true)
    frame:RegisterForDrag("LeftButton")
    frame:SetScript("OnDragStart", frame.StartMoving)
    frame:SetScript("OnDragStop", frame.StopMovingOrSizing)
    frame:SetClampedToScreen(true)

    local closeButton = CreateThemedButton(frame, "X", 26, 24)
    closeButton:SetPoint("TOPRIGHT", frame, "TOPRIGHT", -6, -6)
    closeButton:SetScript("OnClick", function()
        frame:Hide()
    end)

    local title = frame:CreateFontString(nil, "OVERLAY", "GameFontNormalLarge")
    title:SetPoint("TOPLEFT", frame, "TOPLEFT", 18, -16)
    title:SetText("ALT TRACKING ASSISTANT")
    title:SetTextColor(unpack(ATA.UI.theme.colors.gold))

    local subtitle = frame:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
    subtitle:SetPoint("TOPLEFT", title, "BOTTOMLEFT", 0, -3)
    subtitle:SetText("CHARACTER PROGRESS REPORT")
    subtitle:SetTextColor(unpack(ATA.UI.theme.colors.mutedText))

    local characterCard = CreateCard(frame, 938, 78)
    characterCard:SetPoint("TOP", frame, "TOP", 0, -82)

    local characterIconBorder = characterCard:CreateTexture(nil, "ARTWORK")
    characterIconBorder:SetSize(64, 64)
    characterIconBorder:SetPoint("LEFT", characterCard, "LEFT", 12, 0)
    characterIconBorder:SetTexture("Interface\\Buttons\\WHITE8X8")
    characterIconBorder:SetVertexColor(unpack(ATA.UI.theme.colors.gold))
    local characterIconBorderMask = characterCard:CreateMaskTexture(nil, "ARTWORK")
    characterIconBorderMask:SetTexture("Interface\\CharacterFrame\\TempPortraitAlphaMask")
    characterIconBorderMask:SetAllPoints(characterIconBorder)
    characterIconBorder:AddMaskTexture(characterIconBorderMask)

    local characterIcon = characterCard:CreateTexture(nil, "OVERLAY")
    characterIcon:SetSize(60, 60)
    characterIcon:SetPoint("CENTER", characterIconBorder, "CENTER")
    local characterIconMask = characterCard:CreateMaskTexture(nil, "OVERLAY")
    characterIconMask:SetTexture("Interface\\CharacterFrame\\TempPortraitAlphaMask")
    characterIconMask:SetAllPoints(characterIcon)
    characterIcon:AddMaskTexture(characterIconMask)

    local characterNameText = characterCard:CreateFontString(nil, "OVERLAY", "GameFontNormalLarge")
    characterNameText:SetPoint("LEFT", characterIconBorder, "RIGHT", 14, 8)
    characterNameText:SetWidth(200)
    characterNameText:SetJustifyH("LEFT")
    characterNameText:SetTextColor(unpack(ATA.UI.theme.colors.text))

    local characterBirthDateText = characterCard:CreateFontString(nil, "OVERLAY", "GameFontDisableSmall")
    characterBirthDateText:SetPoint("TOPLEFT", characterNameText, "BOTTOMLEFT", 0, -3)
    characterBirthDateText:SetWidth(200)
    characterBirthDateText:SetJustifyH("LEFT")
    characterBirthDateText:SetTextColor(unpack(ATA.UI.theme.colors.mutedText))

    local function AddCharacterField(labelText, x, width)
        local label = characterCard:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
        label:SetPoint("TOPLEFT", characterCard, "TOPLEFT", x, -26)
        label:SetText(labelText)
        label:SetTextColor(unpack(ATA.UI.theme.colors.mutedText))

        local value = characterCard:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
        value:SetPoint("TOPLEFT", label, "BOTTOMLEFT", 0, -5)
        value:SetWidth(width)
        value:SetJustifyH("LEFT")
        return label, value
    end

    local realmLabel, realmText = AddCharacterField("REALM", 320, 150)

    local factionIcon = characterCard:CreateTexture(nil, "ARTWORK")
    factionIcon:SetSize(64, 64)
    factionIcon:SetPoint("CENTER", characterCard, "LEFT", 488, 0)

    local classLabel, classText = AddCharacterField("CLASS", 552, 112)
    local classIcon = characterCard:CreateTexture(nil, "ARTWORK")
    classIcon:SetSize(16, 16)
    classIcon:SetPoint("TOPLEFT", classLabel, "BOTTOMLEFT", 0, -5)
    classText:ClearAllPoints()
    classText:SetPoint("TOPLEFT", classLabel, "BOTTOMLEFT", 21, -5)
    classText:SetWidth(155)
    classText:SetJustifyH("LEFT")
    classText:SetWordWrap(false)
    classText:SetNonSpaceWrap(false)

    local levelLabel, levelText = AddCharacterField("LEVEL", 732, 42)

    local rescanButton = CreateThemedButton(characterCard, "Rescan", 90, 26)
    rescanButton:SetPoint("RIGHT", characterCard, "RIGHT", -12, 0)
    rescanButton:SetScript("OnClick", function()
        local success, result = ATA:ScanCurrentCharacter()
        if not success then
            print("|cffff4444Alt Tracking Assistant:|r " .. result)
            return
        end
        ATA.selectedCharacterKey = UnitGUID("player")
        ATA:UpdateReport()
    end)

    local contentRow = CreateFrame("Frame", nil, frame)
    contentRow:SetWidth(938)
    contentRow:SetPoint("TOP", characterCard, "BOTTOM", 0, -8)
    contentRow:SetPoint("BOTTOM", frame, "BOTTOM", 0, 30)

    local expansionScroll = CreateFrame("ScrollFrame", nil, contentRow)
    expansionScroll:SetPoint("TOPLEFT", contentRow, "TOPLEFT")
    expansionScroll:SetPoint("BOTTOMLEFT", contentRow, "BOTTOMLEFT")
    expansionScroll:SetWidth(650)
    expansionScroll:EnableMouseWheel(true)
    expansionScroll:SetClipsChildren(true)

    local expansionContent = CreateFrame("Frame", nil, expansionScroll)
    expansionContent:SetWidth(650)
    expansionContent:SetHeight(1)
    expansionContent:SetPoint("TOPLEFT", expansionScroll, "TOPLEFT")
    expansionScroll:SetScrollChild(expansionContent)

    local expansionTopAnchor = CreateFrame("Frame", nil, expansionContent)
    expansionTopAnchor:SetSize(1, 1)
    expansionTopAnchor:SetPoint("TOPLEFT", expansionContent, "TOPLEFT")

    local expansionCards = {}
    local function UpdateExpansionContentHeight()
        local contentHeight = 8
        for _, card in pairs(expansionCards) do
            contentHeight = contentHeight + card.card:GetHeight() + 8
        end
        expansionContent:SetHeight(contentHeight)
    end

    expansionCards.midnight = CreateExpansionCard(expansionContent, expansionTopAnchor, "midnight", {
        title = "MIDNIGHT",
        subtitle = "THE NEXT CHAPTER",
        subtitleColor = { 0.88, 0.78, 0.96 },
        subtitleAlpha = 1,
        icon = "Interface\\AddOns\\AltTrackingAssistant\\Media\\Singularity.png",
        titleColor = { 237 / 255, 181 / 255, 254 / 255 },
        progressColor = ATA.UI.theme.colors.progress.midnight,
        onHeightChanged = UpdateExpansionContentHeight,
    })
    expansionCards.theWarWithin = CreateExpansionCard(
        expansionContent,
        expansionCards.midnight.card,
        "theWarWithin",
        {
            title = "THE WAR WITHIN",
            subtitle = "THE WORLD BELOW",
            subtitleColor = { 1, 1, 1 },
            subtitleAlpha = 0.7,
            icon = "Interface\\AddOns\\AltTrackingAssistant\\Media\\TheWarWithin.png",
            iconSize = 46,
            titleColor = { 1, 216 / 255, 189 / 255 },
            progressColor = ATA.UI.theme.colors.progress.theWarWithin,
            onHeightChanged = UpdateExpansionContentHeight,
        }
    )
    expansionCards.dragonflight = CreateExpansionCard(
        expansionContent,
        expansionCards.theWarWithin.card,
        "dragonflight",
        {
            title = "DRAGONFLIGHT",
            subtitle = "WORLD AWOKEN",
            subtitleColor = { 1, 1, 1 },
            subtitleAlpha = 0.7,
            icon = "Interface\\AddOns\\AltTrackingAssistant\\Media\\Dragonflight.png",
            titleColor = { 129 / 255, 232 / 255, 235 / 255 },
            progressColor = ATA.UI.theme.colors.progress.dragonflight,
            onHeightChanged = UpdateExpansionContentHeight,
        }
    )
    expansionCards.shadowlands = CreateExpansionCard(
        expansionContent,
        expansionCards.dragonflight.card,
        "shadowlands",
        {
            title = "SHADOWLANDS",
            subtitle = "BEYOND THE VEIL",
            subtitleColor = { 1, 1, 1 },
            subtitleAlpha = 0.7,
            icon = "Interface\\AddOns\\AltTrackingAssistant\\Media\\Shadowlands.png",
            titleColor = { 163 / 255, 248 / 255, 253 / 255 },
            progressColor = ATA.UI.theme.colors.progress.shadowlands,
            onHeightChanged = UpdateExpansionContentHeight,
            onCovenantChanged = function(covenantID)
                local characterKey = ATA.selectedCharacterKey or UnitGUID("player")
                local record = ATA.db.characters[characterKey]
                if not record and characterKey == UnitGUID("player") then
                    local success, result = ATA:ScanCurrentCharacter()
                    if not success then
                        print("|cffff4444Alt Tracking Assistant:|r " .. result)
                        return
                    end
                    record = result
                end
                if not record then
                    print("|cffff4444Alt Tracking Assistant:|r The selected character has no saved record.")
                    return
                end

                record.progress = record.progress or {}
                record.progress.shadowlands = record.progress.shadowlands or {}
                record.progress.shadowlands.covenantID = covenantID
                ATA:UpdateReport()
            end,
        }
    )
    UpdateExpansionContentHeight()

    local expansionScrollBar = CreateFrame("Frame", nil, contentRow, "BackdropTemplate")
    expansionScrollBar:SetWidth(10)
    expansionScrollBar:SetPoint("TOPLEFT", expansionScroll, "TOPRIGHT", 4, 0)
    expansionScrollBar:SetPoint("BOTTOMLEFT", expansionScroll, "BOTTOMRIGHT", 4, 0)
    expansionScrollBar:SetBackdrop({
        bgFile = "Interface\\Buttons\\WHITE8X8",
        edgeFile = "Interface\\Buttons\\WHITE8X8",
        edgeSize = 1,
        insets = { left = 0, right = 0, top = 0, bottom = 0 },
    })
    expansionScrollBar:SetBackdropColor(0.035, 0.045, 0.055, 1)
    expansionScrollBar:SetBackdropBorderColor(unpack(ATA.UI.theme.colors.divider))
    expansionScrollBar:Hide()

    local expansionScrollThumb = CreateFrame("Button", nil, expansionScrollBar, "BackdropTemplate")
    expansionScrollThumb:SetWidth(8)
    expansionScrollThumb:SetBackdrop({
        bgFile = "Interface\\Buttons\\WHITE8X8",
        edgeFile = "Interface\\Buttons\\WHITE8X8",
        edgeSize = 1,
        insets = { left = 1, right = 1, top = 1, bottom = 1 },
    })
    expansionScrollThumb:SetBackdropColor(unpack(ATA.UI.theme.colors.goldDark))
    expansionScrollThumb:SetBackdropBorderColor(unpack(ATA.UI.theme.colors.gold))
    expansionScrollThumb:RegisterForDrag("LeftButton")

    local function UpdateExpansionScrollThumb()
        local viewportHeight = expansionScroll:GetHeight()
        local contentHeight = expansionContent:GetHeight()
        local scrollRange = expansionScroll:GetVerticalScrollRange()
        if viewportHeight <= 0 or contentHeight <= viewportHeight or scrollRange <= 0 then
            expansionScrollThumb:Hide()
            expansionScrollBar:Hide()
            return
        end

        expansionScrollBar:Show()
        expansionScrollThumb:Show()
        local trackHeight = expansionScrollBar:GetHeight()
        local thumbHeight = math.max(28, trackHeight * viewportHeight / contentHeight)
        local thumbTravel = math.max(0, trackHeight - thumbHeight)
        local scrollFraction = expansionScroll:GetVerticalScroll() / scrollRange
        expansionScrollThumb:SetHeight(thumbHeight)
        expansionScrollThumb:ClearAllPoints()
        expansionScrollThumb:SetPoint("TOP", expansionScrollBar, "TOP", 0, -thumbTravel * scrollFraction)
    end

    expansionScroll:SetScript("OnVerticalScroll", UpdateExpansionScrollThumb)
    expansionScroll:SetScript("OnShow", UpdateExpansionScrollThumb)
    expansionScroll:SetScript("OnMouseWheel", function(self, delta)
        local scrollRange = self:GetVerticalScrollRange()
        self:SetVerticalScroll(math.max(0, math.min(scrollRange, self:GetVerticalScroll() - delta * ROW_HEIGHT)))
    end)
    expansionScroll:SetScript("OnSizeChanged", UpdateExpansionScrollThumb)
    expansionContent:SetScript("OnSizeChanged", UpdateExpansionScrollThumb)

    expansionScrollThumb:SetScript("OnDragStart", function(self)
        self:SetScript("OnUpdate", function()
            local scale = expansionScrollBar:GetEffectiveScale()
            local cursorY = select(2, GetCursorPosition()) / scale
            local trackTop = expansionScrollBar:GetTop()
            local trackHeight = expansionScrollBar:GetHeight()
            local thumbHeight = self:GetHeight()
            local thumbTravel = trackHeight - thumbHeight
            local scrollRange = expansionScroll:GetVerticalScrollRange()
            if thumbTravel <= 0 or scrollRange <= 0 then
                return
            end

            local thumbOffset = math.max(0, math.min(thumbTravel, trackTop - cursorY - (thumbHeight / 2)))
            expansionScroll:SetVerticalScroll(scrollRange * thumbOffset / thumbTravel)
        end)
    end)
    expansionScrollThumb:SetScript("OnDragStop", function(self)
        self:SetScript("OnUpdate", nil)
    end)
    UpdateExpansionScrollThumb()

    local rosterCard = CreateCard(contentRow, 266, 1)
    rosterCard:SetPoint("TOPLEFT", contentRow, "TOPLEFT", 672, 0)
    rosterCard:SetPoint("BOTTOMRIGHT", contentRow, "BOTTOMRIGHT")

    local scannedText = frame:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
    scannedText:SetPoint("TOPRIGHT", rosterCard, "BOTTOMRIGHT", -2, -3)
    scannedText:SetWidth(266)
    scannedText:SetJustifyH("RIGHT")
    scannedText:SetTextColor(unpack(ATA.UI.theme.colors.mutedText))

    local rosterTitle = rosterCard:CreateFontString(nil, "OVERLAY", "GameFontNormalLarge")
    rosterTitle:SetPoint("TOPLEFT", rosterCard, "TOPLEFT", 12, -12)
    rosterTitle:SetText("ROSTER SUMMARY")
    rosterTitle:SetTextColor(unpack(ATA.UI.theme.colors.gold))

    local rosterSubtitle = rosterCard:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
    rosterSubtitle:SetPoint("TOPLEFT", rosterTitle, "BOTTOMLEFT", 0, -3)
    rosterSubtitle:SetText("ALL CHARACTERS")
    rosterSubtitle:SetTextColor(unpack(ATA.UI.theme.colors.mutedText))

    local rosterStats = rosterCard:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
    rosterStats:SetPoint("TOPLEFT", rosterSubtitle, "BOTTOMLEFT", 0, -10)
    rosterStats:SetPoint("RIGHT", rosterCard, "RIGHT", -12, 0)
    rosterStats:SetJustifyH("LEFT")

    local rosterDivider = rosterCard:CreateTexture(nil, "ARTWORK")
    rosterDivider:SetTexture("Interface\\Buttons\\WHITE8X8")
    rosterDivider:SetVertexColor(unpack(ATA.UI.theme.colors.divider))
    rosterDivider:SetHeight(1)
    rosterDivider:SetPoint("TOPLEFT", rosterStats, "BOTTOMLEFT", 0, -8)
    rosterDivider:SetPoint("RIGHT", rosterCard, "RIGHT", -12, 0)

    local rosterScroll = CreateFrame("ScrollFrame", nil, rosterCard)
    rosterScroll:SetPoint("TOPLEFT", rosterDivider, "BOTTOMLEFT", 0, -4)
    rosterScroll:SetPoint("BOTTOMRIGHT", rosterCard, "BOTTOMRIGHT", -10, 10)
    rosterScroll:EnableMouseWheel(true)
    rosterScroll:SetClipsChildren(true)
    rosterScroll:SetScript("OnMouseWheel", function(self, delta)
        local current = self:GetVerticalScroll()
        local maximum = self:GetVerticalScrollRange()
        self:SetVerticalScroll(math.max(0, math.min(maximum, current - (delta * ROSTER_ROW_HEIGHT))))
    end)

    local rosterScrollBar = CreateFrame("Frame", nil, rosterCard, "BackdropTemplate")
    rosterScrollBar:SetWidth(8)
    rosterScrollBar:SetPoint("TOPLEFT", rosterScroll, "TOPRIGHT", 1, 0)
    rosterScrollBar:SetPoint("BOTTOMLEFT", rosterScroll, "BOTTOMRIGHT", 1, 0)
    rosterScrollBar:SetBackdrop({
        bgFile = "Interface\\Buttons\\WHITE8X8",
        edgeFile = "Interface\\Buttons\\WHITE8X8",
        edgeSize = 1,
        insets = { left = 0, right = 0, top = 0, bottom = 0 },
    })
    rosterScrollBar:SetBackdropColor(0.035, 0.045, 0.055, 1)
    rosterScrollBar:SetBackdropBorderColor(unpack(ATA.UI.theme.colors.divider))
    rosterScrollBar:Hide()

    local rosterScrollThumb = CreateFrame("Button", nil, rosterScrollBar, "BackdropTemplate")
    rosterScrollThumb:SetWidth(6)
    rosterScrollThumb:SetBackdrop({
        bgFile = "Interface\\Buttons\\WHITE8X8",
        edgeFile = "Interface\\Buttons\\WHITE8X8",
        edgeSize = 1,
        insets = { left = 1, right = 1, top = 1, bottom = 1 },
    })
    rosterScrollThumb:SetBackdropColor(unpack(ATA.UI.theme.colors.goldDark))
    rosterScrollThumb:SetBackdropBorderColor(unpack(ATA.UI.theme.colors.gold))
    rosterScrollThumb:RegisterForDrag("LeftButton")

    local rosterContent = CreateFrame("Frame", nil, rosterScroll)
    rosterContent:SetSize(1, 1)
    rosterScroll:SetScrollChild(rosterContent)

    local function UpdateRosterContentWidth(width)
        rosterContent:SetWidth(math.max(1, width))
    end

    local function UpdateRosterScrollThumb()
        local viewportHeight = rosterScroll:GetHeight()
        local contentHeight = rosterContent:GetHeight()
        local scrollRange = rosterScroll:GetVerticalScrollRange()
        if viewportHeight <= 0 or contentHeight <= viewportHeight or scrollRange <= 0 then
            rosterScrollThumb:Hide()
            rosterScrollBar:Hide()
            return
        end

        rosterScrollBar:Show()
        rosterScrollThumb:Show()
        local trackHeight = rosterScrollBar:GetHeight()
        local thumbHeight = math.max(24, trackHeight * viewportHeight / contentHeight)
        local thumbTravel = math.max(0, trackHeight - thumbHeight)
        local scrollFraction = rosterScroll:GetVerticalScroll() / scrollRange
        rosterScrollThumb:SetHeight(thumbHeight)
        rosterScrollThumb:ClearAllPoints()
        rosterScrollThumb:SetPoint("TOP", rosterScrollBar, "TOP", 0, -thumbTravel * scrollFraction)
    end

    rosterScroll:SetScript("OnVerticalScroll", UpdateRosterScrollThumb)
    rosterScroll:SetScript("OnShow", UpdateRosterScrollThumb)
    rosterScroll:SetScript("OnSizeChanged", function(_, width)
        UpdateRosterContentWidth(width)
        UpdateRosterScrollThumb()
    end)
    rosterContent:SetScript("OnSizeChanged", UpdateRosterScrollThumb)
    UpdateRosterContentWidth(rosterScroll:GetWidth())

    rosterScrollThumb:SetScript("OnDragStart", function(self)
        self:SetScript("OnUpdate", function()
            local scale = rosterScrollBar:GetEffectiveScale()
            local cursorY = select(2, GetCursorPosition()) / scale
            local trackTop = rosterScrollBar:GetTop()
            local trackHeight = rosterScrollBar:GetHeight()
            local thumbHeight = self:GetHeight()
            local thumbTravel = trackHeight - thumbHeight
            local scrollRange = rosterScroll:GetVerticalScrollRange()
            if thumbTravel <= 0 or scrollRange <= 0 then
                return
            end

            local thumbOffset = math.max(0, math.min(thumbTravel, trackTop - cursorY - (thumbHeight / 2)))
            rosterScroll:SetVerticalScroll(scrollRange * thumbOffset / thumbTravel)
        end)
    end)
    rosterScrollThumb:SetScript("OnDragStop", function(self)
        self:SetScript("OnUpdate", nil)
    end)

    frame.characterNameText = characterNameText
    frame.characterBirthDateText = characterBirthDateText
    frame.characterIcon = characterIcon
    frame.realmText = realmText
    frame.factionIcon = factionIcon
    frame.classIcon = classIcon
    frame.classText = classText
    frame.levelText = levelText
    frame.scannedText = scannedText
    frame.rescanButton = rescanButton
    frame.expansionCards = expansionCards
    frame.rosterStats = rosterStats
    frame.rosterScroll = rosterScroll
    frame.rosterContent = rosterContent
    frame.rosterScrollBar = rosterScrollBar
    frame.rosterScrollThumb = rosterScrollThumb
    frame.updateRosterScrollThumb = UpdateRosterScrollThumb
    frame.rosterRows = {}
    frame.rosterDividers = {}
    frame:SetScript("OnShow", function(self)
        self:SetScript("OnUpdate", function(updateFrame)
            updateFrame:SetScript("OnUpdate", nil)
            UpdateExpansionScrollThumb()
            UpdateRosterScrollThumb()
        end)
    end)
    frame:Hide()
    return frame
end

function ATA:UpdateReport()
    if not reportFrame then
        return
    end

    local entries = GetCharacterEntries()
    local selectedEntry = GetSelectedCharacter(entries)
    local selectedKey = selectedEntry and selectedEntry.key
    local record = selectedEntry and selectedEntry.record
    local currentGUID = UnitGUID("player")
    local isCurrentCharacter = selectedKey ~= nil and selectedKey == currentGUID
    local characterName = record and record.name or (isCurrentCharacter and UnitName("player")) or "Unknown"
    local realm = record and record.realm or (isCurrentCharacter and GetRealmName()) or "Unknown"
    local race = record and record.race or (isCurrentCharacter and select(1, UnitRace("player")))
    local className = record and record.class or (isCurrentCharacter and select(1, UnitClass("player")))
    local classFile = record and record.classFile or (isCurrentCharacter and select(2, UnitClass("player")))
    local level = record and record.level or (isCurrentCharacter and UnitLevel("player"))
    local faction = record and record.faction or (isCurrentCharacter and UnitFactionGroup("player"))

    local trueMainMarker = ATA:IsTrueMain(selectedKey) and (" " .. TRUE_MAIN_ICON) or ""
    reportFrame.characterNameText:SetText(characterName .. trueMainMarker)
    reportFrame.characterNameText:SetTextColor(
        unpack(ATA:IsCharacterMain(selectedKey) and ATA.UI.theme.colors.gold or ATA.UI.theme.colors.text)
    )
    reportFrame.characterBirthDateText:SetText(
        record and record.level10Date
            and ("DOB: " .. date("%b %d, %Y", record.level10Date))
            or "DOB: Unknown"
    )
    reportFrame.realmText:SetText(realm or "Unknown")

    local classColor = classFile and RAID_CLASS_COLORS and RAID_CLASS_COLORS[classFile]
    reportFrame.classText:SetText(className or "--")
    local classIconCoords = classFile and CLASS_ICON_COORDS[classFile]
    if classIconCoords then
        reportFrame.classIcon:SetTexture("Interface\\GLUES\\CHARACTERCREATE\\UI-CHARACTERCREATE-CLASSES")
        reportFrame.classIcon:SetTexCoord(unpack(classIconCoords))
        reportFrame.classIcon:Show()
    else
        reportFrame.classIcon:Hide()
    end
    if classColor then
        reportFrame.classText:SetTextColor(classColor.r, classColor.g, classColor.b)
    else
        reportFrame.classText:SetTextColor(unpack(ATA.UI.theme.colors.text))
    end
    reportFrame.levelText:SetText(level and tostring(level) or "--")

    if isCurrentCharacter then
        reportFrame.characterIcon:SetTexCoord(0, 1, 0, 1)
        SetPortraitTexture(reportFrame.characterIcon, "player")
    elseif classFile and CLASS_ICON_COORDS[classFile] then
        reportFrame.characterIcon:SetTexture("Interface\\GLUES\\CHARACTERCREATE\\UI-CHARACTERCREATE-CLASSES")
        reportFrame.characterIcon:SetTexCoord(unpack(CLASS_ICON_COORDS[classFile]))
    else
        reportFrame.characterIcon:SetTexture("Interface\\Icons\\INV_Misc_QuestionMark")
        reportFrame.characterIcon:SetTexCoord(0, 1, 0, 1)
    end

    if faction == "Alliance" then
        reportFrame.factionIcon:SetTexture("Interface\\AddOns\\AltTrackingAssistant\\media\\Alliance.png")
        reportFrame.factionIcon:Show()
    elseif faction == "Horde" then
        reportFrame.factionIcon:SetTexture("Interface\\AddOns\\AltTrackingAssistant\\media\\Horde.png")
        reportFrame.factionIcon:Show()
    else
        reportFrame.factionIcon:Hide()
    end

    if record and record.lastScanned then
        reportFrame.scannedText:SetText("Last scanned: " .. date("%b %d, %Y %H:%M", record.lastScanned))
    elseif isCurrentCharacter then
        reportFrame.scannedText:SetText("Last scanned: Not scanned yet")
    else
        reportFrame.scannedText:SetText("Last scanned: No saved scan")
    end

    for expansionKey, card in pairs(reportFrame.expansionCards) do
        card.updateVisibility()
        local progress, completed, total = GetProgress(record, expansionKey)
        if progress then
            local percent = total > 0 and math.floor((completed / total) * 100 + 0.5) or 0
            card.progressText:SetText(percent .. "% Complete")
            card.progressBar:SetValue(percent / 100, unpack(card.progressColor))
        else
            card.progressText:SetText("Not scanned")
            card.progressBar:SetValue(0, unpack(card.progressColor))
        end

        for checkID, status in pairs(card.checkRows) do
            if status.type == "select" then
                local covenantID = progress and progress[checkID]
                if not covenantID
                    and isCurrentCharacter
                    and C_Covenants
                    and C_Covenants.GetActiveCovenantID
                then
                    covenantID = C_Covenants.GetActiveCovenantID()
                end
                local covenantName = "Select Covenant"
                local activeCovenantID = progress and progress.activeCovenantID
                if not activeCovenantID
                    and isCurrentCharacter
                    and C_Covenants
                    and C_Covenants.GetActiveCovenantID
                then
                    activeCovenantID = C_Covenants.GetActiveCovenantID()
                end
                local activeCovenant
                for _, covenant in ipairs(ATA.shadowlandsCovenants or {}) do
                    if covenant.id == covenantID then
                        covenantName = covenant.name
                    end
                    if covenant.id == activeCovenantID then
                        activeCovenant = covenant
                    end
                end
                status.button.label:SetText(covenantName)
                if activeCovenant then
                    status.activeIcon:SetTexture(activeCovenant.icon)
                    status.activeIcon:Show()
                    status.activeText:SetText(activeCovenant.name)
                    if ATA:IsArmorMain(selectedKey) then
                        status.activeText:SetFontObject(GameFontNormal)
                        status.activeText:SetTextColor(unpack(ATA.UI.theme.colors.gold))
                    else
                        status.activeText:SetFontObject(GameFontHighlight)
                        status.activeText:SetTextColor(unpack(activeCovenant.color))
                    end
                else
                    status.activeIcon:Hide()
                    status.activeText:SetText("--")
                    status.activeText:SetFontObject(GameFontHighlight)
                    status.activeText:SetTextColor(unpack(ATA.UI.theme.colors.mutedText))
                end
            elseif status.type == "count" then
                local value = progress and progress[checkID]
                status.value:SetText(
                    type(value) == "number" and (value .. "/" .. status.max) or ("--/" .. status.max)
                )
            elseif progress and progress[checkID] == true then
                status.checkmark:Show()
                status.unknown:Hide()
            elseif progress and progress[checkID] ~= nil then
                status.checkmark:Hide()
                status.unknown:Hide()
            else
                status.checkmark:Hide()
                status.unknown:Show()
            end
        end
    end

    reportFrame.rescanButton:SetEnabled(currentGUID ~= nil)

    local rosterCompleted = 0
    local rosterPossible = 0
    for _, entry in ipairs(entries) do
        for expansionKey in pairs(ATA.trackerDefinitions) do
            local expansionProgress, characterCompleted, characterTotal = GetProgress(entry.record, expansionKey)
            if expansionProgress then
                rosterCompleted = rosterCompleted + characterCompleted
                rosterPossible = rosterPossible + characterTotal
            end
        end
    end

    local averageText = rosterPossible > 0
        and (math.floor((rosterCompleted / rosterPossible) * 100 + 0.5) .. "% avg. complete")
        or "-- avg. complete"
    reportFrame.rosterStats:SetText(#entries .. " characters  ·  " .. averageText)

    local content = reportFrame.rosterContent
    local rows = reportFrame.rosterRows
    local dividers = reportFrame.rosterDividers
    local rosterContentHeight = 0
    local previousGroup
    for index, entry in ipairs(entries) do
        local classOrder = ROSTER_CLASS_ORDER[entry.classFile] or { group = 5, order = 99 }
        if previousGroup and classOrder.group ~= previousGroup then
            local dividerIndex = index - 1
            local divider = dividers[dividerIndex]
            if not divider then
                divider = content:CreateTexture(nil, "ARTWORK")
                divider:SetTexture("Interface\\Buttons\\WHITE8X8")
                divider:SetVertexColor(unpack(ATA.UI.theme.colors.gold))
                divider:SetHeight(1)
                dividers[dividerIndex] = divider
            end
            divider:ClearAllPoints()
            divider:SetPoint("TOPLEFT", content, "TOPLEFT", 4, -(rosterContentHeight + (ROSTER_GROUP_GAP / 2)))
            divider:SetPoint("RIGHT", content, "RIGHT", -4, 0)
            divider:Show()
            rosterContentHeight = rosterContentHeight + ROSTER_GROUP_GAP
        end
        previousGroup = classOrder.group

        local row = rows[index]
        if not row then
            row = CreateRosterRow(content)
            rows[index] = row
        end

        row.characterKey = entry.key
        row:ClearAllPoints()
        row:SetPoint("TOPLEFT", content, "TOPLEFT", 0, -rosterContentHeight)
        row:SetPoint("RIGHT", content, "RIGHT", 0, 0)
        local trueMainMarker = ATA:IsTrueMain(entry.key) and (" " .. TRUE_MAIN_ICON) or ""
        row.nameText:SetText(
            entry.name .. trueMainMarker .. " - " .. (entry.level and tostring(entry.level) or "--")
        )
        row.nameText:SetTextColor(
            unpack(ATA:IsCharacterMain(entry.key) and ATA.UI.theme.colors.gold or ATA.UI.theme.colors.text)
        )

        local classFile = entry.classFile
        local red, green, blue = GetClassColor(classFile)
        local characterCompleted = 0
        local characterPossible = 0
        for expansionKey in pairs(ATA.trackerDefinitions) do
            local expansionProgress, expansionCompleted, expansionTotal = GetProgress(entry.record, expansionKey)
            if expansionProgress then
                characterCompleted = characterCompleted + expansionCompleted
                characterPossible = characterPossible + expansionTotal
            end
        end

        if characterPossible > 0 then
            local percent = math.floor((characterCompleted / characterPossible) * 100 + 0.5)
            row.completionText:SetText(percent .. "%")
            row.progressBar:SetValue(percent / 100, red, green, blue)
        else
            row.completionText:SetText("--")
            row.progressBar:SetValue(0, red, green, blue)
        end

        if entry.key == currentGUID then
            row.avatar:SetTexCoord(0, 1, 0, 1)
            SetPortraitTexture(row.avatar, "player")
        elseif entry.faction == "Alliance" then
            row.avatar:SetTexture("Interface\\Icons\\Achievement_PVP_A_16")
            row.avatar:SetTexCoord(0, 1, 0, 1)
        elseif entry.faction == "Horde" then
            row.avatar:SetTexture("Interface\\Icons\\Achievement_PVP_H_16")
            row.avatar:SetTexCoord(0, 1, 0, 1)
        else
            row.avatar:SetTexture("Interface\\Icons\\INV_Misc_QuestionMark")
            row.avatar:SetTexCoord(0, 1, 0, 1)
        end

        row.completionText:SetTextColor(red, green, blue)

        if entry.key == selectedKey then
            row.background:SetVertexColor(0.28, 0.20, 0.34, 0.9)
        else
            row.background:SetVertexColor(0.08, 0.10, 0.13, 0.8)
        end
        row:Show()
        rosterContentHeight = rosterContentHeight + ROSTER_ROW_HEIGHT
    end

    for index = #entries + 1, #rows do
        rows[index]:Hide()
    end
    for index, divider in pairs(dividers) do
        if index >= #entries then
            divider:Hide()
        end
    end

    content:SetHeight(math.max(1, rosterContentHeight))
    reportFrame.rosterScroll:SetVerticalScroll(0)
    reportFrame.updateRosterScrollThumb()
end

function ATA:ToggleReport()
    if not reportFrame then
        reportFrame = CreateReportFrame()
    end

    if reportFrame:IsShown() then
        reportFrame:Hide()
    else
        self:UpdateReport()
        reportFrame:Show()
    end
end

SLASH_ALTTRACKINGASSISTANT1 = "/ata"
SLASH_ALTTRACKINGASSISTANT2 = "/alttrackingassistant"
SlashCmdList.ALTTRACKINGASSISTANT = function()
    ATA:ToggleReport()
end
