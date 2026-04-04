# Examples — LWC Imperative Apex

## Example 1: Save Form Data With Loading Spinner and Toast

**Context:** A custom record edit form collects field values in a Lightning Web Component and saves them via an Apex upsert method when the user clicks a Save button. The form must disable the button while the save is in progress and show a toast on success or failure.

**Problem:** Without explicit loading state management and error handling, the form allows double-submission (user clicks Save again while the first call is in-flight) and displays a raw JavaScript error object — which renders as `[object Object]` — instead of a readable message.

**Solution:**

Apex class:
```apex
public with sharing class ContactSaveController {
    @AuraEnabled
    public static Id saveContact(Contact contact) {
        upsert contact;
        return contact.Id;
    }
}
```

LWC JavaScript:
```js
import { LightningElement, api } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import saveContact from '@salesforce/apex/ContactSaveController.saveContact';

function getErrorMessage(error) {
    if (Array.isArray(error.body)) {
        return error.body.map(e => e.message).join(', ');
    }
    if (typeof error.body?.message === 'string') {
        return error.body.message;
    }
    return error.message ?? 'Unknown error';
}

export default class ContactForm extends LightningElement {
    @api recordId;
    isLoading = false;
    draftContact = {};

    handleFieldChange(event) {
        this.draftContact = { ...this.draftContact, [event.target.fieldName]: event.target.value };
    }

    async handleSave() {
        this.isLoading = true;
        try {
            const savedId = await saveContact({ contact: this.draftContact });
            this.dispatchEvent(new ShowToastEvent({
                title: 'Success',
                message: `Contact saved: ${savedId}`,
                variant: 'success'
            }));
            this.draftContact = {};
        } catch (error) {
            this.dispatchEvent(new ShowToastEvent({
                title: 'Save failed',
                message: getErrorMessage(error),
                variant: 'error'
            }));
        } finally {
            this.isLoading = false;
        }
    }
}
```

LWC HTML (relevant portion):
```html
<lightning-button
    label="Save"
    onclick={handleSave}
    disabled={isLoading}
></lightning-button>
<template if:true={isLoading}>
    <lightning-spinner alternative-text="Saving..."></lightning-spinner>
</template>
```

**Why it works:** The `isLoading = true` line executes synchronously before the async call, so the button disables immediately on click. The `finally` block resets it regardless of outcome. `getErrorMessage` handles both the single-message shape (`error.body.message`) and the array shape (`error.body[].message`) that Apex validation rule violations return.

---

## Example 2: Load Multiple Related Data Sets in Parallel on Component Mount

**Context:** A custom Account detail panel needs to display both open opportunities and active contacts for the account when the component loads. Each data set comes from a different Apex method.

**Problem:** Calling the two methods sequentially with `await` means the second call does not start until the first completes, adding avoidable round-trip latency. On slow connections or large result sets, this is noticeable to users.

**Solution:**

Apex class:
```apex
public with sharing class AccountDetailController {
    @AuraEnabled(cacheable=true)
    public static List<Opportunity> getOpenOpportunities(Id accountId) {
        return [SELECT Id, Name, Amount, CloseDate FROM Opportunity
                WHERE AccountId = :accountId AND IsClosed = false];
    }

    @AuraEnabled(cacheable=true)
    public static List<Contact> getActiveContacts(Id accountId) {
        return [SELECT Id, Name, Email, Title FROM Contact
                WHERE AccountId = :accountId AND IsDeleted = false];
    }
}
```

LWC JavaScript:
```js
import { LightningElement, api } from 'lwc';
import getOpenOpportunities from '@salesforce/apex/AccountDetailController.getOpenOpportunities';
import getActiveContacts from '@salesforce/apex/AccountDetailController.getActiveContacts';

function getErrorMessage(error) {
    if (Array.isArray(error.body)) {
        return error.body.map(e => e.message).join(', ');
    }
    if (typeof error.body?.message === 'string') {
        return error.body.message;
    }
    return error.message ?? 'Unknown error';
}

export default class AccountDetail extends LightningElement {
    @api recordId;
    opportunities = [];
    contacts = [];
    error;
    isLoading = false;

    async connectedCallback() {
        this.isLoading = true;
        try {
            const [opps, cons] = await Promise.all([
                getOpenOpportunities({ accountId: this.recordId }),
                getActiveContacts({ accountId: this.recordId })
            ]);
            this.opportunities = opps;
            this.contacts = cons;
            this.error = undefined;
        } catch (error) {
            this.error = getErrorMessage(error);
            this.opportunities = [];
            this.contacts = [];
        } finally {
            this.isLoading = false;
        }
    }
}
```

**Why it works:** `Promise.all` fires both Apex calls in the same event-loop tick. The LWC framework sends both HTTP requests to the Salesforce server nearly simultaneously. The component waits for both to resolve before rendering data, reducing total load time compared to sequential awaits. Both methods are `cacheable=true` because they are read-only queries — the Lightning Data Service cache can serve repeated calls to the same record without a network round-trip.

---

## Anti-Pattern: Using refreshApex on an Imperatively Populated Variable

**What practitioners do:** After writing a record via an imperative save call, they call `refreshApex(this.contacts)` expecting the contacts list to refresh with the latest data — mirroring how `refreshApex` works with wire results.

**What goes wrong:** `refreshApex()` only works with wire-provisioned values. When called on a plain reactive property populated by an imperative call, it silently does nothing and returns a resolved Promise. The data stays stale. No error is thrown and no warning appears in the console, making this extremely hard to diagnose.

**Correct approach:** Re-call the Apex method imperatively after the write and assign the result back to the reactive property:

```js
// After a successful write:
this.contacts = await getContacts({ accountId: this.recordId });
```

This forces a fresh server round-trip and updates the component's reactive property, triggering a re-render with the latest data.
