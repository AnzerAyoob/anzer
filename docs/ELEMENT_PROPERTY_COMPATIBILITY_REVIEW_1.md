# Element / Property Compatibility Review — v0.1

Status: **Review result — proposed resolution, pending user acceptance**  
Scope: v0.1 element semantics and native style compatibility

## 1. Why this review exists

The element catalog and style catalog previously described compatibility in broad terms, leaving contradictions and omissions. This review proposes a concrete allowlist so the compiler can reject incompatible properties deterministically rather than silently emitting questionable CSS. This is a specification exercise, not implementation or runtime testing.

## 2. v0.1 elements

| Anzer element | HTML default | Kind | Content |
|---|---|---|---|
| title | h1 | leaf | required plain text |
| paragraph | p | leaf | required plain text |
| button | button | leaf | required plain text; limited action optional |
| link | a | leaf | required plain text and URL |
| image | img | void leaf | required src; optional alt |
| section | section | container | optional direct text and children |
| container | div | container | optional direct text and children |

Type override rules remain those in the Element Catalog. Type override changes the HTML tag only; it does not change Anzer element semantics or expand the property's allowlist.

## 3. Property groups

**Text properties:** color, font-family (font alias), font-size, font-weight, text-align.

**Box properties:** width, height, min-width, max-width, min-height, max-height, margin, padding, border, border-width, border-style, border-color, border-radius.

**Layout properties:** display, flex-direction, flex-wrap, justify-content, align-items, align-content, grid-template-columns, grid-template-rows, grid-auto-flow, grid-auto-columns, grid-auto-rows, justify-items, gap, row-gap, column-gap. Layout values and display compatibility are governed by the accepted Layout Property Catalog.

## 4. Proposed allowlist matrix

Legend: **Y** = allowed; **—** = rejected in v0.1.

| Property/group | title | paragraph | button | link | image | section | container |
|---|---:|---:|---:|---:|---:|---:|---:|
| Text properties | Y | Y | Y | Y | Y | Y |
| width / height | Y | Y | Y | Y | Y | Y |
| min/max dimensions | Y | Y | Y | Y | Y | Y |
| margin | Y | Y | Y | Y | Y | Y |
| padding | Y | Y | Y | Y | Y | Y |
| border properties | Y | Y | Y | Y | Y | Y |
| border-radius | Y | Y | Y | Y | Y | Y |
| display | — | — | — | — | — | Y |
| Flex properties | — | — | — | — | Y* | Y* |
| Grid properties | — | — | — | — | Y* | Y* |

*Layout properties apply only when an explicit compatible display value is present. Flex properties require flex/inline-flex; grid properties require grid/inline-grid; gap-family properties require either. Section/container must explicitly declare display. No layout mode is inferred.

### Image special rule

Image accepts only width, height, margin, border, border-width, border-style, border-color, and border-radius. Image does not accept text properties, padding, min/max dimensions, or layout properties in v0.1. The earlier style catalog statement that image could accept display is withdrawn because display is defined as a layout property and the accepted layout catalog limits layout properties to section/container.

## 5. Semantics and validation notes

1. HTML type override does not widen the allowlist. A paragraph rendered as span or div remains an Anzer paragraph for property compatibility and content rules.
2. Leaf/container rules are syntax and semantic rules, not CSS rules. Leaf elements cannot contain child Anzer elements. Containers can.
3. Native property validation is strict. Unknown properties and disallowed properties on an element are compile errors.
4. Reusable-style compatibility is checked at use-site. When a style is applied, every property must be allowed on that element; incompatible properties cause an error rather than being silently ignored.
5. Direct properties and reusable styles are validated after normalization. Alias duplicates are errors within one layer. Direct properties override reusable-style values only for properties valid on the element.
6. Border shorthand is normalized to components. The same allowlist applies to border components as to the shorthand. Explicit individual components override shorthand components within the same declaration layer.
7. Image alt is content metadata, not a style property. Filename-derived fallback remains a weak fallback, not a substitute for accurate alt text.

## 6. Compatibility examples

**Valid styled paragraph:** text, color, font-size, and margin.

**Valid layout container:** display=flex, flex-direction=column, and gap.

**Invalid layout property on paragraph:** display=flex; layout is restricted to section/container.

**Invalid text property on image:** color=red; image is a void media element and does not accept text properties.

**Invalid layout property on image:** display=inline; image layout properties are excluded in v0.1.

## 7. Open items

- This allowlist is a proposed resolution and requires user acceptance.
- Reusable-style declarations are recommended to remain context-neutral syntactically, with property compatibility validated at every use site.
- Global baseline CSS remains pending approval in the style catalog.
- URL safety, toggle accessibility, and container direct-text ordering remain open in the element catalog.
- No compiler tests have run; examples are specification examples only.

## 8. Recommendation

Adopt this explicit matrix for v0.1. It is intentionally restrictive and predictable. Revisit individual properties only when concrete authoring needs justify expanding the allowlist.
