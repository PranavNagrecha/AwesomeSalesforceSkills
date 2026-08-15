# LLM Anti-Patterns — LWC Virtualized Lists

---

## Anti-Pattern 1: `OFFSET` pagination past the platform ceiling

**What the LLM generates:**

```apex
@AuraEnabled(cacheable=true)
public static List<Account> getPage(Integer pageNumber, Integer pageSize) {
    Integer offset = pageNumber * pageSize;
    return [SELECT Id, Name FROM Account ORDER BY Name LIMIT :pageSize OFFSET :offset];
}
```

**Why it happens:** `LIMIT`/`OFFSET` is the universal pagination idiom across
every SQL dialect and ORM. The 2,000-row cap is a Salesforce-specific constraint
with no analogue elsewhere, so nothing in the model's priors flags it.

**Correct pattern:** the maximum number of records `OFFSET` can skip is **2,000**
([OFFSET](https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_offset.htm)).
Use keyset pagination — carry the last row's sort key as a cursor — for anything
deeper. The tradeoff is that keyset is sequential-only, which suits infinite
scroll exactly.

**Detection hint:** an `OFFSET` bind variable computed from a page number, with
no cap on the page number.

---

## Anti-Pattern 2: Keyset pagination with no tiebreak

**What the LLM generates:**

```apex
WHERE CreatedDate < :lastSeenDate
ORDER BY CreatedDate DESC
```

**Why it happens:** the single-column comparison is the obvious translation of
"give me everything after this point", and it is correct whenever the sort key is
unique — which the model has no way to know it is not.

**Correct pattern:** the ordering must be total. Compare on a compound key with a
unique tiebreak:

```apex
WHERE CreatedDate < :cursorDate
   OR (CreatedDate = :cursorDate AND Id < :cursorId)
ORDER BY CreatedDate DESC, Id DESC
```

Without it, rows sharing a timestamp are silently dropped or duplicated at page
boundaries — intermittently, which makes it read as a data bug.

**Detection hint:** a cursor comparison on a single non-unique field.

---

## Anti-Pattern 3: The unbounded "get everything" Apex method

**What the LLM generates:**

```apex
@AuraEnabled(cacheable=true)
public static List<Account> getAllAccounts() {
    return [SELECT Id, Name, Industry FROM Account];
}
```

paired with a datatable bound to the whole result.

**Why it happens:** it is the shortest complete answer to "show accounts in a
datatable", and demo-scale data makes it work. Governor limits are invisible in a
scratch org with 200 records.

**Correct pattern:** always bound the query. The published guidance is **50 rows
per request** and a client-side ceiling of **1,000 rows / 5 columns**. Past that,
the honest UI is a filter or an export, not more DOM.

**Detection hint:** a SOQL query in an `@AuraEnabled` method with no `LIMIT`.

---

## Anti-Pattern 4: `enable-infinite-loading` without a fixed-height container

**What the LLM generates:** the attribute and the `onloadmore` handler, with the
table dropped straight into the template.

**Why it happens:** the attribute name reads as self-contained, and the container
requirement is a sentence in the performance guide rather than part of the API.

**Correct pattern:** the table must sit in a container with a defined height so
it can calculate where its bottom is — the documentation notes this both enables
the load-more calculation and prevents infinite looping. It is the first thing to
check when infinite loading "doesn't work".

**Detection hint:** `enable-infinite-loading` in a template with no height on any
ancestor.

---

## Anti-Pattern 5: No in-flight guard on `loadmore`

**What the LLM generates:**

```javascript
handleLoadMore() {
    this.loadNextPage();
}
```

**Why it happens:** the event reads as "the user reached the bottom", which
sounds like a discrete occurrence. That it fires repeatedly while the trigger
zone stays in view is behaviour, not signature.

**Correct pattern:** an in-flight boolean checked at the top, plus
`enableInfiniteLoading = false` when a page returns empty. Without the second
part the table keeps asking at the bottom of a complete list forever.

**Detection hint:** a `loadmore` handler with no guard and no termination
condition.

---

## Anti-Pattern 6: `IntersectionObserver` in `renderedCallback`, unguarded

**What the LLM generates:**

```javascript
renderedCallback() {
    const observer = new IntersectionObserver(...);
    observer.observe(this.template.querySelector('.sentinel'));
}
```

**Why it happens:** `renderedCallback` is where DOM references become available,
and the observer needs a DOM node. The multiplication is a consequence of LWC's
lifecycle rather than of the observer API.

**Correct pattern:** guard on an instance field so it is created once, and
`disconnect()` in `disconnectedCallback`. Appending items re-renders, so an
unguarded observer accumulates and each new page triggers several loads.

