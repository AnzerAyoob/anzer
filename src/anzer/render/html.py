"""Serialize the validated, normalized model into a complete HTML document."""

from dataclasses import dataclass
from html import escape

from ..normalize import NormalizedDocument, NormalizedElement, NormalizedHtml, NormalizedProperty
from ..semantic import CONTAINER_KINDS, DEFAULT_TAGS, TYPE_ALLOWED
from .css import BASELINE_CSS, CSS_PROPERTIES, render_declarations
from .runtime import TOGGLE_CSS, TOGGLE_SCRIPT

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
    f"<style>\n{BASELINE_CSS}"
)


@dataclass(frozen=True)
class _ToggleTarget:
    key: str
    initially_collapsed: bool


def _prepare_toggle_targets(document: NormalizedDocument) -> dict[str, _ToggleTarget]:
    references: set[str] = set()
    candidates: dict[str, bool] = {}
    pending = list(reversed(document.elements))
    while pending:
        node = pending.pop()
        if not isinstance(node, NormalizedElement):
            continue
        pending.extend(reversed(node.children))
        if node.toggle is not None:
            references.add(node.toggle.target_id)
        if node.kind in CONTAINER_KINDS and node.shape == "container":
            properties = {
                prop.name: prop.value for prop in node.properties
                if isinstance(prop, NormalizedProperty)
            }
            if "id" in properties:
                candidates[properties["id"]] = properties.get("display") == "none"
    return {
        target_id: _ToggleTarget(str(index), collapsed)
        for index, (target_id, collapsed) in enumerate(
            ((name, collapsed) for name, collapsed in candidates.items() if name in references),
            start=1,
        )
    }


def render_document(document: NormalizedDocument, *, allow_trusted_html: bool = False) -> str:
    """Render a document produced by normalize_document after successful validation.

    Callers must obtain explicit acknowledgement before enabling trusted HTML.
    Acknowledged fragments are inserted verbatim and can affect the whole page.
    """
    if not isinstance(document, NormalizedDocument):
        raise TypeError("Expected a normalized Anzer document")
    toggle_targets = _prepare_toggle_targets(document)
    parts = [_DOCUMENT_START]
    if toggle_targets:
        parts.append(f"\n{TOGGLE_CSS}")
    parts.append("\n</style>\n</head>\n<body>")
    for element in document.elements:
        _render_element(element, parts, allow_trusted_html, toggle_targets)
    if toggle_targets:
        parts.append(f"\n<script>\n{TOGGLE_SCRIPT}\n</script>\n")
    parts.append("</body>\n</html>\n")
    return "".join(parts)


def _escape(value: str, *, quote: bool) -> str:
    # HTML preprocessing would otherwise convert authored carriage returns to LF.
    return escape(value, quote=quote).replace("\r", "&#13;")


def _render_element(
    element: NormalizedElement,
    parts: list[str],
    allow_trusted_html: bool,
    toggle_targets: dict[str, _ToggleTarget],
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

    target = toggle_targets.get(attributes.get("id", ""))
    if target is not None and element.kind in CONTAINER_KINDS:
        attributes["data-anzer-toggle-target"] = target.key
        if target.initially_collapsed:
            attributes["data-anzer-display"] = "none"
            attributes["hidden"] = ""
    if element.toggle is not None and element.toggle.target_id in toggle_targets:
        target = toggle_targets[element.toggle.target_id]
        attributes["data-anzer-toggle-key"] = target.key
        attributes["aria-expanded"] = "false" if target.initially_collapsed else "true"

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
            _render_element(child, parts, allow_trusted_html, toggle_targets)
    parts.append(f"</{tag}>")
