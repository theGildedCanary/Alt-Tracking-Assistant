import copy
import sqlite3
import re
import tempfile
import unittest
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from types import SimpleNamespace

import app
import db
import roster_format
import settings_sync as ss
from settings_ui import SettingsTab


class SettingsRefreshTests(unittest.TestCase):
    def test_shared_tracker_catalog_matches_addon(self):
        root = Path(__file__).resolve().parent.parent
        for expansion, _, checks in ss.TRACKERS:
            matches = []
            for source in (root / "Features").glob("*.lua"):
                text = source.read_text(encoding="utf-8-sig")
                marker = "ATA.trackerDefinitions." + expansion + " ="
                if marker in text:
                    block = text.split(marker, 1)[1].split("scan = function", 1)[0]
                    matches = re.findall(r'id\s*=\s*"([^"]+)"', block)
                    break
            self.assertEqual(matches, [key for key, _ in checks], expansion)

    def test_actual_tracking_widgets_refresh_without_restart(self):
        root = tk.Tk()
        root.withdraw()
        self.addCleanup(root.destroy)
        tab = SettingsTab(root, lambda settings: 1, lambda: None, lambda fmt: None,
                          roster_format.normalize({}), lambda mode: None, "Light Mode")

        def controls(widget):
            result = []
            for child in widget.winfo_children():
                if isinstance(child, ttk.Checkbutton):
                    result.append(child)
                result.extend(controls(child))
            return result

        count = sum(len(checks) for _, _, checks in ss.TRACKERS)
        for enabled in (False, True, False):
            settings = ss.normalize({"trackedItems": {
                expansion: {key: enabled for key, _ in checks}
                for expansion, _, checks in ss.TRACKERS}})
            tab.load([], settings, False)
            checks = controls(tab.tracking_pages["Expansions"])
            self.assertEqual(len(checks), count)
            self.assertTrue(all(bool(root.getvar(check.cget("variable"))) == enabled for check in checks))

        checks[0].invoke()
        self.assertTrue(tab.dirty)
        tab.load([], ss.normalize({}), False)
        refreshed = controls(tab.tracking_pages["Expansions"])
        self.assertTrue(bool(root.getvar(refreshed[0].cget("variable"))))
        self.assertTrue(tab.dirty)

    def test_every_tracker_imports_and_updates_display(self):
        aliases = {("shadowlands", "covenant"): "activeCovenantID",
                   ("shadowlands", "renown"): "renownByCovenant"}
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            source = Path(folder) / "AltTrackingAssistant.lua"
            conn = sqlite3.connect(":memory:")
            conn.row_factory = sqlite3.Row
            conn.executescript(db.SCHEMA)
            self.addCleanup(conn.close)
            for expansion, _, checks in ss.TRACKERS:
                for key, _ in checks:
                    with self.subTest(expansion=expansion, setting=key):
                        for enabled in (False, True):
                            settings = ss.normalize({"trackedItems": {expansion: {key: enabled}}})
                            source.write_text("AltTrackingAssistantDB = " + ss._lua_value({"settings": settings}), encoding="utf-8")
                            imported, pending = ss.effective_settings(conn, [source])
                            self.assertEqual(imported, settings)
                            self.assertFalse(pending)
                            tab = self.make_tab()
                            previous = copy.deepcopy(settings)
                            previous["trackedItems"][expansion][key] = not enabled
                            SettingsTab.load(tab, [], previous, False)
                            SettingsTab.load(tab, [], imported, pending)
                            self.assertEqual(tab.settings, settings)
                            display_key = aliases.get((expansion, key), key)
                            records = [{"guid": "one", "progress": {expansion: {display_key: True}}}]
                            columns, _ = app.build_roster_grid(records, roster_format.normalize({}), imported)
                            shown, _ = app.build_roster_grid(records, roster_format.normalize({}), ss.normalize({}))
                            self.assertEqual(len(columns), len(shown) - (0 if enabled else 1))

                            draft = copy.deepcopy(previous)
                            draft["characterMains"]["trueMainEnabled"] = True
                            merged, conflicts = ss.merge_refresh(previous, draft, imported)
                            self.assertEqual(merged["trackedItems"][expansion][key], enabled)
                            self.assertTrue(merged["characterMains"]["trueMainEnabled"])
                            self.assertFalse(conflicts)

    @staticmethod
    def make_tab():
        return SimpleNamespace(characters=[], settings=ss.normalize({}), baseline=ss.normalize({}),
                               conflicts=[], dirty=False, loaded=False,
                               status=SimpleNamespace(set=lambda value: None), _build=lambda: None)

    def test_dirty_refresh_merges_and_reports_conflicts(self):
        tab = self.make_tab()
        initial = ss.normalize({})
        initial["characterMains"]["selections"]["single"] = "old"
        SettingsTab.load(tab, [], initial, False)
        tab.dirty = True
        tab.settings["characterMains"]["selections"]["single"] = "local"
        incoming = copy.deepcopy(initial)
        incoming["characterMains"]["selections"]["single"] = "remote"
        incoming["trackedItems"] = {"classic": {"aq40": False}}
        SettingsTab.load(tab, [], incoming, False)
        self.assertEqual(tab.settings["characterMains"]["selections"]["single"], "local")
        self.assertFalse(tab.settings["trackedItems"]["classic"]["aq40"])
        self.assertEqual(tab.conflicts, ["characterMains.selections.single"])
        SettingsTab.load(tab, [], incoming, False)
        self.assertEqual(tab.settings["characterMains"]["selections"]["single"], "local")
        tab.dirty = tab.loaded = False
        SettingsTab.load(tab, [], incoming, False)
        self.assertEqual(tab.settings, incoming)

    def test_main_fields_refresh_without_losing_other_edits(self):
        changes = [("characterMode", mode) for mode, _ in ss.CHARACTER_MODES]
        changes += [("armorMode", mode) for mode, _ in ss.ARMOR_MODES]
        changes += [("trueMainEnabled", True)]
        changes += [("selections", {slot: "new"}) for mode, _ in ss.CHARACTER_MODES
                    for slot, *_ in ss.character_slots(mode)]
        changes += [("selections", {slot: "new"}) for mode, _ in ss.ARMOR_MODES
                    for slot, *_ in ss.armor_slots(mode)]
        changes += [("selections", {"trueMain": "new"})]
        for field, value in changes:
            with self.subTest(field=field, value=value):
                old = ss.normalize({})
                draft = copy.deepcopy(old)
                draft["trackedItems"] = {"classic": {"aq40": False}}
                incoming = copy.deepcopy(old)
                incoming["characterMains"][field] = value
                merged, conflicts = ss.merge_refresh(old, draft, incoming)
                self.assertEqual(merged["characterMains"][field], value)
                self.assertFalse(merged["trackedItems"]["classic"]["aq40"])
                self.assertFalse(conflicts)

    def test_pending_settings_yield_after_addon_acknowledgement(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            conn = sqlite3.connect(":memory:")
            conn.row_factory = sqlite3.Row
            conn.executescript(db.SCHEMA)
            self.addCleanup(conn.close)
            source = Path(folder) / "AltTrackingAssistant.lua"
            remote = ss.normalize({"trackedItems": {"classic": {"aq40": False}}})
            db.set_json(conn, ss.PENDING_KEY, {**ss.normalize({}), "rev": 10})
            for revision, pending in ((9, True), (10, False), (11, False)):
                source.write_text("AltTrackingAssistantDB = " + ss._lua_value({"settings": remote, "appSyncRev": revision}), encoding="utf-8")
                settings, waiting = ss.effective_settings(conn, [source])
                self.assertEqual(waiting, pending)
                self.assertEqual(settings, ss.normalize({}) if pending else remote)


if __name__ == "__main__":
    unittest.main()


