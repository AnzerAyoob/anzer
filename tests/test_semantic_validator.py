import unittest
from anzer.source import Source
from anzer.lexer import Lexer
from anzer.parser import Parser
from anzer.semantic import SemanticValidator

class SemanticValidatorTests(unittest.TestCase):
    def parse(self, body):
        source=Source(f"<anzer start>\n{body}\n<anzer end>","semantic.anzer")
        tokens,lex_errors=Lexer(source).tokenize()
        document,parse_errors=Parser(source,tokens).parse_document()
        self.assertEqual(lex_errors,[]); self.assertEqual(parse_errors,[])
        return document
    def validate(self,body): return SemanticValidator().validate(self.parse(body))
    def test_valid_container_and_matching_style_reference(self):
        errors=self.validate('anzer make paragraph style 1: color="blue"; anzer make section: use style="section style 2" { anzer make paragraph: text="Styled", use style="paragraph style 1"; } anzer make section style 2: padding=10;')
        self.assertEqual(errors,[])
    def test_required_properties_are_enforced(self):
        self.assertTrue(any(e.code=="SEMELEM004" for e in self.validate('anzer make link: text="bad";')))
    def test_unsafe_link_scheme_is_rejected(self):
        self.assertTrue(any(e.code=="SEMURL001" for e in self.validate('anzer make link: text="x", url="javascript:alert(1)";')))
    def test_toggle_requires_target_and_resolves_container(self):
        self.assertTrue(any(e.code=="SEMACT004" for e in self.validate('anzer make button: text="Toggle", action="toggle", target="missing";')))
    def test_layout_properties_require_flex_or_grid(self):
        self.assertTrue(any(e.code=="SEMLOUT004" for e in self.validate('anzer make section: gap=10;')))
    def test_layout_properties_are_container_only(self):
        self.assertTrue(any(e.code=="SEMLOUT001" for e in self.validate('anzer make paragraph: text="x", gap=10;')))
    def test_image_rejects_text_style_properties(self):
        self.assertTrue(any(e.code=="SEMPROP002" for e in self.validate('anzer make image: src="https://example.com/a.png", color="red";')))
    def test_unknown_property_is_rejected(self):
        self.assertTrue(any(e.code=="SEMPROP003" for e in self.validate('anzer make paragraph: text="x", colour="red";')))
    def test_image_padding_is_rejected(self):
        self.assertTrue(any(e.code=="SEMPROP002" for e in self.validate('anzer make image: src="https://example.com/a.png", padding=10;')))
    def test_container_accepts_native_style_and_layout_properties(self):
        self.assertEqual(self.validate('anzer make container: display="flex", gap=10, color="red" { }'),[])
    def test_unknown_element_kind(self):
        self.assertTrue(any(e.code=="SEMELEM001" for e in self.validate("anzer make banana;")))
    def test_leaf_cannot_have_children(self):
        self.assertTrue(any(e.code=="SEMELEM002" for e in self.validate("anzer make paragraph { anzer make button; }")))
    def test_container_requires_block_body(self):
        self.assertTrue(any(e.code=="SEMELEM003" for e in self.validate("anzer make section;")))
    def test_unknown_style_reference(self):
        self.assertTrue(any(e.code=="SEMSTYLE003" for e in self.validate('anzer make paragraph: use style="paragraph style 9";')))
    def test_style_target_mismatch(self):
        self.assertTrue(any(e.code=="SEMSTYLE004" for e in self.validate('anzer make button style 1: color="red"; anzer make paragraph: use style="button style 1";')))
    def test_duplicate_style_declaration(self):
        self.assertTrue(any(e.code=="SEMSTYLE002" for e in self.validate('anzer make paragraph style 1: color="red"; anzer make paragraph style 1: color="blue";')))
    def test_unknown_style_target(self):
        self.assertTrue(any(e.code=="SEMSTYLE001" for e in self.validate('anzer make banana style 1: color="red";')))
    def test_style_declaration_inside_container_is_rejected(self):
        self.assertTrue(any(e.code=="SEMSTYLE005" for e in self.validate('anzer make section { anzer make paragraph style 1: color="red"; }')))
    def test_html_embedding_outside_container(self):
        self.assertTrue(any(e.code=="SEMHTML001" for e in self.validate('anzer use html="<b>Hi</b>";')))
    def test_html_embedding_inside_container_allowed(self):
        self.assertEqual(self.validate('anzer make section { anzer use html="<b>Hi</b>"; }'),[])
    def test_invalid_color_rejected(self):
        self.assertTrue(any(e.code=="SEMPROP005" for e in self.validate('anzer make paragraph: text="x", color="not-a-color";')))
    def test_hex_color_forms_and_named_color_allowed(self):
        self.assertEqual(self.validate('anzer make paragraph: text="x", color="#abc", background-color="aliceblue";'),[])
    def test_invalid_font_weight_rejected(self):
        self.assertTrue(any(e.code=="SEMPROP005" for e in self.validate('anzer make paragraph: text="x", font-weight="950";')))
    def test_invalid_text_alignment_rejected(self):
        self.assertTrue(any(e.code=="SEMPROP005" for e in self.validate('anzer make paragraph: text="x", text-align="middle";')))
    def test_length_grammar_accepts_whitespace_before_unit(self):
        self.assertEqual(self.validate('anzer make paragraph: text="x", width="12 px";'),[])
    def test_length_grammar_rejects_repeated_decimal_points(self):
        self.assertTrue(any(e.code=="SEMPROP005" for e in self.validate('anzer make paragraph: text="x", width="12..px";')))
    def test_invalid_unit_rejected(self):
        self.assertTrue(any(e.code=="SEMPROP005" for e in self.validate('anzer make paragraph: text="x", width="12foo";')))
    def test_min_dimensions_reject_negative(self):
        self.assertTrue(any(e.code=="SEMPROP005" for e in self.validate('anzer make paragraph: text="x", min-width="-2px";')))
    def test_margin_allows_negative_and_auto(self):
        self.assertEqual(self.validate('anzer make paragraph: text="x", margin="-2px auto";'),[])
    def test_padding_rejects_auto(self):
        self.assertTrue(any(e.code=="SEMPROP005" for e in self.validate('anzer make paragraph: text="x", padding="auto";')))
    def test_border_style_enum(self):
        self.assertTrue(any(e.code=="SEMPROP005" for e in self.validate('anzer make paragraph: text="x", border-style="wavy";')))
    def test_border_shorthand_accepts_components(self):
        self.assertEqual(self.validate('anzer make paragraph: text="x", border="2px solid #abc";'),[])
    def test_layout_properties_resolve_across_style_and_element(self):
        self.assertEqual(self.validate('anzer make container style 1: display="flex"; anzer make container: use style="container style 1", gap=10 { }'),[])
    def test_direct_display_override_invalidates_style_layout(self):
        self.assertTrue(any(e.code=="SEMLOUT004" for e in self.validate('anzer make container style 1: display="flex"; anzer make container: use style="container style 1", display="block", gap=10 { }')))
    def test_border_shorthand_rejects_duplicate_component(self):
        self.assertTrue(any(e.code=="SEMPROP005" for e in self.validate('anzer make paragraph: text="x", border="2px solid dashed";')))
    def test_flex_enum_and_display_required(self):
        self.assertTrue(any(e.code=="SEMLOUT005" for e in self.validate('anzer make container: display="flex", flex-wrap="maybe" { }')))
    def test_grid_track_invalid_expression(self):
        self.assertTrue(any(e.code=="SEMLOUT005" for e in self.validate('anzer make container: display="grid", grid-template-columns="repeat(2, 1fr)" { }')))
    def test_grid_fr_track_valid(self):
        self.assertEqual(self.validate('anzer make container: display="grid", grid-template-columns="1fr 2fr" { }'),[])
    def test_gap_two_lengths_valid(self):
        self.assertEqual(self.validate('anzer make container: display="grid", gap="10px 20px" { }'),[])
    def test_gap_negative_rejected(self):
        self.assertTrue(any(e.code=="SEMLOUT005" for e in self.validate('anzer make container: display="flex", gap="-2px" { }')))
if __name__=="__main__": unittest.main()
