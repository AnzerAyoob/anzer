import unittest
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
        source_text = '<anzer start>\\nanzer make paragraph: text="A\\\\nB";\\n<anzer end>'
        source = Source(source_text, "span.anzer")
        tokens, lex_errors = Lexer(source).tokenize()
        doc, errors = Parser(source, tokens).parse_document()
        self.assertEqual(lex_errors, [])
        self.assertEqual(errors, [])
        prop = doc.declarations[0].properties[0]
        self.assertEqual(source_text[prop.span.start_offset:prop.span.end_offset], 'text="A\\\\nB"')

    def test_property_span_ends_at_closing_quote(self):
        source_text = '<anzer start>\\nanzer make paragraph: text="Hi";\\n<anzer end>'
        source = Source(source_text, "span.anzer")
        tokens, lex_errors = Lexer(source).tokenize()
        doc, errors = Parser(source, tokens).parse_document()
        self.assertEqual(lex_errors, [])
        self.assertEqual(errors, [])
        prop = doc.declarations[0].properties[0]
        self.assertEqual(source_text[prop.span.start_offset:prop.span.end_offset], 'text="Hi"')

    def test_multiple_properties_and_scalar_types(self):
        doc, lex, errors = self.parse('anzer make button: text="Go", width=120, active=true;')
        self.assertEqual(lex, [])
        self.assertEqual(errors, [])
        props = doc.declarations[0].properties
        self.assertEqual([p.name for p in props], ["text", "width", "active"])
        self.assertEqual([p.value for p in props], ["Go", 120, True])

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
