# Anzer v0.1 Compiler Architecture

**Status:** Architecture proposal for implementation  
**Scope:** v0.1 frozen language specification  
**Purpose:** Define compiler boundaries, internal representations, module layout, and implementation order before writing compiler code.

This document is implementation-facing. The unified v0.1 specification and decision-freeze documents remain authoritative for language behavior. This architecture must not introduce new syntax or silently alter frozen semantics.

## 1. Architectural principles

1. **Pipeline, not a monolith.** Lexing, parsing, validation, normalization, rendering, and output are separate phases.
2. **Parse before render.** The parser must never generate HTML or CSS.
3. **Validate before output.** No final output is written when compilation has errors.
4. **Canonical internals.** Aliases and flexible spelling are resolved to canonical names before later stages.
5. **Deterministic output.** The same source and compiler version produce the same output.
6. **Small v0.1 surface.** No speculative framework, plugin system, macro system, or extension API.
7. **Useful diagnostics.** Errors retain source locations and identify the phase and category.
8. **Security by construction.** Render only validated nodes and properties; escape text and attributes; apply URL policies centrally.

## 2. Compiler pipeline

`Source → Lexer → Parser → AST → Semantic Validator → Normalizer → Renderer → Output`

The pipeline is strictly ordered:

1. **Source loader** — read UTF-8 source and establish filename/source identity.
2. **Lexer** — emit tokens with source spans; decode string escapes once.
3. **Parser** — build a syntax AST from tokens; enforce grammar and block structure.
4. **Semantic validator** — validate element rules, property compatibility, required values, IDs, references, and toggle targets.
5. **Normalizer** — canonicalize property names/aliases, resolve reusable styles, calculate effective properties and normalized values.
6. **Renderer** — produce HTML, CSS and the minimal toggle runtime from the validated normalized document.
7. **Output writer** — write artifacts only after successful compilation; avoid partial output on errors.

No phase should bypass the preceding phase's guarantees.

## 3. Proposed repository layout

The architecture is language-agnostic. If v0.1 is implemented in Python, use the following initial structure; keep module boundaries even if packaging changes later.

```
anzer/
  README.md
  pyproject.toml
  src/
    anzer/
      __init__.py
      cli.py
      compiler.py
      source.py
      diagnostics.py
      tokens.py
      lexer.py
      ast.py
      parser.py
      elements.py
      properties.py
      semantic.py
      normalize.py
      styles.py
      urls.py
      render/
        __init__.py
        html.py
        css.py
        runtime.py
        document.py
  tests/
    lexer/
    parser/
    semantic/
    normalize/
    render/
    integration/
    fixtures/
  docs/
```

Avoid splitting every helper into its own file at the outset. This is a suggested logical layout, not a requirement for dozens of tiny modules.

## 4. Source and location model

Every token and AST node should retain a source span:

- filename or source identifier
- start offset
- end offset
- start line and column
- end line and column where useful

Offsets should use Python string positions consistently. Line and column should be 1-based in diagnostics.

The source object owns the original text and line-start index table. Diagnostics should use this table to calculate line/column; lexer and parser should not repeatedly scan from the beginning.

## 5. Lexer

### Responsibilities
- recognize document markers, statement keywords, identifiers, punctuation, braces, equals signs, commas, and semicolons
- tokenize quoted strings and decode the supported escapes
- recognize numeric literals and unquoted boolean literals as tokens
- recognize property names with allowed lowercase characters and separators
- track source spans
- reject invalid characters, malformed strings, unknown escapes, physical newlines inside strings, and invalid token forms

### Does not
- decide whether an element exists
- decide whether a property is valid for an element
- resolve style references
- generate markup

### Token model
Each token contains:
- token kind
- raw lexeme
- decoded value when applicable
- source span

Do not discard raw string spelling: retaining it helps diagnostics and tests while the decoded value is used semantically.

The lexer should be deterministic and have no hidden permissive fallback. Any recovery must preserve safe token boundaries.

## 6. Parser

### Responsibilities
- parse document start/end markers
- parse `anzer make` declarations
- parse properties and their values
- parse reusable style declarations and references according to the frozen grammar
- parse leaf statements and container blocks
- enforce semicolon termination for leaf statements
- enforce balanced braces and valid nesting
- construct AST nodes and source spans

### Does not
- output HTML/CSS
- validate CSS values
- infer layout mode
- resolve styles
- decide toggle target existence

Parser recovery is allowed only when it can safely continue at a known boundary (such as a semicolon or closing brace). If recovery risks misinterpreting subsequent content, stop parsing and report the error.

## 7. AST

The AST represents source structure, not browser output.

