local _, ATA = ...

-- GetProfessions returns two main slots, then archaeology, fishing, cooking.
ATA.professionSlots = {
    { key = "primary", label = "Profession 1" },
    { key = "secondary", label = "Profession 2" },
    { key = "archaeology", label = "Archaeology" },
    { key = "fishing", label = "Fishing" },
    { key = "cooking", label = "Cooking" },
}

local expansionOrder = {
    "Midnight", "Khaz Algar", "Dragon Isles", "Shadowlands",
    "Kul Tiran", "Legion", "Draenor", "Pandaria", "Cataclysm",
    "Northrend", "Outland", "Classic",
}

local tertiaryByID = {
    [794] = { key = "archaeology", label = "Archaeology", icon = "Interface\\Icons\\Trade_Archaeology" },
    [356] = { key = "fishing", label = "Fishing", icon = "Interface\\Icons\\Trade_Fishing" },
    [185] = { key = "cooking", label = "Cooking", icon = "Interface\\Icons\\INV_Misc_Food_15" },
}

-- Cooking and Fishing tiers are not reliably included in the general profession list.
local secondaryTiers = {
    [185] = { 2908, 2873, 2824, 2752, 2541, 2542, 2543, 2544, 2545, 2546, 2547, 2548 },
    [356] = { 2911, 2876, 2826, 2754, 2585, 2586, 2587, 2588, 2589, 2590, 2591, 2592 },
}

local function GetExpansionOrder(tier)
    local name = tier.name or ""
    -- Horde characters use Zandalari for the same tier as Kul Tiran.
    if name:find("Zandalari", 1, true) then return 5 end
    for index, expansion in ipairs(expansionOrder) do
        if name:find(expansion, 1, true) then return index end
    end
    return #expansionOrder + 1
end

function ATA:SortProfessionTiers(tiers)
    table.sort(tiers, function(a, b)
        local left, right = GetExpansionOrder(a), GetExpansionOrder(b)
        if left ~= right then return left < right end
        return (a.skillLineID or 0) > (b.skillLineID or 0)
    end)
end

function ATA:ScanProfessions(record)
    if not GetProfessions or not GetProfessionInfo then return end
    local primary, secondary, archaeology, fishing, cooking = GetProfessions()
    local indices = { primary, secondary, archaeology, fishing, cooking }
    local previous = record.professions or {}
    local professions, byID = {}, {}
    for slot, definition in ipairs(self.professionSlots) do
        local index = indices[slot]
        if index then
            local name, icon, rank, maximum, _, _, skillLineID = GetProfessionInfo(index)
            if not name or not skillLineID then return end -- Keep the last complete snapshot while loading.
            local old = previous[definition.key]
            local profession = {
                name = name, icon = icon, skillLineID = skillLineID,
                skillLevel = rank or 0, maxSkillLevel = maximum or 0,
                expansions = old and old.skillLineID == skillLineID and old.expansions or {},
            }
            professions[definition.key] = profession
            byID[skillLineID] = profession
        end
    end

    local api = C_TradeSkillUI
    if api and api.GetAllProfessionTradeSkillLines and api.GetProfessionInfoBySkillLineID then
        local lines, seen, tierParents = {}, {}, {}
        for _, id in ipairs(api.GetAllProfessionTradeSkillLines() or {}) do
            lines[#lines + 1], seen[id] = id, true
        end
        for parentID, ids in pairs(secondaryTiers) do
            if byID[parentID] then
                for _, id in ipairs(ids) do
                    tierParents[id] = parentID
                    if not seen[id] then lines[#lines + 1], seen[id] = id, true end
                end
            end
        end
        -- Some characters expose secondary skills only through learned trade-skill lines.
        -- A positive maximum is required: the API also lists unlearned expansion tiers.
        for _, id in ipairs(lines or {}) do
            local info = api.GetProfessionInfoBySkillLineID(id)
            local parentID = info and (info.parentProfessionID or id)
            local definition = tertiaryByID[parentID]
            if definition and not byID[parentID] and (info.maxSkillLevel or 0) > 0 then
                local baseInfo = api.GetProfessionInfoBySkillLineID(parentID)
                local old = previous[definition.key]
                local profession = {
                    name = info.parentProfessionName or (baseInfo and baseInfo.professionName) or definition.label,
                    icon = definition.icon, skillLineID = parentID,
                    skillLevel = info.skillLevel or 0, maxSkillLevel = info.maxSkillLevel,
                    expansions = old and old.skillLineID == parentID and old.expansions or {},
                }
                professions[definition.key] = profession
                byID[parentID] = profession
            end
        end
        local tiers, complete = {}, type(lines) == "table" and #lines > 0
        for _, id in ipairs(lines or {}) do
            local info = api.GetProfessionInfoBySkillLineID(id)
            if not info then
                complete = false
            elseif (tierParents[id] or info.parentProfessionID) and byID[tierParents[id] or info.parentProfessionID] then
                local parentID = tierParents[id] or info.parentProfessionID
                tiers[parentID] = tiers[parentID] or {}
                tiers[parentID][#tiers[parentID] + 1] = {
                    skillLineID = id, name = info.professionName,
                    skillLevel = info.skillLevel or 0, maxSkillLevel = info.maxSkillLevel or 0,
                }
            end
        end
        for id, profession in pairs(byID) do
            if tiers[id] then
                self:SortProfessionTiers(tiers[id])
                profession.expansions = tiers[id]
            elseif complete and not secondaryTiers[id] then
                profession.expansions = {}
            end
        end

        -- The open window can supply skill data before the global queries are ready.
        local remote = (api.IsTradeSkillLinked and api.IsTradeSkillLinked())
            or (api.IsTradeSkillGuild and api.IsTradeSkillGuild())
        if not remote and api.GetBaseProfessionInfo and api.GetChildProfessionInfos then
            local base = api.GetBaseProfessionInfo()
            local profession = base and byID[base.professionID]
            if profession then
                local captured = {}
                for _, tier in ipairs(profession.expansions) do captured[tier.skillLineID] = tier end
                for _, info in ipairs(api.GetChildProfessionInfos() or {}) do
                    if (info.maxSkillLevel or 0) > 0 then
                        captured[info.professionID] = {
                            skillLineID = info.professionID, name = info.professionName,
                            skillLevel = info.skillLevel or 0, maxSkillLevel = info.maxSkillLevel,
                        }
                    end
                end
                profession.expansions = {}
                for _, tier in pairs(captured) do profession.expansions[#profession.expansions + 1] = tier end
                self:SortProfessionTiers(profession.expansions)
            end
        end
    end
    record.professions = professions
    record.professionsScanned = time()
end
