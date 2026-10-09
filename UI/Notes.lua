local _, ATA = ...

local MAX_NOTE_LENGTH = 1000
local PANEL_WIDTH = 650
local INPUT_HEIGHT = 96
local ENTRY_GAP = 10
local CONTENT_WIDTH = 612
local HEADER_HEIGHT = 22
local DAY_INDENT = 16
local NOTE_INDENT = 32

function ATA:GetNotes(characterKey)
    local record = characterKey and self.db and self.db.characters[characterKey]
    return record and record.notes or {}
end

function ATA:DeleteNote(characterKey, noteId)
    local record = characterKey and self.db and self.db.characters[characterKey]
    if not (record and record.notes and noteId) then
        return false
    end
    for index, note in ipairs(record.notes) do
        if note.id == noteId then
            table.remove(record.notes, index)
            return true
        end
    end
    return false
end

-- Notes are stored per character as { id, text, created } so a companion app can merge them by id.
function ATA:AddNote(characterKey, text)
    local record = characterKey and self.db and self.db.characters[characterKey]
    if not record then
        return false, "Scan this character in game before adding notes."
    end

    text = strtrim(text or "")
    if text == "" then
        return false, "Enter a note first."
    end
    if #text > MAX_NOTE_LENGTH then
        return false, "Notes are limited to " .. MAX_NOTE_LENGTH .. " characters."
    end

    local now = time()
    record.notes = record.notes or {}
    record.notes[#record.notes + 1] = {
        id = now .. "-" .. math.random(100000, 999999),
        text = text,
        created = now,
    }
    return true
end

