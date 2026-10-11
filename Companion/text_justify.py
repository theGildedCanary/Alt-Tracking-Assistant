"""Justify wrapped lines in the built-in Tk HTML preview."""
import re
from tkinter import font as tkfont


def justify_range(widget, start, end, left, right, serial):
    text = widget.get(start, end)
    if not text.strip():
        return
    tags = [widget.tag_names(f'{start}+{offset}c') for offset in range(len(text))]
    fonts = {}
    def measure(first, last):
        total = 0
        run, active = '', None
        for offset in range(first, last):
            spec = widget.cget('font')
            for tag in tags[offset]:
                value = widget.tag_cget(tag, 'font')
                if value:
                    spec = value
            key = str(spec)
            if key != active and run:
                total += fonts[active].measure(run)
                run = ''
            if key not in fonts:
                fonts[key] = tkfont.Font(root=widget, font=spec)
            active, run = key, run + text[offset]
        return total + (fonts[active].measure(run) if run else 0)
    inset = sum(int(widget.cget(option)) for option in ('borderwidth', 'highlightthickness', 'padx'))
    width = max(1, (widget.winfo_width() if widget.winfo_width() > 32 else 400) - 2*inset-left-right-2)
    lines = []
    offset = 0
    for paragraph in text.split('\n'):
        words = [(offset+match.start(), offset+match.end()) for match in re.finditer(r'\S+', paragraph)]
        line, used = [], 0
        for word in words:
            size = measure(*word)
            gap = measure(word[0]-1, word[0]) if line else 0
            if line and used+gap+size > width:
                lines.append((line, True))
                line, used, gap = [], 0, 0
            line.append((word, size))
            used += gap + size
        lines.append((line, False))
        offset += len(paragraph)+1
    top = max((int(widget.tag_cget(tag, 'spacing1') or 0) for tag in tags[0] if tag.startswith('padding_top_')), default=0)
    bottom = max((int(widget.tag_cget(tag, 'spacing3') or 0) for group in tags for tag in group if tag.startswith('padding_bottom_')), default=0)
    widget.delete(start, end)
    cursor = start
    last_content = max((number for number, (words, _) in enumerate(lines) if words), default=0)
    for number, (words, justified) in enumerate(lines):
        line_tag = f'justified_{serial}_{number}'
        stops = []
        if justified and len(words) > 1:
            gap = (width-sum(size for _, size in words))/(len(words)-1)
            position = 0
            for _, size in words[:-1]:
                position += size+gap
                stops.extend((left+round(position), 'left'))
        widget.tag_configure(line_tag, justify='left', lmargin1=left, lmargin2=left, rmargin=right,
                             tabs=tuple(stops), tabstyle='wordprocessor', wrap='none',
                             spacing1=top if number == 0 else 0,
                             spacing3=bottom if number == last_content else 0)
        def insert(value, source_offset):
            nonlocal cursor
            original = tuple(tag for tag in tags[source_offset] if not tag.startswith(('padding_top_', 'padding_bottom_')))
            widget.insert(cursor, value, (*original, line_tag))
            cursor = widget.index(f'{cursor}+{len(value)}c')
        for index, ((first, last), _) in enumerate(words):
            if index:
                insert('\t' if stops else ' ', first)
            # Keep inline colors and fonts, including spans splitting a word.
            for char_offset in range(first, last):
                insert(text[char_offset], char_offset)
        if number < len(lines)-1:
            insert('\n', words[-1][0][1]-1 if words else min(len(text)-1, 0))
