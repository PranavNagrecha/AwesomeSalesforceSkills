# LLM Anti-Patterns — LWC Datatable Advanced

Common mistakes AI coding assistants make when building advanced datatables.

---

## Anti-Pattern 1: Sequential `await updateRecord` in a loop

**What the LLM generates.**

```js
for (const draft of event.detail.draftValues) {
    await updateRecord({ fields: { ...draft, Id: draft.Id } });
}
```

**Correct pattern.**

```js
const promises = event.detail.draftValues.map(d =>
    updateRecord({ fields: { ...d, Id: d.Id } })
);
await Promise.all(promises);
```

Sequential awaits make 50 rows take 50× the round-trip time.
`Promise.all` parallelizes; the platform handles concurrency.

**Detection hint.** Any `for (...)` / `for...of` with `await
updateRecord` inside a datatable `onsave` handler.

---

## Anti-Pattern 2: Mutating wired data directly

**What the LLM generates.**

```js
@wire(getAccounts) accounts;
addRow() {
    this.accounts.data.push({ Name: 'New' });
}
```

**Correct pattern.** Copy into a `@track`-backed array:

```js
@track localData = [];
@wire(getAccounts) wired({ data }) {
    if (data) this.localData = [...data];
}
addRow() { this.localData = [...this.localData, { Id: tempId(), Name: 'New' }]; }
```

Wired data is a read-only proxy; mutations are silently dropped
or throw.

**Detection hint.** Any `this.<wireName>.data.push` or `.splice`.

---

## Anti-Pattern 3: Custom cell type with component-scoped CSS

**What the LLM generates.**

```css
/* myComponent.css */
.status-badge { background: red; }
```

```html
<!-- statusBadge.html (custom type template) -->
<span class="status-badge">{...}</span>
```

**Correct pattern.** The custom-type template runs in
`lightning-datatable`'s shadow DOM. Component CSS does not pierce
it. Either ship the CSS in the custom-type module's CSS file, or
use `--slds-c-*` styling hooks.

**Detection hint.** Any custom cell type referencing class names
defined only in the consuming component's CSS file.

---

## Anti-Pattern 4: `enable-infinite-loading` without `isLoading` reset

**What the LLM generates.**

```js
async loadMore(event) {
    const next = await fetch();
    this.data = [...this.data, ...next];
}
```

**Correct pattern.** The platform set
`event.target.isLoading = true` to show the spinner. You must
reset it:

```js
async loadMore(event) {
    event.target.isLoading = true;
    try {
        const next = await fetch();
        this.data = [...this.data, ...next];
    } finally {
        event.target.isLoading = false;
    }
}
```

**Detection hint.** Any `onloadmore` handler that does not set
`event.target.isLoading = false` in a `finally` block.

---

## Anti-Pattern 5: Not deduplicating on infinite scroll

**What the LLM generates.**

```js
this.data = [...this.data, ...next];
```

**Correct pattern.**

```js
const seen = new Set(this.data.map(r => r.Id));
this.data = [...this.data, ...next.filter(r => !seen.has(r.Id))];
```

A re-fetch (refreshApex, hot reload, route change) can pull a
page already in `data`. Without dedup, rows appear twice.

**Detection hint.** Any `onloadmore` that concatenates without
filtering by `key-field`.

---

## Anti-Pattern 6: Clearing `draftValues` before save completes

**What the LLM generates.**

```js
async handleSave(event) {
    this.draftValues = [];  // cleared too early
    await Promise.all(...);
}
```

**Correct pattern.** Clear after success:

```js
async handleSave(event) {
    try {
        await Promise.all(...);
        this.draftValues = [];
    } catch (e) { /* keep drafts so user can retry */ }
}
```

If the save fails, the user has to retype their changes.

**Detection hint.** Any `this.draftValues = []` that appears
*before* the awaited save call.

---

## Anti-Pattern 7: Hard-coding column type strings without using
the type's `typeAttributes`

**What the LLM generates.**

```js
{ label: 'Owner', fieldName: 'OwnerName', type: 'url' }
```

**Correct pattern.**

```js
{ label: 'Owner', fieldName: 'OwnerLink', type: 'url',
  typeAttributes: { label: { fieldName: 'OwnerName' }, target: '_blank' } }
```

The `url` type renders the raw URL by default; without
`typeAttributes.label` the user sees the link href, not the
person's name.

**Detection hint.** Any `type: 'url' | 'date' | 'currency'`
column lacking a `typeAttributes` configuration.
