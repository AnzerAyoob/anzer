# Style Property Catalog — v0.1

Status: **Proposal — coherent review draft; not frozen**  
Scope: Anzer v0.1 native style declarations

## 1. Purpose and boundary

This catalog defines the native, typed style properties Anzer accepts in v0.1. It is deliberately not a general CSS parser. Each property has a known value grammar, normalized output, and element compatibility rules.

Detailed layout grammar is defined in the accepted Layout Property Catalog (LAYOUT_PROPERTY_CATALOG_PROPOSAL_1.md). This document references that catalog rather than duplicating it.

## 2. Declaration rules

- Property names are lowercase kebab-case; friendly aliases are accepted only when explicitly listed.
- Alias normalization happens before duplicate detection.
- An alias and its canonical property in the same declaration is a duplicate error.
- Duplicate properties in one declaration layer are errors. The same canonical property in a reusable style and direct element declaration is allowed; the direct value wins.
- Values are validated by property type. Unsupported syntax is a compile error, not emitted as raw CSS.
- Strings follow core string rules; arbitrary CSS fragments are not accepted.
- No expressions, calculations, CSS variables, !important, or arbitrary CSS functions in native style declarations in v0.1.
- Properties not listed here or in the accepted layout catalog are errors.

## 3. Property catalog

### Color and background

| Property | Type | CSS output | Allowed values |
|---|---|---|---|
| color | color | color | CSS named colors; hex #RGB, #RGBA, #RRGGBB, #RRGGBBAA |
| background-color | color | background-color | Same color grammar |

RGB/RGBA/HSL functions and arbitrary color strings are excluded from v0.1.

### Typography and text

| Property | Type | CSS output | Allowed values / rules |
|---|---|---|---|
| font-family | string/list | font-family | Quoted family name or quoted fallback list |
| font | alias | font-family | Alias; does not accept CSS font shorthand |
| font-size | length | font-size | Supported length units; nonzero bare numbers resolve to px |
| font-weight | enum/number | font-weight | normal, bold, or 100–900 in increments of 100 |
| text-align | enum | text-align | left, center, right, justify |

Font-family fallback lists are supported. The font alias is only a shortcut for font-family, not the CSS multi-component font shorthand.

### Dimensions and spacing

| Property | Type | CSS output | Allowed values / rules |
|---|---|---|---|
| width | length/keyword | width | Supported units; auto |
| height | length/keyword | height | Supported units; auto |
| min-width | length | min-width | Supported units; nonnegative |
| max-width | length/keyword | max-width | Supported units; none where allowed by validation |
| min-height | length | min-height | Supported units; nonnegative |
| max-height | length/keyword | max-height | Supported units; none where allowed by validation |
| margin | spacing | margin | One to four supported lengths; auto where valid; negative values permitted |
| padding | spacing | padding | One to four supported lengths; nonnegative; auto forbidden |
| border-radius | length | border-radius | Supported units; nonnegative |

Friendly dimension aliases: minimum-width → min-width, maximum-width → max-width, minimum-height → min-height, maximum-height → max-height. Aliases normalize before duplicate checks.

### Borders

| Property | Type | CSS output | Allowed values / rules |
|---|---|---|---|
| border | restricted shorthand | border (expanded internally) | Width, style, and color tokens in any order |
| border-width | length/keyword | border-width | Supported nonnegative lengths or CSS border-width keywords |
| border-style | enum | border-style | none, hidden, dotted, dashed, solid, double, groove, ridge, inset, outset |
| border-color | color | border-color | Named colors and accepted hex forms |

Border shorthand components may be omitted. Omitted components use CSS-compatible defaults: width medium, style none, and color currentcolor. Duplicate shorthand components are errors. The shorthand establishes component values; explicitly supplied border-width, border-style, or border-color overrides the corresponding shorthand component regardless of source order. This precedence is resolved within one declaration layer.

### Layout

Layout properties are restricted to section and container elements. See the accepted Layout Property Catalog for complete grammar and compatibility rules.

- display accepts the values listed in the layout catalog.
- Flex properties require display=flex or inline-flex.
- Grid properties require display=grid or inline-grid.
- gap, row-gap, and column-gap require explicit flex or grid display.
- No layout mode is inferred.

## 4. Length and unit normalization

Supported unit abbreviations and friendly aliases:

| Canonical unit | Accepted examples |
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

Rules:

- Nonzero bare numeric lengths default to px (e.g. width=20 becomes 20px).
- Unitless zero remains 0.
- Unit aliases are case-insensitive and normalized to canonical CSS units.
- Whitespace between a number and unit may be accepted and normalized.
- Units are validated per property. Unsupported unit/property combinations are errors.
- Negative values are property-specific: allowed for margin; rejected for padding, gap, border-width, and border-radius; other properties follow their explicit validation rule.
- auto is property-specific and only accepted where listed.
- Unknown units, malformed values, and unsupported expressions/functions are errors.

## 5. Property applicability

Applicability is validated semantically, after parsing.

| Property family | Applicable elements |
|---|---|
| Color, background, typography, text alignment | title, paragraph, button, link, section, container; image only where explicitly allowed by image rules |
| Dimensions, margin, padding, border, border-radius | Elements according to the element-specific allowlist; image supports width, height, margin, border, border-radius, and display only |
| Layout properties | section, container only |

The final element/property compatibility matrix must be reconciled with the element catalog before this proposal is frozen. Unknown properties and incompatible properties are compile errors.

## 6. Reusable styles and precedence

- An element may reference one reusable style in v0.1.
- Reusable styles do not inherit from or reference other reusable styles.
- Resolution order: element defaults → reusable style → direct element properties.
- Direct element properties override reusable-style properties.
- Duplicate properties within one declaration layer are errors.
- Alias normalization happens before duplicate detection and resolution.
- Border shorthand is expanded to components before component overrides are applied.

## 7. Compiler-generated baseline CSS (pending decision)

Recommended baseline:

```css
*, *::before, *::after { box-sizing: border-box; }
body { margin: 0; }
img { max-width: 100%; height: auto; }
```

Rationale: consistent sizing, a clean page canvas, and images that do not overflow narrow screens. This baseline is NOT accepted yet. It changes browser behavior globally, so the user must explicitly approve it before implementation. Do not inject global font, color, heading spacing, paragraph spacing, link appearance, or button styling in v0.1.

## 8. Security and output

- Native properties map only to catalogued CSS properties.
- Validate values before generating output.
- CSS output must serialize values safely; never concatenate untrusted text into raw CSS.
- Embedded HTML is a separate trusted escape hatch and is not governed by this catalog. It can affect page content, styles, and scripts and must be clearly documented as trusted input.

## 9. Review checklist before freezing

- [ ] Reconcile element/property applicability against the element catalog.
- [ ] Confirm exact keyword grammar for max-width and max-height (including none).
- [ ] Confirm border-width keyword acceptance and interaction with numeric units.
- [ ] Verify border shorthand parsing, omitted-token defaults, and source-order-independent component overrides.
- [ ] Verify font-family list parsing and font alias semantics.
- [ ] Review baseline CSS and explicitly accept or reject it.
- [ ] Cross-check all style stress tests (S1–S50) against this document.
- [ ] Create an executable validator/compiler test suite before implementation claims.

## 10. Status

This rewrite removes contradictory earlier wording. Accepted v0.1 decisions are documented as rules; unresolved items remain explicitly open. The catalog is still a review draft and is not frozen.
