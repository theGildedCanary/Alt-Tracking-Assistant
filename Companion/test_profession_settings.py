import unittest
import app
import roster_format

class ProfessionFormattingTests(unittest.TestCase):
    def test_legacy_purple_default_upgrades_to_blue(self):
        old = {"colors": {"professionProgress": "#331E53"}}
        upgraded = roster_format.normalize(old)
        self.assertEqual(upgraded["colors"]["professionProgress"], "#3F64B5")
        self.assertEqual(upgraded["professionBarVersion"], 1)
        self.assertEqual(roster_format.normalize(upgraded)["colors"]["professionProgress"], "#3f64b5")

    def test_custom_profession_colors_are_preserved(self):
        custom = roster_format.normalize({"colors": {"professionProgress": "#ABCDEF"}})
        self.assertEqual(custom["colors"]["professionProgress"], "#abcdef")
        custom["colors"]["professionProgress"] = "#331E53"
        self.assertEqual(roster_format.normalize(custom)["colors"]["professionProgress"], "#331e53")

    def test_formatting_controls_each_profession_column(self):
        fmt = roster_format.defaults()
        record = {"professions": {"primary": {"name": "Alchemy"}}}
        columns, rows = app.build_roster_grid([record], fmt)
        self.assertIn("Prof 1", [c.title for c in columns])
        for key in ("primary", "secondary", "archaeology", "fishing", "cooking"):
            spec = next(c for c in fmt["columns"] if c["key"] == key)
            spec["visible"] = False
            columns, rows = app.build_roster_grid([record, {}], fmt)
            self.assertNotIn(spec["title"], [c.title for c in columns])
            self.assertTrue(all(len(row) == len(columns) for row in rows))
            spec["visible"] = True
        columns, rows = app.build_roster_grid([record], fmt)
        self.assertEqual(rows[0][10].text, "Alchemy")

if __name__ == "__main__":
    unittest.main()
