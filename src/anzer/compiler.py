"""Shared in-memory analysis for Anzer commands."""

from dataclasses import dataclass
from typing import Literal

from .ast import Document
from .diagnostics import Diagnostic
from .lexer import Lexer
from .parser import Parser
from .semantic import SemanticResult, SemanticValidator
from .source import Source


AnalysisStage = Literal["lexing", "parsing", "semantic analysis"]


@dataclass(frozen=True)
class AnalysisResult:
    source: Source
    document: Document | None = None
    semantic_result: SemanticResult | None = None
    diagnostics: tuple[Diagnostic, ...] = ()
    failed_stage: AnalysisStage | None = None


class AnalysisFailure(RuntimeError):
    """An unexpected exception from a specific compiler stage."""

    def __init__(self, stage: AnalysisStage):
        super().__init__(stage)
        self.stage = stage


def analyze_source(source: Source) -> AnalysisResult:
    """Run the existing compiler stages through semantic analysis."""
    stage: AnalysisStage = "lexing"
    try:
        tokens, lexical = Lexer(source).tokenize()
        if lexical:
            return AnalysisResult(source, diagnostics=tuple(lexical), failed_stage=stage)

        stage = "parsing"
        document, syntax = Parser(source, tokens).parse_document()
        if syntax:
            return AnalysisResult(source, diagnostics=tuple(syntax), failed_stage=stage)

        stage = "semantic analysis"
        semantic = SemanticValidator().analyze(document)
    except Exception as error:
        raise AnalysisFailure(stage) from error

    if semantic.diagnostics:
        return AnalysisResult(
            source, document, diagnostics=semantic.diagnostics, failed_stage=stage
        )
    return AnalysisResult(source, document, semantic)
