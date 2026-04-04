# LWC Imperative Apex — Work Template

Use this template when implementing or reviewing an imperative Apex call in a Lightning Web Component.

## Scope

**Skill:** `lwc-imperative-apex`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Answer these before writing any code:

- **Apex class and method name:** (e.g., `ContactController.getContacts`)
- **Is the method read-only or does it perform DML?**
  - Read-only → use `@AuraEnabled(cacheable=true)`
  - DML → use `@AuraEnabled` (no cacheable)
- **When should the call fire?** (on mount / on button click / on input change)
- **Does the component need to show a loading state?** (almost always yes)
- **Does the component need to refresh data after a write?** (re-call the read method — NOT `refreshApex`)
- **Are multiple independent calls needed?** (use `Promise.all`)

## Apex Method Checklist

Before wiring up the LWC, confirm the Apex method:

- [ ] Is `static`
- [ ] Is annotated `@AuraEnabled` (add `cacheable=true` only for read-only methods)
- [ ] Throws `AuraHandledException` for user-facing errors
- [ ] Uses `with sharing` on the class declaration
- [ ] Enforces CRUD/FLS where needed (use `Security.stripInaccessible` or Schema describe)

## Standard Error Extraction Utility

Copy this into a shared utility file (`lwcUtils.js`) or inline it in the component:

```js
/**
 * Extract a readable error message from an LWC Apex error object.
 * Handles both AuraHandledException (body.message string) and
 * unhandled exceptions (body array of {message} objects).
 */
export function getErrorMessage(error) {
    if (Array.isArray(error.body)) {
        return error.body.map(e => e.message).join(', ');
    }
    if (typeof error.body?.message === 'string') {
        return error.body.message;
    }
    return error.message ?? 'Unknown error';
}
```

## Pattern A — Single Async Call on Mount (Read)

```js
import { LightningElement, api } from 'lwc';
import getRecords from '@salesforce/apex/MyController.getRecords';
import { getErrorMessage } from 'c/lwcUtils';

export default class MyComponent extends LightningElement {
    @api recordId;
    data;
    error;
    isLoading = false;

    async connectedCallback() {
        this.isLoading = true;
        try {
            this.data = await getRecords({ recordId: this.recordId });
            this.error = undefined;
        } catch (error) {
            this.error = getErrorMessage(error);
            this.data = undefined;
        } finally {
            this.isLoading = false;
        }
    }
}
```

HTML template additions:
```html
<template if:true={isLoading}>
    <lightning-spinner alternative-text="Loading..."></lightning-spinner>
</template>
<template if:true={error}>
    <p class="slds-text-color_error">{error}</p>
</template>
<template if:true={data}>
    <!-- render data here -->
</template>
```

## Pattern B — DML Call on Button Click (Write)

```js
import { LightningElement, api } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import saveRecord from '@salesforce/apex/MyController.saveRecord';
import getRecords from '@salesforce/apex/MyController.getRecords';
import { getErrorMessage } from 'c/lwcUtils';

export default class MyForm extends LightningElement {
    @api recordId;
    draftValues = {};
    data;
    error;
    isLoading = false;

    // Set isLoading FIRST — before any await — to prevent double-submission
    async handleSave() {
        this.isLoading = true;
        try {
            await saveRecord({ record: this.draftValues });
            // Re-fetch after write — refreshApex() does NOT work here
            this.data = await getRecords({ recordId: this.recordId });
            this.draftValues = {};
            this.dispatchEvent(new ShowToastEvent({
                title: 'Success', variant: 'success', message: 'Record saved.'
            }));
        } catch (error) {
            this.error = getErrorMessage(error);
            this.dispatchEvent(new ShowToastEvent({
                title: 'Error', variant: 'error', message: this.error
            }));
        } finally {
            this.isLoading = false;
        }
    }
}
```

HTML template additions:
```html
<lightning-button
    label="Save"
    variant="brand"
    onclick={handleSave}
    disabled={isLoading}
></lightning-button>
<template if:true={isLoading}>
    <lightning-spinner alternative-text="Saving..."></lightning-spinner>
</template>
```

## Pattern C — Parallel Reads on Mount

```js
import { LightningElement, api } from 'lwc';
import getSetA from '@salesforce/apex/MyController.getSetA';
import getSetB from '@salesforce/apex/MyController.getSetB';
import { getErrorMessage } from 'c/lwcUtils';

export default class MyDetail extends LightningElement {
    @api recordId;
    setA = [];
    setB = [];
    error;
    isLoading = false;

    async connectedCallback() {
        this.isLoading = true;
        try {
            const [a, b] = await Promise.all([
                getSetA({ recordId: this.recordId }),
                getSetB({ recordId: this.recordId })
            ]);
            this.setA = a;
            this.setB = b;
            this.error = undefined;
        } catch (error) {
            this.error = getErrorMessage(error);
            this.setA = [];
            this.setB = [];
        } finally {
            this.isLoading = false;
        }
    }
}
```

## Checklist Before Marking Complete

Copy from SKILL.md and tick as you go:

- [ ] Apex method is `static`, `@AuraEnabled`, and `cacheable=true` only if read-only
- [ ] Apex class uses `with sharing` and enforces CRUD/FLS
- [ ] `isLoading` is set synchronously before any `await`
- [ ] `isLoading` is reset in a `finally` block
- [ ] Error handling uses `getErrorMessage` (not raw `error.message`)
- [ ] Data refresh after write re-calls the read method imperatively
- [ ] Parallel independent reads use `Promise.all`
- [ ] Jest tests mock Apex imports at the module level (not as wire adapters)

## Notes

Record any deviations from the standard pattern and why (for example: non-standard error handling, skip loading state because the call is fire-and-forget, etc.).
