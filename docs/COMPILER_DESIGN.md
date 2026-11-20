# Compiler Design

A minimal compiler pipeline is proposed:

1. Read source text.
2. Lex/tokenize source.
3. Parse tokens into a syntax tree.
4. Validate constructs and report diagnostics.
5. Generate HTML, CSS, and JavaScript.
6. Write output files to a build directory.

The initial implementation language is undecided, though Python is a practical candidate for a zero-budget prototype.

The compiler should be testable without requiring a browser. Generated output can then be checked with fixtures and browser smoke tests.
