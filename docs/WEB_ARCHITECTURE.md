# Web Architecture

## Target

The initial target is the browser, using existing web standards.

## Planned compilation outputs

A build may produce:

- `dist/index.html`
- `dist/assets/anzer.css`
- `dist/assets/anzer.js`

The exact output layout is subject to implementation decisions.

## Compatibility

Generated files should work on ordinary static hosting and in current browsers without an Anzer-specific browser plugin.

## Separation

The compiler should separate parsing, semantic validation, code generation, and diagnostics. Avoid mixing parser logic with output-writing code.