### Document
- document marker span
- ordered declarations/styles and root nodes
- source span

### Element node
- source element name as written
- property assignments (preserving source order)
- optional style reference
- children for container nodes
- direct text where supported by the frozen grammar
- source span

### Property assignment
- property name as written
- raw value representation (string, number, boolean)
- source span

### Style declaration
- style name
- target element kind
- property assignments
- source span

Use a small set of typed node classes or tagged structures. Avoid a generic untyped dictionary AST where mistakes are discovered only at runtime. At the same time, avoid premature visitor frameworks or complex inheritance.

AST nodes should be immutable after parsing where practical. Validation and normalization should produce separate representations instead of mutating parser output in place.

## 8. Element and property registries

Element and property metadata should be centralized, not scattered through parser conditionals or renderer branches.

The element registry defines:
- Anzer element name
- HTML tag mapping
- leaf/container/void classification
- allowed properties
- required properties
- supported type overrides
- semantic category

The property registry defines:
- canonical property name
- explicit aliases
- accepted value category
- allowed element kinds
- normalization rules
- validation function or rule
- CSS output mapping
- whether it is a layout property and required layout mode

Registry data should be declarative where possible. Complex validators can be code-backed, but they must be referenced from the registry.

## 9. Semantic validation

Semantic validation consumes the AST and emits diagnostics. It should not render.

Checks include:
- known element names and style declarations
- valid property spelling/alias and canonical duplicate detection
- element/property compatibility
- required properties
- value types and property-specific constraints
- supported type overrides
- container-only layout properties
- explicit display/layout compatibility
- flex/grid property compatibility
- valid grid track syntax within v0.1 limits
- IDs: duplicate IDs and ID constraints
- toggle action and target requirements
- toggle target exists, is a supported target kind, and is unique
- URL scheme and URL category policy
- trusted HTML usage acknowledgement requirements

Validation should accumulate independent errors when safe to do so. It should not accumulate cascaded noise from a single malformed declaration.

The semantic result is either:
- a valid AST plus semantic metadata; or
- diagnostics with no renderable compilation result.

## 10. Normalization and style resolution

Normalization converts valid AST values into canonical compiler data.

### Property normalization
- aliases → canonical property names
- unit aliases → canonical unit spelling
- values → validated canonical representation
- enum aliases → canonical CSS values
- canonical property order should be defined for deterministic output

### Reusable styles
Resolve each element's effective property set using the frozen order:

**browser baseline → reusable style → direct element properties**

Style references are element-kind scoped. No style-to-style inheritance. Direct properties override style properties. A property cannot appear twice in the same layer after alias normalization.

Normalization should produce a resolved element tree, retaining source spans for diagnostics and debugging.

Do not let the renderer repeat style-resolution logic.

## 11. Render model

The renderer should consume only the normalized, semantically valid model.

Renderer responsibilities:
- produce safe HTML structure
- escape text nodes
- escape attribute values
- emit validated URLs
- emit deterministic inline or generated CSS according to the chosen v0.1 output strategy
- render containers and child ordering
- render images with alt fallback policy
- render button toggles using the small runtime contract
- render trusted HTML only at its explicit insertion point, after acknowledgement

Renderer must not:
- validate unknown properties
- normalize aliases
- resolve styles
- guess missing required values
- silently drop invalid declarations

## 12. HTML, CSS, and runtime separation

Keep output generation split into three components:

### HTML renderer
Responsible for tags, content, attributes, and child order. HTML escaping is centralized and tested.

### CSS renderer
Responsible for baseline CSS and validated style declarations. CSS output should be stable and should not accept arbitrary source strings as CSS values.

### Toggle runtime
The smallest runtime needed for `action="toggle"`. It should:
- find the validated target ID
- toggle visibility without destroying the target's original display styling
- synchronize accessibility state (including button state and relevant ARIA attributes)
- avoid arbitrary user code or dynamic expression evaluation

No runtime should be emitted if the document contains no toggle behavior.

## 13. Compiler API

Keep the compiler callable independently from the CLI.

Suggested API shape:

```python
compile_source(source_text: str, filename: str = "<input>") -> CompileResult
```

CompileResult contains:
- success flag
- diagnostics
- generated HTML (only on success)
- generated CSS (only on success, if separate)
- optional runtime flag/content (only when needed)
- compiler version

The CLI should be a thin layer over this API. It should not duplicate parsing or validation.

## 14. CLI v0.1

Keep command-line scope small.

Proposed initial commands:
- `anzer compile input.anzer`
- optional explicit output path flag, once output packaging is decided
- `anzer check input.anzer` (validation without writing output)

Avoid watch mode, dev server, package manager, project scaffolding, or multi-file imports in v0.1.

