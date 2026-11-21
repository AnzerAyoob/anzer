# Anzer Language Specification — v0.1 (Design Draft)

**Status:** Proposal — not frozen, not implemented  
**Target:** Browser web pages  
**Source extension:** `.anzer`

This specification records the current design direction. Syntax is still provisional and must be tested against realistic examples before implementation.

## 1. Goals

- Make web authoring approachable through readable, command-oriented instructions.
- Describe structure, semantics, appearance, and basic behavior in one source file.
- Compile to standard HTML, CSS, and JavaScript for ordinary browsers and hosting.
- Allow compact single-line and readable multiline instructions interchangeably.
- Reduce repetition through reusable numbered style definitions, while allowing inline properties.
- Keep generated output safe, accessible, and deterministic.

## 2. Non-goals for the first compiler

- Native browser support for `.anzer`.
- Server-side programming, databases, networking APIs, or package management.
- General-purpose loops, classes, modules, or user-defined functions.
- Arbitrary raw HTML or JavaScript execution.
- A custom runtime for simple static pages.

## 3. Document boundaries

```
<anzer start>

...Anzer instructions...

<anzer end>
```

Both markers are required in this proposal. All instructions between them belong to the Anzer document. The compiler must support compact and multiline instruction formatting with equivalent meaning.

## 4. Command direction

Anzer uses command-oriented declarations, currently proposed as:

```
anzer make title: text="My heading";
anzer make paragraph: text="My paragraph";
```

The exact command grammar and punctuation are not finalized.

## 5. Element defaults and semantic types

Elements have default semantic types to avoid unnecessary duplication. Proposed defaults include:

| Element command | Default type | HTML output |
|---|---|---|
| title | H1 | `<h1>` |
| paragraph | paragraph | `<p>` |
| button | button | `<button>` |
| link | link | `<a>` |
| image | image | `<img>` |

A title defaults to H1 when no type is specified. Explicit type overrides are permitted where compatible, e.g. a title with `type="H2"`. Heading types H1–H6 are semantic HTML headings and also receive corresponding default visual presentation.

The final element list and default mapping are not yet exhaustive.

## 6. Reusable numbered styles

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

Style definitions are independent of document element positions and can be referenced by name.

## 7. Applying a reusable style

```
anzer make paragraph:
    use style="paragraph style 2",
    text="Sample paragraph";
```

When a style defines the compatible element type, the user does not need to repeat that type on the element.

## 8. Inline properties

Properties may also be declared directly on an element without defining a reusable style:

```
anzer make paragraph:
    font="Arial",
    color="black",
    text-size="10pt",
    text="One-off paragraph styling";
```

Both inline and reusable styles are intended to be supported. Choose inline properties for one-off elements and reusable styles when a set of properties should be shared.

## 9. Property precedence

Proposed resolution order, from lowest to highest:

1. Element defaults.
2. Reusable style properties.
3. Direct properties specified on the element.

Direct properties override style properties. A style supplies a default type and appearance for compatible elements.

## 10. Style compatibility

If a style's semantic type conflicts with the target element, the compiler must report a diagnostic rather than silently generate contradictory semantics. The precise warning/error policy remains to be decided.

## 11. Containers and nesting

The accepted design direction is brace-delimited containers:

```
anzer make section {
    anzer make title: text="About";
    anzer make paragraph: text="Section content";
}
```

Opening braces begin container bodies; closing braces end the most recently opened container. Containers may nest and may be empty. Unmatched braces and document end markers encountered with open containers must be diagnosed. Exact property/style placement for containers is not yet finalized.

## 12. Single-line and multiline formatting

Both formats are intended to be equivalent:

```
anzer make paragraph: use style="paragraph style 2", text="Hello";
```

and

```
anzer make paragraph:
    use style="paragraph style 2",
    text="Hello";
```

Whitespace and line breaks are formatting and should not change meaning, except where token separation is required.

## 13. Styling presets

Anzer may provide named visual presets for properties such as shadows. Proposed shadow presets include `soft`, `hard`, `raised`, `3D`, and `glow`. Each preset must have defined rendering behavior rather than ambiguous interpretation. Users may customize supported parameters such as color, size, intensity, and position.

## 14. Embeds and rich link previews (design exploration)

A proposed `anzer embed` family uses concise commands to request provider-aware content:

```
anzer embed tweet="post-url";
anzer embed drop="Journoist-Drop-url";
anzer embed video="video-url";
anzer embed link="webpage-url";
```

The intents are different:
- `tweet`: social post embed.
- `drop`: Journoist Drop embed, contingent on a supported platform embed contract.
- `video`: detect a supported video provider and render a suitable player.
- `link`: rich preview card (title, description, image, and destination), not an ordinary inline hyperlink.

This is not a finalized command or a guarantee that every provider permits embedding. Unsupported or blocked content should fall back to a safe clickable link. Provider scripts, privacy/consent, loading/performance, URL validation, and metadata-fetch security must be specified. Any server-side metadata fetch must guard against SSRF and unsafe URL targets.

## 15. Inline hyperlinks (design exploration)

Ordinary inline hyperlinks are separate from embeds and preview cards. One syntax proposal:

```
anzer make paragraph:
    text="Read {a-link="https://example.com/report", text="the report"} for details.";
```

This proposal needs parser tests for quote nesting, escaping, and token boundaries. If it is ambiguous or brittle, use a simpler inline token or child-command design.

## 16. Proposed example

```
<anzer start>

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

anzer make title:
    font="Times New Roman",
    color="black",
    shadow="3D",
    shadow-position="bottom",
    shadow-size="1px",
    text="This is a sample title";

anzer make paragraph:
    use style="paragraph style 1",
    text="This paragraph uses style 1.";

anzer make paragraph:
    use style="paragraph style 2",
    text="This paragraph uses style 2.";

<anzer end>
```

This example illustrates the direction only; it is not compilable syntax.

## 17. Compilation model

`Source → Lexer → Parser → AST → Validation → HTML/CSS/JS Generator → Output Files`

Suggested outputs:
- `dist/index.html`
- `dist/assets/anzer.css`
- `dist/assets/anzer.js` (only when needed)

## 18. Safety and diagnostics

- Escape text and attributes correctly.
- Validate and safely emit CSS values.
- Do not execute source during compilation.
- Arbitrary raw HTML and JavaScript are out of scope for the initial compiler.
- Errors should include source file, line, column, and actionable explanation.
- Reject malformed input rather than emitting broken partial output.

## 19. Next design validation

Before grammar freeze, test syntax against realistic page scenarios: a simple landing page, article/news page, multilingual content with styles, cards/sections, forms/interactions, embeds, and inline hyperlinks. Identify ambiguities and revise the grammar based on those tests.

## 20. Change policy

This is a design draft, not a compatibility promise. Syntax changes are expected before implementation. Once a release is stable, changes must be documented and versioned.
