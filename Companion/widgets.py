"""Shared compact controls and category headings for the companion."""
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageDraw, ImageFont, ImageTk
import theme


def style_main_tabs(notebook, point_size=8, user_icon=False, fit_labels=False):
    """Centered Montserrat captions with point-based tracking and active weight."""
    labels = {tab: notebook.tab(tab, 'text').upper() for tab in notebook.tabs()}
    notebook._hover_tab = None
    def refresh(event=None):
        scale = notebook.winfo_fpixels('1p')
        fonts = {}
        for weight in ('Regular', 'Bold'):
            font = ImageFont.truetype(str(Path(__file__).parent / 'fonts/Montserrat.ttf'), round(point_size*scale))
            font.set_variation_by_name(weight)
            fonts[weight] = font
        spacing = 2*scale
        width = round(max(sum(fonts['Bold'].getlength(c) for c in text) + spacing*(len(text)-1)
                          for text in labels.values()) + (26 if user_icon else 12)*scale)
        height = round(16*scale)
        images = []
        for tab, text in labels.items():
            active = tab == notebook.select()
            highlighted = active or tab == notebook._hover_tab
            font = fonts['Bold' if active else 'Regular']
            length = sum(font.getlength(c) for c in text) + spacing*(len(text)-1)
            icon = user_icon and text in ('CHARACTER INFO', 'INFO')
            icon_width = 10*scale if icon else 0
            tab_width = round(length + icon_width + 20*scale) if fit_labels else width
            bounds = font.getbbox(text)
            art = Image.new('RGBA', (tab_width, height))
            draw = ImageDraw.Draw(art)
            x, y = (tab_width-length-icon_width)/2 + icon_width, (height-bounds[3]+bounds[1])/2-bounds[1]
            for char in text:
                draw.text((x, y), char, font=font, fill=theme.GOLD if highlighted else theme.MUTED_TEXT)
                x += font.getlength(char)+spacing
            if icon:
                cx = (tab_width-length-icon_width)/2 + 3*scale
                cy = height/2
                color = theme.GOLD if highlighted else theme.MUTED_TEXT
                draw.ellipse((cx-1.6*scale, cy-4*scale, cx+1.6*scale, cy-.8*scale), fill=color)
                draw.rounded_rectangle((cx-3.2*scale, cy, cx+3.2*scale, cy+4*scale), radius=1.6*scale, fill=color)
            image = ImageTk.PhotoImage(art, master=notebook)
            images.append(image)
            notebook.tab(tab, text=text, image=image, compound='none')
        notebook._caption_images = images
    notebook.refresh_art = refresh
    if fit_labels:
        style = ttk.Style(notebook)
        root = notebook.winfo_toplevel()
        if hasattr(root, '_ata_theme_images'):
            if 'Character.tab' not in style.element_names():
                assets = Path(__file__).parent / 'assets' / 'theme'
                cropped = []
                for filename in ('TabInactive.png', 'TabActive.png'):
                    art = Image.open(assets / filename)
                    cropped.append(ImageTk.PhotoImage(art.crop((0, 0, art.width, art.height-6)), master=root))
                inactive = Image.open(assets / 'TabInactive.png').convert('RGBA')
                active = Image.open(assets / 'TabActive.png').convert('RGBA')
                hover = Image.blend(inactive, active, .45)
                cropped.append(ImageTk.PhotoImage(hover.crop((0, 0, hover.width, hover.height-6)), master=root))
                root._character_tab_art = cropped
                style.element_create('Character.tab', 'image', cropped[0], ('selected', cropped[1]), ('active', '!selected', cropped[2]),
                                     border=(6, 6, 6, 0), width=1, sticky='nsew')
            style.layout('Character.TNotebook.Tab', [('Character.tab', {
                'sticky': 'nsew', 'children': [('Notebook.label', {'sticky': 'nsew'})]})])
        style.configure('Character.TNotebook.Tab', padding=0)
        style.configure('Character.TNotebook', tabmargins=(0, 2, 0, 0))
        notebook.configure(style='Character.TNotebook')
    def hover(event=None):
        tab = None
        if event is not None:
            try:
                tab = notebook.tabs()[notebook.index(f'@{event.x},{event.y}')]
            except tk.TclError:
                pass
        if tab == notebook.select():
            tab = None
        if tab != notebook._hover_tab:
            notebook._hover_tab = tab
            refresh()
    notebook.bind('<Motion>', hover, add='+')
    notebook.bind('<Leave>', lambda _: hover(), add='+')
    notebook.bind('<<NotebookTabChanged>>', refresh, add='+')
    refresh()


