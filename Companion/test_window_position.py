import tkinter as tk
import unittest
from unittest import mock
from ctypes import wintypes

import window_position as placement


class PopupPositionTests(unittest.TestCase):
    def test_centers_over_app_instead_of_nested_panel_and_recenters_after_move(self):
        root = tk.Tk()
        self.addCleanup(root.destroy)
        root.geometry('1000x700+100+100')
        root.update()
        panel = tk.Frame(root, width=200, height=100)
        panel.place(x=600, y=400)
        popup = tk.Toplevel(panel)
        popup.geometry('300x200')
        for position in ('1000x700+100+100', '1000x700+200+150'):
            root.geometry(position)
            root.update()
            self.assertTrue(placement.center_popup(popup))
            root.update()
            rects = []
            for window in (root, popup):
                rect = wintypes.RECT()
                placement.user32.GetWindowRect(placement.window_handle(window), placement.ctypes.byref(rect))
                rects.append(rect)
            parent, child = rects
            self.assertLessEqual(abs((parent.left + parent.right) - (child.left + child.right)), 1)
            self.assertLessEqual(abs((parent.top + parent.bottom) - (child.top + child.bottom)), 1)

    def test_negative_monitor_coordinates_and_work_area_clamping(self):
        dialog = mock.Mock()
        def rect(handle, target):
            values = (-1800, 100, -800, 800) if handle == 1 else (0, 0, 300, 200)
            target._obj.left, target._obj.top, target._obj.right, target._obj.bottom = values
            return True
        def monitor(handle, target):
            target._obj.rcWork = wintypes.RECT(*work_area)
            return True
        for work_area, expected in (((-1920, 0, 0, 1080), (-1450, 350)),
                                    ((-1400, 400, 0, 1080), (-1400, 400))):
            with mock.patch.object(placement, 'window_handle', side_effect=[1, 2]), \
                 mock.patch.object(placement.user32, 'GetWindowRect', side_effect=rect), \
                 mock.patch.object(placement.user32, 'GetMonitorInfoW', side_effect=monitor), \
                 mock.patch.object(placement.user32, 'SetWindowPos', return_value=True) as move:
                self.assertTrue(placement.center_popup(dialog))
                move.assert_called_once_with(2, None, *expected, 0, 0, 0x15)


if __name__ == '__main__':
    unittest.main()
