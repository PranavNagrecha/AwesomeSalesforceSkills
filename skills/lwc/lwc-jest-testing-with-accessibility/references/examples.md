# Examples — LWC Jest Testing with Accessibility

Six concrete tests in roughly increasing complexity. Each example is a working `*.test.js` you can adapt to your own component. The same render harness is reused — only the assertions change.

Project layout assumed:

```
force-app/main/default/lwc/<componentName>/
  ├── <componentName>.html
  ├── <componentName>.js
  ├── <componentName>.js-meta.xml
  └── __tests__/
      └── <componentName>.test.js
```

Each test sits in `__tests__/`. `package.json` includes `@salesforce/sfdx-lwc-jest` as a devDependency and a `test:unit` script.

---

## Example 1 — Simple render + accessible name

**Component goal:** A status banner with an `aria-label` driven by a public property.

**Test goal:** Prove the component renders and exposes the right accessible name.

```js
// statusBanner.test.js
import { createElement } from 'lwc';
import StatusBanner from 'c/statusBanner';

describe('c-status-banner', () => {
    afterEach(() => {
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
        jest.clearAllMocks();
    });

    it('renders with role="status" and the supplied aria-label', async () => {
        const element = createElement('c-status-banner', { is: StatusBanner });
        element.label = 'Save complete';
        document.body.appendChild(element);

        await Promise.resolve(); // first render

        const banner = element.shadowRoot.querySelector('[role="status"]');
        expect(banner).not.toBeNull();
        expect(banner.getAttribute('aria-label')).toBe('Save complete');
    });
});
```

**What to notice:**

- `await Promise.resolve()` flushes the microtask queue once, giving LWC a render cycle.
- The query is `element.shadowRoot.querySelector(...)`, never `document.querySelector(...)`.
- `[role="status"]` is the assertion target — checking the *role* is what catches a regression where someone changed the markup to a plain `<div>`.

---

## Example 2 — Wire mock + accessible empty state

**Component goal:** A case list using `@wire(getCases)` that renders a `<ul>` of cases or a `[role="status"]` empty message.

**Test goal:** Simulate an empty wire response and assert the empty message has the correct ARIA role and live-region behavior.

```js
// caseList.test.js
import { createElement } from 'lwc';
import { registerApexTestWireAdapter } from '@salesforce/sfdx-lwc-jest';
import getCases from '@salesforce/apex/CaseController.getCases';
import CaseList from 'c/caseList';

const getCasesAdapter = registerApexTestWireAdapter(getCases);

describe('c-case-list — empty state a11y', () => {
    afterEach(() => {
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
        jest.clearAllMocks();
    });

    it('renders an accessible empty-state announcement when wire returns []', async () => {
        const element = createElement('c-case-list', { is: CaseList });
        document.body.appendChild(element);

        getCasesAdapter.emit([]); // simulate wire response
        await Promise.resolve();   // microtask: wire fires
        await Promise.resolve();   // microtask: re-render

        const empty = element.shadowRoot.querySelector('[role="status"]');
        expect(empty).not.toBeNull();
        expect(empty.getAttribute('aria-live')).toBe('polite');
        expect(empty.textContent.trim()).toBe('No cases assigned');
    });
});
```

**What to notice:**

- `registerApexTestWireAdapter(getCases)` returns a handle whose `.emit(...)` pushes data into the wire.
- Two `await Promise.resolve()` calls — one for the wire, one for the resulting re-render. With one, the assertion runs before the empty state is in the DOM and you get a flaky test.
- Asserting `aria-live="polite"` is what proves the empty state announces itself to screen readers when it appears mid-session.

---

## Example 3 — Button click + ARIA-state assertion

**Component goal:** A disclosure button that shows / hides a panel and reflects state via `aria-expanded`.

**Test goal:** Click the button, assert the panel renders AND `aria-expanded` flips correctly.

