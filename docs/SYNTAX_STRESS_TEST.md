# Anzer Syntax Stress Test

**Status:** Experimental syntax exploration. None of these examples are compiler-ready or grammar-ratified.

Purpose: test Anzer's command-oriented syntax against realistic web authoring patterns before implementation. These cases intentionally include syntax questions and should be reviewed for readability, consistency, ambiguity, parser feasibility, safety, and fallback behavior.

## Proposed container property rule under test

For this round, test a consistent pattern: a container may have a style reference and/or direct properties before its opening brace. The brace begins its child body. A semicolon ends a leaf command or style definition, not a container.

```
anzer make card use style="card style 1" {
    anzer make title: text="Card title";
}
```

Inline container properties:

```
anzer make card:
    background="white",
    padding="16px" {
    anzer make paragraph: text="Inside";
}
```

This placement is a proposal to test—not an accepted grammar rule.

---

## 1. Minimal page

```
<anzer start>
anzer make title: text="Hello, world!";
anzer make paragraph: text="My first Anzer page.";
<anzer end>
```

**Tests:** document boundaries, defaults, minimal authoring.

## 2. Heading hierarchy

```
<anzer start>
anzer make title: text="Main heading";
anzer make title: type="H2", text="Subheading";
anzer make title: type="H3", text="Smaller heading";
<anzer end>
```

**Tests:** semantic heading levels and whether the command name `title` remains natural for all levels.

## 3. Reusable styles

```
<anzer start>
anzer make paragraph style 1:
    font="Arial",
    color="#222222",
    text-size="16px";

anzer make paragraph use style="paragraph style 1": text="First paragraph";
anzer make paragraph use style="paragraph style 1": text="Second paragraph";
<anzer end>
```

**Tests:** numbered style declaration, style references, compact/multiline property syntax. (The mixed placement of `use style` is intentionally under review.)

## 4. Style plus direct override

```
<anzer start>
anzer make paragraph style 1:
    color="black",
    text-size="16px";

anzer make paragraph use style="paragraph style 1":
    color="red",
    text="This paragraph overrides the style color.";
<anzer end>
```

**Tests:** property precedence and whether applying a style and overriding properties is clear.

## 5. Nested sections

```
<anzer start>
anzer make section {
    anzer make title: text="About";
    anzer make paragraph: text="Introductory text.";

    anzer make section {
        anzer make title: type="H2", text="History";
        anzer make paragraph: text="History text.";
    }
}
<anzer end>
```

**Tests:** nested blocks, matching braces, indentation conventions.

## 6. Card with reusable style

```
<anzer start>
anzer make card style 1:
    background="white",
    padding="16px",
    shadow="soft";

anzer make card use style="card style 1" {
    anzer make title: type="H2", text="News";
    anzer make paragraph: text="Summary of the news.";
    anzer make link: url="/story", text="Read story";
}
<anzer end>
```

**Tests:** styled containers, child attachment, style syntax consistency.

## 7. Inline-styled container

```
<anzer start>
anzer make card:
    background="#ffffff",
    border="1px solid #dddddd",
    padding="20px" {
    anzer make title: type="H2", text="One-off card";
    anzer make paragraph: text="No separate style definition needed.";
}
<anzer end>
```

**Tests:** property placement before braces, inline style for containers.

## 8. Image and empty-content element

```
<anzer start>
anzer make image:
    src="/images/chenab.jpg",
    alt="Chenab river valley";
<anzer end>
```

**Tests:** leaf element syntax, required attributes, whether image is self-terminating via semicolon.

## 9. Link

```
<anzer start>
anzer make link:
    url="https://example.com",
    text="Visit website",
    target="new";
<anzer end>
```

**Tests:** URL property naming, target behavior, safe link defaults.

## 10. Form and inputs

```
<anzer start>
anzer make form {
    anzer make input:
        name="email",
        type="email",
        placeholder="Email address",
        required=true;

    anzer make button: text="Submit";
}
<anzer end>
```

**Tests:** form nesting, input void elements, boolean values, control types.

## 11. Multilingual and direction

```
<anzer start>
anzer make paragraph style 1:
    font="Arial",
    direction="ltr",
    text-size="16px";

anzer make paragraph style 2:
    font="Noto Nastaliq Urdu",
    direction="rtl",
    text-size="20px";

anzer make paragraph use style="paragraph style 1": text="English content";
anzer make paragraph use style="paragraph style 2": text="اردو متن";
<anzer end>
```

