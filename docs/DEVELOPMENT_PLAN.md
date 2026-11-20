# Development Plan

## Step 1: Confirm specification v0.1
Agree on the smallest syntax that can express a page, styles, and one interaction.

## Step 2: Create compiler skeleton
Add CLI entry point, source reader, diagnostics, tests, and build directory conventions.

## Step 3: Parser
Implement the grammar and produce a syntax tree. Reject malformed source with useful errors.

## Step 4: Code generation
Generate HTML, CSS, and JS from the syntax tree. Add deterministic output tests.

## Step 5: First demo
Compile one example and verify the resulting page in a browser.

## Step 6: Developer command
Add a build command and then a local preview/watch command.

Do not add variables, loops, functions, modules, or a package system to the web compiler until the first end-to-end build works.
