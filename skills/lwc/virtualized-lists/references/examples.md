# Examples — LWC Virtualized Lists

**Scope note.** This skill covers the two paths that get you to a working long
list quickly: `lightning-datatable` with infinite loading, and an
`IntersectionObserver` sentinel for non-tabular content. Hand-built windowed
rendering — computing a visible slice from scroll position and translating a
spacer — is `lwc/lwc-virtualized-lists`.

---

## The numbers that decide the approach

Salesforce publishes concrete guidance for `lightning-datatable`
([Improve Datatable
Performance](https://developer.salesforce.com/docs/platform/lwc/guide/data-table-performance.html)):

| Guidance | Value |
|---|---|
| Recommended maximum for best performance | **1,000 rows and 5 columns** |
| If exceeding 250 rows | use **fewer than 20 columns** |
| Load per request | **maximum 50 rows** at a time, using `LIMIT` |
| Pagination | `LIMIT` + `OFFSET`, or infinite scrolling |
| Inline editing | reserve for critical fields only — it costs performance |

And a hard platform ceiling that shapes any `OFFSET`-based design: **the maximum
number of records `OFFSET` can skip is 2,000**
([OFFSET](https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_offset.htm)).
That is why offset pagination cannot be the answer for a genuinely large data
set, and why the keyset pattern in Example 3 exists.

**Measure before optimising.** If first render is under ~100 ms and scrolling is
smooth on the lowest-spec device your users have, virtualisation adds complexity
for nothing. Chrome DevTools Performance panel with CPU throttling at 4× is the
cheap version of that measurement.

---

## Example 1 — WRONG vs RIGHT: 10,000 audit-log rows

### WRONG — query everything, render everything

```javascript
import { LightningElement, wire } from 'lwc';
import getAllLogs from '@salesforce/apex/AuditLogController.getAllLogs';

export default class AuditLogViewer extends LightningElement {
    // (1) unbounded query — will hit the Apex heap limit before it hits the UI
    @wire(getAllLogs)
    logs;

    columns = [ /* 14 columns */ ];   // (2) far past the 5-column guidance
}
```

```html
<template>
    <!-- (3) no container height, so infinite loading could not work anyway -->
    <lightning-datatable
        key-field="Id"
        data={logs.data}
        columns={columns}>
    </lightning-datatable>
</template>
```

Three independent failures. The query is unbounded, so a large org hits the Apex
heap governor limit before the browser sees anything. Fourteen columns against a
row count in the thousands is well outside the published guidance. And there is
no fixed-height container, which is a prerequisite for the datatable to know
where its bottom is.

### RIGHT — infinite loading, bounded page size, fixed-height container

```javascript
import { LightningElement } from 'lwc';
import getLogPage from '@salesforce/apex/AuditLogController.getLogPage';

const PAGE_SIZE = 50;          // the documented per-request maximum
const MAX_CLIENT_ROWS = 1000;  // the documented performance ceiling

const COLUMNS = [
    { label: 'When',   fieldName: 'CreatedDate', type: 'date', initialWidth: 160 },
    { label: 'User',   fieldName: 'UserName',    type: 'text' },
    { label: 'Action', fieldName: 'Action__c',   type: 'text' },
    { label: 'Object', fieldName: 'SObject__c',  type: 'text' },
    { label: 'Result', fieldName: 'Result__c',   type: 'text' }
];

export default class AuditLogViewer extends LightningElement {
    columns = COLUMNS;
    rows = [];
    isLoading = false;
    enableInfiniteLoading = true;
    reachedCeiling = false;

    _cursor = null;    // last-seen sort key, NOT an offset — see Example 3
    _inFlight = false;

    connectedCallback() {
        this.loadNextPage();
    }

    async handleLoadMore(event) {
        // The datatable fires loadmore repeatedly while the sentinel is in
        // view. Without this guard you issue four identical requests.
        if (this._inFlight || !this.enableInfiniteLoading) {
            return;
        }
        // The event target exposes isLoading; setting it shows the inline
        // spinner at the bottom of the table rather than over the whole page.
        const table = event.target;
        table.isLoading = true;
        await this.loadNextPage();
        table.isLoading = false;
    }

    async loadNextPage() {
        this._inFlight = true;
        this.isLoading = true;
        try {
            const page = await getLogPage({
                cursorCreatedDate: this._cursor?.createdDate ?? null,
                cursorId: this._cursor?.id ?? null,
                pageSize: PAGE_SIZE
            });

            if (page.length === 0) {
                this.enableInfiniteLoading = false;   // stop asking
                return;
            }

            const last = page[page.length - 1];
            this._cursor = { createdDate: last.CreatedDate, id: last.Id };
            this.rows = [...this.rows, ...page];

            // Respect the client-side ceiling explicitly rather than
            // discovering it as jank. Past this point, the honest answer is
            // "filter or export", not "render more".
            if (this.rows.length >= MAX_CLIENT_ROWS) {
                this.enableInfiniteLoading = false;
                this.reachedCeiling = true;
            }
        } catch (error) {
            this.enableInfiniteLoading = false;
            this.dispatchEvent(new CustomEvent('loaderror', { detail: { error } }));
        } finally {
            this._inFlight = false;
            this.isLoading = false;
        }
    }
}
```

```html
<template>
    <!-- The fixed height is REQUIRED. Place the table in a container with a
         defined height so it can calculate where the bottom is; without it
         the table cannot decide when to load more and can loop. -->
    <div style="height: 480px;" class="slds-scrollable_y">
        <lightning-datatable
            key-field="Id"
            data={rows}
            columns={columns}
            enable-infinite-loading={enableInfiniteLoading}
            load-more-offset="120"
            onloadmore={handleLoadMore}
            hide-checkbox-column>
        </lightning-datatable>
    </div>

    <template lwc:if={reachedCeiling}>
        <div role="status" class="slds-text-body_small slds-p-around_small">
            Showing the first 1,000 entries. Narrow the date range or export
            the full log.
            <lightning-button label="Export" onclick={handleExport}></lightning-button>
        </div>
    </template>
</template>
```

### Why each choice

- **`load-more-offset="120"`** rather than the 20px default. The default triggers
  loading when you scroll to within 20px of the bottom, which on a fast scroll
  means the user reaches empty space before the data arrives. A larger offset
  starts fetching earlier.
- **`_inFlight` guard.** `loadmore` fires repeatedly while the trigger zone is
  visible. Without a guard, one scroll gesture produces several identical
  requests — each consuming an API call and racing to append.
- **`enableInfiniteLoading = false` on an empty page.** This is how you tell the
  table there is nothing more. Leaving it true means the table keeps asking at
  the bottom of the list forever.
- **`table.isLoading` from the event target.** The documented way to show the
  inline bottom spinner during a `loadmore` fetch.
- **A stated ceiling with an escape hatch.** Past 1,000 client rows the honest
  answer is a filter or an export, not more DOM.

---

## Example 2 — `IntersectionObserver` for a non-tabular feed

### Context

An activity feed with variable-height cards. `lightning-datatable` is the wrong
shape.

```javascript
import { LightningElement } from 'lwc';
import getFeedPage from '@salesforce/apex/ActivityFeedController.getPage';

const PAGE_SIZE = 25;

export default class ActivityFeed extends LightningElement {
    items = [];
    isLoading = false;
    hasMore = true;

    _observer = null;
    _cursor = null;
    _inFlight = false;

    connectedCallback() {
        this.loadNextPage();
    }

    renderedCallback() {
        // Create ONCE. renderedCallback runs on every re-render, and appending
        // items re-renders — so an unguarded observer here multiplies.
        if (this._observer) {
            return;
        }
        const sentinel = this.refs?.sentinel;
        if (!sentinel) {
            return;
        }

        this._observer = new IntersectionObserver(
            (entries) => {
                if (entries.some((e) => e.isIntersecting)) {
                    this.loadNextPage();
                }
            },
            {
                // root MUST be the scrolling element inside the shadow tree.
                // Leaving it null uses the viewport, which is wrong whenever
                // the feed scrolls inside its own container.
                root: this.refs.scroller,
                rootMargin: '400px 0px',   // start loading before it is visible
                threshold: 0
            }
        );
        this._observer.observe(sentinel);
    }

    disconnectedCallback() {
        // IntersectionObserver holds a reference to the observed element.
        // Failing to disconnect is a genuine leak across route changes.
        if (this._observer) {
            this._observer.disconnect();
            this._observer = null;
        }
    }

    async loadNextPage() {
        if (this._inFlight || !this.hasMore) {
            return;
        }
        this._inFlight = true;
        this.isLoading = true;
        try {
            const page = await getFeedPage({
                cursorDate: this._cursor?.date ?? null,
                cursorId: this._cursor?.id ?? null,
                pageSize: PAGE_SIZE
            });
            if (page.length < PAGE_SIZE) {
                this.hasMore = false;
            }
            if (page.length > 0) {
                const last = page[page.length - 1];
                this._cursor = { date: last.ActivityDate, id: last.Id };
                this.items = [...this.items, ...page];
            }
        } catch (error) {
            this.hasMore = false;
            this.dispatchEvent(new CustomEvent('loaderror', { detail: { error } }));
        } finally {
            this._inFlight = false;
            this.isLoading = false;
        }
    }
}
```

```html
<template>
    <div lwc:ref="scroller"
         class="slds-scrollable_y"
         style="height: 600px;"
         role="feed"
         aria-busy={isLoading}>

        <template for:each={items} for:item="item">
            <article key={item.Id}
                     role="article"
                     aria-posinset={item.position}
                     aria-setsize="-1">
                <!-- aria-setsize="-1" means "total unknown", which is honest
                     for an infinite feed. Do NOT report the loaded count as
                     the total — that tells a screen reader the list is
                     complete when it is not. -->
                <c-activity-card activity={item}></c-activity-card>
            </article>
        </template>

        <template lwc:if={hasMore}>
            <div lwc:ref="sentinel" class="sentinel" aria-hidden="true"></div>
        </template>
        <template lwc:else>
            <p class="slds-text-body_small slds-align_absolute-center">
                End of feed
            </p>
        </template>
    </div>

    <template lwc:if={isLoading}>
        <div role="status" class="slds-assistive-text">Loading more activities</div>
    </template>
</template>
```

### The three details that break this if you get them wrong

- **`root` must be the scrolling element.** Default `root: null` observes against
  the viewport. When the feed scrolls inside its own fixed-height container, the
  sentinel is "intersecting the viewport" the whole time and the observer fires
  continuously.
- **Create the observer once.** `renderedCallback` runs after every re-render,
  and appending items re-renders. Unguarded, you accumulate observers and each
  new page triggers N loads.
- **`disconnect()` in `disconnectedCallback`.** The observer holds a reference to
  the observed node. Skipping this leaks across every route change.

---

## Example 3 — Keyset pagination, because `OFFSET` caps at 2,000

### The problem with `OFFSET`

```apex
// WRONG past 2,000 rows — and progressively slower before that.
return [
    SELECT Id, Name, CreatedDate FROM Audit_Log__c
    ORDER BY CreatedDate DESC
    LIMIT :pageSize OFFSET :offset          // offset cannot exceed 2000
];
```

The maximum number of records `OFFSET` can skip is **2,000**. Beyond that the
query fails. And even under the cap it degrades: the database must scan and
discard every skipped row, so page 40 is meaningfully more expensive than page 1.

### The fix — carry a cursor, not a count

```apex
public with sharing class AuditLogController {

    /**
     * Keyset ("seek") pagination.
     *
     * The cursor is the sort key of the last row the client already has.
     * The tiebreak on Id is REQUIRED: CreatedDate is not unique, and without
     * it rows sharing a timestamp are skipped or duplicated at page edges.
     */
    @AuraEnabled(cacheable=true)
    public static List<Audit_Log__c> getLogPage(
        Datetime cursorCreatedDate,
        Id cursorId,
        Integer pageSize
    ) {
        Integer size = Math.min(
            pageSize == null ? 50 : pageSize,
            50                                 // documented per-request maximum
        );

        if (cursorCreatedDate == null) {
            return [
                SELECT Id, Name, CreatedDate, Action__c, SObject__c, Result__c
                FROM Audit_Log__c
                WITH USER_MODE
                ORDER BY CreatedDate DESC, Id DESC
                LIMIT :size
            ];
        }

        return [
            SELECT Id, Name, CreatedDate, Action__c, SObject__c, Result__c
            FROM Audit_Log__c
            WHERE CreatedDate < :cursorCreatedDate
               OR (CreatedDate = :cursorCreatedDate AND Id < :cursorId)
            WITH USER_MODE
            ORDER BY CreatedDate DESC, Id DESC
            LIMIT :size
        ];
    }
}
```

### What keyset buys and what it costs

| | `OFFSET` | Keyset |
|---|---|---|
| Depth ceiling | 2,000 rows | None |
| Cost of page N | Grows with N | Constant |
| Jump to page 40 | Yes | **No** — sequential only |
| Stable under concurrent inserts | No — rows shift | Yes |
| Index requirement | Sort field | Sort field, ideally `CreatedDate` |

The cost is real: keyset cannot jump to an arbitrary page. That is fine for
infinite scroll, which is inherently sequential, and wrong for a numbered
pager — in which case reduce the result set with filters until `OFFSET` is
viable, because there is no third option under 2,000.

**The tiebreak is the part that is silently wrong when omitted.** Two audit rows
written in the same second, with a cursor on `CreatedDate` alone, produce a page
boundary that either drops one or repeats it. The compound `(CreatedDate, Id)`
comparison makes the ordering total.

Mark the method `cacheable=true` so it is eligible for the Lightning Data Service
client cache, and keep `WITH USER_MODE` so the running user's FLS and sharing
apply to every page.

---

## Example 4 — Accessibility for a list that is never fully rendered

Virtualisation and infinite loading both break the assumption assistive
technology makes: that the DOM contains the list.

### For `lightning-datatable`

The base component manages its own grid semantics. Do not hand-roll
`aria-rowcount` on top of it — the addition you own is telling the user when
loading is happening and when it has stopped:

```html
<div role="status" aria-live="polite" class="slds-assistive-text">
    {loadingAnnouncement}
</div>
```

```javascript
get loadingAnnouncement() {
    if (this.isLoading) return 'Loading more rows';
    if (this.reachedCeiling) return `Showing the first ${this.rows.length} of many entries. Narrow your filter to see more.`;
    if (!this.enableInfiniteLoading) return `All ${this.rows.length} entries loaded.`;
    return '';
}
```

### For a custom feed

```html
<div role="feed" aria-busy={isLoading}>
    <article role="article"
             aria-posinset={item.position}
             aria-setsize="-1">
```

`aria-setsize="-1"` means "size unknown" and is the honest value for an infinite
feed. **Do not report the loaded count as the total.** Announcing "item 25 of
25" to a screen-reader user when 4,000 more exist tells them the list is
finished, which is worse than saying nothing.

### The keyboard trap to avoid

Focus must not be lost when new items append. If the user is on the last card
and a page loads, the card must keep focus — appending items after it does not
move focus by itself, but re-creating the list (rather than appending to it)
does. This is another reason to append with a spread rather than replacing the
array wholesale from a fresh query.

Provide a real escape hatch: a "load all and export" path, or a filter, so a
keyboard user is never required to tab through 4,000 items to reach the footer.

---

## Example 5 — Debounced filtering, and why filtering belongs on the server

### The failing version

```javascript
handleFilterChange(event) {
    const term = event.target.value.toLowerCase();
    // Re-filters the entire client-side array on EVERY keystroke.
    this.visibleRows = this.allRows.filter(
        (r) => r.Name.toLowerCase().includes(term));
}
```

On 1,000 rows this is perceptible; on a fast typist it queues main-thread work
per keystroke and drops frames. And it can only ever filter what has been
loaded — a search for a record on page 40 finds nothing, which reads as a data
bug rather than a design limit.

### The working version

```javascript
const DEBOUNCE_MS = 300;

handleFilterChange(event) {
    const term = event.target.value;
    window.clearTimeout(this._filterTimer);
    this._filterTimer = window.setTimeout(() => {
        this.applyFilter(term);
    }, DEBOUNCE_MS);
}

disconnectedCallback() {
    window.clearTimeout(this._filterTimer);   // a pending timer outlives the component
}

async applyFilter(term) {
    // A filter change RESETS pagination. Forgetting this appends filtered
    // results onto unfiltered ones — the most common bug in this pattern.
    this.rows = [];
    this._cursor = null;
    this.enableInfiniteLoading = true;
    this.reachedCeiling = false;
    this._filterTerm = term;
    await this.loadNextPage();
}
```

Two points that matter more than the debounce itself:

- **Filtering resets pagination.** The cursor refers to a position in the
  *unfiltered* ordering. Carrying it across a filter change appends the wrong
  rows.
- **The filter goes to the server.** Only the server can search rows the client
  has never loaded. A client-side filter over a paginated list is a correctness
  bug that looks like a performance decision.

Debounce every keystroke-driven server call. 300 ms is a reasonable default: long
enough to skip intermediate states, short enough to feel responsive.
