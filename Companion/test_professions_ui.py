import sqlite3
import tkinter as tk
from tkinter import ttk
import unittest

import db
import roster_format
from professions_ui import ProfessionsTab, SpacedHeading, STATE_KEY, normalize_state, progress_tiers, profession_group, PROFESSION_GROUPS


class ProfessionsDashboardTests(unittest.TestCase):
    def test_live_color_and_font_changes(self):
        root = tk.Tk(); root.withdraw(); self.addCleanup(root.destroy)
        tab = ProfessionsTab(root, [{"guid": "a", "professions": ["171"]}])
        tab.load([{"guid": "a", "name": "Test", "professions": {"primary": {
            "name": "Alchemy", "skillLineID": 171, "expansions": [
                {"name": "Midnight Alchemy", "skillLevel": 50, "maxSkillLevel": 100}]}}}])
        self.assertEqual(tab.fmt["colors"]["professionProgress"], "#3F64B5")
        tab.expanded.add(("a", "171"))
        fmt = roster_format.defaults()
        fmt["colors"]["professionProgress"] = "#abcdef"
        fmt["font"].update(family="Arial", bodySize=18, titleSize=14, bold=False, titleBold=True)
        tab.set_format(fmt)
        self.assertEqual(tab.body_font.actual("size"), 18)
        self.assertEqual(tab.title_font.actual("size"), 14)
        self.assertEqual(tab.body_font.actual("weight"), "normal")
        self.assertIn(("a", "171"), tab.expanded)
        card = tab.details.inner.winfo_children()[0].winfo_children()[0]
        bar = next(child for frame in card.winfo_children() for child in frame.winfo_children()
                   if isinstance(child, tk.Canvas))
        root.update_idletasks()
        bar.event_generate("<Configure>", width=400, height=40)
        self.assertEqual(bar.kit, "alchemy")
        self.assertTrue(any(bar.type(item) == "image" for item in bar.find_all()))
        texts = [item for item in bar.find_all() if bar.type(item) == "text"]
        self.assertEqual(bar.itemcget(texts[-1], "font"), str(tab.body_font))

    def test_character_selection_persistence_and_removal(self):
        root = tk.Tk()
        root.withdraw()
        self.addCleanup(root.destroy)
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.executescript(db.SCHEMA)
        self.addCleanup(conn.close)
        records = [{"guid": guid, "name": "SameName", "realm": "Realm", "professions": {
            "primary": {"name": "Alchemy", "skillLineID": 171, "expansions": [
                {"name": "Midnight Alchemy", "skillLevel": 50, "maxSkillLevel": 100}]}}}
            for guid in ("Player-1", "Player-2")]
        tab = ProfessionsTab(root, on_save=lambda state: db.set_json(conn, STATE_KEY, state))
        tab.load(records)
        labels = list(tab.choices)
        self.assertEqual(len(labels), 2)
        tab.choice.set(next(label for label, guid in tab.choices.items() if guid == "Player-2"))
        tab.add_character()
        self.assertEqual(tab.state, [{"guid": "Player-2", "professions": []}])
        self.assertNotIn("Player-2", tab.choices.values())
        checks = [child for child in tab.sidebar.inner.winfo_children() if isinstance(child, ttk.Checkbutton)]
        self.assertEqual([check.cget("text") for check in checks], ["Alchemy"])
        checks[0].invoke()
        card = tab.details.inner.winfo_children()[0].winfo_children()[0]
        heading = next(child for child in card.winfo_children() if isinstance(child, SpacedHeading))
        self.assertEqual(heading.text, "+  ALCHEMY - SAMENAME")
        heading.invoke()
        self.assertIn(("Player-2", "171"), tab.expanded)
        root.update_idletasks()
        self.assertTrue(any(isinstance(child, tk.Canvas) for frame in card.winfo_children()
                            for child in frame.winfo_children()))
        saved = db.get_json(conn, STATE_KEY)
        reopened = ProfessionsTab(root, saved)
        reopened.load(records)
        self.assertEqual(reopened.state[0]["professions"], ["171"])
        self.assertFalse(reopened.expanded)
        reopened.load([{**records[1], "professions": {}}])
        self.assertEqual(reopened.state, saved)
        reopened.remove_character("Player-2")
        self.assertEqual(reopened.state, [])
        self.assertEqual(records[1]["professions"]["primary"]["name"], "Alchemy")

    def test_groups_and_empty_states(self):
        root = tk.Tk(); root.withdraw(); self.addCleanup(root.destroy)
        tab = ProfessionsTab(root)
        self.assertIn("click Add", tab.details.inner.winfo_children()[0].cget("text"))
        record = {"guid": "a", "name": "MixedCase", "professions": {
            "primary": {"name": "Mining", "skillLineID": 186},
            "secondary": {"name": "Alchemy", "skillLineID": 171},
            "cooking": {"name": "Cooking", "skillLineID": 185}}}
        tab.load([record]); tab.add_character()
        self.assertIn("No professions are currently being tracked", tab.details.inner.winfo_children()[0].cget("text"))
        header = tab.sidebar.inner.winfo_children()[0]
        name = next(child for child in header.winfo_children() if isinstance(child, SpacedHeading))
        self.assertEqual(name.text, "MIXEDCASE")
        for key in ("186", "171", "185"):
            tab.select_profession("a", key, True)
        sections = [child for child in tab.details.inner.winfo_children() if isinstance(child, ttk.LabelFrame)]
        self.assertEqual([section.cget("text") for section in sections], ["Primary", "Secondary", "Tertiary"])
        for section, expected in zip(sections, ("ALCHEMY", "MINING", "COOKING")):
            card = section.winfo_children()[0]
            heading = next(child for child in card.winfo_children() if isinstance(child, SpacedHeading))
            self.assertIn(expected, heading.text)
        for group, professions in PROFESSION_GROUPS.items():
            for skill_id, name in professions.items():
                self.assertEqual(profession_group("primary", {"skillLineID": skill_id, "name": "Localized"}), group)
                self.assertEqual(profession_group("primary", {"name": name}), group)

    def test_roster_highlights_only_tracked_character_professions(self):
        from app import build_roster_grid
        import theme
        fmt = roster_format.defaults()
        records = [{"guid": guid, "professions": {
            "primary": {"name": "Alchemy", "skillLineID": 171},
            "secondary": {"name": "Mining", "skillLineID": 186},
            "cooking": {"name": "Cooking", "skillLineID": 185}}} for guid in ("a", "b")]
        tracking = [{"guid": "a", "professions": ["171", "185"]}]
        columns, rows = build_roster_grid(records, fmt, profession_tracking=tracking)
        specs = [spec for spec in fmt["columns"] if spec["visible"]]
        for index, spec in enumerate(specs):
            if spec["key"] in ("primary", "cooking"):
                self.assertEqual((rows[0][index].bg, rows[0][index].fg), (theme.GOLD, "#000000"))
                self.assertNotEqual(rows[1][index].bg, theme.GOLD)
            elif spec["key"] == "secondary":
                self.assertNotEqual(rows[0][index].bg, theme.GOLD)
        _, cleared = build_roster_grid(records, fmt, profession_tracking=[])
        self.assertFalse(any(cell.bg == theme.GOLD for row in cleared for cell in row))

    def test_missing_data_and_expansion_order(self):
        self.assertEqual(progress_tiers("cooking", {}), [])
        self.assertEqual(progress_tiers("archaeology", {"maxSkillLevel": "unknown"}), [])
        names = ["Classic", "Outland", "Northrend", "Cataclysm", "Pandaria", "Draenor", "Legion",
                 "Kul Tiran", "Shadowlands", "Dragon Isles", "Khaz Algar", "Midnight"]
        profession = {"expansions": [{"name": name + " Cooking", "skillLevel": 10, "maxSkillLevel": 100}
                                     for name in names] + [{"name": "Unlearned", "maxSkillLevel": 0}]}
        self.assertEqual([tier["name"] for tier in progress_tiers("cooking", profession)],
                         [name + " Cooking" for name in reversed(names)])
        self.assertEqual(progress_tiers("archaeology", {"skillLevel": 20, "maxSkillLevel": 950})[0]["name"], "Overall skill")
        self.assertEqual(normalize_state([{}, {"guid": "a", "professions": ["171", "171", None]},
                                         {"guid": "a"}]), [{"guid": "a", "professions": ["171"]}])


if __name__ == "__main__":
    unittest.main()
