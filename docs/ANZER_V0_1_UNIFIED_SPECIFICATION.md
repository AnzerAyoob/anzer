# Anzer v0.1 — Unified Specification

**Status:** Implementation-facing consolidation of accepted v0.1 decisions  
**Authority:** This document consolidates the v0.1 decision freeze and reconciled catalogs. Where older proposals conflict, this document and `ANZER_V0_1_DECISION_FREEZE_1.md` take precedence.  
**Scope:** Source syntax, lexical rules, semantics, native elements, properties, layout, interactions, security, diagnostics, and output requirements.  
**Not status:** This is not a compiler implementation and its test cases have not been executed by a compiler.

## 1. Language goals

Anzer is a simple, human-readable command-style authoring language. Authors should not need to memorize rigid technical spellings where a clearly equivalent friendly form can be accepted.

Strictness is for correctness, compatibility, and security—not arbitrary spelling enforcement. Anzer v0.1 is not a general HTML, CSS, JavaScript, or programming language.

## 2. Document structure

A complete source document uses one opening and one closing marker:

```anzer
<anzer start>

anzer make title: text="Hello";

<anzer end>
```

Rules:
- Exactly one `<anzer start>` and one `<anzer end>` are required.
- They must occur in the correct order and enclose the source document.
- Missing, duplicated, reversed, or misplaced markers are errors.
- Marker-like text inside a valid quoted string is ordinary string content.

## 3. Source encoding and whitespace

- Source must be UTF-8. Invalid UTF-8 is an error.
- Unicode content is preserved.
- Newlines and indentation are formatting; they do not determine nesting.
- Whitespace may separate tokens and around property names, equals signs, and values.
- Missing commas between properties are errors. The compiler must not guess property boundaries.
- Compact and multiline forms must parse to equivalent syntax trees when token order and separators are equivalent.

## 4. Lexical strings

Double quotes are the only string delimiter. Single quotes, raw/triple strings, interpolation, and physical multiline strings are excluded.

Supported escapes:

| Escape | Result |
|---|---|
| `\\"` | double quote |
| `\\\\` | backslash |
| `\\n` | line feed |
| `\\r` | carriage return |
| `\\t` | tab |

Decode escapes exactly once. Unknown or incomplete escapes, unterminated strings, and raw newlines within a quoted string are lexical errors.

Punctuation inside a string—including comma, semicolon, braces, colon, angle brackets, and document-marker text—is content, not syntax.

## 5. Statement grammar and structural parsing

Core forms:

```anzer
anzer make <element>: <properties>;
anzer make <container> { <children> }
anzer make <container>: <properties> { <children> }
anzer make <element style name>: <properties>;
anzer use html="<trusted raw html>";
```

Structural rules:
- A semicolon terminates a leaf element or reusable-style declaration.
- An opening brace `{` begins a container body.
- A closing brace `}` closes the most recently opened container.
- Containers may nest and may be empty.
- Syntax, not the element name or indentation, determines block shape.
- Semantic validation rejects an element used with an incompatible shape (for example, image with a block).
- Unmatched closing braces and unclosed containers are errors.
- The parser must not silently reinterpret a leaf as a container.

Properties follow the colon. Style application is written in the property list as `use style="..."`; alternate placement is not supported.

## 6. Property declaration syntax

- Properties use `name=value`.
- Commas separate entries.
- Property order is unrestricted.
- Semicolon ends leaf/style declarations; container headers end with `{`.
- Strings use double quotes. Numeric values are integer or decimal, optionally negative; exponent notation is not supported.
- Booleans are unquoted lowercase `true` or `false`. Quoted boolean text is a string.
- Null, arrays, objects, and expression values are not supported.
- Empty strings are valid when the property permits strings. Missing values are errors.
- Duplicate canonical properties within the same declaration layer are errors.

### 6.1 Property name normalization

Normalize property names before lookup and duplicate detection:
1. Property names must be lowercase in v0.1. Uppercase and underscore forms are rejected.
2. Runs of spaces and hyphens are treated as a single separator. Thus `font-style`, `font style`, and `font   style` resolve to the same canonical name.
3. Explicit expanded aliases normalize using the alias table below.
4. Duplicate detection occurs on the canonical property name after normalization.

Accepted aliases:
| Accepted name | Canonical property |
|---|---|
| `font` | `font-family` |
| `text-size` | `font-size` |
| `minimum width` | `min-width` |
| `maximum width` | `max-width` |
| `minimum height` | `min-height` |
| `maximum height` | `max-height` |

