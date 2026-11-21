import unittest
from anzer.ast import HtmlEmbedding
from anzer.source import Source
from anzer.lexer import Lexer
from anzer.parser import Parser


class HtmlEmbeddingParserTests(unittest.TestCase):
    def parse(self, body):
        source = Source(f"<anzer start>\n{body}\n<anzer end>", "html.anzer")
        tokens, lex_errors = Lexer(source).tokenize()
        document, parse_errors = Parser(source, tokens).parse_document()
        return source, document, lex_errors, parse_errors

    def test_html_embedding_parses_as_ast_node(self):
        _, doc, lex, errors = self.parse('anzer use html="<strong>Hello</strong>";')
        self.assertEqual(lex, [])
        self.assertEqual(errors, [])
        node = doc.declarations[0]
        self.assertIsInstance(node, HtmlEmbedding)
        self.assertEqual(node.html, "<strong>Hello</strong>")

    def test_html_embedding_span_includes_declaration(self):
        source, doc, lex, errors = self.parse('anzer use html="<em>Hi</em>";')
        self.assertEqual(lex, [])
        self.assertEqual(errors, [])
        node = doc.declarations[0]
        self.assertEqual(source.text[node.span.start_offset:node.span.end_offset], 'anzer use html="<em>Hi</em>";')

    def test_html_embedding_requires_string(self):
        _, _, lex, errors = self.parse("anzer use html=123;")
        self.assertEqual(lex, [])
        self.assertTrue(any(d.code == "PARHTML003" for d in errors))

    def test_html_embedding_requires_semicolon(self):
        _, _, lex, errors = self.parse('anzer use html="<b>Hi</b>"')
        self.assertEqual(lex, [])
        self.assertTrue(any(d.code == "PARHTML004" for d in errors))


if __name__ == "__main__":
    unittest.main()