class WoWScrollbar(tk.Canvas):
    """Blizzard-style arrow buttons, dark track and beveled metal thumb."""
    def __init__(self, parent, orient='vertical', command=None, **kwargs):
        self.vertical = orient == 'vertical'
        self.command = command
        self.first, self.last = 0.0, 1.0
        self.drag = None
        super().__init__(parent, width=18, height=18, bg='#0e0d0a',
                         borderwidth=0, highlightthickness=0, **kwargs)
        self.bind('<Configure>', self._draw)
        self.bind('<Button-1>', self._press)
        self.bind('<B1-Motion>', self._motion)
        self.bind('<ButtonRelease-1>', lambda _: setattr(self, 'drag', None))

    def set(self, first, last):
        self.first, self.last = float(first), float(last)
        self._draw()

    def _geometry(self):
        length = self.winfo_height() if self.vertical else self.winfo_width()
        track = max(1, length - 36)
        thumb = min(track, max(24, track * (self.last - self.first)))
        travel = track - thumb
        start = 18 + travel * self.first / max(1e-9, 1 - (self.last - self.first))
        return length, thumb, travel, start

    def _draw(self, event=None):
        self.delete('all')
        length, thumb, _, start = self._geometry()
        def box(a, b, fill):
            coords = (2, a, 16, b) if self.vertical else (a, 2, b, 16)
            self.create_rectangle(*coords, fill=fill, outline='#8c7960')
            x1, y1, x2, y2 = coords
            self.create_line(x1+1, y2-1, x1+1, y1+1, x2-1, y1+1, fill='#bdac88')
            self.create_line(x2-1, y1+1, x2-1, y2-1, x1+1, y2-1, fill='#30291e')
        box(1, 17, '#514838')
        box(length-17, length-1, '#514838')
        for pos, direction in ((9, -1), (length-9, 1)):
            points = [(5, pos-direction*2), (13, pos-direction*2), (9, pos+direction*3)]
            if not self.vertical:
                points = [(y, x) for x, y in points]
            self.create_polygon(*[v for point in points for v in point], fill=theme.GOLD)
        if self.last - self.first < 0.999:
            box(start, start+thumb, '#75664d')
            for offset in (-3, 0, 3):
                mid = start + thumb/2 + offset
                coords = (5, mid, 13, mid) if self.vertical else (mid, 5, mid, 13)
                self.create_line(*coords, fill='#bdac88')

    def _press(self, event):
        if not self.command or self.last - self.first >= 0.999:
            return
        pos = event.y if self.vertical else event.x
        length, thumb, _, start = self._geometry()
        if pos < 18 or pos > length-18:
            self.command('scroll', -1 if pos < 18 else 1, 'units')
        elif start <= pos <= start+thumb:
            self.drag = (pos, self.first)
        else:
            self.command('scroll', -1 if pos < start else 1, 'pages')

    def _motion(self, event):
        if self.drag and self.command:
            pos = event.y if self.vertical else event.x
            _, _, travel, _ = self._geometry()
            fraction = self.drag[1] + (pos-self.drag[0]) / max(1, travel) * (1-self.last+self.first)
            self.command('moveto', max(0, min(1, fraction)))


def style_dropdowns(root, style):
    """Keep native combobox behavior while using the app's arrow and scrollbar."""
    if hasattr(root, '_wow_dropdowns'):
        return
    root._wow_dropdowns = {}
    art = Image.new('RGBA', (18, 18))
    draw = ImageDraw.Draw(art)
    draw.rectangle((2, 1, 16, 17), fill='#514838', outline='#8c7960')
    draw.line((3, 16, 3, 2, 15, 2), fill='#bdac88')
    draw.line((15, 2, 15, 16, 3, 16), fill='#30291e')
    draw.polygon(((5, 7), (13, 7), (9, 12)), fill=theme.GOLD)
    root._wow_dropdown_arrow = ImageTk.PhotoImage(art, master=root)
    style.element_create('WoW.downarrow', 'image', root._wow_dropdown_arrow, sticky='')
    def replace(layout):
        return [('WoW.downarrow' if name.endswith('.downarrow') else name,
                 {key: replace(value) if key == 'children' else value for key, value in options.items()})
                for name, options in layout]
    style.layout('TCombobox', replace(style.layout('TCombobox')))

    def setup(combobox, popup):
        path = popup + '.f.sb'
        if path in root._wow_dropdowns:
            return
        # The native popdown exists only in Tcl. A lightweight parent proxy lets
        # our regular scrollbar live inside it without replacing list behavior.
        parent = tk.Misc()
        parent.tk, parent._w, parent.children = root.tk, popup + '.f', {}
        parent.master = root
        root.tk.call('destroy', path)
        listbox = popup + '.f.l'
        bar = WoWScrollbar(parent, name='sb', command=lambda *args: root.tk.call(listbox, 'yview', *args))
        bar.grid(row=0, column=1, padx=(0, 1), pady=1, sticky='ns')
        root.tk.call(listbox, 'configure', '-yscrollcommand', bar.register(bar.set))
        root._wow_dropdowns[path] = bar
        # Popdowns are destroyed with their combobox; discard their Python refs.
        bar.bind('<Destroy>', lambda _: root._wow_dropdowns.pop(path, None), add='+')

    callback = root.register(setup)
    root.tk.call('rename', 'ttk::combobox::PopdownWindow', 'ttk::combobox::WoWOriginalPopdownWindow')
    root.tk.eval('''
        proc ttk::combobox::PopdownWindow {cb} {
            set popup [WoWOriginalPopdownWindow $cb]
            CALLBACK $cb $popup
            return $popup
        }
    '''.replace('CALLBACK', callback))


