import unittest
from dataclasses import replace

from anzer.diagnostics import DiagnosticCategory
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

    def effective(self, body):
        document = self.parse(body)
        validator = SemanticValidator()
        self.assertEqual(validator.validate(document), [])
        return validator.properties_for(document.declarations[-1])

    def assert_codes(self, body, *codes):
        self.assertEqual([error.code for error in self.validate(body)], list(codes))
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

    def test_explicit_axes_do_not_hide_an_invalid_gap_shorthand(self):
        self.assert_codes(
            'anzer make section: display="grid", gap="10px, 20px", row-gap=1, column-gap=2 {}',
            "SEMLOUT005",
        )

    def test_border_longhand_overrides_shorthand_regardless_of_order(self):
        resolved = self.effective('anzer make paragraph: text="x", border-color="blue", border="2px solid red";')
        self.assertEqual(self.border_values(resolved), ("2px", "solid", "blue"))

    def test_border_longhand_overrides_shorthand_when_declared_after(self):
        resolved = self.effective('anzer make paragraph: text="x", border="2px solid red", border-color="blue";')
        self.assertEqual(self.border_values(resolved), ("2px", "solid", "blue"))

    def test_direct_border_components_override_style_border_components(self):
        resolved = self.effective(
            'anzer make paragraph style 1: border="2px solid red";\n'
            'anzer make paragraph: text="x", use style="paragraph style 1", border-color="blue";'
        )
        self.assertEqual(self.border_values(resolved), ("2px", "solid", "blue"))

    def border_values(self, properties):
        names = ("border-width", "border-style", "border-color")
        self.assertNotIn("border", properties)
        self.assertEqual(tuple(properties[name].name for name in names), names)
        return tuple(properties[name].value for name in names)

    def test_border_shorthand_resolves_each_component_and_omission(self):
        cases = {
            "2px dashed red": ("2px", "dashed", "red"),
            "DASHED 2 PIXELS": ("2px", "dashed", "currentcolor"),
            "red 2": ("2px", "none", "red"),
            "#ABC dashed": ("medium", "dashed", "#abc"),
            "thin": ("thin", "none", "currentcolor"),
            "dashed": ("medium", "dashed", "currentcolor"),
            "red": ("medium", "none", "red"),
            "0 hidden transparent": ("0", "hidden", "transparent"),
        }
        for shorthand, expected in cases.items():
            with self.subTest(shorthand=shorthand):
                properties = self.effective(f'anzer make paragraph: text="x", border="{shorthand}";')
                self.assertEqual(self.border_values(properties), expected)
                self.assertEqual(properties["border-width"].span.start.line, 2)
                self.assertEqual(properties["border-width"].span, properties["border-color"].span)

    def test_direct_shorthand_overrides_style_components_including_omitted_parts(self):
        properties = self.effective(
            'anzer make image style 1: border-color="blue", border="3px solid red";\n'
            'anzer make image: border-width=4, border="dashed", src="image.png", use style="image style 1";'
        )
        self.assertEqual(self.border_values(properties), ("4px", "dashed", "currentcolor"))

    def test_invalid_border_shorthand_reports_one_value_error(self):
        for value in ("", "thick 2px", "red blue", "none dashed", "10 percent red",
                      "2 furlongs solid", "-2px red", "red, 2px", "2..px"):
            with self.subTest(value=value):
                self.assert_codes(f'anzer make paragraph: text="x", border="{value}";', "SEMPROP005")

    def test_defaults_styles_and_direct_aliases_have_ordered_precedence(self):
        for direct in ('font-family="Roboto", minimum---width="20 PIXELS", type="DIV"',
                       'type="DIV", min-width=20, font="Roboto"'):
            with self.subTest(direct=direct):
                properties = self.effective(
                    'anzer make paragraph style 1: font="Arial", min-width=10, type="SPAN", color="Blue";\n'
                    f'anzer make paragraph: {direct}, use style="paragraph style 1", text="x";'
                )
                self.assertEqual({key: prop.value for key, prop in properties.items()}, {
                    "type": "div", "font-family": "Roboto", "min-width": "20px",
                    "color": "blue", "text": "x",
                })
                self.assertEqual(list(properties), ["color", "font-family", "min-width", "text", "type"])
        self.assertEqual(self.effective('anzer make title: text="x";')["type"].value, "h1")
        inherited = self.effective(
            'anzer make title style 1: type="H2";\n'
            'anzer make title: text="x", use style="title style 1";'
        )
        self.assertEqual(inherited["type"].value, "h2")

    def test_noncanonical_ast_properties_cannot_bypass_duplicate_validation(self):
        document = self.parse('anzer make paragraph: text="x", font="Arial", width=20;')
        element = document.declarations[0]
        props = list(element.properties)
        props[1] = replace(props[1], name="font")
        props[2] = replace(props[2], name="font -- family")
        altered = replace(document, declarations=(replace(element, properties=tuple(props)),))
        result = SemanticValidator().validate(altered)
        self.assertEqual([error.code for error in result], ["SEMPROP006"])
        self.assertEqual(result[0].location, props[2].span.start)
        self.assertEqual(result[0].category, DiagnosticCategory.VALIDATION)

    def test_style_errors_are_reported_at_declaration_once(self):
        self.assert_codes(
            'anzer make image style 1: minimum width=20;\n'
            'anzer make image: src="a.jpg", use style="image style 1";\n'
            'anzer make image: src="b.jpg", use style="image style 1";',
            "SEMPROP002",
        )
        self.assert_codes('anzer make paragraph: text="x", use style="";', "SEMSTYLE003")

    def test_invalid_style_action_is_checked_once_even_without_a_use(self):
        style = 'anzer make button style 1: action="alert";'
        self.assert_codes(style, "SEMACT001")
        self.assert_codes(
            style + '\nanzer make button: text="x", use style="button style 1";',
            "SEMACT001",
        )

    def test_shared_alignment_uses_effective_flex_or_grid_mode(self):
        for display in ("flex", "inline-flex", "grid", "inline-grid"):
            with self.subTest(display=display):
                properties = self.effective(
                    'anzer make section style 1: justify-content="start", align-items="end", align-content="stretch";\n'
                    f'anzer make section: display="{display}", use style="section style 1" {{}}'
                )
                prefix = "flex-" if display.endswith("flex") else ""
                self.assertEqual(properties["justify-content"].value, prefix + "start")
                self.assertEqual(properties["align-items"].value, prefix + "end")
                self.assertEqual(properties["align-content"].value, "stretch")

    def test_layout_modes_and_property_specific_alignment_values(self):
        for property_name, value in (("justify-content", "center"), ("align-items", "baseline"),
                                     ("align-content", "stretch")):
            for display in ("", 'display="block", '):
                with self.subTest(property=property_name, display=display):
                    self.assert_codes(f'anzer make section: {display}{property_name}="{value}" {{}}', "SEMLOUT006")
        for body, code in (
            ('display="grid", flex-direction="row"', "SEMLOUT002"),
            ('display="inline-grid", flex-wrap="wrap"', "SEMLOUT002"),
            ('display="flex", grid-auto-flow="row"', "SEMLOUT003"),
            ('display="flex", justify-items="center"', "SEMLOUT003"),
            ('display="grid", justify-content="baseline"', "SEMLOUT005"),
            ('display="unknown", align-items="center"', "SEMLOUT005"),
        ):
            with self.subTest(body=body):
                self.assert_codes(f"anzer make container: {body} {{}}", code)
        self.assert_codes(
            'anzer make section style 1: display="grid", grid-template-columns="1fr";\n'
            'anzer make section: use style="section style 1", display="flex" {}',
            "SEMLOUT003",
        )
        self.assert_codes('anzer make paragraph: text="x", gap="-1px";', "SEMLOUT001")

    def test_ids_resolve_forward_nested_and_multiple_toggle_references(self):
        self.assert_codes(
            'anzer make button: text="Open", action="toggle", target="details";\n'
            'anzer make container { anzer make section: id="details" {} }\n'
            'anzer make button: text="Close", action="toggle", target="details";'
        )
        self.assert_codes(
            'anzer make button: text="Open", action="toggle", target="one";\n'
            'anzer make section style 1: id="original";\n'
            'anzer make section: use style="section style 1", id="one" {}'
        )

    def test_invalid_id_and_toggle_diagnostics_are_distinct(self):
        for body, codes in (
            ('anzer make container: id="" {}', ("SEMID002",)),
            ('anzer make container: id="   " {}', ("SEMID002",)),
            ('anzer make section: id=123 {}', ("SEMPROP004",)),
            ('anzer make button: text="x", action="toggle";', ("SEMACT002",)),
            ('anzer make button: text="x", action="toggle", target="";', ("SEMACT002",)),
            ('anzer make button: text="x", action="toggle", target=42;', ("SEMPROP004",)),
            ('anzer make button: text="x", action=false, target="absent";', ("SEMPROP004",)),
            ('anzer make button: text="x", target=42;', ("SEMPROP004",)),
            ('anzer make button: text="x", target="";', ("SEMACT002",)),
            ('anzer make button: text="x", action="toggle", target="missing";', ("SEMACT004",)),
            ('anzer make paragraph: text="x", id="leaf";\n'
             'anzer make button: text="x", action="toggle", target="leaf";', ("SEMPROP001", "SEMACT004")),
            ('anzer make section: id="leaf";\n'
             'anzer make button: text="x", action="toggle", target="leaf";', ("SEMELEM003", "SEMACT004")),
        ):
            with self.subTest(body=body):
                self.assert_codes(body, *codes)
        errors = self.validate(
            'anzer make paragraph: text="x", id="leaf";\n'
            'anzer make button: text="x", action="toggle", target="leaf";'
        )
        self.assertIn("must identify a section or container block", errors[-1].message)

    def test_duplicate_ids_report_the_later_declaration_without_target_cascades(self):
        errors = self.validate(
            'anzer make button: text="x", action="toggle", target="same";\n'
            'anzer make section: id="same" {}\n'
            'anzer make container: id="same" {}'
        )
        self.assertEqual([error.code for error in errors], ["SEMID001"])
        self.assertEqual((errors[0].location.line, errors[0].location.column), (4, 23))
        self.assertEqual(errors[0].category, DiagnosticCategory.SEMANTIC)

    def test_images_accept_only_reviewed_native_properties_and_image_metadata(self):
        properties = self.effective(
            'anzer make image: src="/photo.png", alt="", width=320, height="auto", '
            'margin="-2px auto", border="2 pixels solid red", border-radius="20%";'
        )
        self.assertEqual(self.border_values(properties), ("2px", "solid", "red"))
        self.assertEqual(properties["width"].value, "320px")
        for name, value in (("font", '"Arial"'), ("text-size", "20"), ("background-color", '"red"'),
                            ("padding", "10"), ("minimum width", "20"), ("max-height", '"none"')):
            with self.subTest(name=name):
                self.assert_codes(f'anzer make image: src="/photo.png", {name}={value};', "SEMPROP002")
        self.assert_codes('anzer make image: src="/photo.png", display="grid";', "SEMLOUT001")
        self.assert_codes('anzer make image: src="/photo.png", text="x";', "SEMPROP001")

    def test_length_and_track_normalization_with_friendly_units(self):
        properties = self.effective(
            'anzer make section: width="12 VIEWPORT WIDTH", min-height=0, max-width="none", '
            'padding="1 centimetre 0", margin="-2 points auto", border-radius="0.25rem", '
            'display="grid", gap="1 CENTIMETRE 2 PX", row-gap="2 rem", '
            'grid-template-columns="0 .5fr 2 viewport minimum 50 percent" {}'
        )
        for name, value in {
            "width": "12vw", "min-height": "0", "max-width": "none", "padding": "1cm 0",
            "margin": "-2pt auto", "border-radius": "0.25rem", "column-gap": "2px",
            "row-gap": "2rem", "grid-template-columns": "0 0.5fr 2vmin 50%",
        }.items():
            self.assertEqual(properties[name].value, value)
        self.assertNotIn("gap", properties)

    def test_property_specific_lengths_reject_malformed_and_negative_values(self):
        cases = {
            "width": ("-1px", "2emmm", "1e2px", "1px + 2px", "1.px", "١px"),
            "height": ("none",),
            "padding": ("auto", "-.1px", "1 2 3 4 5"),
            "margin": ("1px,2px",),
            "border-width": ("10%", "-1px"),
            "border-radius": ("-1px", "1px 2px"),
            "min-width": ("none", "auto", "-1px"),
            "max-height": ("auto", "-1px"),
        }
        for name, values in cases.items():
            for value in values:
                with self.subTest(name=name, value=value):
                    self.assert_codes(f'anzer make section: {name}="{value}" {{}}', "SEMPROP005")
        self.assert_codes('anzer make section: width=true {}', "SEMPROP004")
        for name, value in (("row-gap", "1px 2px"), ("gap", "1px, 2px"),
                            ("column-gap", "-2px"), ("grid-auto-rows", "0fr")):
            self.assert_codes(f'anzer make section: display="grid", {name}="{value}" {{}}', "SEMLOUT005")

    def test_url_validation_accepts_relative_http_ipv6_and_mailto_forms(self):
        for url in (
            "photo.png", "./images/photo.png", "../photo.png", "/images/photo.png",
            "#anchor", "?query=save", "https://example.com./a%20b?x=1#y",
            "HTTP://localhost:8080", "https://127.0.0.1:65535/a",
            "https://[2001:db8::1]:443/photo.png", "https://bücher.example/é",
        ):
            with self.subTest(url=url):
                self.assert_codes(f'anzer make link: text="x", url="{url}";')
                self.assert_codes(f'anzer make image: src="{url}";')
        for url in ("mailto:", "mailto:alice@example.com", "MAILTO:alice@example.com,bob@example.com?subject=Hi%20there",
                    "mailto:?subject=Hi"):
            self.assert_codes(f'anzer make link: text="x", url="{url}";')
            self.assert_codes(f'anzer make image: src="{url}";', "SEMURL002")

    def test_url_validation_rejects_bad_schemes_authorities_and_separators(self):
        for url in (
            "", "ftp://example.com/a", "JaVaScRiPt:alert(1)", "data:image/png;base64,x",
            "//example.com/a", "https:/example.com", "https:example.com", "https:///example.com",
            "https://-example.com", "https://example..com", "https://foo_bar.example",
            "https://999.0.0.1", "https://example.com:", "https://example.com:65536",
            "https://example.com:-1", "https://example.com:abc", "https://[::1",
            "https://[invalid]/", "https://[::1]extra/", "https://[::1]:bad", "https://::1/",
            " https://example.com", "relative path", r"https:\\example.com",
            r"java\tscript:alert(1)", r"\nhttps://example.com", "https://example.com/\x7f",
        ):
            with self.subTest(url=url):
                self.assert_codes(f'anzer make link: text="x", url="{url}";', "SEMURL001")
                self.assert_codes(f'anzer make image: src="{url}";', "SEMURL002")
        for url in ("mailto://example.com", "mailto:///alice@example.com", "mailto://?subject=Hi", "mailto:alice@"):
            self.assert_codes(f'anzer make link: text="x", url="{url}";', "SEMURL001")
        self.assert_codes('anzer make link: text="x", url=false;', "SEMPROP004")

    def test_diagnostics_are_source_ordered_and_validator_can_be_reused(self):
        document = self.parse(
            'anzer make button: text="x", action="toggle", target="missing";\n'
            'anzer make link: text="x", url="https://[invalid]/";\n'
            'anzer make image style 1: padding=10;'
        )
        validator = SemanticValidator()
        errors = validator.validate(document)
        self.assertEqual([error.code for error in errors], ["SEMACT004", "SEMURL001", "SEMPROP002"])
        self.assertEqual([(error.location.line, error.location.column) for error in errors],
                         [(2, 47), (3, 28), (4, 27)])
        self.assertEqual([error.category for error in errors], [
            DiagnosticCategory.SEMANTIC, DiagnosticCategory.VALIDATION, DiagnosticCategory.VALIDATION,
        ])
        valid = self.parse('anzer make section: id="same" {}')
        self.assertEqual(validator.validate(valid), [])
        self.assertEqual(validator.validate(valid), [])
        self.assertEqual(validator.properties_for(valid.declarations[0])["id"].value, "same")

    def test_protocol_relative_urls_rejected(self):
        self.assertTrue(any(e.code == "SEMURL001" for e in self.validate('anzer make link: text="x", url="//example.com/path";')))
        self.assertTrue(any(e.code == "SEMURL002" for e in self.validate('anzer make image: src="//example.com/image.png";')))

if __name__=="__main__": unittest.main()
