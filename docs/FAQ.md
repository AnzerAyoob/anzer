# FAQ

## How do I install Anzer?

Use Python 3.10 or newer. `python -m pip install anzer` installs the published
package and its `anzer` console command.
[Install and compile your first page](../README.md#compile-your-first-page) · [PyPI](https://pypi.org/project/anzer/)

## Does a browser need to support Anzer?

A standard browser opens the generated HTML directly. Anzer embeds CSS and
includes compiler-supplied JavaScript for native toggles. The compiler only
runs when you check or compile the source.

## What can Anzer do today?

Version 0.1.0 compiles declarative page structure and styles to static HTML.
The CLI supports `check` and `compile`. It has no development server or hot
reload. The built-in interactive action is toggling a section or container.
[Language overview](LANGUAGE_OVERVIEW.md) · [v0.1.0 release](https://github.com/AnzerAyoob/anzer/releases/tag/v0.1.0)

## Is the syntax fixed?

The v0.1 specification defines the syntax supported by this release. Earlier
design proposals are preserved as historical examples.
[v0.1 specification](ANZER_V0_1_UNIFIED_SPECIFICATION.md) · [Examples](../examples/README.md)

## Why does compiling twice to the same path fail?

Anzer preserves existing destinations. Choose a new filename with `-o` or move
the existing output before compiling again. Safe publication requires an
existing parent directory on a filesystem that supports hard links.
[Output safety](ANZER_V0_1_CLI_CONTRACT.md#output-safety)

## Why does trusted HTML pass check but fail compile?

`check` validates where the raw fragment appears. `compile` requires
`--allow-trusted-html` because raw HTML is emitted as authored and can run
scripts or affect the entire page.
[Trusted HTML policy](ANZER_V0_1_CLI_CONTRACT.md#trusted-html)

## Is Anzer free?

Anzer is available under the [MIT License](../LICENSE).
