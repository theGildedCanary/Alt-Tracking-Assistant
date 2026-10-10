# Changelog

All notable changes to Alt Tracking Assistant will be documented in this file.

The project uses semantic versioning:

- **MAJOR** — incompatible or major architectural/release changes
- **MINOR** — new backwards-compatible features
- **PATCH** — backwards-compatible fixes and small corrections

## [2.1.0] - Unreleased

### Added

- Professions tab between Tracking and Notes, with five profession sections collapsed by default.
- Character profession snapshots and expansion skill progress bars for learned profession tiers.
- Automatic profession updates on skill changes and profession window updates; shared Archaeology skill progress.
- Companion roster profession names beside Class and vertical Archaeology, Fishing, and Cooking indicators, with database persistence and local exports.
- Companion Roster settings page with column visibility, order, titles, alignment, and Profession Highlight and Main Highlight toggles.
- Companion Roster expansion controls for custom block names, visibility, and layout order; Formatting lists expansion colors in the same order.
- Companion Roster tracker controls grouped by expansion, with custom names, visibility, and ordering within each block.
- Companion covenant color controls for covenant names and renown; removed the class background checkbox from Formatting.
- Restored the Expansions group box in Companion Tracking settings.
- Companion Professions dashboard with a GUID-based character picker, saved per-character profession selections, removable sidebar entries, and collapsible expansion progress bars.

## [2.0.0] - 2026-10-09

### Added

- Optional Windows companion with a roster spreadsheet and a persistent local character database.
- Local Excel and CSV exports, with optional automatic export after addon data changes.
- Companion controls for character mains, armor mains, True Main, and tracker visibility, synchronized to the addon on login or reload.
- Customizable roster formatting, light and dark themes, and saved window placement.
- Separate Windows companion download, with the executable placed in the main addon folder.

### Changed

- Keep exports local; remove Google sign-in and Google Sheets dependencies.
- Package a neutral settings sync file and exclude generated personal settings from Git tracking.
- Validate companion Python syntax alongside addon checks.

## [1.0.0] - 2026-10-08

### Added

- First public release.
- Add Warlords of Draenor, Mists of Pandaria, Cataclysm, and Classic expansion sections with their trackers, including garrison building checks and an AQ40 reputation progress bar.
- Remove expansion header icons.

## [0.1.0] - Unreleased

### Added

- Add Legion quest trackers, Class Hall quest detection, and automatic class-specific artifact counts from inventory and Void Storage.
- Show a zero baseline for manual count trackers, activate the Artifact count on adjustment, preserve class-specific maxima across character views, and retain Worth Its Weight completion.
- Add Battle for Azeroth introduction, foothold, Nazjatar, Mechagon, cloak, and Taptaf trackers.
- Add a Darkmoon Faire section with custom colors and move Silas' Secret Stash from Dragonflight.
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
- Add the The War Within Delve Belt tracker for quest 91009.
- Show the active Shadowlands covenant beside the covenant-review selector.
- Remove Shadowlands Covenant Campaign progress because completed chapters could not be detected reliably.
- Add an AddOn Options page segmented by expansion for controlling report tracker visibility.
- Keep the active Shadowlands covenant visible when the optional covenant selector is disabled, and show that covenant's Renown.
- Add selectable plate, mail, leather, and cloth armor mains to Shadowlands settings and highlight their active covenant in gold.
- Color the active covenant name using its covenant-specific color.
- Move Armor Mains into the account-wide Character Mains settings and refresh saved selections when the options page is shown.
- Keep options-page checkbox and character selector displays synchronized with SavedVariables while the page is open.
- Add independent Character Mains and Armor Mains modes.
- Highlight configured mains in the character header and roster summary.
- Preserve existing armor-main assignments when creating the new Character Mains configuration.
- Keep character-main and armor-main modes independent, and abbreviate faction slot labels to A/H.
- Split AddOn Options into an overview, Mains tabs, and four-column Expansion tracker pages.
- Arrange Class Mains by roster class order and add the requested faction/class selector layouts.
- Change expansion tracker settings to a three-column layout.
- Track Silas' Secret Stash by quest completion or detecting the stash item, retaining the completed state after the stash is sold.
- Add per-character manual tracker overrides under the Expansions options page.
- Recognize either quest 66221 or 72293 for the Dragonflight Intro Skip tracker.
- Show each character's approximate birth date using the date they earned the Level 10 achievement.
- Add a configurable True Main with a crown marker in the dashboard.
- Track the Dragonflight Elegant Canvas Brush achievement per character.
- Add the The War Within banner emblem, orange styling, and expansion-specific progress bar to the report.
- Add Dragonflight trackers for Silas' Secret Stash, Intro Skip, 5x Sparks, Forbidden Reach, Suffusion Camp, Zaralek Caverns, and Emerald Dream.
- Add Shadowlands covenant selection and renown tracking, the four-covenant renown milestone count, and Korthia, Zereth Mortis, and Helsworn Chest checks.
- Add the Dragonflight banner emblem, teal styling, and expansion-specific progress bar to the report.
- Addon icon metadata.
- Repository validation workflow.
- Automated GitHub Release ZIP packaging.
- Project documentation, contribution guidance, security policy, and issue templates.
