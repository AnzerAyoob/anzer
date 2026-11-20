# Anzer Language Specification — Draft v0.1

**Status: Draft / discussion only**

This specification is a starting point. No grammar or syntax is considered stable yet.

## Scope

Version 0.1 aims to define a minimal source format capable of describing a single web page with:

- Page metadata/title.
- Basic content and structural elements.
- Style declarations.
- At least one user interaction/event.

The compiler output should be ordinary HTML, CSS, and JavaScript.

## Non-goals

- General-purpose systems programming.
- Native machine-code compilation.
- Server-side application framework.
- Package manager or ecosystem in the first milestone.
- Self-hosting compiler in the first milestone.

## Required design decisions

Before implementation, define:
1. Source file and encoding rules.
2. Lexical tokens and comments.
3. Page and element grammar.
4. Style declaration grammar.
5. Event/behavior grammar.
6. Literal and expression rules.
7. Escaping and security behavior.
8. Compiler diagnostics.
9. Output directory and asset naming.
10. Minimum browser compatibility target.

## Acceptance test

A single example file must compile successfully into a web page with styling and an interaction. The generated output must be inspectable and usable on static hosting.
