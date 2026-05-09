---
name: lwc-jest-testing-with-accessibility
description: "Use when authoring or reviewing Jest unit tests for Lightning Web Components and the test plan must include explicit accessibility assertions — covers `@salesforce/sfdx-lwc-jest` setup, `createElement` / `document.body.appendChild` render harness, wire-service mocks via `@salesforce/wire-service-jest-util`, imperative Apex mocks via `jest.fn()`, simulated user interactions (`click`, `keydown`, `focus`), ARIA attribute and accessible-name assertions, focus-management tests, keyboard-navigation tests, and optional `axe-core` integration via `jest-axe`. Triggers: 'add a11y assertions to my LWC jest tests', 'how do I test focus management in LWC', 'jest test for keyboard navigation', 'integrate axe-core into sfdx-lwc-jest', 'assert ARIA attributes after interaction', 'how do I prove the LWC is accessible in CI'. NOT for general LWC jest setup without an a11y angle (use lwc/lwc-testing — this skill is the accessibility-deep-dive sibling), NOT for accessibility-pattern authoring inside the component itself (use lwc/lwc-accessibility-patterns), NOT for end-to-end UI automation via UTAM, NOT for manual screen-reader QA workflows."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - User Experience
  - Reliability
tags:
  - lwc-jest-testing-with-accessibility
  - jest
  - sfdx-lwc-jest
  - accessibility
  - axe-core
  - aria
  - focus-management
  - keyboard-navigation
  - wire-service-mock
triggers:
  - "add accessibility assertions to my LWC jest tests"
  - "how do I test focus management in LWC"
  - "jest test for keyboard navigation in a lightning web component"
  - "integrate axe-core into sfdx-lwc-jest"
  - "assert aria-expanded toggles correctly after click"
  - "how do I prove the LWC is accessible in CI"
  - "test focus traps in a custom modal LWC"
  - "tab order assertions in a jest test"
  - "the lwc passes axe in chrome but fails the jest a11y check"
inputs:
  - "Component under test (HTML / JS / template) and its accessibility-bearing markup (roles, labels, aria-* attributes, focus targets)"
  - "Existing Jest setup — `package.json`, `jest.config.js`, presence of `@salesforce/sfdx-lwc-jest`"
  - "Whether the component uses `@wire` adapters, imperative Apex, navigation, or LMS"
  - "Which a11y dimensions matter: ARIA state, accessible name, focus management, keyboard navigation, contrast (out of scope for jest), screen-reader output (out of scope for jest)"
outputs:
  - "Jest test file(s) covering render, interaction, AND a11y assertions in the same suite"
  - "List of a11y dimensions that CAN be asserted in jest vs those that must be deferred to UTAM / manual QA"
  - "Optional: `axe-core` integration recipe with the caveats that apply to the LWC jest jsdom environment"
  - "CI gate recommendation — which assertions are blocking vs informational"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-08
---

# LWC Jest Testing with Accessibility

Activate this skill when the component already has (or needs) Jest tests and the test plan must prove accessibility behavior — not just rendering and event wiring. The skill is the accessibility-deep-dive sibling of `lwc/lwc-testing`. The core test harness is the same; the difference is what you assert.

---

## Before Starting

Gather this context before writing the test:

- **What a11y dimensions actually live in the component.** Tests can only assert what the component is responsible for. A component that consumes `lightning-input` inherits a lot of accessibility from the base component — you don't re-test SLDS. What you DO test is the markup *your* template adds: `role`, `aria-*`, `tabindex`, dynamic accessible-name updates, focus-target wiring, keyboard handlers.
- **What the jsdom environment can and cannot do.** `@salesforce/sfdx-lwc-jest` runs in jsdom under Node. jsdom has no layout engine, no real focus visualization, no actual screen reader. You can read `aria-*` attributes and check `document.activeElement`, but you cannot assert pixel positions, computed contrast, or screen-reader announcements. Plan accordingly — jest catches structural regressions; manual or UTAM testing catches sensory ones.
- **Whether Locker Service is in play.** It is not, in jest. jest runs the component in a plain Node + jsdom context with no Locker Service or Lightning Locker. Tests that pass in jest can still fail at runtime due to Locker restrictions — keep a Locker-aware end-to-end check separately.
- **Existing setup in the project.** Check `package.json` for `@salesforce/sfdx-lwc-jest` and a `test:unit` script. Check `jest.config.js` for the official Salesforce preset. If either is missing, the first deliverable is the setup, not the assertions.
- **Whether you're going to add `axe-core`.** `axe-core` works in jsdom but with caveats — it cannot evaluate computed style or rendered layout, so a "passes axe in jest" result is a *structural* pass, not a full a11y pass. Decide upfront whether to integrate it (for fail-fast on common ARIA mistakes) or skip it (for less ceremony) and document the choice.

