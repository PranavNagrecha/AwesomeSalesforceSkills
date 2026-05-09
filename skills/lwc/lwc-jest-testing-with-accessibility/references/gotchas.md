# Gotchas — LWC Jest Testing with Accessibility

Non-obvious behaviors of `@salesforce/sfdx-lwc-jest`, jsdom, and the LWC test runtime that bite teams writing accessibility-focused jest tests.

---

## Gotcha 1: jest does not run inside the LWC sandbox / Locker Service

**Symptom:** A test passes in jest. The same component fails at runtime in production with a Locker-related error (e.g. `SecureWindow` proxy refusing a DOM API).

**Why:** `@salesforce/sfdx-lwc-jest` runs the component in plain Node + jsdom — no Locker Service, no Lightning Web Security policies, no synthetic-shadow restrictions beyond what the LWC engine adds for shadow encapsulation. APIs that are blocked at runtime (e.g. `Element.getBoundingClientRect()` returning `0` under Locker, `window.eval`, certain global constructors) work fine in jest.

**Fix:** Treat jest as a *unit-level* check on logic, structure, and a11y attributes. Pair it with at least one real-org smoke test (UTAM, Playwright against a sandbox, or manual) before claiming the component is production-ready. Do not skip jest because of this — a green jest suite still catches 80% of regressions; it just doesn't replace runtime testing.

---

## Gotcha 2: `await Promise.resolve()` once is not always enough

**Symptom:** A11y assertion runs immediately after a click handler. Sometimes the test passes, sometimes it fails with "expected 'true', received 'false'." The flake is real, not random.

**Why:** LWC's render scheduling and any Promise-returning side effect each consume a microtask. A user-driven flow like *click → state change → re-render* is one microtask. *Click → Apex mock resolution → state change → re-render* is two or three. A single `await Promise.resolve()` only flushes one microtask cycle.

**Fix:** Match the number of `await Promise.resolve()` calls to the number of async hops. The canonical patterns:

| Flow | Awaits needed |
|---|---|
| `el.foo = 'x'; await Promise.resolve();` | 1 |
| `button.click(); await Promise.resolve();` | 1 |
| `button.click(); await Promise.resolve(); await Promise.resolve();` (click + mock resolve + re-render) | 2 (sometimes 3) |
| `wireAdapter.emit(data); await Promise.resolve(); await Promise.resolve();` | 2 |

If you start chaining four or more, extract a `flushPromises = () => new Promise(setImmediate)` helper or use `jest.runAllTimers()` in tandem.

---

## Gotcha 3: `document.activeElement` is not the same as `shadowRoot.activeElement`

**Symptom:** Test asserts `expect(document.activeElement).toBe(closeBtn)` after opening a modal. Always fails — `document.activeElement` is the host element, not the focused element inside the shadow tree.

**Why:** Shadow DOM has its own active-element concept. From the document's point of view, the active element is the host (the `c-confirm-modal` custom element). The actual focus-bearing element lives inside `shadowRoot.activeElement`.

**Fix:** Always assert `element.shadowRoot.activeElement` for focus-management tests. If your component delegates focus to a child component, you may need to traverse: `element.shadowRoot.activeElement.shadowRoot.activeElement`. This is a real jest behavior — the same indirection exists in real browsers, but tools like axe and `@testing-library` hide it.

---

## Gotcha 4: `KeyboardEvent` constructed in jsdom does not always have working modifier flags

**Symptom:** Test dispatches `new KeyboardEvent('keydown', { key: 'Tab', shiftKey: true })`. Component handler reads `e.shiftKey` and gets `false` or `undefined`.

**Why:** jsdom's `KeyboardEvent` constructor accepts options but historically had partial fidelity for modifier-key flags depending on jsdom version. The default sfdx-lwc-jest preset pins a known-good jsdom but minor drift is possible across `npm install` runs.

**Fix:** Test what you actually need. For `Escape` / `Enter` / arrow keys, the `key` property is reliable. For shift-tab and other modifier-driven combinations, prefer asserting against the *outcome* (focus moved to previous tab stop) rather than the raw event flag. If you must test modifiers explicitly, dispatch via `element.dispatchEvent(new KeyboardEvent(...))` and read the resulting state, not the event itself.

---

## Gotcha 5: Snapshot tests of `shadowRoot.innerHTML` are unstable across LWC engine upgrades

**Symptom:** Team sets up `expect(element.shadowRoot.innerHTML).toMatchSnapshot()` for a11y "structural" testing. Snapshots break on every Salesforce platform release with no real component change.

**Why:** LWC's compiled output includes engine-managed attributes (`data-id`, `lwc:host` markers, scoped class hashes) that change between versions. Snapshots capture them, so the diff is full of noise unrelated to the component's a11y contract.

**Fix:** Don't snapshot raw HTML for a11y testing. Snapshot specific things you care about:

```js
// Good: explicit assertions on the attributes that matter.
expect(banner.getAttribute('role')).toBe('status');
expect(banner.getAttribute('aria-label')).toBe('Save complete');

// Bad: opaque blob that breaks on every release.
expect(element.shadowRoot.innerHTML).toMatchSnapshot();
```

If you really want a snapshot, narrow it to a structured object:

```js
const a11ySurface = {
    role: banner.getAttribute('role'),
    label: banner.getAttribute('aria-label'),
    live: banner.getAttribute('aria-live')
};
expect(a11ySurface).toMatchSnapshot();
```

---

## Gotcha 6: `axe-core` `color-contrast` rule fails or hangs in jsdom

**Symptom:** Adding `jest-axe` to the project. Tests fail with confusing color-contrast errors, OR the test hangs and times out.

**Why:** jsdom does not implement `getComputedStyle` with full fidelity (no real CSS layout / cascade resolution). `axe-core`'s `color-contrast` rule depends on resolving computed colors and falls into edge cases inside jsdom — sometimes it throws, sometimes it produces false positives.

**Fix:** Always disable `color-contrast` in jest:

```js
const results = await axe(element.shadowRoot, {
    rules: { 'color-contrast': { enabled: false } }
});
```

If the team needs contrast checking, run axe in a real browser via UTAM or a Playwright-based runner — not jest. Document this in the PR.

---

## Gotcha 7: `lwc:dom="manual"` content isn't queryable from jest until you wait an extra cycle

**Symptom:** Component uses `lwc:dom="manual"` to inject content imperatively (e.g. for a third-party widget). Jest test queries for the injected nodes immediately after `connectedCallback` — finds nothing.

**Why:** `lwc:dom="manual"` defers ownership of the subtree to the component's JS, which typically populates it inside `renderedCallback`. `renderedCallback` runs *after* the first synchronous render, so the injected content isn't in the shadow tree until the render cycle is complete.

**Fix:** Add an extra `await Promise.resolve()` after appending the element, OR wait for a specific selector to appear:

```js
document.body.appendChild(element);
await Promise.resolve(); // first render
await Promise.resolve(); // renderedCallback + manual DOM injection
const injected = element.shadowRoot.querySelector('.injected-widget');
expect(injected).not.toBeNull();
```

Then run a11y assertions against the injected subtree as normal.
