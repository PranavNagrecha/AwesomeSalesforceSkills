# Examples — LWC Virtualized Lists

## Example 1 — IntersectionObserver wired in `connectedCallback` doesn't fire

**Context.** Team writes a custom infinite-scroll LWC. It works in the
browser tab they tested in. Inside the Lightning record page it fires
the first observer callback once, then never again — or sometimes
never at all. The team blames "Lightning weirdness".

**Wrong code.**

```js
connectedCallback() {
    const sentinel = this.template.querySelector('[data-sentinel="true"]');
    this._observer = new IntersectionObserver(this.onIntersect.bind(this));
    this._observer.observe(sentinel);  // ← sentinel is null here
}
```

**Why it's wrong.** Two layered bugs:

1. `connectedCallback` runs before the first render. `template.querySelector`
   returns null. `observer.observe(null)` silently no-ops.
2. Default `root: null` means "the viewport". Inside Lightning's shadow
   DOM, "the viewport" isn't always the actual scrollable ancestor — the
   observer never registers an intersection.

**Right code.**

```js
renderedCallback() {
    if (this._observer || !this.hasMore) return;
    const sentinel = this.template.querySelector('[data-sentinel="true"]');
    if (!sentinel) return;  // not yet rendered
    const root = this.template.querySelector('.virtual-list');
    this._observer = new IntersectionObserver(this.onIntersect.bind(this), {
        root,                  // in-shadow-root scrollable ancestor
        rootMargin: '200px',   // pre-fetch before user reaches the sentinel
        threshold: 0,
    });
    this._observer.observe(sentinel);
}

disconnectedCallback() {
    this._observer?.disconnect();
}
```

Two fixes: wire in `renderedCallback` after the sentinel exists, and
pass an explicit in-shadow-root `root`.

---

## Example 2 — Reach for `lightning-datatable` first, fall back only if it fails

**Context.** Product wants a list of 5,000 contracts on an account
record page. Engineer's first instinct: hand-build a virtual list.

**Wrong instinct.** Skip datatable, build a custom virtual list from
scratch.

**Why it's wrong.** 5,000 rows is in datatable's documented capability
range with `enable-infinite-loading` (load 50 at a time, append on
scroll). Custom virtual list adds shadow-DOM, observer, and
key-stability bugs before any of them exists in the requirements.

**Right answer.** `lightning-datatable` with `enable-infinite-loading`
and `pageSize=50`:

```html
<lightning-datatable
    key-field="Id"
    data={rows}
    columns={columns}
    enable-infinite-loading
    onloadmore={handleLoadMore}>
</lightning-datatable>
```

```js
async handleLoadMore(event) {
    event.target.isLoading = true;
    const more = await getRows({ offset: this.rows.length, limit: 50 });
    this.rows = this.rows.concat(more);
    event.target.isLoading = false;
}
```

Custom virtual list is the right answer when datatable's column model
or row complexity doesn't fit — not as the first step.

---

## Example 3 — Append-only virtual list with stable keys

**Context.** Card-style row layout (avatar + multi-line content).
Datatable doesn't fit. ~8,000 rows total. User typically scrolls
top-down once.

**Right answer.** Append-only virtual list. DOM grows as user scrolls;
caps at the dataset size.

```html
<template>
    <ul class="virtual-list" lwc:dom="manual">
        <template for:each={visible} for:item="item">
            <li key={item.id}>
                <c-row-card data={item}></c-row-card>
            </li>
        </template>
        <li class="sentinel" data-sentinel="true"></li>
        <template if:true={hasMore}>
            <li class="loading">Loading…</li>
        </template>
    </ul>
</template>
```

```js
import { LightningElement } from 'lwc';
import getRows from '@salesforce/apex/RowService.getRows';

export default class CardList extends LightningElement {
    visible = [];
    pageSize = 50;
    hasMore = true;
    _observer;

    async connectedCallback() {
        await this.loadNextPage();
    }

    renderedCallback() {
        if (this._observer || !this.hasMore) return;
        const sentinel = this.template.querySelector('[data-sentinel="true"]');
        if (!sentinel) return;
        const root = this.template.querySelector('.virtual-list');
        this._observer = new IntersectionObserver(
            entries => entries.some(e => e.isIntersecting) && this.loadNextPage(),
            { root, rootMargin: '200px', threshold: 0 }
        );
        this._observer.observe(sentinel);
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

`key={item.id}` on the `<li>` is the stable key. Without it, LWC tears
down and rebuilds every `<c-row-card>` on every page-load — the per-card
work multiplies by N pages.

---

## Example 4 — True windowing for very large datasets

**Context.** 100,000 contact records (data-export tool). Append-only
would balloon the DOM past acceptable; user can also scroll back up.

**Right answer.** True windowing — the DOM only ever holds the visible
slice plus a small buffer. Two spacer divs preserve scrollbar geometry.

```html
<template>
    <div class="window" lwc:dom="manual" onscroll={handleScroll}>
        <div class="spacer-top" style={topSpacerStyle}></div>
        <template for:each={slice} for:item="item">
            <div key={item.id} class="row">{item.name}</div>
        </template>
        <div class="spacer-bottom" style={bottomSpacerStyle}></div>
    </div>
</template>
```

```js
const ROW_HEIGHT = 36;       // px, must match CSS exactly
const WINDOW_SIZE = 100;     // rows in the DOM
const BUFFER = 20;           // rows above/below visible area

export default class Windowed extends LightningElement {
    total = 0;
    rows = [];        // full dataset
    start = 0;        // first index in the DOM

    get slice() {
        return this.rows.slice(this.start, this.start + WINDOW_SIZE);
    }

    get topSpacerStyle() {
        return `height: ${this.start * ROW_HEIGHT}px`;
    }

    get bottomSpacerStyle() {
        return `height: ${(this.total - this.start - WINDOW_SIZE) * ROW_HEIGHT}px`;
    }

    handleScroll(event) {
        const scrollTop = event.target.scrollTop;
        const desired = Math.max(
            0,
            Math.floor(scrollTop / ROW_HEIGHT) - BUFFER
        );
        if (Math.abs(desired - this.start) > BUFFER / 2) {
            this.start = desired;
        }
    }
}
```

Significantly more code than append-only. Use only when DOM growth is
a real ceiling.

---

## Anti-Pattern: Re-using a virtualization library written for non-shadow-DOM environments

```js
// react-virtualized-style libraries assume document-scoped IntersectionObserver
import VirtualList from 'some-vanilla-virtual-list';
new VirtualList(this.template.querySelector('.list'), { ... });
```

**What goes wrong.** The library creates its own IntersectionObserver
internally, often with `root: null` (the document). Inside Lightning's
shadow DOM, that observer doesn't fire. The list renders the initial
slice and never grows. Or the library tries to manipulate DOM with
`document.querySelector` and never finds the in-shadow-root nodes.

**Correct.** Either find a library that explicitly supports shadow DOM
and accepts a custom `root`, or hand-build with the patterns above.
The platform's official guidance has a specific caveat about "don't
support creation of infinite list items" precisely because there's no
clean library answer.
