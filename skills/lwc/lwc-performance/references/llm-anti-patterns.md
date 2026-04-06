# LLM Anti-Patterns — LWC Performance

Common mistakes AI coding assistants make when generating or advising on LWC performance optimization.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using a getter that recomputes on every render instead of caching

**What the LLM generates:**

```javascript
get processedRecords() {
    return this.records.map(r => ({
        ...r,
        fullName: `${r.FirstName} ${r.LastName}`,
        statusClass: r.Status === 'Active' ? 'slds-text-color_success' : ''
    }));
}
```

**Why it happens:** LLMs use getters for derived data because they are idiomatic in LWC. But getters recompute on every render cycle, and expensive transformations on large arrays cause visible lag.

**Correct pattern:**

```javascript
_processedRecords;

get processedRecords() {
    return this._processedRecords;
}

@wire(getRecords)
wiredHandler({ data }) {
    if (data) {
        this._processedRecords = data.map(r => ({
            ...r,
            fullName: `${r.FirstName} ${r.LastName}`,
            statusClass: r.Status === 'Active' ? 'slds-text-color_success' : ''
        }));
    }
}
```

Compute once when the source data changes, not on every access.

**Detection hint:** Getter that calls `.map()`, `.filter()`, or `.reduce()` on an array with more than trivial logic.

---

## Anti-Pattern 2: Using for:each without a stable key

**What the LLM generates:**

```html
<template for:each={items} for:item="item">
    <div key={item.name}>{item.label}</div>
</template>
```

**Why it happens:** LLMs use whatever field looks readable as the key. Non-unique or mutable keys cause the framework to destroy and re-create DOM nodes unnecessarily on every update.

**Correct pattern:**

```html
<template for:each={items} for:item="item">
    <div key={item.Id}>{item.label}</div>
</template>
```

Always use a stable, unique identifier. Salesforce record `Id` is ideal.

**Detection hint:** `key=` bound to a field that is not unique per item (e.g., `name`, `label`, `status`).

---

## Anti-Pattern 3: Rendering large lists without pagination or virtualization

**What the LLM generates:**

```javascript
@wire(getAllContacts)
contacts;
```

```html
<template for:each={contacts.data} for:item="contact">
    <c-contact-card key={contact.Id} record={contact}></c-contact-card>
</template>
```

**Why it happens:** LLMs fetch all data and render all rows. With hundreds or thousands of records, initial render time and memory usage spike.

**Correct pattern:**

```javascript
// Fetch paginated data
@wire(getContacts, { pageSize: 50, offset: '$offset' })
contacts;
```

Or use `lightning-datatable` with `enable-infinite-loading` for progressive loading. Never render unbounded lists.

**Detection hint:** Wire or imperative call with no `LIMIT` or `pageSize` parameter feeding a `for:each` loop.

---

## Anti-Pattern 4: Using the deprecated if:true instead of lwc:if for conditional rendering

**What the LLM generates:**

```html
<template if:true={showSection}>
    <c-heavy-component></c-heavy-component>
</template>
```

**Why it happens:** `if:true` was the only option for years and dominates training data. `lwc:if` is more performant because it supports `lwc:elseif`/`lwc:else` without evaluating multiple independent conditions.

**Correct pattern:**

```html
<template lwc:if={showSection}>
    <c-heavy-component></c-heavy-component>
</template>
```

**Detection hint:** Regex `if:true=` or `if:false=` in template files.

---

## Anti-Pattern 5: Fetching all fields with getRecord when only a few are needed

**What the LLM generates:**

```javascript
import { getRecord } from 'lightning/uiRecordApi';

@wire(getRecord, { recordId: '$recordId', layoutTypes: ['Full'] })
record;
```

**Why it happens:** `layoutTypes: ['Full']` is convenient and appears in documentation examples. It returns every field on the page layout, even when the component only needs two or three fields.

**Correct pattern:**

```javascript
import NAME_FIELD from '@salesforce/schema/Account.Name';
import STATUS_FIELD from '@salesforce/schema/Account.Status__c';

@wire(getRecord, { recordId: '$recordId', fields: [NAME_FIELD, STATUS_FIELD] })
record;
```

**Detection hint:** `layoutTypes: ['Full']` in a component that uses fewer than five fields from the record.

---

## Anti-Pattern 6: Making reactive state changes inside renderedCallback that trigger re-render loops

**What the LLM generates:**

```javascript
renderedCallback() {
    const width = this.template.querySelector('.container')?.offsetWidth;
    this.columnCount = Math.floor(width / 200); // Reactive property change triggers re-render
}
```

**Why it happens:** LLMs use `renderedCallback` for layout calculations but assign the result to a tracked property, which triggers another render, which triggers `renderedCallback` again.

**Correct pattern:**

```javascript
renderedCallback() {
    const width = this.template.querySelector('.container')?.offsetWidth;
    const newCount = Math.floor(width / 200);
    if (newCount !== this._columnCount) {
        this._columnCount = newCount; // Use a non-tracked field
    }
}

get columnCount() {
    return this._columnCount;
}
```

Or guard with a flag to prevent re-entry.

**Detection hint:** Assignment to a `@track`-ed or reactive property inside `renderedCallback` without a change-check guard.
