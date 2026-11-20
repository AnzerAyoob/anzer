# Syntax

Syntax is not finalized. This page records a direction, not a promise of compatibility.

## Draft principles

- Block-based declarations with consistent delimiters.
- Clear element/content constructs.
- Style properties should be easy to distinguish from content.
- Event handlers should be explicit.
- Avoid ambiguous parsing rules and unnecessary punctuation.

## Illustrative draft (not implemented)

```anzer
page "Welcome" {
    section {
        heading "Hello, Anzer"
        text "Structure, style and behavior in one source."

        button "Say hello" {
            on click {
                alert("Hello!")
            }
        }
    }
}
```

This sample is only a discussion aid. Do not treat it as valid compiler syntax until the specification and parser agree.
