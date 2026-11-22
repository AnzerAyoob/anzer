# Anzer v0.1 toggle runtime contract

## 1. Purpose and sources

Phase 9A extracted the requirements for the generated browser toggle runtime at checkpoint `5bcefbb`. Phase 9B records the two author-approved visibility decisions and the implementation plan. The frozen sources retain authority, and this companion contract records where the approved decisions clarify their application.

- **Unified** — [ANZER_V0_1_UNIFIED_SPECIFICATION.md](ANZER_V0_1_UNIFIED_SPECIFICATION.md), especially §§4–7, 9–11, and 13–17.
- **Freeze** — [ANZER_V0_1_DECISION_FREEZE_1.md](ANZER_V0_1_DECISION_FREEZE_1.md), especially §2 (lines 14–34) and §7 (lines 67–69). §2 records acceptance of the earlier audit recommendations with the stated image-alt exception.
- **Architecture** — [ANZER_V0_1_COMPILER_ARCHITECTURE_1.md](ANZER_V0_1_COMPILER_ARCHITECTURE_1.md), especially §§2, 9–12, and 16–20. It describes compiler boundaries and defers language behavior to Unified and Freeze.
- **Plan** — [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md), milestone steps 1, 4–5, and 7 (lines 7–10, 22–32, and 39–42). It assigns implementation and verification work.
- **Earlier audit** — [SEMANTIC_CONSISTENCY_AUDIT_1.md](SEMANTIC_CONSISTENCY_AUDIT_1.md), findings A-15 (lines 161–167) and A-20 (lines 206–212), and reconciliation §5 (lines 277–279). The accepted recommendations provide context through Freeze §2. Historical issue descriptions and proposed clarifications do not supply missing rules.
- **Supporting references** — [ELEMENT_PROPERTY_COMPATIBILITY_REVIEW_1.md](ELEMENT_PROPERTY_COMPATIBILITY_REVIEW_1.md), §§2–5, and [ANZER_V0_1_GRAMMAR_TEST_CHECKLIST.md](ANZER_V0_1_GRAMMAR_TEST_CHECKLIST.md), *Elements and semantics* and *Safety and output*.

**SPECIFIED** identifies a frozen rule. **APPROVED** identifies an author-approved Phase 9B decision. **IMPLEMENTATION DETAIL** identifies a choice that can satisfy the rule without changing language semantics. **UNSPECIFIED** identifies an outcome for which the frozen sources supply no rule. **CONFLICT** identifies a contradiction between frozen sources. The tables cite the source abbreviations above.

## 2. Syntax, targets, and validation

```anzer
<anzer start>
anzer make button: text="Details", action="toggle", target="details";
anzer make section: id="details", text="More information." {}
<anzer end>
```

