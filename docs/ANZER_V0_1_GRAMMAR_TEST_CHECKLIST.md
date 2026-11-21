# Anzer v0.1 Grammar & Compiler Test Checklist

**Status:** Definitive implementation checklist. Aligned to the frozen v0.1 specification and decision freeze. This is a test inventory, not executable compiler coverage.

## Authority
- Unified v0.1 specification and decision freeze are authoritative.
- Historical drafts and exploratory stress tests are supplemental, not normative.
- Every test must assert one outcome: pass/fail, normalized value/AST/output, diagnostic category/code and source location, and output-file behavior.

## Document and lexical structure
- [ ] Required start/end markers; missing, duplicate, reversed, misplaced markers diagnosed.
- [ ] UTF-8/Unicode preserved.
- [ ] Whitespace outside strings does not change meaning; token separation remains correct.
- [ ] Comments only if specified by freeze; otherwise rejected.
- [ ] Text outside document boundaries handled exactly per specification.

## Statements and nesting
- [ ] Leaf statements end in semicolon.
- [ ] Containers open/close with braces; nested and empty containers tested.
- [ ] No implicit nesting from names or indentation.
- [ ] Missing terminator, unmatched close, unclosed container, and end marker inside open block diagnosed.
- [ ] Compact and multiline forms yield equivalent AST.
- [ ] Child/sibling order preserved; recovery never merges statements.

## Strings and scalar values
- [ ] Double quotes and exact escape set.
- [ ] Unknown/incomplete escapes, unterminated strings, and raw physical newlines rejected.
- [ ] Escape decoding occurs once.
- [ ] Structural punctuation/marker text inside strings remains literal.
- [ ] Empty strings, URLs, Unicode/mixed scripts, escaped quote/backslash tested.
- [ ] Numeric, negative, decimal, and boolean tokens tested; quoted boolean-like values stay strings.
- [ ] Unsupported arrays, null, exponent notation, and uppercase booleans rejected as specified.

## Properties
- [ ] Names and values distinct; equals required.
- [ ] Commas required; missing comma/equals/value diagnosed.
- [ ] Whitespace around equals accepted.
- [ ] Name normalization, aliases, case rules, canonical duplicate detection.
- [ ] Unknown property catalog entries rejected.
- [ ] Type/range/unit/property-specific validation.
- [ ] CSS injection attempts rejected.
- [ ] Normalized output deterministic.

## Styles
- [ ] Element-kind-scoped numbered styles parse.
- [ ] Duplicate style identifiers diagnosed.
- [ ] Style references resolve; missing references diagnosed.
- [ ] Precedence: element defaults → reusable style → direct properties.
- [ ] Overrides work regardless of order where frozen.
- [ ] Style compatibility enforced.
- [ ] Alias duplicates within styles diagnosed.
- [ ] Compact/multiline style forms equivalent.

## Elements and semantics
- [ ] Only v0.1 catalog: title, paragraph, button, link, image, section, container.
- [ ] Defaults and allowed type overrides enforced.
- [ ] Required properties enforced.
- [ ] Leaf/container/void shape enforced; children inside leaves rejected.
- [ ] IDs unique; targets resolve.
- [ ] Button behavior limited to frozen toggle; target must be section/container ID.
- [ ] Accessibility state/output verified.
- [ ] Image alt fallback verified.
- [ ] Container direct-text/child ordering deterministic.

## Layout/style values
- [ ] Flex properties require flex/inline-flex.
- [ ] Grid properties require grid/inline-grid.
- [ ] Flex/grid cross-use diagnosed.
- [ ] Layout properties restricted to allowed elements.
- [ ] Gap restrictions and normalization.
- [ ] Grid track grammar, units, keywords, positive fr values, unsupported functions.
- [ ] Alignment aliases/allowed values.
- [ ] Length aliases, zero, auto, negative restrictions, colors, fonts, borders, presets.

## Safety and output
- [ ] Text/attributes HTML-escaped.
- [ ] CSS validated and safely emitted.
- [ ] URL schemes validated; unsafe schemes rejected.
- [ ] Raw HTML escape hatch treated as trusted author content and restricted to allowed contexts.
- [ ] No user-written JavaScript/event handlers executed.
- [ ] Compiler does not execute source.
- [ ] Output self-contained HTML; embedded CSS; JS only when required.
- [ ] Errors prevent output; no partial output.
- [ ] CLI: `anzer check input.anzer`; `anzer compile input.anzer [-o output.html]`; default `input.html`.

## Diagnostics/regression
- [ ] Invalid tests assert diagnostic category/code and source location.
- [ ] Valid tests assert AST, normalized properties, and output.
- [ ] Regression corpus runs for every compiler change.
- [ ] Tests do not silently expand frozen features/catalogs.

## Deferred from v0.1
- Native .anzer serving/runtime, `anzer render`, preview/watch/hot reload, separate assets.
- Embeds/rich previews/inline links unless ratified.
- Variables, loops, functions, modules, packages, self-hosting.
