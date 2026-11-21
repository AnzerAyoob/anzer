import unittest
from dataclasses import FrozenInstanceError
from anzer.ast import ElementDeclaration, PropertyAssignment, SourceSpan
from anzer.source import SourceLocation


class AstTests(unittest.TestCase):
    def span(self, start, end):
        return SourceSpan(SourceLocation(start, 1, start + 1), SourceLocation(end, 1, end + 1))

    def test_nodes_are_immutable(self):
        p = PropertyAssignment("text", "Hello", self.span(5, 10))
        node = ElementDeclaration("paragraph", (p,), None, None, self.span(0, 11))
        with self.assertRaises(FrozenInstanceError):
            node.name = "title"

    def test_children_distinguish_leaf_from_container(self):
        leaf = ElementDeclaration("paragraph", (), None, None, self.span(0, 5))
        container = ElementDeclaration("section", (), (), None, self.span(0, 5))
        self.assertIsNone(leaf.children)
        self.assertEqual(container.children, ())

    def test_span_offsets(self):
        span = self.span(3, 9)
        self.assertEqual((span.start_offset, span.end_offset), (3, 9))


if __name__ == "__main__":
    unittest.main()
