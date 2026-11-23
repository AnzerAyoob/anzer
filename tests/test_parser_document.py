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

    def test_trailing_whitespace_is_allowed(self):
        doc, lex, errors = self.parse("<anzer start>\r\n<anzer end> \r\n\t")
        self.assertEqual(lex, [])
        self.assertEqual(errors, [])
        self.assertEqual(doc.end_marker_span.end.offset, 26)

    def test_tokens_after_end_marker_are_rejected(self):
        document = '<anzer start>\nanzer make paragraph: text="kept";\n<anzer end>'
        for trailing in ('anzer make paragraph: text="outside";', '}'):
            with self.subTest(trailing=trailing):
                doc, lex, errors = self.parse(f"{document}\n  {trailing}")
                self.assertEqual(lex, [])
                self.assertEqual([d.code for d in errors], ["PARDOC006"])
                self.assertEqual(
                    errors[0].format("doc.anzer"),
                    "doc.anzer:4:3: error: Unexpected token after document end",
                )
                self.assertEqual([node.properties[0].value for node in doc.declarations], ["kept"])

    def test_repeated_markers_after_end_still_report_duplicate_markers(self):
        for marker in ("<anzer start>", "<anzer end>"):
            with self.subTest(marker=marker):
                _, lex, errors = self.parse(f"<anzer start>\n<anzer end>\n{marker}\n{marker}")
                self.assertEqual(lex, [])
                self.assertEqual([d.code for d in errors], ["PARDOC001", "PARDOC006"])
                self.assertEqual((errors[1].location.line, errors[1].location.column), (3, 1))

    def test_trailing_tokens_reported_even_if_statement_recovery_passes_end(self):
        _, lex, errors = self.parse("<anzer start>\nanzer nope\n<anzer end>\nanzer make paragraph;")
        self.assertEqual(lex, [])
        self.assertEqual([d.code for d in errors], ["PARDECL002", "PARDOC006"])
        self.assertEqual((errors[-1].location.line, errors[-1].location.column), (4, 1))


if __name__ == "__main__":
    unittest.main()
