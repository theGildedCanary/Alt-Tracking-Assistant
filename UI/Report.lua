local _, ATA = ...

local reportFrame
local ROW_HEIGHT = 30
local ROSTER_ROW_HEIGHT = 42
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
        }
        seen[key] = true
    end

    local currentGUID = UnitGUID("player")
    if currentGUID and not seen[currentGUID] then
        entries[#entries + 1] = {
            key = currentGUID,
            label = GetCharacterLabel({
                name = UnitName("player"),
                realm = GetRealmName(),
            }),
        }
    end

    table.sort(entries, function(left, right)
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
    local progress = record and record.progress and record.progress[expansionKey]
    if not progress then
        return nil, 0, #definition.checks
    end

    local completed = 0
    local total = #definition.checks
    for _, check in ipairs(definition.checks) do
        if progress[check.id] == true then
            completed = completed + 1
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
    sectionTitle:SetPoint("TOPLEFT", sectionIcon, "TOPRIGHT", 8, -11)
    sectionTitle:SetText(options.title)
    local titleFont, titleSize, titleFlags = sectionTitle:GetFont()
    sectionTitle:SetFont(titleFont, titleSize + 4, titleFlags)
    sectionTitle:SetTextColor(unpack(options.titleColor))

    local sectionSubtitle = sectionHeader:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
    sectionSubtitle:SetPoint("TOPLEFT", sectionTitle, "BOTTOMLEFT", 0, -1)
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
    for column = 1, columnCount - 1 do
        local divider = sectionBody:CreateTexture(nil, "BACKGROUND")
        divider:SetTexture("Interface\\Buttons\\WHITE8X8")
        divider:SetVertexColor(unpack(ATA.UI.theme.colors.divider))
        divider:SetWidth(1)
        divider:SetPoint("TOPLEFT", sectionBody, "TOPLEFT", column * columnWidth, -6)
        divider:SetPoint("BOTTOMLEFT", sectionBody, "BOTTOMLEFT", column * columnWidth, 6)
    end

    for index, check in ipairs(checks) do
        local column = ((index - 1) % columnCount) + 1
        local row = math.floor((index - 1) / columnCount)
        local rowTop = -12 - (row * ROW_HEIGHT)
        local columnLeft = (column - 1) * columnWidth

        local label = sectionBody:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
        label:SetPoint("TOPLEFT", sectionBody, "TOPLEFT", columnLeft + 16, rowTop)
        label:SetWidth(columnWidth - 58)
        label:SetJustifyH("LEFT")
        label:SetText(check.label)

        local status = CreateFrame("Frame", nil, sectionBody, "BackdropTemplate")
        status:SetSize(18, 18)
        status:SetPoint("TOPLEFT", sectionBody, "TOPLEFT", (column * columnWidth) - 32, rowTop - 3)
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
        checkRows[check.id] = { checkmark = checkmark, unknown = unknown }
    end

    sectionBody:SetHeight(20 + (math.ceil(#checks / columnCount) * ROW_HEIGHT))
    local collapsedCardHeight = 62
    local expandedCardHeight = collapsedCardHeight + sectionBody:GetHeight()
    mainCard:SetHeight(expandedCardHeight)

    local isExpanded = true
    sectionHeader:SetScript("OnClick", function()
        isExpanded = not isExpanded
        sectionBody:SetShown(isExpanded)
        collapseIcon:SetTexture(isExpanded and "Interface\\Buttons\\UI-MinusButton-Up" or "Interface\\Buttons\\UI-PlusButton-Up")
        mainCard:SetHeight(isExpanded and expandedCardHeight or collapsedCardHeight)
        if options.onHeightChanged then
            options.onHeightChanged()
        end
    end)

    return {
        card = mainCard,
        checkRows = checkRows,
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
    name:SetPoint("RIGHT", row, "RIGHT", -40, 0)
    name:SetJustifyH("LEFT")

    local completion = row:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
    completion:SetPoint("TOPRIGHT", row, "TOPRIGHT", -7, -4)
    completion:SetJustifyH("RIGHT")

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

    local characterCaption = characterCard:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
    characterCaption:SetPoint("TOPLEFT", characterCard, "TOPLEFT", 90, -9)
    characterCaption:SetText("SELECT CHARACTER")
    characterCaption:SetTextColor(unpack(ATA.UI.theme.colors.mutedText))

    local characterDropdown = CreateThemedButton(characterCard, "Select Character", 200, 26)
    characterDropdown:SetPoint("TOPLEFT", characterCaption, "BOTTOMLEFT", 0, -5)
    characterDropdown.label:SetJustifyH("LEFT")
    characterDropdown.label:ClearAllPoints()
    characterDropdown.label:SetPoint("LEFT", characterDropdown, "LEFT", 9, 0)
    characterDropdown.label:SetPoint("RIGHT", characterDropdown, "RIGHT", -24, 0)

    local dropdownArrow = characterDropdown:CreateFontString(nil, "OVERLAY", "GameFontNormal")
    dropdownArrow:SetPoint("RIGHT", characterDropdown, "RIGHT", -8, 0)
    dropdownArrow:SetText("v")
    dropdownArrow:SetTextColor(unpack(ATA.UI.theme.colors.gold))

    local characterMenu = CreateCard(characterCard, 200, 30)
    characterMenu:SetFrameStrata("DIALOG")
    characterMenu:SetFrameLevel(characterDropdown:GetFrameLevel() + 10)
    characterMenu:SetPoint("TOPLEFT", characterDropdown, "BOTTOMLEFT", 0, -2)
    characterMenu:Hide()
    characterMenu.rows = {}

    characterDropdown:SetScript("OnClick", function()
        if characterMenu:IsShown() then
            characterMenu:Hide()
            return
        end

        local entries = GetCharacterEntries()
        local menuHeight = math.max(28, #entries * 28 + 4)
        characterMenu:SetHeight(menuHeight)
        for index, entry in ipairs(entries) do
            local option = characterMenu.rows[index]
            if not option then
                option = CreateThemedButton(characterMenu, "", 190, 26)
                characterMenu.rows[index] = option
            end
            option:ClearAllPoints()
            option:SetPoint("TOPLEFT", characterMenu, "TOPLEFT", 4, -((index - 1) * 28) - 3)
            option:SetPoint("RIGHT", characterMenu, "RIGHT", -4, 0)
            option.label:SetText(entry.label)
            option.characterKey = entry.key
            option:SetScript("OnClick", function(self)
                ATA.selectedCharacterKey = self.characterKey
                characterMenu:Hide()
                ATA:UpdateReport()
            end)
            option:Show()
        end
        for index = #entries + 1, #characterMenu.rows do
            characterMenu.rows[index]:Hide()
        end
        characterMenu:Show()
    end)

    local function AddCharacterField(labelText, x, width)
        local label = characterCard:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
        label:SetPoint("TOPLEFT", characterCard, "TOPLEFT", x, -30)
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
    classText:SetWidth(91)
    classText:SetJustifyH("LEFT")

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
        progressColor = { 236 / 255, 143 / 255, 248 / 255 },
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
            progressColor = { 248 / 255, 149 / 255, 4 / 255 },
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
            progressColor = { 32 / 255, 252 / 255, 250 / 255 },
            onHeightChanged = UpdateExpansionContentHeight,
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
    rosterScroll:SetScript("OnMouseWheel", function(self, delta)
        local current = self:GetVerticalScroll()
        local maximum = self:GetVerticalScrollRange()
        self:SetVerticalScroll(math.max(0, math.min(maximum, current - (delta * ROSTER_ROW_HEIGHT))))
    end)

    local rosterContent = CreateFrame("Frame", nil, rosterScroll)
    rosterContent:SetSize(214, 1)
    rosterScroll:SetScrollChild(rosterContent)

    frame.characterDropdown = characterDropdown
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
    frame.rosterRows = {}
    frame.characterMenu = characterMenu
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

    reportFrame.characterDropdown.label:SetText(characterName)
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
            if progress and progress[checkID] == true then
                status.checkmark:Show()
                status.unknown:Hide()
            elseif progress then
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
    for index, entry in ipairs(entries) do
        local row = rows[index]
        if not row then
            row = CreateRosterRow(content)
            rows[index] = row
        end

        row.characterKey = entry.key
        row:ClearAllPoints()
        row:SetPoint("TOPLEFT", content, "TOPLEFT", 0, -((index - 1) * ROSTER_ROW_HEIGHT))
        row:SetPoint("RIGHT", content, "RIGHT", 0, 0)
        row.nameText:SetText(entry.record and entry.record.name or entry.label)

        local classFile = entry.record and entry.record.classFile
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

        local classIconCoords = classFile and CLASS_ICON_COORDS[classFile]
        if entry.key == currentGUID then
            SetPortraitTexture(row.avatar, "player")
        elseif classIconCoords then
            row.avatar:SetTexture("Interface\\GLUES\\CHARACTERCREATE\\UI-CHARACTERCREATE-CLASSES")
            row.avatar:SetTexCoord(unpack(classIconCoords))
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
    end

    for index = #entries + 1, #rows do
        rows[index]:Hide()
    end

    content:SetHeight(math.max(1, #entries * ROSTER_ROW_HEIGHT))
    reportFrame.rosterScroll:SetVerticalScroll(0)
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
