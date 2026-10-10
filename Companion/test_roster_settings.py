import tkinter as tk
import unittest

import app
import roster_format as rf
import settings_sync
from settings_ui import SettingsTab


class RosterSettingsTests(unittest.TestCase):
    def test_order_normalization_and_legacy_highlight(self):
        fmt = rf.normalize({"expansionOrder": ["classic", "classic", {}, "unknown"], "boldMainRows": False})
        self.assertEqual(fmt["expansionOrder"][0], "classic")
        self.assertEqual(len(fmt["expansionOrder"]), len(set(fmt["expansionOrder"])))
        self.assertFalse(fmt["mainHighlight"])

    def test_roster_highlights_and_expansion_order(self):
        fmt = rf.defaults()
        fmt["font"]["bold"] = False
        record = {"guid": "a", "name": "Main", "isMain": True,
                  "professions": {"primary": {"name": "Alchemy", "skillLineID": 171}}}
        tracking = [{"guid": "a", "professions": ["171"]}]
        columns, rows = app.build_roster_grid([record], fmt, profession_tracking=tracking)
        self.assertEqual(rows[0][5].fg, fmt["colors"]["mainName"])
        self.assertTrue(all(cell.bold for cell in rows[0]))
        self.assertTrue(rows[0][10].bg)
        fmt.update(mainHighlight=False, professionHighlight=False)
        fmt["expansionOrder"].remove("classic")
        fmt["expansionOrder"].insert(0, "classic")
        columns, rows = app.build_roster_grid([record], fmt, profession_tracking=tracking)
        self.assertEqual(rows[0][5].fg, fmt["colors"]["text"])
        self.assertFalse(any(cell.bold for cell in rows[0]))
        self.assertFalse(rows[0][10].bg)
        self.assertEqual(columns[len(fmt["columns"])].group, app.GROUP_TITLES["classic"])

    def test_expansion_names_visibility_and_persistence(self):
        fmt = rf.defaults()
        fmt["expansionTitles"].update(midnight="Current", theWarWithin="Current")
        fmt["expansionVisible"]["darkmoonFaire"] = False
        fmt["expansionOrder"].remove("classic")
        fmt["expansionOrder"].insert(0, "classic")
        fmt = rf.normalize(fmt)
        columns, rows = app.build_roster_grid([{"progress": {"darkmoonFaire": {"extra": True}}}], fmt)
        trackers = columns[len(fmt["columns"]):]
        self.assertEqual(trackers[0].group_key, "classic")
        self.assertFalse(any(c.group_key == "darkmoonFaire" for c in trackers))
        self.assertEqual({c.group_key for c in trackers if c.group == "Current"}, {"midnight", "theWarWithin"})
        self.assertTrue(all(len(row) == len(columns) for row in rows))
        invalid = rf.normalize({"expansionTitles": {"midnight": 1}, "expansionVisible": {"classic": "no"}})
        self.assertEqual(invalid["expansionTitles"]["midnight"], rf.defaults()["expansionTitles"]["midnight"])
        self.assertTrue(invalid["expansionVisible"]["classic"])

    def test_tracker_names_visibility_order_and_normalization(self):
        fmt = rf.defaults()
        specs = fmt["trackerColumns"]["midnight"]
        moved = specs.pop(2)
        moved["title"] = "Custom Skip"
        specs.insert(0, moved)
        specs[1]["visible"] = False
        fmt = rf.normalize(fmt)
        columns, rows = app.build_roster_grid([{}], fmt)
        self.assertEqual([c.title for c in columns if c.group_key == "midnight"],
                         ["Custom Skip", "Crafters Needed", "Coil Isle Skip"])
        self.assertEqual(len(rows[0]), len(columns))
        invalid = rf.normalize({"trackerColumns": {"midnight": [
            {"key": "coilIsleSkip", "title": "", "visible": "no"},
            {"key": "coilIsleSkip"}, {"key": []}, {"key": "aq40"}]}})
        self.assertEqual(len(invalid["trackerColumns"]["midnight"]), 4)
        self.assertEqual(invalid["trackerColumns"]["midnight"][0]["title"], "Coil Isle Skip")
        self.assertTrue(invalid["trackerColumns"]["midnight"][0]["visible"])

    def test_covenant_colors_apply_to_names_and_renown(self):
        fmt = rf.normalize({"covenantColors": {"1": "#123456", "2": "#654321", "3": "invalid"}})
        self.assertEqual(fmt["covenantColors"]["3"], rf.defaults()["covenantColors"]["3"])
        records = [{"progress": {"shadowlands": {"activeCovenantID": 1,
                    "renownByCovenant": {"1": 80, 2: 50}}}},
                   {"progress": {"shadowlands": {"activeCovenantID": 2,
                    "renownByCovenant": [20, 30, 40, 50]}}}]
        columns, rows = app.build_roster_grid(records, fmt)
        covenant = next(i for i, c in enumerate(columns) if c.group_key == "shadowlands" and c.title == "Covenant")
        renown = next(i for i, c in enumerate(columns) if c.group_key == "shadowlands" and c.title == "Renown")
        self.assertEqual(rows[0][covenant].fg, "#123456")
        self.assertEqual(rows[1][covenant].fg, "#654321")
        for row in rows:
            self.assertEqual(row[renown].text_runs[0][1], "#123456")
            self.assertEqual(row[renown].text_runs[2][1], "#654321")

    def test_settings_pages_share_edits(self):
        root = tk.Tk()
        root.withdraw()
        self.addCleanup(root.destroy)
        tab = SettingsTab(root, lambda _: 0, lambda: None, lambda _: None,
                          rf.defaults(), lambda _: None, "Dark Mode")
        tab.load([], settings_sync.normalize({}), False)
        self.assertIn("Roster", tab.pages)
        self.assertEqual(tab.tracking_pages["Expansions"].cget("text"), "Expansions")
        self.assertIs(tab.roster_panel.fmt, tab.format_panel.fmt)
        tab.roster_panel._set(("mainHighlight",), False)
        tab.roster_panel._move_expansion(0, 1)
        self.assertFalse(tab.format_panel.fmt["mainHighlight"])
        self.assertEqual(tab.roster_panel.fmt["expansionOrder"][0], "midnight")
        headings = [child.cget("text") for child in tab.format_panel.expansions_box.winfo_children()
                    if isinstance(child, tk.ttk.Label)]
        self.assertNotIn("Order", headings)
        tab.roster_panel._set(("expansionTitles", "midnight"), "Newest")
        tab.roster_panel._set(("expansionVisible", "classic"), False)
        original_other = list(tab.roster_panel.fmt["trackerColumns"]["legion"])
        tab.roster_panel._move_tracker("midnight", 0, 1)
        self.assertEqual(tab.roster_panel.fmt["trackerColumns"]["midnight"][0]["key"], "craftersNeeded")
        self.assertEqual(tab.roster_panel.fmt["trackerColumns"]["legion"], original_other)
        tab.roster_panel._move_tracker("midnight", 0, -1)
        self.assertEqual(tab.roster_panel.fmt["trackerColumns"]["midnight"][0]["key"], "craftersNeeded")
        tab.format_panel._reset()
        self.assertEqual(tab.roster_panel.fmt["trackerColumns"]["midnight"][0]["key"], "craftersNeeded")
        self.assertEqual(tab.roster_panel.fmt["expansionTitles"]["midnight"], "Newest")
        self.assertFalse(tab.roster_panel.fmt["expansionVisible"]["classic"])
        self.assertEqual(tab.roster_panel.fmt["expansionOrder"][0], "midnight")
        self.assertFalse(tab.roster_panel.fmt["mainHighlight"])


if __name__ == "__main__":
    unittest.main()
