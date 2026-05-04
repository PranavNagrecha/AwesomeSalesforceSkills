---
name: lwc-virtualized-lists
description: "Hand-built virtual / windowed list rendering in LWC for datasets above the 1,000-row × 5-column threshold where `lightning-datatable` degrades. Covers the four core mechanics — fixed-window state, IntersectionObserver-based scroll sentinels, stable item keys, server-side pagination caps (50 rows/page) — and the shadow-DOM gotchas that make the standard browser virtual-list libraries unreliable inside Lightning. NOT for the built-in `lightning-datatable` with `enable-infinite-loading` (use that first; this skill is the answer when datatable can't keep up), NOT for `lightning-tree-grid`."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "lwc large dataset rendering performance virtualization"
  - "lwc datatable 1000 rows performance degrades"
  - "lwc infinite scroll intersection observer pattern"
  - "lwc windowed list lazy loading datatable alternative"
  - "lwc shadow dom intersection observer not working"
  - "lwc soql limit offset pagination infinite list"
tags:
  - virtualization
  - infinite-scroll
  - intersection-observer
  - performance
  - shadow-dom
  - pagination
inputs:
  - "Estimated row count and column width of the list"
  - "Whether the data is already in memory (client-only filter) or needs paging from the server"
  - "Whether sort / filter / inline-edit are required (each pushes you toward a different architecture)"
  - "Whether the list lives inside a Lightning page (shadow DOM) or a standalone page"
outputs:
  - "Choice between `lightning-datatable` + `enable-infinite-loading` vs hand-built virtual list"
  - "Window size, page size, and sentinel placement for the virtual implementation"
  - "Shadow-DOM-aware IntersectionObserver setup that actually fires"
  - "Server-side pagination contract (LIMIT/OFFSET or GraphQL cursor)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-04
---

# LWC Virtualized Lists

Salesforce's own performance guidance puts the soft ceiling at **1,000 rows
× 5 columns** for `lightning-datatable`. Above that, the experience degrades
— and the platform has no first-party virtual-list base component, so the
team has to hand-build windowing. This skill is the playbook for that
custom build, including the shadow-DOM pitfalls that make off-the-shelf
browser virtualization libraries unreliable inside Lightning.

What this skill is NOT. If `lightning-datatable` with `enable-infinite-loading`
meets the requirement, use that — it's the platform's first-party answer.
This skill is for cases where datatable's column model, edit semantics, or
performance ceiling don't fit. `lightning-tree-grid` for hierarchical data
is also out of scope.

---

## Before Starting

- **Try `lightning-datatable` first.** Add `enable-infinite-loading` and an
  `onloadmore` handler. Most "I need a virtual list" requests resolve here.
- **Profile the actual bottleneck.** Is it row count (DOM nodes), column
  count (cell complexity), or per-row component complexity (custom data
  types, nested templates)? Each has a different fix.
- **Decide where the data lives.** Already-in-memory client list (filter /
  sort happens client-side) vs server-paged list (each window fetches a
  page from Apex / GraphQL). Server-paged adds latency per scroll-window
  shift; in-memory hits the JS heap on large datasets.
- **Confirm the row count is real.** "We might have a million rows" is
  often false in practice; the actual production max is in the
  10K–50K range. The right design at 50K is different from at 1M.

---

## Core Concepts

### The four mechanics of a hand-built virtual list

1. **Window state** — JS state holds only the visible-plus-buffer slice, e.g. rows 0..49 of a 50,000-row dataset. The template renders that slice via `for:each`, NOT the full dataset.
2. **Scroll sentinel + IntersectionObserver** — empty marker `<div>` at the bottom of the rendered slice. When the sentinel intersects the viewport, the observer callback fires; you shift / extend the window.
3. **Stable item keys** — every rendered item needs a `key={item.id}` that doesn't change across window shifts. Stable keys let LWC reuse DOM nodes across re-renders rather than tearing down and rebuilding.
4. **Server pagination contract** — for server-backed data, define how a window-shift translates to a fetch. Usually LIMIT/OFFSET on Apex or cursor-based on GraphQL. **Cap at 50 rows per page** per Salesforce performance guidance.

### Two flavors of virtualization, very different work

| Flavor | What you render | When to use |
|---|---|---|
| **Append-only / infinite scroll** | All loaded rows stay in the DOM; you grow the rendered slice as the user scrolls | Small-ish total (~5,000 rows), simple rows, rarely scroll back up |
| **True windowing (slide the window)** | DOM only ever holds the visible-plus-buffer slice; rows above and below scroll position are removed from the DOM | Large totals (>10,000 rows), or DOM weight is the bottleneck |

Append-only is *much* simpler. True windowing requires absolute positioning
(or a spacer-div trick) to keep the scrollbar's geometry consistent as DOM
nodes come and go. Most LWC virtual lists are append-only with a sensible
upper cap (drop oldest pages when you exceed N pages in memory).

### Shadow DOM and IntersectionObserver

The browser-standard `IntersectionObserver` works inside Lightning's
shadow DOM with two caveats:

