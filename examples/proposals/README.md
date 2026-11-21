# Anzer Syntax Proposals

A broader syntax stress-test document is available at [docs/SYNTAX_STRESS_TEST.md](../../docs/SYNTAX_STRESS_TEST.md). It contains 15 scenarios, including nesting, styles, forms, multilingual text, behavior, and invalid syntax.

These examples are **design test cases only**. They are not guaranteed to compile and must not be treated as finalized syntax.

They are used to test the command-oriented design against common webpage patterns:

- `landing-page.anzer`: basic content and interaction
- `article-page.anzer`: article structure and repeated paragraphs
- `multilingual-page.anzer`: reusable styles for different scripts/fonts
- `cards-layout.anzer`: layout containers and nested elements
- `form-interaction.anzer`: inputs and interaction

## Review status

These examples currently expose unresolved syntax and semantic questions. In particular:

- How does nesting work and how is a card's content attached to it?
- Is `anzer make card` a container command with an explicit end, block, or scope?
- How are multiple properties and commands terminated?
- How do inputs, labels, form submission and validation work?
- What is the syntax for behavior and event actions?
- How is text direction (RTL/LTR) declared?
- How are repeated style IDs scoped and validated?
- Does a title element with type H2 remain a title command or become a heading command?
- What is the exact syntax for empty elements such as images and inputs?

Do not begin parser implementation until these questions are answered through syntax design.
