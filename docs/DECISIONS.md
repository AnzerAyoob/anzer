# Decision Log

This log records decisions that govern Anzer. Revisit accepted decisions only when new evidence or a concrete implementation need justifies it. Current implementation status is tracked separately; a decision is not proof that a feature exists.

## D-001: Project name and source extension
- **Decision:** The language is Anzer; source files use `.anzer`.
- **Status:** Accepted.

## D-002: Long-term goal and initial target
- **Decision:** Anzer is intended to become a human-friendly, command-oriented document language and ultimately replace HTML as the primary author-facing language. The first milestone compiles to standard browser HTML.
- **Status:** Accepted; long-term native runtime/browser implications remain future exploration.

## D-003: Single authoring source
- **Decision:** A single `.anzer` file is the author-facing source for document structure, style, and supported behavior. Internal AST/IR/normalized structures are compiler implementation details, not additional user-facing file formats.
- **Status:** Accepted.

## D-004: Development and hosting constraints
- **Decision:** Prioritize zero-budget local development and GitHub as the public source and documentation host.
- **Status:** Accepted.

## D-005: Compiler implementation language
- **Decision:** Python is the implementation language for the v0.1 compiler.
- **Status:** Accepted.

## D-006: Command-oriented syntax
- **Decision:** Use command-oriented syntax with explicit document markers and property-based declarations. Grammar details are governed by the frozen v0.1 specification and related grammar documents.
- **Status:** Accepted direction; only changes supported by specification review should revise the grammar.

## D-007: v0.1 compiler contract
- **Decision:** v0.1 compiles one `.anzer` source file into one self-contained HTML output. CSS is embedded; JavaScript/toggle runtime is embedded only when required. The default output replaces the source extension with `.html`.
- **Status:** Accepted and frozen for v0.1.

## D-008: Document boundaries and formatting
- **Decision:** Document boundaries use the specified Anzer markers. Compact and multiline forms are supported only where the specification defines equivalent meaning.
- **Status:** Accepted as specified in v0.1.

## D-009: Semantic element defaults
- **Decision:** Elements use semantic defaults. The `title` element defaults to H1 and generates semantic H1 output; compatible overrides are permitted as specified.
- **Status:** Accepted as specified in v0.1.

## D-010: Reusable styles
- **Decision:** Reusable numbered styles are independent of content position and can be applied to elements using the specified style-use syntax.
- **Status:** Accepted as specified in v0.1.

## D-011: Style precedence
- **Decision:** Property precedence is element defaults, reusable style, then direct element properties. Direct properties override style properties.
- **Status:** Accepted as specified in v0.1.

## D-012: Style compatibility diagnostics
- **Decision:** Incompatible semantic types must not silently create contradictory HTML semantics. The compiler diagnoses incompatibility according to the severity defined by the specification.
- **Status:** Accepted principle; severity follows the spec.

## D-013: Visual presets
- **Decision:** Visual presets are deterministic and only support documented parameters and behavior.
- **Status:** Accepted as specified in v0.1.

## D-014: Containers and nesting
- **Decision:** Containers use the specified brace-delimited nesting. Empty containers are allowed; malformed/unclosed containers are diagnosed.
- **Status:** Accepted as specified in v0.1.

## D-015: Reusable and inline styling
- **Decision:** Reusable styles and inline element properties coexist. Use reusable definitions where reuse is helpful; inline properties for one-off declarations.
- **Status:** Accepted as specified in v0.1.

## D-016: Embeds and rich previews
- **Decision:** Provider-neutral embeds and rich link-preview cards are an exploration, not a v0.1 implementation commitment. Any future support must address provider adapters, fallback behavior, security, and privacy.
- **Status:** Future exploration; not part of the v0.1 contract unless explicitly specified.

## D-017: Inline hyperlinks
- **Decision:** Inline hyperlinks are distinct from embeds and rich preview cards. Syntax and escaping rules are governed by the v0.1 specification.
- **Status:** Accepted only to the extent defined in v0.1; avoid treating unresolved syntax proposals as implemented features.
