---
name: lwc-modal-and-overlay
description: "Use when choosing or reviewing overlay patterns in Lightning Web Components, especially `LightningModal`, confirmation dialogs, toasts, focus handling, and overlay dismissal behavior. Triggers: 'lightning modal in lwc', 'toast or modal decision', 'focus trap in modal', 'overlay close result', 'extends LightningModal', 'lightning-modal-body', 'close(result)', 'LightningConfirm', 'LightningAlert', 'LightningPrompt', 'lightning/toast', 'ShowToastEvent', 'modal stacking', 'CloseActionScreenEvent'. NOT for full Flow screen UX design or record-edit processes that should stay on-page - use flow/screen-flows."
category: lwc
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - User Experience
  - Reliability
tags:
  - lightning-modal
  - overlay
  - toast
  - confirm-dialog
  - focus-management
triggers:
  - "how do i use lightning modal in lwc"
  - "should this be a modal or a toast"
  - "how do i return a result from lightning modal"
  - "focus trap is broken in my modal"
  - "legacy overlay library replacement in lwc"
  - "extend lightningmodal and return a value to the caller"
  - "lightning-modal tag renders nothing in my template"
  - "navigationmixin does not work inside lightning modal"
  - "modal opens on top of another modal in a quick action"
  - "toast never appears in lwr experience cloud site"
  - "replace hand-rolled slds-modal markup with lightningmodal"
  - "write a jest test that asserts modal open resolves"
  - "quick action x button skips my cancel logic"
inputs:
  - "what user action launches the overlay and whether the interaction is blocking or non-blocking"
  - "whether the component needs a return value, confirmation, form entry, or simple notification"
  - "how focus, dismissal, and save failure should behave"
outputs:
  - "overlay selection guidance for modal, confirm, toast, or inline messaging"
  - "review findings for focus handling, dismissal rules, and modal overuse"
  - "implementation pattern for opening, closing, and returning results from overlays"
  - "a deployable modal + launcher bundle with -meta.xml, package.xml, and a Jest test that asserts the close() result"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

Use this skill when a component is reaching for an overlay and the team needs to choose the lightest interaction that still protects the workflow. A modal is appropriate when the user must complete, confirm, or cancel a focused task. It is a poor default for simple success messages, non-blocking feedback, or page-state that would be clearer inline.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the user being informed, confirming an action, or completing a focused secondary task?
- Does the overlay need to return data to the caller, or is a toast or inline message enough?
- What should happen if the user presses Escape, clicks cancel, or the save inside the overlay fails?

---

## Questions to Ask Before Configuring

Ask these before writing the component. Each one maps to a failure in `references/gotchas.md`, and an assistant that skips them produces a modal that renders correctly and returns nothing useful.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "When the overlay closes, what does the caller need to know — a value, a yes/no, or nothing at all?" | Decides whether `close()` needs an argument at all; a bare `close()` resolves the caller's `await` with `undefined` and cancel becomes indistinguishable from save | The result shape, written down: `{ status, ...payload }` and the branch the launcher takes on each |
| "What data does the modal need before it can render — and where does it come from?" | Modal `@api` properties are populated from the `open({...})` config, never from parent markup, so unnamed inputs simply arrive undefined | The exact `open()` config keys, which become the Jest `objectContaining` assertion |
| "Does anything inside the modal navigate the user somewhere?" | `NavigationMixin` cannot wrap a `LightningModal` subclass; if the answer is yes, the design needs the three-component relay before any code is written | A relay plan: child builds the `PageReference`, modal returns it, launcher navigates |
| "If this opens on top of a quick action or another modal, should the one underneath close?" | Stacking is default platform behaviour, not a bug — `replace` decides it, and two documented cases preserve the previous modal regardless | An explicit `replace` value and a note of which stacking exception applies |
| "Is there cleanup that must run when the user backs out?" | On a screen quick action the header X bypasses custom Cancel logic entirely; must-run cleanup put there never runs | Either an idempotent design or cleanup moved onto Save |
| "How many notifications will one user action produce?" | The toast container caps at 3 and silently queues the rest, and `ShowToastEvent` does not work in LWR Experience Cloud sites at all | One summary toast instead of N, on the module that works in the target container |
| "Is there a window during which closing must be blocked, and what ends it?" | A close lock with no defined end condition traps the user; the ending event is what makes it safe | A bounded window with a `finally` that always releases, plus the focus-return target |

What a proper overlay design adds over "just opening a modal": the caller can tell cancel from save and acts on the difference, the modal's inputs are asserted by a test instead of discovered in production, navigation and stacking behave the way the designer intended rather than the way the default happened to fall, and there is no state in which a keyboard user cannot leave.

---

## Core Concepts

Overlay design is mainly about choosing the right interruption level. The more blocking the UI becomes, the stronger the justification must be.