| Topic | Status | Rule and reference |
|---|---|---|
| Declaration and placement | **SPECIFIED** | A toggle is a `button` leaf with `action="toggle"`. It uses the ordinary semicolon-terminated declaration and can occur at document scope or as a child in a `section` or `container`. The button itself cannot contain children. Unified §§5, 7.1–7.2, 11 (lines 60–82, 123–145, 303–314). |
| Required and optional properties | **SPECIFIED** | A button requires `text`. An ordinary button can omit `action` and `target`. For a toggle, the action requires a target. A button can use one kind-scoped reusable style and compatible style properties. Direct properties win over reusable style values. Unified §§7.1–7.2, 9, 11 (lines 125–145, 249–257, 303–314). |
| Target syntax and cardinality | **SPECIFIED** | `target` identifies one native `id` on a `section` or `container`. The example uses double-quoted strings under the ordinary property grammar. Duplicate canonical properties within one layer are errors. The grammar supplies no target list or expression and §11 excludes multi-actions. Unified §§4, 6, 7.2, 11, 17 (lines 42–58, 84–102, 137–145, 303–314, 374–387). |
| Existence, uniqueness, and errors | **SPECIFIED** | The target must resolve to a unique ID on a supported kind. Missing or duplicate IDs, unresolved targets, wrong kinds, and unsupported actions are semantic errors. An untargeted container may omit its ID. Errors prevent final output. Unified §§7.2, 11, 15–16 (lines 137–145, 307–309, 348–369), Architecture §9 (lines 199–224). |
| Nested targets and type overrides | **SPECIFIED** | Containers can nest. A nested `section` or `container` meets the same target eligibility rules. The HTML tag override does not change the Anzer kind. A paragraph emitted as `div` remains ineligible. Unified §§5, 7.1–7.3, 11 (lines 72–80, 123–161, 307–309). |
| A button targeting itself or another button | **SPECIFIED** | Neither can be the target. The source element for the action is a button and the target kind is restricted to `section` or `container`. A button inside its *ancestor* target is a different case. Unified §§7.2, 11 (lines 137–145, 307–309). |
| Several controls for one target | **SPECIFIED** | Multiple buttons may point to the same target. Each must reflect that target's current state. The ID is unique on the target even though multiple buttons reference it. Unified §11 (lines 307–313), Freeze §2 (line 24). |
| Forward references | **IMPLEMENTATION DETAIL** | The compiler can resolve references after collecting the document's IDs. The frozen requirement is successful resolution and gives no declaration-before-use rule. The current document-wide pass and tests accept forward references, including to a nested target. Unified §11 (lines 307–309), Architecture §9 (lines 214–216). |
| ID spelling and matching | **UNSPECIFIED** | **UNSPECIFIED BY FROZEN SPECIFICATION** beyond the string grammar, valid target kind, and unique, resolvable ID. The sources give no separate ID character grammar, trimming rule, or case-folding rule. Unified §§4, 6, 11 (lines 42–58, 84–94, 307–309), Architecture §9 (lines 214–216). |

### Current compiler observations

