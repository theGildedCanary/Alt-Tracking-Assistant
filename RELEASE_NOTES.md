# Alt Tracking Assistant 2.2.2

October 13, 2026

This maintenance update improves item tracking compatibility with World of Warcraft Retail 12.1.5.

## Fixes

- Item-based progression checks now prefer the current `C_Item.GetItemCount` API, with a fallback to the older API when needed.
- Personal-bank and Warband-bank settings continue to apply to item checks, including Legion artifact tracking.

## Validation

- Lua 5.1 syntax checks passed, and all files listed in the addon load list were present.
- Quest Log, background scanning/combat deferral, and item-scanner regression tests passed.
- All 88 Companion tests passed. Some UI tests emitted cleanup warnings.
- Automated validation now runs scanner regression tests and checks local QuestSync.lua and NotesSync.lua syntax when those files are present.

Live in-game behavior still requires confirmation after reloading and rescanning.

## Updating

Close WoW and the Companion before replacing the addon files. After restarting WoW, open `/ata` and click **Rescan** outside combat to refresh the current character's snapshot. Your saved characters, tasks, profiles, and notes are retained.
