# Well-Architected Notes — LWC Focus Management

## Relevant Pillars

- **User Experience** — Primary pillar. Focus is the keyboard user's cursor and
  the screen-reader user's position in the document; losing it is the equivalent
  of the page scrolling somewhere at random. What makes this an architectural
  concern rather than a styling one is that the failure is invisible to the
  people building and reviewing the component: mouse users never notice, nothing
  is logged, and no test fails. The design has to be right on the way in because
  there is no feedback loop that will catch it later.

- **Accessibility as a conformance obligation** — WCAG 2.1 AA is a contract, not
  a preference, for most orgs shipping to employees or customers. Three success
  criteria live entirely in this skill's territory: **2.4.3 Focus Order** (a
  focus order that preserves meaning and operability), **2.1.2 No Keyboard Trap**
  (a component you can `Tab` into must be one you can `Tab` out of), and **4.1.3
  Status Messages** (changes announced without receiving focus). A focus trap
  with a broken `Escape` handler converts an accessibility feature into a
  conformance failure, which is why the exit path is designed before the trap.

- **Security** — Small, real, and frequently missed. Focus decides which element
  receives the next keystroke. A component that yanks focus during an async
  resolution can redirect typing into a different field than the one the user is
  looking at — into a field that is then submitted, or into an editable region
  whose contents are persisted. This is not an exploit chain, but it is a
  correctness property of an input surface, and "announce, do not yank" is the
  design rule that follows from it.

- **Operational Excellence** — The maintenance cost of focus code is concentrated
  in the hand-rolled parts. A custom focus trap has to keep a list of focusable
  element tags in step with the template, has to be re-audited when the component
  gains conditional content, and has to be re-tested against every browser and
  screen reader combination the org supports. Choosing `lightning/modal` moves
  all of that to Salesforce. That is the largest single lever available here and
  it is a design decision, not an implementation detail.

## Architectural Trade-offs

**`lightning/modal` vs a hand-rolled trap.** The module carries a documented
initial-focus rule, maintained trapping, and `Escape` handling, and it is tested
against assistive technology you do not have. It costs you control over markup
and structure, and its `disableClose` is a keyboard trap if misused. A custom
implementation gives complete control and takes on the full ongoing burden — the
focusable-tag list, the shadow-boundary comparisons, the teardown, the
cross-browser verification. The honest default is the module for anything modal
and a custom implementation only for surfaces that genuinely are not modals, with
the reason recorded so a later reviewer does not have to reconstruct it.

**`delegatesFocus` vs an explicit `@api focus()`.** `delegatesFocus` is
declarative, is the documented recommendation, and makes `.focus()` on the host
do the obvious thing — but it always targets the *first* focusable element, and
it must not be combined with `tabindex`. An `@api focus()` lets the component
choose its target based on state (focus the first *invalid* field; focus the
active step) and is self-documenting as a public contract, at the cost of a
method every consumer has to know exists. Use `delegatesFocus` for leaf
components wrapping one control; use `@api focus()` when the choice of target is
a decision.

**`this.refs` vs `data-*` plus `querySelector`.** Refs are faster, need no
selector, and read better — and they are a compile error inside `for:each` and
unavailable with `lwc:dom="manual"`. Data attributes work everywhere and survive
re-renders when what you store is the selector rather than the node. Most
components need both, and mixing them is not inconsistency: it is using each
where it is legal.

**Focus flag in `renderedCallback` vs `Promise.resolve()` after the state
change.** The flag keeps the focus decision next to the render it depends on and
is the documented shape for one-time work in that hook. The microtask keeps it
next to the *transition*, which is where a reader looks for it, at the cost of
depending on LWC's rehydration landing within one microtask. The flag is the more
defensible choice for anything a screen-reader user depends on; the microtask is
fine for restoration after a surface has already left the DOM.

**Announcing vs moving focus on async completion.** Moving focus guarantees the
user encounters the result and guarantees you interrupt whatever they were doing.
Announcing into a live region is non-destructive and can be missed if the region
is configured `polite` and the user is mid-interaction. The rule that resolves it
is not a preference: move focus only when the resolution *destroyed or replaced*
the element that had it. Otherwise announce.

**Live region urgency.** `assertive` (`role="alert"`) interrupts the screen reader
immediately — correct for a validation failure the user must resolve before
continuing, and hostile for anything routine. `polite` (`role="status"`) waits for
a natural pause and may be missed entirely if the user is typing. Orgs that
default everything to `assertive` train users to ignore the channel, which is the
same failure mode as notification fatigue in a different medium.

## Anti-Patterns

1. **`document.activeElement` inside a component.** It retargets to the host, so
   every comparison against it is `false` and every element stored from it is
   unfocusable. `this.template.activeElement` is the scoped alternative.

2. **The general-web focusable-elements selector.** `'button, input, select, …'`
   matches nothing in a form of base components, because the real controls are
   inside their own shadow trees.

