# Eval: lwc/wire-service-patterns

- **Skill under test:** `skills/lwc/wire-service-patterns/SKILL.md`
- **Priority:** P0
- **Cases:** 3
- **Last verified:** 2026-04-16
- **Related templates:** `templates/lwc/patterns/wireServicePattern.js`, `templates/lwc/component-skeleton/`
- **Related decision trees:** None directly (LWC data access is a coding choice, not a tree).

## Pass criteria

The AI must recommend wire for reactive reads from LDS where possible,
reach for `@wire(getRecord, ...)` / `getRelatedListRecords` / `getPicklistValues`
before building an imperative Apex path, use field imports (not string
field names), and handle `data` vs `error` states explicitly.

## Case 1 — Reactive Account read on a record page

**Priority:** P0

**User prompt:**

> "On an Account record page I need to show the Name, Industry, and
> Annual Revenue with live updates when the record changes. Build the LWC."

**Expected output MUST include:**

- `@api recordId` and `@wire(getRecord, { recordId: '$recordId', fields: [...] })`.
- Field imports like `import NAME_FIELD from '@salesforce/schema/Account.Name'`.
- `getFieldValue(this.record.data, NAME_FIELD)` for reads.
- Render loading / error / ready states separately; disable content until data is present.
- `isExposed=true` + target `lightning__RecordPage` in `-meta.xml`.
- Jest test that imports `getRecord` from `@salesforce/sfdx-lwc-jest` mocks
  and emits sample data to the wire adapter.

**Expected output MUST NOT include:**

- Imperative Apex just to read these three fields (LDS handles them).
- String field names (`'Name'`) instead of schema imports.
- Re-fetching on every render (the wire adapter is reactive; don't call
  `refreshApex` unless you need to invalidate after a DML).

**Rubric (0–5):**

- **Correctness:** Uses `getRecord` reactively with field imports.
- **Completeness:** Metadata + Jest test included.
- **Bulk safety:** N/A — score 5.
- **Security:** LDS enforces FLS + sharing automatically; noted.
- **Citation of official docs:** Links to `@wire(getRecord)` docs.

**Reference answer (gold):**

```javascript
// accountSummary.js
import { LightningElement, api, wire } from 'lwc';
import { getRecord, getFieldValue } from 'lightning/uiRecordApi';
import NAME from '@salesforce/schema/Account.Name';
import INDUSTRY from '@salesforce/schema/Account.Industry';
import REVENUE from '@salesforce/schema/Account.AnnualRevenue';

const FIELDS = [NAME, INDUSTRY, REVENUE];

export default class AccountSummary extends LightningElement {
    @api recordId;

    @wire(getRecord, { recordId: '$recordId', fields: FIELDS })
    record;

    get name()     { return getFieldValue(this.record.data, NAME); }
    get industry() { return getFieldValue(this.record.data, INDUSTRY); }
    get revenue()  { return getFieldValue(this.record.data, REVENUE); }

    get isReady()  { return !!(this.record && this.record.data); }
    get hasError() { return !!(this.record && this.record.error); }
    get errorMessage() {
        if (!this.hasError) return '';
        const { error } = this.record;
        if (Array.isArray(error.body)) return error.body.map((e) => e.message).join(', ');
        return (error.body && error.body.message) || error.message || 'Unknown error';
    }
}
```

```html
<!-- accountSummary.html -->
<template>
    <template if:true={hasError}>
        <div role="alert" class="slds-text-color_error">{errorMessage}</div>
    </template>
    <template if:true={isReady}>
        <dl class="slds-list_horizontal slds-wrap">
            <dt>Name</dt><dd>{name}</dd>
            <dt>Industry</dt><dd>{industry}</dd>
            <dt>Annual Revenue</dt><dd>{revenue}</dd>
        </dl>
    </template>
</template>
```

```xml
<!-- accountSummary.js-meta.xml -->
<LightningComponentBundle>
    <apiVersion>62.0</apiVersion>
    <isExposed>true</isExposed>
    <targets><target>lightning__RecordPage</target></targets>
</LightningComponentBundle>
```

Jest test emits sample data to the `getRecord` adapter and asserts the rendered text.

## Case 2 — When wire is wrong

**Priority:** P0

**User prompt:**

> "I need a button that recalculates discounts on all line items of the
> current Opportunity. Should I do this with a wire adapter?"

**Expected output MUST include:**

- No — wire is for REACTIVE READS. This is a WRITE (and likely a server-side
  recalculation beyond plain CRUD).
- Use imperative Apex (`@AuraEnabled(cacheable=false)`) called from the
  button's click handler.
