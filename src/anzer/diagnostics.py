"""Diagnostic model used by lexer, parser, validation and compiler."""
from dataclasses import dataclass
from enum import Enum
from .source import SourceLocation


class DiagnosticCategory(str, Enum):
    LEXICAL = "lexical"
    SYNTAX = "syntax"
    SEMANTIC = "semantic"
    VALIDATION = "validation"


@dataclass(frozen=True)
class Diagnostic:
    category: DiagnosticCategory
    message: str
    location: SourceLocation | None = None
    code: str | None = None
    severity: str = "error"

    def format(self, source_name: str = "<source>") -> str:
        if self.location is None:
            return f"{source_name}: {self.severity}: {self.message}"
        return f"{source_name}:{self.location.line}:{self.location.column}: {self.severity}: {self.message"
