# Anzer

Anzer v0.1 is a command-style language for authoring web pages. Its compiler
turns a UTF-8 `.anzer` file into an HTML page with CSS and, when a toggle is
used, compiler-supplied JavaScript. Open the result in a regular browser.

## Install from source

Anzer requires Python 3.10 or newer. With a virtual environment activated,
run these commands from the root of your local Anzer Git checkout:

```sh
python -m pip install .
anzer --help
```

These commands install from the checkout and require no Anzer release on a
package registry.

## Compile your first page

Save this as `hello.anzer` in a directory where you can create files:

```anzer
<anzer start>
anzer make title: text="Hello, Anzer!";
<anzer end>
```

Run these commands from that directory:

```sh
anzer check hello.anzer
anzer compile hello.anzer
```

Open `hello.html` in your browser. By default, `compile` replaces the input
suffix with `.html` and writes beside the source. Set a different destination
with `-o` or `--output`. Relative output paths are resolved from the current
working directory, and the parent directory must already exist.

```sh
anzer compile hello.anzer -o greeting.html
```

`check` validates source without creating output. Ordinary successful checks
and compiles are silent. Source diagnostics go to standard error and include
the source path, category and code, and line and column when available.

The compiler refuses an output path that refers to the input or any existing
destination. It publishes the completed file atomically without overwriting a
destination created by another process. Publication requires hard-link support
in the output filesystem.

| Exit status | Meaning |
| --- | --- |
| `0` | Help, successful check, or successful publication |
| `1` | Source errors, missing trusted HTML acknowledgement, or compiler failure |
| `2` | Usage, path, or filesystem error, including output collisions |

## Trusted HTML

`anzer use html="...";` embeds explicitly authored raw HTML inside a
`section` or `container`. `check` validates its placement. Compiling a
file containing trusted HTML requires `--allow-trusted-html`. The compiler
emits the HTML as authored, so it can run scripts and affect the entire page.
Use the flag only when you trust the authored HTML.

```sh
anzer compile embedded.anzer --allow-trusted-html
```

A successful publication containing trusted HTML emits a warning on standard
error and exits with status `0`.

## v0.1 scope

Anzer supports a fixed set of native elements, typed style properties, reusable
styles, and flex and grid layout. Native button actions are limited to toggling a
`section` or `container` with a unique ID. Native IDs and toggle targets reject
literal U+0000. Native text is HTML-escaped.

The CLI provides `check` and `compile`. Open or refresh the generated file in
your browser after compiling. Development and preview servers, hot reload,
editor integration, an Anzer package manager, and deployment automation are
outside v0.1.

- [Language specification](docs/ANZER_V0_1_UNIFIED_SPECIFICATION.md)
- [CLI contract](docs/ANZER_V0_1_CLI_CONTRACT.md)
- [Executable and historical examples](examples/README.md)
- [Contributing](CONTRIBUTING.md)

Anzer is licensed under the [MIT License](LICENSE).
