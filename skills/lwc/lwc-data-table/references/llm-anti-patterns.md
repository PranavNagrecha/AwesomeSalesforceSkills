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

---

## Anti-Pattern 7: Registering a custom type without `standardCellLayout`

**What the LLM generates:**

```js
import LightningDatatable from 'lightning/datatable';
import statusCell from './statusCell.html';
import statusEdit from './statusEdit.html';

export default class MyDatatable extends LightningDatatable {
    static customTypes = {
        status: {
            template: statusCell,
            editTemplate: statusEdit,
            typeAttributes: ['tone']
        }
    };
}
```

**Why it happens:** The `customTypes` property table has three keys — `template`, `typeAttributes`, `standardCellLayout` — and the third is the only one whose omission is invisible in a screenshot. Its default is `false`, which selects the bare layout, and the bare layout "doesn't support accessibility and keyboard navigation for editable types" (`data-table-custom-types-styling` L6092–L6095). The column looks slightly wrong (no padding, content flush to the border) and its edit affordance is unreachable by keyboard. A model reproducing an example that happened not to be editable carries the omission forward into one that is.

**Correct pattern:**

```js
export default class MyDatatable extends LightningDatatable {
    static customTypes = {
        status: {
            template: statusCell,
            editTemplate: statusEdit,
            standardCellLayout: true, // required for a11y + keyboard nav (L6097, L6151)
            typeAttributes: ['tone']
        }
    };

    // Overriding connectedCallback without super breaks initialization
    // (data-table-custom-types L5857-L5859).
    connectedCallback() {
        super.connectedCallback();
    }
}
```

The input in the edit template also needs `data-inputable="true"`, which "is required for accessibility support in the standard cell layout" (`data-table-custom-types-editable` L6149).

**Detection hint:** a class extending `LightningDatatable` whose `customTypes` entries carry `editTemplate` but no `standardCellLayout: true`, or a `connectedCallback` override with no `super.connectedCallback()` call.

---

## Anti-Pattern 8: Destructuring the wire result, then calling `refreshApex` on the wrong thing

**What the LLM generates:**

```js
@wire(getContacts, { accountId: '$recordId' })
contacts;   // or: wiredContacts({ data, error }) { this.rows = data; }

async handleSave(event) {
    await updateContacts({ drafts: event.detail.draftValues });
    await refreshApex(this.rows);        // or refreshApex(this.contacts.data)
    this.draftValues = [];
}
```

**Why it happens:** `refreshApex` reads like a generic "reload this" helper, so the model passes whatever variable holds the rows. But the argument "must be an object that was previously emitted by an Apex `@wire`" (`apex-result-caching` L7264) — a shaped array is not that object, and neither is `.data` pulled off it. The refresh silently does nothing, so the table shows pre-edit values until the user reloads the page. The second half of the bug is that an Apex write bypasses Lightning Data Service entirely, so even a correct `refreshApex` leaves the rest of the record page stale: "you must notify Lightning Data Service (LDS) using the `notifyRecordUpdateAvailable(recordIds)` function" (`data-table-inline-edit` L5718).

**Correct pattern:**

```js
wiredResult;   // the whole provisioned object, kept deliberately

@wire(getContacts, { accountId: '$recordId' })
wiredContacts(result) {
    this.wiredResult = result;
    const { data, error } = result;   // hardcoded API names (apex-wire-method L7106)
    if (data) { this.rows = this.shape(data); }
    else if (error) { this.error = error; }
}

async handleSave(event) {
    const touched = await updateContacts({ drafts: this.toPayload(event.detail.draftValues) });
    notifyRecordUpdateAvailable(touched.map((id) => ({ recordId: id })));
    await refreshApex(this.wiredResult);
    this.draftValues = [];
}
```

**Detection hint:** `refreshApex(` whose argument is not the parameter of a wired function or a `@wire`-decorated property; or an Apex save path with no `notifyRecordUpdateAvailable` call.

---

## Anti-Pattern 9: Reaching for `@track` to make the table update

**What the LLM generates:**

```js
@track rows = [];

handleSort(event) {
    this.rows.sort((a, b) => (a[event.detail.fieldName] > b[event.detail.fieldName] ? 1 : -1));
}
```

**Why it happens:** The table did not rerender, `@track` is described as "deep reactivity", and adding a decorator is a smaller edit than restructuring the handler. It often appears to work, which is worse: `@track` does make plain-array mutations observable (`reactivity-fields` L2290–L2294), so the model learns the wrong lesson and ships a component that deep-observes every cell of every row on every keystroke. It also fails outright the moment the rows contain anything that is not a plain object or array — "the framework doesn't observe mutations made to complex objects, such as objects inheriting from `Object`, class instances, `Date`, `Set`, or `Map`" (L2295), which includes a `Date` column value.

**Correct pattern:**

```js
rows = [];   // no decorator needed

handleSort(event) {
    const key = event.detail.fieldName;
    const dir = event.detail.sortDirection === 'desc' ? -1 : 1;
    // A new array reference is what LWC compares with === (reactivity-fields L2287-L2288).
    this.rows = [...this.rows].sort(
        (a, b) => (a[key] > b[key] ? 1 : a[key] < b[key] ? -1 : 0) * dir
    );
}
```

**Detection hint:** `@track` on the array bound to the datatable's `data` attribute, or any `.sort(` / `.push(` / `.splice(` call on that array without a surrounding spread.

---

## Anti-Pattern 10: Calling `updateRecord()` once per draft row for a bulk save

**What the LLM generates:**

```js
async handleSave(event) {
    for (const draft of event.detail.draftValues) {
        await updateRecord({ fields: { ...draft } });
    }
    this.draftValues = [];
}
```

**Why it happens:** The guide's UI API example does map draft values into `updateRecord` calls, and a model that has only seen that page generalises it to every row count. Two things go wrong. `updateRecord()` "expects a single record only" (`data-table-inline-edit` L5714), so a 200-row draft batch becomes 200 network round trips — serialised, in the loop above. And each is its own transaction, so a failure at row 137 leaves the org half-saved with no rollback. The guide's own guidance is explicit: "For bulk record updates in a single transaction, we recommend using Apex" (L5717).

**Correct pattern:** one `@AuraEnabled` (not cacheable — "to set `cacheable=true`, a method must only get data, it can't mutate data", `apex-result-caching` L7254) Apex method taking the whole batch and doing one DML, then `notifyRecordUpdateAvailable` plus `refreshApex`. The full shape is in `references/code-examples.md` §1 and §3.

**Detection hint:** `updateRecord(` inside a `for`, `forEach`, `map`, or `Promise.all` over `draftValues` where the row count is not bounded to a handful.
