import tkinter as tk
import unittest
from info_format import render_info, HEADER_IMAGES, header_name, set_header


class InfoFormatTests(unittest.TestCase):
    def test_justify_wraps_to_both_edges_and_preserves_inline_formatting(self):
        self.root.deiconify()
        self.root.geometry('420x350')
        self.text.pack(fill='both', expand=True)
        self.root.update()
        source = '<p style="text-align: justify; padding: 20px">First <b>bold</b> words with <span style="color: #B87333">colored text</span> and enough additional words to wrap across several lines of the paragraph without changing the saved HTML.</p>'
        render_info(self.text, source)
        self.root.update()
        display = self.text.get('1.0', 'end-1c')
        self.assertIn('\t', display)
        self.assertEqual(display.split(), 'First bold words with colored text and enough additional words to wrap across several lines of the paragraph without changing the saved HTML.'.split())
        colored = self.text.search('colored', '1.0')
        self.assertTrue(any(self.text.tag_cget(t, 'foreground') == '#B87333' for t in self.text.tag_names(colored)))
        last = self.text.bbox('1.end-1c')
        self.assertIsNotNone(last)
        self.assertAlmostEqual(last[0]+last[2], self.text.winfo_width()-24, delta=4)
        self.root.geometry('580x350');self.root.update()
        render_info(self.text, source);self.root.update()
        wider = self.text.bbox('1.end-1c')
        self.assertAlmostEqual(wider[0]+wider[2], self.text.winfo_width()-24, delta=4)

    def test_padding_insets_wrapped_text_and_only_spaces_block_edges(self):
        render_info(self.text, '<p style="color: #FFF5CC; padding: 20px">First<br><br>Second<br><br>Third</p><p>Next</p>')
        first = self.text.tag_names('1.0')
        middle = self.text.tag_names('3.0')
        last = self.text.tag_names('5.0')
        self.assertTrue(any(str(self.text.tag_cget(t, 'lmargin1')) == '20' and str(self.text.tag_cget(t, 'rmargin')) == '20' for t in first))
        self.assertTrue(any(str(self.text.tag_cget(t, 'spacing1')) == '20' for t in first))
        self.assertFalse(any(str(self.text.tag_cget(t, 'spacing1')) == '20' or str(self.text.tag_cget(t, 'spacing3')) == '20' for t in middle))
        self.assertTrue(any(str(self.text.tag_cget(t, 'spacing3')) == '20' for t in last))
        self.assertFalse(any(str(self.text.tag_cget(t, 'lmargin1')) == '20' for t in self.text.tag_names('6.0')))

    def test_padding_shorthand_and_side_overrides(self):
        from info_html import css_padding
        self.assertEqual(css_padding({'padding': '20px'}, 2), (20, 20, 20, 20))
        self.assertEqual(css_padding({'padding': '10px 20px'}, 2), (10, 20, 10, 20))
        self.assertEqual(css_padding({'padding': '1pt 2pt 3pt'}, 2), (2, 4, 6, 4))
        self.assertEqual(css_padding({'padding': '1px 2px 3px 4px', 'padding-left': '8px'}, 2), (1, 2, 3, 8))

    def test_text_transform_inherits_and_can_be_overridden(self):
        source = '<p style="text-transform: uppercase">Mixed <b>case</b> <span style="text-transform: none">Keep Case</span> &amp; café</p><p style="text-transform: lowercase">LOUD TEXT</p><p>Unchanged</p>'
        render_info(self.text, source)
        self.assertEqual(self.text.get('1.0', 'end-1c'), 'MIXED CASE Keep Case & CAFÉ\nloud text\nUnchanged\n')
        self.assertIn('Mixed', source)

    def test_capitalize_preserves_case_and_words_split_across_tags(self):
        render_info(self.text, '<p style="text-transform: capitalize">hel<b>lo</b> world aLL caps</p>')
        self.assertEqual(self.text.get('1.0', 'end-1c'), 'Hello World ALL Caps\n')

    def test_html_heading_alignment_is_not_overridden_by_source_indentation(self):
        source = '\n  <h1 style="text-align: center"><span style="color: #B87333">Heading</span></h1>\n  <h2 align="center">Subtitle</h2>\n<p>Body</p>'
        render_info(self.text, source)
        self.assertEqual(self.text.get('1.0', 'end-1c'), 'Heading\nSubtitle\nBody\n')
        tags = self.text.tag_names('1.0')
        self.assertTrue(any(self.text.tag_cget(tag, 'justify') == 'center' for tag in tags))
        self.assertTrue(any('18' in self.text.tag_cget(tag, 'font') for tag in tags))

    def test_html_formatting_and_header_selector(self):
        source = set_header('<h1 style="text-align: center; color: #B87333">Title</h1><p><b>Bold</b> &amp; <i>Italic</i></p>', 'Sandstorm')
        self.assertEqual(header_name(source), 'Sandstorm')
        render_info(self.text, source, 'Arial')
        self.assertIn('Bold & Italic', self.text.get('1.0', 'end-1c'))
        self.assertNotIn('<h1', self.text.get('1.0', 'end-1c'))
        self.assertEqual(len(self.text._profile_images), 1)
        self.assertTrue(any(self.text.tag_cget(tag, 'justify') == 'center' for tag in self.text.tag_names() if tag.startswith('html_')))

    def test_html_controls_font_family_and_size(self):
        render_info(self.text, '<p style="font-family: Arial; font-size: 16pt">Text</p>')
        tags = self.text.tag_names('1.0')
        self.assertTrue(any('Arial' in self.text.tag_cget(tag, 'font') and '16' in self.text.tag_cget(tag, 'font') for tag in tags))

    def test_horizontal_rule_spans_viewport_and_resizes(self):
        self.root.deiconify()
        self.text.pack(fill='both', expand=True)
        for width in (480, 720):
            self.root.geometry(f'{width}x300')
            self.root.update()
            render_info(self.text, '<p>Before</p><hr><p>After</p>')
            inset = sum(int(self.text.cget(option)) for option in ('borderwidth', 'highlightthickness', 'padx'))
            self.assertEqual(self.text._profile_images[0].width(), self.text.winfo_width() - 2 * inset)
            self.assertIn('After', self.text.get('1.0', 'end-1c'))

    def test_custom_syntax_is_plain_text(self):
        source = '{h1:c}Title{/h1} **Bold**'
        render_info(self.text, source)
        self.assertEqual(self.text.get('1.0', 'end-1c'), source)

    def test_header_selection_replaces_only_leading_banner_and_preserves_body(self):
        body = '<h1>Title</h1>\n<img src="Interface/QUESTFRAME/UI-HorizontalBreak" width="256" height="64">\nBody'
        for name in HEADER_IMAGES:
            source = set_header(body, name)
            self.assertEqual(header_name(source), name)
            self.assertEqual(set_header(source, 'None'), body)
            replaced = set_header(source, 'Sandstorm')
            self.assertEqual(header_name(replaced), 'Sandstorm')
            self.assertEqual(replaced.count('Weather-'), 1)
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.text = tk.Text(self.root)

    def tearDown(self):
        self.root.destroy()

    def test_missing_image_is_explicit_and_does_not_break_remaining_text(self):
        render_info(self.text, '<img src="Interface/Missing"><h2>Title</h2>')
        self.assertIn('Image unavailable', self.text.get('1.0', 'end-1c'))
        self.assertIn('Title', self.text.get('1.0', 'end-1c'))
