import unittest
from anzer.source import Source
from anzer.lexer import Lexer
from anzer.parser import Parser


class ParserRecoveryTests(unittest.TestCase):
    def parse(self, body):
        source = Source(f"<anzer start>\n{body}\n<anzer end>", "recovery.anzer")
        tokens, lex_errors = Lexer(source).tokenize()
        doc, errors = Parser(source, tokens).parse_document()
        return doc, lex_errors, errors

    def test_bad_declaration_does_not_block_following_declaration(self):
        doc, lex, errors = self.parse('anzer nope paragraph; anzer make paragraph: text="kept";')
        self.assertEqual(lex, [])
        self.assertTrue(errors)
        self.assertEqual([node.name for node in doc.declarations], ["paragraph"])

    def test_bad_property_value_recovers_to_next_property(self):
        doc, lex, errors = self.parse('anzer make button: text=, width=80;')
        self.assertEqual(lex, [])
        self.assertTrue(any(e.code == "PARPROP003" for e in errors))
        self.assertEqual([(p.name, p.value) for p in doc.declarations[0].properties], [("width", 80)])

    def test_unexpected_token_inside_container_is_recovered(self):
        doc, lex, errors = self.parse('anzer make section { junk; anzer make paragraph; }')
        self.assertEqual(lex, [])
        self.assertTrue(errors)
        self.assertEqual([node.name for node in doc.declarations[0].children], ["paragraph"])


if __name__ == "__main__":
    unittest.main()
