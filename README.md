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

## Project Status

ATA is in early development. The repository currently contains the project scaffold, validation workflow, and automated release packaging.

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
