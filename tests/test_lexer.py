import unittest
from anzer.source import Source
from anzer.lexer import Lexer
from anzer.tokens import TokenKind
from anzer.diagnostics import DiagnosticCategory


class LexerTests(unittest.TestCase):
    def lex(self, text):
        return Lexer(Source(text, "test.anzer")).tokenize()

    def test_document_markers(self):
        tokens, errors = self.lex("<anzer start>\n<anzer end>")
        self.assertEqual([t.value for t in tokens[:2],], ["start", "end"])
        self.assertEqual(errors, [])

    def test_all_escapes(self):
        tokens, errors = self.lex(r'"quote: \" slash: \\ newline: \n cr: \r tab: \t"')
        self.assertEqual(tokens[0].kind, TokenKind.STRING)
        self.assertEqual(tokens[0].value, 'quote: " slash: \\ newline: \n cr: \r tab: \t')
        self.assertEqual(errors, [])

    def test_marker_text_inside_string_is_content(self):
        tokens, errors = self.lex('"<anzer start>, <anzer end>"')
        self.assertEqual(tokens[0].value, "<anzer start>, <anzer end>")
        self.assertEqual(errors, [])

    def test_scalar_and_punctuation(self):
        tokens, errors = self.lex("true false -12 3.5 .5 : , = ; { }")
        self.assertEqual([t.kind for t in tokens[:5]], [TokenKind.BOOLEAN, TokenKind.BOOLEAN, TokenKind.NUMBER, TokenKind.NUMBER, TokenKind.NUMBER])
        self.assertEqual([t.value for t in tokens[5:11]], [":", ",", "=", ";", "{", "}"])
        self.assertEqual(errors, [])

    def test_number_token_boundaries_are_parser_responsibility(self):
        tokens, errors = self.lex("12abc 1. .5 -.5 --1 +1 1e3")
        self.assertEqual([t.value for t in tokens[:-1]], ["12", "abc", "1", "5", "-.5", "-1", "1", "e3"])
        self.assertEqual([d.code for d in errors], ["LEX001", "LEX001", "LEX001"])
        self.assertEqual(errors[0].location.column, 4)

    def test_exact_boolean_words(self):
        tokens, errors = self.lex("true false TRUE True truefalse")
        self.assertEqual([t.kind for t in tokens[:-1]], [TokenKind.BOOLEAN, TokenKind.BOOLEAN, TokenKind.IDENTIFIER, TokenKind.IDENTIFIER, TokenKind.IDENTIFIER])
        self.assertEqual(errors, [])

    def test_unicode_string_content(self):
        tokens, errors = self.lex('"مرحبا 中文 Sarazi ꯁ"')
        self.assertEqual(tokens[0].value, "مرحبا 中文 Sarazi ꯁ")
        self.assertEqual(errors, [])

    def test_partial_marker_is_not_marker(self):
        tokens, errors = self.lex("<anzer sta>")
        self.assertEqual([t.kind for t in tokens[:-1]], [TokenKind.IDENTIFIER, TokenKind.IDENTIFIER])
        self.assertEqual(len(errors), 2)
        self.assertTrue(all(d.code == "LEX001" for d in errors))

    def test_unknown_escape_diagnostic_and_recovery(self):
        tokens, errors = self.lex('"\\q" next')
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].code, "LEX004")
        self.assertEqual(errors[0].category, DiagnosticCategory.LEXICAL)
        self.assertEqual((errors[0].location.line, errors[0].location.column), (1, 2))
        self.assertEqual([t.value for t in tokens[:-1]], ["next"])

    def test_incomplete_escape_diagnostic(self):
        _, errors = self.lex('"abc\\')
        self.assertEqual(errors[0].code, "LEX003")

    def test_unterminated_string_diagnostic(self):
        _, errors = self.lex('"abc')
        self.assertEqual(errors[0].code, "LEX005")
        self.assertEqual((errors[0].location.line, errors[0].location.column), (1, 1))

    def test_raw_newline_diagnostic(self):
        _, errors = self.lex('"abc\ndef"')
        self.assertEqual(errors[0].code, "LEX002")
        self.assertEqual((errors[0].location.line, errors[0].location.column), (1, 5))

    def test_unexpected_character_location(self):
        _, errors = self.lex("abc\n  @")
        self.assertEqual(errors[0].code, "LEX001")
        self.assertEqual((errors[0].location.line, errors[0].location.column), (2, 3))

    def test_source_location_crlf(self):
        source = Source("one\r\ntwo\rthree")
        self.assertEqual((source.location(6).line, source.location(6).column), (2, 2))
        self.assertEqual((source.location(9).line, source.location(9).column), (3, 1))


if __name__ == "__main__":
    unittest.main()