The CLI must:
- report diagnostics to stderr
- return nonzero exit code for compilation errors
- not overwrite output on failed compilation
- write deterministic artifacts on success
- avoid creating unnecessary files for check-only mode

The exact output format (single HTML file versus HTML/CSS/runtime assets) is an implementation decision to finalize before renderer coding. Architecture supports either without changing the language.

## 15. Diagnostics

A diagnostic should contain:
- stable code
- category (lexical, syntax, semantic, validation, output)
- severity (error/warning)
- message
- source span
- optional related spans or hint

Stable codes matter because tests, editor tooling, and future integrations should not parse human-readable messages.

Diagnostics should be concise, specific, and actionable. Example:

```
E-PROP-UNKNOWN: Unknown property 'colour'.
  --> page.anzer:12:18
  help: Did you mean 'color'?
```

Suggestions may be added only when confidently derived; don't guess.

## 16. Error and recovery strategy

- Lexer/parser errors prevent semantic validation when the AST is structurally unsafe.
- Independent semantic errors should be collected in one run.
- Rendering is skipped whenever errors exist.
- No partially generated HTML/CSS should be returned as a successful result.
- Compiler exceptions are reserved for internal bugs; user mistakes become diagnostics.

## 17. Testing architecture

Test by phase and then end-to-end.

### Lexer
- token sequences
- string escape decoding
- malformed escapes
- line/column
- invalid characters

### Parser
- document markers
- statements
- containers and nested blocks
- leaf terminators
- compact and multiline equivalence
- syntax recovery boundaries

### Semantic
- element/property compatibility
- required properties
- type overrides
- IDs and toggle targets
- URL validation
- flex/grid constraints
- trusted HTML acknowledgement

### Normalization
- aliases
- duplicate detection after canonicalization
- style precedence
- unit canonicalization
- stable property order

### Renderer
- HTML escaping
- attribute escaping
- URL escaping/policy
- baseline CSS
- tag mappings
- image alt fallback
- toggle runtime behavior
- trusted HTML insertion boundary

### Integration
- valid source → deterministic output
- invalid source → diagnostics and no output
- golden fixtures for representative pages
- compact and multiline forms produce equivalent output

Golden tests should assert stable output, but avoid overfitting tests to irrelevant whitespace unless whitespace is part of the output contract.

## 18. Implementation order

Build in slices, each tested before the next:

1. Source and diagnostics foundation
2. Lexer and token tests
3. Parser and AST tests
4. Element/property registry
5. Semantic validator
6. Normalizer and reusable styles
7. HTML/CSS renderer without toggles
8. Toggle runtime and accessibility behavior
9. CLI compile/check
10. Integration/golden tests
11. Security test pass and documentation examples

Do not build the full renderer while parser behavior is unstable. Do not implement toggle behavior before the ordinary element pipeline works.

## 19. Security review checklist

Before v0.1 release:
- all text escaped
- all attributes escaped
- link and image URL policies enforced centrally
- no unsafe URL schemes
- no arbitrary CSS expressions/functions accepted
- no user-supplied JavaScript except acknowledged trusted HTML escape hatch
- trusted HTML acknowledgement is explicit and documented as unsafe
- no output generated on errors
- toggle target IDs validated and safely referenced
- output paths handled without unintended traversal or overwrite

## 20. Final implementation decisions

These decisions are user-approved for v0.1:

1. **Image alt fallback:** When alt is omitted, derive readable text from the filename: remove extension and replace hyphens/underscores with spaces. Do not require alt or default to empty alt.
2. **Output:** Produce one self-contained HTML file. CSS is embedded; toggle runtime is embedded only when needed. Source input uses the `.anzer` extension. Compiler output is HTML, not a second Anzer source file.
3. **CLI:**
   - `anzer compile <input.anzer> [-o <output.html>]`
   - `anzer check <input.anzer>`
   - If `-o` is omitted, output defaults to the input filename with its extension replaced by `.html`.
   - `check` validates without writing output.
   - Compilation errors return a nonzero exit code and do not create/overwrite the output file.
4. **Implementation language:** Python is approved for v0.1.

No additional decisions are required to begin implementation. CLI and packaging can be refined without changing the language specification.

## 21. Definition of architectural completion

Compiler architecture is considered complete when:
- phases and responsibilities are clear
- AST and source location model are defined
- registry-driven element/property design is defined
- validation and normalization boundaries are defined
- rendering and runtime boundaries are defined
- CLI/API contract is defined
- test organization and implementation sequence are defined
- unresolved implementation-affecting decisions are listed

This document completes the architecture planning phase. It does not claim a compiler has been implemented or tested.
