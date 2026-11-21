# Style Property Stress Test 1

Status: **Test proposal**
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

## Notes

- These are specification tests, not executable compiler tests.
- Valid cases must verify normalized CSS output.
- Invalid cases must verify error category and source location.
- Tests should also verify compact/multiline equivalence where relevant.
- Do not silently widen the accepted property catalog while implementing tests.
