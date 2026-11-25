# Examples

Each runnable example is a complete Anzer v0.1 document. Save it as UTF-8 in a
writable directory and open the resulting `.html` file in your browser.
[Install Anzer and compile your first page](../README.md#compile-your-first-page)

## Apply a reusable style

Save as `styled-text.anzer`. The style sets the text color. The paragraph
supplies the content and references that style by its declared kind and ID.

```text
<anzer start>
anzer make paragraph style 1: color="#2563eb";
anzer make paragraph: text="A paragraph with a shared style.", use style="paragraph style 1";
<anzer end>
```

```bash
anzer check styled-text.anzer
anzer compile styled-text.anzer
```

## Toggle a section

Save as `toggle.anzer`. The button targets the section's `id`. Click it in the
browser to hide or reveal the section. Anzer emits the JavaScript for this
action when compiling the document.

```text
<anzer start>
anzer make button: text="Toggle details", action="toggle", target="details";
anzer make section: id="details" {
  anzer make paragraph: text="This section can be hidden or shown.";
}
<anzer end>
```

```bash
anzer check toggle.anzer
anzer compile toggle.anzer
```

[Toggle runtime contract](../docs/ANZER_V0_1_TOGGLE_RUNTIME_CONTRACT.md)

## Embed trusted HTML

Save as `embedded.anzer`. The HTML fragment is placed inside a section and
emitted without sanitization. Only compile embedded content you trust. Raw HTML
can execute scripts and affect the entire page.

```text
<anzer start>
anzer make section {
  anzer use html="<p>Written as <strong>HTML</strong>.</p>";
}
<anzer end>
```

```bash
anzer check embedded.anzer
anzer compile embedded.anzer --allow-trusted-html
```

[Trusted HTML and its warning behavior](../docs/ANZER_V0_1_CLI_CONTRACT.md#trusted-html)

## Historical design proposals

These files record earlier design scenarios and contain syntax outside v0.1.

- [Landing page](proposals/landing-page.anzer)
- [Article page](proposals/article-page.anzer)
- [Multilingual page](proposals/multilingual-page.anzer)
- [Cards layout](proposals/cards-layout.anzer)
- [Form interaction](proposals/form-interaction.anzer)

The article, landing, and multilingual proposals use the unsupported
`type="paragraph"` override. The landing proposal also uses unsupported
`background` and `on click` properties. Native cards, form inputs, and
arbitrary click handlers are outside v0.1.
[Syntax proposals](proposals/README.md) · [Supported v0.1 syntax](../docs/ANZER_V0_1_UNIFIED_SPECIFICATION.md)
