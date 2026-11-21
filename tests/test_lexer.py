import unittest
from anzer.source import Source
from anzer.lexer import Lexer
from anzer.tokens import TokenKind

class LexerTests(unittest.TestCase):
    def lex(self, text):
        return Lexer(Source(text)).tokenize()

    def test_document_markers(self):
        tokens, errors = self.lex("<anzer start><anzer end>")
        self.assertEqual([t.value for t in tokens[:2]], ["start", "end"])
        self.assertEqual(errors, [])

    def test_string_escape_decoding(self):
        tokens, errors = self.lex('"a\\nb"')
        self.assertEqual(tokens[0].kind, TokenKind.STRING)
        self.assertEqual(tokens[0].value, "a\nb")
        self.assertEqual(errors, [])

    def test_boolean_and_punctuation(self):
        tokens, errors = self.lex("true false : , = ; { }")
        self.assertEqual(tokens[0].kind, TokenKind.BOOLEAN)
        self.assertEqual([t.value for t in tokens[2:8]], [":", ",", "=", ";", "{", "}"])
        self.assertEqual(errors, [])

    def test_unknown_escape_reports_error(self):
        _, errors = self.lex('"\\q"')
        self.assertTrue(errors)
        self.assertEqual(errors[0].code, "LEX004")

if __name__ == "__main__":
    unittest.main()
