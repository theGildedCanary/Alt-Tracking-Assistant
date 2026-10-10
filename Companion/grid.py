"""Spreadsheet-style grid drawn on canvases: frozen left columns, a frozen header, and scrolling everywhere else."""

import ctypes
import os
import sys
import tkinter as tk
from dataclasses import dataclass
from tkinter import font as tkfont
from tkinter import ttk

import theme

MIN_BAND_HEIGHT = 22
MIN_TITLE_HEIGHT = 90


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


@dataclass
class GridStyle:
    family: str = FAMILY
    body_size: int = 9
    title_size: int = 7
    title_bold: bool = True
    spacing: int = 2
    row_height: int = 24
    bg: str = theme.PANEL
    stripe: str = theme.PANEL_ALT
    line: str = theme.DIVIDER
    separator: str = theme.GOLD


def style_from_format(fmt):
    colors = fmt["colors"]
    return GridStyle(
        family=fmt["font"]["family"],
        body_size=fmt["font"]["bodySize"],
        title_size=fmt["font"]["titleSize"],
        title_bold=fmt["font"]["titleBold"],
        spacing=fmt["font"]["titleSpacing"],
        row_height=fmt["rowHeight"],
        bg=colors["background"],
        stripe=colors["stripe"] if fmt["stripes"] else colors["background"],
        line=colors["gridLine"],
        separator=colors["separator"],
    )


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
    separator_before: bool = False


@dataclass
class Cell:
    text: str = ""
    fg: str = theme.TEXT
    bg: str = ""
    bold: bool = True
    spacing: int = 0
    italic: bool = False
    text_runs: tuple = ()  # (text, font color) segments within a cell


