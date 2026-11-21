"""Lexer for the frozen Anzer v0.1 lexical rules."""
import re
from .source import Source
from .tokens import Token, TokenKind
from .diagnostics import Diagnostic, DiagnosticCategory


_NUMBER = re.compile(r"-?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)")
_WORD = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")
_PUNCTUATION = set(":,=;{}")
_MARKERS = (("<anzer start>", "start"), ("<anzer end>", "end"))
_ESCAPES = {'"': '"', "\\": "\\", "n": "\n", "r": "\r", "t": "\t"}


class Lexer:
    def __init__(self, source: Source):
        self.source = source
        self.text = source.text
        self.index = 0
        self.tokens = []
        self.diagnostics = []

    def _error(self, message, offset, code):
        self.diagnostics.append(Diagnostic(DiagnosticCategory.LEXICAL, message, self.source.location(offset), code))

    def tokenize(self):
        while self.index < len(self.text):
            ch = self.text[self.index]
            if ch.isspace():
                self.index += 1
                continue
            start = self.index
            marker = next((m for m in _MARKERS if self.text.startswith(m[0], start)), None)
            if marker:
                self.tokens.append(Token(TokenKind.MARKER, marker[1], self.source.location(start)))
                self.index += len(marker[0])
                continue
            if ch == '"':
                self._string()
                continue
            if ch in _PUNCTUATION:
                self.tokens.append(Token(TokenKind.PUNCTUATION, ch, self.source.location(start)))
                self.index += 1
                continue
            number = _NUMBER.match(self.text, start)
            if number:
                self.tokens.append(Token(TokenKind.NUMBER, number.group(0), self.source.location(start)))
                self.index = number.end()
                continue
            word = _WORD.match(self.text, start)
            if word:
                value = word.group(0)
                kind = TokenKind.BOOLEAN if value in ("true", "false") else TokenKind.IDENTIFIER
                self.tokens.append(Token(kind, value, self.source.location(start)))
                self.index = word.end()
                continue
            self._error(f"Unexpected character {ch!r}", start, "LEX001")
            self.index += 1
        self.tokens.append(Token(TokenKind.EOF, "", self.source.location(len(self.text))))
        return self.tokens, self.diagnostics

    def _string(self):
        start = self.index
        self.index += 1
        chars = []
        while self.index < len(self.text):
            ch = self.text[self.index]
            if ch == '"':
                self.index += 1
                self.tokens.append(Token(TokenKind.STRING, "".join(chars), self.source.location(start)))
                return
            if ch in "\r\n":
                self._error("Raw newline inside quoted string", self.index, "LEX002")
                return
            if ch == "\\":
                esc_offset = self.index
                self.index += 1
                if self.index >= len(self.text):
                    self._error("Incomplete escape sequence", esc_offset, "LEX003")
                    return
                esc = self.text[self.index]
                if esc not in _ESCAPES:
                    self._error(f"Unsupported escape sequence \\\\{esc}", esc_offset, "LEX004")
                    self.index += 1
                    while self.index < len(self.text) and self.text[self.index] not in '"\\r\\n':
                        self.index += 1
                    if self.index < len(self.text) and self.text[self.index] == '"':
                        self.index += 1
                    return
                chars.append(_ESCAPES[esc])
                self.index += 1
                continue
            chars.append(ch)
            self.index += 1
        self._error("Unterminated string", start, "LEX005")
