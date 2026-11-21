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
        prefix = self.text[:offset]
        line = 1 + prefix.count("\n") + prefix.count("\r") - prefix.count("\r\n")
        last_lf = prefix.rfind("\n")
        last_cr = prefix.rfind("\r")
        last_break = max(last_lf, last_cr)
        column = offset - last_break
        return SourceLocation(offset=offset, line=line, column=column)
