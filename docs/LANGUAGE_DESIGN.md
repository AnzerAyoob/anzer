# Language Design

## Design goals

1. A single source file should be able to describe a simple web page.
2. Syntax should be readable and distinctive—not HTML, CSS, and JavaScript pasted together.
3. Style and behavior should have clear boundaries within the unified language.
4. Compilation should be deterministic and produce inspectable standards-based files.
5. Errors should be understandable and point to source locations.

## Open questions

- What are the canonical page and element constructs?
- How should style declarations be expressed?
- What is the event syntax?
- How are expressions and values represented?
- How should escaping and raw HTML be handled?
- How do reusable components and imports work?
- What is the security model for generated behavior?

These questions must be resolved in the specification before implementation becomes tightly coupled to a syntax.
