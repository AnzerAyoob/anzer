# Anzer v0.1 CLI contract

This contract defines the command-line interface built on the compiler through Phase 9 and the parser checkpoint from Phase 10B-1. The [unified language specification](ANZER_V0_1_UNIFIED_SPECIFICATION.md), [language decision freeze](ANZER_V0_1_DECISION_FREEZE_1.md), and [toggle runtime contract](ANZER_V0_1_TOGGLE_RUNTIME_CONTRACT.md) remain authoritative for their respective behavior.

## Commands and help

```text
anzer check INPUT.anzer
anzer compile INPUT.anzer [ -o OUTPUT.html | --output OUTPUT.html ] [ --allow-trusted-html ]
anzer (-h | --help)
anzer check (-h | --help)
anzer compile (-h | --help)
```

Square brackets indicate an optional group, parentheses indicate a required group, and the pipe separates alternatives. Each operational command takes exactly one input path. `-o` and `--output` set the same value. If repeated, the last value wins. Repeating `--allow-trusted-html` has the same effect as supplying it once. Standard `argparse` value forms such as `--output=page.html` are accepted. `--` ends option parsing for the selected command. There are no stdin, stdout HTML, or overwrite modes. A bare `-` is a path argument with no special stream meaning.

The CLI uses `argparse` with program name `anzer`, a required subcommand, and long-option abbreviation disabled on the root parser and its subparsers. A missing or unknown command, missing operand or option value, extra operand, or unsupported option is a usage error. The parser prints usage and an error to stderr and exits with status `2`. In particular, `check` does not accept either output alias or the trusted HTML flag.

Help prints the relevant usage line to stdout, exits with status `0`, and opens no files.

```text
usage: anzer [-h] {check,compile} ...
usage: anzer check [-h] INPUT.anzer
usage: anzer compile [-h] [-o OUTPUT.html] [--allow-trusted-html] INPUT.anzer
```

Root help lists both commands. Check help describes validation without output. Compile help lists both output aliases, the default output name, and the no-overwrite policy. It describes `--allow-trusted-html` as explicit acknowledgement that embedded raw HTML can run scripts and affect the entire page. Standard `argparse` heading and wrapping differences across supported Python versions are permitted.

## Source loading and shared analysis

The CLI validates the input path, opens the source read-only in binary mode, and decodes it as strict UTF-8. It preserves the decoded characters and original line endings. A leading UTF-8 BOM decodes to U+FEFF and is passed through to the existing lexer. A decode failure is a source error with a zero-based byte offset into the original file.

Both commands use the same in-memory analysis routine in this order.

1. Create a `Source` with the decoded text and the input path as its display name.
2. Call `Lexer(source).tokenize()` to obtain tokens and lexical diagnostics.
3. Call `Parser(source, tokens).parse_document()` to obtain a `Document` and syntax diagnostics.
4. Call `SemanticValidator().analyze(document)` to obtain a `SemanticResult`.

Stop after the first stage that reports errors and retain all structured diagnostics from that stage in their returned order. The partial AST returned by a failing parse must not proceed to semantic analysis. A successful analysis returns the semantic result associated with the same AST instance. Command handlers share this routine and leave language rules in the compiler stages.

### Check

`check` ends after successful semantic analysis. It performs no normalization, rendering, output path handling, or output file creation. A successful check exits `0` with empty stdout and stderr. A semantically valid trusted HTML embedding passes without a flag or warning. Invalid placement remains a semantic error.

### Compile

`compile` starts with successful shared analysis before preparing the HTML output.

1. Normalize the original document with `normalize_document(document, semantic_result)`.
2. Apply the trusted HTML policy below to the normalized document.
3. Render the complete HTML string in memory with `render_document` and encode it as UTF-8 without platform newline translation.
4. Validate the output path and publish the finished bytes under the rules below.

Source and compiler errors take precedence over output filesystem errors. HTML bytes go only to the destination. Successful ordinary compilation is silent. Phase 9 toggle assets are emitted through the existing renderer according to the existing toggle runtime contract.

## Trusted HTML

Compilation with a valid trusted HTML embedding requires `--allow-trusted-html` on that invocation. Without the flag, report `security/TRUSTED_HTML_REQUIRED` at the start of the first embedding in document order, exit `1`, and create no output. The message identifies the flag and explains that embedded raw HTML can run scripts and affect the entire page.

The CLI passes `allow_trusted_html=True` to the renderer only when the flag is supplied. The renderer's existing acknowledgement guard remains in force. Semantic validation still applies, including the placement rules. Acknowledged fragments are emitted verbatim by the renderer.

After successful publication, a compile that emitted acknowledged trusted HTML reports exactly one `warning[security/TRUSTED_HTML_ENABLED]` on stderr at the first embedding. Supplying the flag for a document without an embedding produces no trust warning.

## Native path rules

