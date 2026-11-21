"""Semantic validation for Anzer v0.1 documents. AST nodes remain immutable."""
import re
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
    'title': TEXT_PROPERTIES | BOX_PROPERTIES, 'paragraph': TEXT_PROPERTIES | BOX_PROPERTIES,
    'button': TEXT_PROPERTIES | BOX_PROPERTIES, 'link': TEXT_PROPERTIES | BOX_PROPERTIES,
    'image': IMAGE_STYLE_PROPERTIES, 'section': TEXT_PROPERTIES | BOX_PROPERTIES | LAYOUT_PROPERTIES,
    'container': TEXT_PROPERTIES | BOX_PROPERTIES | LAYOUT_PROPERTIES,
}
NON_STYLE_PROPERTIES = {'text','type','url','src','alt','action','target','id'}
KNOWN_PROPERTIES = set().union(*ELEMENT_STYLE_ALLOWLIST.values()) | NON_STYLE_PROPERTIES

COLOR_NAMES = set("""aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue blueviolet brown burlywood cadetblue chartreuse chocolate coral cornflowerblue cornsilk crimson cyan darkblue darkcyan darkgoldenrod darkgray darkgrey darkgreen darkkhaki darkmagenta darkolivegreen darkorange darkorchid darkred darksalmon darkseagreen darkslateblue darkslategray darkslategrey darkturquoise darkviolet deeppink deepskyblue dimgray dimgrey dodgerblue firebrick floralwhite forestgreen fuchsia gainsboro ghostwhite gold goldenrod gray grey green greenyellow honeydew hotpink indianred indigo ivory khaki lavender lavenderblush lawngreen lemonchiffon lightblue lightcoral lightcyan lightgoldenrodyellow lightgray lightgrey lightgreen lightpink lightsalmon lightseagreen lightskyblue lightslategray lightslategrey lightsteelblue lightyellow lime limegreen linen magenta maroon mediumaquamarine mediumblue mediumorchid mediumpurple mediumseagreen mediumslateblue mediumspringgreen mediumturquoise mediumvioletred midnightblue mintcream mistyrose moccasin navajowhite navy oldlace olive olivedrab orange orangered orchid palegoldenrod palegreen paleturquoise palevioletred papayawhip peachpuff peru pink plum powderblue purple rebeccapurple red rosybrown royalblue saddlebrown salmon sandybrown seagreen seashell sienna silver skyblue slateblue slategray slategrey snow springgreen steelblue tan teal thistle tomato turquoise violet wheat white whitesmoke yellow yellowgreen transparent currentcolor""".split())
UNIT_ALIASES = {'pixel':'px','pixels':'px','percent':'%','percentage':'%','viewport width':'vw','viewport height':'vh','viewport minimum':'vmin','viewport maximum':'vmax','centimetre':'cm','centimetres':'cm','centimeter':'cm','centimeters':'cm','millimetre':'mm','millimetres':'mm','millimeter':'mm','millimeters':'mm','inch':'in','inches':'in','point':'pt','points':'pt','pica':'pc','picas':'pc'}
LENGTH_RE = re.compile(r'^([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*([a-z%]*)$', re.I)
SUPPORTED_UNITS = {'px','%','em','rem','vw','vh','vmin','vmax','ch','ex','cm','mm','in','pt','pc'}
def _length(token, allow_negative=False, allow_auto=False, allow_none=False):
    t = token.strip().lower()
    if allow_auto and t == 'auto': return True
    if allow_none and t == 'none': return True
    m = LENGTH_RE.fullmatch(t)
    if not m: return False
    number, unit = m.groups()
    try: value = float(number)
    except ValueError: return False
    if not unit and value == 0: return True
    if not unit: unit = 'px'
    unit = UNIT_ALIASES.get(unit, unit)
    return unit in SUPPORTED_UNITS and (allow_negative or value >= 0)

def _color(value):
    v=value.strip().lower()
    return v in COLOR_NAMES or bool(re.fullmatch(r'#(?:[0-9a-f]{3}|[0-9a-f]{4}|[0-9a-f]{6}|[0-9a-f]{8})',v))