- The **`root`** option must be the scrollable ancestor that lives in the
  *same* shadow root as the sentinel. If you pass an element from a
  different shadow tree (or the document), the observer never fires.
- The sentinel element must be **rendered** before you create the observer.
  Calling `new IntersectionObserver(...)` in `connectedCallback` against a
  sentinel that hasn't been queried yet returns silently — wire it up in
  `renderedCallback` after `this.template.querySelector(...)` finds the
  node.

Off-the-shelf virtualization libraries (react-virtualized, vanilla
virtual-list packages) often assume a document-level scroll context.
Inside a Lightning record page they don't reach the right shadow root and
fail silently — which is why the Salesforce team's official guidance
caveat says "don't support creation of infinite list items" and stops
short of a recipe.

---

## Common Patterns

### Pattern A — `lightning-datatable` with `enable-infinite-loading` (try this first)

```js
// list.js
import { LightningElement, wire } from 'lwc';
import getRows from '@salesforce/apex/RowService.getRows';

export default class List extends LightningElement {
    rows = [];
    columns = [/* … */];
    pageSize = 50;
    enableInfiniteLoading = true;

    connectedCallback() {
        this.loadMore();
    }

    async handleLoadMore(event) {
        event.target.isLoading = true;
        await this.loadMore();
        event.target.isLoading = false;
    }

    async loadMore() {
        const more = await getRows({ offset: this.rows.length, limit: this.pageSize });
        this.rows = this.rows.concat(more);
    }
}
```

```html
<lightning-datatable
    key-field="Id"
    data={rows}
    columns={columns}
    enable-infinite-loading={enableInfiniteLoading}
    onloadmore={handleLoadMore}>
</lightning-datatable>
```

This handles 1,000–10,000 rows comfortably. Above that, datatable's
DOM weight starts to bite — that's when you go custom.

### Pattern B — Append-only custom virtual list

**When to use.** Datatable's column model doesn't fit (custom card layout,
non-tabular rows). Up to ~10,000 rows total in the DOM is acceptable.

```html
<template>
    <ul class="virtual-list" lwc:dom="manual">
        <template for:each={visible} for:item="item">
            <li key={item.id}>
                <c-row-card data={item}></c-row-card>
            </li>
        </template>
        <li class="sentinel" data-sentinel="true"></li>
    </ul>
</template>
```

```js
import { LightningElement } from 'lwc';
import getRows from '@salesforce/apex/RowService.getRows';

export default class VirtualList extends LightningElement {
    visible = [];          // rows currently rendered
    pageSize = 50;
    hasMore = true;
    _observer;

    async connectedCallback() {
        await this.loadNextPage();
    }

    renderedCallback() {
        if (this._observer || !this.hasMore) return;
        const sentinel = this.template.querySelector('[data-sentinel="true"]');
        if (!sentinel) return;  // not yet rendered
        // Root must be the scrollable ancestor IN THE SAME SHADOW ROOT.
        const root = this.template.querySelector('.virtual-list');
        this._observer = new IntersectionObserver(this.onIntersect.bind(this), {
            root,
            rootMargin: '200px',
            threshold: 0,
        });
        this._observer.observe(sentinel);
    }

    onIntersect(entries) {
        if (entries.some(e => e.isIntersecting)) {
            this.loadNextPage();
        }
    }

    async loadNextPage() {
        const more = await getRows({ offset: this.visible.length, limit: this.pageSize });
        if (more.length === 0) {
            this.hasMore = false;
            this._observer?.disconnect();
            return;
        }
        this.visible = this.visible.concat(more);
    }

    disconnectedCallback() {
        this._observer?.disconnect();
    }
}
```

