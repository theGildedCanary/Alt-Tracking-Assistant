"""HTML profile formatting rendered locally in a Tk text widget."""
import re
from html.parser import HTMLParser
from pathlib import Path
from PIL import Image, ImageTk
import theme


def css_padding(css, pixels_per_point):
    def length(value):
        match = re.fullmatch(r'(\d+(?:\.\d+)?)(px|pt)?', value.lower())
        if not match:
            return None
        return round(float(match.group(1)) * (pixels_per_point if match.group(2) == 'pt' else 1))
    sides = [0, 0, 0, 0]
    # Preserve CSS declaration order so later shorthand/longhand wins.
    for name, value in css.items():
        if name == 'padding':
            values = [length(part) for part in value.split()]
            if 1 <= len(values) <= 4 and None not in values:
                if len(values) == 1:
                    sides = values * 4
                elif len(values) == 2:
                    sides = values * 2
                elif len(values) == 3:
                    sides = [values[0], values[1], values[2], values[1]]
                else:
                    sides = values
        elif name in ('padding-top', 'padding-right', 'padding-bottom', 'padding-left'):
            size = length(value)
            if size is not None:
                sides[('padding-top', 'padding-right', 'padding-bottom', 'padding-left').index(name)] = size
    return tuple(sides)


def render_html(widget, source, family, image_catalog):
    widget.configure(state='normal')
    widget.delete('1.0', 'end')
    widget._profile_images = []
    class Renderer(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.stack = []
            self.tag_count = 0
            self.suppress = 0
            self.padding_blocks = []
            self.justified_ranges = []
        def styles(self):
            style = {'family': family, 'size': 9, 'color': theme.TEXT, 'align': 'left'}
            for _, overrides in self.stack:
                style.update(overrides)
            style['left'] = sum(overrides.get('padding', (0, 0, 0, 0))[3] for _, overrides in self.stack)
            style['right'] = sum(overrides.get('padding', (0, 0, 0, 0))[1] for _, overrides in self.stack)
            return style
        def insert(self, text):
            if not text or self.suppress:
                return
            style = self.styles()
            key = 'html_'+str(sorted(style.items()))
            weights = tuple(v for k, v in (('bold', 'bold'), ('italic', 'italic')) if style.get(k))
            widget.tag_configure(key, font=(style['family'], style['size'], ' '.join(weights) or 'normal'),
                                 foreground=style['color'], justify='left' if style['align'] == 'justify' else style['align'],
                                 underline=bool(style.get('underline')), overstrike=bool(style.get('strike')),
                                 lmargin1=style['left'], lmargin2=style['left'], rmargin=style['right'],
                                 spacing1=0, spacing2=0, spacing3=0)
            start = widget.index('end-1c')
            widget.insert('end', text, (key,))
            if style['align'] == 'justify':
                end = widget.index('end-1c')
                if self.justified_ranges and self.justified_ranges[-1][1:] == (start, style['left'], style['right']):
                    previous = self.justified_ranges.pop()
                    start = previous[0]
                self.justified_ranges.append((start, end, style['left'], style['right']))
        def newline(self):
            if widget.get('end-2c', 'end-1c') not in ('', '\n'):
                self.insert('\n')
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag in ('script', 'style'):
                self.suppress += 1
                return
            if self.suppress:
                return
            if tag == 'br':
                self.insert('\n')
                return
            if tag == 'hr':
                self.newline()
                available = widget.winfo_width()
                if available <= 32:
                    available = 400
                inset = sum(int(widget.cget(option)) for option in ('borderwidth', 'highlightthickness', 'padx'))
                width = max(1, available - 2 * inset)
                photo = ImageTk.PhotoImage(Image.new('RGB', (width, 2), theme.DIVIDER), master=widget)
                widget._profile_images.append(photo)
                widget.image_create('end', image=photo)
                self.insert('\n')
                return
            if tag == 'img':
                path = attrs.get('src', '').replace('\\', '/').lower().removesuffix('.blp')
                asset = Path(__file__).parent/'assets'/'profiles'/image_catalog.get(path, '__missing__')
                self.newline()
                if asset.is_file():
                    try:
                        width, height = int(attrs.get('width', 512)), int(attrs.get('height', 128))
                    except ValueError:
                        width, height = 512, 128
                    available = widget.winfo_width()-16 if widget.winfo_width() > 32 else 400
                    scale = min(1, max(1, available)/max(1, width))
                    art = Image.open(asset).convert('RGBA').resize((max(1, min(2048, round(width*scale))), max(1, min(2048, round(height*scale)))), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(art, master=widget)
                    widget._profile_images.append(photo)
                    start = widget.index('end-1c')
                    widget.image_create('end', image=photo)
                    align = attrs.get('align', 'center')
                    widget.tag_configure('html_image_'+align, justify=align if align in ('left', 'center', 'right') else 'center')
                    widget.tag_add('html_image_'+align, start, 'end-1c')
                    self.insert('\n')
                else:
                    self.insert('[Image unavailable: '+attrs.get('src', '')+']\n')
                return
            if tag in ('p', 'div', 'h1', 'h2', 'h3', 'h4', 'li', 'tr', 'blockquote', 'hr'):
                self.newline()
            override = {}
            if tag.startswith('h') and tag[1:].isdigit():
                override.update(size={1:18, 2:14, 3:11}.get(int(tag[1:]), 10), bold=True)
            if tag in ('b', 'strong', 'th'): override['bold'] = True
            if tag in ('i', 'em'): override['italic'] = True
            if tag == 'u': override['underline'] = True
            if tag in ('s', 'del'): override['strike'] = True
            if tag in ('code', 'pre'): override['family'] = 'Consolas'
            css = dict((k.strip().lower(), v.strip()) for k, v in re.findall(r'([\w-]+)\s*:\s*([^;]+)', attrs.get('style', '')))
            padding = css_padding(css, widget.winfo_fpixels('1p'))
            if any(padding):
                override['padding'] = padding
                self.padding_blocks.append((tag, widget.index('end-1c'), padding))
            color = css.get('color', attrs.get('color', ''))
            if re.fullmatch(r'#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?', color): override['color'] = color
            align = css.get('text-align', attrs.get('align', ''))
            if align in ('left', 'center', 'right', 'justify'): override['align'] = align
            if css.get('font-weight') in ('bold', '700'): override['bold'] = True
            if css.get('font-style') == 'italic': override['italic'] = True
            transform = css.get('text-transform', '').lower()
            if transform in ('uppercase', 'lowercase', 'capitalize', 'none'):
                override['transform'] = transform
            font_family = css.get('font-family', attrs.get('face', ''))
            if font_family:
                override['family'] = font_family.split(',')[0].strip().strip('"\'')
            font_size = re.fullmatch(r'(\d+(?:\.\d+)?)(pt|px)?', css.get('font-size', ''))
            if font_size:
                size = float(font_size.group(1))
                if font_size.group(2) == 'px':
                    size *= 72 / widget.winfo_fpixels('1i')
                override['size'] = max(1, min(144, round(size)))
            self.stack.append((tag, override))
            if tag == 'li': self.insert('• ')
            if tag in ('td', 'th') and widget.get('end-2c', 'end-1c') not in ('', '\n'): self.insert('  |  ')
        def handle_endtag(self, tag):
            if tag in ('script', 'style'):
                self.suppress = max(0, self.suppress-1)
                return
            end = widget.index('end-1c')
            for i in range(len(self.padding_blocks)-1, -1, -1):
                block_tag, start, padding = self.padding_blocks[i]
                if block_tag == tag:
                    del self.padding_blocks[i]
                    if widget.compare(start, '<', end):
                        self.tag_count += 1
                        top, bottom = f'padding_top_{self.tag_count}', f'padding_bottom_{self.tag_count}'
                        widget.tag_configure(top, spacing1=padding[0])
                        widget.tag_configure(bottom, spacing3=padding[2])
                        widget.tag_add(top, start, f'{start} lineend')
                        widget.tag_add(bottom, f'{end}-1c linestart', end)
                    break
            if tag in ('p', 'div', 'h1', 'h2', 'h3', 'h4', 'li', 'tr', 'blockquote'):
                self.newline()
            for i in range(len(self.stack)-1, -1, -1):
                if self.stack[i][0] == tag:
                    del self.stack[i]
                    break
        def handle_data(self, data):
            # HTML source indentation does not create display paragraphs.
            if any(t == 'pre' for t, _ in self.stack):
                self.insert(self.transform_text(data))
                return
            if not data.strip() and ('\n' in data or '\r' in data):
                return
            text = re.sub(r'\s+', ' ', data)
            if widget.get('end-2c', 'end-1c') in ('', '\n'):
                text = text.lstrip()
            self.insert(self.transform_text(text))
        def transform_text(self, text):
            transform = self.styles().get('transform', 'none')
            if transform == 'uppercase':
                return text.upper()
            if transform == 'lowercase':
                return text.lower()
            if transform == 'capitalize':
                previous = widget.get('end-2c', 'end-1c')
                return re.sub(r'(?<!\w)([^\W\d_])',
                              lambda match: match.group() if match.start() == 0 and (previous.isalnum() or previous == '_')
                              else match.group().upper(), text)
            return text
    parser = Renderer()
    parser.feed(source)
    parser.close()
    if parser.justified_ranges:
        from text_justify import justify_range
        for serial, (start, end, left, right) in enumerate(reversed(parser.justified_ranges)):
            justify_range(widget, start, end, left, right, serial)
    widget.configure(state='disabled')