| Area | Requirement |
| --- | --- |
| Source filename | The supplied filename must have a final `.anzer` suffix, matched case-insensitively on every platform. The OS still determines how the actual filename resolves. Validate the suffix before opening the file. |
| Source file type | The path must identify a regular file. Source hard links and symlinks to regular files are allowed. A dangling source symlink is missing input. Reject directories and special files. |
| Default output | Replace the final source suffix with lowercase `.html` in the supplied input path. For example, `pages/about.en.ANZER` produces `pages/about.en.html`. A source symlink uses the supplied link name and directory for this calculation. |
| Explicit output | Accept the supplied filename without changing its suffix. The working directory resolves relative inputs and explicit relative outputs. Accept native absolute paths, Unicode names, and names containing spaces. Shell quoting remains the caller's responsibility. |
| Output parent | The parent must already resolve to a directory. The CLI does not create missing directories. Directory symlinks and Windows junctions in parent paths may resolve normally. |
| Windows paths | Accept ordinary relative paths, fully qualified drive paths such as `C:\work\page.anzer`, and fully qualified UNC paths such as `\\server\share\page.anzer`. Interpret the drive or UNC anchor before validating ordinary components. Reject drive-relative paths such as `C:page.anzer`, current-drive-rooted paths such as `\page.anzer`, raw device and extended namespace prefixes, reserved device names, alternate data streams, and components with trailing dots or spaces other than the navigation components `.` and `..`. UNC output is subject to the same publication guarantees as local output. |

Linux uses its native path rules. The Windows restrictions do not impose Windows filename rules on Linux. Use the supplied spelling in diagnostics even when the OS resolves the path through an alias.

## Output safety

### Requirements

- An existing destination entry must be preserved. This includes regular files, directories, hard links, symlinks, and dangling symlinks.
- Report `output/OUTPUT_COLLISION` when the destination is provably the same file as the opened source, including hard-link and symlink aliases and case variants when the filesystem resolves them to the same file. Report `output/OUTPUT_EXISTS` for other existing entries. Only follow a destination's final symlink for identity diagnosis. Publication never writes through it.
- Publish only the complete rendered bytes using a supported atomic hard-link operation that fails if the destination name already exists. Only that operation decides whether the final name can be created. Preliminary checks are for diagnostics.
- If safe publication is unavailable, fail with `output/OUTPUT_ATOMIC_UNSUPPORTED` and preserve any existing destination. A detected concurrent creator is handled as an existing destination or a source collision when identity can be established.
- If publication reports an ambiguous result, treat it as successful only when a reliable identity check confirms the destination entry is a hard link to the staged file. Otherwise report `output/OUTPUT_PUBLISH` with exit `2` and leave any destination entry alone. An uncertain result must never be silently reported as success.
- Attempt to remove the staging name on every exit from publication. On failure before confirmed publication, retain the primary error and report a cleanup warning if removal also fails. After confirmed publication, a cleanup failure emits `warning[output/OUTPUT_CLEANUP]` with the leftover temporary path, preserves the destination, and leaves the exit status at `0`.

### Implementation guidance

For the source, check the regular-file type before reading and verify the opened file with `fstat`. Retain its identity for collision checks. Use filesystem identity comparisons for existing destinations and inspect final entries without following links when checking for existence or verifying publication.

