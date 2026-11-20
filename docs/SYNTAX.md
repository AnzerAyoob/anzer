# Syntax Design — Proposal

**Status:** Experimental syntax proposal. Not ratified.

Anzer syntax must be cohesive and not merely HTML/CSS/JavaScript embedded in a file. The proposal uses named content constructs, nested `style` blocks, and explicit `on event` blocks.

## Example

```anzer
page "Anzer Demo" {
    section {
        heading "One language."
        text "Structure, style and behavior together."

        button "Try Anzer" {
            style {
                background: "#2563eb"
                color: "#ffffff"
                padding: 12
                radius: 8
            }

            on click {
                alert("Welcome!")
            }
        }
    }
}
```

## Syntax goals

- Blocks use braces.
- Strings are double-quoted.
- Content is expressed with named constructs, not raw HTML tags.
- Style properties use a readable property/value form.
- Behavior is explicit and attached to the element that handles it.
- The compiler can report precise errors.

## Questions to resolve

1. Should `section` be the only generic container, or should `container`, `card`, `row`, etc. be built-in?
2. Should style properties use CSS names (`border-radius`) or Anzer names (`radius`)?
3. Should text nodes use `text`, `paragraph`, or both?
4. How should links and images be declared?
5. Is global styling necessary in the first milestone?

Don't implement this syntax until these questions are reviewed and the grammar is complete.
