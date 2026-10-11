# Alt Tracking Assistant 2.2.0

This update adds a Quest Log dashboard and a roster character panel to the Companion, with shared quests, recurring tasks, and character notes available in the addon too.

## Quest Log and To Do

Choose which characters to track, reorder them, and view progress in weekly, daily, and task columns. Add quests or tasks directly from the dashboard, reuse them across characters, and check off manual tasks without opening a character panel. Names show Level - Name on class-colored backgrounds.

The addon's Notes tab now separates automatic quest, achievement, and item tracking from manual tasks. Pick reset weekdays in either the addon or Companion: one day is Weekly, every day is Daily, and other combinations reset on the selected days. Resets use **11 a.m. fixed EST (UTC−5)**, including during daylight saving time. Leave every day unchecked for no reset.

Compact markers beside each title show [D] Daily, [W] Weekly, and priority [1] High, [2] Medium, or [3] Low. Removing an assignment affects one character; Delete to do removes it from every assigned character.

## Roster character panel

Click a roster character name to open **Info**, **To Do**, and **Notes**.

- **Info:** save a character profile with supported HTML formatting, a color picker, WoW weather image headers, and fonts including Skurri, Morpheus, and Friz Quadrata TT. The info icon lists supported HTML and CSS; full browser CSS is not supported.
- **To Do:** review automatic tracking and manual tasks, with compact pen, character-assignment, and X actions.
- **Notes:** add and edit addon Notes / History, grouped into collapsible years and days. Edits preserve the original date; pen and X buttons sit before each note.

## Improvements

Brown-and-gold WoW styling now extends throughout the Companion, including scrollbars, dropdowns, tab hover states, and compact action buttons. This release also improves scrolling, character-panel loading, profession snapshot retention, and task/note synchronization.

## Updating and syncing

Close the Companion and exit WoW before installing the ZIP. Copy its **AltTrackingAssistant** folder into your Retail **Interface/AddOns** folder, replacing the existing addon files. Your WoW SavedVariables and Companion database remain in their existing locations.

Start WoW and the updated Companion, then select the correct WoW folder. The addon scans tracked quests shortly after entering the world. After saving Companion changes, click the addon's **Rescan** button: it scans and reloads the UI to apply the new assignments and notes, showing a brief loading screen. Rescan cannot run in combat. Logout or `/reload` also writes addon data for the Companion to import.

The download includes the addon and Windows Companion together. No sign-in or browser runtime is required.
