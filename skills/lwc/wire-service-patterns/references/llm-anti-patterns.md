# LLM Anti-Patterns — Wire Service Patterns

Common mistakes AI coding assistants make when generating or advising on LWC wire service usage.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Passing a literal value instead of a reactive '$' parameter to @wire

**What the LLM generates:**

```javascript
@wire(getRecord, { recordId: this.recordId, fields: FIELDS })
record;
```

**Why it happens:** LLMs use `this.recordId` because that is standard JavaScript property access. The wire service requires the `'$propertyName'` string syntax to establish reactivity.

**Correct pattern:**

```javascript
@wire(getRecord, { recordId: '$recordId', fields: FIELDS })
record;
```

The `$` prefix tells the wire service to re-provision when `this.recordId` changes.

**Detection hint:** `@wire` parameters using `this.` instead of `'$'` prefix strings.

---

## Anti-Pattern 2: Calling refreshApex with the data property instead of the wired result

**What the LLM generates:**

```javascript
@wire(getAccounts)
accounts;

async handleRefresh() {
    await refreshApex(this.accounts.data);
    // Does nothing — refreshApex needs the wired property, not .data
}
```

**Why it happens:** LLMs access `.data` because that is where the useful payload is. But `refreshApex` needs the entire provisioned object (which includes internal wire metadata) to invalidate the cache.

**Correct pattern:**

```javascript
@wire(getAccounts)
wiredAccounts;

async handleRefresh() {
    await refreshApex(this.wiredAccounts);
}
```

If using a wired function, store the full provisioned result:

```javascript
_wiredResult;

@wire(getAccounts)
wiredHandler(result) {
    this._wiredResult = result;
    const { data, error } = result;
    if (data) this.accounts = data;
}

async handleRefresh() {
    await refreshApex(this._wiredResult);
}
```

**Detection hint:** `refreshApex(this.<property>.data)` or `refreshApex(this.<property>.error)`.

---

## Anti-Pattern 3: Using @wire for non-cacheable or DML operations

**What the LLM generates:**

```javascript
@wire(createRecord, { apiName: 'Account', fields: { Name: 'Test' } })
newRecord;
```

**Why it happens:** LLMs apply `@wire` to any imported function. Wire adapters are for read-only, cacheable data provisioning. DML operations like `createRecord` must be called imperatively.

**Correct pattern:**

```javascript
import { createRecord } from 'lightning/uiRecordApi';

async handleCreate() {
    const record = await createRecord({
        apiName: 'Account',
        fields: { Name: 'Test' }
    });
    this.newRecordId = record.id;
}
```

**Detection hint:** `@wire` decorator on `createRecord`, `updateRecord`, `deleteRecord`, or any Apex method without `cacheable=true`.

---

## Anti-Pattern 4: Not handling both data and error from wire results

**What the LLM generates:**

```javascript
@wire(getRecord, { recordId: '$recordId', fields: FIELDS })
wiredRecord({ data }) {
    this.record = data;
    // Error completely ignored
}
```

**Why it happens:** LLMs destructure only `data` for brevity. If the wire call fails (permissions, invalid ID, network), the component silently shows nothing.

**Correct pattern:**

```javascript
@wire(getRecord, { recordId: '$recordId', fields: FIELDS })
wiredRecord({ data, error }) {
    if (data) {
        this.record = data;
        this.error = undefined;
    } else if (error) {
        this.error = error;
        this.record = undefined;
    }
}
```

**Detection hint:** Wired function handler that destructures `{ data }` without `error`, or vice versa.

---

## Anti-Pattern 5: Using getRecord with layoutTypes when specific fields are known

**What the LLM generates:**

```javascript
@wire(getRecord, { recordId: '$recordId', layoutTypes: ['Full'] })
record;
```

**Why it happens:** `layoutTypes: ['Full']` is a convenient shortcut that LLMs use to "get everything." It fetches every field on the page layout, which is wasteful when only a few fields are needed.

**Correct pattern:**

```javascript
import NAME_FIELD from '@salesforce/schema/Account.Name';
import PHONE_FIELD from '@salesforce/schema/Account.Phone';

@wire(getRecord, { recordId: '$recordId', fields: [NAME_FIELD, PHONE_FIELD] })
record;
```

**Detection hint:** `layoutTypes: ['Full']` in a component that accesses fewer than 5 fields from the record.

---

## Anti-Pattern 6: Expecting @wire to fire when the component first loads with undefined parameters

**What the LLM generates:**

```javascript
@api recordId; // May be undefined on initial render

@wire(getRelatedRecords, { parentId: '$recordId' })
relatedRecords;

connectedCallback() {
    // Expects relatedRecords to already have data
    console.log(this.relatedRecords.data); // undefined
}
```

**Why it happens:** LLMs assume wire fires immediately on component creation. In reality, wire does not provision data until all reactive parameters have defined (non-undefined) values. If `recordId` is not yet set, the wire does not fire.

**Correct pattern:**

```javascript
@api recordId;

@wire(getRelatedRecords, { parentId: '$recordId' })
wiredRelated({ data, error }) {
    // This handler fires when recordId gets a defined value
    if (data) {
        this.relatedRecords = data;
    }
}
```

Do not rely on wire data being available in `connectedCallback`. Handle the loading state in the template.

**Detection hint:** Accessing `this.<wiredProperty>.data` in `connectedCallback` or `constructor`.