3. **Restoration owned by the overlay.** Only the opener can see its trigger. An
   overlay that tries to restore focus is guessing, and the guess is a host
   element.

4. **`.focus()` in `connectedCallback`.** The children do not exist yet, the
   query returns `null`, and optional chaining makes the failure silent.

5. **Unguarded `renderedCallback` focus.** It re-fires on every render and eats
   the user's keystrokes. Guard with a plain boolean field — never with reactive
   state, which risks an infinite render loop.

6. **A trap with no `Escape` route.** WCAG 2.1.2 is failed by exactly this, and
   the component was built to improve accessibility.

7. **Positive `tabindex`.** Rejected by the compiler, and the impulse behind it —
   "fix the order without touching the DOM" — is the actual problem.

8. **`tabindex` on a component that sets `delegatesFocus`.** The documentation
   says it "throws off the focus order"; they are alternatives, not layers.

9. **Reaching through `.shadowRoot` into a child.** It couples the parent to
   another component's private markup, and it breaks the first time that markup
   changes.

10. **Treating a green Jest suite as the accessibility gate.** jsdom has no
    layout and no real sequential focus navigation. Assert focus *identity* in
    Jest, then do the keyboard walk.

## Official Sources Used

- Lightning Web Components Developer Guide — Handle Focus (only `tabindex="0"` and `tabindex="-1"` are supported; "By default, focus skips the component container and moves to the elements inside the component. To include the component itself in navigation, add `tabindex="0"` to the component tag in the parent template"; `static delegatesFocus = true`; "Don't use `tabindex` with `delegatesFocus` because it throws off the focus order") — https://developer.salesforce.com/docs/platform/lwc/guide/create-components-focus.html
- Lightning Web Components Developer Guide — Access Elements the Component Owns (`this.template.querySelector` / `querySelectorAll` scoping, "Don't use ID selectors with `querySelector`", `lwc:ref` and `this.refs`, "If you place `lwc:ref` in a `for:each` or `iterator:*` loop, the template compiler throws an error", "If you call `this.refs` for a nonexistent ref, it returns `undefined`", refs unavailable with `lwc:dom="manual"`) — https://developer.salesforce.com/docs/platform/lwc/guide/create-components-dom-work.html
- Lightning Web Components Developer Guide — `connectedCallback()` ("You can't access child elements from the callbacks because they don't exist yet"; "connectedCallback() can fire more than one time") — https://developer.salesforce.com/docs/platform/lwc/guide/create-lifecycle-hooks-dom.html
- Lightning Web Components Developer Guide — `renderedCallback()` (fires after every render, "flows from child to parent", the `hasRendered` boolean-guard pattern for one-time operations, and "Updating the state of your component in `renderedCallback()` can cause an infinite loop") — https://developer.salesforce.com/docs/platform/lwc/guide/create-lifecycle-hooks-rendered.html
- Lightning Web Components Developer Guide — HTML Template Directives (`lwc:ref`, `lwc:dom`) — https://developer.salesforce.com/docs/platform/lwc/guide/reference-directives.html
- Lightning Web Components Developer Guide — Synthetic Shadow DOM ("Currently, Lightning Experience and Experience Builder sites use synthetic shadow by default") — https://developer.salesforce.com/docs/platform/lwc/guide/create-dom-synthetic.html
- Lightning Component Reference — Modal (`lightning/modal`, `LightningModal.open()` with `label` / `size` / `description` / `disableClose`, the `lightning-modal-header` / `-body` / `-footer` helper components, the documented initial-focus priority order, and the `disableClose` keyboard-trap warning) — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide/lightning-modal.html
- Lightning Component Reference — `lightning-input` (`focus()` "Sets focus on the input element", `reportValidity()` "Displays the error messages and returns false if the input is invalid", `setCustomValidity()`, the required `label` attribute and `variant="label-hidden"`) — https://developer.salesforce.com/docs/component-library/bundle/lightning-input/documentation
- W3C — Web Content Accessibility Guidelines (WCAG) 2.1, success criteria 2.1.2 No Keyboard Trap, 2.4.3 Focus Order, 2.4.7 Focus Visible, 4.1.3 Status Messages — https://www.w3.org/TR/WCAG21/
- Salesforce Well-Architected — Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

### Claims deliberately not made

`this.template.activeElement` is used throughout this skill as the scoped
alternative to `document.activeElement`. It is the standard `ShadowRoot`
`activeElement` property rather than an LWC-specific API, and the LWC Developer
Guide pages fetched for this skill do not discuss it by name. It is presented
here on the strength of the DOM specification and of the retargeting behaviour
the shadow-DOM pages do describe.

The Synthetic Shadow DOM page documents the styling and rendering differences
between synthetic and native shadow but does not enumerate focus- or
`activeElement`-specific divergences, so no claim is made here about how the two
modes differ on focus. Verify against a real org before relying on a difference.
