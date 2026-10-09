# Alt Tracking Assistant

**Alt Tracking Assistant (ATA)** is a World of Warcraft Retail addon for tracking alternate characters, progression, unlocks, quest completion, and other account-wide checklist information.

The project is designed around a cached character database: the currently logged-in character can be scanned and its results stored in account-wide SavedVariables so previously scanned characters can be reviewed later from the addon.

## Planned Features

- Account-wide cached character roster
- Per-character report pages
- Completion checks for quests, campaign steps, skips, unlocks, and other progression
- Progress displays such as checkmarks and `current/total` values
- Character selector for reviewing cached alts
- Last-scanned timestamps
- An all-characters overview for comparing progression across the roster
- Organized report sections matching the categories used by the Alt Tracker spreadsheet

## Implemented Progress Checks

The current scanner records progress for Shadowlands, Dragonflight, The War Within, and Midnight:

**Shadowlands**

- **Covenant** — the selected character's active covenant is always shown in its covenant color. The optional **View Covenant** selector lets you review another covenant's Renown; when disabled, Renown follows the active covenant. Character mains are highlighted in gold.
- **Character Mains** — configure a character-main set (Single, Faction, Class, or Class Faction) and an independent armor-main set (Armor or Armor Faction). Both sets can be active at once; selectors are filtered by faction, class, or armor type when relevant.
- **4k Anima** — counts covenants with Renown 60 or higher, out of four.
- **Renown** — current renown level out of 80 for the selected covenant.
- **Korthia** — quest 63665 or 63944 is complete.
- **Zereth Mortis** — quest 64957 is complete.
- **Helsworn Chest** — quest 64256 is complete.

**Dragonflight**

- **Silas' Secret Stash** — tracked when quest 38934 is completed or stash item 127148 is detected; the completed state is retained after the stash is sold.
- **Intro Skip** — quest 66221 or 72293 is complete.
- **5x Sparks** — quest 70900 is complete.
- **Forbidden Reach** — quest 73076 is complete.
- **Suffusion Camp** — quest 75887 is complete.
- **Zaralek Caverns** — quest 75643 is complete.
- **Emerald Dream** — quest 77283 is complete.
- **Elegant Canvas Brush** — achievement 16301 is earned by that character.

**Midnight**

- **Intro Skip** — quest 94993 or 95008 is complete.
- **Crafters Needed** — quest 93723 is complete.
- **Val / Naigtal Skip** — quest 97071 or 97072 is complete.
- **Coiled Isle Skip** — quest 93012 is complete.

**The War Within**

- **Intro Skip** — quest 83543 is complete.
- **Crafting to Order** — quest 84260 is complete.
- **Undermine** — quest 83151 is complete.
- **Delve Belt** — quest 91009 is complete.
- **Reshii Wraps** — item 235499 is in the character's inventory, bags, bank, reagent bank, or account bank.

Results are saved under each character's GUID in account-wide SavedVariables. The scanner records the character's approximate birth date from the character-earned Level 10 achievement. The scanner runs at login, after achievement or quest earn events, and when bags or bank contents change. Open the report from the minimap button or with `/ata`; it includes a manual rescan button. The **Alt Tracking Assistant** options page links to the dashboard and provides a tester thank-you. Configure character mains, armor mains, and the separately designated **True Main** on the **Mains** page. The True Main is marked with a crown in the dashboard. Configure tracker visibility or per-character **Manual Overrides** on the **Expansions** page. An active override replaces the scanner result for that character and tracker; inactive overrides leave scans in control. These settings and overrides are account-wide saved data. The active Shadowlands covenant is always shown; disabling **View Covenant** hides only the covenant selector and makes Renown display the active covenant's level.

## Project Status

ATA is in early development. Its report displays Shadowlands, Dragonflight, The War Within, and Midnight checks, character details, and a cached-roster summary. Additional expansions and trackers are still to come. The repository also includes the validation workflow and automated release packaging.

The report UI uses a shared gray-blue and gold theme. The roster shows a live portrait for the logged-in character and faction emblems for other cached characters, with progress bars colored by class.

