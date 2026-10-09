local _, ATA = ...

local MAX_NOTE_LENGTH = 1000
local MAX_TODO_LENGTH = 200
local PANEL_WIDTH = 650
local CONTENT_WIDTH = 610
local INPUT_HEIGHT = 90
local ENTRY_GAP = 10
local HEADER_HEIGHT = 22
local DAY_INDENT = 16
local NOTE_INDENT = 32
local TODO_MIN_HEIGHT = 24
local CHECKBOX_SIZE = 18

local function GetRecord(characterKey)
    return characterKey and ATA.db and ATA.db.characters[characterKey]
end

-- To-dos are stored per character as { id, text, done, created }.
function ATA:GetTodos(characterKey)
    local record = GetRecord(characterKey)
    local todos = record and record.todos or {}
    for _, todo in ipairs(todos) do
        if todo.done == nil then
            todo.done = todo.active == false
            todo.active = nil
        end
    end
    return todos
end

function ATA:HasPendingTodo(characterKey)
    for _, todo in ipairs(self:GetTodos(characterKey)) do
        if not todo.done then
            return true
        end
    end
    return false
end

function ATA:AddTodo(characterKey, text)
    local record = GetRecord(characterKey)
    if not record then
        return false, "Scan this character in game before adding to-dos."
    end

    text = strtrim(text or "")
    if text == "" then
        return false, "Enter a to-do first."
    end

    local now = time()
    record.todos = record.todos or {}
    record.todos[#record.todos + 1] = {
        id = now .. "-" .. math.random(100000, 999999),
        text = text:sub(1, MAX_TODO_LENGTH),
        done = false,
        created = now,
    }
    return true
end

function ATA:ToggleTodo(characterKey, todoId)
    for _, todo in ipairs(self:GetTodos(characterKey)) do
        if todo.id == todoId then
            todo.done = not todo.done
            return true
        end
    end
    return false
end

function ATA:DeleteTodo(characterKey, todoId)
    local record = GetRecord(characterKey)
    if not (record and record.todos and todoId) then
        return false
    end
    for index, todo in ipairs(record.todos) do
        if todo.id == todoId then
            table.remove(record.todos, index)
            return true
        end
    end
    return false
end

function ATA:GetNotes(characterKey)
    local record = GetRecord(characterKey)
    return record and record.notes or {}
end

function ATA:DeleteNote(characterKey, noteId)
    local record = GetRecord(characterKey)
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
    local record = GetRecord(characterKey)
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

local BOX_BACKDROP = {
    bgFile = "Interface\\Buttons\\WHITE8X8",
    edgeFile = "Interface\\Buttons\\WHITE8X8",
    edgeSize = 1,
    insets = { left = 1, right = 1, top = 1, bottom = 1 },
}

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

