# Anzer Syntax Audit — Pre-Grammar Review

> **HISTORICAL DOCUMENT — NOT NORMATIVE.** This draft predates the v0.1 decision freeze. It is retained for design history only. Implementers must follow `docs/ANZER_V0_1_UNIFIED_SPECIFICATION.md`, `docs/ANZER_V0_1_DECISION_FREEZE_1.md`, and `docs/ANZER_V0_1_GRAMMAR_TEST_CHECKLIST.md`.

**Status:** Historical pre-freeze audit; superseded by accepted v0.1 decisions in `ANZER_V0_1_DECISION_FREEZE_1.md`.
> **HISTORICAL DOCUMENT — NOT NORMATIVE.** This draft predates the v0.1 decision freeze. It is retained for design history only. Implementers must follow `docs/ANZER_V0_1_UNIFIED_SPECIFICATION.md`, `docs/ANZER_V0_1_DECISION_FREEZE_1.md`, and `docs/ANZER_V0_1_GRAMMAR_TEST_CHECKLIST.md`.

**Scope:** Existing syntax proposals in `docs/SYNTAX.md`, `docs/SYNTAX_STRESS_TEST.md`, and `specification/VERSION_0.1.md`.

This audit is intentionally critical. A syntax can look readable in an isolated example but become inconsistent or difficult to parse across the language.

## Reconciliation notice

This audit predates the accepted v0.1 decision freeze. Its recommendations and open questions must not be treated as current decisions where the freeze has resolved them. The freeze is authoritative. Image-alt policy remains open.

## Executive verdict

Anzer has a viable design direction: readable commands, semantic defaults, property-based configuration, reusable styles, brace-delimited containers, and one-file authoring. However, the syntax is **not ready to freeze or implement**. Several surface forms currently express the same concepts differently, and the embed/inline-link proposals introduce grammar complexity before the base grammar is stable.

## Keep (strong candidates for grammar freeze)

### A. Explicit document markers
Keep `<anzer start>` and `<anzer end>` for the first draft. They're visually unmistakable. Validate marker placement and reject missing, duplicated, or reversed markers.

### B. Command-oriented element creation
Keep the general `anzer make <element>` direction. Semantic defaults are valuable: title -> H1, paragraph -> P, button -> BUTTON, link -> A, image -> IMG.

### C. Semicolon-terminated leaf declarations
Keep semicolons for leaf declarations and style definitions, pending a precise statement rule. This gives the parser an explicit terminator and makes compact and multiline forms equivalent.

### D. Brace-delimited containers
Keep braces for child content. They're familiar, handle nesting, and do not require indentation to carry meaning. Indentation remains a readability convention, not grammar.

### E. Direct properties and reusable styles
Keep both. Reusable styles are useful for repeated patterns; inline properties are useful for one-offs. Keep precedence: defaults -> style -> direct element properties.

## Revise before freezing

### 1. Style application placement is inconsistent
Current drafts show both:
- `anzer make paragraph use style="paragraph style 1": ...`
- `anzer make paragraph: use style="paragraph style 1", ...`

**Recommendation:** Choose one canonical placement. Prefer style application as an ordinary property after the colon, because the colon already introduces the property list. Do not support multiple placements in v0.1 unless a real need justifies the parser burden.

### 2. Container properties are syntactically unclear
Current experiments put a property colon-list before a brace, e.g.:
`anzer make card: background="white", padding="16px" {`

This risks treating the colon-list as a terminated leaf statement when the parser sees the brace. The grammar must explicitly define a container header that ends with `{`, and properties in that header must not require a semicolon.

**Recommendation:** Make the parser's distinction explicit: a declaration ending in `{` is a block/container; a declaration ending in `;` is a leaf. Do not make both delimiters legal for the same statement.

### 3. Element type is overloaded
`type="H2"` for headings is sensible, but `type` also appears in styles and could become overloaded for unrelated behavior.

**Recommendation:** Restrict `type` to documented semantic variants per element. Invalid combinations should be diagnosed, not guessed.

