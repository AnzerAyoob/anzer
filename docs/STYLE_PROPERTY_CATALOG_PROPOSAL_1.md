# Style Property Catalog Proposal 1

Status: **Proposal — awaiting review**  
Scope: Anzer v0.1

## Goal

Provide a small, typed styling vocabulary that maps predictably to CSS. Anzer should not expose arbitrary CSS property/value pairs in its native styling syntax in v0.1.

## Proposed style properties

| Anzer property | Value type | CSS output | Proposed allowed values / notes |
|---|---|---|---|
| color | color | color | Named colors, hex, rgb/rgba syntax deferred; proposal: named colors and hex only initially |
| background-color | color | background-color | Same color rules as color |
| font-family | string | font-family | Quoted family name; fallback lists deferred |
| font-size | length | font-size | px, rem, em; numeric values without units rejected |
| font-weight | enum or number | font-weight | normal, bold, 100–900 (step 100) |
| text-align | enum | text-align | left, center, right, justify |
| width | length or percent | width | px, %, rem, em; auto allowed |
| height | length or percent | height | px, %, rem, em; auto allowed |
| margin | spacing | margin | px, %, rem, em; auto allowed; shorthand supported |
| padding | spacing | padding | px, %, rem, em; shorthand supported |
| border | restricted string | border | Proposal: width + style + color; avoid arbitrary CSS parsing if possible |
| border-radius | length | border-radius | px, %, rem, em |
| display | enum | display | block, inline, inline-block, flex, grid, none |
| gap | length | gap | px, rem, em; used for flex/grid containers |

## Value rules

- Style properties use the accepted property syntax and value typing rules.
- CSS-like values are not automatically treated as strings; property validation determines the allowed type.
- Units are mandatory for length values except documented keywords (such as auto for width/height/margin).
- Negative values are permitted only for properties where the semantic validator allows them (proposal: margin only; not padding, border radius, or gap).
- Color values are validated; unsupported formats should be errors, not silently emitted.
- No expressions, calculations, CSS variables, !important, or arbitrary functions in v0.1.
- No direct shorthand expansion beyond explicitly supported properties.

## Layout and property applicability

Properties may be accepted on elements only when semantically applicable. Proposal:

- Text properties: title, paragraph, button, link, section, container.
- Box properties: all catalog elements, subject to element-specific restrictions; image may accept width, height, margin, border, border-radius, and display only.
- Layout properties (display, gap): section and container only.
- Unknown property or property used on an incompatible element is a semantic error.

## Reusable styles

Reusable styles continue to use the existing style declaration mechanism and numbered names. Style declarations may contain style properties, and elements may use them through the accepted style reference syntax. Precedence remains: element defaults → reusable style → direct element properties. Duplicate property names in the same declaration are errors. Direct element properties override style values.

## Proposed default values

Anzer should avoid surprising styling defaults. Proposal: compiler-generated output includes only the minimum reset/base styles required for predictable layout and accessibility. Element styling defaults should remain browser-compatible unless a later design specifies otherwise. This decision needs an explicit baseline CSS document.

## Security and output

- Property names map only through the known catalog; no arbitrary CSS property injection.
- Values are validated by type and range before CSS generation.
- Strings must be escaped for CSS output.
- Embedded HTML is a separate trusted escape hatch and is not governed by this native property catalog.

## Open decisions

1. Confirm initial property list and whether border should be decomposed into border-width, border-style, and border-color instead of one combined property.
2. Decide accepted color syntax (named colors and hex recommended; RGB(A) deferred).
3. Decide whether font-family accepts one name or a fallback list.
4. Finalize length units and whether unitless zero is permitted.
5. Decide whether width/height support auto and whether min/max dimensions are needed in v0.1.
6. Decide baseline/reset CSS behavior.
7. Create stress tests for valid and invalid property/value combinations.

## Recommendation

Keep native style properties typed, limited, and element-aware. Avoid accepting arbitrary CSS strings in v0.1. Expand the catalog later based on actual authoring needs and tests.
