# LLM Anti-Patterns — LWC Jest Testing with Accessibility

Common mistakes AI coding assistants make when generating Jest tests for Lightning Web Components with accessibility assertions. Each pattern carries a detection hint so a reviewing agent can self-check its own output.

---

## Anti-Pattern 1: Importing real Apex / wire modules instead of mocking them

**What the LLM generates:**

```js
import getCases from '@salesforce/apex/CaseController.getCases';
// ... uses it directly in the test
```

**Why it happens:** The LLM treats the `@salesforce/apex/...` import the way a real component does. In a real component, the platform resolves the virtual module at deploy time. In jest there is no platform — the module does not exist on disk and `jest` cannot resolve it without help.

**Correct pattern:**

```js
jest.mock(
    '@salesforce/apex/CaseController.getCases',
    () => ({ default: jest.fn() }),
    { virtual: true }
);
import getCases from '@salesforce/apex/CaseController.getCases';
// ... now getCases is jest.fn() — set with .mockResolvedValue / .mockRejectedValue
```

The `{ virtual: true }` option is what tells jest "the module is fine; just use my factory."

**Detection hint:** Any test file importing from `@salesforce/apex/...` without a sibling `jest.mock(...)` call OR `registerApexTestWireAdapter(...)` registration is wrong.

---

## Anti-Pattern 2: Querying through `document.querySelector` instead of `shadowRoot.querySelector`

**What the LLM generates:**

```js
const banner = document.querySelector('[role="status"]');
expect(banner).not.toBeNull();
```

**Why it happens:** Generic web-testing knowledge defaults to `document.querySelector`. LWC uses Shadow DOM and the test target lives inside the host element's shadow root, which `document.querySelector` cannot pierce.

**Correct pattern:**

```js
const banner = element.shadowRoot.querySelector('[role="status"]');
expect(banner).not.toBeNull();
```

**Detection hint:** Any `document.querySelector` / `document.getElementById` inside a test for an LWC is almost certainly wrong. Replace with `element.shadowRoot.querySelector(...)`.

---

## Anti-Pattern 3: Asserting `document.activeElement` for focus tests

**What the LLM generates:**

```js
trigger.click();
await Promise.resolve();
expect(document.activeElement).toBe(closeBtn);
```

**Why it happens:** Standard DOM testing intuition. From the *document's* perspective, the host custom element is the active element when something inside its shadow root is focused — `document.activeElement` returns the host, not the inner element.

**Correct pattern:**

```js
trigger.click();
await Promise.resolve();
await Promise.resolve();
expect(element.shadowRoot.activeElement).toBe(closeBtn);
```

For nested shadow roots, traverse: `element.shadowRoot.activeElement.shadowRoot.activeElement`.

**Detection hint:** `document.activeElement` in an LWC focus-management test is wrong. Use `element.shadowRoot.activeElement`.

---

## Anti-Pattern 4: Forgetting to wait through async re-renders

**What the LLM generates:**

```js
button.click();
expect(panel.getAttribute('aria-expanded')).toBe('true'); // asserts immediately
```

**Why it happens:** The LLM treats the click as synchronous. LWC re-renders asynchronously — the `aria-expanded` attribute is updated after the next microtask cycle.

**Correct pattern:**

```js
button.click();
await Promise.resolve(); // re-render
expect(button.getAttribute('aria-expanded')).toBe('true');
```

For chained async (mock Apex resolution + re-render), use multiple `await Promise.resolve()`s — see Concept 1 in `SKILL.md` for the awaits-per-flow table.

**Detection hint:** Any test that mutates state and asserts on an attribute or DOM element in the next line, with no `await`, is racing the LWC render scheduler.

---

## Anti-Pattern 5: Generating snapshot tests of `shadowRoot.innerHTML`

**What the LLM generates:**

```js
expect(element.shadowRoot.innerHTML).toMatchSnapshot();
```

**Why it happens:** Generic React / Vue testing pattern. In LWC, the engine emits version-specific attributes (synthetic-shadow markers, scoped class hashes, internal `data-*` flags) that change across platform releases — the snapshot becomes noisy and gets blindly accepted on every diff.

**Correct pattern:**

```js
// Assert on the specific a11y surface you care about.
expect(banner.getAttribute('role')).toBe('status');
expect(banner.getAttribute('aria-label')).toBe('Save complete');
expect(banner.getAttribute('aria-live')).toBe('polite');
```

If a snapshot is wanted, snapshot a structured object of explicit attributes — never raw HTML.

**Detection hint:** `toMatchSnapshot()` on `innerHTML` or `outerHTML` of any LWC shadow content is wrong by default.

---

## Anti-Pattern 6: Using real timers with `setTimeout`-driven a11y announcements

**What the LLM generates:**

```js
button.click();
await new Promise((resolve) => setTimeout(resolve, 200)); // wait for live region
expect(liveRegion.textContent).toContain('Saved');
```

**Why it happens:** The LLM models the test the way a manual user would — wait 200ms, then check. In jest this introduces real wall-clock delay (slow tests) AND is racy (200ms might not be enough on a slow CI runner).

**Correct pattern:** If the component uses `setTimeout`, use jest's fake timers:

```js
jest.useFakeTimers();
button.click();
jest.runAllTimers(); // synchronously fast-forward
await Promise.resolve();
expect(liveRegion.textContent).toContain('Saved');
```

If the component uses Promises (no `setTimeout`), just use `await Promise.resolve()` chains — no real timer wait needed.

**Detection hint:** `setTimeout(resolve, ...)` inside a test body or `await new Promise(setTimeout, ...)` is almost always a sign of incorrect async handling.

---

## Anti-Pattern 7: Asserting on contrast, color, or visible focus indicator in jest

**What the LLM generates:**

```js
const btn = element.shadowRoot.querySelector('button');
const style = window.getComputedStyle(btn);
expect(style.outlineWidth).toBe('2px'); // testing focus ring
```

**Why it happens:** The LLM conflates "accessibility" with "all of accessibility." Color contrast, focus-ring visibility, computed font sizes, and similar presentation properties are layout-dependent and cannot be evaluated in jsdom — `getComputedStyle` returns mostly empty / default values.

**Correct pattern:** Don't test these in jest. Test the structural surface (ARIA, `tabindex`, focus targets, keyboard handlers) and defer presentation a11y to a real-browser test (UTAM + axe, or Playwright + axe).

```js
// Good: structural assertion that jest can verify.
expect(btn.getAttribute('aria-label')).toBe('Close');
expect(btn.getAttribute('tabindex')).not.toBe('-1');
```

**Detection hint:** `getComputedStyle`, `offsetWidth`, `getBoundingClientRect`, or any pixel / color check inside a jest a11y test is in the wrong test layer.
