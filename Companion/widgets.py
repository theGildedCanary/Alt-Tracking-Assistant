"""Shared compact controls and category headings for the companion."""
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageDraw, ImageFont, ImageTk
import theme


def caption_image(master, text, color, square=False):
    text = str(text).upper()
    scale = master.winfo_fpixels("1p")
    point_size = 12 if text in ("▲", "▼") else 7
    font = ImageFont.truetype(str(Path(__file__).parent / "fonts/Montserrat.ttf"), max(1, round(point_size*scale)))
    font.set_variation_by_name("Bold")
    spacing = 2*scale
    widths = [font.getlength(char) for char in text]
    bounds = font.getbbox(text or "A")
    width = max(1, round(sum(widths)+spacing*max(0, len(text)-1)))
    height = bounds[3]-bounds[1]+4
    if square:
        width = height = max(16, round(12*scale))
    image = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(image)
    x = (width-sum(widths)-spacing*max(0, len(text)-1))/2
    y = (height-(bounds[3]-bounds[1]))/2-bounds[1]
    for char, advance in zip(text, widths):
        draw.text((x, y), char, font=font, fill=color)
        x += advance+spacing
    return ImageTk.PhotoImage(image, master=master)


class Button(ttk.Button):
    def __init__(self, parent, **kwargs):
        self.caption = kwargs.get("text", "")
        self.square = self.caption in ("▲", "▼", "x", "X", "×")
        kwargs["width"] = 0
        if self.square:
            kwargs["style"] = "Order.TButton"
        super().__init__(parent, **kwargs)
        self.refresh_art()

    def refresh_art(self):
        color = getattr(self.winfo_toplevel(), "_ata_caption_color", theme.GOLD)
        self._caption_image = caption_image(self, self.caption, color, self.square)
        super().configure(image=self._caption_image, compound="none", width=0)


class Section(ttk.LabelFrame):
    """A full-width shaded category banner above the existing content layout."""
    def __init__(self, parent, **kwargs):
        title = kwargs.pop("text", "")
        kwargs["text"] = title
        self.heading = tk.Canvas(parent, height=28, width=150, highlightthickness=0)
        kwargs["labelwidget"] = self.heading
        super().__init__(parent, **kwargs)
        self.title = title
        self.bind("<Configure>", self._draw_heading)
        self.bind("<Destroy>", self._cleanup)

    def _cleanup(self, event):
        if event.widget is self:
            self.heading.destroy()

    def refresh_art(self):
        self._draw_heading()

    def _draw_heading(self, event=None):
        colors = getattr(self.winfo_toplevel(), "_ata_colors", theme.UI_THEMES["WoW Mode"])
        width = max(150, self.winfo_width()-22)
        self.heading.configure(width=width, background=colors["background"])
        self.heading.delete("all")
        self.heading.create_rectangle(0, 0, width-1, 27, fill=colors["control"], outline=colors["border"])
        self._title_image = caption_image(self.heading, self.title, theme.GOLD if colors != theme.UI_THEMES["Light Mode"] else colors["text"])
        self.heading.create_image(14, 14, anchor="w", image=self._title_image)
