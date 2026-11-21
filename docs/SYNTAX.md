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

## Applying a reusable style

```
anzer make paragraph:
    use style="paragraph style 2",
    text="This paragraph uses style 2.";
```

If the style already defines the compatible element type, the element does not need to repeat it.

## Inline properties

Authors may also define properties directly on an element without creating a separate reusable style:

```
anzer make paragraph:
    font="Arial",
    color="black",
    text-size="10pt",
    text="This paragraph has inline properties.";
```

Reusable styles and inline properties are both supported design goals. Inline properties are useful for one-off elements; reusable styles are useful when the same appearance or compatible semantic defaults should be applied repeatedly.

## Property precedence

Resolve properties in this order, from lowest to highest priority:
1. Element defaults.
2. Reusable style properties.
3. Direct properties on the element.

Direct element properties override reusable style properties. A compatible semantic type supplied by a reusable style need not be repeated on the element.

## Style compatibility

A style with a semantic type incompatible with its target element must not silently produce contradictory HTML semantics. The compiler should report a diagnostic; whether that is a warning or error remains open.

## Containers and nesting (proposal accepted; grammar provisional)

Brace-delimited blocks are the proposed way to define nested content:

```
anzer make section {
    anzer make title: text="About Us";
    anzer make paragraph: text="Our story...";
}
```

- `{` opens a container body.
- `}` closes the most recently opened container.
- Containers may contain child elements and nested containers.
- Empty containers are permitted.
- Unmatched opening/closing braces must produce diagnostics.
- `<anzer end>` is invalid if any container remains open.

A container can use a reusable style or inline properties. Exact placement of properties relative to the opening brace is still being refined.

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
- Inline properties available for one-off styling.
- Clear property precedence.
- Compact or multiline formatting at the author's choice.
- Helpful errors for incompatible styles and element types.

## Still unresolved

- Complete command grammar and delimiters.
- Element catalog and nesting rules in detail.
- Property naming and accepted value types.
- Style scope, uniqueness, and reference rules.
- Compatibility diagnostic severity.
- Behavior/event syntax.
- Responsive layout syntax.
- Exact container syntax when style/properties are present.

Do not implement the parser until realistic examples have been reviewed and the grammar is sufficiently precise.
