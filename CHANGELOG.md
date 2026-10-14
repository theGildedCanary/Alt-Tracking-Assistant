# Changelog

All notable changes to Alt Tracking Assistant will be documented in this file.

The project uses semantic versioning:

- **MAJOR** — incompatible or major architectural/release changes
- **MINOR** — new backwards-compatible features
- **PATCH** — backwards-compatible fixes and small corrections

## [Unreleased]

### Added

- Aggro Ring tracking in Warlords of Draenor for item 113082 in bags, personal bank, or equipped gear, with matching Companion settings and column layout.

## [2.2.2] - 2026-10-13

### Fixed

- Item-based progression scans prefer `C_Item.GetItemCount` for Retail 12.1.5 compatibility, retaining the legacy fallback and existing personal/Warband bank scope.
- Updated Quest Log regression tests to match current reset snapshots and login/event scheduling.

### Added

- Regression coverage for current and legacy item APIs, bank scope, Legion artifact counts, and unavailable item APIs.
- Automated validation runs scanner regression tests and checks local QuestSync.lua and NotesSync.lua syntax when present.

### Validation

- Lua 5.1 syntax, addon load-list references, three scanner regression tests, and all 88 Companion tests passed. Some Companion UI tests emitted cleanup warnings; live in-game verification remains pending.

## [2.2.1] - 2026-10-11

### Fixed

- Recurring manual tasks reset while the app/addon stays open, even without saved-data changes or an open Notes panel. Existing reset deadlines are preserved when task metadata is edited. Reset time is corrected to 11 a.m. EDT (UTC−4); existing EST deadlines migrate automatically.


### Added

- Editable quest IDs in the dashboard quest popup and support for multiple alternate IDs on one task, with completion when any tracked variant is complete.
- Action Needed checkbox in the Companion character To Do panel. Checking it highlights that character's name on the Roster with a reddish maroon background; unchecking restores the usual formatting.
- Action Needed flags persist per character across app restarts and refreshes, independently of task completion.

## [2.2.0] - 2026-10-11

### Added

- Companion Quest Log with opt-in characters, saved character ordering, class-colored names in Level - Name format, and vertical nickname columns.
- Weekly, daily, and shared task columns with completion checkboxes directly in the dashboard; completion stays independent for each character.
- Quest and task creation from the dashboard, with nickname, notes, priority, and multiple-character assignments.
- Roster character panel with Info, To Do, and Notes tabs; selected roster names stay highlighted while the panel is open.
- Character Info editor with supported HTML formatting, an HTML help reference, a hex/color picker, and alphabetized WoW weather image headers. Bundled fonts include Montserrat, Skurri, Morpheus, and Friz Quadrata TT.
- Addon Notes / To Do automatic tracking using quest IDs, achievement IDs, or item IDs, separated from manual tasks.
- Weekday reset selections in the addon and Companion. All seven days count as Daily, one selected day as Weekly, and other combinations use those selected days. Resets occur at 11 a.m. fixed EST (UTC−5); selecting no days disables resets.
- Companion Notes tab with editable addon Notes / History, collapsible years and days with entry counts, and compact pen/X actions before each note. Editing preserves the original entry date.
- Separate options to remove a quest or task from one character or delete it from all assigned characters.

### Changed

- Character To Do details combine automatic items under Auto Tracking and show compact reset/priority markers after titles: [D], [W], [1] High, [2] Medium, and [3] Low.
- Quest status indicators use a circle for not picked up, empty checkbox for picked up or pending, checked checkbox for completed, ? for an unavailable scan, and — for an unassigned item.
- Companion uses the WoW theme throughout: brown backgrounds, gold borders, WoW scrollbars/dropdown arrows, and centered uppercase Montserrat tabs with hover highlights.
- Quest editor/assignment windows remember their placement. Removed player IDs and realms from Quest Log character labels.
- Rescan refreshes available character data and then reloads WoW's UI to load Companion edits and save updated snapshots; it is unavailable in combat.

### Fixed

- Quest scanning waits until after entering the world so login data and the character record are available.
- Quest/To Do checkbox updates avoid rebuilding the entire character panel or highlighting dashboard rows.
- Corrected Quest Log and Professions scrolling and preserved previously scanned profession tier information.
- Improved character-panel loading, heading spacing, text alignment, and supported HTML rendering, including horizontal rules, text transforms, padding, and justified paragraphs.
- Added timestamp-based merging and deletion tracking so old SavedVariables do not overwrite newer task/note edits or restore deleted items.
- Release packages include neutral AppSync.lua, QuestSync.lua, and NotesSync.lua templates, excluding personal settings, assignments, and history.

## [2.1.1] - 2026-10-10

### Changed

- Updated addon panels, rounded borders, muted gold accents, and active-only tab highlights to match the WoW-inspired appearance.
- Added Blizzard-style red action buttons and scrollbars, and warm roster summary colors.
- Added original profession-specific WoW progress bar artwork and fill animations to the addon and companion; corrected clipping, border layering, and text alignment, and added thin black text outlines for readability. Archaeology uses Blizzard's default artwork.
- Added Companion WoW Mode with warm panels, textured profession headings, and rounded tabs with a clearer selected gold fade.
- Added circular WoW-style Settings indicators, category header backdrops, clearer profession group separators, and compact square order buttons with larger arrows.
- Standardized action captions to bold 7-point uppercase with 2-point spacing, improved padding and contrast, and added a 2-point text inset to editable fields. Existing Pick color buttons are preserved.
- Added an italicized main-character row toggle under Settings → Roster → Highlights.
- Preserved custom roster colors while migrating the old default palette.

## [2.1.0] - 2026-10-10

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
