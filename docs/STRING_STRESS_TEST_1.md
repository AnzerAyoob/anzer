# String Stress Test 1

**Status:** Test draft — against accepted v0.1 string rules  
**Purpose:** Verify lexer behavior for strings and escapes. This does not test property parsing beyond string token boundaries.

## Accepted behavior under test

- Double quotes only.
- Accepted escapes: \\", \\\\, \\n, \\r, \\t.
- Unknown escapes are lexical errors.
- Raw physical newline inside a quoted string is invalid.
- Unicode is preserved.
- Structural punctuation inside strings is content.
- Escape decoding occurs once.

## Valid cases

### S1. Plain string

\`\`\`anzer
anzer make paragraph: text="Hello";
\`\`\`

Expected value: \`Hello\`.

### S2. Escaped quotation marks

\`\`\`anzer
anzer make paragraph: text="She said \\"Hello\\".";
\`\`\`

Expected value: \`She said "Hello".\`.

### S3. Literal backslash

\`\`\`anzer
anzer make paragraph: text="Folder\\\\File";
\`\`\`

Expected value contains one literal backslash: \`Folder\\File\`.

### S4. Newline escape

\`\`\`anzer
anzer make paragraph: text="First\\nSecond";
\`\`\`

Expected value contains a line-feed between First and Second.

### S5. Carriage return and tab

\`\`\`anzer
anzer make paragraph: text="A\\rB\\tC";
\`\`\`

Expected value contains CR between A and B and TAB between B and C.

### S6. Punctuation stress

\`\`\`anzer
anzer make paragraph: text="comma, semicolon; colon: braces {} brackets [] angle <> and marker <anzer end>";
\`\`\`

Expected: all punctuation and marker-like text are preserved; statement ends only after the quote and semicolon.

### S7. URL and query punctuation

\`\`\`anzer
anzer make paragraph: text="https://example.com/path?a=1&b=two#fragment";
\`\`\`

Expected: URL punctuation remains unchanged.

### S8. Unicode and mixed scripts

\`\`\`anzer
anzer make paragraph: text="السلام علیکم | नमस्ते | ಕನ್ನಡ | 😀";
\`\`\`

Expected: exact Unicode content is preserved.

### S9. Escaped backslash followed by n

\`\`\`anzer
anzer make paragraph: text="Literal sequence: \\\\n";
\`\`\`

Expected: output ends with the two literal characters backslash and n, not a line-feed. This confirms single-pass escape decoding.

### S10. Compact and multiline source equivalence

Compact:

\`\`\`anzer
anzer make paragraph: text="A,;{} <tag> \\"quoted\\"";
\`\`\`

Multiline:

\`\`\`anzer
anzer make paragraph:
    text="A,;{} <tag> \\"quoted\\"";
\`\`\`

Expected: same string value and same AST leaf.

## Invalid cases

### E1. Unterminated string

\`\`\`anzer
anzer make paragraph: text="Missing end;
\`\`\`

Expected: lexical error.

### E2. Unknown escape

\`\`\`anzer
anzer make paragraph: text="Unknown \\q escape";
\`\`\`

Expected: lexical error for unknown escape.

### E3. Raw newline inside string

\`\`\`anzer
anzer make paragraph: text="First line
Second line";
\`\`\`

Expected: lexical error at or before the physical newline.

### E4. Incomplete escape at end of string/source

\`\`\`anzer
anzer make paragraph: text="Trailing slash\\";
\`\`\`

Expected: incomplete escape / unterminated string lexical error.

### E5. Single quotes

\`\`\`anzer
anzer make paragraph: text='Single quoted';
\`\`\`

Expected: reject; single-quoted string syntax is not supported.

## Implementation checks

The test harness should compare decoded string values, not merely token counts.

- Escapes decoded once.
- Exact Unicode preservation.
- No truncation.
- Structural punctuation never leaks out of strings as syntax.
- Malformed strings yield lexical diagnostics with line/column where practical.
- Recovery should not consume unrelated later statements if safely recoverable.

## Out of scope

- Property type checking.
- HTML output escaping.
- JavaScript string escaping.
- URL validation.
- String interpolation.
- Multiline raw strings.
