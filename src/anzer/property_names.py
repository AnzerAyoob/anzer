"""Canonical Anzer v0.1 property spellings shared by parser and validator."""

ALIASES = {
    "font": "font-family",
    "text-size": "font-size",
    "minimum-width": "min-width",
    "maximum-width": "max-width",
    "minimum-height": "min-height",
    "maximum-height": "max-height",
}


def canonical_property_name(name: str) -> str:
    normalized = "-".join(name.replace("-", " ").split())
    return ALIASES.get(normalized, normalized)
