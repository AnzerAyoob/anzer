import unittest
from anzer.source import Source
from anzer.lexer import Lexer
from anzer.parser import Parser
from anzer.semantic import SemanticValidator


class SemanticValidatorTests(unittest.TestCase):
    def parse(self, body):
        source = Source(f"<anzer start>\n{body}\n<anzer end>", "semantic.anzer")
        tokens, lex_errors = Lexer(source).tokenize()
        document, parse_errors = Parser(source, tokens).parse_document()
        self.assertEqual(lex_errors, [])
        self.assertEqual(parse_errors, [])
        return document

    def validate(self, body):
        return SemanticValidator().validate(self.parse(body))

    def test_valid_container_and_matching_style_reference(self):
        errors = self.validate('anzer make paragraph style 1: color="blue"; anzer make section: use style="section style 2" { anzer make paragraph: text="Styled", use style="paragraph style 1"; } anzer make section style 2: padding=10;')
        self.assertEqual(errors, [])

    def test_required_properties_are_enforced(self):
        errors = self.validate("anzer make link: text="bad";")
        self.assertTrue(any(e.code == "SEMELEM004" for e in errors))

    def test_unsafe_link_scheme_is_rejected(self):
        errors = self.validate('anzer make link: text="x", url="javascript:alert(1)";')
        self.assertTrue(any(e.code == "SEMURL001" for e in errors))

    def test_toggle_requires_target_and_resolves_container(self):
        errors = self.validate('anzer make button: text="Toggle", action="toggle", target="missing";')
        self.assertTrue(any(e.code == "SEMACT004" for e in errors))

    def test_unknown_element_kind(self):
        errors = self.validate("anzer make banana;")
        self.assertTrue(any(e.code == "SEMELEM001" for e in errors))

    def test_leaf_cannot_have_children(self):
        errors = self.validate("anzer make paragraph { anzer make button; }")
        self.assertTrue(any(e.code == "SEMELEM002" for e in errors))

    def test_container_requires_block_body(self):
        errors = self.validate("anzer make section;")
        self.assertTrue(any(e.code == "SEMELEM003" for e in errors))

    def test_unknown_style_reference(self):
        errors = self.validate('anzer make paragraph: use style="paragraph style 9";')
        self.assertTrue(any(e.code == "SEMSTYLE003" for e in errors))

    def test_style_target_mismatch(self):
        errors = self.validate('anzer make button style 1: color="red"; anzer make paragraph: use style="button style 1";')
        self.assertTrue(any(e.code == "SEMSTYLE004" for e in errors))

    def test_duplicate_style_declaration(self):
        errors = self.validate('anzer make paragraph style 1: color="red"; anzer make paragraph style 1: color="blue";')
        self.assertTrue(any(e.code == "SEMSTYLE002" for e in errors))

    def test_unknown_style_target(self):
        errors = self.validate('anzer make banana style 1: color="red";')
        self.assertTrue(any(e.code == "SEMSTYLE001" for e in errors))

    def test_style_declaration_inside_container_is_rejected(self):
        errors = self.validate('anzer make section { anzer make paragraph style 1: color="red"; }')
        self.assertTrue(any(e.code == "SEMSTYLE005" for e in errors))

    def test_html_embedding_outside_container(self):
        errors = self.validate('anzer use html="<b>Hi</b>";')
        self.assertTrue(any(e.code == "SEMHTML001" for e in errors))

    def test_html_embedding_inside_container_allowed(self):
        errors = self.validate('anzer make section { anzer use html="<b>Hi</b>"; }')
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
