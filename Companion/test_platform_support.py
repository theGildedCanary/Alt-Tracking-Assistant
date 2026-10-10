import importlib.util
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import app
from platform_support import data_dir, wheel_units, wow_dirs


class PlatformTests(unittest.TestCase):
    def test_mac_data_is_in_application_support(self):
        self.assertEqual(data_dir("darwin", "/Users/test", {"APPDATA": "/wrong"}),
                         Path("/Users/test/Library/Application Support/AltTrackingAssistantCompanion"))

    def test_windows_data_location_is_preserved(self):
        self.assertEqual(data_dir("win32", "C:/Users/test", {"APPDATA": "C:/Users/test/AppData/Roaming"}),
                         Path("C:/Users/test/AppData/Roaming/AltTrackingAssistantCompanion"))

    def test_detects_mac_install_and_saved_variables(self):
        with tempfile.TemporaryDirectory() as temporary:
            wow = Path(temporary) / "Applications" / "World of Warcraft"
            saved = wow / "_retail_" / "WTF" / "Account" / "TEST#1" / "SavedVariables" / app.SV_FILE
            saved.parent.mkdir(parents=True)
            saved.write_text("AltTrackingAssistantDB = {}", encoding="utf-8")
            with patch.object(app, "DEFAULT_WOW_DIRS", wow_dirs("darwin", temporary)):
                self.assertEqual(Path(app.detect_wow_dir()), wow)
            self.assertEqual(app.find_saved_variable_files(wow / "_retail_"), [saved])

    def test_wheels_and_trackpads(self):
        self.assertEqual(wheel_units(120, platform="win32"), -3)
        self.assertEqual(wheel_units(-240, multiplier=5, platform="win32"), 10)
        self.assertEqual(wheel_units(2, platform="darwin"), -2)
        self.assertEqual(wheel_units(-1, platform="darwin"), 1)
        self.assertEqual(wheel_units(0, platform="darwin"), 0)

    def test_portable_window_restore_keeps_window_visible(self):
        spec = importlib.util.spec_from_file_location("portable_window", Path(__file__).with_name("window_position.py"))
        module = importlib.util.module_from_spec(spec)
        with patch("sys.platform", "darwin"):
            spec.loader.exec_module(module)
        restored = []
        root = SimpleNamespace(winfo_screenwidth=lambda: 1440, winfo_screenheight=lambda: 900,
                               geometry=restored.append)
        self.assertTrue(module.restore(root, {"geometry": "1280x760+3000+2000"}))
        self.assertEqual(restored, ["1280x760+160+140"])
        self.assertFalse(module.restore(root, {"geometry": "invalid"}))
        self.assertFalse(module.restore(root, {"normal_rect": [0, 0, 1280, 760]}))


if __name__ == "__main__":
    unittest.main()
