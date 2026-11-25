<h1 align="center">Anzer</h1>

<p align="center"><strong>A declarative language for static web pages.</strong></p>

<p align="center">Compile UTF-8 Anzer documents into HTML with embedded CSS and a small JavaScript runtime for native toggles.</p>

<p align="center">
  <a href="#compile-your-first-page">Quick start</a> ·
  <a href="#documentation">Documentation</a> ·
  <a href="examples/README.md">Examples</a> ·
  <a href="https://github.com/AnzerAyoob/anzer/releases">Releases</a> ·
  <a href="https://pypi.org/project/anzer/">PyPI</a>
</p>

<p align="center">
  <a href="https://pypi.org/project/anzer/"><img alt="PyPI version" src="https://img.shields.io/pypi/v/anzer?color=2563eb"></a>
  <a href="#installation"><img alt="Python 3.10 or newer" src="https://img.shields.io/badge/Python-3.10%2B-1d4ed8"></a>
  <a href="LICENSE"><img alt="MIT license" src="https://img.shields.io/badge/License-MIT-334155"></a>
  <a href="https://github.com/AnzerAyoob/anzer/actions/workflows/tests.yml"><img alt="Python Tests on main" src="https://github.com/AnzerAyoob/anzer/actions/workflows/tests.yml/badge.svg?branch=main"></a>
</p>

## Compile your first page

Install Anzer, then confirm the `anzer` command is available.

```bash
python -m pip install anzer
anzer --help
```

Save this UTF-8 document as `example.anzer` in a writable directory.

```text
<anzer start>
anzer make title: text="Hello, Anzer!";
<anzer end>
```

From that directory, validate the source and compile it.

```bash
anzer check example.anzer
anzer compile example.anzer
```

Open `example.html` in your browser. The compiler writes it beside the source by
default. Both commands are silent on ordinary success.

## What Anzer does

- **Structure and style.** Declare page elements, nest sections and containers,
  and apply typed properties, reusable styles, and flex or grid layouts.
- **Validation.** Parse strict UTF-8 into an immutable abstract syntax tree.
  Structured diagnostics identify the source path, error category and code,
  and line and column when available.
- **Browser output.** Generate a complete HTML file with embedded CSS. Native
  buttons can toggle a section or container with a unique ID. The compiler
  includes its fixed JavaScript runtime when native toggles are used.
- **Safe output.** Publish completed output atomically on filesystems that
  support hard links. An existing destination is preserved, including one
  created concurrently in a stable output directory.

### How it works

```text
Anzer source → Lexer → Parser → Immutable AST → Semantic validation
                                                       ↓
                                HTML/CSS output ← Normalization
```

`check` ends after semantic validation. `compile` continues through
normalization, applies the trusted HTML policy, then renders and publishes the
output.

## CLI reference

| Command or option | Behavior |
| --- | --- |
| `anzer check INPUT.anzer` | Validate source without creating output. |
| `anzer compile INPUT.anzer` | Replace the input suffix with `.html` and save beside the source. |
| `-o PATH` or `--output PATH` | Choose an explicit output path for `compile`. Relative paths use the current working directory. The parent directory must exist. |
| `--allow-trusted-html` | Acknowledge raw HTML for this `compile` invocation. |

```bash
anzer compile example.anzer -o greeting.html
```

Choose a new destination for each compile. Anzer refuses existing destination
entries and paths that alias the input. The publication guarantee assumes a
stable directory and requires hard-link support. See the [CLI contract](docs/ANZER_V0_1_CLI_CONTRACT.md#output-safety)
for filesystem limits and [exit statuses](docs/ANZER_V0_1_CLI_CONTRACT.md#diagnostics-and-exit-status).
Source diagnostics go to standard error.

### Trusted HTML

Native text is HTML-escaped. The `anzer use html="...";` statement embeds raw
HTML inside a section or container. `check` validates placement. `compile`
requires explicit acknowledgement and emits a warning on standard error after
a successful write.

> [!WARNING]
> Trusted HTML is emitted as authored. It can run scripts, inject styles, and
> affect the entire page. Use `--allow-trusted-html` only with content you trust.

Compile the [trusted HTML example](examples/README.md#embed-trusted-html) with
explicit acknowledgement.

```bash
anzer compile embedded.anzer --allow-trusted-html
```

## Language and examples

Every document starts with `<anzer start>` and ends with `<anzer end>`.
`anzer make` declares elements or styles. Sections and containers may hold
nested declarations in braces. A reusable style applies to its declared element
kind, and direct properties override its values.

Try the [reusable style](examples/README.md#apply-a-reusable-style) and
[native toggle](examples/README.md#toggle-a-section) examples, or browse the
[language overview](docs/LANGUAGE_OVERVIEW.md) for supported syntax.

## Installation

Anzer requires **Python 3.10 or newer** and declares no runtime dependencies.
The PyPI package installs the `anzer` console command. For a fresh install, the
unpinned command selects the latest compatible release. To follow these
examples with a specific version, pin v0.1.0.

```bash
python -m pip install anzer==0.1.0
```

### Install from source

With a virtual environment active, install from the root of a checkout at the
revision you want to use.

```bash
python -m pip install .
anzer --help
```

## v0.1 scope

Anzer v0.1 is a static compiler. Open or refresh the generated HTML in a browser
after compiling. Development and preview servers, hot reload, IDE integration,
deployment automation, plugins, and an Anzer package manager are outside the
release scope. The native toggle is the built-in interactive action.

## Documentation

| Start here | Reference |
| --- | --- |
| Learn the syntax and page model | [Language overview](docs/LANGUAGE_OVERVIEW.md) |
| Run a complete example | [Examples](examples/README.md) |
| Look up grammar, elements, and properties | [v0.1 specification](docs/ANZER_V0_1_UNIFIED_SPECIFICATION.md) |
| Check CLI behavior and filesystem guarantees | [CLI contract](docs/ANZER_V0_1_CLI_CONTRACT.md) |
| Understand native toggle behavior | [Toggle runtime contract](docs/ANZER_V0_1_TOGGLE_RUNTIME_CONTRACT.md) |
| Find answers and release notes | [FAQ](docs/FAQ.md) · [v0.1.0 release](https://github.com/AnzerAyoob/anzer/releases/tag/v0.1.0) |

## Contributing

For bug reports, include a small `.anzer` example and the command used. For a
language change, explain the compatibility implications.
[Contribution guide](CONTRIBUTING.md) · [Issues](https://github.com/AnzerAyoob/anzer/issues)

## License

Anzer is released under the [MIT License](LICENSE).

---

[GitHub](https://github.com/AnzerAyoob/anzer) · [PyPI](https://pypi.org/project/anzer/) · [Releases](https://github.com/AnzerAyoob/anzer/releases) · [Documentation](#documentation)
