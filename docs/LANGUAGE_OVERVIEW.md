# Language overview

Anzer v0.1 is a declarative language for authoring static web pages. Write UTF-8
source in an `.anzer` file and open the compiled HTML in a browser.
[Compile your first page](../README.md#compile-your-first-page)

## Structure

Each document begins with `<anzer start>` and ends with `<anzer end>`. Use
`anzer make` to declare native elements. Properties follow a colon and use
comma-separated `name=value` pairs. A leaf declaration ends with a semicolon.
Sections and containers can enclose child statements in braces.
[Document structure and grammar](ANZER_V0_1_UNIFIED_SPECIFICATION.md#2-document-structure)

## Style and layout

Native properties are validated against the element that receives them.
Reusable styles are scoped to an element kind, and an element can reference one
style. Direct properties override reusable style values. Flex and grid layout
apply to sections and containers with a compatible `display` value.
[Reusable styles and layout](ANZER_V0_1_UNIFIED_SPECIFICATION.md#9-reusable-styles)

## Interaction and HTML

A native button can toggle a section or container by its unique ID. The
compiler includes a fixed JavaScript runtime for toggles and synchronizes the
button's expanded state with target visibility.
[Toggle runtime contract](ANZER_V0_1_TOGGLE_RUNTIME_CONTRACT.md)

Native text is HTML-escaped. Raw HTML fragments can be embedded inside a section
or container and require explicit trust acknowledgement when compiling.
[Trusted HTML policy](ANZER_V0_1_CLI_CONTRACT.md#trusted-html)

## Continue reading

- [Runnable examples](../examples/README.md)
- [Frozen v0.1 language specification](ANZER_V0_1_UNIFIED_SPECIFICATION.md)
- [CLI contract](ANZER_V0_1_CLI_CONTRACT.md)
- [FAQ](FAQ.md)