| Principle | Default | Anti-pattern | Why it matters |
|---|---|---|---|
| Smallest viable overlay | Toast for status; confirm dialog for short irreversible actions; modal only for a dedicated task | Wrapping every secondary interaction in a modal | Most weak modal UX is really a toast or one-line confirm wearing the wrong component |
| `LightningModal` is a contract | Component extends `LightningModal`, opened via static `open()`, returns via `close(result)` | Inlining `<lightning-modal>` markup or hand-rolled SLDS dialog HTML | The static-open + `close(result)` contract is what makes result-passing and lifecycle predictable |
| Focus and dismissal are product decisions | Define initial focus, escape behavior, and focus return on every overlay | Leaving focus wherever the browser parked it; permanently undismissable modals | A user must always know how to exit and where they land after closing |
| Stacking is chosen, not inherited | Set `replace` deliberately when navigating out of a modal; keep multi-step work on a page or screen Flow | Letting the default stack modals and then hand-closing them | Undeclared stacking compounds focus, Back-button, and accessibility bugs |

### Which Overlay Module

| Need | Module | Import style | Resolves with |
|---|---|---|---|
| A focused subtask with custom UI and a return value | `lightning/modal` | Extend `LightningModal` (default import, no tag) | Whatever `close(value)` was given |
| Yes / no before a destructive action | `lightning/confirm` | `LightningConfirm.open({ message, variant, label })` | `true` on OK, `false` on Cancel |
| An urgent halt the user must acknowledge | `lightning/alert` | `LightningAlert.open({ message, theme, label })` | Resolves when the user clicks OK |
| One string of input | `lightning/prompt` | `LightningPrompt.open({ message, theme, label, defaultValue })` | The entered text, or `null` on Cancel |
| Transient status, no acknowledgement | `lightning/toast` | `LightningToast.show({ label, message, variant }, this)` | Nothing — fire and forget |
| A quick action's own modal frame | `lightning-quick-action-panel` | A tag in the template; close with `CloseActionScreenEvent` | Nothing — the panel closes |

`confirm` takes `variant`; `alert` and `prompt` take `theme`. They are not interchangeable. Full sources and the caveats on each attribute are in `references/code-examples.md` § 5.

---

## Common Patterns

### Result-Returning Modal

**When to use:** The caller needs a focused subtask such as choosing a record, editing a small payload, or confirming a set of options.

**How it works:** Create a component that extends `LightningModal`, open it with `MyModal.open({...})`, and return the outcome through `close(result)`. The full bundle — modal, launcher, both `-meta.xml` files, `package.xml`, and the Jest test — is in `references/code-examples.md` §§ 1–4.

**Why not the alternative:** Embedding conditional modal markup in every parent component spreads focus and dismissal logic everywhere.

### Toast Or Inline Message Instead Of A Modal

**When to use:** The UI only needs to acknowledge success, warn gently, or point the user to the next step.

**How it works:** Use `lightning/toast` or inline feedback and keep the user in the current context. Check the target container first — `lightning/platformShowToastEvent` does not work in LWR Experience Cloud sites.

**Why not the alternative:** Blocking overlays slow users down and add accessibility work when the interaction is not truly modal.

### Temporarily Non-Dismissable Save Window

**When to use:** The modal launches a short-running save that should not be interrupted midway.

**How it works:** Disable dismissal only for the bounded save window inside a `try`, show clear progress, and restore close behavior in the `finally` so an exception cannot strand the user.

### Navigating Out Of A Modal

**When to use:** The modal's job ends by sending the user somewhere — a new record, a list view, a related object.

**How it works:** The modal never navigates. It returns the `PageReference` through `close()`, and the launcher — a plain `LightningElement` wrapped in `NavigationMixin` — performs the navigation. See `references/code-examples.md` § 7 and `lwc/navigation-and-routing`.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need lightweight success or status feedback | `lightning/toast` | The user should stay in context |
| Need quick confirmation of a risky action | `lightning/confirm` | One call, no component, resolves `true`/`false` |
| Need an error the user must acknowledge | `lightning/alert` | A toast auto-dismisses and the user may never see it |
| Need a focused secondary task with a returned result | `LightningModal` subclass | Clear lifecycle and result-passing contract |
| Need a modal launched from a record-page action button | Screen quick action + `lightning-quick-action-panel` | Setup owns the placement; no launcher component needed |
| Need a large multi-step workflow | Consider a page or Flow-based experience | A modal may become cramped and hard to navigate |
| Team plans to hand-build all modal markup | Prefer `LightningModal` unless there is a real gap | Supported primitives reduce focus and dismissal bugs |

---

## Recommended Workflow

