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

    def _validate_nodes(self, nodes, styles, parent_kind):
        for node in nodes:
            if isinstance(node, StyleDeclaration):
                continue
            if isinstance(node, HtmlEmbedding):
                if parent_kind not in CONTAINER_KINDS:
                    self._error("Trusted HTML embedding is only allowed inside section or container", node.span, "SEMHTML001")
                continue
            if not isinstance(node, ElementDeclaration):
                continue
            if node.name not in ELEMENT_KINDS:
                self._error(f"Unknown element kind '{node.name}'", node.span, "SEMELEM001")
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
