# Alt Tracking Assistant Companion

Desktop app that reads the addon's saved data and exports it to a local Excel workbook (`.xlsx`) or CSV file (`.csv`). No sign-in or user approval is required.

## Use (end users)

1. Run `AltTrackingAssistantCompanion.exe` from the main `AltTrackingAssistant` folder.
2. Pick your WoW folder (auto-detected if standard).
3. In **Export**, click **Browse...** next to **Local file** and choose an `.xlsx` or `.csv` destination.
4. Click **Export now**, or enable auto-export to refresh whenever the addon data changes (WoW writes it on logout or `/reload`).

Rows are sorted like the addon's roster: class group (Paladin/Warrior/Death Knight, Hunter/Shaman/Evoker, Druid/Rogue/Monk/Demon Hunter, Mage/Priest/Warlock), then highest level first. The columns are in a fixed order: Name, Realm, Class, Race, Faction, Level, Last Scanned, then the trackers in the addon's order (Darkmoon Faire, Midnight, The War Within, ... Cataclysm, Classic). A new tracker the app doesn't know yet is added at the far right, so existing column numbers don't move. When adding trackers to the addon, add them to `layout.py` too.

In an Excel workbook, only a tab named `Alt Tracking Assistant` is created/replaced; your other tabs are untouched. CSV exports replace the contents of the selected file. Close the destination file in Excel before exporting.

Headless: `python app.py --export "<WoW folder>" "<output.xlsx | output.csv>"`

## Professions tab

**Settings → UI theme → WoW Mode** uses the addon's muted gold and warm brown palette, original selected-tab fade, textured profession headings, and red action controls. It is the default for new installations; Dark Mode also uses the warm palette. Light Mode remains available. Old default roster colors migrate to the warm palette while custom colors are preserved.

The Companion Professions dashboard has a GUID-based character picker, saved per-character profession selections, removable sidebar entries, and collapsible expansion progress bars. Select a character, add them, and check the professions you want to track. Tracked professions are highlighted on the roster when Profession Highlight is enabled.

Profession progress bars display the original profession-specific WoW artwork and its two-second fill animation, including Alchemy's purple glow and Tailoring's blue-and-gold threads. These images were extracted from the installed WoW 12.1.0.69933 archives and cropped using that build's atlas coordinates. Font family, body/title sizes, and bold settings still update immediately. The fills retain Blizzard's original colors; the legacy profession color setting no longer tints them.

All 13 professions with dedicated Blizzard bar artwork are included. Archaeology uses Blizzard's default blue artwork because this build has no dedicated Archaeology fill. ATA references the corresponding native atlases in game. `assets/profession_bars/manifest.json` records texture IDs, crop coordinates, source hashes, and the build. `../scripts/extract-profession-art.py` reproduces the PNG conversion from extracted BLP files and atlas CSV metadata.

Use **Settings → Roster → Columns** to show or hide the five profession columns, reorder columns, and change titles and alignment. **Profession Highlight** toggles gold shading for tracked professions. **Main Highlight** toggles main name coloring (gold by default) and bold main rows.

Use **Settings → Roster → Expansions** to edit roster expansion names, show or hide entire blocks, and move expansions up or down. **Expansion trackers** below it provides names, visibility, and ordering for individual tracker columns, grouped by expansion. Trackers can only move within their own expansion. These choices are saved locally and apply immediately. **Settings → Formatting → Expansion tracker colors** controls colors and lists expansions in the same saved order.

**Settings → Formatting → Faction, gender, class and covenant** includes covenant colors shared by covenant names and each covenant’s renown values.

## Roster tab

Prof 1 and Prof 2 show profession names in separate columns next to Class. The vertical Arch., Fish., and Cook. columns show `x` for learned Archaeology, Fishing, and Cooking, and stay blank otherwise. Profession data comes from the addon after logging in to each character and logging out or using `/reload`. Professions are also included in local exports.

