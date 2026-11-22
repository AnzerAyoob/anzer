"""Build the resolved, compiler-internal document tree from a validated AST."""

from dataclasses import dataclass, field
from posixpath import splitext
from typing import Literal
from urllib.parse import unquote, urlsplit

from .ast import Document, ElementDeclaration, HtmlEmbedding, SourceSpan
from .semantic import CONTAINER_KINDS, DEFAULT_TAGS, SemanticResult


@dataclass(frozen=True)
class NormalizedProperty:
    name: str
    value: str
    span: SourceSpan = field(compare=False)


@dataclass(frozen=True)
class NormalizedHtml:
    html: str
    span: SourceSpan = field(compare=False)


@dataclass(frozen=True)
class ToggleAction:
    target_id: str
    span: SourceSpan = field(compare=False)


@dataclass(frozen=True)
class NormalizedElement:
    kind: str
    tag: str
    shape: Literal["leaf", "container", "void"]
    properties: tuple[NormalizedProperty, ...]
    children: tuple["NormalizedElement | NormalizedHtml", ...]
    toggle: ToggleAction | None
    span: SourceSpan = field(compare=False)


@dataclass(frozen=True)
class NormalizedDocument:
    elements: tuple[NormalizedElement, ...]
    span: SourceSpan = field(compare=False)
    start_marker_span: SourceSpan = field(compare=False)
    end_marker_span: SourceSpan = field(compare=False)


def normalize_document(document: Document, semantic_result: SemanticResult) -> NormalizedDocument:
    """Resolve the validated AST into a tree with properties sorted by canonical name.

    Source positions remain available for traceability and are excluded from model
    equality. Child elements and trusted HTML retain their authored order. The
    browser and document-level CSS baseline stay implicit in this tree.
    """
    if semantic_result.document is not document:
        raise ValueError("Semantic result belongs to a different document")
    if semantic_result.diagnostics:
        raise ValueError("Cannot normalize a document with semantic errors")

    return NormalizedDocument(
        elements=tuple(
            _normalize_element(node, semantic_result)
            for node in document.declarations
            if isinstance(node, ElementDeclaration)
        ),
        span=document.span,
        start_marker_span=document.start_marker_span,
        end_marker_span=document.end_marker_span,
    )


def _normalize_element(node: ElementDeclaration, result: SemanticResult) -> NormalizedElement:
    properties = {}
    for assignment in result.properties_for(node).values():
        assert isinstance(assignment.value, str)
        properties[assignment.name] = NormalizedProperty(
            assignment.name, assignment.value, assignment.span
        )

    kind = node.name
    type_property = properties.get("type")
    tag = type_property.value if type_property is not None else DEFAULT_TAGS[kind]
    shape: Literal["leaf", "container", "void"] = "leaf"
    if kind in CONTAINER_KINDS:
        shape = "container"
    elif kind == "image":
        shape = "void"
        if "alt" not in properties:
            src = properties["src"]
            alt = _filename_alt(src.value)
            if alt:
                properties["alt"] = NormalizedProperty("alt", alt, src.span)
    elif kind == "button":
        properties["type"] = NormalizedProperty("type", "button", node.span)

    toggle = None
    if "action" in properties:
        target = properties["target"]
        toggle = ToggleAction(target.value, target.span)

    children: list[NormalizedElement | NormalizedHtml] = []
    for child in node.children or ():
        if isinstance(child, HtmlEmbedding):
            children.append(NormalizedHtml(child.html, child.span))
        else:
            assert isinstance(child, ElementDeclaration)
            children.append(_normalize_element(child, result))
    return NormalizedElement(
        kind=kind,
        tag=tag,
        shape=shape,
        properties=tuple(properties[name] for name in sorted(properties)),
        children=tuple(children),
        toggle=toggle,
        span=node.span,
    )


def _filename_alt(src: str) -> str:
    filename = unquote(urlsplit(src).path.rsplit("/", 1)[-1])
    stem, _ = splitext(filename)
    return " ".join(stem.replace("-", " ").replace("_", " ").split())
