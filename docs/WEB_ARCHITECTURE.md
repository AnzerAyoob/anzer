# Web Architecture

## Target

The initial target is the browser, using existing web standards.

## Planned compilation outputs

For v0.1, the compiler emits a single self-contained HTML file. CSS is embedded, and the toggle runtime is embedded only when needed. The default filename is the source filename with `.html` substituted. Separate asset files are not the v0.1 output contract.

## Compatibility

Generated files should work on ordinary static hosting and in current browsers without an Anzer-specific browser plugin.

## Separation

The compiler should separate parsing, semantic validation, code generation, and diagnostics. Avoid mixing parser logic with output-writing code.
