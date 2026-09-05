# Examples - LWC Testing

## Example 1: Testing A Wired Record Viewer

**Context:** A component displays an Account name through a wire adapter and shows an inline error state when the wire fails.

**Problem:** The initial tests only assert that the component mounts. They never prove that data and error states render correctly.

**Solution:**

```js
import { createElement } from 'lwc';
import AccountSummary from 'c/accountSummary';
import getAccountSummary from '@salesforce/apex/AccountController.getAccountSummary';

// Mock the Apex module with a test wire adapter. The mocked default export
// IS the adapter, so `getAccountSummary.emit(...)` drives the wire directly —
// no separate register* step (that was the 2.x API, removed in 3.x).
jest.mock(
    '@salesforce/apex/AccountController.getAccountSummary',
    () => {
        const { createApexTestWireAdapter } = require('@salesforce/sfdx-lwc-jest');
        return { default: createApexTestWireAdapter(jest.fn()) };
    },
    { virtual: true }
);

const flushPromises = () => Promise.resolve();

describe('c-account-summary', () => {
    afterEach(() => {
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
    });

    it('renders account data from the wire', async () => {
        const element = createElement('c-account-summary', { is: AccountSummary });
        element.recordId = '001000000000001AAA';
        document.body.appendChild(element);

        getAccountSummary.emit({ name: 'Acme' });
        await flushPromises();

        expect(element.shadowRoot.querySelector('[data-id=\"name\"]').textContent).toBe('Acme');
    });
});
```

**Why it works:** The test exercises the actual wire contract and waits for rerender before asserting.

**UNVERIFIED (2026-09-05): `createApexTestWireAdapter` is not named in the Lightning Web Components Developer Guide.** The guide describes the generation change in prose — registering the adapter under test "was" required in Spring '21 and earlier and "isn't recommended" now (`lwc_guide unit-testing-using-wire-utility L12562`) — but the function names come from the `wire-service-jest-util` README. The guide's own worked example needs no `jest.mock` at all for an LDS adapter: it imports `getRecord` from `lightning/uiRecordApi` and calls `getRecord.emit(mock)` on the sfdx-lwc-jest stub (`L12547-L12554`). Use that plainer form for `lightning/ui*Api` adapters; the `create*TestWireAdapter` factory is for wiring an *Apex* method as an adapter, and carries this marker.

**UNVERIFIED (2026-09-05): `flushPromises` does not appear in the crawled guide.** It is this repo's local helper (see `templates/lwc/component-skeleton/__tests__/componentSkeleton.test.js`); the guide writes `await Promise.resolve()` (`L12485`).

---

## Example 2: Testing An Imperative Save Path

**Context:** A form component saves through an imperative Apex call and then shows a success state.

**Problem:** The test suite never covers the rejected promise path, so production errors only appear after deployment.

**Solution:**

```js
import { createElement } from 'lwc';
import ContactEditor from 'c/contactEditor';
import saveContact from '@salesforce/apex/ContactController.saveContact';

jest.mock(
    '@salesforce/apex/ContactController.saveContact',
    () => ({ default: jest.fn() }),
    { virtual: true }
);

const flushPromises = () => Promise.resolve();

it('shows an error state when save fails', async () => {
    saveContact.mockRejectedValue({ body: { message: 'Validation failed' } });

    const element = createElement('c-contact-editor', { is: ContactEditor });
    document.body.appendChild(element);

    element.shadowRoot.querySelector('lightning-button').click();
    await flushPromises();

    expect(element.shadowRoot.querySelector('[data-id=\"error\"]')).not.toBeNull();
});
```

**Why it works:** The test matches the imperative contract and proves the failure state instead of only the happy path.

---

## Anti-Pattern: Snapshot-Only Testing

**What practitioners do:** They add a snapshot test after rendering the component once and consider the component covered.

**What goes wrong:** The suite does not prove user interactions, error handling, wire updates, or event dispatching. Snapshot churn also makes reviews noisy.

**Correct approach:** Use focused assertions around behavior, events, and state transitions. Add snapshots only when a stable structural contract truly matters.

A snapshot is not a behavioural assertion. Replace it with the state transition it was standing in for — assert the *before* and the *after*, with the awaited boundary between them, so the test fails when the transition stops happening:

```js
it('swaps the spinner for the row list once the wire provisions data', async () => {
    const element = createElement('c-order-list', { is: OrderList });
    document.body.appendChild(element);

    // Before: loading state, no rows. This half is what a snapshot silently accepts.
    expect(element.shadowRoot.querySelector('lightning-spinner')).not.toBeNull();
    expect(element.shadowRoot.querySelectorAll('[data-id="order-row"]')).toHaveLength(0);

    getOrders.emit([{ Id: '801000000000001AAA', Name: 'ORD-1' }]);
    await Promise.resolve();

    // After: spinner gone, exactly one row, and the row carries the real value.
    expect(element.shadowRoot.querySelector('lightning-spinner')).toBeNull();
    const rows = element.shadowRoot.querySelectorAll('[data-id="order-row"]');
    expect(rows).toHaveLength(1);
    expect(rows[0].textContent).toBe('ORD-1');
});
```

Three properties a snapshot cannot give you: the assertion names the transition, it fails if the spinner never clears, and it fails if the row renders empty. `toHaveLength(0)` before and `toHaveLength(1)` after is the part that makes the test capable of going red — see the verification table in `references/code-examples.md`.
