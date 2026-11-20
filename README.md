# Anzer

**A unified language for the web.**

Anzer is an experimental programming-language project exploring a single, readable source format for web structure, styling, and behavior. Anzer source files use the `.anzer` extension and are intended to compile into standards-based HTML, CSS, and JavaScript that can run in ordinary browsers and be hosted anywhere.

> One language for structure, style and behaviour.

## Status

**Pre-alpha / language design.** The syntax, compiler architecture, and scope are still being designed. Examples in this repository are proposals, not implemented guarantees.

## Vision

- Keep structure, styles, and interaction together in a cohesive source file.
- Create syntax that is distinctive and easier to read than manually coordinating HTML, CSS, and JavaScript.
- Compile to web standards rather than requiring browser-native Anzer support.
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
