# Syntax Design — Command-Based Draft

**Status:** Experimental proposal. Not ratified or implemented.

Anzer is intended to use readable commands and properties rather than requiring authors to write HTML, CSS, and JavaScript separately.

## Document boundaries

```
<anzer start>

...instructions...

<anzer end>
```

The draft requires both markers and supports compact and multiline formatting within them.

## Elements and defaults

```
anzer make title: text="My Main Heading";
anzer make paragraph: text="Welcome to my page.";
anzer make button: text="Click Me";
```

Proposed default semantics:
- `title` defaults to `H1` and emits an HTML `h1`.
- `paragraph` defaults to paragraph semantics and emits `p`.
- `button` defaults to button semantics and emits `button`.
- `link` defaults to link semantics and emits `a`.
- `image` defaults to image semantics and emits `img`.

Heading types H1–H6 are semantic heading levels as well as visual presets. A title may override its default type, for example `type="H2"`.

## Reusable numbered styles

```
anzer make paragraph style 1:
    font="Arial",
    type="paragraph",
    color="black",
    text-size="10pt";

anzer make paragraph style 2:
    font="Noto Nastaliq",
    type="paragraph",
    color="black",
    text-size="12pt";
```

Styles are reusable definitions. Their numbers do not refer to paragraph positions.

## Applying a style

```
anzer make paragraph:
    use style="paragraph style 2",
    text="This paragraph uses style 2.";
```

If the style already defines the compatible element type, the element does not need to repeat it.

Direct element properties override properties from the reusable style. Defaults are lowest priority, reusable style next, and direct properties highest.

## Single-line and multiline

Compact:

```
anzer make paragraph: use style="paragraph style 2", text="Hello";
```

Multiline:

```
anzer make paragraph:
    use style="paragraph style 2",
    text="Hello";
```

They should compile identically. Line breaks are not intended to alter instruction semantics.

## Presets

Possible built-in style values include shadow presets `soft`, `hard`, `raised`, `3D`, and `glow`. Each will have a standardized meaning and supported customization parameters.

## Design principles

- No unnecessary duplication.
- Semantic output, not merely visual imitation.
- Styles reusable by name/number and independent of element positions.
- Clear property precedence.
- Compact or multiline formatting at the author's choice.
- Helpful errors for incompatible styles and element types.

## Still unresolved

- Complete command grammar and delimiters.
- Element catalog and nesting rules.
- Property naming and accepted value types.
- Style scope, uniqueness, and reference rules.
- Compatibility diagnostics.
- Behavior/event syntax.
- Responsive layout syntax.

Do not implement the parser until realistic examples have been reviewed and the grammar is sufficiently precise.
