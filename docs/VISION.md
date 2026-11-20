# Anzer Vision

Anzer explores a unified authoring language for web applications and pages. A developer writes one `.anzer` source file for the page's structure, styling, and behavior; the compiler emits standard web assets.

## Problem

Web development often requires authors to coordinate HTML, CSS, and JavaScript across files and syntaxes. This separation is useful and powerful, but can add friction for small projects and beginners.

## Proposed direction

Anzer should provide a coherent authoring experience without discarding the browser standards ecosystem. Generated output should remain ordinary HTML, CSS, and JavaScript.

## Principles

- Readability over cleverness.
- One source format for the initial web target.
- Explicit behavior and predictable output.
- Progressive scope: prove a small compiler before expanding.
- No proprietary runtime requirement for generated websites.
