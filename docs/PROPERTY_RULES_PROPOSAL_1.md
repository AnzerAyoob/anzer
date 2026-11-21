# Property Rules Proposal 1

**Status: Updated to reflect v0.1 decisions; consolidated freeze record is authoritative**  
**Scope:** Property names, separators, value types, duplicates, and ordering in v0.1.

## 1. Property shape

A property is written as `name=value` and appears after the colon in an element/style declaration.

```anzer
anzer make paragraph:
    color="black",
    font-size="16px",
    text="Hello";
```

## 2. Separators

- A comma separates property entries.
- A semicolon ends a leaf statement or style declaration.
- An opening brace starts a container body.
- Newlines and indentation are formatting, not separators.

Compact and multiline forms parse identically. Missing commas are syntax errors; the parser must not guess property boundaries.

## 3. Property names and friendly aliases

Canonical property names are case-sensitive lowercase kebab-case. A name starts with a lowercase letter and uses lowercase letters, digits, and hyphens thereafter. The style reference `use style` is a special property phrase.

Anzer v0.1 intentionally accepts this friendly alias:

- `text-size` → `font-size`

Both spellings are valid and have identical meaning. Normalize aliases before duplicate detection. Using both `text-size` and `font-size` in one declaration is a duplicate-property error.

```anzer
anzer make paragraph: text="Hello", text-size="18px";
anzer make paragraph: text="Hello", font-size="18px";
```

This is not unrestricted aliasing. Other aliases must be explicitly listed in their relevant catalogs. Uppercase names and underscores are rejected in v0.1.

## 4. Value types

Allow three basic value forms:

- **String:** double-quoted strings using accepted string rules.
- **Number:** integer or decimal, optionally preceded by minus; no exponent notation in v0.1.
- **Boolean:** unquoted `true` or `false` only. Quoted booleans remain strings.

No null, arrays, objects, or expression values in v0.1.

## 5. Property ordering

Property order is unrestricted, except duplicate handling is an error.

## 6. Duplicate properties

Duplicate canonical property names within one declaration are errors. Alias normalization occurs first, so `text-size` and `font-size` together are duplicates.

Style values and direct element properties are not duplicates: direct properties intentionally override style values according to precedence.

## 7. Type validation

The parser recognizes string, number, and boolean forms. Semantic validation checks whether each property accepts that type. Incompatible types produce diagnostics.

## 8. Empty values

Empty strings are valid; missing values are invalid.

## 9. Whitespace

Whitespace around property names, equals signs, and values is insignificant outside quoted strings. Whitespace inside strings is preserved.

## 10. Invalid cases

- Missing comma between properties.
- Missing equals sign or value.
- Uppercase property name or underscore.
- Duplicate canonical property in a declaration, including aliases.
- Unsupported value type.
- Invalid numeric literal.
- Uppercase boolean `TRUE`/`FALSE`.

## 11. Status

The v0.1 property naming and value-form decisions are recorded in `ANZER_V0_1_DECISION_FREEZE_1.md`. Property catalogs define which properties exist and their semantic validation.
