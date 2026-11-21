# Anzer v0.1 Decision Freeze — Record 1

Status: **User-approved v0.1 decisions recorded; implementation decisions finalized**
Scope: v0.1 language simplicity, grammar, semantics, styles, layout, elements, security, and implementation boundaries.

## 1. Language philosophy

Anzer v0.1 is intentionally a **simple, human-readable command language**. It should feel like writing normal text commands, not like learning a rigid programming language or memorizing technical vocabulary.

Where reasonable alternatives are clear and harmless, Anzer should accept friendly aliases and normalize them internally. Strictness should protect correctness and security—not force users to remember one exact spelling when another is equally understandable.

## 2. Accepted decisions

The user accepted the recommendations from the semantic consistency audit for v0.1, with the exception of image-alt policy.

- Reusable styles are **element-kind scoped**. A style may be applied only to the matching Anzer element kind.
- Border shorthand parsing follows CSS-compatible semantics. Component tokens are classified and duplicate components rejected; explicit component properties override shorthand components regardless of source order within the same declaration layer.
- `max-width` and `max-height` accept supported nonnegative lengths or `none`. Min dimensions accept supported nonnegative lengths only.
- Layout properties have explicit mode/property compatibility. Flex properties require explicit `flex` or `inline-flex`; grid properties require explicit `grid` or `inline-grid`. Shared gap properties require explicit flex or grid. Two-value `gap` uses row-gap then column-gap; values are whitespace-separated, not comma-separated.
- Container direct text renders before child Anzer elements. HTML embedding remains at its exact source position.
- Raw HTML embedding is trusted-author content only, not sanitized or sandboxed. It may execute scripts, use event handlers, add styles, and affect the wider page. It must be clearly warned about and require a trust acknowledgement in tooling. If that cannot be implemented visibly, HTML embedding must be deferred rather than presented as safe.
- Toggle behavior uses a hidden-state strategy that preserves authored display styling, synchronizes accessibility state, and defaults targets to visible. Buttons default to non-submit behavior. Multiple buttons may control the same target and must reflect its current state.
- URLs are validated by strict scheme allowlists: links allow relative, HTTP, HTTPS, and mailto; images allow relative, HTTP, and HTTPS. Reject javascript, data, and other unsupported schemes. Protocol-relative URLs are rejected for clarity. Attribute values/text are escaped in their HTML contexts.
- Type overrides change only the emitted tag; they do not alter Anzer element kind, required properties, allowed properties, child capability, or interaction semantics.
- Baseline CSS is accepted:
  ```css
  *, *::before, *::after { box-sizing: border-box; }
  body { margin: 0; }
  img { max-width: 100%; height: auto; }
  ```
  Do not globally set fonts, colors, heading/paragraph spacing, link styles, or button styles.
- Diagnostics must distinguish lexical, syntax, semantic, and validation errors; include source line and column; recover where safe; and prevent output generation when errors remain. No unsafe partial output is emitted in v0.1.

## 3. Friendly property names

Property spelling is normalized before semantic lookup: runs of spaces and hyphens are treated equivalently, so `font-style` and `font style` resolve to the same property. Defined friendly expanded names also resolve through an explicit alias table (for example, `minimum width` → `min-width`). Property names remain lowercase in v0.1; arbitrary synonyms are not accepted unless listed. Alias normalization happens before duplicate detection.

Both `font-size` and `text-size` are valid spellings and have identical meaning. Normalize `text-size` to `font-size` internally before duplicate detection.

Example:

```anzer
anzer make paragraph: text="Hello", text-size="18px";
anzer make paragraph: text="Hello", font-size="18px";
```

If multiple spellings of the same property are used in one declaration, they count as a duplicate canonical property and produce an error.

This alias is a deliberate simplicity choice. It does not imply unrestricted aliasing for other properties.

## 4. Image alt policy — unresolved

The user explicitly retains the existing filename-derived fallback when `alt` is omitted:

- remove the filename extension;
- replace hyphens and underscores with spaces;
- normalize to readable text.

The user recognizes this is a pragmatic fallback and not guaranteed to be accurate or accessible. This is the only decision from the audit's decision set that remains open for further discussion; do not replace it with empty-alt or required-alt behavior without user approval.

## 5. Implementation boundary

These decisions freeze the intended v0.1 behavior, not implementation quality. The compiler must still implement, test, and verify these rules. Stress tests are specifications until they are executed by an implementation. A decision freeze does not claim that Anzer v0.1 compiler exists or is ready.

## 7. Supersession

This document is the consolidated record of the user's v0.1 decisions. Older proposal and audit documents may retain historical statuses or recommendations; they should be reconciled to this record as a documentation cleanup task.