function ATA.CreateNotesPanel(parent, helpers)
    local colors = ATA.UI.theme.colors
    local panel = helpers.CreateCard(parent, PANEL_WIDTH, 1)

    local title = panel:CreateFontString(nil, "OVERLAY", "GameFontNormalLarge")
    title:SetPoint("TOPLEFT", panel, "TOPLEFT", 12, -12)
    title:SetText("NOTES")
    title:SetTextColor(unpack(colors.gold))

    local subtitle = panel:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
    subtitle:SetPoint("TOPLEFT", title, "BOTTOMLEFT", 0, -3)
    subtitle:SetTextColor(unpack(colors.mutedText))

    local inputBox = CreateFrame("Frame", nil, panel, "BackdropTemplate")
    inputBox:SetPoint("TOPLEFT", panel, "TOPLEFT", 12, -58)
    inputBox:SetPoint("RIGHT", panel, "RIGHT", -12, 0)
    inputBox:SetHeight(INPUT_HEIGHT)
    inputBox:SetClipsChildren(true)
    inputBox:EnableMouse(true)
    inputBox:SetBackdrop({
        bgFile = "Interface\\Buttons\\WHITE8X8",
        edgeFile = "Interface\\Buttons\\WHITE8X8",
        edgeSize = 1,
        insets = { left = 1, right = 1, top = 1, bottom = 1 },
    })
    inputBox:SetBackdropColor(0.035, 0.045, 0.055, 1)
    inputBox:SetBackdropBorderColor(unpack(colors.divider))

    local input = CreateFrame("EditBox", nil, inputBox)
    input:SetPoint("TOPLEFT", inputBox, "TOPLEFT", 8, -8)
    input:SetPoint("BOTTOMRIGHT", inputBox, "BOTTOMRIGHT", -8, 8)
    input:SetMultiLine(true)
    input:SetAutoFocus(false)
    input:SetFontObject(ChatFontNormal)
    input:SetTextColor(unpack(colors.text))
    input:SetMaxLetters(MAX_NOTE_LENGTH)
    input:SetScript("OnEscapePressed", input.ClearFocus)
    inputBox:SetScript("OnMouseDown", function()
        input:SetFocus()
    end)

    local submitButton = helpers.CreateThemedButton(panel, "Submit", 90, 26)
    submitButton:SetPoint("TOPRIGHT", inputBox, "BOTTOMRIGHT", 0, -8)

    local status = panel:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
    status:SetPoint("RIGHT", submitButton, "LEFT", -10, 0)
    status:SetPoint("LEFT", panel, "LEFT", 12, 0)
    status:SetJustifyH("RIGHT")

    local divider = panel:CreateTexture(nil, "ARTWORK")
    divider:SetTexture("Interface\\Buttons\\WHITE8X8")
    divider:SetVertexColor(unpack(colors.divider))
    divider:SetHeight(1)
    divider:SetPoint("TOPLEFT", inputBox, "BOTTOMLEFT", 0, -42)
    divider:SetPoint("RIGHT", panel, "RIGHT", -12, 0)

    local historyTitle = panel:CreateFontString(nil, "OVERLAY", "GameFontNormal")
    historyTitle:SetPoint("TOPLEFT", divider, "BOTTOMLEFT", 0, -8)
    historyTitle:SetText("HISTORY")
    historyTitle:SetTextColor(unpack(colors.gold))

    local scroll = CreateFrame("ScrollFrame", nil, panel)
    scroll:SetPoint("TOPLEFT", historyTitle, "BOTTOMLEFT", 0, -8)
    scroll:SetPoint("BOTTOMRIGHT", panel, "BOTTOMRIGHT", -26, 12)
    scroll:SetClipsChildren(true)
    scroll:EnableMouseWheel(true)

    local content = CreateFrame("Frame", nil, scroll)
    content:SetSize(CONTENT_WIDTH, 1)
    scroll:SetScrollChild(content)

    local scrollBar = CreateFrame("Frame", nil, panel, "BackdropTemplate")
    scrollBar:SetWidth(10)
    scrollBar:SetPoint("TOPLEFT", scroll, "TOPRIGHT", 4, 0)
    scrollBar:SetPoint("BOTTOMLEFT", scroll, "BOTTOMRIGHT", 4, 0)
    scrollBar:SetBackdrop({
        bgFile = "Interface\\Buttons\\WHITE8X8",
        edgeFile = "Interface\\Buttons\\WHITE8X8",
        edgeSize = 1,
        insets = { left = 1, right = 1, top = 1, bottom = 1 },
    })
    scrollBar:SetBackdropColor(0.035, 0.045, 0.055, 1)
    scrollBar:SetBackdropBorderColor(unpack(colors.divider))
    scrollBar:Hide()

    local thumb = CreateFrame("Button", nil, scrollBar, "BackdropTemplate")
    thumb:SetWidth(8)
    thumb:SetBackdrop({
        bgFile = "Interface\\Buttons\\WHITE8X8",
        edgeFile = "Interface\\Buttons\\WHITE8X8",
        edgeSize = 1,
        insets = { left = 1, right = 1, top = 1, bottom = 1 },
    })
    thumb:SetBackdropColor(unpack(colors.goldDark))
    thumb:SetBackdropBorderColor(unpack(colors.gold))
    thumb:RegisterForDrag("LeftButton")

    local function UpdateThumb()
        local range = scroll:GetVerticalScrollRange()
        local viewport = scroll:GetHeight()
        if range <= 0 or viewport <= 0 then
            scrollBar:Hide()
            return
        end
        scrollBar:Show()
        local track = scrollBar:GetHeight()
        local thumbHeight = math.max(24, track * viewport / (viewport + range))
        thumb:SetHeight(thumbHeight)
        thumb:ClearAllPoints()
        thumb:SetPoint("TOP", scrollBar, "TOP", 0, -(track - thumbHeight) * scroll:GetVerticalScroll() / range)
    end

    scroll:SetScript("OnVerticalScroll", UpdateThumb)
    scroll:SetScript("OnScrollRangeChanged", UpdateThumb)
    scroll:SetScript("OnSizeChanged", UpdateThumb)
    scroll:SetScript("OnMouseWheel", function(self, delta)
        local target = self:GetVerticalScroll() - delta * 40
        self:SetVerticalScroll(math.max(0, math.min(self:GetVerticalScrollRange(), target)))
    end)
    thumb:SetScript("OnDragStart", function(self)
        self:SetScript("OnUpdate", function()
            local scale = scrollBar:GetEffectiveScale()
            local cursorY = select(2, GetCursorPosition()) / scale
            local travel = scrollBar:GetHeight() - self:GetHeight()
            local range = scroll:GetVerticalScrollRange()
            if travel <= 0 or range <= 0 then
                return
            end
            local offset = math.max(0, math.min(travel, scrollBar:GetTop() - cursorY - self:GetHeight() / 2))
            scroll:SetVerticalScroll(range * offset / travel)
        end)
    end)
    thumb:SetScript("OnDragStop", function(self)
        self:SetScript("OnUpdate", nil)
    end)

    local emptyText = content:CreateFontString(nil, "OVERLAY", "GameFontDisable")
    emptyText:SetPoint("TOPLEFT", content, "TOPLEFT", 0, 0)
    emptyText:SetText("No notes yet.")

    panel.collapsed = {}
    local yearRows, dayRows, noteRows = {}, {}, {}

    local function SetStatus(text, color)
        status:SetText(text or "")
        status:SetTextColor(unpack(color or colors.mutedText))
    end

    local function GetHeaderRow(pool, index, indent, color)
        local row = pool[index]
        if row then
            return row
        end
        row = CreateFrame("Button", nil, content)
        row:SetHeight(HEADER_HEIGHT)
        row.label = row:CreateFontString(nil, "OVERLAY", "GameFontNormal")
        row.label:SetPoint("LEFT", row, "LEFT", indent, 0)
        row.label:SetTextColor(unpack(color))
        row.line = row:CreateTexture(nil, "ARTWORK")
        row.line:SetTexture("Interface\\Buttons\\WHITE8X8")
        row.line:SetVertexColor(unpack(colors.divider))
        row.line:SetHeight(1)
        row.line:SetPoint("BOTTOMLEFT", row, "BOTTOMLEFT", indent, 0)
        row.line:SetPoint("BOTTOMRIGHT", row, "BOTTOMRIGHT")
        row:SetScript("OnClick", function(self)
            panel.collapsed[self.groupKey] = not panel.collapsed[self.groupKey]
            panel:Render()
        end)
        pool[index] = row
        return row
    end

    local function GetNoteRow(index)
        local row = noteRows[index]
        if row then
            return row
        end
        row = CreateFrame("Frame", nil, content)
        row.timeText = row:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
        row.timeText:SetPoint("TOPLEFT", row, "TOPLEFT", NOTE_INDENT, 0)
        row.timeText:SetTextColor(unpack(colors.mutedText))
        row.bodyText = row:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
        row.bodyText:SetPoint("TOPLEFT", row.timeText, "BOTTOMLEFT", 0, -2)
        row.bodyText:SetWidth(CONTENT_WIDTH - NOTE_INDENT - 30)
        row.bodyText:SetJustifyH("LEFT")
        row.bodyText:SetJustifyV("TOP")
        row.bodyText:SetWordWrap(true)
        row.bodyText:SetTextColor(unpack(colors.text))
        row.deleteButton = helpers.CreateThemedButton(row, "X", 20, 20)
        row.deleteButton:SetPoint("TOPRIGHT", row, "TOPRIGHT", -2, 0)
        row.deleteButton:SetScript("OnClick", function(self)
            panel.pendingDeleteId = self.noteId
            StaticPopup_Show("ATA_DELETE_NOTE")
        end)
        noteRows[index] = row
        return row
    end

    local function GroupNotes(notes)
        local sorted = {}
        for _, note in ipairs(notes) do
            sorted[#sorted + 1] = note
        end
        table.sort(sorted, function(a, b)
            return (a.created or 0) > (b.created or 0)
        end)

        local years = {}
        for _, note in ipairs(sorted) do
            local created = note.created or 0
            local yearKey = date("%Y", created)
            local dayKey = date("%Y-%m-%d", created)
            local year = years[#years]
            if not year or year.key ~= yearKey then
                year = { key = yearKey, days = {}, count = 0 }
                years[#years + 1] = year
            end
            local day = year.days[#year.days]
            if not day or day.key ~= dayKey then
                day = { key = dayKey, label = date("%A, %b %d", created), notes = {} }
                year.days[#year.days + 1] = day
            end
            day.notes[#day.notes + 1] = note
            year.count = year.count + 1
        end
        return years
    end

    function panel:Render()
        local notes = ATA:GetNotes(self.characterKey)
        emptyText:SetShown(#notes == 0)

        local usedYears, usedDays, usedNotes = 0, 0, 0
        local offset = 0

        for _, year in ipairs(GroupNotes(notes)) do
            usedYears = usedYears + 1
            local yearKey = "y" .. year.key
            local yearRow = GetHeaderRow(yearRows, usedYears, 0, colors.gold)
            yearRow.groupKey = yearKey
            yearRow.label:SetText((self.collapsed[yearKey] and "[+] " or "[-] ") .. year.key .. "  (" .. year.count .. ")")
            yearRow:ClearAllPoints()
            yearRow:SetPoint("TOPLEFT", content, "TOPLEFT", 0, -offset)
            yearRow:SetPoint("RIGHT", content, "RIGHT")
            yearRow:Show()
            offset = offset + HEADER_HEIGHT + 4

            if not self.collapsed[yearKey] then
                for _, day in ipairs(year.days) do
                    usedDays = usedDays + 1
                    local dayKey = "d" .. day.key
                    local dayRow = GetHeaderRow(dayRows, usedDays, DAY_INDENT, colors.text)
                    dayRow.groupKey = dayKey
                    dayRow.label:SetText((self.collapsed[dayKey] and "[+] " or "[-] ") .. day.label .. "  (" .. #day.notes .. ")")
                    dayRow:ClearAllPoints()
                    dayRow:SetPoint("TOPLEFT", content, "TOPLEFT", 0, -offset)
                    dayRow:SetPoint("RIGHT", content, "RIGHT")
                    dayRow:Show()
                    offset = offset + HEADER_HEIGHT + 4

                    if not self.collapsed[dayKey] then
                        for _, note in ipairs(day.notes) do
                            usedNotes = usedNotes + 1
                            local row = GetNoteRow(usedNotes)
                            row.timeText:SetText(note.created and date("%I:%M %p", note.created) or "")
                            row.bodyText:SetText(note.text or "")
                            row.deleteButton.noteId = note.id
                            local height = row.timeText:GetStringHeight() + 2 + row.bodyText:GetStringHeight()
                            row:SetSize(CONTENT_WIDTH, math.max(height, 20))
                            row:ClearAllPoints()
                            row:SetPoint("TOPLEFT", content, "TOPLEFT", 0, -offset)
                            row:Show()
                            offset = offset + row:GetHeight() + ENTRY_GAP
                        end
                    end
                end
            end
        end

        for index = usedYears + 1, #yearRows do
            yearRows[index]:Hide()
        end
        for index = usedDays + 1, #dayRows do
            dayRows[index]:Hide()
        end
        for index = usedNotes + 1, #noteRows do
            noteRows[index]:Hide()
        end

        content:SetHeight(math.max(1, offset))
        local range = scroll:GetVerticalScrollRange()
        if scroll:GetVerticalScroll() > range then
            scroll:SetVerticalScroll(range)
        end
        UpdateThumb()
    end

    function panel:Refresh(characterKey, characterName, hasRecord)
        if characterKey ~= self.characterKey then
            self.characterKey = characterKey
            self.collapsed = {}
            input:SetText("")
            input:ClearFocus()
            SetStatus("")
            scroll:SetVerticalScroll(0)
        end

        subtitle:SetText(characterName and string.upper(characterName) or "")
        submitButton:SetEnabled(hasRecord and true or false)
        submitButton:SetAlpha(hasRecord and 1 or 0.4)
        if not hasRecord then
            SetStatus("Scan this character in game before adding notes.")
        end
        self:Render()
    end

    StaticPopupDialogs["ATA_DELETE_NOTE"] = {
        text = "Delete this note? This cannot be undone.",
        button1 = YES,
        button2 = NO,
        timeout = 0,
        whileDead = true,
        hideOnEscape = true,
        OnAccept = function()
            if ATA:DeleteNote(panel.characterKey, panel.pendingDeleteId) then
                panel:Render()
                SetStatus("Note deleted.")
            end
        end,
    }
    submitButton:SetScript("OnClick", function()
        local success, message = ATA:AddNote(panel.characterKey, input:GetText())
        if not success then
            SetStatus(message, { 1, 0.35, 0.3, 1 })
            return
        end

        input:SetText("")
        input:ClearFocus()
        local record = ATA.db.characters[panel.characterKey]
        panel:Refresh(panel.characterKey, record and record.name, true)
        SetStatus("Note saved.", colors.completed)
    end)

    return panel
end
