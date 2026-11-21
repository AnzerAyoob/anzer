import unittest
from anzer.source import Source
from anzer.lexer import Lexer
from anzer.parser import Parser


class StyleReferenceParserTests(unittest.TestCase):
    def parse(self, body):
        source = Source(f"<anzer start>\\n{body}\\n<anzer end>", "style-reference.anzer")
        tokens, lex_errors = Lexer(source).tokenize()
        document, parse_errors = Parser(source, tokens).parse_document()
        return document, lex_errors, parse_errors

    def test_style_reference_is_separated_from_direct_properties(self):
        doc, lex, errors = self.parse('anzer make paragraph: use style="paragraph style 1", text="Hello";')
        self.assertEqual(lex, [])
        self.assertEqual(errors, [])
        element = doc.declarations[0]
        self.assertEqual(element.style_reference, "paragraph style 1")
        self.assertEqual([(p.name, p.value) for p in element.properties], [("text", "Hello")])

    def test_style_reference_on_container(self):
        doc, lex, errors = self.parse('anzer make section: use style="section style 2" { anzer make paragraph; }')
        self.assertEqual(lex, [])
        self.assertEqual(errors, [])
        element = doc.declarations[0]
        self.assertEqual(element.style_reference, "section style 2")
        self.assertEqual(len(element.children), 1)

    def test_non_string_style_reference_reports_error(self):
        _, lex, errors = self.parse('anzer make paragraph: use style=1;')
        self.assertEqual(lex, [])
        self.assertTrue(any(d.code == "PARSTYLE005" for d in errors))

    def test_duplicate_style_reference_reports_error(self):
        _, lex, errors = self.parse('anzer make paragraph: use style="paragraph style 1", use style="paragraph style 2";')
        self.assertEqual(lex, [])
        self.assertTrue(any(d.code == "PARSTYLE006" for d in errors))


if __name__ == "__main__":
    unittest.main()
