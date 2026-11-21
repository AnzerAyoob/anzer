# Anzer

**A language intended to unify web authoring—and ultimately replace HTML as the author-facing language.**

Anzer is an experimental language for describing web structure, styling, and behavior in one readable source file. Anzer source files use the `.anzer` extension.

## Vision

Anzer's long-term ambition is to become a complete web language and a practical alternative to writing HTML directly—not merely a shorthand that permanently depends on HTML as its authoring language.

That ambition is not yet achieved. The current early compiler milestone targets standard HTML, CSS, and JavaScript so Anzer documents can run in ordinary browsers and be hosted anywhere. Replacing HTML at the authoring level, and potentially through a dedicated runtime or browser ecosystem, is a longer-term goal requiring substantial design and implementation.

## Status

**Pre-alpha / language design.** The syntax, compiler architecture, and scope are still being designed. Examples in this repository are proposals, not implemented guarantees.

## Principles

- Keep structure, styles, and interaction together in a cohesive source file.
- Make the language distinctive, readable, and approachable without sacrificing precision.
- Treat HTML output as the current compatibility/compiler milestone, not the ultimate definition of Anzer.
- Start small, test every feature, and grow through a documented specification.

## Planned workflow

Eventually:

```sh
anzer build index.anzer
anzer dev
```

The first compiler milestone should generate a simple, working website from one `.anzer` file.

## Repository

- `specification/`: versioned language specification
- `docs/`: design, architecture, roadmap, and contributor documentation
- `examples/`: proposed and working examples, clearly labeled

## Contributing

The project is early. Read [CONTRIBUTING.md](CONTRIBUTING.md) and the [language design](docs/LANGUAGE_DESIGN.md) before proposing syntax or implementation work.

## License

MIT. See [LICENSE](LICENSE).
