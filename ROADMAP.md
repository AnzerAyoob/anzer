# Roadmap

This roadmap is tentative and will change as the design is validated.

## Phase 0 — Language design
- Define core goals, non-goals, syntax, and compilation model.
- Establish specification v0.1.
- Validate examples for clarity and consistency.

## Phase 1 — Minimal web compiler
- Parse a single `.anzer` file.
- Represent source in a simple internal structure.
- Generate HTML, CSS, and JavaScript.
- Produce a predictable `dist/` directory.
- Add compiler tests and a minimal example.

## Phase 2 — Developer experience
- CLI: build and development preview.
- Diagnostics with source locations.
- Watch mode and useful error messages.

## Phase 3 — Language features
- Variables, expressions, conditionals, functions, and reusable components—only after their design is settled.
- Imports and module boundaries.

## Phase 4 — Ecosystem
- Package/library conventions.
- Documentation, examples, editor tooling, and formatting.

## Long-term explorations
- Self-hosting and compiler written in Anzer.
- Optimization and alternate targets, if there is a justified need.
