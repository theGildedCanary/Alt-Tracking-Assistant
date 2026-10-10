local _, ATA = ...

function ATA.CreateProfessionsPanel(parent, helpers)
    local panel = helpers.CreateCard(parent, 650, 1)
    local scroll = CreateFrame("ScrollFrame", nil, panel)
    scroll:SetPoint("TOPLEFT", 8, -8)
    scroll:SetPoint("BOTTOMRIGHT", -28, 8)
    scroll:SetClipsChildren(true)
    scroll:EnableMouseWheel(true)
    local content = CreateFrame("Frame", nil, scroll)
    content:SetSize(610, 1)
    scroll:SetScrollChild(content)
    local expanded, sections = {}, {}
    local colors = ATA.UI.theme.colors
    local track, UpdateScroll = ATA.UI.CreateBlizzardScrollBar(
        panel, scroll, "AltTrackingAssistantProfessionsScrollBar", 34)
    track:SetPoint("TOPRIGHT", panel, "TOPRIGHT", -8, -24)
    track:SetPoint("BOTTOMRIGHT", panel, "BOTTOMRIGHT", -8, 24)
    scroll:HookScript("OnSizeChanged", function()
        content:SetWidth(math.max(1, scroll:GetWidth()))
    end)
    content:HookScript("OnSizeChanged", UpdateScroll)

    for index, definition in ipairs(ATA.professionSlots) do
        local section = { rows = {} }
        section.header = helpers.CreateThemedButton(content, definition.label, 610, 38)
        section.header.label:SetJustifyH("LEFT")
        section.header.label:ClearAllPoints()
        section.header.label:SetPoint("LEFT", 42, 0)
        section.header.label:SetPoint("RIGHT", -12, 0)
        section.icon = section.header:CreateTexture(nil, "ARTWORK")
        section.icon:SetSize(26, 26)
        section.icon:SetPoint("LEFT", 8, 0)
        section.header:SetScript("OnClick", function()
            if not panel.characterKey then return end
            local state = expanded[panel.characterKey] or {}
            expanded[panel.characterKey] = state
            state[definition.key] = not state[definition.key]
            panel:Refresh(panel.characterKey, panel.record)
        end)
        sections[index] = section
    end

    function panel:Refresh(characterKey, record)
        if self.characterKey ~= characterKey then scroll:SetVerticalScroll(0) end
        self.characterKey, self.record = characterKey, record
        local state = expanded[characterKey] or {}
        local y = 0
        for index, definition in ipairs(ATA.professionSlots) do
            local section = sections[index]
            local profession = record and record.professions and record.professions[definition.key]
            local open = state[definition.key]
            section.header:SetShown(profession ~= nil)
            for _, row in ipairs(section.rows) do row:Hide() end
            if profession then
            section.header:SetPoint("TOPLEFT", 0, -y)
            section.header:SetPoint("RIGHT", content, "RIGHT", 0, 0)
            section.header.label:SetText((open and "-  " or "+  ") .. profession.name)
            section.icon:SetTexture(profession.icon)
            y = y + 44
            if open then
                local tiers = {}
                for _, tier in ipairs(profession.expansions or {}) do
                    if tier.maxSkillLevel and tier.maxSkillLevel > 0 then tiers[#tiers + 1] = tier end
                end
                ATA:SortProfessionTiers(tiers)
                -- Archaeology has one shared skill rather than expansion skill lines.
                if profession and #tiers == 0 and definition.key == "archaeology" then
                    tiers = { { name = "Overall skill", skillLevel = profession.skillLevel, maxSkillLevel = profession.maxSkillLevel } }
                end
                local count = math.max(1, #tiers)
                for rowIndex = 1, count do
                    local row = section.rows[rowIndex]
                    if not row then
                        row = helpers.CreateProfessionProgressBar(content, 22)
                        row:SetWidth(590)
                        row:SetScript("OnSizeChanged", function(self)
                            self:SetValue(self.fraction or 0)
                        end)
                        -- Keep the label above the rounded bar's fill frame.
                        row.labelFrame = CreateFrame("Frame", nil, row)
                        row.labelFrame:SetAllPoints()
                        row.labelFrame:SetFrameLevel(row:GetFrameLevel() + 2)
                        row.text = row.labelFrame:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
                        row.text:SetPoint("LEFT", 8, row:GetHeight() * 2.5 / 29)
                        row.text:SetPoint("RIGHT", -8, row:GetHeight() * 2.5 / 29)
                        row.text:SetJustifyH("CENTER")
                        local fontPath, fontSize = row.text:GetFont()
                        row.text:SetFont(fontPath, fontSize, "OUTLINE")
                        row.text:SetShadowOffset(0, 0)
                        section.rows[rowIndex] = row
                    end
                    local tier = tiers[rowIndex]
                    row:SetPoint("TOPLEFT", 12, -y)
                    row:SetPoint("RIGHT", content, "RIGHT", -12, 0)
                    local fraction = tier and tier.maxSkillLevel > 0 and tier.skillLevel / tier.maxSkillLevel or 0
                    row.fraction = fraction
                    row:SetProfession(profession and profession.skillLineID)
                    row:SetValue(fraction)
                    row.text:SetText(tier and ((tier.name or "Profession skill") .. "   " .. tier.skillLevel .. " / " .. tier.maxSkillLevel)
                        or (profession and "Expansion skills unavailable. Open this profession in game and rescan."
                            or (record and record.professions and "This profession has not been learned." or "Log in to this character and rescan to collect professions.")))
                    row:Show()
                    y = y + 34
                end
                y = y + 8
            end
            end
        end
        content:SetHeight(math.max(1, y))
        scroll:SetVerticalScroll(math.min(scroll:GetVerticalScroll(), math.max(0, y - scroll:GetHeight())))
        UpdateScroll()
    end
    return panel
end
