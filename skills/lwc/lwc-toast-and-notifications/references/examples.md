# Examples — LWC Toast And Notifications

## Example 1: Success Toast After Apex Save Operation

**Context:** A contact editor component calls an Apex method to persist changes. The user needs confirmation that the save succeeded, and must be clearly informed if it failed.

**Problem:** The original implementation called `window.alert('Saved!')` which Locker Service blocks, and it did not differentiate between success and error feedback. Error messages disappeared too quickly to act on.

**Solution:**

```javascript
// contactEditor.js
import { LightningElement, api } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import saveContact from '@salesforce/apex/ContactController.saveContact';

export default class ContactEditor extends LightningElement {
    @api recordId;
    isSaving = false;

    async handleSave() {
        this.isSaving = true;
        try {
            await saveContact({ contactId: this.recordId });
            this.dispatchEvent(
                new ShowToastEvent({
                    title: 'Contact Saved',
                    message: 'Your changes have been saved successfully.',
                    variant: 'success'
                    // mode defaults to 'dismissable' — correct for success
                })
            );
        } catch (error) {
            this.dispatchEvent(
                new ShowToastEvent({
                    title: 'Save Failed',
                    message: error?.body?.message ?? 'An unexpected error occurred. Please try again.',
                    variant: 'error',
                    mode: 'sticky'  // sticky so the user cannot accidentally dismiss an error
                })
            );
        } finally {
            this.isSaving = false;
        }
    }
}
```

**Jest test to verify toast dispatch:**

```javascript
// contactEditor.test.js
import { createElement } from 'lwc';
import ContactEditor from 'c/contactEditor';
import saveContact from '@salesforce/apex/ContactController.saveContact';
import { ShowToastEventName } from 'lightning/platformShowToastEvent';

jest.mock('@salesforce/apex/ContactController.saveContact', () => ({
    default: jest.fn()
}), { virtual: true });

describe('contactEditor — toast feedback', () => {
    afterEach(() => {
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
    });

    it('dispatches success toast after save', async () => {
        saveContact.mockResolvedValue(undefined);

        const element = createElement('c-contact-editor', { is: ContactEditor });
        element.recordId = '003xx000000XXXX';
        document.body.appendChild(element);

        const toastHandler = jest.fn();
        element.addEventListener(ShowToastEventName, toastHandler);

        element.shadowRoot.querySelector('[data-id="save-button"]').click();
        await Promise.resolve();
        await Promise.resolve(); // flush async

        expect(toastHandler).toHaveBeenCalledTimes(1);
        const detail = toastHandler.mock.calls[0][0].detail;
        expect(detail.variant).toBe('success');
    });

    it('dispatches sticky error toast on failure', async () => {
        saveContact.mockRejectedValue({ body: { message: 'Server error' } });

        const element = createElement('c-contact-editor', { is: ContactEditor });
        element.recordId = '003xx000000XXXX';
        document.body.appendChild(element);

        const toastHandler = jest.fn();
        element.addEventListener(ShowToastEventName, toastHandler);

        element.shadowRoot.querySelector('[data-id="save-button"]').click();
        await Promise.resolve();
        await Promise.resolve();

        const detail = toastHandler.mock.calls[0][0].detail;
        expect(detail.variant).toBe('error');
        expect(detail.mode).toBe('sticky');
    });
});
```

**Why it works:** Using `mode: 'sticky'` for errors ensures the user cannot accidentally dismiss an important failure message before reading it. The try/catch/finally pattern guarantees `isSaving` resets regardless of outcome, and the default `dismissable` mode on success keeps the UX unobtrusive.

---

## Example 2: Confirm Dialog Before Destructive Action Using lightning-confirm

**Context:** A case manager component allows supervisors to bulk-close cases. Closing is permanent — it triggers downstream automation and cannot be reversed.

**Problem:** The first version executed the bulk close immediately on button click. Users accidentally triggered it, and the team added a `LightningModal` with a paragraph of instructions. The modal was heavier than the decision warranted and slowed the user down on a frequent action.

**Solution:**

```javascript
// caseManager.js
import { LightningElement, api } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import LightningConfirm from 'lightning/confirm';
import bulkCloseCases from '@salesforce/apex/CaseController.bulkCloseCases';

export default class CaseManager extends LightningElement {
    @api selectedCaseIds = [];

    async handleBulkClose() {
        if (!this.selectedCaseIds.length) return;

        const confirmed = await LightningConfirm.open({
            message: `Close ${this.selectedCaseIds.length} selected case(s)? This action cannot be undone.`,
            theme: 'warning',
            label: 'Confirm Bulk Close'
        });

        if (!confirmed) return;

        try {
            await bulkCloseCases({ caseIds: this.selectedCaseIds });
            this.dispatchEvent(
                new ShowToastEvent({
                    title: 'Cases Closed',
                    message: `{0} case(s) were closed successfully.`,
                    messageData: [String(this.selectedCaseIds.length)],
                    variant: 'success'
                })
            );
            this.dispatchEvent(new CustomEvent('refresh'));
        } catch (error) {
            this.dispatchEvent(
                new ShowToastEvent({
                    title: 'Bulk Close Failed',
                    message: error?.body?.message ?? 'An error occurred during bulk close.',
                    variant: 'error',
                    mode: 'sticky'
                })
            );
        }
    }
}
```

**Why it works:** `LightningConfirm.open()` is a promise that resolves to `true` or `false`, making the guard clause clean and avoiding nested callbacks. The `messageData` substitution dynamically inserts the count without string concatenation in the `message` parameter. The pattern keeps the confirmation lean while preventing accidental destructive operations.

---

## Anti-Pattern: Using window.alert() or window.confirm() in LWC

**What practitioners do:** Developers familiar with vanilla JS use `window.alert('Saved!')` or `window.confirm('Are you sure?')` inside LWC component handlers.

**What goes wrong:** Locker Service intercepts and silences native browser dialog calls in Lightning Experience. `window.alert()` does nothing; `window.confirm()` always returns `false` in some container contexts. The behavior differs between Lightning Experience, Experience Cloud, and local Jest tests, making the component behave inconsistently across environments.

**Correct approach:** Use `ShowToastEvent` for non-blocking notifications, `lightning-alert` for mandatory-read messages, and `lightning-confirm` for boolean-decision gates. These are platform-supported primitives with predictable behavior across all LWC deployment contexts.