---

## Core Concepts

### Concept 1 — The `createElement` + `document.body.appendChild` harness

Every LWC jest test follows the same render harness:

```js
import { createElement } from 'lwc';
import MyComponent from 'c/myComponent';

describe('c-my-component', () => {
    afterEach(() => {
        // Clear DOM between tests so state doesn't leak.
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
        // Clear any leftover async calls.
        jest.clearAllMocks();
    });

    it('renders with the correct accessible name', async () => {
        const element = createElement('c-my-component', { is: MyComponent });
        element.label = 'Customer details';
        document.body.appendChild(element);
        await Promise.resolve(); // wait for first render
        const region = element.shadowRoot.querySelector('[role="region"]');
        expect(region.getAttribute('aria-label')).toBe('Customer details');
    });
});
```

Two things are non-negotiable:

1. **`shadowRoot` queries.** LWC uses Shadow DOM (synthetic in older API versions, native in newer). Inside the test, query through `element.shadowRoot.querySelector(...)` — never through `document.querySelector`, which won't pierce the shadow boundary.
2. **Wait for render before assertions.** LWC re-renders asynchronously. `await Promise.resolve()` flushes the microtask queue and lets pending re-renders settle. Skip this and your assertion runs before the DOM updates, producing flaky tests. For multiple re-render cycles, chain multiple awaits or use a `flushPromises()` helper.

The same harness handles a11y assertions — there is no special "a11y mode." You use it to read `aria-*` attributes, query focusable elements, dispatch keyboard events, and check `document.activeElement`.

### Concept 2 — A11y assertions you CAN make in jest

These structural a11y dimensions are reliably testable in the jest jsdom environment:

| Dimension | Test approach |
|---|---|
| Static ARIA attributes | `el.getAttribute('aria-label')`, `getAttribute('role')`, etc. |
| Dynamic ARIA state | Toggle the component, `await Promise.resolve()`, re-read `aria-expanded` / `aria-pressed` / `aria-selected` |
| Accessible name | `getAttribute('aria-label')` OR `getAttribute('aria-labelledby')` resolved against the referenced element's text |
| Focus management | `expect(element.shadowRoot.activeElement).toBe(expectedEl)` after an action |
| Keyboard handlers | Dispatch `new KeyboardEvent('keydown', { key: 'Escape' })` and assert state change |
| `tabindex` correctness | Read `tabindex`; assert `-1` for programmatically-focused elements, `0` for tab-stops |
| Live region usage | Query `[role="status"]` / `[aria-live]` and assert text content updates after async |
| `aria-describedby` wiring | Read the attribute, then look up the referenced ID inside `shadowRoot` to confirm it resolves |

These dimensions are NOT reliably testable in jest jsdom — defer to UTAM, real-browser e2e, or manual QA:

- **Computed contrast** — jsdom has no rendering layer.
- **Visible focus indicator** — no real layout / `:focus-visible` evaluation.
- **Screen-reader announcement order** — no AT integration in jsdom.
- **`prefers-reduced-motion` and other media queries** — partial / unreliable in jsdom.
- **Layout-dependent role inferences** (e.g. table semantics, scroll containers).

Knowing the jest/jsdom boundary is the difference between a useful test and a misleading "looks accessible" badge.

### Concept 3 — Mocking `@wire` and imperative Apex without breaking a11y assertions

Wire and Apex mocks are essential because jest does not have a Salesforce server. Two official patterns:

**Wire adapters** — use the test wire adapter helpers bundled with `@salesforce/sfdx-lwc-jest`:

```js
import { createElement } from 'lwc';
import { registerApexTestWireAdapter } from '@salesforce/sfdx-lwc-jest';
import getCases from '@salesforce/apex/CaseController.getCases';
import CaseList from 'c/caseList';

const getCasesAdapter = registerApexTestWireAdapter(getCases);

it('shows accessible empty state when no cases', async () => {
    const element = createElement('c-case-list', { is: CaseList });
    document.body.appendChild(element);
    getCasesAdapter.emit([]); // simulate wire returning empty
    await Promise.resolve();
    const empty = element.shadowRoot.querySelector('[role="status"]');
    expect(empty).not.toBeNull();
    expect(empty.textContent).toContain('No cases');
});
```

**Imperative Apex** — use `jest.mock` with `jest.fn()` returning a Promise:

