"""Serialize the validated, normalized model into a complete HTML document."""

from html import escape

from ..normalize import NormalizedDocument, NormalizedElement, NormalizedHtml, NormalizedProperty
from ..semantic import CONTAINER_KINDS, DEFAULT_TAGS, TYPE_ALLOWED
from .css import BASELINE_CSS, CSS_PROPERTIES, render_declarations

_TAGS = frozenset(DEFAULT_TAGS.values()).union(*TYPE_ALLOWED.values())
_ATTRIBUTES = {
    "id": "id",
    "url": "href",
    "src": "src",
    "alt": "alt",
    "action": "data-anzer-action",
    "target": "data-anzer-target",
}
_DOCUMENT_START = (
    "<!doctype html>\n"
    "<html>\n<head>\n"
    '<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    "<title>Anzer document</title>\n"
    f"<style>\n{BASELINE_CSS}\n</style>\n"
    "</head>\n<body>"
)


def render_document(document: NormalizedDocument, *, allow_trusted_html: bool = False) -> str:
    """Render a document produced by normalize_document after successful validation.

    Callers must obtain explicit acknowledgement before enabling trusted HTML.
    Acknowledged fragments are inserted verbatim and can affect the whole page.
    """
    if not isinstance(document, NormalizedDocument):
        raise TypeError("Expected a normalized Anzer document")
    parts = [_DOCUMENT_START]
    for element in document.elements:
        _render_element(element, parts, allow_trusted_html)
    parts.append("</body>\n</html>\n")
    return "".join(parts)


def _escape(value: str, *, quote: bool) -> str:
    # HTML preprocessing would otherwise convert authored carriage returns to LF.
    return escape(value, quote=quote).replace("\r", "&#13;")


def _render_element(
    element: NormalizedElement, parts: list[str], allow_trusted_html: bool
) -> None:
    if not isinstance(element, NormalizedElement):
        raise ValueError("Expected a normalized element at this position")
    tag = element.tag
    if element.kind not in DEFAULT_TAGS or tag not in _TAGS:
        raise ValueError(f"Unsupported normalized element or tag: {element.kind!r}, {tag!r}")
    if element.shape not in {"leaf", "container", "void"} or (element.shape == "void") != (tag == "img"):
        raise ValueError(f"Unsupported shape for normalized tag {tag!r}")
    if element.children and element.shape != "container":
        raise ValueError("Only normalized containers can have children")

    attributes: dict[str, str] = {}
    styles: dict[str, str] = {}
    seen: set[str] = set()
    content = ""
    for prop in element.properties:
        if not isinstance(prop, NormalizedProperty) or not isinstance(prop.value, str):
            raise ValueError("Expected a normalized string property")
        name, value = prop.name, prop.value
        if name in seen:
            raise ValueError(f"Duplicate property in normalized element: {name!r}")
        seen.add(name)
        if name == "text":
            content = _escape(value, quote=False)
        elif name == "type":
            if tag == "button":
                attributes["type"] = value
            elif value != tag:
                raise ValueError("Normalized type does not match the resolved tag")
        elif name in _ATTRIBUTES:
            attributes[_ATTRIBUTES[name]] = value
        elif name in CSS_PROPERTIES:
            styles[name] = value
        else:
            raise ValueError(f"No renderer mapping for normalized property {name!r}")

    if styles:
        attributes["style"] = render_declarations(styles)
    rendered_attrs = "".join(
        f' {name}="{_escape(value, quote=True)}"' for name, value in sorted(attributes.items())
    )
    parts.append(f"<{tag}{rendered_attrs}>")
    if element.shape == "void":
        if "text" in seen:
            raise ValueError("A normalized void element cannot contain text")
        return

    parts.append(content)
    for child in element.children:
        if isinstance(child, NormalizedHtml):
            if element.kind not in CONTAINER_KINDS or tag not in {"div", "section"}:
                raise ValueError("Trusted HTML is only allowed inside section or container")
            if allow_trusted_html is not True:
                raise ValueError("Trusted HTML requires explicit acknowledgement")
            parts.append(child.html)
        else:
            _render_element(child, parts, allow_trusted_html)
    parts.append(f"</{tag}>")
