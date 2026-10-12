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

**WoW Mode** uses the addon's muted gold and warm brown palette, original selected-tab fade, textured profession headings, and red action controls. It is the only app theme. Old default roster colors migrate to the warm palette while custom colors are preserved.

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

The Quest Log sits between Professions and Settings. Add only the characters you want to track. Reorder them with Order Characters; remove them with the red X before the table. Names show Level - Name with black text on class-colored backgrounds.

Add quests and tasks from the dashboard. Give quests a nickname for the vertical headings and choose any tracking characters. Click a heading or task name to edit its settings and assignments. Weeklies use purple columns, Dailies blue, and To Dos green. Manual tasks have gold completion checkboxes directly in the grid, with separate progress per character.

Reset weekday selections replace the old reset dropdown. Choose all seven days for Daily, one day for Weekly, or several days for that schedule. Leave all unchecked for no reset. Each selected day resets at **11 a.m. fixed EDT (UTC−4)**. Existing weekly schedules default to Tuesday. [D]/[W] identify Daily/Weekly; [1], [2], and [3] identify High, Medium, and Low priority. Remove from character removes one assignment; Delete to do removes all assignments for that quest/task.

Quest indicators are ○ not picked up, an empty checkbox for picked up or pending, a checked checkbox for completed, ? awaiting scan, and — not assigned. Completed quest snapshots need a new character scan after a reset. Quest Log refreshes with the rest of the app after WoW saves on logout or reload. Popups remember their placement.

## Roster character panel

Click a character name on the Roster to open Info, To Do, and Notes. The selected roster name remains highlighted until the panel closes.

Companion popups open centered over the main app window on its current monitor. Saved popup positions no longer override this placement. Popups stay within the monitor's available work area where their size allows.

**Info** provides an editable character profile with supported HTML formatting. Edit Info shows the HTML source; Save Info renders it. The info icon lists supported tags/CSS. This is a native renderer with a supported subset, not a full browser. Choose a WoW weather image header or insert colors through the hex/color picker. Montserrat is the default; Skurri, Morpheus, and Friz Quadrata TT are bundled.

**To Do** includes an **Action Needed** checkbox. Check it to highlight this character’s name with a reddish maroon background on the Roster; uncheck it to restore normal formatting. The flag is saved per character and remains independent of task completion.

**To Do** groups quests, achievements, and item tracking under Auto Tracking, followed by manual tasks. Use the completion checkbox for manual items and the square pen, character, and X buttons to manage assignments.

**Notes** reads and edits the addon's Notes / History. Enter a note and click Save, or click the pen before an existing note to edit it. Year and day headers collapse independently and include entry counts; editing preserves the original date. The X asks before deleting.

## Addon synchronization

The Companion writes separate AppSync.lua, QuestSync.lua, and NotesSync.lua files into the selected addon installation. WoW loads them on login or UI reload. After saving app edits, click Rescan in the addon: it scans and then reloads the UI to apply changes, causing a brief loading screen. It is blocked in combat. The Companion receives addon snapshots when WoW saves on logout or `/reload`; scans alone do not write SavedVariables to disk.

Automatic addon IDs accept a quest number, achievement:ID, or item:ID. A blank ID creates a manual task. Offline characters use their saved snapshots; only the logged-in character can be scanned live.