function ATA.CreateNotesPanel(parent, helpers)
    local colors = ATA.UI.theme.colors
    local panel = helpers.CreateCard(parent, PANEL_WIDTH, 1)
    panel.collapsed = {}

    local scroll = CreateFrame("ScrollFrame", nil, panel)
    scroll:SetPoint("TOPLEFT", panel, "TOPLEFT", 12, -12)
    scroll:SetPoint("BOTTOMRIGHT", panel, "BOTTOMRIGHT", -28, 12)
    scroll:SetClipsChildren(true)
    scroll:EnableMouseWheel(true)

    local content = CreateFrame("Frame", nil, scroll)
    content:SetSize(CONTENT_WIDTH, 1)
    scroll:SetScrollChild(content)

    -- Scrollbar for the whole page
    local scrollBar = CreateFrame("Frame", nil, panel, "BackdropTemplate")
    scrollBar:SetWidth(10)
    scrollBar:SetPoint("TOPRIGHT", panel, "TOPRIGHT", -10, -12)
    scrollBar:SetPoint("BOTTOMRIGHT", panel, "BOTTOMRIGHT", -10, 12)
    scrollBar:SetBackdrop(BOX_BACKDROP)
    scrollBar:SetBackdropColor(0.035, 0.045, 0.055, 1)
    scrollBar:SetBackdropBorderColor(unpack(colors.divider))
    scrollBar:Hide()

    local thumb = CreateFrame("Button", nil, scrollBar, "BackdropTemplate")
    thumb:SetWidth(8)
    thumb:SetBackdrop(BOX_BACKDROP)
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

    local function MakeDivider()
        local line = content:CreateTexture(nil, "ARTWORK")
        line:SetTexture("Interface\\Buttons\\WHITE8X8")
        line:SetVertexColor(unpack(colors.divider))
        line:SetHeight(1)
        return line
    end

    local function MakeBox(height)
        local box = CreateFrame("Frame", nil, content, "BackdropTemplate")
        box:SetHeight(height)
        box:SetBackdrop(BOX_BACKDROP)
        box:SetBackdropColor(0.035, 0.045, 0.055, 1)
        box:SetBackdropBorderColor(unpack(colors.divider))
        return box
    end

    local function Place(frame, y, leftInset, rightInset)
        frame:ClearAllPoints()
        frame:SetPoint("TOPLEFT", content, "TOPLEFT", leftInset or 0, -y)
        frame:SetPoint("TOPRIGHT", content, "TOPRIGHT", -(rightInset or 0), -y)
    end

    local statusColor = { 1, 0.35, 0.3, 1 }

    -- To-do section
    local todoTitle = content:CreateFontString(nil, "OVERLAY", "GameFontNormalLarge")
    todoTitle:SetText("TO-DO")
    todoTitle:SetTextColor(unpack(colors.gold))

    local subtitle = content:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
    subtitle:SetPoint("LEFT", todoTitle, "RIGHT", 10, -1)
    subtitle:SetTextColor(unpack(colors.mutedText))

    local todoAddButton = helpers.CreateThemedButton(content, "Add", 60, 24)
    local todoInputBox = MakeBox(24)
    local todoInput = CreateFrame("EditBox", nil, todoInputBox)
    todoInput:SetPoint("TOPLEFT", todoInputBox, "TOPLEFT", 8, 0)
    todoInput:SetPoint("BOTTOMRIGHT", todoInputBox, "BOTTOMRIGHT", -8, 0)
    todoInput:SetAutoFocus(false)
    todoInput:SetFontObject(ChatFontNormal)
    todoInput:SetTextColor(unpack(colors.text))
    todoInput:SetMaxLetters(MAX_TODO_LENGTH)
    todoInput:SetScript("OnEscapePressed", todoInput.ClearFocus)
    todoInputBox:EnableMouse(true)
    todoInputBox:SetScript("OnMouseDown", function()
        todoInput:SetFocus()
    end)

    local todoEmpty = content:CreateFontString(nil, "OVERLAY", "GameFontDisable")
    todoEmpty:SetText("No to-dos yet.")

    local todoRows = {}

    local function GetTodoRow(index)
        local row = todoRows[index]
        if row then
            return row
        end

        row = CreateFrame("Frame", nil, content)

        row.checkbox = CreateFrame("Button", nil, row, "BackdropTemplate")
        row.checkbox:SetSize(CHECKBOX_SIZE, CHECKBOX_SIZE)
        row.checkbox:SetPoint("TOPLEFT", row, "TOPLEFT", 2, -3)
        row.checkbox:SetBackdrop(BOX_BACKDROP)
        row.checkbox:SetBackdropColor(0.035, 0.045, 0.055, 1)
        row.checkbox:SetBackdropBorderColor(unpack(colors.goldDark))
        row.checkbox.check = row.checkbox:CreateTexture(nil, "OVERLAY")
        row.checkbox.check:SetPoint("CENTER", 0, 0)
        row.checkbox.check:SetSize(CHECKBOX_SIZE + 4, CHECKBOX_SIZE + 4)
        row.checkbox.check:SetTexture("Interface\\Buttons\\UI-CheckBox-Check")
        row.checkbox.check:SetVertexColor(unpack(colors.gold))
        row.checkbox:SetScript("OnEnter", function(self)
            self:SetBackdropBorderColor(unpack(colors.gold))
        end)
        row.checkbox:SetScript("OnLeave", function(self)
            self:SetBackdropBorderColor(unpack(colors.goldDark))
        end)
        row.checkbox:SetScript("OnClick", function(self)
            ATA:ToggleTodo(panel.characterKey, self.todoId)
            panel:Render()
        end)

        row.deleteButton = helpers.CreateThemedButton(row, "X", 20, 20)
        row.deleteButton:SetPoint("TOPRIGHT", row, "TOPRIGHT", -2, -2)
        row.deleteButton:SetScript("OnClick", function(self)
            ATA:DeleteTodo(panel.characterKey, self.todoId)
            panel:Render()
        end)

        row.text = row:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
        row.text:SetPoint("TOPLEFT", row.checkbox, "TOPRIGHT", 8, -2)
        row.text:SetWidth(CONTENT_WIDTH - CHECKBOX_SIZE - 8 - 2 - 34)
        row.text:SetJustifyH("LEFT")
        row.text:SetJustifyV("TOP")
        row.text:SetWordWrap(true)

        todoRows[index] = row
        return row
    end

    -- Notes input section
    local dividerOne = MakeDivider()
    local notesTitle = content:CreateFontString(nil, "OVERLAY", "GameFontNormalLarge")
    notesTitle:SetText("NOTES")
    notesTitle:SetTextColor(unpack(colors.gold))

    local inputBox = MakeBox(INPUT_HEIGHT)
    inputBox:SetClipsChildren(true)
    inputBox:EnableMouse(true)
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

    local submitButton = helpers.CreateThemedButton(content, "Submit", 90, 26)
    local status = content:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
    status:SetJustifyH("LEFT")

    local dividerTwo = MakeDivider()
    local historyTitle = content:CreateFontString(nil, "OVERLAY", "GameFontNormal")
    historyTitle:SetText("HISTORY")
    historyTitle:SetTextColor(unpack(colors.gold))

    local emptyText = content:CreateFontString(nil, "OVERLAY", "GameFontDisable")
    emptyText:SetText("No notes yet.")

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

    -- Lays out the whole page top to bottom so each section grows or shrinks with its content.
    function panel:Render()
        local y = 0

        todoTitle:ClearAllPoints()
        todoTitle:SetPoint("TOPLEFT", content, "TOPLEFT", 0, -y)
        y = y + 28

        todoAddButton:ClearAllPoints()
        todoAddButton:SetPoint("TOPRIGHT", content, "TOPRIGHT", 0, -y)
        Place(todoInputBox, y, 0, 66)
        y = y + 32

        local todos = ATA:GetTodos(self.characterKey)
        todoEmpty:ClearAllPoints()
        todoEmpty:SetPoint("TOPLEFT", content, "TOPLEFT", 2, -y)
        todoEmpty:SetShown(#todos == 0)
        if #todos == 0 then
            y = y + 22
        end
        for index, todo in ipairs(todos) do
            local row = GetTodoRow(index)
            row.checkbox.todoId = todo.id
            row.checkbox.check:SetShown(todo.done)
            row.deleteButton.todoId = todo.id
            row.text:SetText(todo.text or "")
            row.text:SetTextColor(unpack(todo.done and colors.mutedText or colors.text))
            local height = math.max(TODO_MIN_HEIGHT, row.text:GetStringHeight() + 8)
            row:SetHeight(height)
            Place(row, y)
            row:Show()
            y = y + height + 2
        end
        for index = #todos + 1, #todoRows do
            todoRows[index]:Hide()
        end
        y = y + 8

        Place(dividerOne, y)
        y = y + 10
        notesTitle:ClearAllPoints()
        notesTitle:SetPoint("TOPLEFT", content, "TOPLEFT", 0, -y)
        y = y + 28
        Place(inputBox, y)
        y = y + INPUT_HEIGHT + 8
        submitButton:ClearAllPoints()
        submitButton:SetPoint("TOPRIGHT", content, "TOPRIGHT", 0, -y)
        status:ClearAllPoints()
        status:SetPoint("TOPLEFT", content, "TOPLEFT", 0, -(y + 7))
        status:SetPoint("RIGHT", submitButton, "LEFT", -10, 0)
        y = y + 36

        Place(dividerTwo, y)
        y = y + 10
        historyTitle:ClearAllPoints()
        historyTitle:SetPoint("TOPLEFT", content, "TOPLEFT", 0, -y)
        y = y + 26

        local notes = ATA:GetNotes(self.characterKey)
        emptyText:ClearAllPoints()
        emptyText:SetPoint("TOPLEFT", content, "TOPLEFT", 0, -y)
        emptyText:SetShown(#notes == 0)
        if #notes == 0 then
            y = y + 22
        end

        local usedYears, usedDays, usedNotes = 0, 0, 0
        for _, year in ipairs(GroupNotes(notes)) do
            usedYears = usedYears + 1
            local yearKey = "y" .. year.key
            local yearRow = GetHeaderRow(yearRows, usedYears, 0, colors.gold)
            yearRow.groupKey = yearKey
            yearRow.label:SetText((self.collapsed[yearKey] and "[+] " or "[-] ") .. year.key .. "  (" .. year.count .. ")")
            Place(yearRow, y)
            yearRow:Show()
            y = y + HEADER_HEIGHT + 4

            if not self.collapsed[yearKey] then
                for _, day in ipairs(year.days) do
                    usedDays = usedDays + 1
                    local dayKey = "d" .. day.key
                    local dayRow = GetHeaderRow(dayRows, usedDays, DAY_INDENT, colors.text)
                    dayRow.groupKey = dayKey
                    dayRow.label:SetText((self.collapsed[dayKey] and "[+] " or "[-] ") .. day.label .. "  (" .. #day.notes .. ")")
                    Place(dayRow, y)
                    dayRow:Show()
                    y = y + HEADER_HEIGHT + 4

                    if not self.collapsed[dayKey] then
                        for _, note in ipairs(day.notes) do
                            usedNotes = usedNotes + 1
                            local row = GetNoteRow(usedNotes)
                            row.timeText:SetText(note.created and date("%I:%M %p", note.created) or "")
                            row.bodyText:SetText(note.text or "")
                            row.deleteButton.noteId = note.id
                            local height = row.timeText:GetStringHeight() + 2 + row.bodyText:GetStringHeight()
                            row:SetHeight(math.max(height, 22))
                            Place(row, y)
                            row:Show()
                            y = y + row:GetHeight() + ENTRY_GAP
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

        content:SetHeight(y + 8)
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
            todoInput:SetText("")
            todoInput:ClearFocus()
            SetStatus("")
            scroll:SetVerticalScroll(0)
        end

        subtitle:SetText(characterName and string.upper(characterName) or "")
        for _, button in ipairs({ submitButton, todoAddButton }) do
            button:SetEnabled(hasRecord and true or false)
            button:SetAlpha(hasRecord and 1 or 0.4)
        end
        if not hasRecord then
            SetStatus("Scan this character in game before adding notes or to-dos.")
        end
        self:Render()
    end

    local function AddTodoFromInput()
        local success, message = ATA:AddTodo(panel.characterKey, todoInput:GetText())
        if not success then
            SetStatus(message, statusColor)
            return
        end
        todoInput:SetText("")
        panel:Render()
    end
    todoAddButton:SetScript("OnClick", AddTodoFromInput)
    todoInput:SetScript("OnEnterPressed", AddTodoFromInput)

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
            SetStatus(message, statusColor)
            return
        end

        input:SetText("")
        input:ClearFocus()
        panel:Render()
        SetStatus("Note saved.", colors.completed)
    end)

    return panel
end
