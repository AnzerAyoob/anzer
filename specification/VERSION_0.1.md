# Anzer Language Specification — v0.1 (Design Draft)

**Status:** Proposal — not frozen, not implemented  
**Target:** Static/browser web pages  
**Source extension:** `.anzer`

This document proposes a small, testable language surface. It is deliberately limited to one-page web authoring. It does not define Anzer as a general-purpose language yet.

## 1. Goals

- One source file can describe page structure, visual styles, and basic interaction.
- Syntax should be cohesive and readable, not HTML/CSS/JavaScript with renamed keywords.
- Compile to ordinary HTML, CSS, and JavaScript.
- Generated output must be inspectable and hostable on static hosting.
- Keep v0.1 small enough to implement and test.

## 2. Non-goals

- Native browser support for `.anzer`.
- Server-side programming, databases, networking APIs, or package management.
- General-purpose loops, classes, modules, or user-defined functions.
- A custom runtime for simple pages.
- Guaranteed syntax compatibility beyond this draft.

## 3. Source file

- UTF-8 text.
- File extension: `.anzer`.
- One top-level `page` declaration per file.
- Whitespace and line breaks are not semantically significant except where required to separate tokens.
- Blocks use braces `{}`.
- Strings use double quotes. Escape sequences are proposed: `\\`, `\"`, `\\n`, `\\t`.
- Comments: `// line comment` and `/* block comment */`.

## 4. Proposed page structure

```anzer
page "My First Anzer Page" {
    section {
        heading "Hello, Anzer!"
        text "Structure, style and behavior in one source."

        button "Click me" {
            style {
                background: "#2563eb"
                color: "#ffffff"
                padding: 12
                radius: 8
            }

            on click {
                alert("Hello from Anzer!")
            }
        }
    }
}
```

This is a proposal. Element names, nesting, and property syntax may change after usability review.

## 5. Core constructs proposed for v0.1

### 5.1 Page

`page "Title" { ... }` declares the page and title. A page block contains content and optional global settings.

### 5.2 Content elements

Initial candidate elements:

- `section { ... }`
- `heading "text"`
- `text "text"`
- `paragraph "text"`
- `button "label" { ... }`
- `link "label" to "https://example.com"`
- `image "path" alt "description"`

The exact list is not finalized. Element nesting rules must be explicit.

### 5.3 Styles

Style declarations are allowed inside an element and apply to that element. Property names are CSS-like; values are Anzer literals.

```anzer
section {
    style {
        background: "#111827"
        color: "#ffffff"
        padding: 24
        align: center
    }
}
```

Initial value types:
- quoted strings
- numeric values (unitless)
- booleans, if a property requires them

The compiler must define unit handling. Draft rule: numbers are emitted as CSS numbers without units unless a property-specific rule or explicit unit string applies. Lengths can be written as quoted CSS strings such as `"20px"`, `"2rem"`, or `"10%"`.

### 5.4 Global style selectors

A proposed global style block:

```anzer
style {
    selector ".card" {
        background: "#ffffff"
        radius: 12
        padding: 20
    }
}
```

Global selectors are optional for the first implementation. If included, selector text is passed through to CSS after validation/escaping; it is not an expression.

### 5.5 Behavior and events

Event handlers are explicitly nested:

```anzer
button "Greet" {
    on click {
        alert("Hello!")
    }
}
```

Candidate v0.1 actions:
- `alert("message")`
- `console.log(...)`

These are only candidate actions. The initial compiler should support a very small, safe set and must not execute Anzer source during compilation.

## 6. Literals and identifiers

Proposed literals:
- string: `"text"`
- integer/decimal: `12`, `3.5`
- boolean: `true`, `false`

Identifiers are ASCII letters or underscore followed by letters, digits, or underscores. Unicode identifiers are deferred. This restriction does not apply to quoted text.

## 7. Parsing rules (draft)

The compiler should parse source into an AST, not generate output directly from token matches.

High-level grammar (illustrative EBNF):

```ebnf
program      = page_decl ;
page_decl    = "page" string block ;
block        = "{" statement* "}" ;
statement    = element | style_block ;
element      = "section" block
             | "heading" string
             | "text" string
             | "paragraph" string
             | "button" string block
             | "link" string "to" string
             | "image" string "alt" string ;
style_block  = "style" block ;
```

This grammar is incomplete: nested style and event blocks, property declarations, and expression rules must be formally specified before implementation.

## 8. Compilation model

Conceptual pipeline:

`Source → Lexer → Parser → AST → Validation → HTML/CSS/JS Generator → Files`

Suggested outputs:

- `dist/index.html`
- `dist/assets/anzer.css`
- `dist/assets/anzer.js`

A page without interactive behavior should not require a JavaScript output file. Generated files should be deterministic for identical source and compiler version.

## 9. Diagnostics

Errors should include:
- filename
- line and column
- clear explanation
- optional suggestion

The compiler should stop on syntax errors rather than emit partially broken output.

## 10. Security and escaping

- Text and attribute content must be HTML-escaped.
- CSS strings must be escaped and validated before emission.
- JavaScript strings must be safely encoded; do not concatenate raw source into generated JS.
- Anzer must not execute code during compilation.
- Arbitrary raw HTML and arbitrary JavaScript are out of scope for v0.1.
- External URLs and event actions require explicit syntax.

## 11. Minimum acceptance demo

A v0.1 compiler is considered demonstrable when it compiles one `.anzer` file into a valid page with:
- title and semantic structure
- at least two style declarations
- a button
- one click event that produces a visible result
- generated output that works in a modern browser on static hosting

## 12. Decisions still open

- Final names and grammar for elements.
- Whether global selectors are in the first release.
- CSS property mapping and unit rules.
- Supported event/action list.
- Accessibility defaults and semantic mapping.
- CLI shape and output path.
- Compiler implementation language.

## 13. Change policy

This draft is not a compatibility promise. Syntax changes are expected before the first implementation. Once a release is marked stable, changes should be documented in the changelog and specification version.
