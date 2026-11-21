import unittest
from anzer.source import Source
from anzer.lexer import Lexer
from anzer.parser import Parser


class ParserRecoveryAndSpanTests(unittest.TestCase):
    def parse(self, body):
        source = Source(f"<anzer start>\n{body}\n<anzer end>", "recovery-span.anzer")
        tokens, lex_errors = Lexer(source).tokenize()
        document, parse_errors = Parser(source, tokens).parse_document()
        return source, document, lex_errors, parse_errors

    def test_html_error_recovers_to_following_element(self):
        source, doc, lex, errors = self.parse('anzer use html=123; anzer make paragraph: text="ok";')
        self.assertEqual(lex, [])
        self.assertTrue(any(e.code == "PARHTML003" for e in errors))
        self.assertEqual([getattr(node, "name", None) for node in doc.declarations], ["paragraph"])

    def test_style_reference_error_recovers_to_following_element(self):
        source, doc, lex, errors = self.parse('anzer make paragraph: use style=1; anzer make button;')
        self.assertEqual(lex, [])
        self.assertTrue(any(e.code == "PARSTYLE005" for e in errors))
        self.assertEqual([node.name for node in doc.declarations], ["paragraph", "button"])

    def test_unclosed_container_preserves_style_reference(self):
        _, doc, lex, errors = self.parse('anzer make section: use style="section style 2" { anzer make paragraph;')
        self.assertEqual(lex, [])
        self.assertTrue(any(e.code == "PARDECL005" for e in errors))
        self.assertEqual(doc.declarations[0].style_reference, "section style 2")

    def test_element_span_covers_container_declaration(self):
        source, doc, lex, errors = self.parse('anzer make section { anzer make paragraph; }')
        self.assertEqual(lex, [])
        self.assertEqual(errors, [])
        node = doc.declarations[0]
        self.assertEqual(source.text[node.span.start_offset:node.span.end_offset], 'anzer make section { anzer make paragraph; }')

    def test_style_declaration_span_covers_full_statement(self):
        source, doc, lex, errors = self.parse('anzer make paragraph style 3: color="blue";')
        self.assertEqual(lex, [])
        self.assertEqual(errors, [])
        node = doc.declarations[0]
        self.assertEqual(source.text[node.span.start_offset:node.span.end_offset], 'anzer make paragraph style 3: color="blue";')


if __name__ == "__main__":
    unittest.main()
