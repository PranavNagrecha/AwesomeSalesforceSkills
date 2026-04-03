# Examples — Wire Service Patterns

## Example 1: `getRecord` With A Reactive `recordId`

**Context:** A record page component displays Account details and must update automatically when the host record changes.

**Problem:** The first version uses imperative Apex even though the component only reads standard record data.

**Solution:**

```js
import { LightningElement, api, wire } from 'lwc';
import { getRecord } from 'lightning/uiRecordApi';
import NAME_FIELD from '@salesforce/schema/Account.Name';

export default class AccountSummary extends LightningElement {
    @api recordId;

    @wire(getRecord, { recordId: '$recordId', fields: [NAME_FIELD] })
    account;
}
```

**Why it works:** UI API wires bring caching plus sharing, CRUD, and FLS-aware record reads without custom Apex.

---

## Example 2: Imperative Save With Explicit Refresh

**Context:** A component wires a list of Opportunities but also includes a button that updates one of them through Apex.

**Problem:** After the save, the list stays stale because the component assumes the wire will refresh itself automatically.

**Solution:**

```js
import { refreshApex } from '@salesforce/apex';

async handleCloseWon() {
    await markOpportunityWon({ recordId: this.recordId });
    await refreshApex(this.wiredOpportunities);
}
```

**Why it works:** The write is explicit and the wired read is refreshed intentionally rather than left to chance.

---

## Anti-Pattern: Mutating Wired Data In Place

**What practitioners do:** They sort or edit `this.account.data` directly after a wire emits.

**What goes wrong:** The component blurs the line between provisioned input and local state, which leads to stale UI assumptions and hard-to-trace rendering bugs.

**Correct approach:** Clone the wired payload into local state before transforming it for display.
