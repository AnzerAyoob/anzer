"""Semantic validation and validated property layers for Anzer v0.1 ASTs."""

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from decimal import Decimal
from ipaddress import IPv4Address, IPv6Address
from types import MappingProxyType
from urllib.parse import unquote, urlsplit

from .ast import Document, ElementDeclaration, HtmlEmbedding, PropertyAssignment, StyleDeclaration
from .diagnostics import Diagnostic, DiagnosticCategory
from .property_names import canonical_property_name

CONTAINER_KINDS = {"section", "container"}
ELEMENT_KINDS = CONTAINER_KINDS | {"title", "paragraph", "button", "link", "image"}
REQUIRED = {
    "title": ("text",),
    "paragraph": ("text",),
    "button": ("text",),
    "link": ("text", "url"),
    "image": ("src",),
}
DEFAULT_TAGS = {
    "title": "h1",
    "paragraph": "p",
    "button": "button",
    "link": "a",
    "image": "img",
    "section": "section",
    "container": "div",
}
TYPE_ALLOWED = {
    "title": {"h1", "h2", "h3", "h4", "h5", "h6"},
    "paragraph": {"p", "span", "div"},
    "section": {"section", "div"},
    "container": {"div", "section"},
}
COLOR_PROPERTIES = {"color", "background-color", "border-color"}
TEXT_STYLES = {"color", "background-color", "font-family", "font-size", "font-weight", "text-align"}
IMAGE_STYLES = {"width", "height", "margin", "border", "border-width", "border-style", "border-color", "border-radius"}
MIN_DIMENSIONS = {"min-width", "min-height"}
MAX_DIMENSIONS = {"max-width", "max-height"}
BOX_STYLES = IMAGE_STYLES | MIN_DIMENSIONS | MAX_DIMENSIONS | {"padding"}

FLEX_ONLY = {"flex-direction", "flex-wrap"}
GRID_TRACKS = {"grid-template-columns", "grid-template-rows", "grid-auto-columns", "grid-auto-rows"}
GRID_ONLY = GRID_TRACKS | {"grid-auto-flow", "justify-items"}
ALIGNMENT = {"justify-content", "align-items", "align-content"}
GAPS = {"gap", "row-gap", "column-gap"}
LAYOUT_PROPERTIES = {"display"} | FLEX_ONLY | GRID_ONLY | ALIGNMENT | GAPS
FLEX_DISPLAYS = {"flex", "inline-flex"}
GRID_DISPLAYS = {"grid", "inline-grid"}
LAYOUT_DISPLAYS = FLEX_DISPLAYS | GRID_DISPLAYS

PROPERTY_KINDS = {
    "text": ELEMENT_KINDS - {"image"},
    "type": TYPE_ALLOWED.keys(),
    "url": {"link"},
    "src": {"image"},
    "alt": {"image"},
    "action": {"button"},
    "target": {"button"},
    "id": CONTAINER_KINDS,
}
KNOWN_PROPERTIES = TEXT_STYLES | BOX_STYLES | LAYOUT_PROPERTIES | PROPERTY_KINDS.keys()

BORDER_WIDTHS = {"thin", "medium", "thick"}
BORDER_STYLES = {"none", "hidden", "dotted", "dashed", "solid", "double", "groove", "ridge", "inset", "outset"}
BORDER_DEFAULTS = {"border-width": "medium", "border-style": "none", "border-color": "currentcolor"}
FONT_WEIGHTS = {"normal", "bold", "100", "200", "300", "400", "500", "600", "700", "800", "900"}

ENUMS = {
    "border-style": BORDER_STYLES,
    "text-align": {"left", "center", "right", "justify"},
    "display": LAYOUT_DISPLAYS | {"block", "inline", "inline-block", "none"},
    "flex-direction": {"row", "row-reverse", "column", "column-reverse"},
    "flex-wrap": {"nowrap", "wrap", "wrap-reverse"},
    "justify-content": {"start", "end", "center", "space-between", "space-around", "space-evenly"},
    "align-items": {"start", "end", "center", "stretch", "baseline"},
    "align-content": {"start", "end", "center", "stretch", "space-between", "space-around", "space-evenly"},
    "grid-auto-flow": {"row", "column", "dense", "row dense", "column dense"},
    "justify-items": {"start", "end", "center", "stretch"},
}

