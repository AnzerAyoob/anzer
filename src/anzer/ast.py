"""Immutable syntax AST for Anzer v0.1.

The AST records source structure only. Semantic validation and normalization must
produce separate representations rather than mutating these nodes.
"""
from dataclasses import dataclass
from typing import TypeAlias

from .source import SourceLocation


@dataclass(frozen=True)
class SourceSpan:
    start: SourceLocation
    end: SourceLocation

    @property
    def start_offset(self) -> int:
        return self.start.offset

    @property
    def end_offset(self) -> int:
        return self.end.offset


ScalarValue: TypeAlias = str | int | float | bool


@dataclass(frozen=True)
class PropertyAssignment:
    name: str
    value: ScalarValue
    span: SourceSpan


@dataclass(frozen=True)
class ElementDeclaration:
    name: str
    properties: tuple[PropertyAssignment, ...]
    children: tuple["Declaration", ...] | None
    style_reference: str | None
    span: SourceSpan


@dataclass(frozen=True)
class StyleDeclaration:
    name: str
    target_kind: str
    properties: tuple[PropertyAssignment, ...]
    span: SourceSpan


@dataclass(frozen=True)
class HtmlEmbedding:
    html: str
    span: SourceSpan


Declaration: TypeAlias = ElementDeclaration | StyleDeclaration | HtmlEmbedding


@dataclass(frozen=True)
class Document:
    start_marker_span: SourceSpan
    end_marker_span: SourceSpan
    declarations: tuple[Declaration, ...]
    span: SourceSpan
