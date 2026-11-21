# Decision Log

Decisions are recorded as the project develops. Revisit accepted decisions only when there is a concrete reason.

## D-001: Project name and extension
- **Decision:** Anzer; source extension `.anzer`.
- **Status:** Accepted.

## D-002: Initial target
- **Decision:** Browser websites, compiled to standard HTML, CSS, and JavaScript.
- **Status:** Accepted.

## D-003: Unified source
- **Decision:** Explore one authoring file for structure, style, and behavior.
- **Status:** Accepted.

## D-004: Hosting and development
- **Decision:** Zero-budget local development, GitHub as primary public source and documentation host.
- **Status:** Accepted.

## D-005: Compiler implementation language
- **Decision:** Not yet selected; Python is a practical candidate for the first prototype.
- **Status:** Open.

## D-006: Syntax
- **Decision:** Command-oriented syntax using `anzer make`, explicit document markers, and property-based declarations. Syntax is still provisional and must be tested before grammar freeze.
- **Status:** Accepted direction; grammar open.

## D-007: v0.1 compiler scope
- **Decision:** The first compiler milestone should produce a static browser page from one source file, including structure, style, and one basic interaction.
- **Status:** Accepted as milestone goal; grammar remains open.

## D-008: Document boundaries and formatting
- **Decision:** Draft source uses `<anzer start>` and `<anzer end>`. Both compact single-line and multiline instruction formats must be supported with equivalent meaning.
- **Status:** Accepted design direction.

## D-009: Semantic element defaults
- **Decision:** Element commands have sensible semantic defaults. In particular, `title` defaults to H1 and generates semantic HTML H1; heading types also determine default visual presentation. Type can be overridden where compatible.
- **Status:** Accepted design direction.

## D-010: Numbered reusable styles
- **Decision:** Reusable style definitions use numbered identifiers (e.g., paragraph style 1, paragraph style 2) and are independent of content position. Elements can apply a style using `use style`.
- **Status:** Accepted design direction.

## D-011: Style property precedence
- **Decision:** Resolve properties in order: element defaults, reusable style, direct element properties. Direct properties override style properties. When a reusable style defines the compatible semantic type, the element does not need to repeat it.
- **Status:** Accepted design direction.

## D-012: Style compatibility diagnostics
- **Decision:** A style with a semantic type incompatible with the target element must not silently produce contradictory HTML semantics. The compiler should report a diagnostic; whether that is a warning or error is still open.
- **Status:** Accepted principle; diagnostic severity open.

## D-013: Visual presets
- **Decision:** Named visual presets such as `soft`, `hard`, `raised`, `3D`, and `glow` may be used, but each must have standardized deterministic rendering and supported parameters.
- **Status:** Accepted design direction.

## D-014: Containers and nesting
- **Decision:** Use brace-delimited container blocks for nesting. Opening `{` begins a container body and `}` closes the most recently opened container. Containers may contain elements and nested containers; empty containers are allowed. Unmatched braces and an `<anzer end>` with open containers must be diagnosed.
- **Status:** Accepted design direction; exact grammar remains provisional.

## D-015: Flexible style definition
- **Decision:** Support both reusable numbered/named style definitions and inline properties attached to an element. Reusable styles are applied with `use style`; inline properties avoid defining a separate style when reuse is unnecessary. Both workflows should coexist.
- **Status:** Accepted design direction; exact syntax remains provisional.

## D-016: Embeds and rich link previews
- **Decision:** Explore a simple `anzer embed` command family for social posts, Journoist Drops, video embeds, and rich link-preview cards. The syntax should conceal provider-specific markup, with a provider adapter layer and graceful fallback to a clickable URL when embedding is unsupported or blocked.
- **Status:** Accepted design direction for exploration; provider support, security, privacy, and syntax remain open.

## D-017: Inline hyperlinks
- **Decision:** Ordinary hyperlinks within text must be supported separately from embeds and rich link-preview cards. Inline link syntax is under exploration; quoted/nested syntax must be stress-tested for parsing and escaping.
- **Status:** Accepted design direction; syntax open.
