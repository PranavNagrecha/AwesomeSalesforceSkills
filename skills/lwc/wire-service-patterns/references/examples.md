# Examples — Wire Service Patterns

Short walk-throughs. The full deployable bundle — controller, component, `js-meta.xml`,
`package.xml`, Jest suite, deploy order — is in `references/code-examples.md`.

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

## Example 3: The Same Save, When A UI API Wire Is Also On The Page

**Context:** The component above also carries a `getRecord` wire on the parent Account, and a `lightning-record-form` sits beside it on the same record page.

**Problem:** `refreshApex()` refreshes the Apex wire and nothing else. The `getRecord` wire and the record form keep showing pre-save values, and adding `refreshApex(this.wiredAccount)` does not fix it — using `refreshApex` on a non-Apex wire adapter is deprecated.

**Solution:** One refresh call per cache.

```js
import { refreshApex } from '@salesforce/apex';
import { notifyRecordUpdateAvailable } from 'lightning/uiRecordApi';

async handleCloseWon() {
    await markOpportunityWon({ recordId: this.opportunityId });
    await Promise.all([
        // Apex cache: re-runs with the config bound to the @wire.
        refreshApex(this.wiredOpportunities),
        // LDS cache: re-emits to every wire on this record, in every component.
        notifyRecordUpdateAvailable([{ recordId: this.accountId }])
    ]);
}
```

**Why it works:** Apex data is unmanaged and LDS data is managed; they are two caches with two refresh functions. `notifyRecordUpdateAvailable()` returns a Promise that resolves only after LDS has pushed updated values to every affected wire, so awaiting it is what makes the sibling record form correct too.

---

## Example 4: Wiring One Adapter Into Another

**Context:** A combobox must show the Rating picklist values for the Account record type the running user actually gets.

**Problem:** `getPicklistValues` requires both `recordTypeId` and `fieldApiName`, and the record type Id is not known at design time.

**Solution:** Make the intermediate value reactive.

```js
import { getObjectInfo, getPicklistValues } from 'lightning/uiObjectInfoApi';
import ACCOUNT_OBJECT from '@salesforce/schema/Account';
import RATING_FIELD from '@salesforce/schema/Account.Rating';

export default class RatingPicker extends LightningElement {
    defaultRecordTypeId;

    @wire(getObjectInfo, { objectApiName: ACCOUNT_OBJECT })
    wiredInfo({ data, error }) {
        if (data) {
            this.defaultRecordTypeId = data.defaultRecordTypeId;
        } else if (error) {
            this.infoError = error;
        }
    }

    // Silent until defaultRecordTypeId is set. That is the gate, not a bug.
    @wire(getPicklistValues, {
        recordTypeId: '$defaultRecordTypeId',
        fieldApiName: RATING_FIELD
    })
    ratings;
}
```

**Why it works:** The second wire's configuration is incomplete until the first emits, so it simply does not evaluate. Save `value` (the untranslated API name) back to Salesforce and render `label`, which is translated into the running user's language when Translation Workbench provides one.

---

## Anti-Pattern: Mutating Wired Data In Place

**What practitioners do:** They sort or edit `this.account.data` directly after a wire emits.

**What goes wrong:** The provisioned object is behind a read-only proxy, so the assignment throws `Invalid mutation … is read-only` in the browser console — and because it throws at runtime rather than at compile time, it can ship.

**Correct approach:** Copy at the wire handler, then transform the copy.

```js
@wire(getOpenCases, { accountId: '$recordId' })
wiredCases(result) {
    this.wiredCasesResult = result;          // kept whole, for refreshApex()
    const { data, error } = result;
    if (data) {
        this.rows = data
            .map((row) => ({ ...row, isUrgent: row.Priority === 'High' }))
            .sort((a, b) => a.CaseNumber.localeCompare(b.CaseNumber));
        this.error = undefined;
    } else if (error) {
        this.error = error;
        this.rows = [];
    }
}
```

Note both halves: `map` produces new objects so the spread is safe to annotate, and `sort` runs on the array `map` returned — not on `data`, which would mutate the provisioned array in place.
