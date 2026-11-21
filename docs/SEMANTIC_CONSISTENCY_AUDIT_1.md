# Anzer v0.1 Semantic Consistency Audit

Status: **Audit reconciled against the v0.1 decision freeze; accepted findings closed, image-alt remains open**  
Scope: cross-document consistency of grammar, strings, properties, elements, styles, layout, embedding, and interactions.

## 1. Executive summary

The audit findings have now been reconciled with the user-approved v0.1 decision freeze. Most previously proposed resolutions are accepted and recorded; image-alt policy remains the only explicitly open decision. Remaining work is documentation consistency, precision checks, and later compiler implementation/testing. No compiler implementation or executable specification tests were run.


## 2. Document status map (reconciled)

The decision freeze (`ANZER_V0_1_DECISION_FREEZE_1.md`) is authoritative where this audit or older proposals conflict. Accepted resolutions are not pending user approval.

| Document | Current status | Audit result |
|---|---|---|
| Syntax audit | Review recommendations | Historical audit; superseded on some points by accepted grammar decisions |
| Grammar resolution | Reconcile with freeze | Structural rules accepted; decision freeze is authoritative |
| Core grammar stress test | Test draft | Valid structure coverage; some legacy element/property names remain |
| Property rules | Updated | Friendly spelling normalization and aliases are accepted; freeze is authoritative |
| Property stress test | Test draft | Mostly consistent with core rules; must not be mistaken for semantic property catalog tests |
| String rules | Accepted v0.1 | Consistent with string stress suite |
| String stress test | Test draft | Consistent with accepted string behavior |
| Element catalog | Reconcile with freeze | Accepted directions are recorded in freeze; image-alt policy remains open |
| Element/property compatibility review | Accepted resolution recorded | Freeze governs; compatibility matrix must remain aligned |
| Style property catalog | Reconcile with freeze | Catalog and stress suite require precision/alignment pass |
| Style stress test | Specification test suite | 50 cases, but some test examples use stale or incompatible names/elements |
| Layout catalog | Accepted v0.1 | Freeze governs accepted semantics; precision pass remains |
| Layout stress test | Test proposal | Good coverage, but no direct tests for section/container matrix or two-value gap semantics |


## 3. Findings


### A-01 — Historical syntax audit conflicts with later accepted grammar rules

**Severity: Documentation**

`SYNTAX_AUDIT.md` presents multiple issues as unresolved that were subsequently resolved: canonical style-reference placement after the colon, semicolon leaf termination, brace container opening, accepted string rules, property naming/value rules, and the explicit element catalog. It also recommends deferring HTML embedding, while the later element catalog marks scoped `anzer use html` as accepted.

**Resolution proposed:** Keep the audit as historical analysis, add a superseded/reconciled note linking the newer decisions. Do not treat it as the current specification.


### A-02 — Property rules examples use legacy names

**Severity: High**

`PROPERTY_RULES_PROPOSAL_1.md`, `PROPERTY_STRESS_TEST_1.md`, and `CORE_GRAMMAR_STRESS_TEST_1.md` contain `text-size`, while the style catalog defines `font-size`. `text-size` is not an accepted alias.

**Resolution proposed:** Replace `text-size` with `font-size` in current examples/tests, or explicitly accept and define `text-size` as an alias. Recommendation: do not add the alias; use canonical `font-size`.


### A-03 — Stress-test element names do not match the v0.1 catalog

**Severity: High**

Grammar and style tests use `card` as if it were a native element. The element catalog currently defines only title, paragraph, button, link, image, section, and container. A card can be authored as a container with a reusable style, but it is not a native element.

**Resolution proposed:** Replace test uses of `card` with `container` or `section` where semantic intent allows. Do not add `card` to the element catalog solely to preserve test fixtures.


### A-04 — Style applicability remains internally inconsistent

**Severity: High**

The compatibility review says the image allowlist excludes min/max dimensions and padding, while the style catalog's broad family table implies box properties may be allowed according to an element allowlist. The compatibility review's text-property row also needs image explicitly marked rejected, not generically allowed.

**Resolution proposed:** Treat the explicit compatibility matrix as authoritative once accepted. Rewrite the style catalog's family table so it points to the compatibility matrix and does not imply image accepts all box properties. Ensure image's allowed set is exactly width, height, margin, border components/shorthand, and border-radius.


### A-05 — `display` compatibility must be consistent across section/container

**Severity: High**