Create an exclusive temporary file in the destination directory using `tempfile.mkstemp`. Write in binary mode, flush, sync, and close before calling `os.link(staged_path, destination)`. A write, sync, or close failure prevents publication. Same-directory staging keeps both names on the same filesystem under ordinary directory access. Delete only the staging name during cleanup. `os.replace`, replacement-capable rename, direct destination writes, and an existence check followed by a write cannot serve as fallbacks. [Python temporary-file API](https://docs.python.org/3.10/library/tempfile.html#tempfile.mkstemp) · [Python link and rename APIs](https://docs.python.org/3.10/library/os.html#os.link)

### Known limits

Hard-link availability depends on the filesystem and provider. Local Linux filesystems with hard-link support and Windows NTFS volumes are candidates. Some removable and network filesystems do not support this operation or cannot reliably report its outcome. An OS name or the presence of `os.link` alone does not establish support. Test native filesystem behavior on both Windows and Linux. [Linux link semantics](https://man7.org/linux/man-pages/man2/link.2.html) · [Windows hard-link API](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-createhardlinkw)

The guarantee covers concurrent creation of the destination filename in a stable directory. It assumes the user controls the source and output directories and their ancestors. Concurrent replacement of a parent directory, junction, or staging name is outside this guarantee. Sudden process termination can leave a staging file. Atomic visibility of the completed file does not provide a power-loss durability guarantee.

## Diagnostics and exit status

Command diagnostics go to stderr, one per line. For a compiler diagnostic, preserve the existing category, code, severity, and message. Use recorded one-based line and column when available. Omit both for diagnostics without a location. When a diagnostic lacks a code, render the category alone inside the brackets. Escape control characters in user-controlled paths and messages to keep each diagnostic on one line.

```text
input.anzer:2:7: error[syntax/PARDECL002]: Expected 'make' after 'anzer'
input.anzer: error[lexical/SOURCE_ENCODING]: Invalid UTF-8 at byte offset 18
missing.anzer: error[input/INPUT_NOT_FOUND]: Input file does not exist
private.anzer: error[input/INPUT_PERMISSION]: Permission denied reading input
output.html: error[output/OUTPUT_PERMISSION]: Permission denied publishing output
input.anzer: error[output/OUTPUT_COLLISION]: Output refers to the input file
output.html: error[output/OUTPUT_EXISTS]: Output destination already exists
input.anzer: error[compiler/INTERNAL_ERROR]: Internal compiler failure during rendering
```

For invalid UTF-8, use the decoder's zero-based byte offset without a line or column. Path failures name the relevant input or destination. A staging cleanup warning names the leftover staging path. Usage errors use the standard `argparse` format.

| Exit status | Meaning |
| --- | --- |
| `0` | Help, successful check, or confirmed publication. A post-publication trust or cleanup warning does not change this status. |
| `1` | Invalid UTF-8, lexical, syntax, semantic, or validation errors, missing trusted HTML acknowledgement, or an unexpected compiler failure. |
| `2` | CLI usage, missing or invalid path, permission, collision, existing destination, unsupported or uncertain publication, or other filesystem failure. |

| Category | Codes and boundaries |
| --- | --- |
| `lexical` | `SOURCE_ENCODING` for UTF-8 decoding failure. Existing lexer codes are preserved. |
| `syntax`, `semantic`, `validation` | Existing compiler codes and source locations are preserved. |
| `security` | `TRUSTED_HTML_REQUIRED` is an error before rendering. `TRUSTED_HTML_ENABLED` is a warning after successful publication. Both use the first embedding's location. |
| `input` | `INPUT_PATH` for an invalid path, suffix, or file type. `INPUT_NOT_FOUND` for missing input. `INPUT_PERMISSION` for denied access. `INPUT_READ` for other read failures. |
| `output` | `OUTPUT_PATH` for an invalid destination name. `OUTPUT_PARENT` for a missing or invalid parent. `OUTPUT_PERMISSION` for denied access. `OUTPUT_COLLISION` and `OUTPUT_EXISTS` for destination conflicts. `OUTPUT_WRITE` for other staging failures. `OUTPUT_ATOMIC_UNSUPPORTED` for unavailable safe publication and `OUTPUT_PUBLISH` for other publication failures or indeterminate outcomes. `OUTPUT_CLEANUP` is a warning for a leftover staging path. |
| `compiler` | `INTERNAL_ERROR` for an unexpected compiler-stage or output-encoding exception. Include the failing stage, with no fabricated location. |

### Exception handling

Translate expected path and filesystem exceptions at the operation that failed. Handle strict source decoding separately from input I/O. Translate unexpected exceptions only at the CLI boundary around compiler-stage calls and output encoding. Report the failing stage without raw Python exception text or a traceback in ordinary use. Existing library APIs retain their exception behavior. Let `argparse` handle help and usage exits. Allow process interrupts to propagate through cleanup. External process termination is outside the command exit-status contract.

## Acceptance tests

Use the existing `unittest` infrastructure, temporary directories, subprocess argument lists, and bounded timeouts. Inject race and failure conditions at defined operation boundaries without timing-dependent sleeps or user-specific paths.

| Area | Required cases |
| --- | --- |
| Arguments and help | Root and subcommand help, missing and unknown commands, extra operands, missing option values, unsupported flags and long-option abbreviations, `--`, both output aliases, and a repeated output option |
| Check and source errors | Silent valid source and valid trusted HTML, no normalization or output, strict malformed UTF-8 with byte offset, existing lexical/parser/semantic/validation diagnostics with real locations, and missing or invalid source paths |
| Compile | Default naming beside a nested input from a different working directory, explicit relative and absolute output, deterministic UTF-8 bytes, and no destination created on compilation failure |
| Trusted HTML and toggle runtime | Refusal without acknowledgement, exact fragment with acknowledgement and one warning, rejection of illegal placement with either flag setting, and unchanged Phase 9 output and browser behavior |
| Filesystem and native paths | Unicode and spaces, mixed-case source suffixes, source symlink naming, valid Windows drive and UNC syntax, Windows path rejection cases, source/output identity through links, existing and dangling output entries, missing parents, permission failures, and staging write failures |
| Publication | A competing entry created immediately before publication, an unsupported filesystem, confirmed and indeterminate link results, and cleanup failures before and after publication. Assert that existing files and source bytes are preserved and no partial destination is exposed. |
| Installed launcher | Run `anzer` as a subprocess on Windows and Linux from a temporary working directory. Verify stdout, stderr, all three exit statuses, argument handling, and output bytes. Exercise native filesystem capabilities where available and use injected failures for portable error-path coverage. |

## Phase 10 implementation boundaries

- **10C** implements shared source analysis, CLI argument parsing, strict source loading, source diagnostics, exit-code mapping, and the complete `anzer check` command. It leaves the `compile` command unregistered until 10D. This phase adds no rendering or publication logic.
- **10D** adds `anzer compile`, trusted HTML acknowledgement and warnings, output path handling, staging, and atomic no-clobber publication.
- **10E** completes integration and verifies the installed launcher on Windows and Linux, including deterministic HTML output and preservation of the toggle runtime contract.