class SemanticValidator:
    def __init__(self):
        self.diagnostics = []
        self._ids = {}
    def _error(self, message, span, code):
        self.diagnostics.append(Diagnostic(DiagnosticCategory.SEMANTIC, message, span.start if span else None, code))
    def _props(self, node):
        return {p.name: p for p in node.properties}
    def _resolve_properties(self, style_properties, element_properties, span):
        """Merge style and element properties without mutating AST nodes.

        Border shorthand expands into longhands. Direct element declarations
        override style declarations; duplicates within a layer are diagnosed.
        """
        def layer(properties, label):
            result={}
            for prop in properties:
                if prop.name in result:
                    self._error(f"Duplicate property '{prop.name}' in {label}", prop.span, "SEMPROP006")
                result[prop.name]=prop
            expanded={}
            for name, prop in result.items():
                if name != "border":
                    expanded[name]=prop
                    continue
                parts=str(prop.value).strip().lower().split()
                for part in parts:
                    if part in {"thin","medium","thick"} or _length(part):
                        expanded["border-width"]=prop
                    elif part in {"none","hidden","dotted","dashed","solid","double","groove","ridge","inset","outset"}:
                        expanded["border-style"]=prop
                    elif _color(part):
                        expanded["border-color"]=prop
            return expanded
        merged=layer(style_properties, "style") if style_properties else {}
        merged.update(layer(element_properties, "element"))
        return merged
    def validate(self, document: Document):
        self.diagnostics=[]; self._ids={}; styles={}
        for declaration in document.declarations:
            if isinstance(declaration, StyleDeclaration):
                if declaration.target_kind not in ELEMENT_KINDS:
                    self._error(f"Unknown style target '{declaration.target_kind}'", declaration.span, "SEMSTYLE001")
                if declaration.name in styles:
                    self._error(f"Duplicate style declaration '{declaration.name}'", declaration.span, "SEMSTYLE002")
                else: styles[declaration.name]=declaration
        self._walk(document.declarations, styles, None)
        self._validate_targets(document.declarations)
        return self.diagnostics
    def _walk(self, nodes, styles, parent_kind):
        for node in nodes:
            if isinstance(node, StyleDeclaration):
                if parent_kind is not None: self._error("Style declarations must be at document scope", node.span, "SEMSTYLE005")
                self._validate_properties(node.target_kind, node.properties, node.span, check_layout=False); continue
            if isinstance(node, HtmlEmbedding):
                if parent_kind not in CONTAINER_KINDS: self._error("Trusted HTML embedding is only allowed inside section or container", node.span, "SEMHTML001")
                continue
            if not isinstance(node, ElementDeclaration): continue
            if node.name not in ELEMENT_KINDS:
                self._error(f"Unknown element kind '{node.name}'", node.span, "SEMELEM001")
                if node.children is not None: self._walk(node.children, styles, node.name)
                continue
            props=self._props(node)
            for key in REQUIRED.get(node.name, ()):
                if key not in props: self._error(f"Element '{node.name}' requires property '{key}'", node.span, "SEMELEM004")
            if "type" in props and str(props["type"].value).lower() not in TYPE_ALLOWED.get(node.name,set()):
                self._error(f"Type override '{props['type'].value}' is not allowed for '{node.name}'", props["type"].span, "SEMELEM005")
            if node.children is not None and node.name not in CONTAINER_KINDS: self._error(f"Element '{node.name}' cannot contain child declarations", node.span, "SEMELEM002")
            if node.children is None and node.name in CONTAINER_KINDS: self._error(f"Container '{node.name}' must use a block body", node.span, "SEMELEM003")
            if node.name in CONTAINER_KINDS and "id" in props:
                ident=str(props["id"].value)
                if ident in self._ids: self._error(f"Duplicate container id '{ident}'", props["id"].span, "SEMID001")
                else: self._ids[ident]=node
            self._validate_properties(node.name,node.properties,node.span,check_layout=False)
            style_properties=()
            if node.style_reference:
                style=styles.get(node.style_reference)
                if style is None: self._error(f"Referenced style '{node.style_reference}' does not exist",node.span,"SEMSTYLE003")
                elif style.target_kind != node.name: self._error(f"Style '{node.style_reference}' targets '{style.target_kind}', not '{node.name}'",node.span,"SEMSTYLE004")
                else: style_properties=style.properties
            effective=self._resolve_properties(style_properties,node.properties,node.span)
            self._validate_merged_layout(node.name,effective,node.span)
            if node.name=="button":
                action,target=props.get("action"),props.get("target")
                if action and action.value!="toggle": self._error(f"Unsupported button action '{action.value}'",action.span,"SEMACT001")
                if action and action.value=="toggle" and target is None: self._error("Toggle action requires target",action.span,"SEMACT002")
                if target and not action: self._error("Button target requires action='toggle'",target.span,"SEMACT003")
            if node.name=="link" and "url" in props: self._url(props["url"].value,{"http","https","mailto"},props["url"].span,"SEMURL001")
            if node.name=="image" and "src" in props: self._url(props["src"].value,{"http","https"},props["src"].span,"SEMURL002")
            if node.children is not None: self._walk(node.children,styles,node.name)
    def _validate_properties(self, kind, properties, span, check_layout=True):
        if kind not in ELEMENT_KINDS: return
        names={p.name for p in properties}
        for prop in properties:
            n,v=prop.name,prop.value
            if n not in KNOWN_PROPERTIES:
                self._error(f"Unknown property '{n}'",prop.span,'SEMPROP003'); continue
            if n in PROPERTY_KINDS and kind not in PROPERTY_KINDS[n]:
                self._error(f"Property '{n}' is not allowed on '{kind}'",prop.span,'SEMPROP001')
            if n in LAYOUT_PROPERTIES and kind not in CONTAINER_KINDS:
                self._error(f"Layout property '{n}' is only allowed on section/container",prop.span,'SEMLOUT001')
            elif n in STYLE_PROPERTIES and n not in ELEMENT_STYLE_ALLOWLIST[kind]:
                self._error(f"Style property '{n}' is not supported for '{kind}'",prop.span,'SEMPROP002')
            if n in NON_STYLE_PROPERTIES:
                expected_string=n not in {'id'}
                if expected_string and not isinstance(v,str): self._error(f"Property '{n}' requires a string value",prop.span,'SEMPROP004')
                if n=='id' and not isinstance(v,str): self._error("Property 'id' requires a string value",prop.span,'SEMPROP004')
                continue
            self._validate_value(n,v,prop.span)
        if check_layout:
            self._validate_merged_layout(kind,{p.name:p for p in properties},span)
    def _validate_merged_layout(self,kind,properties,span):
        names=set(properties)
        display=str(properties['display'].value).lower() if 'display' in properties else None
        flex={'flex-direction','flex-wrap','justify-content','align-items','align-content'}
        grid={'grid-template-columns','grid-template-rows','grid-auto-flow','grid-auto-columns','grid-auto-rows','justify-items'}
        gaps={'gap','row-gap','column-gap'}
        if names & flex and display not in {'flex','inline-flex'}: self._error('Flex properties require explicit flex display',span,'SEMLOUT002')
        if names & grid and display not in {'grid','inline-grid'}: self._error('Grid properties require explicit grid display',span,'SEMLOUT003')
        if names & gaps and display not in {'flex','inline-flex','grid','inline-grid'}: self._error('Gap requires explicit flex or grid display',span,'SEMLOUT004')
    def _validate_value(self,n,v,span):
        if isinstance(v,bool) or not isinstance(v,(str,int,float)):
            self._error(f"Property '{n}' has an unsupported value type",span,'SEMPROP004'); return
        s=str(v).strip().lower()
        if n in {'color','background-color','border-color'}:
            if not isinstance(v,str) or not _color(s): self._error(f"Invalid color value for '{n}'",span,'SEMPROP005')
        elif n in {'font-family'}:
            if not isinstance(v,str) or not v.strip(): self._error("font-family requires a non-empty string",span,'SEMPROP005')
        elif n in {'font-weight'}:
            if not isinstance(v,str) and not isinstance(v,int): self._error("Invalid font-weight",span,'SEMPROP005')
            elif s not in {'normal','bold'} and not (s.isdigit() and int(s) in range(100,1000,100)): self._error("Invalid font-weight",span,'SEMPROP005')
        elif n=='text-align' and s not in {'left','center','right','justify'}: self._error("Invalid text-align value",span,'SEMPROP005')
        elif n in {'width','height','font-size'}:
            if not _length(s,allow_auto=n in {'width','height'}): self._error(f"Invalid length for '{n}'",span,'SEMPROP005')
        elif n in {'min-width','min-height','max-width','max-height','border-radius'}:
            if not _length(s,allow_none=n in {'max-width','max-height'}): self._error(f"Invalid nonnegative length for '{n}'",span,'SEMPROP005')
        elif n in {'padding','margin'}:
            parts=s.split()
            if not 1<=len(parts)<=4 or any(not _length(x,allow_negative=n=='margin',allow_auto=n=='margin') for x in parts): self._error(f"Invalid spacing value for '{n}'",span,'SEMPROP005')
        elif n=='border-width':
            if s not in {'thin','medium','thick'} and not _length(s): self._error("Invalid border-width",span,'SEMPROP005')
        elif n=='border-style' and s not in {'none','hidden','dotted','dashed','solid','double','groove','ridge','inset','outset'}: self._error("Invalid border-style",span,'SEMPROP005')
        elif n=='border':
            tokens=s.split()
            widths={'thin','medium','thick'}
            styles={'none','hidden','dotted','dashed','solid','double','groove','ridge','inset','outset'}
            seen=set()
            valid=bool(tokens) and len(tokens)<=3
            for token in tokens:
                if token in widths or _length(token):
                    category='width'
                elif token in styles:
                    category='style'
                elif _color(token):
                    category='color'
                else:
                    valid=False; continue
                if category in seen: valid=False
                seen.add(category)
            if not valid: self._error("Invalid border shorthand or duplicate component",span,'SEMPROP005')
        elif n in LAYOUT_PROPERTIES: self._validate_layout_value(n,s,span)
    def _validate_layout_value(self,n,s,span):
        enums={
          'display':{'block','inline','inline-block','flex','inline-flex','grid','inline-grid','none'},
          'flex-direction':{'row','row-reverse','column','column-reverse'},
          'flex-wrap':{'nowrap','wrap','wrap-reverse'},
          'justify-content':{'start','end','center','space-between','space-around','space-evenly'},
          'align-items':{'start','end','center','stretch','baseline'},
          'align-content':{'start','end','center','stretch','space-between','space-around','space-evenly'},
          'grid-auto-flow':{'row','column','dense','row dense','column dense'},
          'justify-items':{'start','end','center','stretch'},
        }
        if n in enums and s not in enums[n]: self._error(f"Invalid value for '{n}'",span,'SEMLOUT005')
        elif n in {'gap','row-gap','column-gap'}:
            parts=s.split()
            if not 1<=len(parts)<=2 or any(not _length(x) for x in parts): self._error(f"Invalid gap value for '{n}'",span,'SEMLOUT005')
        elif n in {'grid-template-columns','grid-template-rows','grid-auto-columns','grid-auto-rows'}:
            parts=s.split()
            if not parts or any(not (x in {'auto','min-content','max-content'} or re.fullmatch(r'(?:\d+(?:\.\d*)?|\.\d+)fr',x) and float(x[:-2])>0 or _length(x)) for x in parts): self._error(f"Invalid grid track value for '{n}'",span,'SEMLOUT005')
    def _url(self,value,allowed,span,code):
        value=str(value).strip(); parsed=urlparse(value)
        if not value or value.startswith("//") or (parsed.scheme and parsed.scheme.lower() not in allowed): self._error(f"Invalid or unsupported URL '{value}'",span,code)
        elif parsed.scheme.lower() in {"http","https"} and not parsed.netloc: self._error("URL requires a host",span,code)
    def _validate_targets(self,nodes):
        for node in nodes:
            if isinstance(node,ElementDeclaration):
                props=self._props(node)
                if node.name=="button" and props.get("action") and props["action"].value=="toggle" and props.get("target"):
                    target=str(props["target"].value).lstrip("#")
                    if target not in self._ids: self._error(f"Toggle target '{target}' does not resolve to a container id",props["target"].span,"SEMACT004")
                if node.children is not None: self._validate_targets(node.children)
