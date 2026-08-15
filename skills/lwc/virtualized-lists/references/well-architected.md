# Well-Architected Notes — LWC Virtualized Lists

## Scope Boundary

Two skills cover long lists in this corpus:

| Approach | Skill |
|---|---|
| `lightning-datatable` + infinite loading; `IntersectionObserver` sentinel; server pagination | **this skill** |
| Hand-built windowed rendering — computing a visible slice from scroll offset, spacer sizing, height measurement | `lwc/lwc-virtualized-lists` |

The distinction is not stylistic. Infinite loading bounds the **network** work;
windowing bounds the **DOM**. Most Salesforce lists need only the first.

---

## Relevant Pillars

### Performance

The published guidance for `lightning-datatable` gives you the budget without
having to derive it: a maximum of **1,000 rows and 5 columns** for best
performance, **fewer than 20 columns** past 250 rows, and **50 rows per
request** ([Improve Datatable
Performance](https://developer.salesforce.com/docs/platform/lwc/guide/data-table-performance.html)).

Three consequences worth stating explicitly:

- **Columns are a budget line, not a requirement.** Row count is what teams
  manage; column count is what they add without noticing. A custom cell type
  multiplies its own cost by every rendered row, which is why the same guidance
  says to minimise `setTimeout()`, promises, and DOM nesting inside them.
- **Inline editing is a performance decision.** Reserve it for the fields that
  genuinely need it.
- **A ceiling with an escape hatch beats an unbounded list.** Past 1,000 client
  rows the honest UI is a filter or an export. "Showing the first 1,000 — narrow
  your filter" is a better product than a list that degrades silently.

Measure before building any of it. Under ~100 ms first render with 4× CPU
throttling, virtualisation buys nothing and costs a class of bugs — duplicate
requests, cursor resets, observer leaks — that a plain list does not have.

### Scalability

The binding constraint is a platform limit, not a rendering one: **`OFFSET`
cannot skip more than 2,000 records**
([OFFSET](https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_offset.htm)).
Any design that paginates by page number has a hard ceiling at page
`2000 / pageSize`, and degrades before reaching it because the database scans and
discards every skipped row.

Keyset pagination removes the ceiling and makes per-page cost constant. Its cost
is that it is sequential-only — which matches infinite scroll exactly and rules
it out for a numbered pager. For a numbered pager there is no third option:
filter until the result set fits under 2,000.

The tiebreak on a unique field is not optional. Without it, rows sharing a sort
value straddle a page boundary and are dropped or duplicated — intermittently,
which is the worst way for a bug to present.

### User Experience (Accessibility)

Both patterns break the assumption assistive technology makes: that the DOM
contains the list.

- **Never report the loaded count as the total.** `aria-setsize="-1"` means "size
  unknown" and is honest. Announcing "item 25 of 25" with 4,000 rows still to
  load is confident misinformation, which is worse than the attribute being
  absent.
- **Announce loading state and completion.** A polite live region saying
  "loading more" and then "all 340 entries loaded" is what tells a screen-reader
  user where they are.
- **Provide an escape hatch.** A keyboard user must never be required to tab
  through 4,000 items to reach the page footer. A filter, or a "load all and
  export" path, is the affordance.

For `lightning-datatable`, the base component owns its grid semantics — do not
hand-roll `aria-rowcount` on top of it. What you own is the loading and
completion announcement.

### Reliability

Three failure modes are structural rather than incidental:

| Failure | Cause | Fix |
|---|---|---|
| Duplicate page loads | `loadmore` fires while the trigger zone is visible | In-flight guard + termination flag |
| Endless polling at the end of the list | `enableInfiniteLoading` never set false | Set false on an empty page |
| Observer leak across route changes | `IntersectionObserver` holds the observed node | `disconnect()` in `disconnectedCallback` |

The one that produces wrong data rather than wasted work is the filter reset: a
cursor refers to a position in the *unfiltered* ordering, so carrying it across a
filter change appends rows from the wrong result set. It is the most commonly
omitted step in the pattern.

---

## Architectural Tradeoffs

### Infinite loading vs. true windowing

| | Infinite loading | Windowed rendering |
|---|---|---|
| Bounds the query | Yes | Yes |
| Bounds DOM nodes | **No** — grows monotonically | Yes |
| Variable row heights | Not a problem | Hard problem |
| Focus and scroll stability | Stable | Needs care |
| Build cost | Low | High |

Infinite loading is correct for the overwhelming majority of Salesforce lists,
because a stated ceiling plus a filter is an acceptable product. Windowing earns
its cost when the list genuinely must be scrollable to tens of thousands of rows
in one view — a rare requirement that is usually a report in disguise.

### `OFFSET` vs. keyset

`OFFSET` supports jump-to-page and caps at 2,000 with growing per-page cost.
Keyset is unbounded and constant-cost and cannot jump. Choose by whether the UI
has page numbers. If it does and the data set exceeds 2,000, the design decision
is upstream: reduce the result set with filters, because neither mechanism will
serve a numbered pager over 50,000 rows.

### `lightning-datatable` vs. a custom list

The base component brings grid accessibility, column resizing, sorting, row
selection, and inline editing for free, and imposes tabular structure plus the
documented row/column budget. A custom list gives arbitrary layout and requires
you to build the semantics. Take the base component whenever the data is
genuinely tabular; the accessibility work alone justifies it.

### Server filtering vs. client filtering

Client filtering is instant over loaded rows and cannot see anything else — a
correctness failure that presents as missing data. Server filtering costs a round
trip and a debounce and is the only version that is correct. For a fully-loaded
list under the ceiling, client filtering is fine; the moment pagination exists,
it is not.

### Ceiling with a filter vs. unbounded loading

A hard ceiling is a product decision that admits the tool's limits and gives the
user a better path (narrow the filter, export the rest). Unbounded loading defers
the decision to the point where the browser makes it, badly. The ceiling is
almost always the better product.

---

## Anti-Patterns

1. **`OFFSET` paging past 2,000.** A platform limit with no analogue in other
   SQL dialects, so it is easy to design past.

2. **Keyset without a tiebreak.** Silently drops or duplicates rows at page
   boundaries, intermittently.

3. **Unbounded `@AuraEnabled` queries.** Work at demo scale, hit heap limits in
   real orgs.

4. **`enable-infinite-loading` with no fixed-height container.** The attribute
   cannot function; the documentation ties the container to both the calculation
   and loop prevention.

5. **No in-flight guard on `loadmore`.** One scroll gesture, four identical
   requests.

6. **Observer created per render, or never disconnected.** Multiplied loads and a
   real leak.

7. **`aria-setsize` set to the loaded count.** Tells a screen-reader user the
   list is finished when it is not.

8. **Client filtering over a paginated list.** A correctness bug dressed as a
   performance choice.

---

## Hygiene

- Baseline measurement recorded before any virtualisation work begins.
- Page size capped at 50; client row ceiling stated in the UI with an escape
  hatch.
- In-flight guard and a termination flag on every load-more path.
- `disconnect()` and `clearTimeout` in `disconnectedCallback`.
- Cursor reset on every filter or sort change.
- Column count reviewed alongside row count.

---

## Related

- `lwc/lwc-virtualized-lists` — hand-built windowed rendering past the datatable
  budget.
- `lwc/lwc-custom-datatable-types` — custom cell types, whose cost multiplies by
  rendered row count.
- `lwc/lwc-performance-budgets` — where the row and column ceilings become
  enforceable budget lines.
- `lwc/lwc-accessibility-patterns` — live regions and `role="feed"` semantics.
- `apex/soql-performance` and `data/large-data-volume-patterns` — the query side
  of the same problem.
- `templates/lwc/patterns/imperativeApexPattern.js` — the imperative call shape
  the paging methods use.

---

## Official Sources Used

- Improve Datatable Performance — https://developer.salesforce.com/docs/platform/lwc/guide/data-table-performance.html
- lightning-datatable (Component Reference) — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide/lightning-datatable.html
- OFFSET (SOQL and SOSL Reference) — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_offset.htm
- LIMIT (SOQL and SOSL Reference) — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_limit.htm
- Access Elements the Component Owns (`lwc:ref`) — https://developer.salesforce.com/docs/platform/lwc/guide/create-components-dom-work.html
- Shadow DOM — https://developer.salesforce.com/docs/platform/lwc/guide/create-dom.html
- Lightning Web Components Developer Guide — https://developer.salesforce.com/docs/platform/lwc/guide/
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
