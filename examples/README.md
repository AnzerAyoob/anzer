# Examples

## Executable v0.1 example

Use the [first-page example in the README](../README.md#compile-your-first-page)
with the installed v0.1 CLI. Save and compile it in a directory outside the
checkout to keep the generated HTML with your working files.

## Historical design proposals

The files in [Syntax Proposals](proposals/README.md) record earlier design
scenarios. They contain unsupported syntax and should be read as historical
material.

- [Landing page](proposals/landing-page.anzer)
- [Article page](proposals/article-page.anzer)
- [Multilingual page](proposals/multilingual-page.anzer)
- [Cards layout](proposals/cards-layout.anzer)
- [Form interaction](proposals/form-interaction.anzer)

v0.1 supports paragraph style declarations such as `anzer make paragraph style 1:`
and references such as `use style="paragraph style 1"`. The article, landing,
and multilingual proposals use the unsupported `type="paragraph"` override.
The landing proposal also uses unsupported `background` and `on click`
properties. Native cards, form inputs, and arbitrary click handlers
are outside v0.1. Use the [v0.1 language specification](../docs/ANZER_V0_1_UNIFIED_SPECIFICATION.md)
for supported elements, properties, and actions.
