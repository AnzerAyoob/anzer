# Development Plan

This plan follows the v0.1 decision freeze and compiler architecture. Planned work is not an implementation claim.

## Current milestone: v0.1 compiler

### 1. Repository and specification baseline
- Keep the authoritative v0.1 specification and architecture documents consistent.
- Convert frozen grammar and semantic rules into implementation tests.
- Record any necessary specification change before implementing behavior that conflicts with the freeze.

### 2. Compiler foundation
- Implement Python package structure and CLI entry point.
- Implement source loading, diagnostics, and source-location tracking.
- Establish test conventions and a deterministic test harness.

### 3. Front end
- Implement lexer/tokenization and parser for the frozen grammar.
- Build internal AST structures.
- Reject malformed syntax with actionable diagnostics.

### 4. Semantic validation and normalization
- Validate element/property compatibility, style resolution, defaults, and semantic rules.
- Normalize the internal document representation.
- Keep internal representations private to the compiler; do not create a second user-facing source format.

### 5. HTML output
- Render a single self-contained HTML file.
- Embed CSS.
- Embed JavaScript or interaction runtime only when the source requires it.
- Preserve semantic HTML and safe output/escaping behavior.
- Use the source filename with `.html` as the default output name; allow an explicit output path.

### 6. CLI contract
- `anzer check input.anzer`: validate without writing output.
- `anzer compile input.anzer [-o output.html]`: compile to HTML.
- Compilation errors must prevent output; do not leave partial output behind.

### 7. Verification and first end-to-end example
- Add tests for lexer, parser, semantic validation, rendering, CLI, errors, and output determinism.
- Compile representative examples and open the generated HTML in a browser.
- Verify the generated artifact is self-contained and that required interactions work.

## Explicitly deferred
- A runtime/viewer command such as `anzer render`.
- Preview server, watch mode, hot reload, and separate asset output directories.
- Variables, loops, functions, modules, packages, and advanced expressions.
- An Anzer-native browser runtime or self-hosting.

Deferred work should not be added to the v0.1 milestone without a deliberate scope/specification revision.