```js
// disclosurePanel.test.js
import { createElement } from 'lwc';
import DisclosurePanel from 'c/disclosurePanel';

describe('c-disclosure-panel', () => {
    afterEach(() => {
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
    });

    it('toggles aria-expanded when clicked', async () => {
        const element = createElement('c-disclosure-panel', { is: DisclosurePanel });
        document.body.appendChild(element);
        await Promise.resolve();

        const trigger = element.shadowRoot.querySelector('button.disclosure-trigger');
        expect(trigger.getAttribute('aria-expanded')).toBe('false');
        expect(trigger.getAttribute('aria-controls')).toBeTruthy();

        trigger.click();
        await Promise.resolve(); // re-render after state change

        expect(trigger.getAttribute('aria-expanded')).toBe('true');

        // The aria-controls target should now exist in the shadow tree.
        const controlledId = trigger.getAttribute('aria-controls');
        const panel = element.shadowRoot.getElementById(controlledId);
        expect(panel).not.toBeNull();
        expect(panel.hidden).toBe(false);

        trigger.click();
        await Promise.resolve();
        expect(trigger.getAttribute('aria-expanded')).toBe('false');
    });
});
```

**What to notice:**

- The test checks `aria-controls` resolves to a real element inside the shadow tree — a common regression is for the pointer to dangle after a refactor.
- Toggling the same button twice within one test catches "off-by-one toggle" bugs that a single click misses.

---

## Example 4 — Keyboard navigation + focus management

**Component goal:** A custom modal that opens, traps focus on the close button, and closes on `Escape`.

**Test goal:** Open the modal, assert focus moves to the close button, dispatch `Escape`, assert focus returns to the trigger.

```js
// confirmModal.test.js
import { createElement } from 'lwc';
import ConfirmModal from 'c/confirmModal';

describe('c-confirm-modal — focus + keyboard', () => {
    afterEach(() => {
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
    });

    it('moves focus into the modal on open and back to the trigger on Escape', async () => {
        const element = createElement('c-confirm-modal', { is: ConfirmModal });
        document.body.appendChild(element);
        await Promise.resolve();

        const trigger = element.shadowRoot.querySelector('button.open-modal');
        trigger.focus();
        expect(element.shadowRoot.activeElement).toBe(trigger);

        trigger.click();
        await Promise.resolve(); // open
        await Promise.resolve(); // post-open focus shift

        const dialog = element.shadowRoot.querySelector('[role="dialog"]');
        expect(dialog).not.toBeNull();
        expect(dialog.getAttribute('aria-modal')).toBe('true');
        expect(dialog.getAttribute('aria-labelledby')).toBeTruthy();

        // Focus should now be on the close button inside the dialog.
        const closeBtn = dialog.querySelector('button.close');
        expect(element.shadowRoot.activeElement).toBe(closeBtn);

        // Press Escape.
        dialog.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
        await Promise.resolve();
        await Promise.resolve();

        // Modal closed.
        expect(element.shadowRoot.querySelector('[role="dialog"]')).toBeNull();
        // Focus returned to the trigger that opened it.
        expect(element.shadowRoot.activeElement).toBe(trigger);
    });
});
```

**What to notice:**

- `element.shadowRoot.activeElement` is what you assert against, NOT `document.activeElement` — the active element inside a shadow root is a separate concept.
- `KeyboardEvent` with `bubbles: true` so the handler at the dialog or component level catches it.
- Asserting both directions of focus (in on open, back on close) is the test that actually proves the focus-management contract.

---

## Example 5 — `axe-core` integration via `jest-axe`

**Component goal:** Same disclosure panel as Example 3.

**Test goal:** Add a structural-a11y gate that runs `axe-core` on the rendered subtree.

**One-time install:** add `jest-axe` as a devDependency.

```bash
npm install --save-dev jest-axe
```

**Test:**

