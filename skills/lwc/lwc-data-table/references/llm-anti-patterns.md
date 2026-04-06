# LLM Anti-Patterns — LWC Data Table

Common mistakes AI coding assistants make when generating or advising on lightning-datatable usage.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Passing array index as key-field instead of a stable unique identifier

**What the LLM generates:**

```html
<lightning-datatable
    data={tableData}
    columns={columns}
    key-field="rowIndex">
</lightning-datatable>
```

**Why it happens:** LLMs sometimes generate synthetic row indices when the data shape is unknown. Array indices are unstable across sort, filter, and pagination operations.

**Correct pattern:**

```html
<lightning-datatable
    data={tableData}
    columns={columns}
    key-field="Id">
</lightning-datatable>
```

If the data lacks an `Id`, use any immutable unique field. Never use a position-based key.

**Detection hint:** `key-field` value of `"index"`, `"rowIndex"`, or any field name that suggests positional identity.

---

## Anti-Pattern 2: Mutating the data array in place instead of creating a new reference

**What the LLM generates:**

```javascript
handleSort(event) {
    this.tableData.sort((a, b) => /* ... */);
    // Component does not rerender — same array reference
}
```

**Why it happens:** LLMs use in-place `Array.sort()` because it is standard JavaScript. LWC reactivity requires a new array reference to trigger a rerender.

**Correct pattern:**

```javascript
handleSort(event) {
    const sorted = [...this.tableData].sort((a, b) => /* ... */);
    this.tableData = sorted;
}
```

**Detection hint:** `this.<dataProperty>.sort(` or `this.<dataProperty>.splice(` without reassignment to a new array.

---

## Anti-Pattern 3: Saving inline edits by iterating draftValues and calling DML per row

**What the LLM generates:**

```javascript
async handleSave(event) {
    for (const draft of event.detail.draftValues) {
        await updateRecord({ fields: draft }); // One DML per row
    }
}
```

**Why it happens:** LLMs model the save operation as one-update-per-row because `updateRecord` takes a single record. This causes N DML calls and potential governor limit hits.

**Correct pattern:**

```javascript
async handleSave(event) {
    const updatePromises = event.detail.draftValues.map(draft =>
        updateRecord({ fields: draft })
    );
    await Promise.all(updatePromises);
    this.draftValues = [];
    return refreshApex(this._wiredResult);
}
```

Or use a single Apex bulkified update method for large edit volumes.

**Detection hint:** `for` or `forEach` loop containing `updateRecord` or imperative Apex inside `handleSave`.

---

## Anti-Pattern 4: Not clearing draftValues after a successful save

**What the LLM generates:**

```javascript
async handleSave(event) {
    await saveDrafts({ records: event.detail.draftValues });
    await refreshApex(this._wiredResult);
    // draftValues not cleared — yellow edit indicators persist
}
```

**Why it happens:** LLMs focus on persisting data and refreshing the source but forget that `draftValues` is a separate binding that must be explicitly reset.

**Correct pattern:**

```javascript
async handleSave(event) {
    await saveDrafts({ records: event.detail.draftValues });
    this.draftValues = [];
    await refreshApex(this._wiredResult);
}
```

**Detection hint:** `handleSave` that calls refresh but does not assign `this.draftValues = []`.

---

## Anti-Pattern 5: Implementing infinite loading without a stop condition

**What the LLM generates:**

```javascript
loadMoreData() {
    this.isLoading = true;
    fetchNextPage({ offset: this.offset }).then(result => {
        this.tableData = [...this.tableData, ...result];
        this.offset += result.length;
        this.isLoading = false;
    });
}
```

**Why it happens:** LLMs implement the incremental load but never check whether all records have been fetched, causing repeated empty fetches or scroll jank.

**Correct pattern:**

```javascript
loadMoreData() {
    if (this._allLoaded) return;
    this.isLoading = true;
    fetchNextPage({ offset: this.offset }).then(result => {
        if (result.length === 0) {
            this._allLoaded = true;
            this.enableInfiniteLoading = false;
        } else {
            this.tableData = [...this.tableData, ...result];
            this.offset += result.length;
        }
        this.isLoading = false;
    });
}
```

**Detection hint:** `loadMoreData` or `onloadmore` handler that never sets `enableInfiniteLoading = false` or checks for empty results.

---

## Anti-Pattern 6: Defining row actions without handling the row context

**What the LLM generates:**

```javascript
handleRowAction(event) {
    const action = event.detail.action;
    if (action.name === 'delete') {
        this.deleteRecord(); // Which record?
    }
}
```

**Why it happens:** LLMs extract the action name but forget to extract `event.detail.row`, so the handler does not know which row was acted on.

**Correct pattern:**

```javascript
handleRowAction(event) {
    const action = event.detail.action;
    const row = event.detail.row;
    if (action.name === 'delete') {
        this.deleteRecord(row.Id);
    }
}
```

**Detection hint:** `handleRowAction` that reads `event.detail.action` but never reads `event.detail.row`.