class RosterGrid(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        self.style = GridStyle()
        self._make_fonts()
        self._visible_data = None
        self._redraw_job = None

        def make_canvas(**options):
            return tk.Canvas(self, bg=self.style.bg, highlightthickness=0, **options)

        self.band_height = MIN_BAND_HEIGHT
        self.title_height = MIN_TITLE_HEIGHT
        self.header_height = self.band_height + MIN_TITLE_HEIGHT
        self.corner = make_canvas(height=self.header_height)
        self.top = make_canvas(height=self.header_height, xscrollincrement=20)
        self.left = make_canvas(yscrollincrement=self.style.row_height)
        self.body = make_canvas(yscrollincrement=self.style.row_height, xscrollincrement=20)

        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self._yview)
        self.hsb = ttk.Scrollbar(self, orient="horizontal", command=self._xview)
        self.body.configure(yscrollcommand=self._on_yscroll, xscrollcommand=self._on_xscroll)

        self.corner.grid(row=0, column=0, sticky="nsew")
        self.top.grid(row=0, column=1, sticky="nsew")
        self.left.grid(row=1, column=0, sticky="nsew")
        self.body.grid(row=1, column=1, sticky="nsew")
        self.vsb.grid(row=1, column=2, sticky="ns")
        self.hsb.grid(row=2, column=1, sticky="ew")

        self.body.bind("<Configure>", self._schedule_redraw)
        self.left.bind("<Configure>", self._schedule_redraw)

        for canvas in (self.corner, self.top, self.left, self.body):
            canvas.bind("<MouseWheel>", self._on_wheel)
            canvas.bind("<Shift-MouseWheel>", self._on_shift_wheel)

    def _make_fonts(self):
        style = self.style
        family = style.family if style.family in set(tkfont.families(self)) else FAMILY
        self.f_body = tkfont.Font(root=self, family=family, size=style.body_size, weight="normal")
        self.f_bold = tkfont.Font(root=self, family=family, size=style.body_size, weight="bold")
        self.f_italic = tkfont.Font(
            root=self, family=family, size=style.body_size, weight="normal", slant="italic"
        )
        self.f_bold_italic = tkfont.Font(
            root=self, family=family, size=style.body_size, weight="bold", slant="italic"
        )
        self.f_title = tkfont.Font(
            root=self, family=family, size=style.title_size, weight="bold" if style.title_bold else "normal"
        )

    def _yview(self, *args):
        self.body.yview(*args)

    def _xview(self, *args):
        self.body.xview(*args)

    def _on_yscroll(self, first, last):
        self.vsb.set(first, last)
        self.left.yview_moveto(first)
        self._schedule_redraw()

    def _on_xscroll(self, first, last):
        self.hsb.set(first, last)
        self.top.xview_moveto(first)
        self._schedule_redraw()

    def _on_wheel(self, event):
        self.body.yview_scroll(-3 * (event.delta // 120 or (1 if event.delta > 0 else -1)), "units")

    def _on_shift_wheel(self, event):
        self.body.xview_scroll(-5 * (event.delta // 120 or (1 if event.delta > 0 else -1)), "units")

    def _autofit(self, columns, rows):
        """Size every column to its widest cell or title; widen the first column of a group if its title is wider."""
        spacing = self.style.spacing
        for index, column in enumerate(columns):
            content = max((self._cell_length(row[index]) for row in rows), default=0)
            if column.vertical:
                column.width = max(44, content + 20)
            else:
                column.width = max(content, self._spaced_length(column.title.upper(), spacing)) + 24
        longest = max((self._spaced_length(c.title.upper(), spacing) for c in columns if c.vertical), default=0)
        self.title_height = max(MIN_TITLE_HEIGHT, longest + 20)
        self.band_height = max(MIN_BAND_HEIGHT, self.f_bold.metrics("linespace") + 8)
        self.header_height = self.band_height + self.title_height
        groups = {}
        for column in columns:
            if column.group:
                groups.setdefault(column.group, []).append(column)
        for name, members in groups.items():
            shortfall = self.f_bold.measure(name.upper()) + 24 - sum(c.width for c in members)
            if shortfall > 0:
                members[0].width += shortfall

    def _cell_length(self, cell):
        if cell.italic:
            font = self.f_bold_italic if cell.bold else self.f_italic
        else:
            if cell.italic:
                font = self.f_bold_italic if cell.bold else self.f_italic
            else:
                font = self.f_bold if cell.bold else self.f_body
        return font.measure(cell.text) + cell.spacing * max(len(cell.text) - 1, 0)

    def _spaced_length(self, text, spacing):
        return sum(self.f_title.measure(ch) for ch in text) + spacing * max(len(text) - 1, 0)

    def set_data(self, columns, rows, style=None):
        if style is not None:
            self.style = style
            self._make_fonts()
        row_height = self.style.row_height
        for canvas in (self.corner, self.top, self.left, self.body):
            canvas.delete("all")
            canvas.configure(bg=self.style.bg)
        self.left.configure(yscrollincrement=row_height)
        self.body.configure(yscrollincrement=row_height)
        self._autofit(columns, rows)

        frozen = [c for c in columns if c.frozen]
        scrolling = [c for c in columns if not c.frozen]
        frozen_width = sum(c.width for c in frozen)
        scroll_width = sum(c.width for c in scrolling)
        body_height = len(rows) * row_height

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

        self._visible_data = (columns, rows, offsets, frozen_width)

        if frozen_width:
            self.corner.create_line(
                frozen_width - 1, 0,
                frozen_width - 1, self.header_height,
                fill=self.style.separator,
                width=2
            )

        self.body.yview_moveto(0)
        self.body.xview_moveto(0)
        self._schedule_redraw()

    def _schedule_redraw(self, event=None):
        if self._redraw_job is None:
            self._redraw_job = self.after(30, self._draw_visible)

    def _draw_visible(self):
        self._redraw_job = None
        if self._visible_data is None:
            return

        columns, rows, offsets, frozen_width = self._visible_data
        row_height = self.style.row_height

        # Keep the full scroll regions, but draw only visible cells.
        for canvas in (self.left, self.body):
            canvas.delete("all")

        top = self.body.canvasy(0)
        bottom = top + self.body.winfo_height()

        first_row = max(0, int(top // row_height) - 1)
        last_row = min(len(rows), int(bottom // row_height) + 2)

        visible_columns = []
        for col_index, column in enumerate(columns):
            canvas = self.left if column.frozen else self.body
            left = canvas.canvasx(0)
            right = left + canvas.winfo_width()
            x = offsets[col_index]

            if x + column.width >= left and x <= right:
                visible_columns.append((col_index, column, canvas, x))

        for row_index in range(first_row, last_row):
            row = rows[row_index]
            y = row_index * row_height
            stripe = (
                self.style.bg
                if row_index % 2 == 0
                else self.style.stripe
            )

            for col_index, column, canvas, x in visible_columns:
                self._draw_cell(
                    canvas, x, y, column, row[col_index], stripe
                )

        for _, column, canvas, x in visible_columns:
            if column.separator_before:
                canvas.create_line(x, first_row * row_height, x, last_row * row_height,
                                   fill=self.style.line, width=3)

        if frozen_width:
            self.left.create_line(
                frozen_width - 1, first_row * row_height,
                frozen_width - 1, last_row * row_height,
                fill=self.style.separator,
                width=2
            )

    def _draw_header(self, canvas, columns):
        style = self.style
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
                x, 0, x + span_width, self.band_height, fill=span[0].bg, outline=style.line
            )
            if group:
                canvas.create_text(
                    x + span_width / 2, self.band_height / 2, text=group.upper(), fill=span[0].fg, font=self.f_bold
                )
            x += span_width
            index = span_end + 1

        x = 0
        for column in columns:
            canvas.create_rectangle(
                x, self.band_height, x + column.width, self.header_height, fill=column.bg, outline=style.line
            )
            if column.vertical:
                self._draw_vertical_title(canvas, x + column.width / 2, column.title, column.title_fg)
            else:
                self._draw_spaced_title(canvas, x + column.width / 2, column.title, column.fg)
            x += column.width

        x = 0
        for column in columns:
            if column.separator_before:
                canvas.create_line(x, 0, x, self.header_height, fill=style.line, width=3)
            x += column.width

    def _draw_spaced_title(self, canvas, cx, title, color):
        text = title.upper()
        spacing = self.style.spacing
        left = cx - self._spaced_length(text, spacing) / 2
        cy = self.band_height + self.title_height / 2
        for ch in text:
            width = self.f_title.measure(ch)
            canvas.create_text(left + width / 2, cy, text=ch, fill=color, font=self.f_title)
            left += width + spacing

    def _draw_vertical_title(self, canvas, cx, title, color):
        text = title.upper()
        spacing = self.style.spacing
        center = self.band_height + self.title_height / 2
        y = center + self._spaced_length(text, spacing) / 2
        for ch in text:
            width = self.f_title.measure(ch)
            canvas.create_text(cx, y - width / 2, text=ch, angle=90, fill=color, font=self.f_title)
            y -= width + spacing

    def _draw_cell(self, canvas, x, y, column, cell, stripe):
        height = self.style.row_height
        canvas.create_rectangle(x, y, x + column.width, y + height, fill=cell.bg or stripe, outline=self.style.line)
        if not cell.text:
            return
        if cell.italic:
            font = self.f_bold_italic if cell.bold else self.f_italic
        else:
            font = self.f_bold if cell.bold else self.f_body
        if cell.text_runs:
            length = sum(font.measure(text) for text, _ in cell.text_runs)
            if column.align == "center":
                left = x + (column.width - length) / 2
            elif column.align == "e":
                left = x + column.width - 6 - length
            else:
                left = x + 6
            for text, color in cell.text_runs:
                canvas.create_text(left, y + height / 2, text=text, fill=color, font=font, anchor="w")
                left += font.measure(text)
        elif cell.spacing:
            length = self._cell_length(cell)
            left = x + (column.width - length) / 2 if column.align == "center" else x + 6
            for ch in cell.text:
                width = font.measure(ch)
                canvas.create_text(left + width / 2, y + height / 2, text=ch, fill=cell.fg, font=font)
                left += width + cell.spacing
        elif column.align == "center":
            canvas.create_text(x + column.width / 2, y + height / 2, text=cell.text, fill=cell.fg, font=font)
        elif column.align == "e":
            canvas.create_text(x + column.width - 6, y + height / 2, text=cell.text, fill=cell.fg, font=font, anchor="e")
        else:
            canvas.create_text(x + 6, y + height / 2, text=cell.text, fill=cell.fg, font=font, anchor="w")