```js
// disclosurePanel.axe.test.js
import { createElement } from 'lwc';
import { axe, toHaveNoViolations } from 'jest-axe';
import DisclosurePanel from 'c/disclosurePanel';

expect.extend(toHaveNoViolations);

describe('c-disclosure-panel — axe', () => {
    afterEach(() => {
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
    });

    it('has no axe violations in the default (collapsed) state', async () => {
        const element = createElement('c-disclosure-panel', { is: DisclosurePanel });
        document.body.appendChild(element);
        await Promise.resolve();

        // axe needs a real DOM subtree — pass the shadowRoot.
        const results = await axe(element.shadowRoot, {
            // Disable rules that depend on layout or computed style — jsdom can't evaluate them.
            rules: {
                'color-contrast': { enabled: false }
            }
        });
        expect(results).toHaveNoViolations();
    });

    it('has no axe violations in the expanded state', async () => {
        const element = createElement('c-disclosure-panel', { is: DisclosurePanel });
        document.body.appendChild(element);
        await Promise.resolve();

        element.shadowRoot.querySelector('button.disclosure-trigger').click();
        await Promise.resolve();

        const results = await axe(element.shadowRoot, {
            rules: { 'color-contrast': { enabled: false } }
        });
        expect(results).toHaveNoViolations();
    });
});
```

**What to notice:**

- `axe(element.shadowRoot)` — pass the shadow root, otherwise axe sees the host element as a leaf with no internal structure.
- Both state branches are checked. A common bug is that the collapsed state passes axe but the expanded state introduces an `aria-controls` pointer to a non-existent ID.
- `color-contrast` is disabled because jsdom can't compute it. If the team needs contrast checks, run them in a real browser via UTAM or a Playwright-based axe runner — not jest.

---

## Example 6 — Live-region updates after imperative Apex

**Component goal:** A "Reassign Case" button that calls imperative Apex and announces success in a live region.

**Test goal:** Mock the Apex call, click the button, assert the live region announces the result.

```js
// reassignCase.test.js
import { createElement } from 'lwc';
import ReassignCase from 'c/reassignCase';

// Mock the imperative Apex module (virtual: true required for @salesforce/apex/...).
jest.mock(
    '@salesforce/apex/CaseController.assignCase',
    () => ({ default: jest.fn() }),
    { virtual: true }
);
import assignCase from '@salesforce/apex/CaseController.assignCase';

describe('c-reassign-case — live-region announcement', () => {
    afterEach(() => {
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
        jest.clearAllMocks();
    });

    it('announces success in [aria-live=polite] after Apex resolves', async () => {
        assignCase.mockResolvedValue({ status: 'OK', assignee: 'Alex' });

        const element = createElement('c-reassign-case', { is: ReassignCase });
        element.recordId = '5003i00000abcDeAAI';
        document.body.appendChild(element);
        await Promise.resolve();

        const liveRegion = element.shadowRoot.querySelector('[aria-live="polite"]');
        expect(liveRegion).not.toBeNull();
        expect(liveRegion.textContent.trim()).toBe(''); // empty before action

        const btn = element.shadowRoot.querySelector('button.reassign');
        btn.click();

        // Three microtask flushes: click handler → mock resolution → re-render.
        await Promise.resolve();
        await Promise.resolve();
        await Promise.resolve();

        expect(liveRegion.textContent).toContain('Case reassigned to Alex');
        expect(assignCase).toHaveBeenCalledWith({ caseId: '5003i00000abcDeAAI' });
    });

    it('announces error in [role=alert] when Apex rejects', async () => {
        assignCase.mockRejectedValue({ body: { message: 'Insufficient privileges' } });

        const element = createElement('c-reassign-case', { is: ReassignCase });
        element.recordId = '5003i00000abcDeAAI';
        document.body.appendChild(element);
        await Promise.resolve();

        element.shadowRoot.querySelector('button.reassign').click();
        await Promise.resolve();
        await Promise.resolve();
        await Promise.resolve();

        const alert = element.shadowRoot.querySelector('[role="alert"]');
        expect(alert).not.toBeNull();
        expect(alert.textContent).toContain('Insufficient privileges');
    });
});
```

**What to notice:**

- `aria-live="polite"` for non-critical announcements; `role="alert"` (which implies `aria-live="assertive"`) for errors. The test asserts the right channel for each.
- The triple `await Promise.resolve()` is the canonical "wait through one async + re-render" pattern. If you find yourself adding a fourth, the component probably has a chained promise; consider extracting a `flushPromises()` helper.
- Asserting both the success path and the error path is what proves the *contract* of the live region — not just that it exists.
