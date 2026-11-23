import os
from pathlib import Path
import subprocess
import sysconfig
import tempfile
import unittest
from unittest.mock import patch

from anzer.compiler import analyze_source
from anzer.diagnostics import DiagnosticCategory
from anzer.lexer import Lexer
from anzer.parser import Parser
from anzer.semantic import SemanticValidator
from anzer.source import Source
from anzer.tokens import TokenKind


_REPRODUCERS = (
    ("semicolon", 'anzer make paragraph: text="Hello" ";"', '";"', "PARPROP004", 36),
    ("equals", 'anzer make paragraph: text "=" "Hello";', '"="', "PARPROP002", 28),
    ("brace", 'anzer make section { anzer make paragraph: text="Hello"; "}"', '"}"', "PARDECL001", 58),
)


def _source(body):
    return Source(f"<anzer start>\n{body}\n<anzer end>\n")


class PunctuationParserTests(unittest.TestCase):
    def parse(self, source):
        tokens, lexical = Lexer(source).tokenize()
        self.assertEqual(lexical, [])
        document, diagnostics = Parser(source, tokens).parse_document()
        return document, diagnostics, tokens

    def test_quoted_punctuation_cannot_replace_syntax(self):
        more_cases = (
            ('anzer make paragraph ":" text="Hello";', '":"', "PARDECL006"),
            ('anzer make paragraph: text="Hello" "," color="red";', '","', "PARPROP004"),
            ('anzer make section "{" }', '"{"', "PARDECL006"),
            ('anzer make paragraph ";"', '";"', "PARDECL006"),
            ('anzer make paragraph style 1 ":" color="red";', '":"', "PARSTYLE002"),
            ('anzer make paragraph style 1: color="red" ";"', '";"', "PARPROP004"),
            ('anzer make section { anzer use html "=" "<b>Hello</b>"; }', '"="', "PARHTML002"),
            ('anzer make section { anzer use html="<b>Hello</b>" ";" }', '";"', "PARHTML004"),
        )
        cases = [(body, spelling, code, column) for _, body, spelling, code, column in _REPRODUCERS]
        cases.extend(
            (body, spelling, code, body.index(spelling) + 1) for body, spelling, code in more_cases
        )
        for body, spelling, code, column in cases:
            with self.subTest(body=body):
                _, diagnostics, tokens = self.parse(_source(body))
                self.assertTrue(diagnostics)
                error = diagnostics[0]
                self.assertEqual(error.code, code)
                self.assertIs(error.category, DiagnosticCategory.SYNTAX)
                self.assertEqual((error.location.line, error.location.column), (2, column))
                token, = [token for token in tokens if token.location == error.location]
                self.assertIs(token.kind, TokenKind.STRING)
                self.assertEqual(token.value, spelling[1:-1])

    def test_real_punctuation_preserves_nested_content_and_spans(self):
        body = (
            'anzer make paragraph style 1: color="red";\n'
            'anzer make section { anzer make container {\n'
            '  anzer make paragraph: use style="paragraph style 1", text=":";\n'
            '  anzer make paragraph: text=","; anzer make paragraph: text="=";\n'
            '  anzer make paragraph: text=";"; anzer make paragraph: text="{";\n'
            '  anzer make paragraph: text="}"; anzer use html="<b>:,=;{}()</b>";\n'
            '} }\n'
            'anzer make paragraph: text="<anzer start> <anzer end> (text)";'
        )
        source = _source(body)
        document, diagnostics, tokens = self.parse(source)
        self.assertEqual(diagnostics, [])
        self.assertEqual(
            {token.value for token in tokens if token.kind == TokenKind.PUNCTUATION}, set(":,=;{}")
        )
        self.assertEqual([token.value for token in tokens if token.kind == TokenKind.MARKER], ["start", "end"])
        style, section, following = document.declarations
        container, = section.children
        first, *middle, embedding = container.children
        children = (first, *middle)
        self.assertEqual([node.properties[0].value for node in children], list(":,=;{}"))
        self.assertEqual(first.style_reference, style.name)
        for node, value in zip(children, ":,=;{}"):
            prop = node.properties[0]
            self.assertEqual(source.text[prop.span.start_offset:prop.span.end_offset], f'text="{value}"')
        self.assertEqual(embedding.html, "<b>:,=;{}()</b>")
        self.assertEqual(following.properties[0].value, "<anzer start> <anzer end> (text)")
        self.assertEqual(source.text[section.span.end_offset - 3:section.span.end_offset], "} }")

    def test_statement_recovery_ignores_quoted_semicolon_and_closing_brace(self):
        source = _source(
            'anzer make section {\n'
            'anzer nope "}" ";" junk;\n'
            'anzer make container { anzer make paragraph: text="kept"; }\n'
            '}\n'
            'anzer make paragraph: text="after";'
        )
        document, diagnostics, _ = self.parse(source)
        self.assertEqual([(d.code, d.location.line, d.location.column) for d in diagnostics], [
            ("PARDECL002", 3, 7),
        ])
        section, following = document.declarations
        container, = section.children
        paragraph, = container.children
        self.assertEqual(paragraph.properties[0].value, "kept")
        self.assertEqual(following.properties[0].value, "after")

    def test_property_recovery_ignores_quoted_comma_and_braces(self):
        body = 'anzer make paragraph: broken "," "{" "}" , text="kept", color="red";'
        document, diagnostics, _ = self.parse(_source(body))
        self.assertEqual([(d.code, d.location.line, d.location.column) for d in diagnostics], [
            ("PARPROP002", 2, body.index('","') + 1),
        ])
        paragraph, = document.declarations
        self.assertEqual([(p.name, p.value) for p in paragraph.properties], [
            ("text", "kept"), ("color", "red"),
        ])

    def test_quoted_punctuation_after_document_end_is_still_reported(self):
        document, diagnostics, _ = self.parse(Source('<anzer start>\n<anzer end>\n  "}"'))
        self.assertEqual(document.declarations, ())
        self.assertEqual([(d.code, d.location.line, d.location.column) for d in diagnostics], [
            ("PARDOC006", 3, 3),
        ])

    def test_syntax_failure_does_not_call_semantic_analysis(self):
        for name, body, _, code, _ in _REPRODUCERS:
            with self.subTest(name=name), patch.object(SemanticValidator, "analyze") as analyze:
                result = analyze_source(_source(body))
                analyze.assert_not_called()
                self.assertEqual(result.failed_stage, "parsing")
                self.assertEqual(result.diagnostics[0].code, code)


class InstalledPunctuationTests(unittest.TestCase):
    def test_check_and_compile_reject_quoted_delimiters_without_output(self):
        launcher = Path(sysconfig.get_path("scripts")) / ("anzer.exe" if os.name == "nt" else "anzer")
        if not launcher.is_file():
            self.skipTest("The anzer console entry point is not installed in this interpreter")
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for name, body, _, code, column in _REPRODUCERS:
                with self.subTest(name=name):
                    path = directory / f"{name}.anzer"
                    original = _source(body).text.encode("utf-8")
                    path.write_bytes(original)
                    siblings = set(directory.iterdir())
                    for command in ("check", "compile"):
                        result = subprocess.run(
                            [str(launcher), command, path.name], cwd=directory,
                            capture_output=True, timeout=8,
                        )
                        self.assertEqual((result.returncode, result.stdout), (1, b""), result.stderr)
                        self.assertTrue(
                            result.stderr.startswith(f"{path.name}:2:{column}: error[syntax/{code}]: ".encode()),
                            result.stderr,
                        )
                        self.assertEqual(set(directory.iterdir()), siblings)
                        self.assertEqual(path.read_bytes(), original)