**Detection hint:** `new IntersectionObserver` in `renderedCallback` with no
early return, or no `disconnect()` in the component.

---

## Anti-Pattern 7: `IntersectionObserver` with the default `root`

**What the LLM generates:**

```javascript
new IntersectionObserver(callback, { rootMargin: '200px' });   // root: null
```

**Why it happens:** viewport-relative observation is the common case in ordinary
web pages and the default exists because of that. A list scrolling inside its own
container is the exception.

**Correct pattern:** set `root` to the scrolling element in your shadow tree,
obtained via `lwc:ref` / `this.refs` — `document.querySelector` cannot reach into
a shadow tree. With the default root the sentinel is inside the viewport
regardless of container scroll, so the observer fires continuously.

**Detection hint:** no `root` in the observer options for a list that scrolls
inside a fixed-height container.

---

## Anti-Pattern 8: Reporting the loaded count as `aria-setsize`

**What the LLM generates:**

```html
<li aria-posinset={item.index} aria-setsize={items.length}>
```

**Why it happens:** `items.length` is the only count in scope, and populating the
attribute reads as more accessible than leaving it out.

**Correct pattern:** `aria-setsize="-1"` means "size unknown" and is the honest
value for an infinite list. Announcing "item 25 of 25" to a screen-reader user
with 4,000 rows still to load tells them the list is complete — confident
misinformation, which is worse than the attribute being absent.

**Detection hint:** `aria-setsize` bound to the length of a progressively-loaded
array.

---

## Anti-Pattern 9: Client-side filtering over a paginated list

**What the LLM generates:**

```javascript
get filteredRows() {
    return this.rows.filter((r) => r.Name.includes(this.searchTerm));
}
```

**Why it happens:** `Array.filter` is the natural expression of filtering and it
is genuinely correct for a fully-loaded list. The interaction with pagination is
a system-level property that a single component does not reveal.

**Correct pattern:** filtering goes to the server, because only the server can
search rows the client has never loaded. A client-side filter over a paginated
list is a correctness bug — a user searching for a record on page 40 finds
nothing — presented as a performance decision.

And when the filter changes, **reset the cursor**. It refers to a position in the
unfiltered ordering; carrying it across a filter change appends the wrong rows.
That reset is the most commonly omitted step in the whole pattern.

**Detection hint:** a filter applied to a locally-accumulated array in a
component that also paginates.

---

## Anti-Pattern 10: Calling infinite loading "virtualisation"

**What the LLM generates:** infinite loading, described as virtualising the list
and as solving memory usage.

**Why it happens:** both techniques answer "my list is too long" and both appear
under the same search terms. The distinction — bounding network work versus
bounding DOM nodes — is not one the framing forces.

**Correct pattern:** infinite loading bounds the query and the initial render;
loaded rows stay in the DOM, so memory grows monotonically as the user scrolls.
True virtualisation removes off-screen nodes and is a harder build with its own
failure modes (variable heights, scrollbar drift, focus loss). Say which one you
are doing. For most Salesforce lists, infinite loading with a stated ceiling —
and a filter or export past it — is the right answer.

**Detection hint:** the word "virtualised" applied to a design where nothing is
ever removed from the DOM.

---

## Anti-Pattern 11: Optimising with no measurement

**What the LLM generates:** a full virtualisation design in response to "my list
feels slow", with no measurement step.

**Why it happens:** the request implies a problem and the model supplies the
strongest solution to the implied problem. Asking for a measurement first is not
what "help me make this faster" appears to request.

**Correct pattern:** measure before building. Chrome DevTools Performance with
4× CPU throttling approximates a low-end device. Under ~100 ms first render and
smooth scrolling there, virtualisation adds a class of bugs — duplicate
requests, cursor resets, observer leaks — that the simple list does not have.

**Detection hint:** an optimisation plan with no baseline and no target.

---

## Anti-Pattern 12: Ignoring the column budget

**What the LLM generates:** an 18-column datatable with attentive row-count
management.

**Why it happens:** rows are the variable in the question, so rows are the
variable that gets managed. Columns are treated as a requirement rather than a
cost.

**Correct pattern:** the guidance names both — a maximum of 1,000 rows and 5
columns for best performance, and fewer than 20 columns past 250 rows. Inline
editing should be reserved for critical fields because it costs performance, and
custom cell types should minimise `setTimeout()`, promises, and DOM nesting,
because their cost multiplies by every rendered row.

**Detection hint:** a column array longer than about eight entries in a table
that also paginates.
