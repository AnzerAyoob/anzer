# Layout Property Stress Test 1

Status: **Specification stress suite for accepted v0.1 layout rules; compiler execution pending**
Scope: Accepted Anzer v0.1 layout catalog
Purpose: Validate accepted layout grammar and compatibility rules before compiler implementation.

## Valid cases

### L1 — Flex basic

```anzer
anzer make container:
    display="flex",
    gap=16;
```

Expected: valid; `gap` normalizes to `16px`.

### L2 — Flex direction and wrapping

```anzer
anzer make section:
    display="flex",
    flex-direction="column",
    flex-wrap="wrap";
```

Expected: valid.

### L3 — Flex alignment aliases

```anzer
anzer make container:
    display="flex",
    justify-content="start",
    align-items="end";
```

Expected: valid; values normalize to `flex-start` and `flex-end`.

### L4 — Flex gap with two values

```anzer
anzer make container:
    display="flex",
    gap="10px 20px";
```

Expected: valid.

### L5 — Separate gaps

```anzer
anzer make container:
    display="flex",
    row-gap=10,
    column-gap="2 rem";
```

Expected: valid; lengths normalize.

### L6 — Inline flex

```anzer
anzer make container:
    display="inline-flex",
    flex-direction="row-reverse";
```

Expected: valid.

### L7 — Grid basics

```anzer
anzer make container:
    display="grid",
    grid-template-columns="1fr 2fr",
    gap=12;
```

Expected: valid.

### L8 — Grid tracks with lengths and keywords

```anzer
anzer make container:
    display="grid",
    grid-template-columns="200px auto max-content",
    grid-template-rows="min-content 2fr";
```

Expected: valid.

### L9 — Inline grid and auto-flow

```anzer
anzer make container:
    display="inline-grid",
    grid-auto-flow="row";
```

Expected: valid.

### L10 — Grid alignment

```anzer
anzer make container:
    display="grid",
    justify-items="center",
    align-items="stretch",
    justify-content="space-between";
```

Expected: valid.

### L11 — Grid gap with friendly units

```anzer
anzer make container:
    display="grid",
    gap="1 centimetre";
```

Expected: valid; normalized to `1cm`.

### L12 — Display only

```anzer
anzer make container:
    display="block";
```

Expected: valid.

## Invalid cases

### L13 — Gap without display

```anzer
anzer make container:
    gap=10;
```

Expected: error; explicit flex/grid display required.

### L14 — Gap on block

```anzer
anzer make container:
    display="block",
    gap=10;
```

Expected: compatibility error.

### L15 — Flex property without flex display

```anzer
anzer make container:
    flex-direction="column";
```

Expected: error; requires flex/inline-flex.

### L16 — Grid property without grid display

```anzer
anzer make container:
    grid-template-columns="1fr 1fr";
```

Expected: error; requires grid/inline-grid.

### L17 — Invalid display

```anzer
anzer make container:
    display="masonry";
```

Expected: unknown display value error.

### L18 — Unsupported grid function

```anzer
anzer make container:
    display="grid",
    grid-template-columns="repeat(3, 1fr)";
```

Expected: unsupported grid track grammar error.

### L19 — Invalid fr value

```anzer
anzer make container:
    display="grid",
    grid-template-columns="0fr 1fr";
```

Expected: error; fr tracks require positive values.

### L20 — Invalid alignment value

```anzer
anzer make container:
    display="flex",
    justify-content="baseline";
```

Expected: error; baseline is not accepted for justify-content.

### L21 — Flex property on grid

```anzer
anzer make container:
    display="grid",
    flex-direction="column";
```

Expected: compatibility error.

### L22 — Grid property on flex

```anzer
anzer make container:
    display="flex",
    grid-template-columns="1fr 1fr";
```

Expected: compatibility error.

### L23 — Layout property on paragraph

```anzer
anzer make paragraph:
    display="flex",
    gap=10;
```

Expected: semantic error; layout properties are restricted to section/container in v0.1.

### L24 — Grid property on section with flex display

```anzer
anzer make section:
    display="flex",
    grid-auto-flow="column";
```

Expected: compatibility error.

## Notes

- These tests are specification examples, not executable tests until the compiler exists.
- A test implementation must verify both diagnostics and normalized CSS for valid cases.
- The catalog and stress tests should be reviewed together; do not silently expand the accepted grammar during implementation.
