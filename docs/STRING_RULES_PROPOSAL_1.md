# String Rules Proposal 1

**Status:** Proposed — not frozen  
**Scope:** Lexical string handling only. This proposal does not define property types.

## 1. String delimiter

Use double quotes for string values:

```anzer
anzer make paragraph: text="Hello, world!";
```

Single-quoted strings are not supported in the proposed v0.1 syntax. Avoid supporting two quoting styles without a clear benefit.

## 2. Escapes

Inside double-quoted strings, propose these escapes:

| Escape | Meaning |
|---|---|
| \\" | Literal double quote |
| \\\\ | Literal backslash |
| \\n | Line-feed/new line in string value |
| \\r | Carriage return |
| \\t | Tab |

Example:

```anzer
anzer make paragraph: text="She said \\"Hello\\".";
```

Example with a newline in the resulting text:

```anzer
anzer make paragraph: text="First line\\nSecond line";
```

Unknown escape sequences should produce an error in v0.1 rather than being silently rewritten or passed through unpredictably.

## 3. Structural punctuation inside strings

Commas, semicolons, braces, colons, and angle brackets are ordinary string characters when they occur inside a quoted string. They must not terminate properties, statements, or containers.

```anzer
anzer make paragraph: text="Punctuation: commas,; braces {} and tags <anzer end> are text.";
```

The lexer must recognize the string as one token before the parser interprets punctuation.

## 4. Multiline source formatting vs multiline string content

Source formatting may split a command across lines:

```anzer
anzer make paragraph:
    text="This string is on one logical line.";
```

But raw line breaks inside a quoted string are not proposed for v0.1. Use \\n explicitly:

```anzer
anzer make paragraph: text="Line one\\nLine two";
```

This avoids ambiguity about whether an accidental source newline ends, continues, or changes a string.

## 5. Unicode

Strings should accept Unicode text, including regional scripts and emoji, without requiring ASCII transliteration or escape sequences. Examples include Arabic, Urdu, Kashmiri, Sarazi, Bhaderwahi, and Devanagari text.

```anzer
anzer make paragraph: text="السلام علیکم — नमस्ते — नमस्कार";
```

The compiler must preserve valid Unicode string contents.

## 6. Proposed invalid strings

These should produce clear lexical diagnostics:

- Unterminated double quote.
- Trailing backslash before end of string.
- Unknown escape such as \\q.
- Raw newline before the closing quote.
- Invalid encoding (if the source file is not valid UTF-8).

## 7. Lexer expectations

- Strings are lexed as a single token.
- Structural punctuation inside strings is ignored by the structural parser.
- Escape decoding happens once, in the lexer/string-token stage.
- Diagnostics include line and column where practical.
- The compiler should not silently drop, replace, or reinterpret string characters.

## 8. Open decisions

- Whether to support raw strings or triple quotes in a later version.
- Whether string interpolation is ever supported.
- Whether escapes beyond the five listed are necessary.
- Whether source files must be UTF-8 strictly or a BOM is tolerated.

## Recommendation

Keep v0.1 strings simple: double quotes, a small documented escape set, Unicode, and no raw multiline strings. Stress-test this before accepting it.