Separator normalization also accepts hyphen forms of expanded names, e.g. `minimum-width`. Arbitrary synonyms are not accepted unless explicitly catalogued. The special property phrase `use style` is recognized as style application.

Examples of duplicate errors:
- `font="Arial", font-family="Roboto"`
- `font-style="italic", font style="normal"`
- `minimum width=300, min-width=200`

## 7. Elements

### 7.1 Built-in element catalog

| Anzer element | Default HTML | Kind | Required properties |
|---|---|---|---|
| title | h1 | leaf | text |
| paragraph | p | leaf | text |
| button | button | leaf | text |
| link | a | leaf | text, url |
| image | img | void leaf | src |
| section | section | container | none |
| container | div | container | none |

Leaf elements cannot contain child Anzer elements. Containers may contain direct text and nested elements. Image is a void leaf.

### 7.2 Element properties

- `title`: required text; optional type, style reference, and compatible style properties.
- `paragraph`: required text; optional type, style reference, and compatible style properties.
- `button`: required text; optional action, target, style reference, and compatible style properties.
- `link`: required text and url; optional style reference and compatible style properties.
- `image`: required src; optional alt, style reference, and image-compatible style properties.
- `section`: optional id, text, style reference, and compatible style properties; nested elements allowed.
- `container`: optional id, text, style reference, and compatible style properties; nested elements allowed.

Element text is plain text and must be HTML-escaped. It is never interpreted as HTML. A container's direct text renders before its child Anzer elements. HTML embedding is inserted at its source position.

### 7.3 Type overrides

Type overrides alter only the emitted HTML tag. They do not change Anzer element kind, required fields, property compatibility, child capability, or action semantics.

| Anzer element | Allowed type |
|---|---|
| title | H1, H2, H3, H4, H5, H6 |
| paragraph | P, SPAN, DIV |
| section | SECTION, DIV |
| container | DIV, SECTION |
| button, link, image | no override |

Input tag values are case-insensitive and normalized; output tags are lowercase. No arbitrary tag names or custom elements.

### 7.4 Image alt fallback

Alt is optional. If omitted, derive fallback from filename: remove extension, replace hyphens/underscores with spaces, and normalize into readable text. This is a fallback only; it may be inaccurate or inaccessible. The policy remains a known open issue, not a compiler claim of accessibility compliance.

## 8. Native style property catalog

The native style system is restricted and typed. Unknown properties, invalid values, and unsupported syntax are errors. No arbitrary CSS fragments, expressions, CSS variables, `!important`, or functions in native style properties.

### 8.1 Colors

- `color`, `background-color`
- CSS named colors or hex: `#RGB`, `#RGBA`, `#RRGGBB`, `#RRGGBBAA`
- RGB, RGBA, HSL functions and arbitrary color strings are excluded.

### 8.2 Typography

| Property | Accepted values |
|---|---|
| font-family | Quoted family name or quoted fallback list |
| font-weight | normal, bold, or 100–900 in steps of 100 |
| text-align | left, center, right, justify |

`font` is an alias for `font-family`, not CSS font shorthand. `font-size` accepts supported lengths; bare nonzero numbers become px.

### 8.3 Dimensions and spacing

| Property | Rules |
|---|---|
| width, height | Supported lengths or auto |
| min-width, min-height | Supported nonnegative lengths only |
| max-width, max-height | Supported nonnegative lengths or none |
| margin | 1–4 supported lengths; auto where valid; negative values permitted |
| padding | 1–4 supported lengths; nonnegative; auto forbidden |
| border-radius | supported nonnegative length |

### 8.4 Length units

| Canonical unit | Accepted aliases |
|---|---|
| px | px, pixel, pixels |
| % | %, percent, percentage |
| em | em |
| rem | rem |
| vw | vw, viewport width |
| vh | vh, viewport height |
| vmin | vmin, viewport minimum |
| vmax | vmax, viewport maximum |
| ch | ch |
| ex | ex |
| cm | cm, centimetre(s), centimeter(s) |
| mm | mm, millimetre(s), millimeter(s) |
| in | in, inch(es) |
| pt | pt, point(s) |
| pc | pc, pica(s) |

- Unit aliases are case-insensitive.
- Whitespace between number and unit may be accepted.
- Nonzero bare numeric lengths resolve to px. Unitless zero remains 0.
- Unit validity is property-specific.
- Negative values are permitted only where catalogued (not for padding, gap, border-width, border-radius, min/max dimensions).
- Unsupported units, malformed values, and expressions are errors.

### 8.5 Borders

