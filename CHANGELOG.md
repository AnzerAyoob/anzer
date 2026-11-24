# Changelog

All notable changes to Anzer will be documented here.

## Unreleased (v0.1.0)

- Implemented UTF-8 lexing and parsing with an immutable AST, semantic
  validation, and normalization of properties and reusable styles.
- Added HTML and CSS rendering and a fixed JavaScript runtime for native
  toggles that preserves authored display and synchronizes controls.
- Added the `anzer check` and `anzer compile` commands, with source diagnostics
  and explicit acknowledgement and warnings for trusted HTML publication.
- Added atomic, no-clobber filesystem publication with output collision checks.
- Added package installation and launcher testing on Windows and Linux for
  Python 3.10 and 3.12. The mandatory Ubuntu browser gate requires at least
  eight cases and fails if a required browser case skips.
- Corrected numeric-token conversion failure to report `syntax/PARPROP003`
  and recover without treating the token as text.
- Rejected literal U+0000 in native IDs and toggle target references with
  semantic diagnostics. U+FFFD and other permitted Unicode remain valid.

### Project beginnings

- Project repository initialized.
- Initial vision and language-design documentation added.