**Tests:** direction property, font naming, text encoding, RTL output.

## 12. Repeated content / lists

```
<anzer start>
anzer make list {
    anzer make list-item: text="First item";
    anzer make list-item: text="Second item";
    anzer make list-item: text="Third item";
}
<anzer end>
```

**Tests:** list semantics, child item restrictions, repeated commands.

## 13. Button and behavior

```
<anzer start>
anzer make button:
    text="Show message",
    action="alert",
    message="Hello from Anzer";
<anzer end>
```

**Tests:** behavior syntax. This example is intentionally speculative; the language should not expose unsafe arbitrary JavaScript as a default action.

## 14. Multiple nested containers

```
<anzer start>
anzer make page {
    anzer make header {
        anzer make title: text="Site name";
    }

    anzer make main {
        anzer make section {
            anzer make title: type="H2", text="Section";
            anzer make card {
                anzer make paragraph: text="Card body";
            }
        }
    }

    anzer make footer {
        anzer make paragraph: text="Footer";
    }
}
<anzer end>
```

**Tests:** nesting depth, semantic container mapping, indentation and closure readability.

## 15. Invalid syntax and diagnostics

These should be rejected with useful line/column diagnostics:

### Missing closing brace
```
<anzer start>
anzer make card {
    anzer make paragraph: text="Unclosed";
<anzer end>
```

### Extra closing brace
```
<anzer start>
}
<anzer end>
```

### Missing required image alt text (policy under consideration)
```
<anzer start>
anzer make image: src="/photo.jpg";
<anzer end>
```

### Duplicate style identifier
```
<anzer start>
anzer make paragraph style 1: color="black";
anzer make paragraph style 1: color="red";
<anzer end>
```

**Tests:** compiler errors, warning policy, source locations, validation rather than silent output.

## 16. Embeds and link previews

These are proposed commands for testing a simple author experience with provider-aware rendering. The syntax is not finalized, and provider support is not guaranteed for every URL.

```
<anzer start>
anzer embed tweet="https://social.example/post/123";
anzer embed drop="https://journoist.example/drop/123";
anzer embed video="https://video.example/watch/123";
anzer embed link="https://example.com/article";
<anzer end>
```

**Intended behavior under test:**
- `tweet`: render an embedded social post using an approved/provider-supported method, or show a fallback link.
- `drop`: render a Journoist Drop embed only if Journoist provides a supported embed contract.
- `video`: detect supported video providers and use the appropriate player/embed; unsupported URLs fall back to a link.
- `link`: show a link-preview card (title, description, image, and destination), distinct from a normal hyperlink.

**Tests:** provider detection, privacy/security, graceful fallback, and whether one generic embed command is understandable. “Support everything” means a simple syntax with an extensible provider layer—not a guarantee that every provider permits embedding. Arbitrary URL metadata fetching must be constrained to prevent SSRF and unsafe content.

## 17. Inline hyperlink inside text

```
<anzer start>
anzer make paragraph:
    text="Read {a-link="https://example.com/report", text="the report"} for details.";
<anzer end>
```

**Intended behavior under test:** render the phrase “the report” as an ordinary inline hyperlink within the paragraph, not as a standalone preview card or embed.

**Tests:** escaping and quote parsing, nested/inline token boundaries, link text, URL safety, and whether embedded property syntax inside a quoted text string is too parser-complex. Consider a simpler alternative if this inline syntax proves fragile.

---

## Review checklist

For each case, review:

1. Is the syntax understandable to a beginner without HTML/CSS knowledge?
2. Is the syntax consistent with the other cases?
3. Can a parser interpret it unambiguously?
4. Does it avoid unnecessary punctuation and repetition?
5. Does the syntax scale to more complex pages?
6. Are defaults intuitive and safe?
7. Does it encourage semantic and accessible output?

## Known problems to resolve after review

- Whether style references belong before the colon, inside properties, or both.
- Whether `anzer make paragraph use style=...` reads naturally.
- Exact inline property syntax for containers.
- How empty/void elements (image, input) terminate.
- Whether `text`, `url`, and other content properties can be shorthand positional arguments.
- Behavior/event syntax.
- Container names and their HTML mapping.
- Whether styles are global or scoped.
- Duplicate style handling.
- Required accessibility attributes and diagnostic severity.
- Embed provider registry, supported provider behavior, privacy/loading policy, and fallback design.
- Inline hyperlink grammar and escaping within text.
