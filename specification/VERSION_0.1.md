# Anzer Language Specification — v0.1

**Status:** Frozen for implementation. This file is a navigation/authority notice, not an independent specification.

The earlier draft in this file is superseded. It contained provisional grammar, unresolved decisions, and output assumptions that no longer match the v0.1 freeze.

## Authoritative documents
- [Unified specification: `docs/ANZER_V0_1_UNIFIED_SPECIFICATION.md`
- Decision freeze: `docs/ANZER_V0_1_DECISION_FREEZE_1.md`
- Definitive compiler test checklist: `docs/ANZER_V0_1_GRAMMAR_TEST_CHECKLIST.md`

Implement v0.1 against those documents. Historical syntax explorations and stress tests are supplemental test material only; they must not override the frozen specification.

## Frozen compiler contract
- Source: `.anzer`
- Check: `anzer check input.anzer`
- Compile: `anzer compile input.anzer [-o output.html]`
- Default output: `input.html`
- One self-contained HTML output; CSS embedded; JavaScript only when required.
- Compiler errors prevent output; no partial output.

The HTML output is a v0.1 browser-compatibility artifact, not a change to Anzer's long-term goal of becoming the primary author-facing web language.
