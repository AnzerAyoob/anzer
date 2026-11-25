# Anzer language specification · v0.1

This page points to the frozen references for the v0.1 language and compiler.
Earlier drafts and stress tests remain useful as design history.

## Authoritative documents

- [Unified language specification](../docs/ANZER_V0_1_UNIFIED_SPECIFICATION.md)
- [Language decision freeze](../docs/ANZER_V0_1_DECISION_FREEZE_1.md)
- [CLI contract](../docs/ANZER_V0_1_CLI_CONTRACT.md)
- [Toggle runtime contract](../docs/ANZER_V0_1_TOGGLE_RUNTIME_CONTRACT.md)
- [Grammar and compiler test checklist](../docs/ANZER_V0_1_GRAMMAR_TEST_CHECKLIST.md)

## Frozen compiler contract

- Source files use the `.anzer` extension.
- `anzer check input.anzer` validates the source.
- `anzer compile input.anzer` writes `input.html` beside the source by default.
  Use `-o output.html` to choose another destination.
- The compiler emits a complete HTML file with embedded CSS and JavaScript for
  native toggles when required. It publishes output only after successful
  analysis and rendering.

[Language overview](../docs/LANGUAGE_OVERVIEW.md) · [Runnable examples](../examples/README.md)
