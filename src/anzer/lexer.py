"""Lexer for the frozen Anzer v0.1 lexical rules."""
import re
from .source import Source
from .tokens import Token, TokenKind
from .diagnostics import Diagnostic, DiagnosticCategory

_NUMBER = re.compile(r"-?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)")
_WORD = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")
_PUNCTUATION = set(":,=;{}")

class Lexer:
    def __init__(self, source: Source):
        self.source = source
        self.text = source.text
        self.index = 0
        self.tokens = []
        self.diagnostics = []

    def _loc(self, offset):
        return self.source.location(offset)

    def _error(self, message, offset, code):
        self.diagnostics.append(Diagnostic(DiagnosticCategory.LEXICAL, message, self._loc(offset), code))

    def tokenize(self):
        while self.index < len(self.text):
            ch = self.text[self.index]
            if ch.isspace():
                self.index += 1
                continue
            start = self.index
            if self.text.startswith("<anzer start>", start):
                self.tokens.append(Token(TokenKind.MARKER, "start", self._loc(start)))
                self.index += len("<anzer start>")
                continue
            if self.text.startswith("<anzer end>", start):
                self.tokens.append(Token(TokenKind.MARKER, "end", self._loc(start)))
                self.index += len("<anzer end>")
                continue
            if ch == '"':
                self._string()
                continue
            if ch in _PUNCTUATION:
                self.tokens.append(Token(TokenKind.PUNCTUATION, ch, self._loc(start)))
                self.index += 1
                continue
            number = _NUMBER.match(self.text, start)
            if number:
                self.tokens.append(Token(TokenKind.NUMBER, number.group(0), self._loc(start)))
                self.index = number.end()
                continue
            word = _WORD.match(self.text, start)
            if word:
                value = word.group(0)
                kind = TokenKind.BOOLEAN if value in ("true", "false") else TokenKind.IDENTIFIER
                self.tokens.append(Token(kind, value, self._loc(start)))
                self.index = word.end()
                continue
            self._error(f"Unexpected character {ch!r}", start, "LEX001")
            self.index += 1
        self.tokens.append(Token(TokenKind.EOF, "", self._loc(len(self.text))))
        return self.tokens, self.diagnostics

    def _string(self):
        start = self.index
        self.index += 1
        chars = []
        escapes = {'"': '"', '\\': '\\', 'n': '\n', 'r': '\r', 't': '\t'}
        while self.index < len(self.text):
            ch = self.text[self.index]
            if ch == '"':
                self.index += 1
                self.tokens.append(Token(TokenKind.STRING, "".join(chars), self._loc(start)))
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
                if esc not in escapes:
                    self._error(f"Unsupported escape sequence \\{esc}", esc_offset, "LEX004")
                    self.index += 1
                    return
                chars.append(escapes[esc])
                self.index += 1
                continue
            chars.append(ch)
            self.index += 1
        self._error("Unterminated string", start, "LEX005")
