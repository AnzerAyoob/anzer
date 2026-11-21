import unittest
from anzer.source import Source
from anzer.lexer import Lexer
from anzer.parser import Parser


class DocumentParserTests(unittest.TestCase):
    def parse(self, text):
        source = Source(text, "doc.anzer")
        tokens, lex_errors = Lexer(source).tokenize()
        document, parse_errors = Parser(source, tokens).parse_document()
        return document, lex_errors, parse_errors

    def test_valid_marker_pair(self):
        doc, lex, parse = self.parse("<anzer start>\n<anzer end>")
        self.assertEqual(lex, [])
        self.assertEqual(parse, [])
        self.assertEqual(doc.start_marker_span.start.offset, 0)
        self.assertEqual(doc.end_marker_span.start.offset, 14)

    def test_missing_start_marker(self):
        _, _, errors = self.parse("anzer make paragraph: text=\"Hi\";\n<anzer end>")
        self.assertTrue(any(d.code == "PARDOC002" for d in errors))

    def test_missing_end_marker(self):
        _, _, errors = self.parse("<anzer start>\nanzer make paragraph: text=\"Hi\";")
        self.assertTrue(any(d.code == "PARDOC003" for d in errors))

    def test_reversed_markers(self):
        _, _, errors = self.parse("<anzer end>\n<anzer start>")
        self.assertTrue(any(d.code == "PARDOC004" for d in errors))

    def test_duplicate_markers(self):
        _, _, errors = self.parse("<anzer start>\n<anzer start>\n<anzer end>")
        self.assertTrue(any(d.code == "PARDOC001" for d in errors))

    def test_simple_declaration_is_parsed(self):
        doc, lex, errors = self.parse("<anzer start>\nanzer make paragraph: text=\"Hi\";\n<anzer end>")
        self.assertEqual(lex, [])
        self.assertEqual(errors, [])
        self.assertEqual(len(doc.declarations), 1)
        self.assertEqual(doc.declarations[0].name, "paragraph")
        self.assertEqual(doc.declarations[0].properties[0].value, "Hi")


if __name__ == "__main__":
    unittest.main()