### 4. Embed commands bypass the main command shape
`anzer embed video="...";` is concise, but it does not follow `anzer make <element>`. It may be okay as a specialized directive, but the language needs a small, deliberate set of top-level directives—not ad hoc command families.

**Recommendation:** Keep embeds experimental for v0.1. Define them as an explicit directive category and decide where they can occur (document root, container, or both). Do not claim universal provider support.

### 5. Inline hyperlink syntax is fragile
The proposal nests quotes and key-value syntax inside a quoted text value. It creates escape rules, tokenization complexity, and makes the paragraph text less readable.

**Recommendation:** Do not freeze this syntax. Test alternatives such as nested link commands or a dedicated inline token grammar. Inline formatting is a feature worth keeping; this particular syntax is not.

### 6. Void elements need a consistent statement rule
Image and input cannot contain children, but examples use property lists and semicolons. This is compatible with the general leaf rule, yet required fields (such as image alt text) and boolean attributes must be specified.

**Recommendation:** Treat void elements as leaf declarations; validate required/accessibility properties. Do not introduce a separate closing syntax unless necessary.

### 7. Text and attribute escaping
Anzer must distinguish ordinary text, property values, and embedded inline syntax. Quote/escape rules are not documented sufficiently.

**Recommendation:** Specify string escapes and text handling before implementing the lexer. If inline markup is included inside strings, its parser must be separate and precisely defined.

## Keep experimental (not part of initial grammar freeze)

- Social post, video, Drop, and rich-preview embeds
- Provider autodetection and provider adapters
- Inline hyperlink tokens
- Visual presets like `3D`, `glow`, `soft`, `raised`
- Action/event declarations beyond one tightly scoped basic interaction
- Responsive layout syntax
- Arbitrary custom properties

These are not rejected as ideas. They're deferred because they expand the grammar, runtime, security, and testing surface before core syntax is reliable.

## Proposed canonical pattern to test next

This is a **candidate pattern only**, not accepted syntax:

```
<anzer start>

anzer make paragraph style 1:
    color="black",
    text-size="16px";

anzer make paragraph:
    use style="paragraph style 1",
    text="A paragraph.";

anzer make card:
    background="white",
    padding="16px" {
    anzer make title: text="Card";
    anzer make paragraph: text="Content";
}

<anzer end>
```

Interpretation rule to test:
- `;` closes a leaf declaration or style definition.
- `{` closes a container header and opens its body.
- `}` closes the current container.
- Properties are introduced only after `:`.
- `use style` is a property, not a modifier in the command name.
- Newlines and indentation do not alter meaning.

## Recommended order before grammar freeze

1. Decide one canonical style-reference placement.
2. Define the declaration terminator rule (semicolon vs opening brace).
3. Specify string quoting and escaping.
4. Specify property names, types, boolean syntax, and duplicate-property behavior.
5. Define container and void-element catalogs and allowed children.
6. Decide semantic diagnostics (warning/error) and source locations.
7. Keep embeds/inline links outside the v0.1 core grammar until a separate test round.
8. Write 10–15 accepted examples and 10 invalid examples from the frozen rules.
9. Only then freeze v0.1 and begin lexer/parser implementation.

## Final assessment

**Do not freeze the grammar yet.** The foundation is sound enough to continue, but current examples contain avoidable inconsistency. Resolve the seven core grammar questions above before implementation. Feature additions should pause until those are resolved.


## Reconciliation note (November 2026)
This document is a historical pre-grammar audit. Several recommendations listed as unresolved were later addressed by newer v0.1 design documents, including canonical property placement, semicolon leaf terminators and brace-delimited containers, strict property/value rules, string escaping, element definitions, and scoped trusted HTML embedding. Use GRAMMAR_RESOLUTION_1.md, accepted string rules, property rules, element catalog, and SEMANTIC_CONSISTENCY_AUDIT_1.md as newer design references. This historical audit is not the current checklist. Its recommendation to defer all HTML embedding is superseded by the scoped HTML escape-hatch decision, which remains security-sensitive.
