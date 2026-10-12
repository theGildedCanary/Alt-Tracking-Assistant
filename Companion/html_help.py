"""Reference for the character Info panel's built-in HTML renderer."""
import tkinter as tk
from tkinter import ttk
import theme
import window_position
from widgets import Button, WoWScrollbar


HELP = '''Use HTML syntax to format your character information.
The tags and CSS properties listed here are supported by the Companion.

HTML tags
<h1> through <h6> — headings
<p>, <div> — text blocks
<span> — style part of a line
<br> — line break
<hr> — horizontal divider
<b>, <strong> — bold
<i>, <em> — italic
<u> — underline
<s>, <del> — strikethrough
<code>, <pre> — monospace text; pre preserves whitespace
<ul>, <ol>, <li> — simple lists (bullet markers)
<table>, <tr>, <td>, <th> — simple text rows separated by |; th is bold
<img> — bundled WoW header images and divider artwork

CSS inside style="..."
color: #FFF5CC
    Text color, using a 3 or 6 digit hex code.
font-family: Skurri
    Font name. Also supports Morpheus, Friz Quadrata TT,
    Arial Narrow, Montserrat, and installed fonts.
font-size: 16pt
    Font size in pt or px.
font-weight: bold
    Bold text; 700 is also supported.
font-style: italic
    Italic text.
text-align: center
    left, center, right, or justify.
text-transform: uppercase
    uppercase, lowercase, capitalize, or none.
padding: 20px
    Space around a text block. Accepts px or pt.
    One value: all sides.
    Two values: top/bottom, left/right.
    Three values: top, left/right, bottom.
    Four values: top, right, bottom, left.
padding-top / padding-right / padding-bottom / padding-left
    Set an individual side, for example padding-left: 20px.

Examples
<h1 style="font-family: Skurri; color: #B87333; text-align: center">Character Name</h1>

<p style="color: #FFF5CC; padding: 20px">Your character information.</p>

<span style="text-transform: uppercase">Your text</span>

<img src="Interface\\PETBATTLES\\Weather-Sandstorm" width="512" height="128" align="center">

Other CSS properties, style sheets, and scripts are not rendered.
This section uses the Companion's built-in formatter, so no browser or additional runtime is required.
'''


def show_help(parent):
    existing = getattr(parent, '_html_help', None)
    if existing is not None and existing.winfo_exists():
        existing.deiconify()
        window_position.center_popup(existing)
        existing.lift()
        return existing
    window = tk.Toplevel(parent, background=theme.PANEL)
    parent._html_help = window
    window.title('Supported HTML formatting')
    window.transient(parent.winfo_toplevel())
    window.geometry('620x650')
    window.protocol('WM_DELETE_WINDOW', window.withdraw)
    frame = ttk.Frame(window, padding=14)
    frame.pack(fill='both', expand=True)
    ttk.Label(frame, text='Supported HTML Formatting', font=('Montserrat', 11, 'bold'),
              foreground=theme.GOLD).pack(anchor='w', pady=(0, 10))
    area = ttk.Frame(frame)
    area.pack(fill='both', expand=True)
    text = tk.Text(area, wrap='word', font=('Montserrat', 9), background=theme.PANEL,
                   foreground=theme.TEXT, highlightthickness=0, borderwidth=0,
                   padx=8, pady=8, selectbackground=theme.GOLD_DARK)
    bar = WoWScrollbar(area, command=text.yview)
    bar.pack(side='right', fill='y')
    text.configure(yscrollcommand=bar.set)
    text.pack(fill='both', expand=True)
    text.insert('1.0', HELP)
    text.tag_configure('heading', foreground=theme.GOLD, font=('Montserrat', 9, 'bold'))
    for heading in ('HTML tags', 'CSS inside style="..."', 'Examples'):
        start = text.search(heading, '1.0', exact=True)
        text.tag_add('heading', start, f'{start}+{len(heading)}c')
    text.configure(state='disabled')
    Button(frame, text='Close', command=window.withdraw).pack(anchor='e', pady=(10, 0))
    window.bind('<Escape>', lambda _: window.withdraw())
    window_position.center_popup(window)
    return window
