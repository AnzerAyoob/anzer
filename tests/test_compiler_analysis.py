import unittest
from unittest.mock import patch

from anzer.compiler import AnalysisFailure, analyze_source
from anzer.diagnostics import Diagnostic, DiagnosticCategory
from anzer.lexer import Lexer
from anzer.normalize import normalize_document
from anzer.parser import Parser
from anzer.render import render_document
from anzer.semantic import SemanticValidator
from anzer.source import Source


class CompilerAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.source = Source(
            '<anzer start>\nanzer make paragraph: text="Hello";\n<anzer end>',
            "sample.anzer",
        )

    def test_success_retains_source_document_and_semantic_result(self):
        tokens, _ = Lexer(self.source).tokenize()
        document, _ = Parser(self.source, tokens).parse_document()
        semantic = SemanticValidator().analyze(document)

        with (
            patch.object(Parser, "parse_document", return_value=(document, [])),
            patch.object(SemanticValidator, "analyze", return_value=semantic) as analyze,
            patch("anzer.normalize.normalize_document", wraps=normalize_document) as normalize,
            patch("anzer.render.render_document", wraps=render_document) as render,
        ):
            result = analyze_source(self.source)

        analyze.assert_called_once_with(document)
        normalize.assert_not_called()
        render.assert_not_called()
        self.assertIs(result.source, self.source)
        self.assertIs(result.document, document)
        self.assertIs(result.semantic_result, semantic)
        self.assertIs(result.semantic_result.document, result.document)
        self.assertEqual(result.diagnostics, ())
        self.assertIsNone(result.failed_stage)

    def test_lexical_failure_preserves_diagnostics_without_parsing(self):
        first = Diagnostic(DiagnosticCategory.LEXICAL, "First", code="LEX001")
        second = Diagnostic(DiagnosticCategory.LEXICAL, "Second", code="LEX002")
        with (
            patch.object(Lexer, "tokenize", return_value=([], [first, second])),
            patch.object(Parser, "parse_document") as parse,
            patch.object(SemanticValidator, "analyze") as analyze,
        ):
            result = analyze_source(self.source)

        parse.assert_not_called()
        analyze.assert_not_called()
        self.assertEqual(result.failed_stage, "lexing")
        self.assertIs(result.source, self.source)
        self.assertIsNone(result.document)
        self.assertIsNone(result.semantic_result)
        self.assertEqual(result.diagnostics, (first, second))
        self.assertIs(result.diagnostics[0], first)
        self.assertIs(result.diagnostics[1], second)

    def test_syntax_failure_does_not_analyze_a_partial_document(self):
        source = Source("<anzer start>\nanzer nope;\n<anzer end>")
        tokens, _ = Lexer(source).tokenize()
        partial, diagnostics = Parser(source, tokens).parse_document()
        with (
            patch.object(Parser, "parse_document", return_value=(partial, diagnostics)),
            patch.object(SemanticValidator, "analyze") as analyze,
        ):
            result = analyze_source(source)

        analyze.assert_not_called()
        self.assertEqual(result.failed_stage, "parsing")
        self.assertIsNone(result.document)
        self.assertIsNone(result.semantic_result)
        self.assertIs(result.diagnostics[0], diagnostics[0])

    def test_semantic_failure_retains_parsed_document_and_original_diagnostics(self):
        source = Source("<anzer start>\nanzer make unknown;\n<anzer end>")
        tokens, _ = Lexer(source).tokenize()
        document, _ = Parser(source, tokens).parse_document()
        semantic = SemanticValidator().analyze(document)
        with (
            patch.object(Parser, "parse_document", return_value=(document, [])),
            patch.object(SemanticValidator, "analyze", return_value=semantic),
        ):
            result = analyze_source(source)

        self.assertEqual(result.failed_stage, "semantic analysis")
        self.assertIs(result.document, document)
        self.assertIsNone(result.semantic_result)
        self.assertIs(result.diagnostics, semantic.diagnostics)

    def test_unexpected_exception_retains_stage_and_cause(self):
        for implementation, method, stage in (
            (Lexer, "tokenize", "lexing"),
            (Parser, "parse_document", "parsing"),
            (SemanticValidator, "analyze", "semantic analysis"),
        ):
            with self.subTest(stage=stage):
                cause = ValueError("internal details")
                with patch.object(implementation, method, side_effect=cause):
                    with self.assertRaises(AnalysisFailure) as raised:
                        analyze_source(self.source)
                self.assertEqual(raised.exception.stage, stage)
                self.assertIs(raised.exception.__cause__, cause)
