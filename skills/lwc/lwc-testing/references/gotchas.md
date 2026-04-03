# Gotchas - LWC Testing

## Assertions Often Run Before Rerender Finishes

**What happens:** A click or emitted wire value appears to do nothing in the test even though the component works in the browser.

**When it occurs:** The test asserts immediately after an async boundary instead of waiting for the rerender cycle.

**How to avoid:** Use a small `flushPromises` helper or `await Promise.resolve()` after state changes that trigger rerender.

---

## Imperative Apex And Wired Apex Need Different Mocks

**What happens:** The test uses a wire adapter helper for an imperative import or tries to `mockResolvedValue` on a wire adapter.

**When it occurs:** The implementation path changed and the tests did not change with it.

**How to avoid:** Match the mocking strategy to the production contract: wire utilities for `@wire`, promise mocks for imperative imports.

---

## Base Component Markup Is Not The Live Platform DOM

**What happens:** A test reaches too deeply into the internal markup of a `lightning-*` base component and breaks after tooling or dependency updates.

**When it occurs:** Assertions depend on private base-component structure instead of the contract your component controls.

**How to avoid:** Assert your own component behavior, labels, events, and state, not the platform's internal stub structure.

---

## Missing DOM Cleanup Causes Cross-Test Leakage

**What happens:** Later tests fail or pass for strange reasons because earlier elements were left mounted in `document.body`.

**When it occurs:** The suite appends elements but skips `afterEach` cleanup.

**How to avoid:** Remove all mounted elements after every test and keep shared setup small.
