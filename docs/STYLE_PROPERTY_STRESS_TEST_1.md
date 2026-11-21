# Style Property Stress Test 1

Status: **Specification stress suite; compiler execution pending**
Scope: Accepted Anzer v0.1 style and unit decisions
Purpose: Verify property parsing, value validation, normalization, aliases, shorthand expansion, and conflict resolution before compiler implementation.

## Valid cases

### S1 — Bare numeric lengths default to pixels
```anzer
anzer make container:
    width=300,
    height=200,
    padding=20;
```
Expected: `300px`, `200px`, `20px`.

### S2 — Unitless zero
```anzer
anzer make container:
    margin=0,
    padding=0;
```
Expected: unitless `0`.

### S3 — CSS unit abbreviations
```anzer
anzer make container:
    width="80%",
    padding="2rem",
    margin="10px";
```
Expected: valid.

### S4 — Friendly full unit names
```anzer
anzer make container:
    width="80 percent",
    padding="20 pixels",
    margin="2 centimetres";
```
Expected: normalized to `80%`, `20px`, `2cm`.

### S5 — Case-insensitive unit aliases
```anzer
anzer make container:
    padding="12 PIXELS";
```
Expected: valid; normalized to `12px`.

### S6 — Negative margin
```anzer
anzer make container:
    margin="-10px";
```
Expected: valid.

### S7 — Auto dimensions
```anzer
anzer make container:
    width="auto",
    height="auto";
```
Expected: valid.

### S8 — Named color
```anzer
anzer make paragraph:
    color="darkblue";
```
Expected: valid.

### S9 — Hex color formats
```anzer
anzer make paragraph:
    color="#abc",
    background-color="#abcd";
```
Expected: valid.

### S10 — Full hex color and alpha
```anzer
anzer make section:
    background-color="#12345678";
```
Expected: valid.

### S11 — Font family fallback list
```anzer
anzer make paragraph:
    font-family="Arial, Helvetica, sans-serif";
```
Expected: valid; output is properly CSS-escaped.

### S12 — Font alias
```anzer
anzer make paragraph:
    font="Arial";
```
Expected: valid; normalized to `font-family`.

### S13 — Font weight
```anzer
anzer make paragraph:
    font-weight="bold";
```
Expected: valid.

### S14 — Border shorthand
```anzer
anzer make container:
    border="1px solid black";
```
Expected: valid; shorthand parsed into components.

### S15 — Border individual properties
```anzer
anzer make container:
    border-width=2,
    border-style="solid",
    border-color="blue";
```
Expected: valid; width defaults to px.

### S16 — Border shorthand plus individual override
```anzer
anzer make container:
    border="1px solid black",
    border-color="red",
    border-width=3;
```
Expected: valid; final border is `3px solid red`, regardless of declaration order.

### S17 — Alias for minimum width
```anzer
anzer make container:
    minimum-width=300;
```
Expected: valid; normalized to `min-width: 300px`.

### S18 — Layout styling on container
```anzer
anzer make container:
    display="flex",
    gap=10;
```
Expected: valid; gap normalizes to pixels.

## Invalid cases

### S19 — Unknown unit
```anzer
anzer make container:
    width="10 furlongs";
```
Expected: unknown unit error.

### S20 — Negative padding
```anzer
anzer make container:
    padding="-10px";
```
Expected: invalid negative value.

### S21 — Negative gap
```anzer
anzer make container:
    display="grid",
    gap="-2px";
```
Expected: invalid negative value.

### S22 — Unsupported color function
```anzer
anzer make paragraph:
    color="rgb(255, 0, 0)";
```
Expected: unsupported color syntax error.

### S23 — Invalid hex color
```anzer
anzer make paragraph:
    color="#12GG99";
```
Expected: invalid hex color.

### S24 — Alias and canonical duplicate
```anzer
anzer make paragraph:
    font="Arial",
    font-family="Roboto";
```
Expected: duplicate property after alias normalization.

### S25 — Duplicate min-width alias
```anzer
anzer make container:
    minimum-width=300,
    min-width=200;
```
Expected: duplicate property after alias normalization.

### S26 — Unknown property
```anzer
anzer make container:
    opacity=0.5;
```
Expected: unknown property error for v0.1 catalog.

### S27 — Unit invalid for property
```anzer
anzer make container:
    border-width="10%";
```
Expected: invalid unit for border-width.

### S28 — Invalid width syntax
```anzer
anzer make container:
    width="10px + 5px";
```
Expected: unsupported expression error.

## Reusable style cases

### S29 — Direct element override of style
```anzer
anzer make style "card style 1":
    font="Arial",
    padding=20;
anzer make container:
    use style="card style 1",
    font-family="Roboto",
    padding=30;
```
Expected: valid; element properties override style properties.

### S30 — Alias duplicate inside reusable style
```anzer
anzer make style "bad style":
    font="Arial",
    font-family="Roboto";
```
Expected: duplicate property error within the style declaration.


