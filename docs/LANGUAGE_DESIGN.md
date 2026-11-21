# Language Design

## Current direction

Anzer is a command-oriented web authoring language intended to make website creation approachable without sacrificing precision. Authors should describe content, semantic type, appearance, and behavior in one `.anzer` source file.

The long-term ambition is to replace HTML as the primary author-facing language. The initial compiler milestone, however, targets standard HTML, CSS, and JavaScript for compatibility with existing browsers and hosting. That output target should not be mistaken for Anzer's ultimate identity or ceiling.

## Core design

- Explicit document boundaries: `<anzer start>` and `<anzer end>`.
- Command-oriented creation syntax: `anzer make ...`.
- Properties attach directly to the element or reusable style.
- Element defaults reduce mandatory repetition.
- Reusable numbered styles are independent of content position.
- Compact single-line and multiline forms are both supported and semantically equivalent.
- Initial compiler output is standard HTML, CSS, and JavaScript.

## Element semantics and defaults

An element command has a default semantic type. For example, `title` defaults to H1 and therefore generates an actual HTML heading, not a generic element styled to resemble one. Explicit type overrides may be supported where valid.

A reusable style may define a semantic type. Applying that style should not require the element to repeat its type.

## Style reuse and precedence

Reusable numbered styles can be declared and applied by reference. The proposed property resolution order is:

1. Element defaults.
2. Reusable style properties.
3. Direct properties on the element.

Direct element properties override reusable style values.

Styles should be reusable independently of element position or document ordering.

## Presets

Friendly presets such as `soft`, `hard`, `raised`, `3D`, and `glow` may represent standardized visual effects. Presets must have deterministic definitions; their names cannot be left to subjective interpretation.

## Constraints

- Keep the language consistent and learnable.
- Avoid needless punctuation and duplicated information.
- Preserve accessibility and semantic HTML during the compatibility-target phase.
- Keep compilation deterministic.
- Escape and validate emitted content.
- Separate parsing, validation, and code generation.
- Do not add commands solely because they sound natural; each needs a defined grammar and behavior.

## Validation process

Before freezing the grammar or implementing a parser, review the language against realistic scenarios: a landing page, article page, multilingual content, layout/card components, and a form or interaction. The examples should expose ambiguous syntax, missing capabilities, and excessive complexity.
