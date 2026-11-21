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
- **Status:** Accepted as project direction.

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
- **Decision:** A style with a semantic type incompatible with the target element must not silently produce contradictory HTML semantics. The compiler should report a diagnostic; whether this is a warning or error is still open.
- **Status:** Accepted principle; diagnostic severity open.

## D-013: Visual presets
- **Decision:** Named visual presets such as `soft`, `hard`, `raised`, `3D`, and `glow` may be used, but each must have standardized deterministic rendering and supported parameters.
- **Status:** Accepted design direction.
