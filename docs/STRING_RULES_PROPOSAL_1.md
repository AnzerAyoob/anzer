# String Rules Proposal 1

**Status:** Proposed — not frozen  
**Scope:** Lexical string handling only. This proposal does not define property types.

## 1. String delimiter

Use double quotes for string values:

\`\`\`anzer
anzer make paragraph: text="Hello, world!";
\`\`\`

Single-quoted strings are not supported in the proposed v0.1 syntax.

## 2. Escapes

Proposed escapes inside double-quoted strings:

| Escape | Meaning |
|---|---|
| \\" | Literal double quote |
| \\\\ | Literal backslash |
| \\n | Line-feed/new line in the resulting string |
| \\r | Carriage return |
| \\t | Tab |

Example:

\`\`\`anzer
anzer make paragraph: text="She said \\"Hello\\".";
\`\`\`

Example resulting in a line break:

\`\`\`anzer
anzer make paragraph: text="First line\\nSecond line";
\`\`\`

Unknown escapes should produce a lexical error rather than be silently rewritten.

## 3. Structural punctuation inside strings

Commas, semicolons, braces, colons, and angle brackets are ordinary characters inside strings. They must not terminate properties, statements, or containers.

\`\`\`anzer
anzer make paragraph: text="Punctuation: commas,; braces {} and tags <anzer end> are text.";
\`\`\`

The lexer must identify the complete quoted string before structural parsing.

## 4. Source newlines vs string newlines

Newlines may format source statements outside strings:

\`\`\`anzer
anzer make paragraph:
    text="This string is on one logical line.";
\`\`\`

Raw physical newlines inside quoted strings are not proposed for v0.1. Use the escaped sequence \`\\n\`:

\`\`\`anzer
anzer make paragraph: text="Line one\\nLine two";
\`\`\`

## 5. Unicode

Accept and preserve Unicode text (subject to valid UTF-8 source), including Arabic, Urdu, Kashmiri, Sarazi, Bhaderwahi, Devanagari, and emoji.

\`\`\`anzer
anzer make paragraph: text="السلام علیکم — नमस्ते — नमस्कार 😀";
\`\`\`

## 6. Invalid cases

Proposed lexical errors:

- Unterminated double-quoted string.
- Trailing backslash at end of string.
- Unknown escape (example: \`\\q\`).
- Raw newline before the closing quote.
- Invalid UTF-8 source.

## 7. Lexer requirements

- A string is one token.
- Structural punctuation inside a string is not structural.
- Escape decoding occurs exactly once.
- Diagnostics include line/column when practical.
- No silent truncation, substitution, or reinterpretation.

## 8. Deferred decisions

- Raw strings/triple quotes.
- Interpolation.
- Additional escapes.
- UTF-8 BOM policy.

## Recommendation

Keep v0.1 strings simple: double quotes, a small escape set, Unicode, and no raw multiline strings. Stress-test before acceptance.