- `border` accepts width, style, and color tokens in any order.
- Border-width accepts supported nonnegative lengths or `thin`, `medium`, `thick`.
- Border-style: `none`, `hidden`, `dotted`, `dashed`, `solid`, `double`, `groove`, `ridge`, `inset`, `outset`.
- Border-color accepts named colors and accepted hex forms (including `currentcolor`).
- Duplicate shorthand components are errors.
- Omitted shorthand components use CSS-compatible defaults: width `medium`, style `none`, color `currentcolor`.
- Shorthand components are expanded. Explicit border-width/style/color properties override shorthand components regardless of source order in the same declaration layer.

### 8.6 Property applicability

Use the accepted Element / Property Compatibility Review allowlist. Summary:
- Text properties: title, paragraph, button, link, section, container; image excluded.
- width/height: all built-in elements.
- min/max dimensions: all built-in elements except image.
- margin: all built-in elements.
- padding: all built-in elements except image.
- border properties and border-radius: all built-in elements.
- display and layout properties: section/container only.
- image supports only width, height, margin, border (shorthand and components), and border-radius.

If a property is incompatible with an element, compilation errors. Type override does not widen the allowlist.

## 9. Reusable styles

- One reusable style reference per element in v0.1.
- Styles are element-kind scoped; a style declared for paragraph may only be applied to paragraph.
- Styles cannot reference or inherit from other styles.
- Validate properties against the style's element kind at declaration and use.
- Precedence: element defaults → reusable style values → direct element properties.
- Direct properties override style values.
- Duplicates within one declaration layer are errors; the same canonical property across style and direct declaration is an intentional override.
- Normalize aliases before style resolution.
- Border shorthand is expanded before component overrides.

## 10. Layout properties

Layout is allowed only on section and container and requires an explicit compatible display value. Anzer never infers flex/grid.

### 10.1 Display

Allowed: block, inline, inline-block, flex, inline-flex, grid, inline-grid, none. Table display excluded.

### 10.2 Flex

Flex properties require display flex or inline-flex.

| Property | Values |
|---|---|
| flex-direction | row, row-reverse, column, column-reverse |
| flex-wrap | nowrap, wrap, wrap-reverse |
| justify-content | start, end, center, space-between, space-around, space-evenly |
| align-items | start, end, center, stretch, baseline |
| align-content | start, end, center, stretch, space-between, space-around, space-evenly |

start/end normalize to flex-start/flex-end where applicable.

### 10.3 Grid

Grid properties require display grid or inline-grid.

Properties: grid-template-columns, grid-template-rows, grid-auto-flow, grid-auto-columns, grid-auto-rows, justify-items, align-items, justify-content, align-content.

Track tokens (space-separated): auto, supported lengths, percentages, positive numeric fr values, min-content, max-content. Bare nonzero numbers normalize to px. `0fr` is invalid.

Unsupported: repeat(), minmax(), fit-content(), named lines, grid-template-areas, nested functions, expressions.

### 10.4 Gap

gap, row-gap, column-gap require explicit flex or grid display. Gap accepts one or two whitespace-separated lengths; two values mean row-gap then column-gap. Commas and expressions are rejected. Each length uses ordinary unit normalization.

### 10.5 Alignment

Values are property-specific. Shared tokens include start, end, center, stretch, baseline (where permitted), space-between, space-around, space-evenly. baseline is not valid for justify-content.

Unknown values and incompatible layout properties are errors. Browser defaults remain when properties are omitted; Anzer does not secretly add direction, wrapping, alignment, or tracks.

## 11. Button behavior

Buttons default to type=button (not form submit). v0.1 action is limited to toggle.

- `action="toggle"` requires `target`.
- Target must resolve to a unique id on section/container.
- Missing/duplicate ids, unresolved targets, wrong target kinds, or unsupported action values are semantic errors.
- Toggle uses a hidden-state mechanism that preserves the authored display style; it must not overwrite display with arbitrary values.
- Targets are visible initially unless otherwise specified by the accepted hidden-state semantics.
- State and accessibility attributes (including aria-expanded) synchronize with target visibility.
- Multiple buttons may target the same container and must reflect current target state.
- No user JavaScript, event handlers, alerts, multi-actions, or other arbitrary behavior.

## 12. URL safety

- Link URLs: relative, http, https, mailto.
- Image src: relative, http, https.
- Reject javascript:, data:, unsupported schemes, and protocol-relative URLs.
- Validate URLs and escape output in the proper HTML attribute context.
- Do not treat URL text as trusted HTML.

## 13. HTML embedding

