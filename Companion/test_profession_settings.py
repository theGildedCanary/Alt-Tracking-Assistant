import unittest
import app
import roster_format

class ProfessionFormattingTests(unittest.TestCase):
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
