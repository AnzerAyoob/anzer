import unittest
from dataclasses import replace
from html.parser import HTMLParser

from anzer.lexer import Lexer
from anzer.normalize import NormalizedHtml, NormalizedProperty, normalize_document
from anzer.parser import Parser
from anzer.render import render_document
from anzer.semantic import SemanticValidator
from anzer.source import Source


class _Tags(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.tags = []
        self.feed(html)
        self.close()

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def attributes(self, tag):
        return [attrs for name, attrs in self.tags if name == tag]


class RendererTests(unittest.TestCase):
    def parse(self, body):
        source = Source(f"<anzer start>\n{body}\n<anzer end>", "render.anzer")
        tokens, lexical = Lexer(source).tokenize()
        document, syntax = Parser(source, tokens).parse_document()
        self.assertEqual(lexical, [])
        self.assertEqual(syntax, [])
        return document

    def normalize(self, body):
        document = self.parse(body)
        result = SemanticValidator().analyze(document)
        self.assertEqual(result.diagnostics, ())
        return normalize_document(document, result)

    def render(self, body, **options):
        return render_document(self.normalize(body), **options)

    def test_every_element_maps_to_its_default_tag(self):
        html = self.render(
            'anzer make title: text="Welcome";\n'
            'anzer make paragraph: text="Read more";\n'
            'anzer make button: text="Continue";\n'
            'anzer make link: text="Contact", url="mailto:editor@example.com";\n'
            'anzer make image: src="/images/blue_bird.png";\n'
            'anzer make section { anzer make container {} }'
        )
        self.assertIn(
            '<body><h1>Welcome</h1><p>Read more</p>'
            '<button type="button">Continue</button>'
            '<a href="mailto:editor@example.com">Contact</a>'
            '<img alt="blue bird" src="/images/blue_bird.png">'
            '<section><div></div></section></body>',
            html,
        )

    def test_resolved_overrides_change_tags_and_keep_nested_content_order(self):
        html = self.render(
            'anzer make section: type="DIV", text="intro " {\n'
            '  anzer make title: type="H4", text="First";\n'
            '  anzer make container: type="SECTION", text="Nested " {\n'
            '    anzer make paragraph: type="SPAN", text="Second";\n'
            '  }\n'
            '  anzer make paragraph: type="DIV", text="Last";\n'
            '}'
        )
        self.assertIn(
            '<body><div>intro <h4>First</h4><section>Nested <span>Second</span>'
            '</section><div>Last</div></div></body>',
            html,
        )

    def test_ordinary_text_is_escaped_without_creating_elements(self):
        html = self.render(
            r'anzer make paragraph: text="<strong>Café & tea</strong>\r\n\"Quote\"";'
        )
        self.assertIn(
            '<p>&lt;strong&gt;Café &amp; tea&lt;/strong&gt;&#13;\n"Quote"</p>',
            html,
        )
        self.assertEqual(_Tags(html).attributes("strong"), [])

    def test_attribute_values_and_url_entities_round_trip(self):
        html = self.render(
            r"""anzer make section: id="note\"&<one>'" {}""" "\n"
            r"""anzer make image: src="/bird.png?size=1&crop=2", alt="It's a \"bird\" & <friend>";""" "\n"
            r'anzer make link: url="https://example.com/?a=\"one\"&b=&amp;", text="Open";'
        )
        tags = _Tags(html)
        self.assertEqual(tags.attributes("section"), [{"id": 'note"&<one>\''}])
        self.assertEqual(tags.attributes("img"), [{
            "src": "/bird.png?size=1&crop=2",
            "alt": 'It\'s a "bird" & <friend>',
        }])
        self.assertEqual(tags.attributes("a"), [{
            "href": 'https://example.com/?a="one"&b=&amp;',
        }])
        self.assertIn('&quot;one&quot;&amp;b=&amp;amp;', html)

    def test_trusted_html_requires_acknowledgement_and_keeps_exact_position(self):
        model = self.normalize(
            'anzer make section: text="Direct & " {\n'
            '  anzer make paragraph: text="Before";\n'
            r'  anzer use html="<em data-note=\"x\"> A\nB &amp; </em>";' "\n"
            '  anzer make paragraph: text="After";\n'
            '}'
        )
        with self.assertRaisesRegex(ValueError, "requires explicit acknowledgement"):
            render_document(model)
        self.assertIn(
            '<section>Direct &amp; <p>Before</p><em data-note="x"> A\nB &amp; </em>'
            '<p>After</p></section>',
            render_document(model, allow_trusted_html=True),
        )

    def test_raw_html_cannot_appear_at_root_or_in_leaf(self):
        model = self.normalize('anzer make paragraph: text="Leaf";')
        leaf, = model.elements
        raw = NormalizedHtml("<em>Raw</em>", leaf.span)
        for elements in ((raw,), (replace(leaf, children=(raw,)),)):
            with self.subTest(elements=elements):
                with self.assertRaises(ValueError):
                    render_document(replace(model, elements=elements), allow_trusted_html=True)

    def test_empty_document_has_metadata_and_the_frozen_stylesheet(self):
        self.assertEqual(
            self.render(""),
            '<!doctype html>\n<html>\n<head>\n'
            '<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>Anzer document</title>\n'
            '<style>\n*, *::before, *::after { box-sizing: border-box; }\n'
            'body { margin: 0; }\nimg { max-width: 100%; height: auto; }\n'
            '</style>\n</head>\n<body></body>\n</html>\n',
        )

    def test_css_uses_effective_properties_and_encodes_fonts(self):
        html = self.render(
            r'anzer make section style 1: display="FLEX", justify-content="START", ' "\n"
            r'  font="A\" & B, Times New Roman, sans-serif", color="red", border="solid";' "\n"
            'anzer make section: use style="section style 1", gap="1 pixels 2 REM", '
            'column-gap=4, row-gap=3, border-width=0, color="#ABC" {}'
        )
        style = _Tags(html).attributes("section")[0]["style"]
        self.assertEqual(
            style,
            r'border-color: currentcolor; border-style: solid; border-width: 0; '
            r'color: #abc; column-gap: 4px; display: flex; '
            r'font-family: "A\22  & B", "Times New Roman", sans-serif; '
            r'justify-content: flex-start; row-gap: 3px;',
        )
        self.assertIn('&quot;A\\22  &amp; B&quot;', html)

    def test_css_emits_only_the_resolved_gap_axes(self):
        html = self.render(
            'anzer make section style 1: display="grid", row-gap=5, column-gap=8;\n'
            'anzer make section: use style="section style 1", gap="20 30" {}\n'
            'anzer make section: use style="section style 1", column-gap=40, gap="20 30" {}\n'
            'anzer make section: display="flex", gap="0 2rem" {}'
        )
        self.assertEqual([attrs["style"] for attrs in _Tags(html).attributes("section")], [
            "column-gap: 30px; display: grid; row-gap: 20px;",
            "column-gap: 40px; display: grid; row-gap: 20px;",
            "column-gap: 2rem; display: flex; row-gap: 0;",
        ])

    def test_toggle_metadata_and_initial_state_preserve_escaped_id(self):
        html = self.render(
            'anzer make button: text="Open", action="toggle", target="a&b";\n'
            'anzer make section: id="a&b", display="grid" {}'
        )
        self.assertIn(
            '<button aria-expanded="true" data-anzer-action="toggle" data-anzer-target="a&amp;b" '
            'data-anzer-toggle-key="1" type="button">Open</button>'
            '<section data-anzer-toggle-target="1" id="a&amp;b" style="display: grid;"></section>',
            html,
        )
        self.assertEqual(_Tags(html).attributes("script"), [{}])
        self.assertLess(html.index("</section>"), html.index("<script>"))

    def test_equivalent_normalized_documents_render_identical_bytes(self):
        a = self.normalize(
            'anzer make paragraph style 1: font="Georgia", color="RED";\n'
            'anzer make paragraph: use style="paragraph style 1", text="Café", text-size=12;'
        )
        b = self.normalize(
            'anzer make paragraph: font-family="Georgia", font-size="12px", '
            'color="red", text="Café";'
        )
        self.assertEqual(a, b)
        expected = render_document(a).encode("utf-8")
        self.assertEqual(expected, render_document(a).encode("utf-8"))
        self.assertEqual(expected, render_document(b).encode("utf-8"))

    def test_unsupported_or_malformed_normalized_input_fails(self):
        ast = self.parse('anzer make paragraph: text="Plain";')
        with self.assertRaisesRegex(TypeError, "normalized Anzer document"):
            render_document(ast)

        model = normalize_document(ast, SemanticValidator().analyze(ast))
        element, = model.elements
        for node, message in (
            (replace(element, tag="unknown"), "Unsupported normalized element or tag"),
            (replace(element, shape="void"), "Unsupported shape"),
            (replace(element, properties=element.properties * 2), "Duplicate property"),
            (
                replace(element, properties=(NormalizedProperty("font", "Arial", element.span),)),
                "No renderer mapping",
            ),
            (
                replace(element, properties=(NormalizedProperty("color", "red; width", element.span),)),
                "Cannot serialize normalized CSS value",
            ),
        ):
            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError, message):
                    render_document(replace(model, elements=(node,)))


if __name__ == "__main__":
    unittest.main()
