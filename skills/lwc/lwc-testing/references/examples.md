# Examples - LWC Testing

## Example 1: Testing A Wired Record Viewer

**Context:** A component displays an Account name through a wire adapter and shows an inline error state when the wire fails.

**Problem:** The initial tests only assert that the component mounts. They never prove that data and error states render correctly.

**Solution:**

```js
import { createElement } from 'lwc';
import AccountSummary from 'c/accountSummary';
import { registerApexTestWireAdapter } from '@salesforce/sfdx-lwc-jest';
import getAccountSummary from '@salesforce/apex/AccountController.getAccountSummary';

const getAccountSummaryAdapter = registerApexTestWireAdapter(getAccountSummary);

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

        getAccountSummaryAdapter.emit({ name: 'Acme' });
        await flushPromises();

        expect(element.shadowRoot.querySelector('[data-id=\"name\"]').textContent).toBe('Acme');
    });
});
```

**Why it works:** The test exercises the actual wire contract and waits for rerender before asserting.

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
