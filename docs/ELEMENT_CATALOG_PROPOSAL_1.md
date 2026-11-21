# Element Catalog & Semantics Proposal 1

Status: **Accepted v0.1 decisions recorded; decision freeze is authoritative**  
Scope: Anzer v0.1

## Goal

Define a small, explicit set of elements that Anzer v0.1 can author. Supporting arbitrary HTML in v0.1 would expand the semantic surface, complicate validation, and weaken the language's consistency.

## v0.1 catalog

| Anzer element | Default HTML output | Kind | v0.1 purpose |
|---|---|---|---|
| title | h1 | leaf | Main heading |
| paragraph | p | leaf | Text content |
| button | button | leaf | Basic interaction target |
| link | a | leaf | Navigation to a URL |
| image | img | void leaf | Display an image |
| section | section | container | Semantic grouping |
| container | div | container | Generic structural/layout grouping |

## Accepted decisions

- `title` defaults to H1. `type` may select H2 through H6.
- Keep both `section` and `container`; they serve distinct semantic and structural purposes.
- `type` overrides are restricted to a compatibility allowlist; arbitrary tag names are not permitted.
- Image `alt` text is optional. When omitted, the compiler derives a fallback from the image filename: remove the extension, replace filename separators such as hyphens and underscores with spaces, and normalize it to readable text. This is a fallback only; filenames may not accurately describe the image.
- Containers support both direct text and nested Anzer elements.

## Element kinds and syntax

- **Leaf** elements cannot contain child Anzer elements.
- **Container** elements may contain nested Anzer elements and direct text.
- **Void leaf** elements have no children and do not require text content.

Syntax determines shape: semicolon terminates a leaf; an opening brace starts a container. Semantic validation rejects shape mismatches (e.g. an image written as a container).


## Type override compatibility (allowlist proposal)

Proposed v0.1 compatibility:

| Element | Allowed type values |
|---|---|
| title | H1, H2, H3, H4, H5, H6 |
| paragraph | P, SPAN, DIV |
| section | SECTION, DIV |
| container | DIV, SECTION |
| button, link, image | No type override in v0.1 |

Tag values are case-insensitive at input and normalized internally. Output tags are lowercase. No arbitrary tags, custom elements, script tags, or event-handler attributes.

## Properties by element

- `title`: required `text`; optional `type`, `use style`, and style properties.
- `paragraph`: required `text`; optional `type`, `use style`, and style properties.
- `button`: required `text`; optional `action`, `target`, `use style`, and style properties.
- `link`: required `text` and `url`; optional `use style` and style properties.
- `image`: required `src`; optional `alt`, `use style`, and style properties.
- `section`: optional `id`, `text`, `use style`, and style properties; nested elements allowed.
- `container`: optional `id`, `text`, `use style`, and style properties; nested elements allowed.


## Button interaction in v0.1

To keep the language safe and predictable, Anzer does not accept user-written JavaScript or arbitrary event handlers. The initial button interaction is deliberately limited to toggling the visibility of a target container.


| Property | Rule |
|---|---|
| `action` | Required for an interactive button; currently only `toggle` is supported |
| `target` | Required with `toggle`; must be the `id` of a section or container |


Example:

```anzer
<anzer start>

anzer make button:
    text="Show details",
    action="toggle",
    target="details";


anzer make section { id="details"
    text="Additional details are shown or hidden when the button is activated."
}

<anzer end>
```

Compiler behavior: generate a button that toggles the target's visibility. The target must resolve to a section/container ID. Missing IDs, duplicate IDs, unresolved targets, unsupported actions, or targets of the wrong element kind are semantic errors. Generated behavior must not evaluate user-provided code or inject text as HTML. Accessibility behavior (including synchronized `aria-expanded`/target state where appropriate) must be specified and tested before implementation.


No arbitrary JavaScript, inline event handlers, alert actions, or multi-action sequences in v0.1. Links remain the navigation mechanism. JavaScript embedding is explicitly excluded from v0.1.

## HTML escape hatch (v0.1 — accepted scope)

Syntax: `anzer use html="...";`

- Allowed only inside `section` and `container` blocks.
- Inserts raw HTML at that exact position in the parent container.
- Cannot be used at document root or replace/override the entire Anzer document or compiler-generated page shell.
- Embedded HTML is not parsed as Anzer syntax.
- The compiler preserves embedded HTML as faithfully as possible.
- This is trusted author content, not a security sandbox. HTML may contain scripts, event handlers, CSS, or other browser features that can affect the wider page.
- Dedicated JavaScript embedding (`anzer use js`) is excluded from v0.1.

## Content model

Element text is plain text and is never interpreted as HTML. Containers may have both a `text` property and nested elements; generated output must define a consistent ordering. Proposal: render a container's direct text before its child elements. This ordering must be tested and documented. Link URLs and image sources are strings; URL scheme safety (e.g. rejecting `javascript:`) belongs in a security validation specification.

## Semantic validation

Report errors for:

- unknown element names;
- leaf/container syntax mismatch;
- required property missing;
- incorrect property value type;
- incompatible type override;
- children inside leaf elements;
- unknown or unsupported properties/actions;
- duplicate IDs;
- missing, unresolved, or invalid button targets;
- invalid URLs or unsafe schemes.

Do not silently drop invalid elements or properties.

## Remaining open decisions

1. Confirm container direct text ordering relative to nested children (proposal: direct text first).
2. Confirm button toggle semantics and accessibility behavior after reviewing this proposal.
3. Finalize URL validation and security rules.
4. Finalize the exact HTML/CSS compatibility behavior and test cases.

## Recommendation

Keep the catalog small and strict. Do not add an arbitrary HTML escape hatch in v0.1. Add elements and interactions only when a concrete authoring use case and test suite justify them.
