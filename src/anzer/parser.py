"""Declaration parser for Anzer v0.1 (element declarations)."""
from .ast import Document, SourceSpan, PropertyAssignment, ElementDeclaration
from .diagnostics import Diagnostic, DiagnosticCategory
from .source import Source
from .tokens import TokenKind

_MARKER_LENGTHS = {"start": len("<anzer start>"), "end": len("<anzer end>")}


class Parser:
    def __init__(self, source: Source, tokens):
        self.source, self.tokens, self.index = source, tokens, 0
        self.diagnostics = []

    def _current(self):
        return self.tokens[min(self.index, len(self.tokens)-1)]

    def _advance(self):
        t=self._current()
        if t.kind != TokenKind.EOF: self.index += 1
        return t

    def _error(self, message, token=None, code="PAR001"):
        t=token or self._current()
        self.diagnostics.append(Diagnostic(DiagnosticCategory.SYNTAX,message,t.location,code))

    def _span(self, a, b):
        return SourceSpan(self.source.location(a), self.source.location(b))

    def _token_end_offset(self, token):
        """Return the source offset immediately after a token, using its lexeme."""
        start = token.location.offset
        if token.kind == TokenKind.STRING:
            i = start + 1
            while i < len(self.source.text):
                ch = self.source.text[i]
                if ch == "\\":
                    i += 2
                    continue
                if ch == '"' :
                    return i + 1
                i += 1
            return len(self.source.text)
        return start + len(token.value)

    def _canonical_property_name(self, raw_name):
        normalized = "-".join(part for part in raw_name.replace("-", " ").split() if part)
        aliases = {
            "font": "font-family",
            "text-size": "font-size",
            "minimum-width": "min-width",
            "maximum-width": "max-width",
            "minimum-height": "min-height",
            "maximum-height": "max-height",
        }
        return aliases.get(normalized, normalized)

    def parse_document(self):
        markers=[t for t in self.tokens if t.kind==TokenKind.MARKER]
        starts=[t for t in markers if t.value=="start"]
        ends=[t for t in markers if t.value=="end"]
        start=starts[0] if starts else None
        end=ends[0] if ends else None
        if len(markers)!=2: self._error("Document must contain exactly one start and one end marker",markers[0] if markers else self._current(),"PARDOC001")
        if not start: self._error("Missing <anzer start> marker",markers[0] if markers else self._current(),"PARDOC002")
        if not end: self._error("Missing <anzer end> marker",markers[-1] if markers else self._current(),"PARDOC003")
        if start and end and start.location.offset>=end.location.offset: self._error("<anzer start> must precede <anzer end>",end,"PARDOC004")
        if not start or not end or start.location.offset>=end.location.offset:
            eof=self._current().location.offset
            doc=self._span(0,eof)
            return Document(doc,doc,(),doc),self.diagnostics
        start_end=start.location.offset+_MARKER_LENGTHS["start"]
        end_end=end.location.offset+_MARKER_LENGTHS["end"]
        declarations=[]
        self.index=0
        while self._current().kind!=TokenKind.EOF and self._current().location.offset<end.location.offset:
            t=self._current()
            if t.kind==TokenKind.MARKER:
                self._advance(); continue
            if t.location.offset<start_end:
                self._error("Unexpected token before document start",t,"PARDOC005"); self._advance(); continue
            node=self._parse_declaration()
            if node is not None: declarations.append(node)
        start_span=self._span(start.location.offset,start_end)
        end_span=self._span(end.location.offset,end_end)
        doc_span=self._span(start.location.offset,end_end)
        return Document(start_span,end_span,tuple(declarations),doc_span),self.diagnostics

    def _parse_declaration(self):
        begin=self._current()
        if begin.kind!=TokenKind.IDENTIFIER or begin.value!="anzer":
            self._error("Expected 'anzer make' declaration",begin,"PARDECL001")
            self._recover_statement(); return None
        self._advance()
        if self._current().kind!=TokenKind.IDENTIFIER or self._current().value!="make":
            self._error("Expected 'make' after 'anzer'",self._current(),"PARDECL002")
            self._recover_statement(); return None
        self._advance()
        if self._current().kind!=TokenKind.IDENTIFIER:
            self._error("Expected element name",self._current(),"PARDECL003")
            self._recover_statement(); return None
        name=self._advance().value
        # Style declarations use the element-kind-scoped form:
        # "anzer make paragraph style 1: ...;"
        if self._current().kind==TokenKind.IDENTIFIER and self._current().value=="style":
            self._advance()
            style_number=self._current()
            if style_number.kind!=TokenKind.NUMBER or "." in style_number.value:
                self._error("Expected integer style identifier",style_number,"PARSTYLE001")
                self._recover_statement()
                return None
            self._advance()
            if self._current().value!=":":
                self._error("Expected ':' after style identifier",self._current(),"PARSTYLE002")
                self._recover_statement()
                return None
            self._advance()
            props,style_reference=self._parse_properties()
            if style_reference is not None:
                self._error("Style declarations cannot reference another style",style_number,"PARSTYLE004")
            if self._current().value!=";":
                self._error("Expected ';' after style declaration",self._current(),"PARSTYLE003")
                self._recover_statement()
                return None
            close=self._advance()
            from .ast import StyleDeclaration
            style_name=f"{name} style {style_number.value}"
            return StyleDeclaration(style_name,name,tuple(props),self._span(begin.location.offset,close.location.offset+1))
        props=[]
        style_reference=None
        if self._current().value==":":
            self._advance()
            props,style_reference=self._parse_properties()
        if self._current().value=="{":
            open_tok=self._advance()
            children=[]
            while self._current().kind!=TokenKind.EOF and self._current().value!="}":
                if self._current().kind==TokenKind.MARKER:
                    self._error("Unexpected marker inside container",self._current(),"PARDECL004"); self._advance(); continue
                child=self._parse_declaration()
                if child: children.append(child)
            if self._current().value=="}":
                close=self._advance()
                return ElementDeclaration(name,tuple(props),style_reference,self._span(begin.location.offset,close.location.offset+1))
            self._error("Unclosed container",open_tok,"PARDECL005")
            return ElementDeclaration(name,tuple(props),tuple(children),None,self._span(begin.location.offset,self._current().location.offset))
        if self._current().value==";":
            close=self._advance()
            return ElementDeclaration(name,tuple(props),style_reference,self._span(begin.location.offset,close.location.offset+1))
        self._error("Expected ';' or '{' after declaration",self._current(),"PARDECL006")
        self._recover_statement()
        return None

    def _parse_properties(self):
        props=[]
        style_reference=None
        seen_names=set()
        while self._current().kind!=TokenKind.EOF and self._current().value not in (";","{","}"):
            name_start=self._current()
            if name_start.kind!=TokenKind.IDENTIFIER:
                self._error("Expected property name",name_start,"PARPROP001")
                self._advance()
                continue

            name_tokens=[self._advance()]
            # Friendly multi-word property names are recognized by collecting
            # identifier tokens up to the equals sign. Whitespace is lexical
            # formatting, so both "minimum width" and "minimum-width" work.
            while self._current().kind==TokenKind.IDENTIFIER and self._current().value!="=":
                name_tokens.append(self._advance())
            raw_name=" ".join(token.value for token in name_tokens)
            name=self._canonical_property_name(raw_name)
            is_style_reference=(raw_name=="use style")
            if self._current().value!="=":
                self._error("Expected '=' after property name",self._current(),"PARPROP002")
                self._recover_property()
                continue
            self._advance()
            value_tok=self._current()
            if value_tok.kind not in (TokenKind.STRING,TokenKind.NUMBER,TokenKind.BOOLEAN):
                self._error("Expected scalar property value",value_tok,"PARPROP003")
                self._recover_property()
                continue
            self._advance()
            value=value_tok.value
            if value_tok.kind==TokenKind.BOOLEAN:
                value=value=="true"
            elif value_tok.kind==TokenKind.NUMBER:
                try:
                    value=int(value) if "." not in value else float(value)
                except ValueError:
                    pass
            if is_style_reference:
                if value_tok.kind!=TokenKind.STRING:
                    self._error("Style reference must be a string",value_tok,"PARSTYLE005")
                elif style_reference is not None:
                    self._error("Duplicate style reference",name_start,"PARSTYLE006")
                else:
                    style_reference=value
            elif name in seen_names:
                self._error(f"Duplicate property '{name}' after normalization",name_start,"PARPROP005")
            else:
                seen_names.add(name)
                props.append(PropertyAssignment(name,value,self._span(name_start.location.offset,self._token_end_offset(value_tok))))
            if self._current().value==",":
                self._advance()
            elif self._current().value not in (";","{","}"):
                self._error("Expected ',' between properties",self._current(),"PARPROP004")
                self._recover_property()
        return props,style_reference


    def _recover_property(self):
        while self._current().kind!=TokenKind.EOF and self._current().value not in (",",";","{","}"):
            self._advance()
        if self._current().value==",": self._advance()

    def _recover_statement(self):
        while self._current().kind!=TokenKind.EOF and self._current().value not in (";","}"):
            self._advance()
        if self._current().value==";": self._advance()