Two things this gets right that hand-rolled-from-tutorial code often
misses:
- The IntersectionObserver `root` is the scrollable ancestor inside
  the same shadow root, not `null` (which would mean "the viewport"
  and may not work inside Lightning's shadow tree).
- `renderedCallback` (not `connectedCallback`) is where the observer
  is wired up, after the sentinel is actually queryable.

### Pattern C — True windowing (slide-the-window)

**When to use.** Total dataset > 10,000 rows AND the user can scroll back
up. Append-only would balloon the DOM past acceptable.

The DOM only ever holds rows `[start, start + window)` for a window of,
say, 100. As the user scrolls, you adjust `start` and re-render the slice.
Two complications:

- **Scrollbar geometry.** As DOM rows leave / enter, the document height
  changes; the scrollbar jumps. Fix with two spacer divs above and below
  the rendered slice with heights `start * rowHeight` and `(total - start
  - window) * rowHeight`. The scrollbar now reflects total height.
- **Two sentinels.** One above the slice (intersection → window slides
  up), one below (intersection → window slides down). Both observers
  attach to the same scrollable root.

This pattern is significantly more code. Use only when append-only's
memory ceiling is a real ceiling — most LWC use cases never reach it.

### Pattern D — GraphQL cursor pagination instead of LIMIT/OFFSET

**When to use.** Server data, large total, frequent re-paginations.
LIMIT/OFFSET pages re-evaluate the query at each page boundary; cursor
pagination uses an opaque token to resume from the last record without
re-evaluating the full predicate.

GraphQL UI API supports cursor pagination natively. For Apex-backed
data, implement cursor-style by using `LastModifiedDate + Id` as the
cursor and filtering `WHERE LastModifiedDate > :cursor.timestamp OR
(LastModifiedDate = :cursor.timestamp AND Id > :cursor.id)`.

---

## Decision Guidance

| Situation | Approach | Reason |
|---|---|---|
| Tabular rows, 1,000–10,000 total | **lightning-datatable + enable-infinite-loading** | Platform-native; meets datatable's documented threshold |
| Tabular rows, >10,000 total | **Custom append-only virtual list** | Datatable degrades past the threshold |
| Custom card layout (non-tabular rows) | **Custom append-only virtual list** | Datatable's column model doesn't fit |
| User can scroll back up across many pages | **True windowing** (Pattern C) | Append-only's DOM grows without bound |
| Frequent server re-pagination on the same dataset | **GraphQL cursor pagination** | Avoids OFFSET re-evaluation cost |
| Inline edit on multiple columns | **Stay with datatable, accept the perf hit** | Inline edit on >2-3 columns is itself a major perf hit per Salesforce guidance — virtualization can't compensate |
| Component lives outside a Lightning page (Experience Cloud, standalone aura host) | **Verify shadow-DOM scope before implementing** | IntersectionObserver root must be in the same shadow root as the sentinel |
| Bottleneck is per-row complexity (custom data type with many sub-components) | **Simplify the row component before virtualizing** | DOM count is one input to perf; cell complexity is another |
| Total rows < 1,000 | **Plain `for:each` rendering, no virtualization** | Below the threshold, virtualization adds complexity for no gain |

---

## Recommended Workflow

1. **Try `lightning-datatable` + `enable-infinite-loading` first.** Profile against the actual data volume.
2. **If datatable is the wrong shape, choose append-only vs true windowing.** Append-only unless DOM growth is a real ceiling.
3. **Wire IntersectionObserver in `renderedCallback`,** with `root` set to the in-shadow-root scrollable ancestor.
4. **Use stable `key={item.id}`** on every for-each item.
5. **Cap server pages at 50 rows** per Salesforce performance guidance.
6. **Disconnect the observer in `disconnectedCallback`** to avoid leaks.
7. **Consider cursor pagination** if LIMIT/OFFSET re-evaluation cost is a profile-visible bottleneck.

---

## Review Checklist

- [ ] `lightning-datatable + enable-infinite-loading` was tried before going custom.
- [ ] Row count + column count are profile-measured, not estimated.
- [ ] IntersectionObserver `root` option is the in-shadow-root scrollable element, not `null`.
- [ ] Observer is wired in `renderedCallback`, not `connectedCallback`.
- [ ] Every rendered item has a stable `key={item.id}`.
- [ ] Server pages capped at 50 rows.
- [ ] Observer is disconnected in `disconnectedCallback`.
- [ ] Inline edit, if present, is on ≤3 columns.

---

## Salesforce-Specific Gotchas

1. **No first-party virtual-list base component in LWC.** You hand-build. (See `references/gotchas.md` § 1.)
2. **IntersectionObserver inside shadow DOM needs in-shadow-root `root`.** Default `null` (viewport) often doesn't fire inside Lightning. (See `references/gotchas.md` § 2.)
3. **`lightning-datatable` degrades past 1,000 rows × 5 columns.** Documented Salesforce threshold. (See `references/gotchas.md` § 3.)
4. **For tables > 250 rows, keep < 20 columns.** Per Salesforce guidance. (See `references/gotchas.md` § 4.)
5. **Inline editing on multiple columns is itself a major perf hit.** Reserve for critical fields. (See `references/gotchas.md` § 5.)
6. **Observers wired in `connectedCallback` against an unrendered sentinel silently fail.** Use `renderedCallback`. (See `references/gotchas.md` § 6.)
7. **OFFSET-based pagination re-evaluates the predicate at every page.** GraphQL cursor or `LastModifiedDate + Id` keyset is cheaper for large datasets. (See `references/gotchas.md` § 7.)

---

## Output Artifacts

| Artifact | Description |
|---|---|
| LWC bundle | `.html` template + `.js` controller + `.js-meta.xml` config |
| Apex / GraphQL paginator | Server-side LIMIT/OFFSET or cursor-based fetch contract |
| Performance baseline | Render time + DOM node count + JS heap at p50, p95 row counts |
| Profile evidence | Confirmation that the chosen flavor (datatable / append-only / windowing) actually fits the workload |

---

## Related Skills

- `lwc/lwc-data-table` — when datatable is the right shape (this skill is the escape hatch).
- `lwc/lwc-performance-best-practices` — broader LWC performance patterns (memoization, `@track`, render scoping).
- `apex/apex-soql-pagination` — server-side LIMIT/OFFSET vs cursor patterns referenced here.
- `lwc/lwc-shadow-dom-patterns` — shadow-DOM-aware DOM manipulation generally; IntersectionObserver is one instance.
