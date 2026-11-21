# Element Catalog & Semantics Proposal 1

Status: **Proposal — awaiting review**  
Scope: Anzer v0.1

## Goal

Define a small, explicit set of elements that Anzer v0.1 can author. The catalog is intentionally limited. Supporting arbitrary HTML in v0.1 would expand the semantic surface, complicate validation, and weaken the promise of a consistent authoring language.

## Proposed catalog

| Anzer element | Default HTML output | Kind | v0.1 purpose |
|---|---|---|---|
| title | h1 | leaf | Main page heading |
| paragraph | p | leaf | Text content |
| button | button | leaf | Basic interaction target |
| link | a | leaf | Navigation to a URL |
| image | img | void leaf | Display an image |
| section | section | container | Group related content |
| container | div | container | Generic grouping/layout wrapper |

## Element kinds

- **Leaf** elements cannot contain child Anzer elements.
- **Container** elements may contain nested Anzer elements.
- **Void leaf** elements have no children and do not require content text.

The parser determines leaf/container shape from syntax (semicolon versus opening brace) rather than guessing from the element name. Semantic validation then rejects a mismatch (for example, opening a block for image).

## Default semantics and type overrides

Default output mapping is the catalog table above. A type override may select a compatible HTML tag, subject to a validation allowlist and element-specific constraints.

Proposal: allow type overrides only for title, paragraph, container, and section in v0.1. For title, allow heading levels H1 through H6; for paragraph, allow a limited text-flow set such as P, SPAN, and DIV; for container and section, allow DIV and SECTION. The exact compatibility matrix needs approval before implementation.

Do not permit arbitrary tag names, custom elements, script tags, or event-handler attributes through type.

## Proposed property expectations (semantic layer; property syntax is already accepted)

This is not a complete property catalog. It identifies likely required/optional properties for each element and leaves exact styling-property validation to a later proposal.

- title: text required; optional type, use style, and style properties.
- paragraph: text required; optional type, use style, and style properties.
- button: text required; optional use style, style properties, and a future interaction/action property.
- link: text and url required; optional use style and style properties.
- image: src required; optional alt, use style, and style properties. alt should be required by semantic/accessibility validation unless the author explicitly marks the image decorative (decorative syntax is not yet designed).
- section: optional id, use style, and style properties; children allowed.
- container: optional id, use style, and style properties; children allowed.

## Content model

Proposal: v0.1 elements use a single text property for plain text content. Text is not HTML and is never interpreted as markup. Child Anzer elements are permitted only inside container elements. This avoids ambiguous mixed-content behavior in v0.1.


Links use url; image uses src. These values are strings. URL safety and allowed schemes (for example, rejecting javascript:) must be specified in a security/semantic rules document.

## Semantic validation

A compiler should report errors for:

- unknown element names;
- element used with the wrong syntactic form (leaf vs container);
- required property missing;
- wrong property value type;
- incompatible type override;
- children inside leaf elements;
- text property on a container if the no-mixed-content proposal is adopted;
- unknown or unsupported semantic properties.

Do not silently drop invalid elements or properties.

## Open decisions

1. Approve, remove, or rename catalog elements.
2. Confirm title is always a main heading by default, or whether a separate heading element is preferable.
3. Decide whether container is needed alongside section.
4. Approve the limited type override matrix or defer type overrides in v0.1.
5. Confirm whether image requires alt in v0.1 and how decorative images are represented.
6. Confirm no mixed text/children in containers for v0.1.
7. Define button interaction syntax separately; button should not be considered functional until a supported action is specified.

## Recommendation

Keep the catalog small and validate it strictly. Avoid an html escape hatch in v0.1: it would undermine the safety, portability, and semantic guarantees of the language. Add new elements only when a real authoring use case and test cases justify them.
