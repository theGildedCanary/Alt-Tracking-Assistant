"""Spreadsheet-style grid drawn on canvases: frozen left columns, a frozen header, and scrolling everywhere else."""

import ctypes
import os
import sys
import tkinter as tk
from dataclasses import dataclass
from tkinter import font as tkfont
from tkinter import ttk

import theme

BAND_HEIGHT = 22
MIN_TITLE_HEIGHT = 90
LETTER_SPACING = 2
ROW_HEIGHT = 24
def _load_font():
    """Register the bundled Montserrat for this process; fall back to Segoe UI if unavailable."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base, "fonts", "Montserrat.ttf")
    try:
        if os.path.exists(path) and ctypes.windll.gdi32.AddFontResourceExW(path, 0x10, 0):
            return "Montserrat"
    except (AttributeError, OSError):
        pass
    return "Segoe UI"


FAMILY = _load_font()
FONT = (FAMILY, 9)
FONT_BOLD = (FAMILY, 9, "bold")
FONT_TITLE = (FAMILY, 7, "bold")
FONT_VERT = (FAMILY, 7, "bold")


@dataclass
class Column:
    title: str
    width: int
    group: str = ""
    bg: str = theme.PANEL_ALT
    fg: str = theme.GOLD
    align: str = "w"
    frozen: bool = False
    vertical: bool = False
    title_fg: str = "#ffffff"


@dataclass
class Cell:
    text: str = ""
    fg: str = theme.TEXT
    bg: str = ""
    bold: bool = True
    spacing: int = 0


class RosterGrid(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        def make_canvas(**options):
            return tk.Canvas(self, bg=theme.PANEL, highlightthickness=0, **options)

        self.title_height = MIN_TITLE_HEIGHT
        self.header_height = BAND_HEIGHT + MIN_TITLE_HEIGHT
        self.corner = make_canvas(height=self.header_height)
        self.top = make_canvas(height=self.header_height, xscrollincrement=20)
        self.left = make_canvas(yscrollincrement=ROW_HEIGHT)
        self.body = make_canvas(yscrollincrement=ROW_HEIGHT, xscrollincrement=20)

        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self._yview)
        self.hsb = ttk.Scrollbar(self, orient="horizontal", command=self._xview)
        self.body.configure(yscrollcommand=self._on_yscroll, xscrollcommand=self._on_xscroll)

        self.corner.grid(row=0, column=0, sticky="nsew")
        self.top.grid(row=0, column=1, sticky="nsew")
        self.left.grid(row=1, column=0, sticky="nsew")
        self.body.grid(row=1, column=1, sticky="nsew")
        self.vsb.grid(row=1, column=2, sticky="ns")
        self.hsb.grid(row=2, column=1, sticky="ew")

        for canvas in (self.corner, self.top, self.left, self.body):
            canvas.bind("<MouseWheel>", self._on_wheel)
            canvas.bind("<Shift-MouseWheel>", self._on_shift_wheel)

    def _yview(self, *args):
        self.body.yview(*args)

    def _xview(self, *args):
        self.body.xview(*args)

    def _on_yscroll(self, first, last):
        self.vsb.set(first, last)
        self.left.yview_moveto(first)

    def _on_xscroll(self, first, last):
        self.hsb.set(first, last)
        self.top.xview_moveto(first)

    def _on_wheel(self, event):
        self.body.yview_scroll(-3 * (event.delta // 120 or (1 if event.delta > 0 else -1)), "units")

    def _on_shift_wheel(self, event):
        self.body.xview_scroll(-5 * (event.delta // 120 or (1 if event.delta > 0 else -1)), "units")

    def _autofit(self, columns, rows):
        """Size every column to its widest cell or title; widen the first column of a group if its title is wider."""
        body, title, band = (tkfont.Font(root=self, font=f) for f in (FONT, FONT_TITLE, FONT_BOLD))
        body_bold = band
        for index, column in enumerate(columns):
            content = max((self._cell_length(body, body_bold, row[index]) for row in rows), default=0)
            if column.vertical:
                column.width = max(44, content + 20)
            else:
                column.width = max(content, self._spaced_length(title, column.title)) + 24
        vert = tkfont.Font(root=self, font=FONT_VERT)
        longest = max((self._vertical_length(vert, c.title) for c in columns if c.vertical), default=0)
        self.title_height = max(MIN_TITLE_HEIGHT, longest + 20)
        self.header_height = BAND_HEIGHT + self.title_height
        groups = {}
        for column in columns:
            if column.group:
                groups.setdefault(column.group, []).append(column)
        for name, members in groups.items():
            shortfall = band.measure(name.upper()) + 24 - sum(c.width for c in members)
            if shortfall > 0:
                members[0].width += shortfall

    @staticmethod
    def _cell_length(font, bold_font, cell):
        used = bold_font if cell.bold else font
        return used.measure(cell.text) + cell.spacing * max(len(cell.text) - 1, 0)

    @staticmethod
    def _spaced_length(font, title):
        text = title.upper()
        return sum(font.measure(ch) for ch in text) + LETTER_SPACING * max(len(text) - 1, 0)

    @staticmethod
    def _vertical_length(font, title):
        text = title.upper()
        return sum(font.measure(ch) for ch in text) + LETTER_SPACING * max(len(text) - 1, 0)

    def set_data(self, columns, rows):
        self._autofit(columns, rows)
        for canvas in (self.corner, self.top, self.left, self.body):
            canvas.delete("all")

        frozen = [c for c in columns if c.frozen]
        scrolling = [c for c in columns if not c.frozen]
        frozen_width = sum(c.width for c in frozen)
        scroll_width = sum(c.width for c in scrolling)
        body_height = len(rows) * ROW_HEIGHT

        self.corner.configure(width=frozen_width, height=self.header_height)
        self.top.configure(height=self.header_height)
        self.left.configure(width=frozen_width)
        self.corner.configure(scrollregion=(0, 0, frozen_width, self.header_height))
        self.top.configure(scrollregion=(0, 0, scroll_width, self.header_height))
        self.left.configure(scrollregion=(0, 0, frozen_width, body_height))
        self.body.configure(scrollregion=(0, 0, scroll_width, body_height))

        self._draw_header(self.corner, frozen)
        self._draw_header(self.top, scrolling)

        x_frozen = x_scroll = 0
        offsets = {}
        for index, column in enumerate(columns):
            if column.frozen:
                offsets[index] = x_frozen
                x_frozen += column.width
            else:
                offsets[index] = x_scroll
                x_scroll += column.width

        for row_index, row in enumerate(rows):
            y = row_index * ROW_HEIGHT
            stripe = theme.PANEL if row_index % 2 == 0 else theme.PANEL_ALT
            for col_index, cell in enumerate(row):
                column = columns[col_index]
                canvas = self.left if column.frozen else self.body
                self._draw_cell(canvas, offsets[col_index], y, column, cell, stripe)

        if frozen_width:
            # Drawn after the cells so the separator runs the full height of the frozen columns.
            for canvas, height in ((self.corner, self.header_height), (self.left, body_height)):
                canvas.create_line(frozen_width - 1, 0, frozen_width - 1, height, fill=theme.GOLD, width=2)

        self.body.yview_moveto(0)
        self.body.xview_moveto(0)

    def _draw_header(self, canvas, columns):
        x = 0
        index = 0
        while index < len(columns):
            span_end = index
            while span_end + 1 < len(columns) and columns[span_end + 1].group == columns[index].group:
                span_end += 1
            span = columns[index : span_end + 1]
            span_width = sum(c.width for c in span)
            group = columns[index].group
            canvas.create_rectangle(
                x, 0, x + span_width, BAND_HEIGHT, fill=span[0].bg if group else theme.PANEL, outline=theme.DIVIDER
            )
            if group:
                canvas.create_text(x + span_width / 2, BAND_HEIGHT / 2, text=group.upper(), fill=span[0].fg, font=FONT_BOLD)
            x += span_width
            index = span_end + 1

        x = 0
        for column in columns:
            canvas.create_rectangle(
                x, BAND_HEIGHT, x + column.width, self.header_height, fill=column.bg, outline=theme.DIVIDER
            )
            if column.vertical:
                self._draw_vertical_title(canvas, x + column.width / 2, column.title, column.title_fg)
            else:
                self._draw_spaced_title(canvas, x + column.width / 2, column.title, column.fg)
            x += column.width

    def _draw_spaced_title(self, canvas, cx, title, color):
        font = tkfont.Font(root=self, font=FONT_TITLE)
        text = title.upper()
        left = cx - self._spaced_length(font, text) / 2
        cy = BAND_HEIGHT + self.title_height / 2
        for ch in text:
            width = font.measure(ch)
            canvas.create_text(left + width / 2, cy, text=ch, fill=color, font=FONT_TITLE)
            left += width + LETTER_SPACING

    def _draw_vertical_title(self, canvas, cx, title, color):
        font = tkfont.Font(root=self, font=FONT_VERT)
        text = title.upper()
        center = BAND_HEIGHT + self.title_height / 2
        y = center + self._vertical_length(font, text) / 2
        for ch in text:
            width = font.measure(ch)
            canvas.create_text(cx, y - width / 2, text=ch, angle=90, fill=color, font=FONT_VERT)
            y -= width + LETTER_SPACING

    def _draw_cell(self, canvas, x, y, column, cell, stripe):
        canvas.create_rectangle(
            x, y, x + column.width, y + ROW_HEIGHT, fill=cell.bg or stripe, outline=theme.DIVIDER
        )
        if not cell.text:
            return
        spec = FONT_BOLD if cell.bold else FONT
        if cell.spacing:
            font = tkfont.Font(root=self, font=spec)
            length = self._cell_length(font, font, cell)
            left = x + (column.width - length) / 2 if column.align == "center" else x + 6
            for ch in cell.text:
                width = font.measure(ch)
                canvas.create_text(left + width / 2, y + ROW_HEIGHT / 2, text=ch, fill=cell.fg, font=spec)
                left += width + cell.spacing
        elif column.align == "center":
            canvas.create_text(x + column.width / 2, y + ROW_HEIGHT / 2, text=cell.text, fill=cell.fg, font=spec)
        else:
            canvas.create_text(x + 6, y + ROW_HEIGHT / 2, text=cell.text, fill=cell.fg, font=spec, anchor="w")
