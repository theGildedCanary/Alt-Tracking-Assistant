# Alt Tracking Assistant Companion

Desktop app that reads the addon's saved data and exports it to your existing Google Sheet (or a local `.xlsx`/`.csv`).

## Use (end users)

1. Run `AltTrackingAssistantCompanion.exe`.
2. Pick your WoW folder (auto-detected if standard).
3. Paste the link to your Google Sheet and click **Sign in with Google** (once). The account must be able to edit that sheet.
4. Click **Export now**, or enable auto-export to refresh whenever the addon data changes (WoW writes it on logout or `/reload`).

Rows are sorted like the addon's roster: class group (Paladin/Warrior/Death Knight, Hunter/Shaman/Evoker, Druid/Rogue/Monk/Demon Hunter, Mage/Priest/Warlock), then highest level first. The columns are in a fixed order: Name, Realm, Class, Race, Faction, Level, Last Scanned, then the trackers in the addon's order (Darkmoon Faire, Midnight, The War Within, ... Cataclysm, Classic). A new tracker the app doesn't know yet is added at the far right, so existing column numbers don't move. When adding trackers to the addon, add them to `layout.py` too.

Only a tab named `Alt Tracking Assistant` is created/replaced; your other tabs are untouched. Choose **Local file** instead to export to an existing `.xlsx`/`.csv`.

Headless: `python app.py --export <WoW folder> <Google Sheet URL | output.xlsx | output.csv>`

## Roster tab

The **Roster** tab shows every character in a spreadsheet-style grid (realm, faction, level, DOB, name, race, class main, class, then every tracker grouped by expansion). Data is copied into a local database (%APPDATA%\AltTrackingAssistantCompanion\companion.db) each time the addon data changes, so characters stay in the app even if they are no longer in the addon's data. The grid updates after you /reload or log out in game.

## Building the executable (maintainer, one time)

Google sign-in needs an OAuth client belonging to the app. End users never see this step.

1. In Google Cloud Console, create a project and enable the **Google Sheets API**.
2. Configure the OAuth consent screen and create an **OAuth client ID** of type **Desktop app**.
3. Download it as `client_secret.json` into this folder (git-ignored; bundled into the exe).
4. `python -m pip install pyinstaller -r requirements.txt`, then `.\build_exe.ps1`. The exe is written to `dist\`.

The Sheets scope is "sensitive": until the app passes Google verification, users see an "unverified app" warning and only test users you add (max 100) can sign in.