1. **Classify the interruption.** Run the Which Overlay Module table above. If the answer is `confirm`, `alert`, `prompt`, or `toast`, stop — you do not need a component, and `references/code-examples.md` § 5 has the whole call.
2. **Fill in `templates/lwc-modal-and-overlay-template.md`.** The Modal Contract block (opened from / initial focus / cancel behavior / close result / focus return target) is the design; write it before any JavaScript exists.
3. **Build the bundle from `references/code-examples.md` §§ 1–3.** Copy the shape from `templates/lwc/component-skeleton/`, extend `LightningModal` with a default import, start the template with `lightning-modal-body`, and give the modal its own `-meta.xml` with `isExposed=false`.
4. **Wire the result contract.** Every path out of the modal calls `close()` with a tagged object; the launcher awaits `open()` and branches on the tag. Route navigation through the launcher, never through the modal (§ 7).
5. **Write the Jest test from § 4** — one case asserting `open()` resolves with the `close()` value, one asserting the cancel path writes nothing, one asserting the `open()` config carries every `@api` input. Add the `^lightning/modal$` `moduleNameMapper` entry to `jest.config.js`.
6. **Run the checker** over the source tree: `python3 scripts/check_lwc_modal_and_overlay.py --manifest-dir force-app/main/default/lwc`. Fix every ISSUE before review; it catches hand-rolled `slds-modal` markup, a missing `lightning-modal-body`, an unawaited `open()`, a modal with no `close()` on any path, `@api` inputs no launcher passes, and a bundle with no `__tests__` folder.
7. **Verify in the org.** Deploy with the `package.xml` in § 3, then exercise Escape, the header X, and Cancel — confirm the launcher regains focus and that the SOQL check in § 3 shows the write actually landed.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] The overlay type matches the true interruption level of the task.
- [ ] `LightningModal` is used for real modal workflows instead of ad hoc SLDS dialog markup.
- [ ] The modal imports `LightningModal` as a default import and never imports `LightningElement`.
- [ ] The template contains `lightning-modal-body`.
- [ ] Every exit path calls `close()` with a tagged result, and the launcher branches on it.
- [ ] Every `@api` property on the modal appears in the launcher's `open()` config and in a Jest assertion.
- [ ] Initial focus, dismissal behavior, and focus return are defined.
- [ ] Escape, cancel, and save-failure behavior are all tested.
- [ ] Any close lock is set in a `try` and released in a `finally`.
- [ ] Navigation from the modal goes through the launcher, not `NavigationMixin` on the modal.
- [ ] Stacking behaviour is a deliberate `replace` value, not the default.
- [ ] The toast module is the one supported in the target container, and one action produces one toast.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems. Full grounding in `references/gotchas.md`.

1. **`LightningModal` is opened through an API, not conditional markup in the parent** - teams coming from generic web patterns often model it the wrong way first.
2. **There is no `<lightning-modal>` tag and the import has no braces** - the named-import form yields `undefined` and `extends undefined` throws before anything renders.
3. **`@api` properties on a modal look like dead code** - nothing in any template sets them; the `open()` config does.
4. **`close()` with no argument resolves the caller's `await` to `undefined`** - cancel and save become the same event.
5. **`NavigationMixin` cannot wrap a `LightningModal` subclass** - the mixin is for `LightningElement` only.
6. **Modal stacking is the documented default** - `replace` decides it, and two cases preserve the previous modal even when `replace` is true.
7. **A modal without focus planning is functionally broken** - the overlay may look complete while still being hostile to keyboard users.
8. **`disableClose` should be temporary** - using it as a permanent guard creates an interaction the user cannot exit safely.
9. **A screen quick action's X bypasses your Cancel logic** - anything that must run on backing out cannot live there.
10. **Many modal requests are really toast or inline-message requests** - choosing the heavier interaction by default adds friction and complexity without better UX.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Overlay choice | Recommendation for modal, confirm, alert, prompt, toast, or inline feedback |
| Modal lifecycle design | Open, close, result, failure, and focus behavior plan |
| Component bundle | Modal + launcher js/html, both `-meta.xml` files, `package.xml`, and the deploy command |
| Jest suite | Tests asserting the `open()` promise resolves with the `close()` value, the cancel path, and the `@api` inputs |
| Review findings | Concrete issues in dismissal logic, accessibility, and modal overuse |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/code-examples.md` | You are writing the code — full modal + launcher bundle, `-meta.xml`, `package.xml`, Jest test, confirm/alert/prompt table, the labelled BAD SLDS modal, and the navigation relay |
| `references/gotchas.md` | Something already behaves oddly — twelve grounded platform behaviours with line citations to the LWC Developer Guide |
| `references/llm-anti-patterns.md` | You are reviewing AI-generated overlay code, or self-checking your own output before handing it over |
| `references/examples.md` | You want the short worked scenarios and the reasoning for picking one overlay over another |
| `references/well-architected.md` | You are justifying the design in a review, or need the source list behind every claim in this package |

---

## Related Skills

- `lwc/lwc-lightning-modal` - use for the `LightningModal` base-class API surface on its own; this skill covers the overlay choice and the end-to-end buildable bundle.
- `lwc/lwc-accessibility` - use alongside this skill when focus, labeling, and keyboard behavior are the highest risk.
- `lwc/lwc-focus-management` - use when the focus trap, restore, or programmatic focus inside the overlay is the actual problem.
- `lwc/navigation-and-routing` - use when the modal's job ends in a navigation, or when `PageReference` construction is the hard part.
- `lwc/lwc-toast-and-notifications` - use when the answer turns out to be a toast or a custom notification rather than an overlay.
- `lwc/lifecycle-hooks` - use when overlay bugs are really rerender or cleanup issues.
- `flow/screen-flows` - use when the task is large enough that it should probably become a guided flow instead of a modal.
