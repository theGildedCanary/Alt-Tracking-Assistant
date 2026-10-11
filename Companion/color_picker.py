"""Brown themed HSV color picker for HTML text colors."""
import colorsys
import math
import re
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import theme
from widgets import Button


def normalize_hex(value):
    value = value.strip().removeprefix('#')
    if not re.fullmatch(r'[0-9a-fA-F]{3}|[0-9a-fA-F]{6}', value):
        raise ValueError('Enter a 3 or 6 digit hex color.')
    if len(value) == 3:
        value = ''.join(char * 2 for char in value)
    return '#' + value.upper()


def hsv_hex(h, s, v):
    return '#%02X%02X%02X' % tuple(round(channel * 255) for channel in colorsys.hsv_to_rgb(h, s, v))


class ColorPicker(tk.Toplevel):
    def __init__(self, parent, initial, apply):
        super().__init__(parent, background=theme.PANEL)
        self.title('Text color')
        self.transient(parent.winfo_toplevel())
        self.resizable(False, False)
        self.apply_color = apply
        self.h, self.s, self.v = 0., 1., 1.
        self.hex_value = tk.StringVar(value=normalize_hex(initial))
        frame = ttk.Frame(self, padding=14)
        frame.pack()
        self.canvas = tk.Canvas(frame, width=260, height=260, bg=theme.PANEL, highlightthickness=0)
        self.canvas.grid(row=0, column=0, rowspan=5)
        self.preview = tk.Canvas(frame, width=90, height=54, bg=initial, highlightthickness=1,
                                 highlightbackground=theme.GOLD)
        self.preview.grid(row=0, column=1, columnspan=2, padx=(16, 0), sticky='ew')
        ttk.Label(frame, text='HEX').grid(row=1, column=1, padx=(16, 8))
        entry = ttk.Entry(frame, textvariable=self.hex_value, width=12)
        entry.grid(row=1, column=2)
        entry.bind('<Return>', lambda _: self.apply())
        self.rgb = tk.StringVar()
        ttk.Label(frame, textvariable=self.rgb).grid(row=2, column=1, columnspan=2, padx=(16, 0))
        self.message = tk.StringVar()
        ttk.Label(frame, textvariable=self.message, wraplength=140).grid(row=3, column=1, columnspan=2, padx=(16, 0))
        buttons = ttk.Frame(frame)
        buttons.grid(row=5, column=0, columnspan=3, sticky='e', pady=(12, 0))
        Button(buttons, text='Cancel', command=self.destroy).pack(side='right')
        Button(buttons, text='Apply', command=self.apply).pack(side='right', padx=8)
        ring = Image.new('RGBA', (260, 260))
        pixels = ring.load()
        for y in range(260):
            for x in range(260):
                dx, dy = x - 130, y - 130
                if 105 <= math.hypot(dx, dy) <= 128:
                    hue = (math.atan2(dy, dx) / (2 * math.pi)) % 1
                    pixels[x, y] = tuple(round(c * 255) for c in colorsys.hsv_to_rgb(hue, 1, 1)) + (255,)
        self.ring = ImageTk.PhotoImage(ring, master=self)
        self.canvas.create_image(0, 0, anchor='nw', image=self.ring)
        self.drag_mode = None
        self.canvas.bind('<Button-1>', self.press)
        self.canvas.bind('<B1-Motion>', self.drag)
        self.hex_value.trace_add('write', self.from_hex)
        self.from_hex()
        self.bind('<Escape>', lambda _: self.destroy())
        self.geometry(f'+{parent.winfo_rootx()+30}+{parent.winfo_rooty()+50}')
        self.grab_set()

    def from_hex(self, *_):
        try:
            color = normalize_hex(self.hex_value.get())
        except ValueError as error:
            self.message.set(str(error))
            return
        rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
        h, self.s, self.v = colorsys.rgb_to_hsv(*(c/255 for c in rgb))
        if self.s:
            self.h = h
        self.preview.configure(bg=color)
        self.rgb.set('RGB: %d, %d, %d' % rgb)
        self.message.set('Drag the ring for hue;\nuse the square for shade.')
        self.draw()

    def draw(self):
        self.canvas.delete('shade')
        art = Image.new('RGB', (144, 144))
        pixels = art.load()
        for y in range(144):
            for x in range(144):
                pixels[x, y] = tuple(round(c*255) for c in colorsys.hsv_to_rgb(self.h, x/143, 1-y/143))
        self.shade = ImageTk.PhotoImage(art, master=self)
        self.canvas.create_image(58, 58, anchor='nw', image=self.shade, tags='shade')
        angle = self.h * 2 * math.pi
        x, y = 130+116*math.cos(angle), 130+116*math.sin(angle)
        self.canvas.create_oval(x-5, y-5, x+5, y+5, outline=theme.GOLD, width=2, tags='shade')
        x, y = 58+143*self.s, 58+143*(1-self.v)
        self.canvas.create_oval(x-4, y-4, x+4, y+4, outline='#000000', width=3, tags='shade')
        self.canvas.create_oval(x-4, y-4, x+4, y+4, outline=theme.GOLD, width=1, tags='shade')

    def press(self, event):
        if 58 <= event.x <= 201 and 58 <= event.y <= 201:
            self.drag_mode = 'shade'
        elif 105 <= math.hypot(event.x-130, event.y-130) <= 130:
            self.drag_mode = 'hue'
        else:
            self.drag_mode = None
        self.drag(event)

    def drag(self, event):
        if self.drag_mode == 'hue':
            self.h = (math.atan2(event.y-130, event.x-130) / (2*math.pi)) % 1
        elif self.drag_mode == 'shade':
            self.s = min(1, max(0, (event.x-58)/143))
            self.v = min(1, max(0, 1-(event.y-58)/143))
        else:
            return
        self.hex_value.set(hsv_hex(self.h, self.s, self.v))

    def apply(self):
        try:
            color = normalize_hex(self.hex_value.get())
        except ValueError as error:
            self.message.set(str(error))
            return
        self.apply_color(color)
        self.destroy()
