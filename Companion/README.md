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

## Roster tab

The **Roster** tab shows every character in a spreadsheet-style grid (realm, faction, level, DOB, name, race, class main, class, then every tracker grouped by expansion). Data is copied into a local database (%APPDATA%\AltTrackingAssistantCompanion\companion.db) each time the addon data changes, so characters stay in the app even if they are no longer in the addon's data. The grid updates after you /reload or log out in game.

## Building the executable (maintainer, one time)

1. Close the companion app before rebuilding it.
2. From this folder, run `python -m pip install pyinstaller -r requirements.txt`, then `.\build_exe.ps1`. The exe is written directly to the main `AltTrackingAssistant` folder. You can also run `.\Companion\build_exe.ps1` from the main folder. If Python is not available on PATH, pass `-PythonExecutable` with the full path to your Python executable.
