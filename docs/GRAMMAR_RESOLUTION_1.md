# Core Grammar Resolution Proposal 1

**Status:** Proposed — not frozen  
**Purpose:** Resolve the two highest-priority structural ambiguities identified in `SYNTAX_AUDIT.md` before parser implementation.

## 1. Canonical property placement

All element properties and style application occur after the colon (`:`) in the property list.

Style definitions remain a distinct declaration form:

```anzer
anzer make paragraph style 1:
    color="black",
    text-size="16px";
```

Style application uses the same property-list position as ordinary properties:

```anzer
anzer make paragraph:
    use style="paragraph style 1",
    text="Styled text.";
```

Direct properties override the referenced style. Proposed precedence:

1. Element defaults
2. Reusable style values
3. Direct element properties

Compact form is equivalent:

```anzer
anzer make paragraph: use style="paragraph style 1", text="Styled text.";
```

Do not support a second style-reference placement outside the property list in v0.1.

## 2. Leaf statements vs. containers

The statement terminator determines the statement shape:

- `;` ends a leaf statement (or style declaration).
- `{` opens a container body.
- `}` closes the most recently opened container.

A container header may have properties. It ends with `{`, not `;`.

```anzer
anzer make card:
    background="white",
    padding="16px" {
    anzer make title: text="Card";
    anzer make paragraph: text="Content";
}
```

Compact form:

```anzer
anzer make card: background="white", padding="16px" { anzer make title: text="Card"; anzer make paragraph: text="Content"; }
```

Both forms should parse to the same structure. Newlines and indentation are formatting only, except where required to separate tokens.

## 3. Nested and empty containers

Nested containers are allowed:

```anzer
anzer make section {
    anzer make card {
        anzer make paragraph: text="Inside the card.";
    }
}
```

Empty containers are syntactically allowed:

```anzer
anzer make section {}
```

Whether empty containers produce output or trigger a warning is a semantic/diagnostic question, not a grammar ambiguity.

## 4. Styles and containers stress tests

The parser should be tested with these cases before grammar freeze:

### Valid candidates

- Style definition followed by styled leaf.
- Styled leaf with direct override.
- Container with properties and children.
- Nested containers.
- Empty container.
- Compact and multiline equivalents.
- Leaf statements inside a container.
- Container header with no properties.
- Style declaration with compact and multiline properties.

### Invalid candidates

- Leaf statement missing its semicolon.
- Container header terminated with semicolon but followed by a body.
- Unmatched closing brace.
- Document end with an open container.
- Style application outside the property list.
- Duplicate property in one declaration (diagnostic policy to be defined).
- A leaf element incorrectly given a block opener.
- A container type terminated as a leaf when a body is intended (the parser should not guess).

## 5. Important parser rule

The parser must not infer whether an element is a container from its semantic name alone. The syntactic opener controls parsing:

- `;` => leaf
- `{` => container

The compiler can then validate whether that element is allowed to have children. This keeps parsing predictable and separates syntax errors from element/semantic errors.

## 6. Still unresolved (do not freeze yet)

- String escape rules and multiline strings.
- Property naming conventions and allowed value types.
- Boolean syntax.
- Duplicate property behavior.
- Element catalog and child restrictions.
- Void-element requirements (e.g., image).
- Inline link token syntax.
- Embed directive syntax and placement.
- Diagnostics and source locations.
- Whether semicolon/newline behavior inside quoted strings is supported.

## Recommendation

If this proposal is accepted, use it as the baseline for a focused lexer/parser stress test. Do not freeze the entire v0.1 grammar until the unresolved list above is addressed.