## Additional edge cases

### S31 — Decimal numeric length defaults to pixels
```anzer
anzer make container:
    width=12.5,
    padding=0.5;
```
Expected: valid; values normalize to `12.5px` and `0.5px`.

### S32 — Friendly viewport unit names
```anzer
anzer make container:
    width="50 viewport width",
    height="75 viewport height";
```
Expected: valid; normalize to `50vw` and `75vh`.

### S33 — Physical unit aliases
```anzer
anzer make container:
    width="3 inches",
    padding="4 millimeters",
    margin="2 points";
```
Expected: valid; normalize to `3in`, `4mm`, and `2pt`.

### S34 — Unit alias spacing
```anzer
anzer make container:
    width="20 px";
```
Expected: valid; whitespace between number and unit is normalized.

### S35 — Min/max dimension properties
```anzer
anzer make container:
    min-width=200,
    max-width="80 percent",
    min-height=100,
    max-height="500 pixels";
```
Expected: valid; values normalize to `200px`, `80%`, `100px`, and `500px`.

### S36 — Border shorthand with omitted components
```anzer
anzer make container:
    border="solid red";
```
Expected: valid. The supplied style and color are parsed; omitted width defaults to medium, so the resolved border is medium solid red. CSS-compatible defaults apply only to omitted components (width=medium, style=none, color=currentcolor). Tokens may appear in any order, with no duplicate component. This shorthand grammar is fixed for v0.1.

### S37 — Border component overrides regardless of order
```anzer
anzer make container:
    border-width=3,
    border="1px solid black";
```
Expected: valid; individual `border-width` remains `3px` after shorthand expansion, independent of order.

### S38 — Border-style allowed values
```anzer
anzer make container:
    border-style="dashed";
```
Expected: valid.

### S39 — Invalid border style
```anzer
anzer make container:
    border-style="sparkle";
```
Expected: error; unsupported border style.

### S40 — Duplicate canonical property
```anzer
anzer make container:
    padding=10,
    padding=20;
```
Expected: duplicate property error.

### S41 — Duplicate aliases with case variation
```anzer
anzer make container:
    padding="10 PIXELS",
    padding="20px";
```
Expected: duplicate property error (property duplicate, not value duplicate).

### S42 — Unsupported unitless nonzero ambiguity is not an error
```anzer
anzer make container:
    width=20;
```
Expected: valid; normalize to `20px`.

### S43 — Negative min/max dimension
```anzer
anzer make container:
    min-width="-10px";
```
Expected: error; negative dimension constraint is invalid.

### S44 — Auto margin
```anzer
anzer make container:
    margin="auto";
```
Expected: valid.

### S45 — Auto padding is invalid
```anzer
anzer make container:
    padding="auto";
```
Expected: error.

### S46 — Reusable style alias override
```anzer
anzer make style "card style 1":
    minimum-width=200;
anzer make container:
    use style="card style 1",
    min-width=300;
```
Expected: valid; element's canonical property overrides the style's normalized property.

### S47 — Alias duplicates inside style
```anzer
anzer make style "card style 1":
    minimum-width=200,
    min-width=300;
```
Expected: duplicate property error inside the style.

### S48 — CSS value injection rejected
```anzer
anzer make container:
    color="red; background-color: blue";
```
Expected: invalid color value; value must not inject another CSS declaration.

### S49 — Unsupported CSS variable rejected
```anzer
anzer make container:
    width="var(--width)";
```
Expected: unsupported expression error in v0.1.

### S50 — Unsupported CSS calc rejected
```anzer
anzer make container:
    width="calc(100% - 20px)";
```
Expected: unsupported expression error in v0.1.


## Notes

- These are specification tests, not executable compiler tests.
- Valid cases must verify normalized CSS output.
- Invalid cases must verify error category and source location.
- Tests should also verify compact/multiline equivalence where relevant.
- Do not silently widen the accepted property catalog while implementing tests.

## Completion

The specification stress test now covers 50 cases, including core accepted behaviors and edge cases. This is considered complete as a design/specification test suite. It is not executable and does not claim compiler runtime validation; execution becomes possible after parser/compiler implementation.


## Friendly property spelling normalization

### S51 — Space separator equivalent to hyphen
```anzer
anzer make paragraph: font style="italic";
```
Expected: valid; normalized to `font-style="italic"`.

### S52 — Expanded minimum-width alias
```anzer
anzer make container: minimum width=300;
```
Expected: valid; normalized to `min-width: 300px`.

### S53 — Canonical duplicate after space normalization
```anzer
anzer make paragraph: font-style="italic", font style="normal";
```
Expected: duplicate canonical property error.

### S54 — Duplicate expanded alias and canonical property
```anzer
anzer make container: minimum width=300, min-width=200;
```
Expected: duplicate canonical property error.
