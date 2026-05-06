# Examples — LWC Datatable Advanced

## Example 1: Inline edit with bulk save

The canonical inline-edit flow: change cells, hit Save, all
changes persist in parallel, drafts clear, errors surface
per-row.

```js
import { LightningElement, wire, track } from 'lwc';
import { updateRecord } from 'lightning/uiRecordApi';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import getAccounts from '@salesforce/apex/AccountList.getAccounts';

const COLUMNS = [
    { label: 'Name',     fieldName: 'Name',     editable: true, sortable: true },
    { label: 'Industry', fieldName: 'Industry', editable: true,
      type: 'text' },
    { label: 'Revenue',  fieldName: 'AnnualRevenue', editable: true,
      type: 'currency' }
];

export default class AccountGrid extends LightningElement {
    columns = COLUMNS;
    @track data = [];
    @track draftValues = [];
    @track errors = { rows: {}, table: {} };

    @wire(getAccounts) wiredAccounts({ data, error }) {
        if (data) this.data = data;
    }

    async handleSave(event) {
        const drafts = event.detail.draftValues;
        const recordInputs = drafts.map(d => ({
            fields: { ...d, Id: d.Id }
        }));
        const promises = recordInputs.map(r => updateRecord(r));
        try {
            await Promise.all(promises);
            this.draftValues = [];
            this.errors = { rows: {}, table: {} };
            this.dispatchEvent(new ShowToastEvent({
                title: 'Saved', variant: 'success'
            }));
            // refresh wire
            return refreshApex(this.wiredAccounts);
        } catch (err) {
            this.errors = this.mapErrors(err, drafts);
        }
    }
}
```

`Promise.all` parallelizes the writes. With 50 rows that's one
~400ms round-trip, not 50 sequential 400ms calls.

---

## Example 2: Server-side sorting

```js
@track sortedBy;
@track sortDirection;

handleSort(event) {
    this.sortedBy = event.detail.fieldName;
    this.sortDirection = event.detail.sortDirection;
    this.refetchPage(0);
}

async refetchPage(offset) {
    this.isLoading = true;
    try {
        const newRows = await getAccountsPaged({
            offset,
            pageSize: 50,
            sortBy: this.sortedBy,
            sortDirection: this.sortDirection
        });
        this.data = offset === 0 ? newRows : [...this.data, ...newRows];
    } finally {
        this.isLoading = false;
    }
}
```

Server-side sort changes the order of *all* rows including ones
not yet loaded — the only correct option for paginated data.
Client-side sort only orders the loaded page; subsequent pages
arrive in the original DB order.

---

## Example 3: Infinite scroll with deduplication

```html
<lightning-datatable
    key-field="Id"
    data={data}
    columns={columns}
    enable-infinite-loading
    onloadmore={loadMore}
    load-more-offset="20">
</lightning-datatable>
```

```js
async loadMore(event) {
    if (this.isLoadingMore || this.allLoaded) return;
    event.target.isLoading = true;
    this.isLoadingMore = true;
    try {
        const next = await getAccountsPaged({
            offset: this.data.length,
            pageSize: 50
        });
        if (next.length === 0) {
            this.allLoaded = true;
            event.target.enableInfiniteLoading = false;
            return;
        }
        const seen = new Set(this.data.map(r => r.Id));
        const fresh = next.filter(r => !seen.has(r.Id));
        this.data = [...this.data, ...fresh];
    } finally {
        event.target.isLoading = false;
        this.isLoadingMore = false;
    }
}
```

The `seen` Set handles the case where a refresh re-fetches a
page already in `data`. Without dedup, refreshing duplicates
every row.

---

## Example 4: Custom cell type (a status badge)

```js
// statusBadgeColumnType.js
import LightningDatatable from 'lightning/datatable';
import statusBadgeTemplate from './statusBadge.html';

export default class StatusBadgeDatatable extends LightningDatatable {
    static customTypes = {
        statusBadge: {
            template: statusBadgeTemplate,
            standardCellLayout: true,
            typeAttributes: ['variant', 'label']
        }
    };
}
```

```html
<!-- statusBadge.html -->
<template>
    <lightning-badge
        label={typeAttributes.label}
        variant={typeAttributes.variant}>
    </lightning-badge>
</template>
```

```js
// in the consuming component
import { LightningElement, track } from 'lwc';
const COLUMNS = [
    { label: 'Status', fieldName: 'status', type: 'statusBadge',
      typeAttributes: { variant: { fieldName: 'badgeVariant' },
                        label:   { fieldName: 'status' } } }
];
```

The custom type runs in the table's shadow DOM. SLDS classes
work; component-scoped CSS does not bleed in. To style, use
`--slds-c-*` design tokens at the consuming component's level.

---

## Example 5: Row-level errors after a partial-save

```js
mapErrors(err, drafts) {
    // Build {rows: {<Id>: {messages, fieldNames, title}}}
    const rows = {};
    if (err.body && err.body.output && err.body.output.errors) {
        for (const e of err.body.output.errors) {
            // err.recordId is set on uiRecordApi rejection
        }
    }
    if (err.recordId) {
        rows[err.recordId] = {
            messages: [err.body.message],
            fieldNames: ['Name'],
            title: 'Save failed'
        };
    }
    return { rows, table: {} };
}
```

The `errors` attribute lights up the affected cells. Without it,
the user sees a generic "save failed" toast and has to guess
which row.
