"""Source text and location utilities."""
from dataclasses import dataclass

@dataclass(frozen=True)
class SourceLocation:
    offset: int
    line: int
    column: int

@dataclass(frozen=True)
class Source:
    text: str
    name: str = "<source>"

    def location(self, offset: int) -> SourceLocation:
        offset = max(0, min(offset, len(self.text)))
        line = self.text.count("\n", 0, offset) + 1
        last_newline = self.text.rfind("\n", 0, offset)
        column = offset - last_newline
        return SourceLocation(offset=offset, line=line, column=column)
