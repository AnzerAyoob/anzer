import unittest
from anzer.ast import StyleDeclaration
from anzer.source import Source
from anzer.lexer import Lexer
from anzer.parser import Parser


class StyleDeclarationParserTests(unittest.TestCase):
    def parse(self, body):
        source = Source(f"<anzer start>\n{body}\n<anzer end>", "style.anzer")
        tokens, lex_errors = Lexer(source).tokenize()
        document, parse_errors = Parser(source, tokens).parse_document()
        return document, lex_errors, parse_errors

    def test_style_declaration_parses_and_preserves_properties(self):
        doc, lex, errors = self.parse('anzer make paragraph style 1: font="Arial", color="black";')
        self.assertEqual(lex, [])
        self.assertEqual(errors, [])
        self.assertIsInstance(doc.declarations[0], StyleDeclaration)
        style = doc.declarations[0]
        self.assertEqual(style.name, "paragraph style 1")
        self.assertEqual(style.target_kind, "paragraph")
        self.assertEqual([p.name for p in style.properties], ["font-family", "color"])
        self.assertEqual([p.value for p in style.properties], ["Arial", "black"])

    def test_compact_style_declaration(self):
        doc, lex, errors = self.parse('anzer make container style 2: padding=20;')
        self.assertEqual(lex, [])
        self.assertEqual(errors, [])
        style = doc.declarations[0]
        self.assertEqual(style.name, "container style 2")
        self.assertEqual(style.target_kind, "container")
        self.assertEqual(style.properties[0].value, 20)

    def test_style_requires_integer_identifier(self):
        _, lex, errors = self.parse('anzer make paragraph style 1.5: color="red";')
        self.assertEqual(lex, [])
        self.assertTrue(any(d.code == "PARSTYLE001" for d in errors))


if __name__ == "__main__":
    unittest.main()
