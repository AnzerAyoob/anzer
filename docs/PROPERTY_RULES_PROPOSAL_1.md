# Property Rules Proposal 1

**Status:** Proposed — not frozen  
**Scope:** Property names, separators, value types, duplicates, and ordering in v0.1.

## 1. Property shape

A property is written as:

\`\`\`
name=value
\`\`\`

Properties appear after the colon in an element/style declaration.

\`\`\`anzer
anzer make paragraph:
    color="black",
    text-size="16px",
    text="Hello";
\`\`\`

## 2. Separators

**Proposal: commas are mandatory between properties.**

- A comma separates property entries.
- A semicolon ends a leaf statement or style declaration.
- An opening brace starts a container body.
- Newlines and indentation are formatting, not separators.

Valid:

\`\`\`anzer
anzer make paragraph:
    color="black",
    text="Hello";
\`\`\`

Compact equivalent:

\`\`\`anzer
anzer make paragraph: color="black", text="Hello";
\`\`\`

Invalid (missing comma):

\`\`\`anzer
anzer make paragraph: color="black" text="Hello";
\`\`\`

Expected: syntax error; the parser must not guess where one property ends and another begins.

## 3. Property names

**Proposal: property names are case-sensitive and lowercase kebab-case.**

Examples: \`text\`, \`color\`, \`text-size\`, \`background-color\`, \`use style\`.

Names should start with a lowercase letter and use lowercase letters, digits, and hyphens thereafter. The style reference \`use style\` is a special property phrase and is not an ordinary property name.

Reject names with uppercase letters or underscores in v0.1 rather than silently normalizing them.

## 4. Value types

Proposal: allow three basic value forms:

### String
Double-quoted strings using the accepted string rules.

\`\`\`anzer
text="Hello"
color="#ffffff"
width="100%"
\`\`\`

### Number
Unquoted numeric values.

\`\`\`anzer
opacity=0.5,
count=3,
spacing=12
\`\`\`

Proposed numeric syntax: integer or decimal, optionally preceded by minus. No exponent notation in v0.1.

### Boolean
Unquoted \`true\` or \`false\` (lowercase only).

\`\`\`anzer
visible=true,
disabled=false
\`\`\`

Quoted \`"true"\` and \`"false"\` remain strings, not booleans.

No null, arrays, objects, or expression values in v0.1.

## 5. Property ordering

Property order is unrestricted. The same declaration with properties in a different order should have the same meaning, except that duplicate handling is an error (see below).

## 6. Duplicate properties

Proposal: duplicate property names within one declaration are an error.

\`\`\`anzer
anzer make paragraph: color="red", color="blue", text="Test";
\`\`\`

Expected: duplicate-property diagnostic. Do not silently use first or last value.

Style values and direct element properties are not duplicates: direct properties intentionally override style values according to the already proposed precedence.

## 7. Property value type validation

The lexer/parser recognizes string, number, and boolean value forms. Later semantic validation checks whether a particular property accepts that type.

For example, \`opacity=0.5\` may accept a number; \`text="Hello"\` accepts a string. A property receiving an incompatible value must produce a diagnostic.

## 8. Empty values

Empty strings are valid:

\`\`\`anzer
anzer make paragraph: text="";
\`\`\`

A missing value is invalid:

\`\`\`anzer
anzer make paragraph: text=;
\`\`\`

## 9. Whitespace

Whitespace around property names, equals signs, and values is insignificant outside quoted strings.

These are equivalent:

\`\`\`anzer
color="red"
color = "red"
\`\`\`

Whitespace inside strings is preserved.

## 10. Proposed invalid cases

- Missing comma between properties.
- Missing equals sign.
- Missing value.
- Uppercase property name.
- Underscore in property name.
- Duplicate property in a declaration.
- Unsupported value type (array/object/null/expression).
- Invalid numeric literal.
- Uppercase boolean \`TRUE\`/\`FALSE\`.

## 11. Open questions

- Whether hyphens are permitted at the end of names (recommend no).
- Property allowlist/catalog and property-specific type rules.
- Whether unknown property names are errors or warnings.
- How style declarations and element declarations share validation.

## Recommendation

Keep property syntax strict and small: mandatory commas, case-sensitive lowercase kebab-case, quoted strings, unquoted numbers, and lowercase booleans. Validate property-specific types separately. Do not accept implicit coercion.