- After the imperative call, use `refreshApex(...)` on any related wire
  subscribers to pull fresh data.
- Or, if LDS can represent the updated data, use `notifyRecordUpdateAvailable`
  after the DML so all wires in the app refresh.

**Expected output MUST NOT include:**

- Attempting to write via a wire adapter (wires are read-only).
- `cacheable=true` on a method that mutates data.
- Polling with a wire adapter.

**Rubric (0–5):**

- **Correctness:** Identifies write vs read.
- **Completeness:** Covers both the imperative call AND how to refresh other wires.
- **Bulk safety:** Apex side handles all line items in one DML.
- **Security:** `WITH USER_MODE` on the Apex side.
- **Citation of official docs:** Links to `refreshApex` + `notifyRecordUpdateAvailable`.

**Reference answer (gold):**

"No — wire is read-only and reactive. Recalculating discounts is a write (and probably non-trivial Apex logic beyond basic CRUD).

Pattern:

```javascript
// opportunityDiscountButton.js
import recalcDiscounts from '@salesforce/apex/OpportunityDiscountService.recalcDiscounts';
import { notifyRecordUpdateAvailable } from 'lightning/uiRecordApi';

async handleClick() {
    this.loading = true;
    try {
        await recalcDiscounts({ opportunityId: this.recordId });
        await notifyRecordUpdateAvailable([{ recordId: this.recordId }]);
    } catch (e) {
        this.showError(e);
    } finally {
        this.loading = false;
    }
}
```

`notifyRecordUpdateAvailable` tells LDS that data changed — every `@wire(getRecord, ...)` in the app that's watching this record will re-fetch.

If your component is reading related records via Apex (not LDS), then use `refreshApex(this.wiredResult)` instead where `wiredResult` is the reactive value set by the wire.

Apex side is bulkified:

```apex
@AuraEnabled
public static void recalcDiscounts(Id opportunityId) {
    // Check sharing/FLS, load all line items, compute, update — all bulk.
}
```

## Case 3 — Combining `getRecord` with a related-list wire

**Priority:** P0

**User prompt:**

> "I want to show an Account's Name plus its open Cases (Status != Closed)
> in one component, with both updating live. How?"

**Expected output MUST include:**

- Two wire adapters on the same component: `getRecord` for Account fields,
  `getRelatedListRecords` for Cases.
- `fields: ['Case.Subject', 'Case.Status']`, `where:` with JSON object
  filter for `Status NOT IN ('Closed')`.
- `parentRecordId: '$recordId'`, `relatedListId: 'Cases'`.
- Both wires expose data + error; the component renders both states.
- Jest tests emit sample data for both wires.

**Expected output MUST NOT include:**

- Imperative Apex for the Cases list (LDS has `getRelatedListRecords`).
- Hard-coding the User's own record Id.
- Missing the `sortBy` — large related lists should have a stable sort.

**Rubric (0–5):**

- **Correctness:** Uses both `getRecord` and `getRelatedListRecords`.
- **Completeness:** Filter + sort + error handling.
- **Bulk safety:** `pageSize` bounded so huge related lists don't blow up.
- **Security:** FLS enforced by LDS.
- **Citation of official docs:** Links to `getRelatedListRecords` docs.

**Reference answer (gold):**

```javascript
import { LightningElement, api, wire } from 'lwc';
import { getRecord, getFieldValue } from 'lightning/uiRecordApi';
import { getRelatedListRecords } from 'lightning/uiRelatedListApi';
import ACCOUNT_NAME from '@salesforce/schema/Account.Name';

export default class AccountSnapshot extends LightningElement {
    @api recordId;

    @wire(getRecord, { recordId: '$recordId', fields: [ACCOUNT_NAME] })
    accountRecord;

    @wire(getRelatedListRecords, {
        parentRecordId: '$recordId',
        relatedListId: 'Cases',
        fields: ['Case.Subject', 'Case.Status', 'Case.Priority', 'Case.CaseNumber'],
        where: '{ Status: { ne: "Closed" } }',
        sortBy: ['-CreatedDate'],
        pageSize: 25
    })
    openCases;

    get accountName() { return getFieldValue(this.accountRecord.data, ACCOUNT_NAME); }

    get cases() {
        return this.openCases?.data?.records ?? [];
    }
}
```

Template renders `this.accountName` and iterates `this.cases`. Jest imports `getRecord` and `getRelatedListRecords` from `@salesforce/sfdx-lwc-jest` mocks and emits both via `.emit(sample)` on each adapter.