- The AST stores regular property assignments and child nodes. The parser uses the ordinary property and leaf/block syntax for buttons and targets. The property alias table has no toggle-specific alias. [AST](../src/anzer/ast.py#L30) · [Parser](../src/anzer/parser.py#L78) · [Property names](../src/anzer/property_names.py#L3)
- `action` and `target` are button properties, while `id` is restricted to section/container blocks. The validator requires strings, rejects blank IDs and targets, accepts the exact action spelling `toggle`, rejects a bare target, and compares the remaining ID strings exactly. It collects effective IDs after style resolution and checks references after the document walk. This describes the current implementation. [Property definitions](../src/anzer/semantic.py#L57) · [Reference pass](../src/anzer/semantic.py#L363) · [Element and toggle checks](../src/anzer/semantic.py#L505) · [Toggle validation tests](../tests/test_semantic_validator.py#L251)
- A read-only check confirmed that the current validator accepts a target with authored `display="none"`, a button inside its ancestor target, and an exact match for an ID with an embedded space. A case mismatch reports `SEMACT004`. A button given its own ID and named as its own target reports `SEMPROP001` and `SEMACT004`. These observations establish what the checkpoint accepts. The runtime behavior of the accepted edge cases is addressed below.

## 3. Runtime state and interaction

| Topic | Status | Rule and reference |
|---|---|---|
| Initial state | **SPECIFIED** with an **APPROVED** exception | Targets default to expanded. A target whose effective authored display is `none` starts collapsed under §3.1. Unified §11 (lines 310–311), Freeze §2 (line 24). |
| Activation, deactivation, and repeat | **SPECIFIED** | The one action switches its target between hidden and visible. A subsequent activation switches the same state back. This two-way behavior follows from the accepted A-15 hidden/visible rule. Unified provides one toggle action and no distinct show or hide command. Unified §11 (lines 305–314), Freeze §2 (lines 16 and 24), earlier audit A-15 (line 167), Architecture §12 (lines 280–285). |
| What changes and who shares it | **SPECIFIED** | The target's visibility changes through a hidden-state mechanism that preserves authored display. The action addresses one target. All buttons referencing it reflect the same current target state. The contract governs visibility and synchronized accessibility state, without a content-editing action. Unified §11 (lines 307–314), Freeze §2 (line 24). |
| Where state is stored | **IMPLEMENTATION DETAIL** | State can be represented on the target or tracked through equivalent generated metadata. Any representation must keep controls synchronized with the same target. No language-level state variable is introduced. Unified §11 (lines 310–314), Architecture §12 (lines 280–287). |
| Authored `display="none"` | **APPROVED** | Initialize the target collapsed and each associated control at `aria-expanded="false"`. First activation reveals it and reports expanded. A subsequent activation hides it and restores collapsed state. Preserve the authored value as specified in §3.1. |
| Nested state | **APPROVED** | Each target owns its state. Hiding or revealing an ancestor leaves the nested target's state and its controls' `aria-expanded` values unchanged. See §3.2. |
| Persistence | **UNSPECIFIED** | **UNSPECIFIED BY FROZEN SPECIFICATION** beyond initial and current state. Phase 9 initializes a freshly rendered document from the approved initial-state rule and adds no persistence. Unified §11 (lines 310–313), Freeze §2 (line 24). |

### 3.1. Authored display and visibility transitions

Here, *authored display* means the target's normalized effective `display` property. It may be supplied directly or by a reusable style. An omitted value stays omitted. *Own toggle state* is whether the target is hidden by its own toggle, independent of its CSS display value.

| Authored display | Initial state and ARIA | Expand a collapsed target | Collapse an expanded target |
|---|---|---|---|
| Omitted | Expanded, `aria-expanded="true"`. Use the element's normal display. | Remove toggle hiding and let normal display apply. Set all its controls to "true". | Apply toggle hiding. Keep display unspecified. Set all its controls to "false". |
| Any supported value other than `none` | Expanded, `aria-expanded="true"`. Use the authored value. | Remove toggle hiding and use the exact authored value, including flex, grid, inline, and inline-block. Set all its controls to "true". | Apply toggle hiding and preserve the authored value. Set all its controls to "false". |
| `none` | Collapsed, `aria-expanded="false"`. Preserve the authored `none`. | Remove toggle hiding and temporarily suppress the authored `none` declaration so normal browser display can apply. Keep `none` as the authored value in the record. Set all its controls to "true". | Apply toggle hiding and reinstate the authored `none` declaration if it was temporarily removed. Set all its controls to "false". |

The reveal exception for `none` is necessary because an effective CSS display of `none` cannot show the target. This uses the display that would apply without that declaration, with no hardcoded `display:block` and no inferred flex or grid layout. The exception applies to the compiler's own authored declaration. A hidden ancestor or other page CSS may still affect effective visibility.

### 3.2. Nested targets and shared controls

**Effective visibility** accounts for ancestor visibility. A nested target can remain expanded in its own toggle state while a collapsed ancestor keeps it from being seen. Its controls report its own state even if they sit outside that ancestor. Closing target A leaves target B and B's controls untouched. Reopening A exposes B according to B's previous state. This applies equally to a B that started collapsed and one that started expanded. There is no ancestor-state propagation, cascading reset, or nested-state synchronization. Controls share state only when they refer to the same target.

## 4. HTML and CSS representation

| Topic | Status | Rule and reference |
|---|---|---|
| HTML elements | **SPECIFIED** | Emit a native `button` with the non-submit `type="button"` default. Native target tags are `section` and `div` for the corresponding Anzer kinds, subject to their allowed tag overrides. Unified §§7.1–7.3, 11 (lines 125–161, 303–309), Freeze §2 (lines 24 and 26). |
| Control identity | **SPECIFIED** | A-15 calls for a stable ID or generated identifier for the control, accepted by reference through Freeze §2. Unified leaves `id` off the authored button property list. The requirement is for control identity, with no prescribed HTML representation. Unified §§7.2, 11 (lines 137–145, 307–313), Freeze §2 (lines 16 and 24), earlier audit A-15 (line 167). |
| Identifier and metadata spelling | **IMPLEMENTATION DETAIL** | The mechanism must find the validated target and distinguish controls as needed to synchronize them. A generated HTML `id` on each button and the attribute names `data-anzer-action` and `data-anzer-target` are implementation choices. Architecture §12 (lines 280–287). |
| Hiding mechanism and DOM representation | **IMPLEMENTATION DETAIL** | The frozen requirement is an independent hidden-state strategy that preserves authored display. A-20 prefers native hidden state and discusses an attribute or class. The freeze does not prescribe DOM retention, detachment, or removal. Keeping the target in place is one implementation option. Destroying content or changing other observable state would go beyond the visibility contract. Unified §11 (lines 310–313), Freeze §2 (line 24), earlier audit A-20 (line 212). |
| Baseline and animation | **SPECIFIED** for the existing baseline. **UNSPECIFIED** for animation. | The baseline remains box sizing, body margin, and responsive image rules. **UNSPECIFIED BY FROZEN SPECIFICATION** are transition or animation behavior, timing, and choreography. Unified §§11, 14 (lines 303–314 and 336–346), Freeze §2 (lines 27–33). |

Phase 7 carries the validated target ID and target property span in `ToggleAction`. Phase 8 emits an escaped HTML `id` on the target, escaped inert `data-anzer-action` and `data-anzer-target` on the button, the button type, and the authored styles. The existing renderer test verifies those attributes with an escaped ID and confirms no generated script. These attributes and the normalized record are implementation choices. [Normalized model](../src/anzer/normalize.py#L26) · [Normalized metadata test](../tests/test_normalizer.py#L287) · [HTML attributes](../src/anzer/render/html.py#L10) · [CSS renderer](../src/anzer/render/css.py#L8) · [Renderer test](../tests/test_renderer.py#L173)

## 5. Accessibility

External accessibility guidance informs the recommendations below. It does not amend the Anzer freeze.

| Topic | Classification | Phase 9 boundary |
|---|---|---|
| Native control and label | **Frozen specification requirement** | Use a native button with required plain text and `type="button"` to avoid form submission. Unified §§7.1–7.3, 11 (lines 125–161, 303–305). |
| Association and shared controls | **Frozen specification requirement** | Each button controls one validated target. All controls for a target reflect its current state. The runtime must have an unambiguous association, and the identifier format remains an implementation choice. Unified §11 (lines 307–313), Freeze §2 (line 24), earlier audit A-15 (line 167), Architecture §12 (lines 280–287). |
| `aria-expanded` | **Frozen specification requirement** and **Approved language/runtime decision** | The freeze requires synchronized accessible state, including `aria-expanded`. Initialize every control and update all of a target's controls after either transition. The approved interpretation is `true` for the target's own expanded state and `false` for its own collapsed state, regardless of hidden ancestors. Unified §11 (lines 310–313), Freeze §2 (line 24). |
| Keyboard activation | **Accessibility recommendation** | Handle the native button's activation event for both pointer and keyboard use. Verify Enter and Space on a focused button. Custom key handlers are outside this boundary. [WAI-ARIA APG disclosure keyboard interaction](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/#keyboard-interaction) |
| Focus when hiding | **Accessibility recommendation** | Preserve focus if it is already outside the collapsing subtree. If focus is inside, the minimal proposed safeguard is to focus the activating button before hiding, only if that button is outside the subtree and still visible and focusable. This is an implementation detail for the existing control. Where no such initiating control remains available, use the browser's native focus handling. |
| Focus policy beyond the safeguard | **Unresolved question** | **UNSPECIFIED BY FROZEN SPECIFICATION** are a guaranteed destination when the initiating control will also be hidden, automatic focus on reveal, and restoring the previously focused descendant. These behaviors need author approval if introduced. The bounded safeguard above does not require a new language rule. Unified §§7, 11 (lines 123–161, 303–314). |
| Screen readers | **Accessibility recommendation** | Expose native button semantics, the current expanded state, and ordinary hidden content behavior. Verify these in the accessibility tree. **UNSPECIFIED BY FROZEN SPECIFICATION** are spoken phrasing, announcement timing, and label changes. Phase 9 promises no custom announcements. [WAI-ARIA APG disclosure semantics](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/#wai-aria-roles-states-and-properties) |
| `aria-controls` and additional ARIA | **Accessibility recommendation** | `aria-controls` is supported and optional for disclosures, and can be appropriate if it can reference one valid, unique DOM ID. The Anzer freeze does not require it. The Phase 9 plan omits it because the runtime association already identifies the target and current Anzer IDs can contain whitespace. No extra role, `aria-hidden`, `aria-pressed`, or live region is justified for this plan. Unified §11 (line 312), Architecture §12 (line 284). [WAI-ARIA APG disclosure semantics](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/#wai-aria-roles-states-and-properties) · [HTML ID requirements](https://html.spec.whatwg.org/multipage/dom.html#the-id-attribute) |

## 6. Security and implementation boundaries

- **SPECIFIED** — Validate authored target IDs and references upstream. Escape attribute values in their HTML context and safely reference the validated target ID. Render the validated normalized model and suppress final output on errors. Unified §§11, 15–16 (lines 307–314, 348–369), Architecture §§9, 11, 16, 19 (lines 199–224, 248–261, 343–349, 422–434).
- **SPECIFIED** — The compatibility output includes minimal, compiler-generated toggle behavior only when the document uses a toggle. The project intends embedded JavaScript for browser behavior and does not require authors to supply any script. Arbitrary user code, event handlers, alerts, multi-actions, and dynamic expression evaluation are excluded. Unified §§11, 16–17 (lines 303–314 and 358–387), Architecture §§12, 20 (lines 280–287 and 438–441), Plan step 5 (lines 27–32).
- **IMPLEMENTATION DETAIL** — The sources require safe target lookup. They prescribe no DOM API, listener arrangement, or executable source template. The authored ID is input data to the relationship, with no authority to become executable code. The checkpoint already emits it as escaped attribute data. Architecture §§12 and 19 (lines 280–287 and 422–434), [HTML renderer](../src/anzer/render/html.py#L44).
- **SPECIFIED** — Trusted HTML is a distinct, acknowledged escape hatch that can affect the page. It supplies no native action syntax and does not relax the native runtime's safety requirements. Unified §§13, 16–17 (lines 324–334 and 358–387), Freeze §2 (lines 23–25), Architecture §19 (lines 425–433).
- **IMPLEMENTATION DETAIL** — The architecture separates HTML rendering, CSS rendering, and runtime generation. Phase 9's implementation boundary is generated toggle behavior and accessibility state for the validated model. The CLI is a later implementation step. Architecture §§11–12, 17–18 (lines 248–287, 351–399, 404–420), Plan steps 4–7 (lines 22–42).

## 7. Proposed runtime state model

One record per target is sufficient. All controls for that target read the same state. The record belongs to the current page.

| Field | Representation |
|---|---|
| Target ID | The exact validated ID identifies the target during compilation. The runtime map can use a deterministic generated key for that identity so DOM serialization of the authored ID cannot change the association. The key is the map index and need not appear twice in each record. |
| Authored display | Read the exact resolved value once from compiler-rendered inline CSS before any runtime changes. Preserve absence as absence. Keep this value stable across activations. |
| Initial toggle-controlled hidden state | Derive once from whether authored display is `none`. This sets the initial current state and the initial markup. A second mutable flag is unnecessary. |
| Current toggle-controlled hidden state | One boolean per target. Every activation flips only that boolean. The visibility mechanism and all `aria-expanded` values are projections of it. |
| Target reference | One resolved DOM element for the target. |
| Controls referencing the target | The group of resolved native buttons associated with that target. A DOM reference can identify each control internally. |

The model needs no per-button state, ancestor state, computed-display snapshot, or persisted copy. It uses no local storage, cookies, server state, or cross-page state.

## 8. Proposed implementation architecture

1. **Prepare renderer metadata.** Walk the normalized tree to associate each `ToggleAction.target_id` with the element's effective `id` and optional `display`. Generate a deterministic internal key per referenced target and put that key in escaped data attributes on the target and its controls. Keep the authored HTML ID and existing metadata behavior. This is an HTML renderer concern. The normalized model already supplies the target ID, target properties, and tree structure, so no model change or new validation rule is required. [Normalized model](../src/anzer/normalize.py#L26) · [Renderer mapping](../src/anzer/render/html.py#L10)
2. **Emit initial markup and a scoped hiding rule.** Emit the correct initial `aria-expanded` values and a hidden-state marker for initially collapsed targets. As an implementation option, use a scoped selector for compiler-marked targets carrying `hidden`. Ensure that its hiding rule wins over this compiler's normal inline display declarations. A bare `hidden` attribute can be overridden by author CSS. Keep the hiding rule limited to toggle targets and preserve the baseline. [HTML Standard on hidden state](https://html.spec.whatwg.org/multipage/interaction.html#the-hidden-attribute)
3. **Embed and initialize one fixed script.** Render it after the body content, only if the validated document contains a toggle. The script discovers compiler-marked targets and native buttons with fixed selectors, reads data attributes, and creates one record for each unambiguous association. Missing, duplicate, or malformed associations stay inactive. Skip affected groups without mutating other groups or interrupting the document. This runtime check covers rendered metadata, while existing semantic validation remains upstream.
4. **Apply one transition.** Route native activation through one event path. Apply the optional focus safeguard before collapsing, flip the target's own state, apply or remove the hiding marker, and synchronize all controls. For an authored `none` target, suppress only its inline display declaration while expanded and restore it on collapse. Keep the other styles and target subtree in place. Leave descendant targets' records and ARIA values alone.
5. **Keep authored data out of executable source.** Embed fixed compiler-owned JavaScript. Resolve DOM references by exact metadata-key lookup, with no selector built from an authored ID. Escape rendered attributes in the HTML renderer. Use no `eval`, dynamic code execution, inline handler strings, or interpolation of user values into JavaScript. Keep JavaScript separate from semantic validation and normalization. Trusted HTML retains its existing acknowledgement boundary.

## 9. Phase 9 implementation boundary

Phase 9 may add only generated toggle JavaScript, target and control discovery with validation of rendered metadata, initial state, activation and deactivation, synchronization of shared controls, `aria-expanded` updates, required visibility and display handling, the bounded focus safeguard if used, and runtime-specific tests. Renderer changes are limited to the metadata, initial state markup, scoped hiding rule, and script placement needed for those items.

CLI commands, filesystem output, new Anzer syntax, elements or properties, persistence, animation or transitions, framework dependencies, a general-purpose JavaScript runtime, and unrelated HTML or CSS refactoring are outside Phase 9.

## 10. Phase 9 test plan

These are proposed implementation tests. No runtime tests are added in Phase 9B.

| Area | Cases and expected evidence |
|---|---|
| Initial state | Test no authored display, `none`, `flex`, `grid`, and the remaining supported values `block`, `inline`, `inline-block`, `inline-flex`, and `inline-grid`. Only `none` starts locally collapsed. Check initial markup and post-initialization state, including a value supplied by a reusable style. |
| Activation and display restoration | Exercise both directions and repeated activation. A `none` target reveals through the normal display cascade, collapses again, and retains its authored value. Other targets return to their exact authored display or omission. Check DOM visibility and CSS, including that inline flex/grid cannot override collapse and that no hardcoded block value is assigned on reveal. |
| Multiple controls | Give two buttons one target. Activate either and verify that both `aria-expanded` values agree after each transition. A separate target stays unchanged. |
| Nested targets | Start B expanded and, in a second case, collapsed. Hide A and verify that B's own state and control values stay unchanged even for a B control outside A. Reopen A and verify that B retains the previous state. |
| Native activation and form behavior | Verify `type="button"`, one transition for pointer activation, Enter, and Space, and no form submission. Check the native button, accessible name, and expanded state in the browser's accessibility tree where available. |
| Focus | Collapse with focus outside, then with focus inside and a visible external activating button. Verify the proposed safeguard in the latter case if included. Cover a button inside its own target with no eligible external activator and verify the absence of custom focus reassignment or reopening behavior. |
| Security and failure isolation | Use exact IDs containing spaces, punctuation, quotes, ampersands, and Unicode. Verify correct associations and HTML escaping, with the same fixed JavaScript source regardless of ID spelling. Check absent, duplicate, and malformed target metadata after HTML generation. Invalid groups stay inactive while valid groups and page content continue to work. |
| Conditional output | Compare documents with and without toggles. The runtime and its scoped support markup appear only when needed. Repeat a render to confirm deterministic metadata and placement. |

## 11. Conflicts and readiness

**CONFLICT — none confirmed between the frozen documents.** Phase 9A identified two gaps in the frozen wording, and §§3.1–3.2 record the approved resolutions. Earlier audit A-20 was marked resolved at the decision level in §5, while its actual recommendation left the specific behavior of authored `display="none"` for clarification. Historical notes that describe all toggle accessibility as open are superseded where Unified and Freeze give a rule. [Unified §§10.1 and 11](ANZER_V0_1_UNIFIED_SPECIFICATION.md#101-display) · [Freeze §§2 and 7](ANZER_V0_1_DECISION_FREEZE_1.md#2-accepted-decisions) · [Earlier audit A-20](SEMANTIC_CONSISTENCY_AUDIT_1.md#a-20--displaynone-and-toggle-behavior-can-conflict)

**Phase 9 can begin within the boundary in §9.** No further language-level decision is required for that scope. Stronger focus or reopening guarantees, additional interaction behaviors, and any change to which IDs the language accepts remain outside the approval.

## 12. Decision register

| Topic | Specification status | Exact rule | Implementation implication | Approval required |
|---|---|---|---|---|
| Source action and target | **SPECIFIED** | A button toggle denotes one unique, validated section/container target. Shared controls are allowed. Unified §§7, 11. | Keep existing native syntax, reference validation, and kind restrictions. | No |
| Basic state transition | **SPECIFIED** | Initially visible by default. Alternate hidden/visible and preserve authored display. Unified §11, Freeze §2, earlier audit A-15. | Share per-target behavior across all controls, including repeated activation. | No |
| Accessible state | **SPECIFIED** and **APPROVED** | Synchronize `aria-expanded` for every control with its target's own state. Unified §11, Freeze §2, contract §3.2. | Set initial and current values from the single target record. | No |
| Target with authored `display="none"` | **APPROVED** | Start collapsed. Reveal by suppressing the authored `none` temporarily. Restore it on collapse. Contract §3.1. | Keep authored display distinct from own hidden state and retain the authored value across activations. | No |
| Target under a hidden ancestor | **APPROVED** | Ancestor visibility leaves descendant toggle state and control ARIA unchanged. Contract §3.2. | Update only the record for the target directly activated. | No |
| Focus and unreachable controls | **UNSPECIFIED** | **UNSPECIFIED BY FROZEN SPECIFICATION** what custom handling applies when hiding a focused descendant or the activating control itself. Unified §§7, 11. | The minimal safeguard in §5 is an implementation recommendation. Additional guarantees or placement constraints are outside Phase 9. | No for the bounded safeguard. Yes for additional behavior. |
| Persistence, custom input, labels, announcements, and animation | **UNSPECIFIED** | **UNSPECIFIED BY FROZEN SPECIFICATION** as additional behavior. Unified §11, earlier audit A-15. | Keep these outside the implementation unless separately approved. | Yes before adding any of these behaviors |
| ID form and comparison beyond current handling | **UNSPECIFIED** | **UNSPECIFIED BY FROZEN SPECIFICATION** beyond unique resolvable IDs and safe output. Unified §11, Architecture §§9, 19. | Account for strings already accepted by the validator. A new rejection rule or observable rewrite requires a decision. | Yes if changing accepted IDs or matching |
| Generated representation | **IMPLEMENTATION DETAIL** | Stable association, safe lookup, hidden state with preserved display, and conditional runtime output. Freeze §2, earlier audit A-15, Architecture §§12, 20. | Choose identifiers, metadata, DOM handling, and event wiring that implement the approved behavior. | No within the existing contract |
