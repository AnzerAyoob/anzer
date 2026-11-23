import json
from pathlib import Path
import subprocess
import sys
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

    def test_top_level_brace_recovery_terminates_and_keeps_following_declaration(self):
        parse_in_subprocess = """
import json
import sys
sys.path.insert(0, sys.argv[1])
from anzer.lexer import Lexer
from anzer.parser import Parser
from anzer.source import Source

source = Source(sys.stdin.read())
tokens, lexical = Lexer(source).tokenize()
document, syntax = Parser(source, tokens).parse_document()
print(json.dumps([
    [d.code for d in lexical],
    [[d.code, d.location.line, d.location.column] for d in syntax],
    [node.name for node in document.declarations],
]))
"""
        src = Path(__file__).resolve().parents[1] / "src"
        cases = (
            ("}", [["PARDECL001", 2, 1]]),
            ("}}\n}", [["PARDECL001", 2, 1], ["PARDECL001", 2, 2], ["PARDECL001", 3, 1]]),
            ("anzer nope }", [["PARDECL002", 2, 7], ["PARDECL001", 2, 12]]),
        )
        for body, expected in cases:
            with self.subTest(body=body):
                result = subprocess.run(
                    [sys.executable, "-B", "-c", parse_in_subprocess, str(src)],
                    input=f"<anzer start>\n{body}\nanzer make paragraph;\n<anzer end>",
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout), [[], expected, ["paragraph"]])

    def test_statement_recovery_leaves_closing_brace_for_enclosing_block(self):
        doc, lex, errors = self.parse("anzer make section { anzer nope }\nanzer make paragraph;")
        self.assertEqual(lex, [])
        self.assertEqual([d.code for d in errors], ["PARDECL002"])
        self.assertEqual([node.name for node in doc.declarations], ["section", "paragraph"])
        self.assertEqual(doc.declarations[0].children, ())
        self.assertEqual(doc.declarations[0].span.end.line, 2)


if __name__ == "__main__":
    unittest.main()