The compatibility matrix currently lists `display` as container-only, while layout catalog permits layout properties on both section and container and the latest correction intended `display` to be allowed on both. This discrepancy must be eliminated.

**Resolution proposed:** `display` is allowed on section and container only. Flex/grid property families are allowed on both, with their required explicit display mode. This is a matrix correction, not a new feature.


### A-06 — Reusable styles need a clear declaration context

**Severity: High**

The style syntax names a style after an element type (e.g. `paragraph style 1`), while the compatibility review recommends context-neutral style blocks and use-site validation. That recommendation is not aligned with element-typed style names.

**Resolution proposed:** For v0.1, styles should be element-kind scoped by their declaration name/type, and may only be applied to the matching Anzer element kind. Validate properties against that element kind at declaration and use-site. Cross-element style reuse is deferred. Alternatively, redesign styles to be genuinely context-neutral; do not keep the current mixed model.


### A-07 — Border shorthand default semantics are unclear

**Severity: High**

The style catalog and S36 state defaults as width=medium, style=none, color=currentcolor. But a shorthand such as `border="solid red"` cannot use `style=none` as the default without nullifying the explicitly supplied style. The stress test now correctly expects `medium solid red`, but the prose still describes generic CSS-compatible component defaults.

**Resolution proposed:** Make shorthand parsing component-aware: initialize omitted width to `medium`, omitted style to `none` only when no style token is provided (otherwise preserve explicit style), omitted color to `currentcolor`. This is not standard CSS shorthand behavior and must be described as Anzer's normalization algorithm or changed to CSS semantics. Recommendation: prefer CSS shorthand semantics for output and tests, avoid custom default rules.


### A-08 — `border-width` and `border-color` grammar are not fully specified

**Severity: Medium**

Catalog permits keywords for border-width but does not list them precisely; `currentcolor` is used as a default color but is not explicitly listed as an accepted color input. The border shorthand needs token classification to disambiguate color/width/style.

**Resolution proposed:** Specify width keywords (`thin`, `medium`, `thick`), whether `currentcolor` is accepted explicitly, token parsing, and whether multiple widths/colors are rejected. Recommendation: accept only one width token, one style token, one color token; allow `currentcolor` as a color keyword; reject duplicate components.


### A-09 — Max dimension keyword rules are vague

**Severity: Medium**

The style catalog says `none` is allowed for max-width/max-height “where specified by validation” but does not specify exact behavior. Min dimensions have no keyword support beyond numeric lengths.

**Resolution proposed:** Define `max-width` and `max-height` as nonnegative supported length or `none`; define min dimensions as nonnegative supported lengths only. Reject `auto` for min/max dimensions.


### A-10 — Style catalog's layout-property set is not complete or explicit

**Severity: Medium**

The style catalog points to the layout catalog, but the layout catalog has a broad Grid property list. The compatibility review groups properties without listing exactly which grid alignment properties and flex properties are included. It also does not distinguish common properties shared by flex/grid (e.g. gap) from family-specific properties.

**Resolution proposed:** Add a precise property-to-layout-mode table in the layout catalog and cross-reference it. Shared alignment properties must have explicitly documented allowed modes; grid-only properties must not be accepted under flex.


### A-11 — Grid track grammar and CSS length grammar overlap but are not reconciled

**Severity: Medium**

Grid tracks allow `auto`, lengths, percentages, `fr`, min-content, max-content, but the shared length parser supports friendly aliases, bare numbers default to px, and unitless zero. Grid tracks also permit `fr`, which is not part of the ordinary length-unit list.

**Resolution proposed:** Define grid-track parsing separately but reuse canonical length normalization for length/percentage tokens; explicitly define positive `fr` tokens, unitless bare numbers as px, and whether zero `fr` is rejected (current stress test says `0fr` rejected).


### A-12 — `gap` two-value order is undocumented

**Severity: Medium**

Layout catalog permits one or two values for gap, but doesn't state CSS row-gap/column-gap order, whether commas are forbidden, or whether friendly aliases and bare numbers are permitted for both tokens.

**Resolution proposed:** One or two whitespace-separated lengths only; two-value order is row-gap then column-gap; commas and expressions are rejected. Apply length normalization to each token independently.


### A-13 — Direct container text ordering remains open

**Severity: Medium**

Containers may have `text` and nested children. The element catalog proposes direct text first, but does not accept/freeze the order.

