"""Render character info markup without changing its saved source."""
import re
import theme


def render_info(widget, source):
    widget.configure(state='normal')
    widget.delete('1.0', 'end')
    for tag, options in {
        'bold': {'font': ('Montserrat', 9, 'bold')},
        'italic': {'font': ('Montserrat', 9, 'italic')},
        'code': {'font': ('Consolas', 9), 'background': theme.PANEL_ALT},
        'heading': {'font': ('Montserrat', 12, 'bold'), 'foreground': theme.GOLD, 'spacing1': 6, 'spacing3': 6},
        'table': {'font': ('Consolas', 9), 'spacing1': 2, 'spacing3': 2},
    }.items():
        widget.tag_configure(tag, **options)
    def inline(text, base=()):
        pattern = r'(\*\*.+?\*\*|\*[^*]+?\*|`[^`]+?`)'
        for part in re.split(pattern, text):
            tag = 'bold' if part.startswith('**') and part.endswith('**') else 'italic' if part.startswith('*') and part.endswith('*') else 'code' if part.startswith('`') and part.endswith('`') else None
            trim = 2 if tag == 'bold' else 1
            widget.insert('end', part[trim:-trim] if tag else part, base + ((tag,) if tag else ()))
    lines = source.splitlines(keepends=True)
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.strip().startswith('|') and line.strip().endswith('|'):
            rows = []
            while index < len(lines) and lines[index].strip().startswith('|') and lines[index].strip().endswith('|'):
                cells = [cell.strip() for cell in lines[index].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-{3,}:?', cell) for cell in cells):
                    rows.append(cells)
                index += 1
            count = max((len(row) for row in rows), default=0)
            widths = [max((len(row[col]) if col < len(row) else 0 for row in rows), default=0) for col in range(count)]
            for row in rows:
                widget.insert('end', ' | '.join((row[col] if col < len(row) else '').ljust(widths[col]) for col in range(count)) + '\n', 'table')
            continue
        heading = re.match(r'^#{1,6}\s+(.*)', line.rstrip('\n'))
        if heading:
            inline(heading.group(1), ('heading',))
            widget.insert('end', '\n')
        else:
            inline(re.sub(r'^\s*[-*+]\s+', '• ', line))
        index += 1
    widget.configure(state='disabled')
