# Examples — LWC Toast And Notifications

## Example 1: Success Toast After Apex Save Operation

**Context:** A contact editor component calls an Apex method to persist changes. The user needs confirmation that the save succeeded, and must be clearly informed if it failed.

**Problem:** The original implementation called `window.alert('Saved!')`, which the platform documents as the wrong primitive — "the HTML specification has deprecated support for the window.alert(), window.confirm(), and window.prompt() methods when used in a third-party context" and the native calls "aren't supported for cross-origin iframes in Chrome and Safari" (`lwc_guide base-components-patterns L4768`; `use-dialog-alert L10401`). It also did not differentiate success from error feedback, and error messages disappeared before anyone could act on them.

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

**Why it works:** The error branch reads `error.body.message`, which is the shape the guide's own samples read (`lwc_guide data-table-inline-edit L5703`), so the user sees a sentence rather than `[object Object]`. The try/catch/finally pattern guarantees `isSaving` resets regardless of outcome, and the success message stays out of the user's way.

UNVERIFIED (2026-09-05): `mode: 'sticky'` and the claim that the default mode is `dismissable` are not printed in the crawled Developer Guide, which names `mode` as a property and notes only that its sample "uses the default value for mode" (`lwc_guide use-toast L10456`). The value list lives on the platformShowToastEvent Component Library specification page. The design intent — a failure the user must act on can outlive a routine confirmation — holds regardless; the literal needs checking.

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

**Why it works:** `LightningConfirm.open()` "returns a promise that resolves to `true` when you click OK and `false` when you click Cancel" (`lwc_guide use-dialog-confirm L10418`), so the guard is a plain early return rather than a nested callback. The gate sits before the Apex call, which is the only place the user can still change their mind, and both branches are mockable in Jest.

UNVERIFIED (2026-09-05): two literals in this example are not grounded in the crawled guide. `theme: 'warning'` — the guide names confirm's third parameter as `variant`, not `theme` (`use-dialog-confirm L10418`, against `theme` for alert at `L10404` and prompt at `L10432`), and prints no value list for either. `messageData` — the property does not appear anywhere in the crawled guide; placeholder substitution is documented only for `lightning/toast`, whose `label` and `message` "support inline links using the placeholder syntax {N} or {linkName}" (`use-toast L10451`), while the event module does not support inline links in the title (`L10449`). Check both against the Component Library specifications before copying this example verbatim.

---

## Anti-Pattern: Using window.alert() or window.confirm() in LWC

**What practitioners do:** Developers familiar with vanilla JS use `window.alert('Saved!')` or `window.confirm('Are you sure?')` inside LWC component handlers.

**What goes wrong:** The HTML specification has deprecated `window.alert()`, `window.confirm()`, and `window.prompt()` in third-party contexts, and Chrome and Safari do not support them in cross-origin iframes (`lwc_guide base-components-patterns L4768`; `use-dialog-alert L10401`, `use-dialog-confirm L10415`, `use-dialog-prompt L10429`). The behaviour therefore depends on the browser and the container the component is embedded in, and differs again in local Jest tests where jsdom stubs them. The second failure is structural: the native calls block, and their replacements do not — "these modules' `.open()` method don't halt execution on the page, and they each return a promise" (`base-components-patterns L4769`). Code written for a blocking `confirm()` keeps running past the question.

UNVERIFIED (2026-09-05): the frequently-repeated claim that Lightning Locker intercepts and silences these calls is not stated anywhere in the crawled Lightning Web Components Developer Guide. The documented reasons are the HTML specification deprecation and the cross-origin iframe gap above. Do not attribute the behaviour to Locker without a source.

**Correct approach:** Use a toast for non-blocking feedback, `lightning/alert` for a message that must be acknowledged, `lightning/confirm` for a boolean gate, and `lightning/prompt` when a value is needed. Move the post-decision code inside the `await`:

```javascript
import LightningConfirm from 'lightning/confirm';

// Before: execution blocked here and continued on the next line.
//   if (window.confirm('Delete this record?')) { deleteRecord(this.recordId); }

// After: .open() returns a promise, so the branch moves inside the await
// (lwc_guide base-components-patterns L4769; use-dialog-confirm L10418).
async handleDelete() {
    const confirmed = await LightningConfirm.open({
        label: 'Delete record',
        message: 'This record cannot be recovered. Delete it?'
    });
    if (!confirmed) {
        return;
    }
    await deleteRecord(this.recordId);
}
```

These are the platform-supported primitives, and the promise makes the decision point explicit in the diff and mockable in Jest — see `references/code-examples.md` § 4.
