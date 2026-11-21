# String Rules — v0.1

**Status:** Accepted for v0.1  
**Scope:** String delimiters and lexical handling. Property types remain a separate decision.

## 1. Quoting

Double quotes are the only string delimiter in v0.1. Single-quoted strings are not supported.

\`\`\`anzer
anzer make paragraph: text="Hello, world!";
\`\`\`

## 2. Accepted escape sequences

| Escape | Meaning |
|---|---|
| \\" | Literal double quote |
| \\\\ | Literal backslash |
| \\n | Line-feed/new line in resulting string |
| \\r | Carriage return |
| \\t | Tab |

Example:

\`\`\`anzer
anzer make paragraph: text="She said \\"Hello\\".";
anzer make paragraph: text="First line\\nSecond line";
\`\`\`

Escape decoding must happen exactly once.

Unknown escape sequences produce a lexical error.

## 3. Punctuation inside strings

Everything inside a valid quoted string is string content, not Anzer syntax. This includes commas, semicolons, braces, colons, angle brackets, and text resembling Anzer commands or document markers.

\`\`\`anzer
anzer make paragraph: text="Punctuation: commas,; braces {} and tags <anzer end> are text.";
\`\`\`

The lexer must consume the entire string token before structural parsing.

## 4. Newlines

Source statements may be formatted across physical lines. Raw physical newline characters inside quoted strings are not supported in v0.1.

Use the escaped sequence \`\\n\` to produce a newline in the string value:

\`\`\`anzer
anzer make paragraph: text="Line one\\nLine two";
\`\`\`

## 5. Unicode

Unicode text must be accepted and preserved, including scripts and emoji. Authors should not need transliteration or escape encoding.

\`\`\`anzer
anzer make paragraph: text="السلام علیکم — नमस्ते — नमस्कार 😀";
\`\`\`

The source encoding policy is UTF-8. Invalid UTF-8 is an error.

## 6. Invalid string cases

These must produce lexical diagnostics:

- Unterminated double-quoted string.
- Trailing backslash / incomplete escape.
- Unknown escape (e.g. \`\\q\`).
- Raw physical newline inside a string.
- Invalid UTF-8 source.

Errors should identify the location (line and column) where feasible. The compiler must not silently drop, replace, or reinterpret content.

## 7. Deferred

Not part of v0.1:

- Single-quoted strings.
- Raw strings or triple quotes.
- String interpolation.
- Additional escape sequences unless a concrete need is identified.
- Raw multiline strings.

## 8. Lexer requirements

- A string is a single lexical token.
- Structural punctuation is inert within strings.
- Escape decoding occurs once.
- String content is preserved faithfully.
- Malformed strings cause diagnostics rather than parser guessing.

## Decision

String rules are accepted for v0.1. This acceptance does not freeze property syntax, value types, or the entire grammar.
