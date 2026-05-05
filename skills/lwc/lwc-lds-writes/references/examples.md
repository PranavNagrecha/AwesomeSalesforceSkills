# Examples — LWC LDS Writes

## Example 1: `lightning-record-edit-form` with custom save button

**Context:** A Case detail panel where the user edits Subject, Priority, and a custom `Reason__c` picklist, then clicks Save.

**Problem:** Hand-rolling `<lightning-input>` + `updateRecord` rebuilds field rendering and error display that the form already provides for free.

**Solution:**

```html
<template>
    <lightning-record-edit-form
        record-id={recordId}
        object-api-name="Case"
        onsuccess={handleSuccess}
        onerror={handleError}>
        <lightning-messages></lightning-messages>
        <lightning-input-field field-name="Subject"></lightning-input-field>
        <lightning-input-field field-name="Priority"></lightning-input-field>
        <lightning-input-field field-name="Reason__c"></lightning-input-field>
        <lightning-button
            class="slds-m-top_small"
            type="submit"
            label="Save Case"
            variant="brand">
        </lightning-button>
    </lightning-record-edit-form>
</template>
```

```javascript
import { LightningElement, api } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

export default class CaseQuickEdit extends LightningElement {
    @api recordId;

    handleSuccess() {
        this.dispatchEvent(new ShowToastEvent({ title: 'Case updated', variant: 'success' }));
    }

    handleError(event) {
        const detail = event.detail;
        this.dispatchEvent(new ShowToastEvent({
            title: 'Save failed',
            message: detail.message ?? detail.detail,
            variant: 'error'
        }));
    }
}
```

**Why it works:** `<lightning-messages>` renders both object-level and field-level errors from UI API automatically. `lightning-input-field` honors FLS, validation rules, and the field's compact-layout-driven rendering (lookups, picklists, dependent picklists). Zero JS write code.

---

## Example 2: imperative `updateRecord` with structured error mapping

**Context:** A wizard step component that persists three custom fields on Opportunity after the user clicks "Next." The component has a custom progress bar; a record-edit-form would not match the layout.

**Problem:** Hand-rolled error toasts lose the field-level granularity UI API already provides; users see "Save failed" with no clue which field is invalid.

**Solution:**

```javascript
import { LightningElement, api, track } from 'lwc';
import { updateRecord } from 'lightning/uiRecordApi';

import OPP_ID from '@salesforce/schema/Opportunity.Id';
import OPP_STAGE from '@salesforce/schema/Opportunity.StageName';
import OPP_REASON from '@salesforce/schema/Opportunity.LossReason__c';
import OPP_NEXT_STEP from '@salesforce/schema/Opportunity.NextStep';

export default class WizardStepCommit extends LightningElement {
    @api recordId;
    @track stage;
    @track lossReason;
    @track nextStep;
    @track fieldErrors = {};
    @track objectError = '';

    async handleAdvance() {
        this.fieldErrors = {};
        this.objectError = '';
        const fields = {
            [OPP_ID.fieldApiName]: this.recordId,
            [OPP_STAGE.fieldApiName]: this.stage,
            [OPP_REASON.fieldApiName]: this.lossReason,
            [OPP_NEXT_STEP.fieldApiName]: this.nextStep
        };
        try {
            await updateRecord({ fields });
            this.dispatchEvent(new CustomEvent('advance'));
        } catch (err) {
            const output = err?.body?.output ?? {};
            this.fieldErrors = output.fieldErrors ?? {};
            this.objectError = (output.errors ?? []).map(e => e.message).join('; ');
        }
    }
}
```

**Why it works:** `OPP_ID.fieldApiName` resolves to the string `'Id'`; `updateRecord` requires `Id` *inside* `fields`. The catch block reads UI API's structured error envelope and binds field errors back to the inputs (the template can render `{fieldErrors.StageName?.[0]?.message}` next to the relevant control). `await updateRecord` returns the updated record; the wizard advances on success.

---

## Example 3: cross-component refresh after Apex DML

**Context:** A custom record page has two LWCs side by side. The left LWC writes via Apex (`without sharing` to honor a service-account audit pattern). The right LWC wires `getRecord` to display Account fields.

**Problem:** After the Apex DML resolves, the right LWC still shows pre-write data because LDS auto-refresh only fires for `getRecord` wires inside the *same* component instance that issued an LDS write.

**Solution:**

```javascript
// LeftLwc — issues the Apex DML
import { LightningElement, api } from 'lwc';
import { notifyRecordUpdateAvailable } from 'lightning/uiRecordApi';
import enrichAccount from '@salesforce/apex/AccountEnrichmentService.enrich';

export default class LeftLwc extends LightningElement {
    @api recordId;

    async handleEnrich() {
        await enrichAccount({ accountId: this.recordId });
        await notifyRecordUpdateAvailable([{ recordId: this.recordId }]);
    }
}
```

**Why it works:** `notifyRecordUpdateAvailable` tells LDS that `recordId` changed outside its visibility. Any `@wire(getRecord)` for that recordId across the page re-provisions on its next cycle. Without it, LDS continues to serve the cached pre-write copy until cache expiry or a navigation event.

---

## Anti-Pattern: looping `updateRecord` for bulk updates

**What practitioners do:** loop over a 50-row table, awaiting `updateRecord` per row. Each call is a UI API round-trip; the user waits ~12 seconds.

**What goes wrong:** UX stalls, governor-style behaviors trip server-side (the user may exceed concurrent UI API calls), and partial-failure handling becomes ambiguous (rows 1-30 succeeded, 31 failed, what now?). LDS has no array form because it is designed around single-record user gestures.

**Correct approach:** route the bulk operation through Apex DML with `Database.update(records, allOrNone=false)` returning a `Database.SaveResult[]`, called from a single `@AuraEnabled` method. Render per-row results from the `SaveResult[]` and call `notifyRecordUpdateAvailable` for any wired reads of the affected records. Reserve LDS writes for the single-record path.
