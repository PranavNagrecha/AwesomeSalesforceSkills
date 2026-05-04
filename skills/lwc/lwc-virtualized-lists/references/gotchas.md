# Gotchas — LWC Virtualized Lists

Non-obvious Lightning / shadow-DOM behaviors that bite custom virtual
lists.

---

## Gotcha 1: No first-party LWC virtual-list base component

**What happens.** Teams search for `<lightning-virtual-list>` /
`<lwc-windowed>` / similar and find nothing. Salesforce's official
performance guidance acknowledges the gap with a "don't support
creation of infinite list items" caveat — the platform doesn't ship
the base component.

**When it occurs.** Any team that needs to render more than the
~1,000-row datatable threshold and assumes a first-party answer
exists.

**How to avoid.** Hand-build using the patterns in this skill. Or
push the requirement back: usually `lightning-datatable` +
`enable-infinite-loading` is enough; the times when it's not are
rarer than they feel.

---

## Gotcha 2: IntersectionObserver `root: null` doesn't fire inside Lightning shadow DOM

**What happens.** A virtual-list LWC creates `new IntersectionObserver(cb)`
with no `root` (default null = the viewport). Inside the Lightning
record page, the observer never fires — or fires once for the initial
intersection and then goes quiet.

**When it occurs.** Standard browser-tutorial code copied into LWC.
Any virtualization library that assumes document-scoped observers.

**How to avoid.** Pass an explicit `root` that's the scrollable
ancestor IN THE SAME shadow root as the sentinel:

```js
const root = this.template.querySelector('.virtual-list');
new IntersectionObserver(cb, { root, rootMargin: '200px', threshold: 0 });
```

The root must be queried via `this.template.querySelector` (in-shadow),
not `document.querySelector` (which can't see into the shadow root).

---

## Gotcha 3: `lightning-datatable` degrades past 1,000 rows × 5 columns

**What happens.** A 5,000-row `lightning-datatable` has visibly
sluggish scroll, sort, and edit. The team blames the user's machine
or "the platform".

**When it occurs.** Above the documented soft ceiling.

**How to avoid.** Either accept the perf at that volume, or move to a
custom virtual list. Salesforce's published threshold is 1,000 rows
× 5 columns. Above that, consider:
- Reducing column count (the docs explicitly say <20 columns for
  >250-row tables)
- Lazy loading via `enable-infinite-loading` (start with 50 rows,
  load more on scroll)
- Custom virtual list (this skill)

(Source: [Improve Datatable Performance](https://developer.salesforce.com/docs/platform/lwc/guide/data-table-performance.html))

---

## Gotcha 4: For tables > 250 rows, keep columns < 20

**What happens.** A 500-row × 25-column datatable hits a different
perf cliff than the 1000×5 threshold — wide tables suffer because
each row's render cost is multiplied by column count.

**When it occurs.** Wide-table use cases (financial detail, audit
log).

**How to avoid.** Per Salesforce guidance: above 250 rows, < 20
columns. If you genuinely need both, virtualize horizontally too —
render only visible columns. That's a custom build; lightning-datatable
doesn't column-virtualize.

---

## Gotcha 5: Inline editing on multiple columns is itself a perf hit

**What happens.** `lightning-datatable` configured with inline-edit on
6+ columns — every row pays the inline-edit overhead even when the
cell isn't being edited. Scroll perf drops noticeably.

**When it occurs.** "Make every column editable for the data entry
team" requirements.

**How to avoid.** Per Salesforce guidance: reserve inline edit for
critical fields only. For data-entry-heavy use cases, consider a
record-page edit form rather than inline-edit-on-everything.

---

## Gotcha 6: Observer wired in `connectedCallback` against an unrendered sentinel silently fails

**What happens.** `connectedCallback` runs before the first render.
`this.template.querySelector('[data-sentinel]')` returns null.
`observer.observe(null)` silently no-ops. The observer never registers
the sentinel; intersection events never fire.

**When it occurs.** Tutorial code that puts all setup in
`connectedCallback`.

**How to avoid.** Wire the observer in `renderedCallback`, guarded so
you only wire it once:

```js
renderedCallback() {
    if (this._observer || !this.hasMore) return;
    const sentinel = this.template.querySelector('[data-sentinel]');
    if (!sentinel) return;
    this._observer = new IntersectionObserver(...);
    this._observer.observe(sentinel);
}
```

---

## Gotcha 7: OFFSET-based pagination re-evaluates the predicate every page

**What happens.** Apex `[SELECT Name FROM Contact WHERE ... LIMIT 50
OFFSET :n]` re-runs the WHERE evaluation for the first n rows every
time. At page 200 (n=10,000) it's evaluating the predicate over 10,050
rows to return the last 50.

**When it occurs.** Long virtual lists with frequent re-fetches.

**How to avoid.** Cursor-style pagination using `LastModifiedDate +
Id`:

```apex
[SELECT Name FROM Contact
 WHERE LastModifiedDate > :cursor.timestamp
    OR (LastModifiedDate = :cursor.timestamp AND Id > :cursor.id)
 ORDER BY LastModifiedDate, Id LIMIT 50]
```

Or use the GraphQL UI API which has cursor pagination natively.

---

## Gotcha 8: Stable keys are non-optional

**What happens.** `<template for:each={visible}>` with `key={item.someComputed}`
where `someComputed` changes between page loads. LWC sees the key
change and tears down the entire row component on every re-render —
so the per-row component's `connectedCallback`, wire adapters, and
DOM mount cost run on every scroll.

**When it occurs.** Computed keys (e.g. `key={item.position}` where
position is the index in the current slice).

**How to avoid.** `key={item.id}` where `id` is a value that doesn't
change across re-renders. The Salesforce record Id is the canonical
choice; for non-record data, generate a stable UUID at fetch time.

---

## Gotcha 9: Forgetting `disconnectedCallback` causes observer leaks

**What happens.** Component unmounts (user navigates away from the
record page) but the IntersectionObserver isn't disconnected.
Multiple navigations later, the page accumulates orphaned observers
referencing detached DOM nodes — memory leak, eventual perf
degradation that resets only on a hard refresh.

**When it occurs.** Tutorial code that doesn't show the cleanup
half.

**How to avoid.** Always pair observer creation with disconnect:

```js
disconnectedCallback() {
    this._observer?.disconnect();
}
```