**Resolution proposed:** Direct `text` renders before child Anzer elements. HTML embeds are inserted at their exact source position. This is the simplest predictable model; test mixed content before acceptance.


### A-14 — HTML embedding is trusted and potentially unsafe

**Severity: High (security) / Medium (scope)**

Scoped raw HTML is accepted directionally, but it bypasses the native property catalog, can inject scripts/event handlers, can affect the global page, and may introduce invalid nesting. It is not sandboxed.

**Resolution proposed:** Keep `anzer use html` only for trusted author input, allowed within section/container, preserved at source position. Add a prominent security warning to docs and require explicit opt-in at compile/deploy/use. Do not treat it as sanitized or safe. If the first compiler cannot provide a trust acknowledgement, defer the feature rather than imply safety.


### A-15 — Button toggle target semantics and accessibility remain open

**Severity: High**

Toggle is restricted to section/container targets, but initial visibility, hidden state output, `aria-expanded`, label synchronization, and behavior for multiple buttons targeting one element are not defined.

**Resolution proposed:** Define initial state as visible unless the target has a native visibility property (currently none). Toggle must switch hidden/visible and synchronize `aria-expanded` on the triggering button. Multiple toggle buttons may target one container; each must reflect the target's current state. Toggle buttons must have a stable id or generated identifier. A no-action button is allowed, but output type should be explicit (default button type=button to avoid form submission).


### A-16 — URL validation and attribute escaping are open

**Severity: High**

Element catalog requires URL safety but has no accepted policy. `link.url` and `image.src` must be escaped at HTML output and scheme-validated; string rules alone do not provide security.

**Resolution proposed:** For links, allow relative URLs and `http`, `https`, and `mailto` schemes; reject `javascript`, `data`, and other schemes in v0.1. For image src, allow relative URLs and `http`/`https`; reject other schemes. Preserve text, but escape for HTML context. Whether protocol-relative URLs are allowed should be specified explicitly; recommendation: allow only if treated as relative network URLs or reject them for clarity.


### A-17 — Type override semantics need a matrix

**Severity: Medium**

The type allowlist is present, but interactions between element semantics, HTML attributes, accessibility, and content model are only summarized. For example paragraph type=DIV must not become a container; title H2-H6 must still be a leaf; section type=DIV remains a container.

**Resolution proposed:** Type override changes only emitted tag; never changes Anzer kind, allowed properties, required fields, child capability, or interaction semantics. Add tests for each allowed override and invalid override.


### A-18 — Image alt fallback can create misleading accessibility text

**Severity: Medium**

Filename-derived alt is better than missing alt only in limited cases. A filename such as `IMG_20261120_1234.jpg` becomes meaningless alt text.

**Resolution proposed:** Consider defaulting missing alt to empty alt (`alt=""`) for decorative/unknown images, and require explicit alt for informative images. If retaining filename fallback, make it a warning and never present it as accessibility-compliant. User decision needed.


### A-19 — Element property compatibility document needs matrix accuracy and semantics

**Severity: Medium**

The compatibility matrix currently allows dimensions, padding, and border properties across all non-image elements. This is technically possible but should be intentional for inline HTML types (e.g. paragraph rendered as P, link rendered as A). CSS properties may still apply, but some can have layout effects or interact with display defaults. The matrix also uses grouped rows that hide property-specific exceptions.

**Resolution proposed:** Expand matrix by individual property or define property groups precisely. Ensure image is excluded from text/padding/min-max and layout. Confirm display on section and container only.


### A-20 — `display=none` and toggle behavior can conflict

**Severity: Medium**

Layout catalog accepts display=none, while toggle behavior controls visibility of target section/container. A target styled with display=none may initially be hidden; toggle runtime must preserve its authored display mode rather than overwrite it with arbitrary display values.

**Resolution proposed:** Define toggle as a hidden attribute/class strategy that preserves authored display style, not by rewriting display to block. Clarify how `display=none` interacts with initial toggle state. Prefer a native hidden attribute/state and a CSS strategy that doesn't permanently override author display.


### A-21 — Baseline CSS policy remains pending but affects semantics

**Severity: Medium**

The recommended baseline resets body margin, applies box-sizing globally, and makes images responsive. This affects dimensions, image layout, and browser defaults. It cannot be treated as an implementation detail.

**Resolution proposed:** Explicit user acceptance required before compiler output is frozen. If rejected, compiler emits no global baseline beyond required generated runtime styles.


### A-22 — Style test S36 shorthand expectation is correct, prose needs cleanup

