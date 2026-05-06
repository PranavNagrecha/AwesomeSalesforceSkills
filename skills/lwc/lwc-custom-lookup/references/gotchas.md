# Gotchas — LWC Custom Lookup

Non-obvious behaviors that break custom typeahead lookups in production.

---

## Gotcha 1: `onclick` on results never fires (blur fires first)

The input's `blur` event fires before the result `<li>`'s `click`,
so the listbox closes and the click target is gone. Use
`onmousedown` on the result row — it fires on the press, before
blur.

---

## Gotcha 2: SOSL has a search-index lag

`FIND :term IN ALL FIELDS RETURNING ...` reads from the search
index. The index is updated asynchronously after DML — a record
created 5 seconds ago may not match yet. SOQL with `LIKE` reads
from the database directly and reflects DML immediately.

---

## Gotcha 3: `cacheable=true` requires no DML in the method

`@AuraEnabled(cacheable=true)` means the wire layer can cache.
Any DML or async (`enqueueJob`, future) inside the method makes
the call fail at runtime: "Action methods that update the
database aren't cacheable". Search methods must be pure reads.

---

## Gotcha 4: `WITH SECURITY_ENFORCED` is per-query

It enforces FLS for that one query. If your lookup also reads
from a related object via subquery, FLS is enforced on the
subquery too — but it raises `QueryException` if any field is
denied. Catch and degrade rather than letting it crash the
component.

---

## Gotcha 5: Debounce timer must be cleared on unmount

If the user navigates away while a search is in flight, the
timer fires and tries to update `this.results` on a disposed
component. LWC throws "Cannot set property on a non-reactive
target". Clear in `disconnectedCallback`:

```js
disconnectedCallback() {
    clearTimeout(this._searchTimer);
}
```

---

## Gotcha 6: Keyboard nav requires `event.preventDefault()` on
ArrowUp/Down

Without it, the browser scrolls the page when the user arrows
through results. `event.preventDefault()` keeps focus inside the
listbox.

---

## Gotcha 7: `aria-activedescendant` must reference an existing id

If you bind `aria-activedescendant` to a result row id but the
results array is empty (or activeIndex is -1), screen readers
report "no such id" and lose track of focus. Conditionally
render the attribute only when an active row exists.

---

## Gotcha 8: SOSL minimum query term is 2 characters

`FIND :term ...` with a 1-character term returns 0 rows in most
orgs (the search index requires ≥2 characters). Validate term
length before calling, and show "Type at least 2 characters" hint
text in the empty state.

---

## Gotcha 9: `String.escapeSingleQuotes` is not enough for SOSL

SOSL has its own escape rules — `?`, `*`, `&`, `|`, `!`, `(`,
`)`, `{`, `}`, `[`, `]`, `^`, `~`, `:`, `"`, `\` are special. For
a typeahead, strip these from user input rather than try to
escape them; `replaceAll('[?*&|!(){}\\[\\]\\^~:"\\\\]', '')` is
the practical default.
