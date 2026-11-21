"""Semantic validation for Anzer v0.1 documents. AST nodes remain immutable."""
from urllib.parse import urlparse
from .ast import Document, ElementDeclaration, StyleDeclaration, HtmlEmbedding
from .diagnostics import Diagnostic, DiagnosticCategory

ELEMENT_KINDS = {"title", "paragraph", "button", "link", "image", "section", "container"}
CONTAINER_KINDS = {"section", "container"}
REQUIRED = {"title": ("text",), "paragraph": ("text",), "button": ("text",),
            "link": ("text", "url"), "image": ("src",)}
TYPE_ALLOWED = {"title": {"h1","h2","h3","h4","h5","h6"},
                "paragraph": {"p","span","div"}, "section": {"section","div"},
                "container": {"div","section"}}



TEXT_PROPERTIES = {'color','background-color','font-family','font-size','font-weight','text-align'}
BOX_PROPERTIES = {'width','height','min-width','min-height','max-width','max-height','margin','padding','border','border-width','border-style','border-color','border-radius'}
STYLE_PROPERTIES = TEXT_PROPERTIES | BOX_PROPERTIES
IMAGE_STYLE_PROPERTIES = {'width','height','margin','border','border-width','border-style','border-color','border-radius'}
LAYOUT_PROPERTIES = {'display','flex-direction','flex-wrap','justify-content','align-items','align-content','grid-template-columns','grid-template-rows','grid-auto-flow','grid-auto-columns','grid-auto-rows','justify-items','gap','row-gap','column-gap'}
PROPERTY_KINDS = {'text':{'title','paragraph','button','link','section','container'},'type':{'title','paragraph','section','container'},'url':{'link'},'src':{'image'},'alt':{'image'},'action':{'button'},'target':{'button'},'id':{'section','container'}}
ELEMENT_STYLE_ALLOWLIST = {
    'title': TEXT_PROPERTIES | BOX_PROPERTIES,
    'paragraph': TEXT_PROPERTIES | BOX_PROPERTIES,
    'button': TEXT_PROPERTIES | BOX_PROPERTIES,
    'link': TEXT_PROPERTIES | BOX_PROPERTIES,
    'image': IMAGE_STYLE_PROPERTIES,
    'section': TEXT_PROPERTIES | BOX_PROPERTIES | LAYOUT_PROPERTIES,
    'container': TEXT_PROPERTIES | BOX_PROPERTIES | LAYOUT_PROPERTIES,
}
NON_STYLE_PROPERTIES = {'text','type','url','src','alt','action','target','id'}
KNOWN_PROPERTIES = set().union(*ELEMENT_STYLE_ALLOWLIST.values()) | NON_STYLE_PROPERTIES
class SemanticValidator:
    def __init__(self):
        self.diagnostics = []
        self._ids = {}

    def _error(self, message, span, code):
        self.diagnostics.append(Diagnostic(DiagnosticCategory.SEMANTIC, message,
            span.start if span else None, code))

    def _props(self, node):
        return {p.name: p for p in node.properties}

    def validate(self, document: Document):
        self.diagnostics = []
        self._ids = {}
        styles = {}
        for declaration in document.declarations:
            if isinstance(declaration, StyleDeclaration):
                if declaration.target_kind not in ELEMENT_KINDS:
                    self._error(f"Unknown style target '{declaration.target_kind}'", declaration.span, "SEMSTYLE001")
                if declaration.name in styles:
                    self._error(f"Duplicate style declaration '{declaration.name}'", declaration.span, "SEMSTYLE002")
                else:
                    styles[declaration.name] = declaration
        self._walk(document.declarations, styles, None)
        self._validate_targets(document.declarations)
        return self.diagnostics

    def _walk(self, nodes, styles, parent_kind):
        for node in nodes:
            if isinstance(node, StyleDeclaration):
                if parent_kind is not None:
                    self._error("Style declarations must be at document scope", node.span, "SEMSTYLE005")
                self._validate_properties(node.target_kind, node.properties, node.span)
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
                    self._walk(node.children, styles, node.name)
                continue
            props = self._props(node)
            for key in REQUIRED.get(node.name, ()):
                if key not in props:
                    self._error(f"Element '{node.name}' requires property '{key}'", node.span, "SEMELEM004")
            if "type" in props and str(props["type"].value).lower() not in TYPE_ALLOWED.get(node.name, set()):
                self._error(f"Type override '{props['type'].value}' is not allowed for '{node.name}'", props["type"].span, "SEMELEM005")
            if node.children is not None and node.name not in CONTAINER_KINDS:
                self._error(f"Element '{node.name}' cannot contain child declarations", node.span, "SEMELEM002")
            if node.children is None and node.name in CONTAINER_KINDS:
                self._error(f"Container '{node.name}' must use a block body", node.span, "SEMELEM003")
            if node.name in CONTAINER_KINDS and "id" in props:
                ident = str(props["id"].value)
                if ident in self._ids:
                    self._error(f"Duplicate container id '{ident}'", props["id"].span, "SEMID001")
                else:
                    self._ids[ident] = node
            self._validate_properties(node.name, node.properties, node.span)
            if node.style_reference:
                style = styles.get(node.style_reference)
                if style is None:
                    self._error(f"Referenced style '{node.style_reference}' does not exist", node.span, "SEMSTYLE003")
                elif style.target_kind != node.name:
                    self._error(f"Style '{node.style_reference}' targets '{style.target_kind}', not '{node.name}'", node.span, "SEMSTYLE004")
            if node.name == "button":
                action, target = props.get("action"), props.get("target")
                if action and action.value != "toggle":
                    self._error(f"Unsupported button action '{action.value}'", action.span, "SEMACT001")
                if action and action.value == "toggle" and target is None:
                    self._error("Toggle action requires target", action.span, "SEMACT002")
                if target and not action:
                    self._error("Button target requires action='toggle'", target.span, "SEMACT003")
            if node.name == "link" and "url" in props:
                self._url(props["url"].value, {"http","https","mailto"}, props["url"].span, "SEMURL001")
            if node.name == "image" and "src" in props:
                self._url(props["src"].value, {"http","https"}, props["src"].span, "SEMURL002")
            if node.children is not None:
                self._walk(node.children, styles, node.name)


    def _validate_properties(self, kind, properties, span):
        if kind not in ELEMENT_KINDS:
            return
        names = {p.name for p in properties}
        for prop in properties:
            if prop.name not in KNOWN_PROPERTIES:
                self._error("Unknown property '{}'".format(prop.name), prop.span, 'SEMPROP003')
                continue
            if prop.name in PROPERTY_KINDS and kind not in PROPERTY_KINDS[prop.name]:
                self._error("Property '{}' is not allowed on '{}'".format(prop.name, kind), prop.span, 'SEMPROP001')
            if prop.name in LAYOUT_PROPERTIES and kind not in CONTAINER_KINDS:
                self._error("Layout property '{}' is only allowed on section/container".format(prop.name), prop.span, 'SEMLOUT001')
            elif prop.name in STYLE_PROPERTIES and prop.name not in ELEMENT_STYLE_ALLOWLIST[kind]:
                self._error("Style property '{}' is not supported for '{}'".format(prop.name, kind), prop.span, 'SEMPROP002')
        display = next((str(p.value).lower() for p in properties if p.name == 'display'), None)
        flex = {'flex-direction','flex-wrap','justify-content','align-items','align-content'}
        grid = {'grid-template-columns','grid-template-rows','grid-auto-flow','grid-auto-columns','grid-auto-rows','justify-items'}
        gaps = {'gap','row-gap','column-gap'}
        if names & flex and display not in {'flex','inline-flex'}:
            self._error('Flex properties require explicit flex display', span, 'SEMLOUT002')
        if names & grid and display not in {'grid','inline-grid'}:
            self._error('Grid properties require explicit grid display', span, 'SEMLOUT003')
        if names & gaps and display not in {'flex','inline-flex','grid','inline-grid'}:
            self._error('Gap requires explicit flex or grid display', span, 'SEMLOUT004')
    def _url(self, value, allowed, span, code):
        value = str(value).strip()
        parsed = urlparse(value)
        if not value or value.startswith("//") or (parsed.scheme and parsed.scheme.lower() not in allowed):
            self._error(f"Invalid or unsupported URL '{value}'", span, code)
        elif parsed.scheme.lower() in {"http", "https"} and not parsed.netloc:
            self._error("URL requires a host", span, code)

    def _validate_targets(self, nodes):
        for node in nodes:
            if isinstance(node, ElementDeclaration):
                props = self._props(node)
                if node.name == "button" and props.get("action") and props["action"].value == "toggle" and props.get("target"):
                    target = str(props["target"].value).lstrip("#")
                    if target not in self._ids:
                        self._error(f"Toggle target '{target}' does not resolve to a container id", props["target"].span, "SEMACT004")
                if node.children is not None:
                    self._validate_targets(node.children)
