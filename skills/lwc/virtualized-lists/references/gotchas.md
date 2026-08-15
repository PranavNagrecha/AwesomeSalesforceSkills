# Gotchas — LWC Virtualized Lists

---

## 1. `enable-infinite-loading` does nothing without a fixed-height container

**What happens:** the attribute is set, `onloadmore` is bound, and the handler
never fires — or fires continuously in a loop.

**Why:** the datatable needs to know where its bottom is in order to decide when
to load more. The documentation is explicit: place the table in a container with
a defined height, which enables the calculation and *prevents infinite looping*
([Improve Datatable
Performance](https://developer.salesforce.com/docs/platform/lwc/guide/data-table-performance.html)).

**How to avoid:** wrap the table in a container with an explicit height, and use
`slds-scrollable_y` on it. This is the first thing to check when infinite loading
"doesn't work".

---

## 2. `loadmore` fires repeatedly, producing duplicate requests

**What happens:** one scroll gesture issues four identical Apex calls. Rows
appear duplicated, or the same page appends several times.

**Why:** the event fires while the trigger zone remains in view, not once per
scroll.

**How to avoid:** an in-flight guard that returns early, plus setting
`enableInfiniteLoading = false` when a page comes back empty. Without the second
part, the table keeps asking at the bottom of a complete list indefinitely.

```javascript
if (this._inFlight || !this.enableInfiniteLoading) return;
```

---

## 3. `OFFSET` cannot exceed 2,000

**What happens:** offset pagination works through the first forty pages and then
the query fails.

**The documented limit:** the maximum number of records `OFFSET` can skip is
**2,000**
([OFFSET](https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_offset.htm)).

**How to avoid:** keyset (seek) pagination — carry the last row's sort key as a
cursor instead of a count. It has no depth ceiling and constant per-page cost.
The tradeoff is that it cannot jump to an arbitrary page, which is fine for
infinite scroll and wrong for a numbered pager. For a numbered pager, filter the
result set down until `OFFSET` is viable; there is no third option.

---

## 4. Keyset pagination without a tiebreak drops or duplicates rows

**What happens:** rows sharing a `CreatedDate` value straddle a page boundary.
One is skipped, or one appears twice. It is intermittent and looks like a data
problem.

**Why:** `WHERE CreatedDate < :cursor` cannot distinguish rows with equal
timestamps, so the ordering is not total.

**How to avoid:** a compound comparison on a unique tiebreak.

```apex
WHERE CreatedDate < :cursorCreatedDate
   OR (CreatedDate = :cursorCreatedDate AND Id < :cursorId)
ORDER BY CreatedDate DESC, Id DESC
```

`Id` is always available and always unique. Order by both, compare on both.

---

## 5. Column count matters as much as row count

**What happens:** a table performs acceptably at 400 rows and 4 columns and
becomes unusable at 400 rows and 18 columns, with no change to the query.

**The documented guidance:** a maximum of **1,000 rows and 5 columns** for best
performance, and if you exceed 250 rows, use **fewer than 20 columns**.

**How to avoid:** treat columns as a budget line alongside rows. The row count is
what teams tune and the column count is what they add without noticing.

Two related notes from the same guidance: reserve inline editing for critical
fields only, as it negatively impacts performance; and in custom data types
minimise `setTimeout()` and promises, reduce DOM nesting, and avoid complex
interactions — a heavy custom cell type multiplies by every rendered row.

---

## 6. `load-more-offset` defaults to 20px, which is too late

**What happens:** on a fast scroll the user reaches blank space before the next
page arrives, and the list appears to stutter.

**Why:** by default, loading is triggered at 20px from the bottom of the table.

**How to avoid:** raise it — `load-more-offset="120"` or more — so the fetch
starts before the user reaches the edge. Tune against a realistic device and a
realistic network, not against a local scratch org on a fast laptop.

---

## 7. `IntersectionObserver` created in `renderedCallback` multiplies

**What happens:** the first page loads once, the second twice, the third four
times.

**Why:** `renderedCallback` runs after every re-render, and appending items
causes a re-render. Each pass creates and attaches another observer.

**How to avoid:** guard on an instance field and create exactly once. And
`disconnect()` in `disconnectedCallback` — the observer holds a reference to the
observed element, so skipping it leaks across route changes.

---

## 8. `IntersectionObserver` with the default `root` fires continuously

**What happens:** the sentinel is reported as intersecting from the moment the
component renders, and pages load until the data runs out.

**Why:** `root: null` observes against the browser viewport. When the list
scrolls inside its own fixed-height container, the sentinel is inside the
viewport regardless of the container's scroll position.

**How to avoid:** set `root` to the scrolling element inside your shadow tree.
Because `document.querySelector` cannot reach into a component's shadow tree,
this must be a reference you hold — `lwc:ref` plus `this.refs.scroller` is the
recommended way to get it
([Access Elements the Component
Owns](https://developer.salesforce.com/docs/platform/lwc/guide/create-components-dom-work.html)).

---

## 9. Reporting the loaded count as the total lies to screen readers

**What happens:** an accessibility fix adds `aria-setsize={items.length}` to a
feed with 4,000 available items and 25 loaded. A screen-reader user hears "item
25 of 25" and concludes the list is finished.

**How to avoid:** `aria-setsize="-1"` means "size unknown" and is the honest
value for an infinite feed. If the true total is known and cheap to query, use
it. What you must not do is report the loaded count as the total — that is worse
than silence, because it produces confident misinformation.

---

## 10. Client-side filtering over a paginated list is a correctness bug

**What happens:** a user searches for a record they know exists. Nothing is
found, because that record is on a page the client never loaded. It reads as
missing data.

**How to avoid:** filtering goes to the server. Only the server can search rows
the client has never seen. Debounce the keystrokes (300 ms is a reasonable
default) and **reset the cursor** when the filter changes — the cursor refers to a
position in the unfiltered ordering, and carrying it across a filter change
appends the wrong rows. That reset is the most commonly forgotten step in this
pattern.

---

## 11. A pending debounce timer outlives the component

**What happens:** the user types, navigates away within the debounce window, and
a callback fires against a destroyed component.

**How to avoid:** `clearTimeout` in `disconnectedCallback`. Any `setTimeout`,
`setInterval`, or `IntersectionObserver` created by the component needs a
matching teardown, and the debounce timer is the one most often missed because
it feels transient.

---

## 12. Variable row heights defeat naive windowing

**What happens:** a hand-built windowed list with a spacer sized as
`rowCount × assumedHeight` scrolls smoothly until a row wraps to two lines, at
which point the scrollbar and content disagree and items jump.

**How to avoid:** fix the row height, or measure heights and maintain a running
offset table. This is the point at which the problem stops being "add infinite
loading" and becomes a genuine virtualisation engineering task — see
`lwc/lwc-virtualized-lists`. Infinite loading with `IntersectionObserver`, as in
this skill, does **not** have this problem, because every loaded row stays in the
DOM.

---

## 13. Infinite loading and DOM-node virtualisation are different things

**What happens:** a team adopts infinite loading, calls the list "virtualised",
and is surprised when memory grows steadily as the user scrolls.

**Why:** infinite loading bounds the *network* work by fetching in pages. It does
not bound the *DOM*, because loaded rows are never removed. Memory and layout
cost grow monotonically.

**How to avoid:** know which problem you have. Infinite loading solves initial
load time and query size. True virtualisation — removing off-screen nodes —
solves memory and sustained scroll performance and is the harder build. For most
Salesforce lists, infinite loading with a stated ceiling (and a filter or export
past it) is the right answer; genuine windowing is `lwc/lwc-virtualized-lists`.

---

## 14. Optimising before measuring

**What happens:** a component is virtualised, an observer added, pagination
built — for a list that renders 60 rows in 40 ms.

**How to avoid:** measure first. Chrome DevTools Performance panel with 4× CPU
throttling approximates a low-end device cheaply. If first render is under
~100 ms and scrolling is smooth there, the complexity buys nothing and costs a
class of bugs — duplicate requests, cursor resets, observer leaks — that a simple
list does not have.
