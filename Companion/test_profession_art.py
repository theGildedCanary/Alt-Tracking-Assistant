import unittest
import tkinter as tk

from profession_art import KITS, asset, frame_count, manifest, profession_kit, render_bar_image, scaled_fill, NativeProfessionBar


class ProfessionArtworkTests(unittest.TestCase):
    def test_every_supported_profession_has_original_artwork(self):
        for skill, kit in KITS.items():
            with self.subTest(kit=kit):
                self.assertEqual(profession_kit({"skillLineID": str(skill)}), kit)
                sheet, info = asset("skillbar_fill_flipbook_" + kit)
                self.assertGreater(frame_count(kit), 1)
                self.assertEqual(sheet.size, (info["width"], info["height"]))
                self.assertGreater(info["sourceFileDataID"], 0)
                self.assertEqual(len(info["sourceSHA256"]), 64)
                w, h = sheet.width // info["columns"], sheet.height // info["rows"]
                self.assertTrue(scaled_fill(kit, w, h, 1).tobytes() == sheet.crop((w, 0, 2*w, h)).tobytes())

    def test_original_colors_and_fraction_clamping(self):
        alchemy = render_bar_image("alchemy", 451, 29, .5)
        tailoring = render_bar_image("tailoring", 451, 29, .5)
        self.assertNotEqual(alchemy.tobytes(), tailoring.tobytes())
        self.assertEqual(render_bar_image("alchemy", 451, 29, -1).tobytes(),
                         render_bar_image("alchemy", 451, 29, 0).tobytes())
        self.assertEqual(render_bar_image("alchemy", 451, 29, 2).tobytes(),
                         render_bar_image("alchemy", 451, 29, 1).tobytes())
        self.assertEqual(profession_kit({"skillLineID": 794}), "defaultblue")
        self.assertEqual(manifest()["build"], "12.1.0.69933")

    def test_hidden_bar_cancels_animation_callback(self):
        root = tk.Tk(); root.withdraw(); self.addCleanup(root.destroy)
        bar = NativeProfessionBar(root, {"skillLineID": 171},
                                  {"name": "Alchemy", "skillLevel": 58, "maxSkillLevel": 100},
                                  29, "TkDefaultFont", "#181612")
        bar._timer = bar.after(1000, lambda: None)
        callback = bar._timer
        bar._stop()
        self.assertIsNone(bar._timer)
        self.assertNotIn(callback, root.tk.call("after", "info"))

    def test_fill_and_flare_stay_inside_scaled_border(self):
        for width in (451, 1000):
            inset = round(width*5/451)
            empty = render_bar_image("alchemy", width, 29, 0)
            for fraction in (.001, .5, 1):
                rendered = render_bar_image("alchemy", width, 29, fraction)
                for bounds in ((0, 0, inset, 29), (width-inset, 0, width, 29),
                               (0, 0, width, 3), (0, 21, width, 29)):
                    self.assertEqual(rendered.crop(bounds).tobytes(), empty.crop(bounds).tobytes())


if __name__ == "__main__":
    unittest.main()
