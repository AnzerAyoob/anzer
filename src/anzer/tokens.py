"""Token definitions for the Anzer v0.1 lexer."""
from dataclasses import dataclass
from enum import Enum
from .source import SourceLocation

class TokenKind(str, Enum):
    MARKER = "marker"
    IDENTIFIER = "identifier"
    NUMBER = "number"
    STRING = "string"
    BOOLEAN = "boolean"
    PUNCTUATION = "punctuation"
    EOF = "eof"

@dataclass(frozen=True)
class Token:
    kind: TokenKind
    value: str
    location: SourceLocation