The **Roster** tab shows every character in a spreadsheet-style grid (realm, faction, level, DOB, name, race, class main, class, then every tracker grouped by expansion). Data is copied into a local database (%APPDATA%\AltTrackingAssistantCompanion\companion.db) each time the addon data changes, so characters stay in the app even if they are no longer in the addon's data. The grid updates after you /reload or log out in game.

## Building the executable (maintainer, one time)

1. Close the companion app before rebuilding it.
2. From this folder, run `python -m pip install pyinstaller -r requirements.txt`, then `.\build_exe.ps1`. The exe is written directly to the main `AltTrackingAssistant` folder. You can also run `.\Companion\build_exe.ps1` from the main folder. If Python is not available on PATH, pass `-PythonExecutable` with the full path to your Python executable.

## Quest Log (v2.2.0)

The Quest Log tab sits between Professions and Settings. Choose a character and click **Add character**; only selected characters appear. Weeklies and Dailies show vertical quest-name columns like the Roster, with a per-character status indicator. The To do fraction shows completed / assigned manual tasks. Click a character name to open the detail panel; **Close** hides it and restores the full-width list. Adding a character or refreshing data does not open the panel. All Quest Log surfaces, dropdowns, and notes fields use the existing brown palette.

Use **Add quest ID** to assign a numeric quest ID to the selected character. Enter a nickname for the vertical heading and detail title, and choose **Auto**, **None**, **Daily**, or **Weekly** under Reset. Auto uses the frequency detected by WoW; manual choices override it and immediately place the quest in the appropriate group. With Auto, unknown frequency stays under Other quests until WoW supplies it. Player IDs are hidden from the character picker; quest IDs appear only in the editor. The indicators are ○ Not picked up, ◇ Picked up but not started, ◐ In progress, and ✓ Completed. Ready to turn in stays In progress until the quest is turned in. A ? indicates that a scan or objective data is needed; — means the quest is not assigned to that character. Old snapshots need a fresh scan to distinguish acceptance from objective progress.

After adding IDs, `/reload` in WoW to load the assignments, then log into each selected character. `/reload` or logout saves the character's snapshot; **Refresh** in the Companion imports it. After a recurring quest's reset, the old snapshot says Awaiting new scan until refreshed data arrives. No live connection to WoW is required.

Manual tasks support titles, multiline notes / steps, priority, and a completion checkbox. Check it to mark Completed; uncheck it to return to Pending. Select None, Daily, or Weekly. Daily resets occur at **11 a.m. EST**; weekly resets occur **Tuesday at 11 a.m. EST**. This schedule uses fixed EST (UTC−5) and also controls when recurring quest snapshots need a new scan. Manual statuses reset to Pending when the reset passes, including while the app was closed, without needing a server-reset snapshot. Edit or delete individual tasks, or remove a character and their assignments.

Assignments and manual tasks are stored in the Companion's local database. Quest IDs use a separate generated QuestSync.lua file, so they do not replace Companion Settings edits. Select the correct WoW folder on Export if the app cannot send assignments to the addon.

To reuse an existing quest or to do, click its name in the character detail panel. Quest headings in the full character list also open the assignment popup. The popup lists only added characters, with independent selection indicators. Choose any number of characters and click **Save**; **Cancel** leaves assignments unchanged. New assignments copy the nickname, notes, priority, and reset settings. Manual task progress remains separate per character and starts Pending on a new character. Existing assignments keep their own progress. Unchecking a character removes that task from their list; unchecking everyone removes all assignments for it.

Shared to dos also appear as vertical columns in the full character list, with independent pending, in progress, and completed indicators. Click a to do heading or use **Characters** in its detail card to change assignments. Group headings and vertical names use white text: Weeklies have dark purple backgrounds, Dailies blue, and To dos green. Other quests use the brown panel background. The character list shows names without realms.

Quest Log follows the app's SavedVariables refresh after `/reload` or logout and supports the same manual Refresh action. It has no separate periodic refresh timer. Reset transitions are applied when data refreshes or tasks are edited. Assignment and task editor popups remember their positions and sizes across reopening and app restarts, with the same disconnected-monitor fallback as the main window.