def bind_scroll_content(canvas, inner, window):
    """Keep short content at the top and recalculate bounds after resizing."""
    def update(event=None):
        if canvas.winfo_width() > 1:
            canvas.itemconfigure(window, width=canvas.winfo_width())
        canvas.configure(scrollregion=(0, 0, canvas.winfo_width(),
                                       max(canvas.winfo_height(), inner.winfo_reqheight())))
    inner.bind('<Configure>', update)
    canvas.bind('<Configure>', update)


def caption_image(master, text, color, square=False, point_size=None):
    text = str(text).upper()
    scale = master.winfo_fpixels("1p")
    root = master.winfo_toplevel()
    cache = getattr(root, '_caption_cache', None)
    if cache is None:
        root._caption_cache = cache = {}
    point_size = point_size or (12 if text in ("▲", "▼") else 7)
    key = (text, color, square, scale, point_size)
    if key in cache:
        return cache[key]
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
    result = ImageTk.PhotoImage(image, master=master)
    if len(cache) >= 256:
        cache.clear()
    cache[key] = result
    return result


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
        color = getattr(self, "caption_color", getattr(self.winfo_toplevel(), "_ata_caption_color", theme.GOLD))
        self._caption_image = caption_image(self, self.caption, color, self.square)
        super().configure(image=self._caption_image, compound="none", width=0)


class IconButton(Button):
    """Compact square action button with a drawn, font-independent icon."""
    def __init__(self, parent, icon, **kwargs):
        self.icon = icon
        self.pixel_size = kwargs.pop('pixel_size', None)
        super().__init__(parent, **kwargs)

    def refresh_art(self):
        color = getattr(self, 'caption_color', theme.GOLD)
        size = self.pixel_size or max(16, round(self.winfo_fpixels('12p')))
        root = self.winfo_toplevel()
        cache = getattr(root, '_icon_cache', None)
        if cache is None:
            root._icon_cache = cache = {}
        key = (self.icon, size, color)
        if key in cache:
            self._caption_image = cache[key]
            self.configure(image=self._caption_image, compound='none', width=0)
            return
        image = Image.new('RGBA', (64, 64))
        draw = ImageDraw.Draw(image)
        if self.icon == 'pencil':
            draw.polygon([(15, 42), (42, 15), (50, 23), (23, 50)], fill=color)
            draw.polygon([(12, 52), (15, 43), (22, 50)], fill=color)
            draw.line([(39, 18), (47, 26)], fill=theme.PANEL, width=3)
        elif self.icon == 'user':
            draw.ellipse((23, 10, 41, 28), fill=color)
            draw.rounded_rectangle((13, 34, 51, 54), radius=10, fill=color)
        elif self.icon == 'info':
            draw.ellipse((8, 8, 56, 56), outline=color, width=4)
            draw.ellipse((28, 18, 36, 26), fill=color)
            draw.rounded_rectangle((29, 30, 35, 46), radius=2, fill=color)
        else:
            draw.line((17, 17, 47, 47), fill=color, width=6)
            draw.line((47, 17, 17, 47), fill=color, width=6)
        self._caption_image = ImageTk.PhotoImage(image.resize((size, size), Image.Resampling.LANCZOS), master=self)
        cache[key] = self._caption_image
        self.configure(image=self._caption_image, compound='none', width=0)


class Section(ttk.LabelFrame):
    """A full-width shaded category banner above the existing content layout."""
    def __init__(self, parent, **kwargs):
        self.colors = kwargs.pop("colors", None)
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
        colors = self.colors or getattr(self.winfo_toplevel(), "_ata_colors", theme.UI_THEMES["WoW Mode"])
        width = max(150, self.winfo_width()-22)
        self.heading.configure(width=width, background=colors["background"])
        self.heading.delete("all")
        self.heading.create_rectangle(0, 0, width-1, 27, fill=colors["control"], outline=colors["border"])
        self._title_image = caption_image(self.heading, self.title, theme.GOLD)
        self.heading.create_image(14, 14, anchor="w", image=self._title_image)
