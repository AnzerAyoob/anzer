"""Serialize normalized style declarations and the document baseline."""

import re
from collections.abc import Mapping

from ..semantic import BOX_STYLES, LAYOUT_PROPERTIES, TEXT_STYLES

BASELINE_CSS = (
    "*, *::before, *::after { box-sizing: border-box; }\n"
    "body { margin: 0; }\n"
    "img { max-width: 100%; height: auto; }"
)
CSS_PROPERTIES = (TEXT_STYLES | BOX_STYLES | LAYOUT_PROPERTIES) - {"border", "gap"}

_GENERIC_FAMILIES = {
    "serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui",
    "ui-serif", "ui-sans-serif", "ui-monospace", "ui-rounded", "math",
}
_CSS_TOKENS = re.compile(r"[a-z0-9.%# -]+")
_CSS_STRING_ESCAPE = re.compile(r'["\\\x00-\x1f\x7f]')


def _font_family(value: str) -> str:
    families = []
    for name in value.split(", "):
        if name.lower() in _GENERIC_FAMILIES:
            families.append(name.lower())
        else:
            escaped = _CSS_STRING_ESCAPE.sub(lambda match: f"\\{ord(match[0]):x} ", name)
            families.append(f'"{escaped}"')
    return ", ".join(families)


def render_declarations(styles: Mapping[str, str]) -> str:
    declarations = []
    for name in sorted(styles):
        value = styles[name]
        if name == "font-family":
            value = _font_family(value)
        elif not _CSS_TOKENS.fullmatch(value):
            # Guard the CSS declaration boundary without rechecking property rules.
            raise ValueError(f"Cannot serialize normalized CSS value for {name!r}")
        declarations.append(f"{name}: {value};")
    return " ".join(declarations)
