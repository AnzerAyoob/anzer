import unittest
from dataclasses import FrozenInstanceError

from anzer.lexer import Lexer
from anzer.normalize import NormalizedHtml, ToggleAction, normalize_document
from anzer.parser import Parser
from anzer.semantic import SemanticValidator
from anzer.source import Source


class NormalizerTests(unittest.TestCase):
    def parse(self, body):
        source = Source(f"<anzer start>\n{body}\n<anzer end>", "normalize.anzer")
        tokens, lex_errors = Lexer(source).tokenize()
        document, parse_errors = Parser(source, tokens).parse_document()
        self.assertEqual(lex_errors, [])
        self.assertEqual(parse_errors, [])
        return document

    def normalize(self, body):
        document = self.parse(body)
        result = SemanticValidator().analyze(document)
        self.assertEqual(result.diagnostics, ())
        return normalize_document(document, result)

    def values(self, element):
        return {prop.name: prop.value for prop in element.properties}

    def test_document_structure_preserves_kind_tag_and_shape(self):
        document = self.normalize(
            'anzer make title: text="Heading", type="H3";\n'
            'anzer make section: type="DIV", text="Introduction" {\n'
            '  anzer make container { anzer make image: src="a.png"; }\n'
            '  anzer make paragraph: text="Body", type="SPAN";\n'
            '}\n'
            'anzer make link: text="More", url="/more";'
        )
        title, section, link = document.elements
        container, paragraph = section.children
        image, = container.children
        self.assertEqual(
            [(node.kind, node.tag, node.shape) for node in
             (title, section, container, image, paragraph, link)],
            [
                ("title", "h3", "leaf"),
                ("section", "div", "container"),
                ("container", "div", "container"),
                ("image", "img", "void"),
                ("paragraph", "span", "leaf"),
                ("link", "a", "leaf"),
            ],
        )
        self.assertEqual(self.values(section)["text"], "Introduction")
        self.assertEqual(self.values(link), {"text": "More", "url": "/more"})
        self.assertEqual((title.children, image.children), ((), ()))

    def test_canonical_names_units_and_numeric_lengths(self):
        element, = self.normalize(
            'anzer make section: font="Arial, serif", text-size=18.5, '
            'minimum---height=-0.0, maximum width="NONE", width="12 VIEWPORT WIDTH", '
            'height="20 percentage", padding="1 CENTIMETRE 0", margin="-2 points auto" {}'
        ).elements
        self.assertEqual(self.values(element), {
            "font-family": "Arial, serif",
            "font-size": "18.5px",
            "height": "20%",
            "margin": "-2pt auto",
            "max-width": "none",
            "min-height": "0",
            "padding": "1cm 0",
            "type": "section",
            "width": "12vw",
        })

    def test_enums_depend_on_effective_display_and_tracks_are_canonical(self):
        flex, grid = self.normalize(
            'anzer make section style 1: display="GRID", justify-content="START", '
            'align-items="END";\n'
            'anzer make section: use style="section style 1", display="INLINE-FLEX", '
            'flex-direction="ROW-REVERSE", color="#ABC" {}\n'
            'anzer make section: use style="section style 1", '
            'grid-template-columns="AUTO .50FR 3 40 PERCENT", gap="0 2 EM" {}'
        ).elements
        self.assertEqual(self.values(flex), {
            "align-items": "flex-end",
            "color": "#abc",
            "display": "inline-flex",
            "flex-direction": "row-reverse",
            "justify-content": "flex-start",
            "type": "section",
        })
        self.assertEqual(self.values(grid), {
            "align-items": "end",
            "column-gap": "2em",
            "display": "grid",
            "grid-template-columns": "auto 0.5fr 3px 40%",
            "justify-content": "start",
            "row-gap": "0",
            "type": "section",
        })

    def test_gap_axes_resolve_within_a_layer(self):
        cases = (
            ('gap=10', {"row-gap": "10px", "column-gap": "10px"}),
            ('gap="10 20"', {"row-gap": "10px", "column-gap": "20px"}),
            ('row-gap=0', {"row-gap": "0"}),
            ('column-gap="2 REM"', {"column-gap": "2rem"}),
            ('gap="10 20", row-gap=30', {"row-gap": "30px", "column-gap": "20px"}),
            ('gap="10 20", column-gap=40', {"row-gap": "10px", "column-gap": "40px"}),
            ('gap="10 20", row-gap=30, column-gap=40', {"row-gap": "30px", "column-gap": "40px"}),
        )
        for declarations, expected in cases:
            with self.subTest(declarations=declarations):
                section, = self.normalize(
                    f'anzer make section: display="grid", {declarations} {{}}'
                ).elements
                self.assertEqual(self.values(section), {"display": "grid", "type": "section", **expected})

    def test_gap_axes_merge_independently_across_layers(self):
        cases = (
            ('gap="5 8"', 'row-gap=12', ("12px", "8px")),
            ('gap="5 8"', 'column-gap=40', ("5px", "40px")),
            ('row-gap=5', 'gap="20 30"', ("20px", "30px")),
            ('column-gap=8', 'gap="20 30"', ("20px", "30px")),
            ('row-gap=5, column-gap=8', 'gap="20 30"', ("20px", "30px")),
            ('gap="5 8"', 'gap="20 30"', ("20px", "30px")),
            ('gap="5 8"', 'gap="20 30", row-gap=40', ("40px", "30px")),
            ('gap="5 8"', 'gap="20 30", column-gap=40', ("20px", "40px")),
            ('gap="5 8", row-gap=6', 'column-gap=40', ("6px", "40px")),
            ('gap="5 8", column-gap=6', 'row-gap=40', ("40px", "6px")),
        )
        for style, direct, (row, column) in cases:
            with self.subTest(style=style, direct=direct):
                section, = self.normalize(
                    f'anzer make section style 1: display="flex", {style};\n'
                    f'anzer make section: use style="section style 1", {direct} {{}}'
                ).elements
                self.assertEqual(self.values(section), {
                    "column-gap": column, "display": "flex", "row-gap": row, "type": "section",
                })

    def test_gap_resolution_is_independent_of_declaration_order(self):
        first = self.normalize(
            'anzer make section style 1: display="grid", gap="5 8", column-gap=9;\n'
            'anzer make section: use style="section style 1", gap="20 30", row-gap=40 {}'
        )
        second = self.normalize(
            'anzer make section style 1: column-gap=9, gap="5 8", display="grid";\n'
            'anzer make section: row-gap=40, gap="20 30", use style="section style 1" {}'
        )
        self.assertEqual(first, second)
        self.assertEqual(first, self.normalize(
            'anzer make section: display="grid", row-gap=40, column-gap=30 {}'
        ))
        self.assertEqual([prop.name for prop in first.elements[0].properties], [
            "column-gap", "display", "row-gap", "type",
        ])

    def test_resolved_gap_axes_keep_their_winning_source_spans(self):
        document = self.parse(
            'anzer make section style 1: display="grid", gap="5 8";\n'
            'anzer make section: use style="section style 1", row-gap=12 {}'
        )
        style, element = document.declarations
        result = SemanticValidator().analyze(document)
        section, = normalize_document(document, result).elements
        spans = {prop.name: prop.span for prop in section.properties}
        self.assertEqual(spans["column-gap"], style.properties[1].span)
        self.assertEqual(spans["row-gap"], element.properties[0].span)

    def test_border_components_override_shorthand_and_cross_layers(self):
        inherited, direct = self.normalize(
            'anzer make paragraph style 1: border-color="blue", border="RED 2 PIXELS SOLID";\n'
            'anzer make paragraph: use style="paragraph style 1", text="First", '
            'border-width=0;\n'
            'anzer make paragraph: border-color="#FFF", use style="paragraph style 1", '
            'text="Second", border="DASHED";'
        ).elements
        self.assertEqual(self.values(inherited), {
            "border-color": "blue", "border-style": "solid", "border-width": "0",
            "text": "First", "type": "p",
        })
        self.assertEqual(self.values(direct), {
            "border-color": "#fff", "border-style": "dashed", "border-width": "medium",
            "text": "Second", "type": "p",
        })

    def test_border_omissions_use_css_defaults_only_when_shorthand_is_present(self):
        shorthand, plain = self.normalize(
            'anzer make paragraph: text="Border", border="4";\n'
            'anzer make paragraph: text="Plain";'
        ).elements
        self.assertEqual(self.values(shorthand), {
            "border-color": "currentcolor", "border-style": "none", "border-width": "4px",
            "text": "Border", "type": "p",
        })
        self.assertEqual(self.values(plain), {"text": "Plain", "type": "p"})

    def test_element_defaults_and_explicit_image_alt(self):
        button, image, decorative, section = self.normalize(
            'anzer make button: text="Continue";\n'
            'anzer make image: src="https://example.com/assets/Blue_Bird-photo%202.png?size=1#preview";\n'
            'anzer make image: src="/decoration.png", alt="";\n'
            'anzer make section {}'
        ).elements
        self.assertEqual((button.tag, self.values(button)), (
            "button", {"text": "Continue", "type": "button"},
        ))
        self.assertEqual(self.values(image)["alt"], "Blue Bird photo 2")
        self.assertEqual(self.values(decorative)["alt"], "")
        self.assertEqual(self.values(section), {"type": "section"})
        self.assertIsNone(button.toggle)

    def test_image_without_a_filename_has_no_derived_alt(self):
        image, = self.normalize('anzer make image: src="https://example.com/";').elements
        self.assertEqual(self.values(image), {"src": "https://example.com/"})

    def test_style_can_supply_required_properties_and_direct_aliases_override_it(self):
        element, = self.normalize(
            'anzer make paragraph: use style="paragraph style 1", font="Roboto", '
            'minimum width=32, type="SPAN";\n'
            'anzer make paragraph style 1: font-family="Arial", min-width=20, '
            'text="From style", color="BLUE", type="DIV";'
        ).elements
        self.assertEqual(element.tag, "span")
        self.assertEqual(self.values(element), {
            "color": "blue", "font-family": "Roboto", "min-width": "32px",
            "text": "From style", "type": "span",
        })
        self.assertEqual([prop.name for prop in element.properties], [
            "color", "font-family", "min-width", "text", "type",
        ])

    def test_style_kind_mismatch_cannot_be_normalized(self):
        document = self.parse(
            'anzer make container style 1: color="blue";\n'
            'anzer make section: type="DIV", use style="container style 1" {}'
        )
        result = SemanticValidator().analyze(document)
        self.assertEqual([diagnostic.code for diagnostic in result.diagnostics], ["SEMSTYLE004"])
        with self.assertRaisesRegex(ValueError, "semantic errors"):
            normalize_document(document, result)

    def test_html_is_preserved_verbatim_between_children(self):
        section, = self.normalize(
            'anzer make section: text="Plain content" {\n'
            '  anzer make paragraph: text="Before";\n'
            r'  anzer use html="<span data-label=\"x\">A\nB &amp;</span>";' "\n"
            '  anzer make paragraph: text="After";\n'
            '}'
        ).elements
        before, html, after = section.children
        self.assertEqual(self.values(before)["text"], "Before")
        self.assertIsInstance(html, NormalizedHtml)
        self.assertEqual(html.html, '<span data-label="x">A\nB &amp;</span>')
        self.assertEqual(self.values(after)["text"], "After")

    def test_spans_track_winning_assignments_and_synthesized_defaults(self):
        ast = self.parse(
            'anzer make section style 1: color="red", padding=2;\n'
            'anzer make section: use style="section style 1", color="Blue", border="solid" {\n'
            '  anzer use html="<b>Body</b>";\n'
            '}'
        )
        style, section = ast.declarations
        result = SemanticValidator().analyze(ast)
        normalized = normalize_document(ast, result)
        node, = normalized.elements
        properties = {prop.name: prop for prop in node.properties}
        self.assertEqual(
            (normalized.span, normalized.start_marker_span, normalized.end_marker_span),
            (ast.span, ast.start_marker_span, ast.end_marker_span),
        )
        self.assertEqual(node.span, section.span)
        self.assertEqual(node.children[0].span, section.children[0].span)
        self.assertEqual(properties["padding"].span, style.properties[1].span)
        self.assertEqual(properties["color"].span, section.properties[0].span)
        for name in ("border-color", "border-style", "border-width"):
            self.assertEqual(properties[name].span, section.properties[1].span)
        self.assertEqual(properties["type"].span, section.span)
        self.assertEqual(section.properties[0].value, "Blue")
        with self.assertRaises(FrozenInstanceError):
            properties["color"].value = "green"
        with self.assertRaises(FrozenInstanceError):
            node.children = ()

    def test_toggle_metadata_carries_validated_id_and_target_span(self):
        document = self.parse(
            'anzer make button style 1: action="toggle", target="Details";\n'
            'anzer make button: text="Open", use style="button style 1";\n'
            'anzer make container { anzer make section: id="Details", display="grid" {} }\n'
            'anzer make button: text="Close", target="Details", action="toggle";'
        )
        style, _, _, direct_button = document.declarations
        result = SemanticValidator().analyze(document)
        self.assertEqual(result.diagnostics, ())
        opening, container, closing = normalize_document(document, result).elements
        self.assertEqual(opening.toggle.target_id, self.values(container.children[0])["id"])
        self.assertEqual(self.values(container.children[0])["display"], "grid")
        for button, target_span in (
            (opening, style.properties[1].span), (closing, direct_button.properties[1].span),
        ):
            self.assertIsInstance(button.toggle, ToggleAction)
            self.assertEqual(button.toggle.target_id, "Details")
            self.assertEqual(button.toggle.span, target_span)
            self.assertEqual(self.values(button)["action"], "toggle")

    def test_equivalent_documents_compare_equal_with_different_spans(self):
        first = self.normalize(
            'anzer make paragraph style 1: minimum width=2, border="red 2px solid";\n'
            'anzer make paragraph: text="Hi", text-size="12 PIXELS", '
            'border-color="BLUE", use style="paragraph style 1";'
        )
        second = self.normalize(
            'anzer make paragraph: border-color="blue", font-size=12, '
            'use style="paragraph style 1", text="Hi";\n'
            'anzer make paragraph style 1: border="solid RED 2 PIXELS", min-width="02px";'
        )
        self.assertEqual(first, second)
        self.assertEqual(hash(first), hash(second))
        self.assertNotEqual(first.elements[0].span, second.elements[0].span)

    def test_invalid_result_stays_invalid_after_validator_reuse(self):
        invalid = self.parse('anzer make button: text="Open", action="toggle", target="missing";')
        valid = self.parse('anzer make button: text="Continue";')
        validator = SemanticValidator()
        invalid_result = validator.analyze(invalid)
        self.assertEqual([diagnostic.code for diagnostic in invalid_result.diagnostics], ["SEMACT004"])
        validator.diagnostics.clear()
        valid_result = validator.analyze(valid)
        validator.validate(invalid)
        with self.assertRaisesRegex(ValueError, "semantic errors"):
            normalize_document(invalid, invalid_result)
        self.assertEqual(self.values(normalize_document(valid, valid_result).elements[0]), {
            "text": "Continue", "type": "button",
        })

    def test_result_cannot_be_used_for_another_ast(self):
        body = 'anzer make paragraph: text="Hello";'
        first, second = self.parse(body), self.parse(body)
        self.assertEqual(first, second)
        with self.assertRaisesRegex(ValueError, "different document"):
            normalize_document(second, SemanticValidator().analyze(first))


if __name__ == "__main__":
    unittest.main()
