# Changelog

All notable changes to Alt Tracking Assistant will be documented in this file.

The project uses semantic versioning:

- **MAJOR** — incompatible or major architectural/release changes
- **MINOR** — new backwards-compatible features
- **PATCH** — backwards-compatible fixes and small corrections

## [0.1.0] - Unreleased

### Added

- Initial addon project scaffold.
- Account-wide SavedVariables initialization.
- Midnight quest completion scanning for the Intro Skip and Crafters Needed checks, saved per character GUID.
- Initial in-game report window with minimap button, slash command, and manual character rescan.
- Use a ready-check texture for completed status and enable minimap button dragging.
- Add cached-character selection and a collapsible, expansion-colored Midnight report section.
- Centralize report colors for consistent expansion styling.
- Match the IRS minimap button treatment with a circularly masked ATA icon and additive hover highlight.
- Rework the report layout with a character header, expansion panel, and cached-roster summary.
- Replace default report controls with ATA gray-blue panels and gold borders; show roster portraits and class-colored progress bars.
- Set the report backdrop to #11161C and align the report and roster cards to the character selector width.
- Use the Midnight Teleport: Silvermoon spell icon in the expansion header with a thin gold ring.
- Display quest completion as gold-bordered checkboxes.
- Add gold portrait rings to roster entries and stack the Last Scanned label above its timestamp.
- Arrange the selected-character header as portrait, selector, realm, faction, class, level, and last scan.
- Set Midnight to #331E53 for its banner and border; size the bordered card around the banner and fixed three-column check grid.
- Keep Midnight purple on the title banner and card border only, with the progress-check backdrop matching the standard gray-blue panel.
- Anchor Midnight checks directly to the three-column section body so Intro Skip and Crafters Needed render in their cells.
- Place Midnight check labels and checkboxes directly in the section body with explicit three-column coordinates.
- Add The War Within trackers for Intro Skip, Crafting to Order, Undermine, and Reshii Wraps.
- Add the The War Within banner emblem, orange styling, and expansion-specific progress bar to the report.
- Add Dragonflight trackers for Silas' Secret Stash, Intro Skip, 5x Sparks, Forbidden Reach, Suffusion Camp, Zaralek Caverns, and Emerald Dream.
- Add the Dragonflight banner emblem, teal styling, and expansion-specific progress bar to the report.
- Addon icon metadata.
- Repository validation workflow.
- Automated GitHub Release ZIP packaging.
- Project documentation, contribution guidance, security policy, and issue templates.
