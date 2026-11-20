# Language Design

## Current direction

Anzer is a unified web authoring language, initially focused on generating browser-compatible websites. The first target is not a general-purpose programming language.

The design should prioritize a cohesive, learnable syntax. Structure, styling, and behavior should be expressed in the same source language, with clear rules and separate compiler stages.

## Proposed syntax model

- `page` establishes the document.
- Content declarations establish structure.
- `style` blocks express visual properties.
- `on event` blocks describe interaction.
- The compiler emits standard HTML, CSS, and JavaScript.

This is a proposal; syntax is not ratified.

## Design constraints

- Simplicity and consistency.
- Avoid redundant syntax and excessive punctuation.
- Preserve accessibility semantics.
- Deterministic output.
- Safe escaping and validation.
- Avoid mixing parsing with code generation.

## Process

Design the semantics and intended behavior of constructs alongside their syntax. Validate proposed syntax against realistic page examples before choosing implementation details.

## Open questions

See [SYNTAX.md](SYNTAX.md) and [specification v0.1](../specification/VERSION_0.1.md).
