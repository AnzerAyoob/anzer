"""Semantic validation for Anzer v0.1 parsed documents.

This module intentionally does not mutate or normalize the immutable AST.
"""
from .ast import Document, ElementDeclaration, StyleDeclaration, HtmlEmbedding
from .diagnostics import Diagnostic, DiagnosticCategory

ELEMENT_KINDS = {"title", "paragraph", "button", "link", "image", "section", "container"}
CONTAINER_KINDS = {"section", "container"}


class SemanticValidator:
    def __init__(self):
        self.diagnostics = []

    def _error(self, message, span, code):
        self.diagnostics.append(Diagnostic(
            DiagnosticCategory.SEMANTIC, message,
            span.start if span else None, code
        ))

    def validate(self, document: Document):
        self.diagnostics = []
        styles = {}
        for declaration in document.declarations:
            if isinstance(declaration, StyleDeclaration):
                if declaration.target_kind not in ELEMENT_KINDS:
                    self._error(f"Unknown style target '{declaration.target_kind}'", declaration.span, "SEMSTYLE001")
                if declaration.name in styles:
                    self._error(f"Duplicate style declaration '{declaration.name}'", declaration.span, "SEMSTYLE002")
                else:
                    styles[declaration.name] = declaration

        self._validate_nodes(document.declarations, styles, parent_kind=None)
        return self.diagnostics

    def _validate_url(self, value, allowed, span, code):
        value = str(value).strip()
        if not value or value.startswith("//"):
            self._error("Invalid or protocol-relative URL", span, code)
            return
        from urllib.parse import urlparse
        parsed = urlparse(value)
        if parsed.scheme and parsed.scheme.lower() not in allowed:
            self._error(f"Unsupported URL scheme '{parsed.scheme}'", span, code)
        elif parsed.scheme and not parsed.netloc and parsed.scheme.lower() in {"http", "https"}:
            self._error("URL requires a host", span, code)

    def _validate_targets(self, nodes):
        for node in nodes:
            if isinstance(node, ElementDeclaration):
                props = {p.name: p for p in node.properties}
                if node.name == "button" and props.get("action") and props["action"].value == "toggle" and props.get("target"):
                    target = str(props["target"].value).lstrip("#")
                    if target not in self._ids:
                        self._error(f"Toggle target '{target}' does not resolve to a container id", props["target"].span, "SEMACT004")
                if node.children is not None:
                    self._validate_targets(node.children)

    def _validate_nodes(self, nodes, styles, parent_kind):
        for node in nodes:
            if isinstance(node, StyleDeclaration):
                if parent_kind is not None:
                    self._error("Style declarations must be at document scope", node.span, "SEMSTYLE005")
                continue
            if isinstance(node, HtmlEmbedding):
                if parent_kind not in CONTAINER_KINDS:
                    self._error("Trusted HTML embedding is only allowed inside section or container", node.span, "SEMHTML001")
                continue
            if not isinstance(node, ElementDeclaration):
                continue
            if node.name not in ELEMENT_KINDS:
                self._error(f"Unknown element kind '{node.name}'", node.span, "SEMELEM001")
                if node.children is not None:
                    self._validate_nodes(node.children, styles, parent_kind=node.name)
                continue
            props = {p.name: p for p in node.properties}
            required = {"title": ("text",), "paragraph": ("text",), "button": ("text",),
                        "link": ("text", "url"), "image": ("src",)}
            for key in required.get(node.name, ()):
                if key not in props:
                    self._error(f"Element '{node.name}' requires property '{key}'", node.span, "SEMELEM004")
            type_allowed = {"title": {"h1","h2","h3","h4","h5","h6"},
                           "paragraph": {"p","span","div"}, "section": {"section","div"},
                           "container": {"div","section"}}
            if "type" in props:
                value = str(props["type"].value).lower()
                if value not in type_allowed.get(node.name, set()):
                    self._error(f"Type override '{value}' is not allowed for '{node.name}'", props["type"].span, "SEMELEM005")
            if node.name in CONTAINER_KINDS and "id" in props:
                container_id = str(props["id"].value)
                if container_id in self._ids:
                    self._error(f"Duplicate container id '{container_id}'", props["id"].span, "SEMID001")
                else:
                    self._ids[container_id] = node
            if node.name == "button":
                action = props.get("action")
                target = props.get("target")
                if action and action.value != "toggle":
                    self._error(f"Unsupported button action '{action.value}'", action.span, "SEMACT001")
                if action and action.value == "toggle" and target is None:
                    self._error("Toggle action requires target", action.span, "SEMACT002")
                if target and not action:
                    self._error("Button target requires action='toggle'", target.span, "SEMACT003")
            if node.name == "link" and "url" in props:
                self._validate_url(props["url"].value, {"http","https","mailto"}, props["url"].span, "SEMURL001")
            if node.name == "image" and "src" in props:
                self._validate_url(props["src"].value, {"http","https"}, props["src"].span, "SEMURL002")
            if node.children is not None and node.name not in CONTAINER_KINDS:
                self._error(f"Element '{node.name}' cannot contain child declarations", node.span, "SEMELEM002")
            if node.children is None and node.name in CONTAINER_KINDS:
                self._error(f"Container '{node.name}' must use a block body", node.span, "SEMELEM003")
            if node.style_reference:
                style = styles.get(node.style_reference)
                if style is None:
                    self._error(f"Referenced style '{node.style_reference}' does not exist", node.span, "SEMSTYLE003")
                elif style.target_kind != node.name:
                    self._error(f"Style '{node.style_reference}' targets '{style.target_kind}', not '{node.name}'", node.span, "SEMSTYLE004")
            if node.children is not None:
                self._validate_nodes(node.children, styles, parent_kind=node.name)
