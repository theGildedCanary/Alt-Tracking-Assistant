import tkinter as tk
import unittest

from grid import Cell, Column, RosterGrid
from professions_ui import ScrollArea
from widgets import WoWScrollbar


class GridScrollTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.geometry('800x800')
        self.grid = RosterGrid(self.root)
        self.grid.pack(fill='both', expand=True)
        self.root.update()

    def tearDown(self):
        if self.grid._redraw_job is not None:
            self.grid.after_cancel(self.grid._redraw_job)
        self.root.destroy()

    def populate(self, count, columns=2):
        headings = [Column('Character', 100, frozen=True)]
        headings += [Column('Quest ' + str(i), 44, vertical=True) for i in range(columns)]
        rows = [[Cell(str(row))] + [Cell('Done') for _ in range(columns)] for row in range(count)]
        self.grid.set_data(headings, rows)
        self.root.update()

    def assert_aligned(self):
        self.root.update()
        self.assertEqual(self.grid.body.canvasy(0), self.grid.left.canvasy(0))
        self.assertEqual(self.grid.body.canvasx(0), self.grid.top.canvasx(0))

    def test_short_grid_cannot_scroll_rows_away_from_names(self):
        self.populate(2)
        for direction in (-3, 3, 30, -30):
            self.grid.body.yview_scroll(direction, 'units')
            self.grid.body.xview_scroll(direction, 'units')
            self.assert_aligned()
            self.assertEqual(self.grid.body.canvasy(0), 0)
            self.assertEqual(self.grid.body.canvasx(0), 0)

    def test_profession_scroll_area_keeps_short_content_at_top(self):
        self.grid.pack_forget()
        area = ScrollArea(self.root)
        area.pack(fill='both', expand=True)
        tk.Label(area.inner, text='Profession').pack()
        self.root.update()
        self.assertTrue(any(isinstance(child, WoWScrollbar) for child in area.winfo_children()))
        for direction in (-30, 30):
            area.canvas.yview_scroll(direction, 'units')
            self.root.update()
            self.assertEqual(area.canvas.canvasy(0), 0)
        self.root.geometry('500x500')
        self.root.update()
        self.assertEqual(area.canvas.canvasy(0), 0)

    def test_scrolling_resize_and_replacing_data_keep_panes_aligned(self):
        self.populate(80, 30)
        self.grid.body.yview_moveto(0.7)
        self.grid.body.xview_moveto(0.7)
        self.assert_aligned()
        self.assertGreater(self.grid.body.canvasy(0), 0)
        self.assertGreater(self.grid.body.canvasx(0), 0)
        self.root.geometry('500x500')
        self.assert_aligned()
        self.root.geometry('1100x1000')
        self.assert_aligned()
        self.populate(2)
        self.assert_aligned()
        self.assertEqual(self.grid.body.canvasy(0), 0)
        self.assertEqual(self.grid.body.canvasx(0), 0)


if __name__ == '__main__':
    unittest.main()
