"""Document-level parser foundation for Anzer v0.1."""
from .ast import Document, SourceSpan
from .diagnostics import Diagnostic, DiagnosticCategory
from .source import Source
from .tokens import TokenKind


_MARKER_LENGTHS = {"start": len("<anzer start>"), "end": len("<anzer end>")}


class Parser:
    def __init__(self, source: Source, tokens):
        self.source = source
        self.tokens = tokens
        self.index = 0
        self.diagnostics = []

    def _current(self):
        return self.tokens[min(self.index, len(self.tokens) - 1)]

    def _advance(self):
        token = self._current()
        if token.kind != TokenKind.EOF:
            self.index += 1
        return token

    def _error(self, message, token=None, code="PAR001"):
        token = token or self._current()
        self.diagnostics.append(Diagnostic(
            DiagnosticCategory.SYNTAX, message, token.location, code
        ))

    def parse_document(self):
        markers = [t for t in self.tokens if t.kind == TokenKind.MARKER]
        start = next((t for t in markers if t.value == "start"), None)
        end = next((t for t in markers if t.value == "end"), None)

        if len(markers) != 2:
            self._error("Document must contain exactly one start and one end marker", markers[0] if markers else self._current(), "PARDOC001")
        if start is None:
            self._error("Missing <anzer start> marker", markers[0] if markers else self._current(), "PARDOC002")
        if end is None:
            self._error("Missing <anzer end> marker", markers[-1] if markers else self._current(), "PARDOC003")
        if start is not None and end is not None and start.location.offset >= end.location.offset:
            self._error("<anzer start> must precede <anzer end>", end, "PARDOC004")

        if start is not None and end is not None:
            start_end = start.location.offset + _MARKER_LENGTHS["start"]
            end_end = end.location.offset + _MARKER_LENGTHS["end"]
            doc_start = start.location.offset
            doc_end = end_end
        else:
            first = self.tokens[0].location.offset if self.tokens else 0
            eof = self.tokens[-1].location.offset if self.tokens else len(self.source.text)
            start_end = first
            end_end = eof
            doc_start, doc_end = first, eof

        for token in self.tokens:
            if token.kind == TokenKind.EOF:
                continue
            if token.kind == TokenKind.MARKER:
                continue
            if start is None or end is None or token.location.offset < start_end or token.location.offset >= end.location.offset:
                self._error("Unexpected token outside document markers", token, "PARDOC005")
            else:
                self._error("Declaration parsing is not implemented yet", token, "PARDOC006")

        start_span = self._span(start.location.offset, start_end) if start else self._span(doc_start, start_end)
        end_span = self._span(end.location.offset, end_end) if end else self._span(doc_end, end_end)
        document_span = self._span(doc_start, doc_end)
        return Document(start_span, end_span, (), document_span), self.diagnostics

    def _span(self, start, end):
        return SourceSpan(self.source.location(start), self.source.location(end))