```js
jest.mock(
    '@salesforce/apex/CaseController.assignCase',
    () => ({ default: jest.fn() }),
    { virtual: true }
);
import assignCase from '@salesforce/apex/CaseController.assignCase';

it('announces success in the live region after assignment', async () => {
    assignCase.mockResolvedValue({ status: 'OK' });
    // ... interact with component, then:
    await Promise.resolve(); // flush click handler
    await Promise.resolve(); // flush mockResolvedValue microtask
    await Promise.resolve(); // flush re-render
    const liveRegion = element.shadowRoot.querySelector('[aria-live="polite"]');
    expect(liveRegion.textContent).toContain('assigned');
});
```

The `{ virtual: true }` option is required because `@salesforce/apex/...` is a virtual module resolved at compile time on the platform — jest needs to be told it's OK that the module doesn't exist on disk.

A11y assertions sit immediately after the mocked async settles. The dance with three `await Promise.resolve()`s exists because click → mock resolution → re-render is three microtasks, not one.

### Concept 4 — `axe-core` integration: structural pass only, with caveats

`axe-core` (https://github.com/dequelabs/axe-core) can run inside jsdom and check a defined subset of WCAG rules — those that don't depend on rendered layout or computed style. The integration via `jest-axe` looks like:

```js
import { axe, toHaveNoViolations } from 'jest-axe';
expect.extend(toHaveNoViolations);

it('has no axe violations in the default state', async () => {
    const element = createElement('c-my-component', { is: MyComponent });
    document.body.appendChild(element);
    await Promise.resolve();
    // axe needs the DOM subtree — pass shadowRoot or the element host.
    const results = await axe(element.shadowRoot);
    expect(results).toHaveNoViolations();
});
```

What axe-in-jest catches:

- Missing `alt` on `img`
- Missing accessible name on interactive elements
- Invalid ARIA attribute usage (e.g. `aria-checked` on a non-checkbox role)
- Duplicate IDs in the rendered subtree
- ARIA role / required-children mismatches

What it does NOT catch (because jsdom can't compute layout):

- Color contrast (`color-contrast` rule is unreliable / disabled by default in jsdom)
- Visible focus indicator
- Reading order vs DOM order in flexbox/grid
- Touch target size

Treat `axe(...)` in jest as an extra gate against ARIA mistakes, not as a full a11y certificate. The "passes axe in jest" claim should always be paired with a manual or UTAM-based real-browser axe pass before release.

---

## Recommended Workflow

1. **Inventory the component's a11y surface.** Open the component template; list every `role`, `aria-*`, `tabindex`, focus target, and keyboard handler. Each is a candidate assertion. If the list is empty, the component may not need a dedicated a11y test (e.g. a thin display-only wrapper around `lightning-card`).
2. **Confirm the jest setup.** `package.json` should depend on `@salesforce/sfdx-lwc-jest`. `jest.config.js` should extend the Salesforce preset (`module.exports = require('@salesforce/sfdx-lwc-jest/config');`). If missing, follow the current `sfdx-lwc-jest` README to install. Without these, none of the assertions in this skill will work.
3. **Write the render + accessible-name baseline.** Start with one test that renders the component in a default state and asserts the accessible name (`aria-label` or `aria-labelledby` chain). This is the cheapest, highest-signal a11y test — if it fails, the component has no accessible identity at all.
4. **Add interaction-driven ARIA-state tests.** For every `aria-expanded`, `aria-pressed`, `aria-selected`, or `aria-checked` your template emits, add one test that toggles the underlying state and asserts the attribute follows. This is where most real a11y regressions happen.
5. **Add focus-management and keyboard-handler tests.** If the component manages focus on open/close (modal, popover, accordion) or implements a keyboard handler (`Escape` to close, `Arrow` to navigate), add a test that dispatches the event and asserts both the state change AND `shadowRoot.activeElement`.
6. **Decide on axe-core.** If the team wants a fail-fast gate against ARIA mistakes, add `jest-axe` and a single per-state axe assertion. Document in the PR description that axe-in-jest does NOT replace browser axe checks. If the team prefers minimal ceremony, skip it — explicit assertions are usually more maintainable.
7. **Run the bundled checker against the project.** `python3 scripts/check_lwc_jest_testing_with_accessibility.py --root force-app/main/default` enumerates LWC components without test files, test files without a11y assertions, and `package.json` lacking the official preset.

---

## Related Skills

- `lwc/lwc-testing` — general LWC jest setup, wire / Apex / navigation / LMS mock recipes; this skill assumes that one as a base
- `lwc/lwc-accessibility-patterns` — how to *build* accessible LWC markup (the source of what this skill asserts against)
- `lwc/lwc-async-patterns` — `flushPromises` and microtask handling — relevant whenever the a11y assertion sits after an async resolve
- `lwc/common-lwc-runtime-errors` — Locker-Service / shadow-DOM gotchas that don't reproduce in jest
