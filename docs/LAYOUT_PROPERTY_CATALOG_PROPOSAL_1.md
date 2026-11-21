# Layout Property Catalog Proposal 1

Status: **Accepted for Anzer v0.1**
Scope: Anzer v0.1

## Goal

Provide beginner-friendly simple layout options and an advanced but restricted layout vocabulary. Anzer should make common layouts easy without becoming a general CSS parser.

## 1. Display values

Allowed values for `display`:

- `block`
- `inline`
- `inline-block`
- `flex`
- `inline-flex`
- `grid`
- `inline-grid`
- `none`

Table display modes are excluded from v0.1.

## 2. Simple layout

Authors can use `display` and `gap` for basic layouts:

```anzer
anzer make container:
    display="flex",
    gap=16;
```

Flex defaults are CSS defaults unless explicitly set. Anzer does not secretly add direction, alignment, or wrapping.

## 3. Flex properties

| Property | Allowed values |
|---|---|
| `flex-direction` | `row`, `row-reverse`, `column`, `column-reverse` |
| `flex-wrap` | `nowrap`, `wrap`, `wrap-reverse` |
| `justify-content` | `start`, `end`, `center`, `space-between`, `space-around`, `space-evenly` |
| `align-items` | `start`, `end`, `center`, `stretch`, `baseline` |
| `align-content` | `start`, `end`, `center`, `stretch`, `space-between`, `space-around`, `space-evenly` |
| `gap` | One length or two length values |
| `row-gap` | One supported length |
| `column-gap` | One supported length |

Friendly `start` and `end` normalize to `flex-start` and `flex-end` where appropriate.

## 4. Grid properties

Supported properties:

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

### Grid track grammar

Allow whitespace-separated tracks:

- `auto`
- supported length units
- `%` length
- `fr` with a positive number
- `min-content`
- `max-content`

No arbitrary functions or nested CSS expressions. `repeat()`, `minmax()`, `fit-content()`, named lines, and grid-template-area syntax are excluded from v0.1.

Example:

```anzer
anzer make container:
    display="grid",
    grid-template-columns="1fr 2fr",
    gap=12;
```

## 5. Alignment values

Allowed alignment values are property-specific, drawn from:

- `start`
- `end`
- `center`
- `stretch`
- `baseline` (only where applicable)
- `space-between`
- `space-around`
- `space-evenly`

For example, `baseline` is not allowed for `justify-content` in this catalog.

## 6. Compatibility rules

- Flex properties require `display=flex` or `display=inline-flex`.
- Grid properties require `display=grid` or `display=inline-grid`.
- `gap`, `row-gap`, and `column-gap` require flex or grid display.
- Layout properties used with incompatible display values are errors.
- Layout properties require an explicit compatible `display`; Anzer does not infer layout modes.
- Layout properties are allowed only on `section` and `container` elements in v0.1.
- Unknown values and unsupported grammar are compile errors.

## 7. CSS defaults

Anzer does not override flex/grid defaults. If a property is omitted, the browser's CSS default applies.

## 8. Accepted decisions

All catalog decisions above are accepted for v0.1. A stress test must be completed before implementation to verify the parser grammar and validation behavior.

