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

The current scanner records progress for Dragonflight, The War Within, and Midnight:

**Dragonflight**

- **Silas' Secret Stash** — quest 38934 is complete.
- **Intro Skip** — quest 72293 is complete.
- **5x Sparks** — quest 70900 is complete.
- **Forbidden Reach** — quest 73076 is complete.
- **Suffusion Camp** — quest 75887 is complete.
- **Zaralek Caverns** — quest 75643 is complete.
- **Emerald Dream** — quest 77283 is complete.

**Midnight**

- **Intro Skip** — quest 94993 or 95008 is complete.
- **Crafters Needed** — quest 93723 is complete.

**The War Within**

- **Intro Skip** — quest 83543 is complete.
- **Crafting to Order** — quest 84260 is complete.
- **Undermine** — quest 83151 is complete.
- **Reshii Wraps** — item 235499 is in the character's inventory, bags, bank, reagent bank, or account bank.

Results are saved under the character's GUID in account-wide SavedVariables. The scanner runs at login, after tracked quests are turned in, and when bags or bank contents change. Open the report from the minimap button or with `/ata`; it includes a manual rescan button. Settings are not yet available, so there is no AddOn Options page yet.

## Project Status

ATA is in early development. Its report displays Dragonflight, The War Within, and Midnight checks, character details, and a cached-roster summary. Additional expansions and trackers are still to come. The repository also includes the validation workflow and automated release packaging.

The report UI uses a shared gray-blue and gold theme. The roster shows a live portrait for the logged-in character and class emblems for other cached characters, with progress bars colored by class.

The selected-character header presents the character portrait and selector, realm, faction, class, level, and last-scan time in a single row.

Expansion progress uses a fixed three-column grid within bordered cards. Dragonflight uses `#04404A`, The War Within uses `#792D0B`, and Midnight uses `#331E53` for their title banners and section borders. Each expansion has its own title treatment and progress-bar color, while the progress-check area retains the standard gray-blue panel.

Current development version: **0.1.0**

## Installation

Once releases are available:

1. Download the latest `AltTrackingAssistant-vX.Y.Z.zip` file from GitHub Releases.
2. Extract it into your Retail WoW addon directory:
   `World of Warcraft/_retail_/Interface/AddOns/`
3. Confirm the resulting folder is named:
   `AltTrackingAssistant`
4. Restart World of Warcraft or reload the UI.

## Repository Structure

```text
AltTrackingAssistant.toc
Core/
Features/
UI/
Media/
scripts/
.github/
```

- **Core/** — addon initialization, SavedVariables, shared data model, and core services
- **Features/** — character scanners, tracker definitions, and feature modules
- **UI/** — report pages, options, character selectors, and other interface code
- **Media/** — addon icons and other bundled media
- **scripts/** — repository validation utilities
- **.github/** — issue templates and GitHub Actions workflows

## Development Validation

Every push to `main` and every pull request runs the addon validation workflow. It checks:

- required project files and folders;
- semantic version formatting in the TOC;
- TOC file references;
- Lua 5.1 syntax for addon Lua files.

## Release Packaging

Release ZIP files are built automatically by GitHub Actions.

To publish a release:

1. Update `## Version:` in `AltTrackingAssistant.toc`.
2. Update `CHANGELOG.md`.
3. Commit the release changes.
4. Create and publish a GitHub Release using a matching tag such as `v0.1.0`.

The release workflow verifies that the tag and TOC versions match, validates the addon, and attaches:

```text
AltTrackingAssistant-v0.1.0.zip
```

The ZIP contains an `AltTrackingAssistant` folder ready to place directly in `Interface/AddOns`.

## Contributions

Bug reports, feature requests, screenshots, diagnostics, and reproducible test cases are welcome. Unsolicited code contributions are not currently accepted unless requested or approved in advance.

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

Copyright © 2026 Gilded Canary. All Rights Reserved.

Alt Tracking Assistant is proprietary software. Personal use and local modification are permitted, but redistribution, republishing modified versions, derivative distribution, repackaging, and commercial distribution are not permitted without prior written permission.

See [LICENSE](LICENSE) for the complete terms.

## Disclaimer

World of Warcraft and related names and trademarks are property of Blizzard Entertainment, Inc. This project is not affiliated with or endorsed by Blizzard Entertainment.
