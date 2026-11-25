# Anzer — Project Overview, Achievements & Roadmap

> **A declarative language for static web pages.**  
> Write structured `.anzer` documents, validate them with a compiler, and generate browser-ready HTML.

[GitHub repository](https://github.com/AnzerAyoob/anzer) · [PyPI package](https://pypi.org/project/anzer/) · [v0.1.0 release](https://github.com/AnzerAyoob/anzer/releases/tag/v0.1.0) · [Language overview](https://github.com/AnzerAyoob/anzer/blob/main/docs/LANGUAGE_OVERVIEW.md)

**Project status:** Anzer v0.1.0 is publicly released on GitHub and PyPI. Its compiler, command-line entry point, and initial static-page feature set are implemented and tested. The future plans below are proposals, not features included in v0.1.0 or delivery commitments.

---

## 1. What is Anzer?

**Anzer** is a small, declarative authoring language and compiler for creating static web pages. Rather than writing a complete HTML document and manually coordinating the related styling, an author writes a structured **`.anzer` source file** describing supported page elements, their properties, layout, and certain built-in interactions.

Anzer's compiler reads the source, checks whether it follows the language rules, and generates a standalone HTML document containing the required CSS and, where needed, a small fixed JavaScript runtime for native toggle behavior.

Anzer v0.1.0 is implemented primarily in **Python**. This does not mean that `.anzer` files are Python scripts: Anzer has its **own syntax, parser, semantic rules, and compilation process**. Python is the implementation language of the compiler; Anzer is the language that users author.

**In one sentence:** Anzer turns constrained, human-readable page declarations into validated, inspectable static web output.

### A simple example

Create `hello.anzer` using UTF-8 encoding:

```text
<anzer start>
anzer make title: text="Hello, Anzer!";
<anzer end>
```

Then run:

```powershell
python -m pip install anzer==0.1.0
anzer check hello.anzer
anzer compile hello.anzer
```

On ordinary success, both compiler commands are silent. The compilation generates `hello.html` alongside the source file, provided that the destination does not already exist. Open that HTML file in a web browser.

> [!NOTE]
> Anzer is currently a **command-line compiler**, not a drag-and-drop web design application or a hosted website builder.

---

## 2. Why does Anzer exist?

The web is built on powerful technologies—HTML, CSS, and JavaScript—but authoring them directly can require managing several layers of syntax, structure, and behavior. Anzer explores a different approach: describe a supported web page in a compact, declarative language, and let a compiler handle translation and validation.

The project's underlying motivations are:

1. **Simplify authorship.** Make common static-page structures expressible using consistent declarations rather than requiring an entire hand-written HTML document.
2. **Make errors discoverable.** Catch malformed source, unsupported properties, invalid values, and conflicting relationships before producing output.
3. **Keep generated pages understandable.** Produce HTML/CSS that can be opened, inspected, and distributed using ordinary web tooling.
4. **Favor predictable behavior.** Define explicit language and CLI contracts, use controlled transformations, and avoid implicit features that are difficult to reason about.
5. **Protect user files.** Refuse to overwrite an existing compilation destination rather than silently replacing it.
6. **Provide a foundation for growth.** Start with a well-defined static compiler, then expand only through reviewed language and tooling changes.

Anzer is **not intended to replace the entire HTML/CSS/JavaScript ecosystem** in its first release. Its current value lies in a deliberately narrower authoring model with strong validation and a small, defined feature set.

---

## 3. Who can use Anzer?

Anzer can be useful to:

- **Learners and experimenters** exploring how a custom language can produce web pages.
- **Developers** generating simple, structured static pages through a compiler-driven workflow.
- **Technical writers and maintainers** building small informational or documentation-style HTML pages.
- **Researchers and language-tooling contributors** studying parsing, immutable abstract syntax trees, semantic validation, rendering, and safe file publication.

Potential projects include simple personal introductions, informational pages, product or service descriptions, and sections that users can show or hide with native toggles. These are **use cases**, not promises of built-in templates, forms, hosting, or a content management system.

Anzer currently requires users to create and edit a `.anzer` file using a text editor and run the compiler from a terminal.

---

## 4. How Anzer works

Anzer follows a compiler pipeline rather than interpreting page declarations directly in a browser:

```text
UTF-8 .anzer source
        |
        v
  Lexical analysis
        |
        v
      Parsing
        |
        v
   Immutable AST
        |
        v
 Semantic validation
        |
        v
   Normalization
        |
        v
 HTML/CSS rendering
        |
        v
Safe output publication
        |
        v
      .html file
```

### Source and parsing

Anzer source documents have explicit start/end markers, element declarations, properties, and block structures for supported containers. The lexer and parser produce structured representations and diagnostics rather than treating Anzer as arbitrary Python or HTML.

### Immutable abstract syntax tree (AST)

The compiler represents parsed source using an **immutable AST**. This provides a stable structure for later validation and transformation and reduces accidental mutation across compilation phases.

### Semantic validation

The compiler checks rules beyond grammar, including supported element kinds and properties, typed values, reusable-style compatibility, identifiers, and native toggle target relationships. Errors are reported with structured diagnostic categories and codes, and source locations where available.

### Normalization and rendering

After successful validation, Anzer resolves effective values and produces browser-ready HTML with embedded CSS. For documents using native toggles, the compiler includes its defined JavaScript behavior. Ordinary native text is HTML-escaped.

### File publication

The compiler uses a no-overwrite output policy: it will not intentionally replace a pre-existing output entry. Its publication approach relies on filesystem hard-link support and documented assumptions about a stable destination directory. This is an important safety feature, **not a universal durability guarantee** across every filesystem and failure mode.

---

## 5. What Anzer v0.1.0 can do today

| Capability | Status in v0.1.0 | What it means |
| --- | --- | --- |
| `.anzer` documents | **Implemented** | Write source using Anzer's own document markers and declaration grammar. |
| Validation command | **Implemented** | `anzer check` validates a source file without creating HTML output. |
| Compilation command | **Implemented** | `anzer compile` produces a static HTML document. |
| Structured diagnostics | **Implemented** | Errors have defined categories/codes and locations when available. |
| Immutable AST | **Implemented** | Parsing produces an immutable source structure. |
| Typed properties | **Implemented** | Supported property values are checked against language rules. |
| Reusable styles | **Implemented** | Supported element kinds can reference declared styles. |
| Flex and grid layout | **Implemented within defined scope** | Validated layout properties are supported on compatible containers. |
| Native toggles | **Implemented** | Buttons can show/hide eligible sections or containers through a fixed runtime. |
| Trusted raw HTML | **Implemented with safeguards** | Raw HTML inside supported containers requires an explicit compile-time acknowledgement. |
| Safe output behavior | **Implemented with documented constraints** | Existing destinations are preserved rather than overwritten. |
| Windows and Linux testing | **Verified within tested environments** | Retained artifacts were tested on Windows and Ubuntu WSL; hosted CI covers Ubuntu and Windows. |
| Distribution on PyPI | **Published** | Install the released compiler with `python -m pip install anzer==0.1.0`. |

### Command-line interface

```text
anzer check INPUT.anzer
anzer compile INPUT.anzer
anzer compile INPUT.anzer -o OUTPUT.html
anzer compile INPUT.anzer --allow-trusted-html
```

- `check` validates the input without publishing output.
- `compile` writes HTML; by default, it replaces the supplied `.anzer` suffix with `.html` beside the input.
- `-o` / `--output` selects a destination; its parent directory must already exist.
- `--allow-trusted-html` acknowledges the security implications of raw HTML. The flag does **not** sanitize that content.

> [!WARNING]
> Trusted HTML is emitted as authored and may execute scripts or alter the page. Use it only for content you trust. Do not treat the acknowledgement flag as an HTML sanitizer or security sandbox.

### A native toggle example

The following is a supported kind of built-in interaction:

```text
<anzer start>
anzer make button: text="Toggle details", action="toggle", target="details";
anzer make section: id="details" {
  anzer make paragraph: text="This section can be hidden or shown.";
}
<anzer end>
```

Compile it using `anzer compile toggle.anzer`, then open the generated HTML and select the button.

For authoritative supported syntax, consult the [language specification](https://github.com/AnzerAyoob/anzer/blob/main/docs/ANZER_V0_1_UNIFIED_SPECIFICATION.md) and [runnable examples](https://github.com/AnzerAyoob/anzer/blob/main/examples/README.md).

---

## 6. What the project has achieved

### 6.1 Language and compiler foundation

Anzer has progressed beyond a language proposal into an implemented, installable compiler. Its v0.1 milestone includes:

- UTF-8 lexing and syntax parsing.
- An immutable AST and defined compiler stages.
- Semantic validation and normalization.
- Static HTML/CSS rendering.
- A constrained, reviewed native-toggle runtime.
- Explicit trusted-HTML policy.
- Structured CLI diagnostics and output-file safety rules.
- Frozen v0.1 language, decision, CLI, and toggle-runtime contracts.

These contracts define what v0.1 supports and help prevent documentation or future enhancements from silently redefining released behavior.

### 6.2 Testing and release verification

The v0.1.0 candidate was tested through multiple complementary methods:

- **Windows:** Exact retained wheel and source distribution exercised on Python 3.10 and 3.12.
- **Ubuntu 24.04 under WSL 2:** Exact retained artifacts exercised on Python 3.12, including normal isolated source-distribution installation, CLI tests, and filesystem checks.
- **Hosted GitHub Actions:** Python test matrix on Ubuntu and Windows, each with Python 3.10 and 3.12, with required browser tests.
- **Distribution integrity:** Wheel and source archive were retained, hashed, compared against their manifests, and verified after publication.
- **Real installation:** The public PyPI wheel was installed successfully on a Windows Python 3.12 environment; its `anzer`, `check`, and `compile` help commands launched correctly.

These are meaningful release checks, but the project does not claim every platform, browser, filesystem, or edge case has been tested.

### 6.3 Public release and packaging

**Version 0.1.0 has been publicly released:**

- The annotated `v0.1.0` Git tag identifies the approved release source commit.
- GitHub provides the retained wheel and source distribution as release assets.
- PyPI distributes `anzer==0.1.0` under the project name `anzer`.
- GitHub Trusted Publishing was configured for the PyPI release, using GitHub Actions rather than a long-lived PyPI API token in the repository.
- GitHub's default `main` branch was brought forward to the released source, and subsequently gained publication and documentation changes.

**Released source commit:** `5c342c654c36c55f6ac6694917c40e03c81f5bf3`

**Published distribution files:**

| File | Size | SHA-256 |
| --- | ---: | --- |
| `anzer-0.1.0-py3-none-any.whl` | 31,407 bytes | `68bac7c986a8f592f07ef16fd5f64c96cc15777bb935e39a492320d4d1b6e7f4` |
| `anzer-0.1.0.tar.gz` | 66,551 bytes | `4be5ec27e5af43cb96b7bba7e895a8afaf2e2849b1dca7ae6ab8acc6a1632b71` |

These historical release files are immutable publication artifacts; subsequent documentation changes do not update the content inside the existing PyPI wheel or sdist.

### 6.4 Documentation and public-facing presentation

After the package release, the project also completed a documentation refresh comprising:

- A redesigned GitHub README with installation and quick-start instructions.
- A clearer CLI reference and compiler pipeline overview.
- Runnable examples distinguishing supported behavior from historical proposals.
- Language overview and FAQ improvements.
- A contribution guide and links to frozen technical contracts.

The documentation redesign was merged into `main` after successful CI checks. It improves how newcomers encounter the project without changing the v0.1.0 compiler binary.

---

## 7. What Anzer does **not** provide yet

To set expectations clearly, Anzer v0.1.0 **does not include**:

| Not yet included | Current implication |
| --- | --- |
| Visual drag-and-drop page editor | Authors write `.anzer` source in a text editor. |
| Built-in preview/development server | Compile and open or refresh the HTML manually. |
| Hot reload | There is no automatic live browser refresh after edits. |
| Dedicated VS Code extension | No official Anzer editor extension is part of v0.1.0. |
| GitHub Linguist recognition | `.anzer` is not yet officially counted as a distinct GitHub language. |
| Website hosting or deployment | Users distribute or host generated HTML separately. |
| Database or backend server | The compiler generates static output, not server-side applications. |
| Built-in authentication or form processing | Login systems and server-side form handling require other technologies. |
| Arbitrary JavaScript event handlers | The supported native interaction is limited to the defined toggle feature. |
| Package manager or plugin ecosystem for Anzer | These are not v0.1.0 capabilities. |

Some older files in the repository may describe experimental syntax for cards, forms, and other features. Those **historical proposals are not evidence of shipped support**. Consult the frozen v0.1 specification and the runnable examples for the actual current language.

---

## 8. What should come next? — Proposed roadmap

The items below are **proposals for discussion and implementation**, not a published delivery schedule. Each new language feature would need design, implementation, tests, documentation, and an explicit compatibility decision before release.

### Phase A — Make Anzer easier to discover and learn

**Priority: High · Type: Documentation and developer experience**

- Maintain a consistent, accurate GitHub README and language guide.
- Expand examples into a small gallery of real, compilable pages.
- Add a beginner tutorial: install → write → check → compile → open.
- Provide helpful troubleshooting for UTF-8 encoding, filenames, paths, diagnostics, and output collisions.
- Clarify distinctions between released features and future ideas.
- Consider downloadable examples and a compact reference sheet.

**Success indicator:** A new user can install Anzer and compile a useful page without needing to inspect compiler source code.

### Phase B — First-class editor experience

**Priority: High · Type: Tooling**

- Create a TextMate grammar for `.anzer` syntax highlighting, with tests against valid and invalid sample programs.
- Add an Anzer VS Code language-support extension with file associations and useful editor configuration.
- Explore snippets, bracket matching, and diagnostics integration, based on actual language requirements.
- Establish a reproducible publishing and versioning process for the extension.

**Success indicator:** `.anzer` files are pleasant to edit in a mainstream code editor, without confusing Anzer syntax with Python or HTML.

### Phase C — GitHub language recognition

**Priority: Medium · Type: Ecosystem integration**

- Prepare representative `.anzer` samples drawn from valid language programs.
- Confirm current GitHub Linguist contribution requirements and adoption criteria.
- Propose Anzer recognition, including `.anzer` extension handling and syntax-highlighting grammar where required.
- Submit a contribution to [GitHub Linguist](https://github.com/github-linguist/linguist) when the evidence is sufficient.

**Important:** GitHub controls whether and when a new language is accepted. Anzer cannot force this recognition through a README badge or `.gitattributes` alone. Even after recognition, the compiler repository may remain predominantly Python because most of its implementation is written in Python.

**Success indicator:** GitHub can classify supported `.anzer` sources as Anzer when its upstream recognition process permits it.

### Phase D — Improve the authoring and feedback loop

**Priority: Medium · Type: User experience**

Investigate, without assuming they should all be included:

- A local preview command or development server.
- File watching and automatic recompilation.
- Clearer diagnostic presentation for editors and terminals.
- A formatting tool or consistent style conventions.
- Better project organization for multi-file authoring, if justified by real examples.

Design such features to preserve the existing `check` and `compile` contracts and the no-overwrite policy unless a future version explicitly documents a compatible alternative.

**Success indicator:** Creating and iterating on a page becomes faster without weakening compiler predictability or file safety.

### Phase E — Explore new language features responsibly

**Priority: Research · Type: Language evolution**

Candidate areas to investigate include:

- Additional native elements, when there is clear user demand.
- More expressive layouts and reusable styling.
- Improved accessibility and semantic HTML authoring.
- Better handling of assets and page metadata.
- Carefully scoped interaction features beyond toggles.
- Multi-page or reusable-component workflows, subject to a coherent design.

**No feature in this section is promised or implemented merely because it is listed here.** New syntax requires a reviewed language proposal, cross-platform implementation, compatibility analysis, security review, and tests. Historical proposals must not be presented as current functionality.

**Success indicator:** The language becomes more useful without turning into an inconsistent collection of shortcuts or abandoning its declarative character.

### Phase F — Strengthen releases, security, and contributor operations

**Priority: Ongoing · Type: Project maintenance**

- Keep automated testing across supported Python versions and operating systems.
- Expand artifact-level testing and browser coverage where practical.
- Maintain secure, reviewable GitHub-to-PyPI publication with exact-file verification.
- Keep distribution metadata, documentation, and published examples aligned with actual package releases.
- Review dependency and workflow security periodically.
- Document contribution, bug-reporting, and security-reporting processes.
- Record known limitations rather than overstating release guarantees.

**Success indicator:** Each future Anzer release can be explained, reproduced as far as its build process permits, and independently verified with clear evidence.

---

## 9. Suggested priorities for the next milestone

A practical near-term sequence is:

1. **Publish stronger user-facing examples.** Demonstrate several complete static pages that compile successfully with the released CLI.
2. **Introduce syntax highlighting.** Build a grammar and basic editor support before adding many new language features.
3. **Establish project visibility.** Improve tutorials and evaluate a GitHub Linguist contribution once enough genuine examples and adoption evidence exist.
4. **Collect real user feedback.** Identify which parts of authoring are difficult, which diagnostics are unclear, and which missing features matter most.
5. **Define the next language revision.** Select a small, coherent set of changes based on that evidence and publish an explicit compatibility plan.

The next numbered Anzer release should follow from implemented and tested improvements—not simply from a long feature wish list.

---

## 10. Principles for future development

Anzer's long-term direction should remain grounded in the qualities established by v0.1:

- **Clarity over magic:** Syntax and compiler decisions should be explainable.
- **Correctness before convenience:** Reject invalid declarations instead of generating surprising output.
- **Small, deliberate features:** Add functionality only when its semantics and tests are clear.
- **Security by explicit choice:** Preserve trust boundaries around raw HTML and browser interaction.
- **File safety:** Keep output-publication behavior predictable and documented.
- **Stable contracts:** Treat published specifications as versioned commitments.
- **Honest documentation:** Distinguish shipped, experimental, proposed, and unsupported capabilities.
- **Accessible contribution:** Make examples, errors, and development instructions understandable to newcomers.

---

## 11. How to get involved

Interested users and contributors can help by:

- Trying the released compiler and reporting reproducible issues.
- Sharing small, valid `.anzer` examples and generated output.
- Reporting unclear syntax or diagnostics.
- Improving tutorials and documentation.
- Proposing well-scoped language features with clear motivation and compatibility implications.
- Contributing tests for supported behavior and platform-specific edge cases.
- Exploring editor tooling and language recognition.

Start with the repository's [contribution guide](https://github.com/AnzerAyoob/anzer/blob/main/CONTRIBUTING.md), [issue tracker](https://github.com/AnzerAyoob/anzer/issues), and [current language specification](https://github.com/AnzerAyoob/anzer/blob/main/docs/ANZER_V0_1_UNIFIED_SPECIFICATION.md).

---

## 12. Project links

| Resource | Link |
| --- | --- |
| Source code | [github.com/AnzerAyoob/anzer](https://github.com/AnzerAyoob/anzer) |
| Released Python package | [pypi.org/project/anzer](https://pypi.org/project/anzer/) |
| v0.1.0 release notes and files | [GitHub release](https://github.com/AnzerAyoob/anzer/releases/tag/v0.1.0) |
| Getting started | [README](https://github.com/AnzerAyoob/anzer#compile-your-first-page) |
| Runnable examples | [examples/README.md](https://github.com/AnzerAyoob/anzer/blob/main/examples/README.md) |
| Language overview | [docs/LANGUAGE_OVERVIEW.md](https://github.com/AnzerAyoob/anzer/blob/main/docs/LANGUAGE_OVERVIEW.md) |
| Frozen language specification | [v0.1 specification](https://github.com/AnzerAyoob/anzer/blob/main/docs/ANZER_V0_1_UNIFIED_SPECIFICATION.md) |
| CLI contract | [v0.1 CLI contract](https://github.com/AnzerAyoob/anzer/blob/main/docs/ANZER_V0_1_CLI_CONTRACT.md) |
| Toggle runtime contract | [v0.1 toggle contract](https://github.com/AnzerAyoob/anzer/blob/main/docs/ANZER_V0_1_TOGGLE_RUNTIME_CONTRACT.md) |
| Issues and ideas | [GitHub Issues](https://github.com/AnzerAyoob/anzer/issues) |

---

## Closing perspective

**Anzer has completed its first significant milestone:** moving from a language design into a tested, documented, publicly installable compiler. Version 0.1.0 establishes the foundation—syntax, validation, deterministic compilation, controlled browser behavior, and distribution through GitHub and PyPI.

**The next milestone is usability and adoption.** Better examples, editing tools, language recognition, and carefully selected improvements can make Anzer more practical for everyday authors while preserving the engineering discipline of its first release.

*This document describes the Anzer v0.1.0 milestone and proposes future directions. The roadmap is informational and does not guarantee specific features or release dates.*