**Severity: Medium**

The stress test expects `border="solid red"` to resolve to `medium solid red`. Catalog wording lists CSS-compatible defaults (style none) ambiguously and should be made consistent with component-aware parsing. Do not change test output silently.

**Resolution proposed:** Choose CSS shorthand semantics and document token defaults and parsing precedence, then align S36.


### A-23 — Source-location and recovery requirements are scattered

**Severity: Medium**

Grammar/property/string test notes require source locations and recovery, but there is no unified diagnostic contract. Error categories and severity are not frozen.

**Resolution proposed:** Add a diagnostic specification with categories (lexical, syntax, semantic, validation), line/column, severity, error recovery policy, and whether compilation aborts or continues. Require errors to prevent output generation unless safe partial output is explicitly defined.


### A-24 — v0.1 examples contain a `card` element that does not exist

**Severity: High**

This duplicates A-03 and affects grammar/layout/style stress examples. `card` should be a styled container unless accepted as a native element.

**Resolution proposed:** Update current stress suites and examples; don't add `card` implicitly.


## 4. Proposed decision set before freeze


### Immediate documentation corrections (no feature decision required)

1. Replace legacy `text-size` with `font-size` in property and grammar stress examples.
2. Replace unsupported `card` native elements with `container` or `section`.
3. Make section/container display eligibility consistent across all docs.
4. Make image compatibility rows explicit and restrictive.
5. Add a reconciliation note to the historical syntax audit.
6. Ensure style catalog references the compatibility review rather than implying image accepts all box properties.

### User decisions required

1. Reusable styles: element-kind scoped vs context-neutral. Recommendation: element-kind scoped.
2. Border shorthand grammar/defaults: CSS-compatible parsing. Recommendation: use CSS semantics.
3. `max-width`/`max-height` exact keywords. Recommendation: lengths or `none`; min dimensions only lengths.
4. Layout property-to-mode matrix and two-value gap semantics. Recommendation: explicit table; gap values are row then column.
5. Container direct text ordering. Recommendation: direct text before children; HTML insertions at source positions.
6. HTML embedding trust acknowledgment or deferral. Recommendation: defer if compiler cannot visibly warn/require trusted input.
7. Toggle semantics/accessibility and display preservation. Recommendation: define before implementation.
8. URL allowlists and protocol-relative URL handling. Recommendation: strict scheme allowlist.
9. Image alt policy. Recommendation: empty alt for unknown/decorative; explicit alt for informative images; filename fallback only as warning.
10. Global baseline CSS. Recommendation: explicitly accept/reject.
11. Diagnostics/recovery contract. Recommendation: define before parser implementation.

## 5. Reconciliation against accepted decisions

The user accepted the audit's recommended v0.1 decisions except image-alt policy. The following findings are therefore resolved at decision level and should not be treated as open user questions: A-04 through A-17, A-19 through A-23. A-02 is superseded by the explicit accepted `text-size` alias; A-03/A-24 are resolved by using `container` rather than a native `card` element. A-18 remains open by explicit user choice. A-01 is historical and superseded by newer records.


## 6. Corrections applied during this audit

The following documentation-only reconciliations were applied after creating this audit:

- Replaced legacy `text-size` with canonical `font-size` in property rules, property stress tests, and core grammar stress test.
- Replaced `card` element examples with `container` in the core grammar stress test; `card` is not a built-in element.
- Added a reconciliation note to the historical syntax audit, pointing readers to newer decisions and clarifying that the old HTML-embedding recommendation is superseded.

Commits: `3f969aa118e9206b1bb254a5a57d65df1cb6755d`, `4ea05f35099fe4e7d1f301c537f043336b8f2440`, `186e4d9de3df691bd12469e04fc587c47f536877`, `e3ec90b1b8b09bef650c06dc368572fe34bc2554`.


## 7. Reconciliation checklist

- [x] User decisions recorded in the freeze, except image-alt policy.
- [ ] Catalogs reference one another consistently.
- [ ] Stress-test examples use valid v0.1 names and current alias rules.
- [ ] Cross-document consistency checks are documented.
- [ ] Compiler tests are implemented later; specification suites are not runtime tests.

## 8. Final verdict

The decision freeze is now the controlling v0.1 record. Do not reopen accepted decisions unless a concrete contradiction or implementation blocker is found. The remaining image-alt policy is deliberately unresolved. Next work is documentation reconciliation and a consolidated specification, not compiler implementation yet.
