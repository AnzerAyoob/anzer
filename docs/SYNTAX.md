# Syntax Design — Command-Based Draft

> **HISTORICAL DOCUMENT — NOT NORMATIVE.** This draft predates the v0.1 decision freeze. It is retained for design history only. Implementers must follow `docs/ANZER_V0_1_UNIFIED_SPECIFICATION.md`, `docs/ANZER_V0_1_DECISION_FREEZE_1.md`, and `docs/ANZER_V0_1_GRAMMAR_TEST_CHECKLIST.md`.

**Status:** Experimental proposal. Not ratified or implemented.
> **HISTORICAL DOCUMENT — NOT NORMATIVE.** This draft predates the v0.1 decision freeze. It is retained for design history only. Implementers must follow `docs/ANZER_V0_1_UNIFIED_SPECIFICATION.md`, `docs/ANZER_V0_1_DECISION_FREEZE_1.md`, and `docs/ANZER_V0_1_GRAMMAR_TEST_CHECKLIST.md`.


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
- `title` defaults to H1 and emits an `h1`.
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

If the style already defines the compatible element type, no need to repeat type.

## Inline properties

Authors may also define properties directly on an element without creating a separate reusable style:

```
anzer make paragraph:
    font="Arial",
    color="black",
    text-size="10pt",
    text="This paragraph has inline properties.";
```

Reusable styles and inline properties are both supported design goals. Inline properties are useful for one-off elements; reusable styles are useful when repeated.

## Property precedence

Resolve properties in this order, from lowest to highest priority:
1. Element defaults.
2. Reusable style properties.
3. Direct properties on the element.

Direct element properties override reusable style properties.

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
- `}` closes the latest open container.
- Containers may contain child elements and nested containers.
- Empty containers are permitted.
- Unmatched braces must produce diagnostics.
- `<anzer end>` is invalid if any container remains open.

A container can use a reusable style or inline properties. Exact placement is still being refined.

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

Possible built-in style values include shadows `soft`, `hard`, `raised`, `3D`, and `glow`. Each should have standardized meaning and supported customization parameters.

## Embeds and link previews (exploration)

The proposed `anzer embed` family aims to hide provider-specific markup behind simple commands:

```
anzer embed tweet="post-url";
anzer embed drop="Journoist-Drop-url";
anzer embed video="video-url";
anzer embed link="webpage-url";
```

These are distinct intents:
- `tweet`: social post embed.
- `drop`: Journoist Drop embed (requires a supported platform embed contract).
- `video`: detect a supported video provider and render its player.
- `link`: rich preview card with title, description, preview image, and destination—not a plain inline hyperlink.

This syntax is an idea under test, not a finalized feature or universal provider guarantee. Unsupported, blocked, or unavailable embeds should degrade to a safe clickable fallback. Provider scripts, consent/privacy, performance, and URL validation need defined policies. Metadata retrieval for link previews must be designed to prevent server-side request forgery (SSRF) and unsafe fetching.

## Inline hyperlinks (exploration)

An ordinary inline hyperlink is different from an embed or rich preview. Proposed text syntax:

```
anzer make paragraph:
    text="Read {a-link="https://example.com/report", text="the report"} for details.";
```

This is experimental. Quoting/nesting and escaping may be difficult to parse safely. A simpler token or child-command syntax may be preferable if tests reveal ambiguity.

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
- Container property syntax.
- Embed provider registry, fallback behavior, privacy, and URL validation.
- Inline hyperlink grammar and escaping.
- Compiler implementation language.

Do not implement the parser until realistic examples have been reviewed and the grammar is sufficiently precise.
