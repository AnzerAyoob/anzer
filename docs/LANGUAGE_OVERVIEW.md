# Language Overview

Anzer is an experimental source language for authoring web pages and applications. Its long-term aim is to unify web structure, styling, and behavior in one readable language and become an alternative to writing HTML directly.

A source document uses the `.anzer` extension. This is the sole intended authoring format; internal compiler data structures are implementation details, not additional document formats.

## Current milestone

The early compiler design translates Anzer source into standard web assets—HTML, CSS, and JavaScript—so output can run in existing browsers. This is a practical compatibility target for the initial milestone, not a limitation on the language's long-term vision.

An Anzer-native runtime or browser execution model is not currently implemented and remains a future architectural question.

## Language concerns

- **Structure:** page elements and content.
- **Style:** visual properties and layout.
- **Behavior:** events and client-side interaction.

The language is not finalized. Sample syntax and examples in this repository are illustrative unless explicitly marked as implemented and tested.