The selected-character header presents the character portrait and selector, realm, faction, class, level, and last-scan time in a single row.

Expansion progress uses a fixed three-column grid within bordered cards. Shadowlands uses `#1C488E`, Dragonflight uses `#04404A`, The War Within uses `#792D0B`, and Midnight uses `#331E53` for their title banners and section borders. Each expansion has its own title treatment and progress-bar color, while the progress-check area retains the standard gray-blue panel.

Current version: **2.0.0**

## Installation

Download from the GitHub Releases page:

1. Download the latest `AltTrackingAssistant-vX.Y.Z.zip` file from GitHub Releases.
2. Extract it into your Retail WoW addon directory:
   `World of Warcraft/_retail_/Interface/AddOns/`
3. Confirm the resulting folder is named:
   `AltTrackingAssistant`
4. Restart World of Warcraft or reload the UI.

### Optional Windows companion

The Windows companion is included in `AltTrackingAssistant-v2.0.0.zip`. After extracting the addon, launch `AltTrackingAssistantCompanion.exe` from the main `AltTrackingAssistant` folder.

Use the companion to view your roster, configure mains and tracker visibility, customize formatting, and export local `.xlsx` or `.csv` files. No sign-in is required. The addon works without running the companion.

WoW writes updated character data when you log out or use `/reload`. Settings edited in the companion apply in game on the next login or `/reload`.

The companion stores its database and preferences in `%APPDATA%\AltTrackingAssistantCompanion`; installing an update preserves those files.

See `Companion-README.md` in the release download, or [the companion instructions](Companion/README.md) in this repository, for details.

## Repository Structure

```text
AltTrackingAssistant.toc
Core/
Features/
UI/
Media/
Companion/
scripts/
.github/
```

- **Core/** — addon initialization, SavedVariables, shared data model, and core services
- **Features/** — character scanners, tracker definitions, and feature modules
- **UI/** — report pages, options, character selectors, and other interface code
- **Media/** — addon icons and other bundled media
- **Companion/** — Windows companion source and build script
- **scripts/** — repository validation utilities
- **.github/** — issue templates and GitHub Actions workflows

## Development Validation

Every push to `main` and every pull request runs the addon validation workflow. It checks:

- required project files and folders;
- semantic version formatting in the TOC;
- TOC file references;
- Lua 5.1 syntax for addon Lua files.
- Python syntax for companion source files.

For a source checkout, copy `scripts/AppSync.default.lua` to `AppSync.lua` before loading the addon. `AppSync.lua` contains local settings generated by the companion and is ignored by Git. Release ZIPs include a neutral starting file.

## Release Packaging

Release ZIP files are built automatically by GitHub Actions.

To publish a release:

1. Update `## Version:` in `AltTrackingAssistant.toc`.
2. Update `CHANGELOG.md`.
3. Commit the release changes.
4. Create and publish a GitHub Release using the matching tag `v2.0.0`.

The release workflow verifies that the tag and TOC versions match, validates the addon, and attaches:

```text
AltTrackingAssistant-v2.0.0.zip
```

The ZIP contains an `AltTrackingAssistant` folder ready to place directly in `Interface/AddOns`. It includes the addon and Windows companion executable together. GitHub builds the companion on Windows and packages a neutral settings sync file without personal settings or Google credentials.

## Contributions

Bug reports, feature requests, screenshots, diagnostics, and reproducible test cases are welcome. Unsolicited code contributions are not currently accepted unless requested or approved in advance.

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

Copyright © 2026 Gilded Canary. All Rights Reserved.

Alt Tracking Assistant is proprietary software. Personal use and local modification are permitted, but redistribution, republishing modified versions, derivative distribution, repackaging, and commercial distribution are not permitted without prior written permission.

See [LICENSE](LICENSE) for the complete terms.

## Disclaimer

World of Warcraft and related names and trademarks are property of Blizzard Entertainment, Inc. This project is not affiliated with or endorsed by Blizzard Entertainment.
