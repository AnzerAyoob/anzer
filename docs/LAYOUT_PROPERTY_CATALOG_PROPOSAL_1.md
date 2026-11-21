# Layout Property Catalog Proposal 1

Status: **Proposal — awaiting review**
Scope: Anzer v0.1

## Goal

Provide beginner-friendly simple layout options and an advanced but restricted layout vocabulary. Anzer should make common layouts easy without becoming a general CSS parser.

## 1. Display values

Proposed allowed values for `display`:

- `block`
- `inline`
- `inline-block`
- `flex`
- `inline-flex`
- `grid`
- `inline-grid`
- `none`

Do not include table display modes in v0.1. Native table elements or a later catalog can handle tabular layout without encouraging div-based table construction.

## 2. Simple layout

Authors can use only `display` and `gap` for basic layouts:

```anzer
anzer make container:
    display="flex",
    gap=16;
```

Flex defaults are CSS defaults unless explicitly set. Anzer should not secretly add direction, alignment, or wrapping.

## 3. Flex properties

Proposed properties and restricted values:

| Property | Allowed values |
|---|---|
| `flex-direction` | `row`, `row-reverse`, `column`, `column-reverse` |
| `flex-wrap` | `nowrap`, `wrap`, `wrap-reverse` |
| `justify-content` | `start`, `end`, `center`, `space-between`, `space-around`, `space-evenly` |
| `align-items` | `start`, `end`, `center`, `stretch`, `baseline` |
| `align-content` | `start`, `end`, `center`, `stretch`, `space-between`, `space-around`, `space-evenly` |
| `gap` | Supported length value or two length values for row/column gap |
| `row-gap` | Supported length value |
| `column-gap` | Supported length value |

Friendly values such as `start` and `end` normalize to CSS `flex-start` and `flex-end` where required. Avoid aliases where they create ambiguity.

## 4. Grid properties

Grid is supported, but v0.1 should use a constrained track grammar.

Proposed properties:

- `grid-template-columns`
- `grid-template-rows`
- `grid-auto-flow`
- `grid-auto-columns`
- `grid-auto-rows`
- `justify-items`
- `align-items`
- `justify-content`
- `align-content`
- `gap`
- `row-gap`
- `column-gap`

### Grid track values (proposal)

Allow a whitespace-separated list of:

- `auto`
- `px` length
- `%` length
- `fr` positive number
- `min-content`
- `max-content`

Do not allow arbitrary functions or nested CSS expressions. To avoid complex parsing, `repeat()`, `minmax()`, `fit-content()`, named lines, and grid-template-area syntax are deferred initially.

Example:

```anzer
anzer make container:
    display="grid",
    grid-template-columns="1fr 2fr",
    gap=12;
```

This is valid and should compile to equivalent CSS.

## 5. Grid and flex alignment values

Proposed allowed values:

- `start`
- `end`
- `center`
- `stretch`
- `baseline` (only where applicable)
- `space-between`
- `space-around`
- `space-evenly`

Validation is property-specific. For example, `baseline` is not accepted for `justify-content` in this catalog.

## 6. Compatibility rules

- Flex properties require `display=flex` or `display=inline-flex`.
- Grid properties require `display=grid` or `display=inline-grid`.
- `gap`, `row-gap`, and `column-gap` require flex or grid display.
- A layout property used with a non-compatible display value is an error.
- Layout properties used without an explicit compatible `display` are errors; Anzer does not infer the display mode.
- Layout properties are permitted only on `section` and `container` elements in v0.1.
- Unknown values and unsupported grammar are compile errors.

## 7. CSS defaults

Anzer does not override flex/grid defaults. If a property is omitted, the browser's CSS default applies. For example, a flex container defaults to row direction unless the author sets `flex-direction`.

## 8. Open decisions

1. Confirm display values.
2. Confirm flex property list and friendly alignment values.
3. Confirm whether `gap` accepts one value or two values (proposal: both).
4. Confirm grid track grammar and whether `fr` is allowed in v0.1.
5. Confirm that `repeat()`, `minmax()`, named grid lines, and grid-template-areas are deferred.
6. Confirm compatibility errors and requirement for explicit display.
7. Create a layout stress test before freezing this catalog.

## Recommendation

Support basic flex and grid now with a restricted grammar. Defer complex grid functions and named layouts until a stress test demonstrates that they can be parsed and validated simply and reliably.
