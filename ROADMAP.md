# Roadmap

This roadmap separates the frozen v0.1 milestone from later work. Roadmap items are plans, not statements that the features exist.

## Phase 0 — Language and specification
- [x] Establish the language goals and long-term direction.
- [x] Define the single `.anzer` authoring source.
- [x] Freeze the v0.1 compiler contract and CLI scope in documentation.
- [ ] Continue validating examples and grammar edge cases against the frozen specification.

## Phase 1 — v0.1 compiler
- [ ] Implement the Python CLI: `anzer check` and `anzer compile`.
- [ ] Implement lexer/tokenizer and parser for the frozen grammar.
- [ ] Build internal AST and semantic validation.
- [ ] Normalize document/style properties.
- [ ] Render a self-contained HTML file with embedded CSS and conditional embedded JS.
- [ ] Ensure deterministic output, actionable diagnostics, and no partial output on errors.
- [ ] Add automated tests across compiler stages.
- [ ] Compile and browser-test a representative example.

## Phase 2 — Basic developer experience (after v0.1)
- [ ] Improve diagnostics and source locations beyond the minimum.
- [ ] Consider a local preview server, watch mode, or hot reload; these are not part of v0.1.
- [ ] Add editor support and formatting only after the grammar stabilizes.

## Phase 3 — Language evolution (post-v0.1, design-led)
Potential features:
- Variables and expressions.
- Conditionals and loops.
- Functions and reusable components.
- Imports and modules.

These require design and specification work; they are not commitments to implement all features.

## Phase 4 — Ecosystem
- [ ] Define package/library conventions if the language needs them.
- [ ] Expand documentation, examples, editor tooling, and formatter.

## Long-term exploration
- [ ] Investigate self-hosting.
- [ ] Explore an Anzer-native runtime/browser or other ways to reduce dependence on HTML as the author-facing language.
- [ ] Consider alternate compilation targets only when there is a clear use case.

The long-term goal remains more ambitious than the first HTML compiler. v0.1 is a practical compatibility milestone, not the final identity of Anzer.
