# Anzer Vision

Anzer's long-term goal is to become a unified, human-readable language for creating web pages and applications, replacing HTML as the primary author-facing document language. Authors should be able to express structure, styling, and behavior in one coherent source format: `.anzer`.

This is a long-term vision, not a description of the current implementation. The initial compiler milestone uses standard HTML, CSS, and JavaScript output so generated sites can run in existing browsers and be hosted with today's web infrastructure. A future Anzer-native runtime or browser ecosystem may be needed to move beyond that compatibility layer; this is an open architectural challenge, not an existing capability.

## Problem

Web development requires authors to coordinate HTML, CSS, and JavaScript across different syntaxes and often separate files. These standards are powerful and necessary for the web ecosystem, but their coordination can add friction—particularly for small projects, newcomers, and authors who want to focus on content and intent.

## Direction

Anzer should offer a coherent authoring model that is more approachable than writing the underlying web languages directly, while preserving precision, accessibility, predictable behavior, and expressive capability.

## Principles

- **One source language:** the `.anzer` format is the authored document format.
- **Readable, not simplistic:** approachable syntax must still support precise, valid, maintainable documents.
- **Long-term independence:** HTML is not the ultimate definition or limit of Anzer.
- **Practical progression:** begin with a compiler targeting standard web assets; validate the language before expanding its runtime ambitions.
- **Semantic and accessible output:** preserve meaningful structure and accessibility.
- **Deterministic behavior:** the same valid source and compiler version should produce predictable results.
- **No premature runtime claims:** Anzer-native browser execution is a future goal, not a current feature.
