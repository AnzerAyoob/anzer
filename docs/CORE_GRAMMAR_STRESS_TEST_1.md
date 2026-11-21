# Core Grammar Stress Test 1

**Status:** Specification stress suite; decisions are frozen, compiler execution pending  
**Scope:** Statement endings and container parsing only. This does not freeze the full grammar.

## Accepted rule under test

- `;` terminates a leaf statement.
- `{` opens a container.
- `}` closes the most recently opened container.
- The parser does not infer container structure from an element's name.
- Newlines and indentation are formatting; compact and multiline forms should parse equivalently.

## A. Valid test cases

### A1. Basic leaf

```anzer
anzer make paragraph: text="Hello";
```

Expected: one paragraph leaf.

### A2. Leaf with token-separating line breaks

```anzer
anzer make paragraph:
text="Hello";
```

Expected: same structure as A1. This tests that indentation is not required and a newline can separate tokens without changing statement shape.

### A3. Leaf with multiline properties

```anzer
anzer make paragraph:
    color="black",
    font-size="16px",
    text="Hello";
```

Expected: one leaf with three properties.

### A4. Container without properties

```anzer
anzer make section {
    anzer make paragraph: text="Inside";
}
```

Expected: section with one paragraph child.

### A5. Container with properties

```anzer
anzer make container:
    background="white",
    padding="16px" {
    anzer make paragraph: text="Inside";
}
```

Expected: container properties plus one child.

### A6. Compact container

```anzer
anzer make container: background="white", padding="16px" { anzer make paragraph: text="Inside"; }
```

Expected: same AST as A5.

### A7. Nested containers

```anzer
anzer make section {
    anzer make container {
        anzer make paragraph: text="Deep";
    }
}
```

Expected: section > container > paragraph.

### A8. Empty container

```anzer
anzer make section {}
```

Expected: parse succeeds; container node has zero children; no diagnostic.

### A9. Sequential siblings

```anzer
anzer make paragraph: text="First";
anzer make paragraph: text="Second";
```

Expected: two sibling leaf nodes.

### A10. Container followed by sibling

```anzer
anzer make section {
    anzer make paragraph: text="Child";
}
anzer make paragraph: text="Sibling";
```

Expected: section and paragraph as document-level siblings.

### A11. Style declaration and use

```anzer
anzer make paragraph style 1:
    color="black",
    font-size="16px";

anzer make paragraph:
    use style="paragraph style 1",
    text="Styled";
```

Expected: style declaration followed by a leaf using that style.

### A12. Style override

```anzer
anzer make paragraph style 1: color="black", font-size="16px";

anzer make paragraph:
    use style="paragraph style 1",
    color="blue",
    text="Override";
```

Expected: direct color property overrides style color. Style reference remains in the property list.

## B. Invalid test cases

Invalid cases should produce a diagnostic; the parser must not silently guess or repair structure.

### B1. Missing leaf terminator

```anzer
anzer make paragraph: text="Missing terminator"
anzer make paragraph: text="Next";
```

Expected: error for first statement; do not merge the two statements.

### B2. Semicolon where container opener is required

```anzer
anzer make section;
    anzer make paragraph: text="Unexpected child";
```

Expected: first declaration parses as a leaf; the following paragraph parses as a separate document-level statement; no implicit nesting.

### B3. Unmatched closing brace

```anzer
anzer make section {}
}
```

Expected: unmatched closing-brace diagnostic.

### B4. Unclosed container at document end

```anzer
anzer make section {
    anzer make paragraph: text="Child";
```

Expected: diagnostic indicating an unclosed container at end of document.

### B5. Invalid style-reference placement

```anzer
anzer make paragraph use style="paragraph style 1": text="Styled";
```

Expected: reject this placement; style application is only permitted in the property list after the colon.

### B6. Leaf given a block opener (semantic check)

```anzer
anzer make image: src="photo.jpg" {
    anzer make paragraph: text="Not allowed";
}
```

Expected: semantic error `void-element-has-children`; no output file.

### B7. Container header terminated as leaf

```anzer
anzer make container: padding="16px";
```

Expected: syntactically a leaf. It must not be guessed to be a container merely because container is commonly a container.

## C. Compact/multiline equivalence pairs

The following pairs should produce equivalent ASTs:

- A3 and its compact single-line property equivalent.
- A5 and A6.
- A7 rewritten on one line (with token separators intact).
- A11 with style declaration and styled element compacted.

The equivalence comparison should ignore source whitespace and formatting, but preserve string contents and the order of child nodes.

## D. Expected diagnostics behavior

At minimum, the parser test harness should assert:

- Diagnostic category (syntax vs semantic).
- Source line and column when available.
- No silent statement merging.
- No implicit container creation.
- No implicit container closure at document end.
- No loss of later valid statements where recovery is safe.

## E. Not tested/frozen here

This test does not resolve:

- Quoting and escaping.
- Whether commas are mandatory between properties.
- Property value typing.
- Duplicate property behavior.
- Newline handling inside strings.
- Element catalog.
- Void-element list.
- Style-name lookup and duplicate style declarations.
- Embed/directive parsing.
- Inline link parsing.

These require separate focused decisions before grammar freeze.