COLOR_NAMES = set("""aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue blueviolet brown burlywood cadetblue chartreuse chocolate coral cornflowerblue cornsilk crimson cyan darkblue darkcyan darkgoldenrod darkgray darkgrey darkgreen darkkhaki darkmagenta darkolivegreen darkorange darkorchid darkred darksalmon darkseagreen darkslateblue darkslategray darkslategrey darkturquoise darkviolet deeppink deepskyblue dimgray dimgrey dodgerblue firebrick floralwhite forestgreen fuchsia gainsboro ghostwhite gold goldenrod gray grey green greenyellow honeydew hotpink indianred indigo ivory khaki lavender lavenderblush lawngreen lemonchiffon lightblue lightcoral lightcyan lightgoldenrodyellow lightgray lightgrey lightgreen lightpink lightsalmon lightseagreen lightskyblue lightslategray lightslategrey lightsteelblue lightyellow lime limegreen linen magenta maroon mediumaquamarine mediumblue mediumorchid mediumpurple mediumseagreen mediumslateblue mediumspringgreen mediumturquoise mediumvioletred midnightblue mintcream mistyrose moccasin navajowhite navy oldlace olive olivedrab orange orangered orchid palegoldenrod palegreen paleturquoise palevioletred papayawhip peachpuff peru pink plum powderblue purple rebeccapurple red rosybrown royalblue saddlebrown salmon sandybrown seagreen seashell sienna silver skyblue slateblue slategray slategrey snow springgreen steelblue tan teal thistle tomato turquoise violet wheat white whitesmoke yellow yellowgreen transparent currentcolor""".split())
UNIT_ALIASES = {
    "pixel": "px", "pixels": "px", "percent": "%", "percentage": "%",
    "viewport width": "vw", "viewport height": "vh", "viewport minimum": "vmin", "viewport maximum": "vmax",
    "centimetre": "cm", "centimetres": "cm", "centimeter": "cm", "centimeters": "cm",
    "millimetre": "mm", "millimetres": "mm", "millimeter": "mm", "millimeters": "mm",
    "inch": "in", "inches": "in", "point": "pt", "points": "pt", "pica": "pc", "picas": "pc",
}
SUPPORTED_UNITS = {"px", "%", "em", "rem", "vw", "vh", "vmin", "vmax", "ch", "ex", "cm", "mm", "in", "pt", "pc"}
NUMBER = r"(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)"
LENGTH_RE = re.compile(rf"(-?{NUMBER}) *(%|[a-z]+(?: [a-z]+)?)?")
FR_RE = re.compile(rf"({NUMBER})fr")
COLOR_HEX = re.compile(r"#(?:[0-9a-f]{3}|[0-9a-f]{4}|[0-9a-f]{6}|[0-9a-f]{8})")
HOST_LABEL = re.compile(r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?")
URL_CONTROL = re.compile(r"[\s\x00-\x1f\x7f-\x9f\\]")
BAD_PERCENT_ESCAPE = re.compile(r"%(?![0-9a-fA-F]{2})")
FONT_SYNTAX = re.compile(r"""[;{}!()\\\x00-\x1f\x7f]""")


def _decimal_spelling(number):
    """Canonicalize a validated decimal without rounding or exponent notation."""
    whole, _, fraction = number.lstrip("-").partition(".")
    whole = whole.lstrip("0") or "0"
    fraction = fraction.rstrip("0")
    if whole == "0" and not fraction:
        return "0"
    sign = "-" if number.startswith("-") else ""
    return sign + whole + ("." + fraction if fraction else "")


def _length(value, *, negative=False, percent=True, keywords=()):
    if value in keywords:
        return value
    match = LENGTH_RE.fullmatch(value)
    if match is None:
        return None
    number, unit = match.groups()
    number = _decimal_spelling(number)
    if number.startswith("-") and not negative:
        return None
    if unit is None:
        return "0" if number == "0" else number + "px"
    unit = UNIT_ALIASES.get(unit, unit)
    if unit in SUPPORTED_UNITS and (percent or unit != "%"):
        return number + unit
    return None


def _length_at(words, index, **rules):
    # A length can occupy a number and up to two words of a named unit.
    for end in range(min(index + 3, len(words)), index, -1):
        value = _length(" ".join(words[index:end]), **rules)
        if value is not None:
            return value, end
    return None, index


def _spacing(value, maximum, **rules):
    words = value.split()
    lengths = []
    index = 0
    while index < len(words) and len(lengths) < maximum:
        length, index = _length_at(words, index, **rules)
        if length is None:
            return None
        lengths.append(length)
    return " ".join(lengths) if lengths and index == len(words) else None


def _is_color(value):
    return value in COLOR_NAMES or COLOR_HEX.fullmatch(value) is not None


def _border(value):
    words = value.split()
    components = {}
    index = 0
    while index < len(words):
        word = words[index]
        if word in BORDER_STYLES:
            name, component, index = "border-style", word, index + 1
        elif _is_color(word):
            name, component, index = "border-color", word, index + 1
        else:
            name = "border-width"
            component, index = _length_at(words, index, percent=False, keywords=BORDER_WIDTHS)
        if component is None or name in components:
            return None
        components[name] = component
    return BORDER_DEFAULTS | components if components else None


def _grid_tracks(value):
    words = value.split()
    tracks = []
    index = 0
    while index < len(words):
        word = words[index]
        fraction = FR_RE.fullmatch(word)
        if word in {"auto", "min-content", "max-content"}:
            track, index = word, index + 1
        elif fraction:
            number = _decimal_spelling(fraction[1])
            if number == "0":
                return None
            track, index = number + "fr", index + 1
        else:
            track, index = _length_at(words, index)
            if track is None:
                return None
        tracks.append(track)
    return " ".join(tracks) if tracks else None


def _style_value(name, value):
    if type(value) is float:
        if not math.isfinite(value):
            return None
        text = format(Decimal(str(value)), "f")
    elif type(value) in {str, int}:
        text = " ".join(str(value).lower().split())
    else:
        return None

    if name in COLOR_PROPERTIES:
        return text if _is_color(text) else None
    if name == "font-family":
        if isinstance(value, str) and not FONT_SYNTAX.search(value):
            families = [family.strip() for family in value.split(",")]
            if all(families):
                return ", ".join(families)
        return None
    if name == "font-weight":
        if type(value) not in {str, int}:
            return None
        weight = _decimal_spelling(text) if re.fullmatch(r"[0-9]+", text) else text
        return weight if weight in FONT_WEIGHTS else None
    if name in ENUMS:
        return text if text in ENUMS[name] else None
    if name in {"width", "height"}:
        return _length(text, keywords={"auto"})
    if name in MAX_DIMENSIONS:
        return _length(text, keywords={"none"})
    if name in MIN_DIMENSIONS | {"font-size", "border-radius"}:
        return _length(text)
    if name == "margin":
        return _spacing(text, 4, negative=True, keywords={"auto"})
    if name == "padding":
        return _spacing(text, 4)
    if name == "border-width":
        return _length(text, percent=False, keywords=BORDER_WIDTHS)
    if name == "border":
        return _border(text)
    if name in GAPS:
        return _spacing(text, 2 if name == "gap" else 1)
    if name in GRID_TRACKS:
        return _grid_tracks(text)
    raise AssertionError(f"Missing validation for {name}")


def _http_host(authority, hostname):
    # urlsplit exposes the hostname and port, but can ignore text after a bracket.
    host_port = authority.rsplit("@", 1)[-1]
    if authority.count("@") > 1:
        return False
    if host_port.startswith("["):
        if not re.fullmatch(r"\[[0-9a-fA-F:.]+\](?::[0-9]+)?", host_port):
            return False
        IPv6Address(hostname)
        return True
    if not re.fullmatch(r"[^:\[\]]+(?::[0-9]+)?", host_port):
        return False
    host = unquote(hostname, errors="strict").encode("idna").decode("ascii").removesuffix(".")
    if re.fullmatch(r"[0-9]+(?:\.[0-9]+){3}", host):
        IPv4Address(host)
        return True
    return len(host) <= 253 and all(HOST_LABEL.fullmatch(label) for label in host.split("."))


def _valid_url(value, *, mailto):
    if not value or value.startswith("//") or URL_CONTROL.search(value) or BAD_PERCENT_ESCAPE.search(value):
        return False
    try:
        url = urlsplit(value)
        if url.scheme in {"http", "https"}:
            if not url.hostname or not _http_host(url.netloc, url.hostname):
                return False
            return url.port is None or 0 <= url.port <= 65535
        if url.scheme == "mailto" and mailto:
            if url.netloc or value.partition(":")[2].startswith("/") or "#" in value:
                return False
            for address in url.path.split(",") if url.path else ():
                local, _, domain = address.rpartition("@")
                if not local or not domain or "@" in local:
                    return False
            return True
        return not url.scheme and not url.netloc and ":" not in url.path.split("/", 1)[0]
    except (ValueError, UnicodeError):
        return False


def _identifier_error(value: str) -> str | None:
    if not value.strip():
        return "must not be empty"
    if "\0" in value:
        return "must not contain U+0000"
    return None


def _resolve_gap_layer(
    layer: Mapping[str, PropertyAssignment],
) -> Mapping[str, PropertyAssignment]:
    gap = layer.get("gap")
    if gap is None:
        return layer

    # Validation has already reduced each length to a single canonical token.
    assert isinstance(gap.value, str)
    row, _, column = gap.value.partition(" ")
    resolved = dict(layer)
    del resolved["gap"]
    resolved.setdefault("row-gap", replace(gap, name="row-gap", value=row))
    resolved.setdefault("column-gap", replace(gap, name="column-gap", value=column or row))
    return resolved


@dataclass(frozen=True)
class _PropertyLayers:
    style: Mapping[str, PropertyAssignment]
    direct: Mapping[str, PropertyAssignment]

    def merge(self) -> dict[str, PropertyAssignment]:
        return {**self.style, **self.direct}

    def resolve(self, node: ElementDeclaration) -> dict[str, PropertyAssignment]:
        """Resolve validated layers into effective assignments with tag defaults."""
        properties = {**_resolve_gap_layer(self.style), **_resolve_gap_layer(self.direct)}
        if node.name in TYPE_ALLOWED and "type" not in properties:
            properties["type"] = PropertyAssignment("type", DEFAULT_TAGS[node.name], node.span)
        display = properties.get("display")
        if display is not None and display.value in FLEX_DISPLAYS:
            for name in ALIGNMENT.intersection(properties):
                prop = properties[name]
                if prop.value in {"start", "end"}:
                    properties[name] = replace(prop, value="flex-" + prop.value)
        return properties


@dataclass(frozen=True)
class SemanticResult:
    """Snapshot of semantic analysis for one immutable AST."""

    document: Document
    diagnostics: tuple[Diagnostic, ...]
    _layers: Mapping[int, _PropertyLayers] = field(repr=False, compare=False)

    def properties_for(self, node: ElementDeclaration) -> dict[str, PropertyAssignment]:
        """Resolve canonical assignments from validated layers, keeping their spans."""
        return self._layers[id(node)].resolve(node)


class SemanticValidator:
    def __init__(self):
        self.diagnostics = []
        self._result: SemanticResult | None = None

    def properties_for(self, node: ElementDeclaration) -> dict[str, PropertyAssignment]:
        """Return the legacy ordered property view of the most recent validation."""
        if self._result is None:
            raise KeyError(id(node))
        return dict(sorted(self._result.properties_for(node).items()))

    def _error(self, message, span, code, category=DiagnosticCategory.SEMANTIC):
        self.diagnostics.append(Diagnostic(category, message, span.start, code))

    def _invalid(self, message, span, code):
        self._error(message, span, code, DiagnosticCategory.VALIDATION)

    def validate(self, document: Document) -> list[Diagnostic]:
        """Validate a document and return the Phase 6 diagnostics list."""
        self.analyze(document)
        return self.diagnostics

    def analyze(self, document: Document) -> SemanticResult:
        """Validate an AST whose lexer and parser completed without errors."""
        self.diagnostics = []
        self._property_layers: dict[int, _PropertyLayers] = {}
        self._ids = {}
        self._invalid_target_ids = set()
        self._duplicate_ids = set()
        self._targets = []
        styles = {}
        for node in document.declarations:
            if not isinstance(node, StyleDeclaration):
                continue
            if node.name in styles:
                self._error(f"Duplicate style declaration '{node.name}'", node.span, "SEMSTYLE002")
            properties = self._validate_style(node)
            styles.setdefault(node.name, (node.target_kind, properties))

        self._walk(document.declarations, styles)
        for target in self._targets:
            if target.value in self._duplicate_ids or target.value in self._ids:
                continue
            if target.value in self._invalid_target_ids:
                message = f"Toggle target '{target.value}' must identify a section or container block"
            else:
                message = f"Toggle target '{target.value}' does not resolve to a container id"
            self._error(message, target.span, "SEMACT004")

        self.diagnostics.sort(key=lambda diagnostic: diagnostic.location.offset)
        if self.diagnostics:
            self._property_layers.clear()
        self._result = SemanticResult(
            document, tuple(self.diagnostics), MappingProxyType(self._property_layers)
        )
        return self._result

    def _validate_style(self, style):
        if style.target_kind not in ELEMENT_KINDS:
            self._error(f"Unknown style target '{style.target_kind}'", style.span, "SEMSTYLE001")
            return {}
        return self._prepare_layer(style.target_kind, style.properties, "style")

    def _walk(self, nodes, styles, parent_kind=None):
        for node in nodes:
            if isinstance(node, StyleDeclaration):
                if parent_kind is not None:
                    self._error("Style declarations must be at document scope", node.span, "SEMSTYLE005")
                    self._validate_style(node)
            elif isinstance(node, HtmlEmbedding):
                if parent_kind not in CONTAINER_KINDS:
                    self._error("Trusted HTML embedding is only allowed inside section or container", node.span, "SEMHTML001")
            elif isinstance(node, ElementDeclaration):
                if node.name not in ELEMENT_KINDS:
                    self._error(f"Unknown element kind '{node.name}'", node.span, "SEMELEM001")
                else:
                    self._validate_element(node, styles)
                if node.children is not None:
                    self._walk(node.children, styles, node.name)

    def _validate_element(self, node, styles):
        kind = node.name
        is_container = kind in CONTAINER_KINDS
        if node.children is not None and not is_container:
            self._error(f"Element '{kind}' cannot contain child declarations", node.span, "SEMELEM002")
        if node.children is None and is_container:
            self._error(f"Container '{kind}' must use a block body", node.span, "SEMELEM003")

        style = {}
        reference_valid = True
        if node.style_reference is not None:
            declaration = styles.get(node.style_reference)
            if declaration is None:
                self._error(f"Referenced style '{node.style_reference}' does not exist", node.span, "SEMSTYLE003")
                reference_valid = False
            elif declaration[0] != kind:
                self._error(f"Style '{node.style_reference}' targets '{declaration[0]}', not '{kind}'", node.span, "SEMSTYLE004")
                reference_valid = False
            else:
                style = declaration[1]

        direct = self._prepare_layer(kind, node.properties, "element")
        layers = _PropertyLayers(MappingProxyType(style), MappingProxyType(direct))
        effective = layers.merge()
        if reference_valid:
            for name in REQUIRED.get(kind, ()):
                if name not in effective:
                    self._error(f"Element '{kind}' requires property '{name}'", node.span, "SEMELEM004")
        self._property_layers[id(node)] = layers

        id_assignment = effective.get("id")
        id_span = node.span if "id" in style and "id" not in direct else None
        self._collect_id(id_assignment, is_container and node.children is not None, id_span)
        if is_container:
            self._validate_layout(effective, allow_missing_display=not reference_valid)
        if kind == "button":
            self._validate_toggle(effective, reference_valid)

    def _prepare_layer(self, kind, properties, label):
        explicit = {}
        shorthand = {}
        seen = set()
        for prop in properties:
            name = canonical_property_name(prop.name)
            if name in seen:
                self._invalid(f"Duplicate property '{name}' in {label}", prop.span, "SEMPROP006")
                continue
            seen.add(name)
            if name not in KNOWN_PROPERTIES:
                self._invalid(f"Unknown property '{name}'", prop.span, "SEMPROP003")
                continue
            if name in PROPERTY_KINDS:
                self._validate_element_value(kind, name, prop)
                value = prop.value
                if name == "type" and isinstance(value, str):
                    value = value.lower()
                explicit[name] = replace(prop, name=name, value=value)
            elif name in LAYOUT_PROPERTIES and kind not in CONTAINER_KINDS:
                self._invalid(f"Layout property '{name}' is only allowed on section/container", prop.span, "SEMLOUT001")
            elif kind == "image" and name not in IMAGE_STYLES:
                self._invalid(f"Style property '{name}' is not supported for '{kind}'", prop.span, "SEMPROP002")
            else:
                value = _style_value(name, prop.value)
                if value is None:
                    if name == "border":
                        message = "Invalid border shorthand or duplicate component"
                    else:
                        message = f"Invalid value for '{name}'"
                    code = "SEMLOUT005" if name in LAYOUT_PROPERTIES else "SEMPROP005"
                    if type(prop.value) not in {str, int, float}:
                        message = f"Property '{name}' has an unsupported value type"
                        code = "SEMPROP004"
                    self._invalid(message, prop.span, code)
                    # Preserve an invalid display override so its layout does not fall back to the style.
                    if name == "display":
                        explicit[name] = replace(prop, name=name, value="")
                elif name == "border":
                    shorthand = {
                        part: PropertyAssignment(part, component, prop.span)
                        for part, component in value.items()
                    }
                else:
                    explicit[name] = replace(prop, name=name, value=value)
        return shorthand | explicit

    def _validate_element_value(self, kind, name, prop):
        value = prop.value
        if name == "type" and isinstance(value, str) and value.lower() not in TYPE_ALLOWED.get(kind, ()):
            self._error(f"Type override '{value}' is not allowed for '{kind}'", prop.span, "SEMELEM005")
        elif kind not in PROPERTY_KINDS[name]:
            self._invalid(f"Property '{name}' is not allowed on '{kind}'", prop.span, "SEMPROP001")
        elif not isinstance(value, str):
            self._invalid(f"Property '{name}' requires a string value", prop.span, "SEMPROP004")
        elif name in {"id", "target"}:
            reason = _identifier_error(value)
            if reason is not None:
                label, code = ("Container id", "SEMID002") if name == "id" else ("Toggle target", "SEMACT002")
                self._error(f"{label} {reason}", prop.span, code)
        elif name == "action" and value != "toggle":
            self._error(f"Unsupported button action '{value}'", prop.span, "SEMACT001")
        elif name in {"url", "src"} and not _valid_url(value, mailto=name == "url"):
            code = "SEMURL001" if name == "url" else "SEMURL002"
            self._invalid(f"Invalid or unsupported URL for '{name}'", prop.span, code)

    def _validate_layout(self, properties, *, allow_missing_display):
        display = properties.get("display")
        mode = display.value if display is not None else None
        if mode == "" or (mode is None and allow_missing_display):
            return
        groups = (
            (FLEX_ONLY, FLEX_DISPLAYS, "Flex properties require explicit flex display", "SEMLOUT002"),
            (GRID_ONLY, GRID_DISPLAYS, "Grid properties require explicit grid display", "SEMLOUT003"),
            (GAPS, LAYOUT_DISPLAYS, "Gap requires explicit flex or grid display", "SEMLOUT004"),
            (ALIGNMENT, LAYOUT_DISPLAYS, "Alignment requires explicit flex or grid display", "SEMLOUT006"),
        )
        for names, allowed, message, code in groups:
            if mode not in allowed:
                first = min(
                    (prop for name, prop in properties.items() if name in names),
                    key=lambda prop: prop.span.start_offset,
                    default=None,
                )
                if first is not None:
                    self._invalid(message, first.span, code)

    def _collect_id(self, prop, eligible, reference_span):
        if prop is None or not isinstance(prop.value, str) or _identifier_error(prop.value):
            return
        if not eligible:
            self._invalid_target_ids.add(prop.value)
        elif prop.value in self._ids:
            self._duplicate_ids.add(prop.value)
            self._error(f"Duplicate container id '{prop.value}'", reference_span or prop.span, "SEMID001")
        else:
            self._ids[prop.value] = prop

    def _validate_toggle(self, properties, reference_valid):
        action, target = properties.get("action"), properties.get("target")
        if target is not None and (not isinstance(target.value, str) or _identifier_error(target.value)):
            return
        if action is None:
            if target is not None and reference_valid:
                self._error("Button target requires action='toggle'", target.span, "SEMACT003")
        elif action.value == "toggle":
            if target is None:
                if reference_valid:
                    self._error("Toggle action requires target", action.span, "SEMACT002")
            else:
                self._targets.append(target)
