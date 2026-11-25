# Contributing to Anzer

Anzer v0.1.0 has a published compiler and a frozen language specification. Start
with the behavior of the released CLI when reporting a bug or proposing a
change. [Language specification](docs/ANZER_V0_1_UNIFIED_SPECIFICATION.md) · [CLI contract](docs/ANZER_V0_1_CLI_CONTRACT.md)

## Before proposing changes

1. Check the current specification and the [decision log](docs/DECISIONS.md).
2. Describe the problem with a small `.anzer` document or CLI invocation.
3. Explain the expected behavior, trade-offs, and compatibility implications.

## Local development

Use Python 3.10 or newer. From the repository root, with a virtual environment
active, install the checkout and run the test suite.

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

The hosted test matrix also includes a required browser run for native toggles
on Ubuntu with Python 3.12. See the [test workflow](.github/workflows/tests.yml)
for its browser and Node.js prerequisites.

## Development principles

- Keep syntax explicit and behavior predictable.
- Keep generated HTML, CSS, and JavaScript inspectable.
- Document implemented behavior and cover compiler changes with tests.

## Issues and pull requests

Include the command, input, expected result, and observed diagnostics when
reporting a bug. For pull requests, describe the motivation, user-visible
changes, and validation performed.
[Issue tracker](https://github.com/AnzerAyoob/anzer/issues) · [Code of conduct](CODE_OF_CONDUCT.md) · [Security reporting](SECURITY.md)
