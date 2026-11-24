import unittest
from unittest.mock import patch

from anzer.diagnostics import DiagnosticCategory
from anzer.source import Source
from anzer.lexer import Lexer
from anzer.parser import Parser


class DeclarationParserTests(unittest.TestCase):
    def parse(self, body):
        source = Source(f"<anzer start>\n{body}\n<anzer end>", "fixture.anzer")
        tokens, lex_errors = Lexer(source).tokenize()
        document, parse_errors = Parser(source, tokens).parse_document()
        return document, lex_errors, parse_errors

    def test_property_span_uses_original_escaped_string_lexeme(self):
        source_text = '<anzer start>\nanzer make paragraph: text="A\\nB";\n<anzer end>'
        source = Source(source_text, "span.anzer")
        tokens, lex_errors = Lexer(source).tokenize()
        doc, errors = Parser(source, tokens).parse_document()
        self.assertEqual(lex_errors, [])
        self.assertEqual(errors, [])
        prop = doc.declarations[0].properties[0]
        self.assertEqual(source_text[prop.span.start_offset:prop.span.end_offset], 'text="A\\nB"')

    def test_property_span_ends_at_closing_quote(self):
        source_text = '<anzer start>\nanzer make paragraph: text="Hi";\n<anzer end>'
        source = Source(source_text, "span.anzer")
        tokens, lex_errors = Lexer(source).tokenize()
        doc, errors = Parser(source, tokens).parse_document()
        self.assertEqual(lex_errors, [])
        self.assertEqual(errors, [])
        prop = doc.declarations[0].properties[0]
        self.assertEqual(source_text[prop.span.start_offset:prop.span.end_offset], 'text="Hi"')

    def test_friendly_multiword_aliases_normalize(self):
        doc, lex, errors = self.parse('anzer make section: minimum width=200, maximum-height=400, font="Arial", text-size="18px";')
        self.assertEqual(lex, [])
        self.assertEqual(errors, [])
        self.assertEqual([p.name for p in doc.declarations[0].properties], ["min-width", "max-height", "font-family", "font-size"])

    def test_space_and_hyphen_spellings_normalize_equally(self):
        doc, lex, errors = self.parse('anzer make section: font style="italic", minimum   width=120;')
        self.assertEqual(lex, [])
        self.assertEqual(errors, [])
        self.assertEqual([p.name for p in doc.declarations[0].properties], ["font-style", "min-width"])

    def test_alias_duplicate_is_reported_after_normalization(self):
        doc, lex, errors = self.parse('anzer make paragraph: font="Arial", font-family="Roboto";')
        self.assertEqual(lex, [])
        self.assertTrue(any(d.code == "PARPROP005" for d in errors))
        self.assertEqual([p.name for p in doc.declarations[0].properties], ["font-family"])

    def test_equivalent_separators_and_aliases_report_duplicates_in_their_own_layers(self):
        doc, lex, errors = self.parse(
            'anzer make section style 1: minimum---width=20, min-width=30;' "\n"
            'anzer make section: use style="section style 1", text-size=12, font  size=16 {}'
        )
        self.assertEqual(lex, [])
        self.assertEqual([error.code for error in errors], ["PARPROP005", "PARPROP005"])
        self.assertEqual([error.location.line for error in errors], [2, 3])
        self.assertEqual([p.name for p in doc.declarations[0].properties], ["min-width"])
        self.assertEqual([p.name for p in doc.declarations[1].properties], ["font-size"])

    def test_multiple_properties_and_scalar_types(self):
        doc, lex, errors = self.parse('anzer make button: text="Go", width=120, active=true;')
        self.assertEqual(lex, [])
        self.assertEqual(errors, [])
        props = doc.declarations[0].properties
        self.assertEqual([p.name for p in props], ["text", "width", "active"])
        self.assertEqual([p.value for p in props], ["Go", 120, True])

    def test_numeric_conversion_error_reports_token_location_and_recovers(self):
        with patch("anzer.parser.int", side_effect=ValueError("conversion failed"), create=True) as convert:
            doc, lex, errors = self.parse(
                'anzer make paragraph: width=123, text="kept";\n'
                'anzer make paragraph: text="also kept";'
            )
        convert.assert_called_once_with("123")
        self.assertEqual(lex, [])
        error, = errors
        self.assertEqual((error.category, error.code), (DiagnosticCategory.SYNTAX, "PARPROP003"))
        self.assertEqual((error.location.line, error.location.column), (2, 29))
        self.assertEqual(
            [tuple((prop.name, prop.value) for prop in node.properties) for node in doc.declarations],
            [(("text", "kept"),), (("text", "also kept"),)],
        )

    def test_quoted_digits_and_bare_integer_keep_distinct_scalar_types(self):
        doc, lex, errors = self.parse('anzer make paragraph: text="123", width=120;')
        self.assertEqual((lex, errors), ([], []))
        text, width = doc.declarations[0].properties
        self.assertIs(type(text.value), str)
        self.assertEqual(text.value, "123")
        self.assertIs(type(width.value), int)
        self.assertEqual(width.value, 120)

    def test_empty_container(self):
        doc, lex, errors = self.parse("anzer make section {}")
        self.assertEqual(lex, [])
        self.assertEqual(errors, [])
        self.assertEqual(doc.declarations[0].children, ())

    def test_nested_container(self):
        doc, lex, errors = self.parse('anzer make section { anzer make paragraph: text="Inner"; }')
        self.assertEqual(lex, [])
        self.assertEqual(errors, [])
        outer = doc.declarations[0]
        self.assertEqual(len(outer.children), 1)
        self.assertEqual(outer.children[0].name, "paragraph")
        self.assertIsNone(outer.children[0].children)

    def test_missing_property_comma_reports_error(self):
        _, lex, errors = self.parse('anzer make button: text="Go" width=120;')
        self.assertEqual(lex, [])
        self.assertTrue(any(d.code == "PARPROP004" for d in errors))

    def test_missing_semicolon_reports_error(self):
        _, lex, errors = self.parse('anzer make paragraph: text="Hi"')
        self.assertEqual(lex, [])
        self.assertTrue(any(d.code == "PARDECL006" for d in errors))

    def test_unclosed_container_reports_error(self):
        _, lex, errors = self.parse("anzer make section { anzer make paragraph: text=\"Hi\";")
        self.assertEqual(lex, [])
        self.assertTrue(any(d.code == "PARDECL005" for d in errors))


if __name__ == "__main__":
    unittest.main()