Syntax: `anzer use html="...";`

- Allowed only inside section/container blocks.
- Insert at the exact source position.
- Cannot be used at document root or replace the compiler page shell.
- Embedded content is not parsed as Anzer syntax.
- It is raw trusted author HTML, not sanitized or sandboxed; it may execute scripts, event handlers, inject styles, and affect the wider page.
- Tooling must visibly warn and require trust acknowledgement. If a tool cannot provide this, it must defer/disable HTML embedding.
- Dedicated JS embedding is excluded.

## 14. Baseline CSS

Compiler output includes:

```css
*, *::before, *::after { box-sizing: border-box; }
body { margin: 0; }
img { max-width: 100%; height: auto; }
```

Do not globally impose fonts, colors, heading/paragraph spacing, link appearance, or button styles.

## 15. Diagnostics and compilation safety

Diagnostics distinguish:
- lexical errors (malformed tokens, strings, escapes, encoding)
- syntax errors (invalid statement/property structure, braces, delimiters)
- semantic errors (unknown element, wrong shape, missing required properties, invalid style/action/type use, IDs/targets)
- validation errors (property types/values, URL safety, compatibility, unsupported syntax)

Each diagnostic includes source line and column where possible and severity. Parser recovery may continue when safe for further diagnostics, but compilation must not emit final output while errors remain. No unsafe partial output is emitted. Warnings may be emitted for nonfatal conditions such as empty containers or questionable alt fallback, without being treated as errors unless specified.

## 16. Compiler output requirements

The v0.1 compiler should:
1. Parse source into a syntax tree without using indentation to infer structure.
2. Validate document markers, statements, element semantics, property aliases/types, style references, compatibility, URLs, and actions.
3. Normalize properties and aliases deterministically.
4. Resolve reusable styles with defined precedence.
5. Generate HTML with context-appropriate escaping for native content/attributes.
6. Generate CSS only from validated native properties.
7. Generate limited runtime behavior only for toggle actions.
8. Preserve trusted HTML embeds only after visible trust acknowledgement.
9. Refuse final output when errors exist.
10. Produce deterministic output for equivalent source.

This specification does not prescribe compiler architecture, CLI, packaging, source maps, or editor UX.

## 17. Explicitly out of scope for v0.1

- Arbitrary HTML element authoring as native Anzer elements.
- Arbitrary CSS or CSS functions/expressions.
- JavaScript embedding, arbitrary handlers, scripts authored through Anzer actions.
- String interpolation.
- Single-quoted, raw, triple-quoted, or physical multiline strings.
- Arrays, objects, null, expressions.
- Table display.
- Grid functions (repeat/minmax/fit-content), named lines, areas.
- Multiple reusable style references, style inheritance, style-to-style references.
- Arbitrary tag overrides or custom elements.
- Native card element.
- Additional actions beyond toggle.

## 18. Final implementation decisions

- Image alt fallback: derive from filename when omitted (remove extension; replace hyphens and underscores with spaces).
- Source input: `.anzer`.
- Compiler language: Python for v0.1.
- Primary compilation product: Anzer-native, versioned intermediate representation (internal normalized document model), not HTML.
- Default compile output: replace source extension with `.html`.
- CLI: `anzer compile <input.anzer> [-o <output.html>]`, `anzer check <input.anzer>`, and runtime-facing `anzer render <input.anzer>` (viewer behavior specified separately).
- HTML is the v0.1 output. Anzer's long-term goal requires runtime/browser support to replace HTML.
- Failed compilation must not create or overwrite output.

The language specification remains unchanged by these product/architecture decisions.

## 19. Supporting documents

- `ANZER_V0_1_DECISION_FREEZE_1.md` — accepted decisions record
- `ELEMENT_CATALOG_PROPOSAL_1.md` — element details
- `ELEMENT_PROPERTY_COMPATIBILITY_REVIEW_1.md` — property allowlist
- `STYLE_PROPERTY_CATALOG_PROPOSAL_1.md` — native style property details
- `LAYOUT_PROPERTY_CATALOG_PROPOSAL_1.md` — layout details
- `STRING_RULES_PROPOSAL_1.md` — string lexical rules
- `CORE_GRAMMAR_STRESS_TEST_1.md`, `PROPERTY_STRESS_TEST_1.md`, `STYLE_PROPERTY_STRESS_TEST_1.md`, `LAYOUT_PROPERTY_STRESS_TEST_1.md` — specification suites (not runtime tests)

---
Consolidated for Anzer v0.1. The decision freeze remains authoritative; implementation and executable validation are pending.
