# LLM Anti-Patterns — LWC Virtualized Lists

Mistakes AI coding assistants commonly make when generating LWC
virtualization code. The consuming agent should self-check against this
list before finalizing output.

---

## Anti-Pattern 1: IntersectionObserver with default `root: null`

**What the LLM generates.**

```js
this._observer = new IntersectionObserver(this.onIntersect.bind(this));
```

**Why it happens.** Browser-tutorial code uses `root: null` (the
viewport) by default. The LLM copies the pattern without surfacing
that inside Lightning's shadow DOM, the default doesn't fire reliably.

**Correct pattern.** Pass an explicit in-shadow-root scrollable
ancestor:

```js
const root = this.template.querySelector('.virtual-list');
this._observer = new IntersectionObserver(this.onIntersect.bind(this), {
    root,
    rootMargin: '200px',
    threshold: 0,
});
```

**Detection hint.** Any `new IntersectionObserver(cb)` call in an LWC
without a second argument (the options object containing `root`) is
suspect.

---

## Anti-Pattern 2: Wiring the observer in `connectedCallback`

**What the LLM generates.**

```js
connectedCallback() {
    const sentinel = this.template.querySelector('[data-sentinel]');
    this._observer = new IntersectionObserver(...);
    this._observer.observe(sentinel);
}
```

**Why it happens.** "Initialize stuff in connectedCallback" is the
React-style mental model. LWC's `connectedCallback` runs before the
first render, so the sentinel is null.

**Correct pattern.** `renderedCallback`, idempotent:

```js
renderedCallback() {
    if (this._observer || !this.hasMore) return;
    const sentinel = this.template.querySelector('[data-sentinel]');
    if (!sentinel) return;
    /* … */
}
```

**Detection hint.** Any `template.querySelector` followed by
`observe(...)` inside `connectedCallback` is wrong.

---

## Anti-Pattern 3: Reaching for an off-the-shelf virtualization library

**What the LLM generates.** "Install `react-virtualized` / `vanilla-virtual-list`
/ `tiny-virtual-list` and wrap it in an LWC."

**Why it happens.** Most JS-ecosystem virtualization advice points at
these libraries. The LLM doesn't surface that they assume document-scoped
DOM and IntersectionObserver, which doesn't work inside shadow DOM.

**Correct pattern.** Either find a library that explicitly supports
shadow DOM and accepts a custom `root`, or hand-build using the patterns
in SKILL.md. Salesforce's official guidance acknowledges the gap.

**Detection hint.** Any LWC virtualization recipe importing a
non-Salesforce npm package is suspect; verify shadow-DOM support
explicitly.

---

## Anti-Pattern 4: Skipping `lightning-datatable` and going custom immediately

**What the LLM generates.** "To handle large lists in LWC, build a
custom virtual list with IntersectionObserver…"

**Why it happens.** The LLM matches "large list" → "virtualization"
without checking whether the platform-native option fits.

**Correct pattern.** Try `lightning-datatable` with
`enable-infinite-loading` first. Above 10K rows OR with non-tabular
row layout, then go custom.

**Detection hint.** Any custom-virtualization recipe that doesn't
mention `lightning-datatable` is missing the first-step option.

---

## Anti-Pattern 5: Computed `key` that changes across re-renders

**What the LLM generates.**

```html
<template for:each={visible} for:item="item" for:index="i">
    <li key={i}>...</li>  <!-- index changes when window slides -->
</template>
```

**Why it happens.** "Every for-each needs a key, the index is a
unique number, problem solved." But when the window slides and item
positions shift, the index for a given item changes — LWC sees a key
change and tears down + rebuilds the row component.

**Correct pattern.**

```html
<li key={item.id}>...</li>
```

`item.id` (or any field that's stable across position) is the right
choice. Never the for-each index in a virtual list.

**Detection hint.** `key={i}` where `i` comes from `for:index` is
almost always wrong in a virtualized context.

---

## Anti-Pattern 6: Forgetting `disconnectedCallback` cleanup

**What the LLM generates.** Observer creation in `renderedCallback`
with no matching disconnect.

**Why it happens.** Tutorial code optimizes for "make it work"; the
cleanup half is often elided.

**Correct pattern.**

```js
disconnectedCallback() {
    this._observer?.disconnect();
}
```

**Detection hint.** Any virtual list LWC with `_observer` /
`new IntersectionObserver(...)` and no `disconnectedCallback` is
leaking.

---

## Anti-Pattern 7: OFFSET pagination on long lists

**What the LLM generates.**

```apex
return [SELECT Name FROM Contact WHERE OrgId__c = :orgId LIMIT 50 OFFSET :offset];
```

**Why it happens.** OFFSET is the simplest paging primitive across SQL
dialects. Tutorial-grade.

**Correct pattern (for long lists).** Cursor pagination:

```apex
return [SELECT Name FROM Contact
        WHERE OrgId__c = :orgId
          AND (LastModifiedDate > :cursor.timestamp
               OR (LastModifiedDate = :cursor.timestamp AND Id > :cursor.id))
        ORDER BY LastModifiedDate, Id LIMIT 50];
```

Or use the GraphQL UI API for native cursor support.

**Detection hint.** Any pagination contract using OFFSET against a
list expected to grow past a few hundred entries is a perf bug
waiting to happen.

---

## Anti-Pattern 8: Inline-edit on every column

**What the LLM generates.**

```js
columns = [
    { label: 'Name',     fieldName: 'Name',     editable: true },
    { label: 'Phone',    fieldName: 'Phone',    editable: true },
    { label: 'Email',    fieldName: 'Email',    editable: true },
    { label: 'Title',    fieldName: 'Title',    editable: true },
    { label: 'Owner',    fieldName: 'Owner',    editable: true },
    /* … 10 more */
];
```

**Why it happens.** "Make it editable" is a flat product requirement;
the LLM applies `editable: true` uniformly without surfacing the perf
cost.

**Correct pattern.** Per Salesforce guidance: reserve inline editing
for critical fields. For multi-field edit, push the user into a
record-page edit form rather than inline-editing every cell.

**Detection hint.** Any datatable with `editable: true` on more than
2-3 columns deserves a perf review.
