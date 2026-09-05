# Examples - LWC Data Table

## Example 1: Inline Edit With Stable Save Handling

**Context:** A sales-ops team needs quick editing of Opportunity stage and amount from a compact table on a record page.

**Problem:** The first version updates local row data immediately and clears the edit state before the server confirms the save.

**Solution:**

Keep edits in `draftValues`, save explicitly, then clear drafts only after persistence succeeds.

```javascript
columns = [
    { label: 'Opportunity', fieldName: 'Name' },
    { label: 'Stage', fieldName: 'StageName', editable: true },
    { label: 'Amount', fieldName: 'Amount', type: 'currency', editable: true }
];

async handleSave(event) {
    const updates = event.detail.draftValues.map((draft) => ({
        fields: { ...draft }
    }));

    await Promise.all(updates.map((recordInput) => updateRecord(recordInput)));
    this.draftValues = [];
    await refreshApex(this.wiredOpportunities);
}
```

**Why it works:** The table keeps view state and persistence state separate, so the user sees a predictable edit lifecycle.

**The nuance the code above hides:** clearing `draftValues` is also what removes the Cancel/Save footer (`data-table-inline-edit` L5712), so the ordering above — clear *after* the awaits — is a policy, not a rule. The guide's own UI API recipe clears immediately after copying the drafts into record objects, before the `updateRecord` promises resolve (L5683–L5684); its Apex recipe clears after the update and refresh (L5739). Choose by asking whether a failed save may discard the user's typing. Note also that `updateRecord()` "expects a single record only" (L5714), which is why the map-then-`Promise.all` shape appears here at all — for more than a handful of rows the guide recommends one Apex transaction instead (L5717), as `references/code-examples.md` §1 does.

---

## Example 2: Infinite Loading With A Clear Stop Condition

**Context:** A service dashboard needs to browse recent cases without loading every historical record at first render.

**Problem:** The original component keeps appending rows forever and never disables loading once the server is exhausted.

**Solution:**

Use a server-side page size and turn off infinite loading when the returned batch is smaller than the requested size.

```javascript
// PAGE_SIZE = 50 — "load a maximum of 50 rows at a time" (data-table-performance L6318).
async handleLoadMore() {
    if (this.loadingMore || !this.enableInfiniteLoading) {
        return;
    }
    this.loadingMore = true;
    try {
        const nextRows = await getRecentCases({
            offsetSize: this.rows.length,
            pageSize: PAGE_SIZE
        });
        // New array reference: an in-place push is not observed
        // (reactivity-fields L2288).
        this.rows = [...this.rows, ...nextRows];
        if (nextRows.length < PAGE_SIZE) {
            this.enableInfiniteLoading = false; // the stop condition
        }
    } finally {
        this.loadingMore = false;
    }
}
```

**Why it works:** The browser only holds the rows users are likely to inspect, and the table knows when to stop asking for more. `enable-infinite-loading` and `onloadmore` are the two attributes the developer guide names (`data-table-performance` L6313); the component drives its own `loadingMore` flag rather than writing `event.target.isLoading`, because that attribute is documented only in the Component Library. UNVERIFIED (2026-09-05): no developer-guide page in the extracted text names an `isLoading` attribute or a settable `enableInfiniteLoading` on the element instance — the stop condition here is a `lwc:if`-guarded attribute on the wrapper's own state, which is grounded reactivity rather than an undocumented setter.

---

## Example 3: The Sort Handler That Works Everywhere Except The Custom Column

**Context:** A partner-scorecard table has four stock columns and one custom `healthBadge` column. Sorting works on all five in the developer's manual test, because they always clicked the stock headers.

**Problem:** In production, clicking the Health header reorders nothing. There is no console error. `event.detail.fieldName` returns `undefined` for a custom data type, so the comparator sorts every row by `undefined` — which is a stable no-op.

**Solution:**

Carry the sortable key on the column definition itself and prefer it over the event, so custom and standard columns take the same path.

```javascript
const COLUMNS = [
    { label: 'Partner', fieldName: 'Name', sortable: true },
    { label: 'Tier', fieldName: 'Tier__c', sortable: true },
    {
        label: 'Health',
        fieldName: 'healthLabel',
        type: 'healthBadge',      // custom type: event.detail.fieldName will be undefined
        sortKey: 'healthScore',   // our own key, read back in the handler below
        sortable: true,
        standardCellLayout: true
    }
];

handleSort(event) {
    // data-table-custom-types L5855-L5856: fieldName is only reliable for
    // standard types. Fall back to the column's own sortKey.
    const column = this.columns.find(
        (c) => c.fieldName === event.detail.fieldName || c.label === event.detail.label
    );
    const key = (column && (column.sortKey || column.fieldName)) || event.detail.fieldName;
    if (!key) {
        // Fail loudly rather than silently sorting by undefined.
        throw new Error('Sort fired with no resolvable field name');
    }
    const dir = event.detail.sortDirection === 'desc' ? -1 : 1;
    this.rows = [...this.rows].sort(
        (a, b) => (a[key] > b[key] ? 1 : a[key] < b[key] ? -1 : 0) * dir
    );
    this.sortedBy = event.detail.fieldName;
    this.sortDirection = event.detail.sortDirection;
}
```

**Why it works:** The custom column's sortable value (`healthScore`, a number) is separated from its display value (`healthLabel`, a badge string), and the handler never depends on the event carrying a field name it is documented not to carry. UNVERIFIED (2026-09-05): `event.detail.sortDirection` and `event.detail.label` are Component-Library details; the developer guide names only `event.detail.fieldName`. The `throw` exists so that if either changes, the table fails visibly instead of quietly refusing to sort.

---

## Anti-Pattern: Using Array Index As Row Identity

**What practitioners do:** They use a generated row index as `key-field` because the source data does not expose a stable ID.

**What goes wrong:** Sorting, filtering, refresh, and pagination all reshuffle row identity. Selection and draft state jump to the wrong records.

**Correct approach:** Choose a real unique identifier, usually `Id` or another stable key from the source model, and make it part of the table contract.

---

## Anti-Pattern: Assigning The Result Of An In-Place Sort

**What practitioners do:** They write `this.rows = this.rows.sort(comparator)`, reasoning that assigning back to the field is what LWC needs to see.

**What goes wrong:** `Array.prototype.sort` sorts in place and returns *the same array reference*. LWC "tracks field value changes in a shallow fashion. Changes are detected when a new value is assigned to the field by comparing the value identity using `===`" (`reactivity-fields` L2287), so the assignment is a no-op and the table keeps rendering the old order. The data really did change; only the reference did not. The same trap catches `this.rows.push(...)` after `onloadmore` and `this.rows[i].Status = 'Done'` after a save.

**Correct approach:** Copy first — `this.rows = [...this.rows].sort(comparator)`, `this.rows = [...this.rows, ...nextPage]`, `this.rows = this.rows.map((r) => (r.Id === id ? { ...r, Status: 'Done' } : r))`. Assert it in the Jest test: `expect(after).not.toBe(before)`.
