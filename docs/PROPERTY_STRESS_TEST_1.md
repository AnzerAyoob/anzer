# Property Stress Test 1

**Status:** Specification stress suite for accepted property value rules; compiler execution pending  
**Scope:** Property parsing and value forms. Not a full semantic property catalog.

## Valid cases

These cases test syntax and value forms, not the full native style catalog. Property aliases and canonical duplicate behavior are covered in the style property stress suite.

### P1. Basic string property

\`\`\`anzer
anzer make paragraph: text="Hello";
\`\`\`

Expected: string value.

### P2. Multiple properties with required commas

\`\`\`anzer
anzer make paragraph: color="black", font-size="16px", text="Hello";
\`\`\`

Expected: three properties.

### P3. Compact and multiline equivalence

Compact:

\`\`\`anzer
anzer make paragraph: color="black", text="Hello";
\`\`\`

Multiline:

\`\`\`anzer
anzer make paragraph:
    color = "black",
    text = "Hello";
\`\`\`

Expected: equivalent properties and values.

### P4. Property ordering

\`\`\`anzer
anzer make paragraph: text="Hello", color="black";
\`\`\`

Expected: same meaning as P2 after property normalization.

### P5. Number values

\`\`\`anzer
anzer make card: opacity=0.5, spacing=12, count=3;
\`\`\`

Expected: numeric values, not strings.

### P6. Negative number

\`\`\`anzer
anzer make card: offset=-12, opacity=-0.5;
\`\`\`

Expected: numeric values accepted by lexer; semantic range validation may reject later.

### P7. Boolean values

\`\`\`anzer
anzer make button: disabled=true, visible=false;
\`\`\`

Expected: boolean tokens.

### P8. Quoted boolean-like strings

\`\`\`anzer
anzer make paragraph: text="true", title="false";
\`\`\`

Expected: strings, not booleans.

### P9. Empty string

\`\`\`anzer
anzer make paragraph: text="";
\`\`\`

Expected: empty string accepted.

### P10. Whitespace around equals

\`\`\`anzer
anzer make paragraph: text = "Hello";
\`\`\`

Expected: same as P1.

### P11. Style reference with ordinary properties

\`\`\`anzer
anzer make paragraph: use style="paragraph style 1", color="blue", text="Styled";
\`\`\`

Expected: style reference recognized as special property phrase; other properties parsed normally.

## Invalid cases

### E1. Missing comma

\`\`\`anzer
anzer make paragraph: color="black" text="Hello";
\`\`\`

Expected: syntax error; no implicit separator.

### E2. Missing equals

\`\`\`anzer
anzer make paragraph: color "black";
\`\`\`

Expected: syntax error.

### E3. Missing value

\`\`\`anzer
anzer make paragraph: text=;
\`\`\`

Expected: syntax error.

### E4. Uppercase name

\`\`\`anzer
anzer make paragraph: Text="Hello";
\`\`\`

Expected: property-name diagnostic.

### E5. Underscore

\`\`\`anzer
anzer make paragraph: text_color="black";
\`\`\`

Expected: property-name diagnostic.

### E6. Duplicate property

\`\`\`anzer
anzer make paragraph: color="red", color="blue";
\`\`\`

Expected: duplicate-property error, not first/last-wins.

### E7. Unsupported array

\`\`\`anzer
anzer make card: values=[1,2,3];
\`\`\`

Expected: unsupported value type in v0.1.

### E8. Unsupported null

\`\`\`anzer
anzer make card: value=null;
\`\`\`

Expected: unsupported value type.

### E9. Exponent notation

\`\`\`anzer
anzer make card: opacity=1e3;
\`\`\`

Expected: reject under proposed numeric grammar.

### E10. Uppercase boolean

\`\`\`anzer
anzer make card: visible=TRUE;
\`\`\`

Expected: reject; only lowercase booleans are recognized.

## Lexer/parser checks

- Property names and values should be distinct tokens.
- Whitespace outside strings should not change meaning.
- Commas are required between properties.
- Values must not be coerced between string/number/boolean.
- Duplicate properties within one declaration are diagnosed.
- String punctuation handling must remain consistent with accepted string rules.

## Deferred semantic checks

- Property-specific allowed types.
- Unknown property name handling.
- Numeric ranges (e.g. opacity).
- CSS/unit interpretation.
- Whether every element/property combination is valid.
