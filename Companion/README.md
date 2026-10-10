# Alt Tracking Assistant Companion

Desktop app that reads the addon's saved data and exports it to a local Excel workbook (`.xlsx`) or CSV file (`.csv`). No sign-in or user approval is required.

## Use (end users)

1. On Windows, run `AltTrackingAssistantCompanion.exe` from the main `AltTrackingAssistant` folder. On macOS, download the separate Companion ZIP matching your Mac (`arm64` for Apple Silicon or `x86_64` for Intel), extract it, and drag `AltTrackingAssistantCompanion.app` into Applications before opening it. Python is included; no separate installation is required.
2. Pick your WoW folder (auto-detected if standard).
3. In **Export**, click **Browse...** next to **Local file** and choose an `.xlsx` or `.csv` destination.
4. Click **Export now**, or enable auto-export to refresh whenever the addon data changes (WoW writes it on logout or `/reload`).

On Mac, the standard WoW location is `/Applications/World of Warcraft`. Use **Browse** if you installed it elsewhere; either the main WoW folder or its `_retail_` folder works. The addon must be installed separately using the main addon ZIP.

The Mac build is ad-hoc signed, but is not notarized with an Apple Developer certificate. If macOS blocks the first launch, follow [Apple's instructions](https://support.apple.com/102445) in **System Settings → Privacy & Security → Open Anyway** for an app you downloaded from this project's GitHub. Managed Macs may require administrator approval. Builds currently use macOS 15 runners; earlier macOS versions have not been verified.

Preferences and the roster database are stored in `%APPDATA%\AltTrackingAssistantCompanion` on Windows and `~/Library/Application Support/AltTrackingAssistantCompanion` on Mac. Updating the app preserves these files.

Rows are sorted like the addon's roster: class group (Paladin/Warrior/Death Knight, Hunter/Shaman/Evoker, Druid/Rogue/Monk/Demon Hunter, Mage/Priest/Warlock), then highest level first. The columns are in a fixed order: Name, Realm, Class, Race, Faction, Level, Last Scanned, then the trackers in the addon's order (Darkmoon Faire, Midnight, The War Within, ... Cataclysm, Classic). A new tracker the app doesn't know yet is added at the far right, so existing column numbers don't move. When adding trackers to the addon, add them to `layout.py` too.

In an Excel workbook, only a tab named `Alt Tracking Assistant` is created/replaced; your other tabs are untouched. CSV exports replace the contents of the selected file. Close the destination file in Excel before exporting.

Headless: `python app.py --export "<WoW folder>" "<output.xlsx | output.csv>"`

## Professions tab

The Companion Professions dashboard has a GUID-based character picker, saved per-character profession selections, removable sidebar entries, and collapsible expansion progress bars. Select a character, add them, and check the professions you want to track. Tracked professions are highlighted on the roster when Profession Highlight is enabled.

**Settings → Formatting → Colors → Profession progress bars** controls the bar color (default `#331E53`). Font family, body/title sizes, and bold settings also update the Professions tab immediately.

Use **Settings → Roster → Columns** to show or hide the five profession columns, reorder columns, and change titles and alignment. **Profession Highlight** toggles gold shading for tracked professions. **Main Highlight** toggles main name coloring (gold by default) and bold main rows.

Use **Settings → Roster → Expansions** to edit roster expansion names, show or hide entire blocks, and move expansions up or down. **Expansion trackers** below it provides names, visibility, and ordering for individual tracker columns, grouped by expansion. Trackers can only move within their own expansion. These choices are saved locally and apply immediately. **Settings → Formatting → Expansion tracker colors** controls colors and lists expansions in the same saved order.

**Settings → Formatting → Faction, gender, class and covenant** includes covenant colors shared by covenant names and each covenant’s renown values.

## Roster tab

Prof 1 and Prof 2 show profession names in separate columns next to Class. The vertical Arch., Fish., and Cook. columns show `x` for learned Archaeology, Fishing, and Cooking, and stay blank otherwise. Profession data comes from the addon after logging in to each character and logging out or using `/reload`. Professions are also included in local exports.

The **Roster** tab shows every character in a spreadsheet-style grid (realm, faction, level, DOB, name, race, class main, class, then every tracker grouped by expansion). Data is copied into `companion.db` in the platform's preferences folder each time the addon data changes, so characters stay in the app even if they are no longer in the addon's data. The grid updates after you /reload or log out in game.

## Building the executable (maintainer, one time)

1. Close the companion app before rebuilding it.
2. From this folder, run `python -m pip install pyinstaller -r requirements.txt`, then `.\build_exe.ps1`. The exe is written directly to the main `AltTrackingAssistant` folder. You can also run `.\Companion\build_exe.ps1` from the main folder. If Python is not available on PATH, pass `-PythonExecutable` with the full path to your Python executable.

## Automatic Mac builds (no Mac required for maintainers)

The **Build macOS Companion** GitHub Actions workflow builds separate Apple Silicon and Intel apps on hosted Macs. It runs on Companion pull requests and pushes to `main`, and can also be run from the Actions page. Each job runs the companion tests, checks the bundle's architecture and signature, launches the packaged GUI, and exports a sample roster to both CSV and Excel. Download the `companion-macOS-arm64` or `companion-macOS-x86_64` workflow artifact to get the app ZIP.

The release workflow attaches both Mac ZIPs alongside the existing Windows/addon ZIP. Release tags must include the Mac build changes; rebuilding an older tag does not add new source code to that release.

For local builds on a Mac with Python/Tk installed: `python3 -m pip install pyinstaller -r Companion/requirements.txt`, then `bash Companion/build_macos.sh`. The output is `Companion/dist/macos/AltTrackingAssistantCompanion.app`. No Apple Developer credentials are needed for these ad-hoc signed builds. Developer ID signing and Apple notarization would require separately supplied Apple credentials.
