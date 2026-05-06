# LLM Anti-Patterns — LWC Custom Lookup

Common mistakes AI coding assistants make when building custom typeahead lookups in LWC.

---

## Anti-Pattern 1: No debounce — Apex callout per keystroke

**What the LLM generates.**

```js
handleInput(event) {
    searchAccounts({ term: event.target.value })
        .then(r => this.results = r);
}
```

**Correct pattern.** Wrap in `setTimeout` / `clearTimeout` with
~280ms debounce. Without it, typing "Acme Corporation" fires 16
callouts and pegs the org's Apex CPU.

**Detection hint.** Any `oninput` handler that calls an Apex
import without a `setTimeout` wrapper is undebounced.

---

## Anti-Pattern 2: `onclick` on result rows

**What the LLM generates.**

```html
<li onclick={handleSelect}>{result.title}</li>
```

**Correct pattern.** Use `onmousedown` — `click` fires after
`blur`, by which time the listbox has closed and the target is
gone. `mousedown` fires on press, before blur.

**Detection hint.** Any `<li onclick=...>` inside a
`role="listbox"` element where the parent input has a blur
handler that closes the list.

---

## Anti-Pattern 3: SOQL `LIKE '%' + term + '%'` without escaping

**What the LLM generates.**

```apex
String like = '%' + term + '%';
List<Account> r = [SELECT Id FROM Account WHERE Name LIKE :like];
```

**Correct pattern.** `String.escapeSingleQuotes(term)` before
concatenation. Without it, a term containing a single quote
breaks the query (with bind variables LIKE is safe-ish, but the
`%` wrappers still allow injection of additional patterns).

**Detection hint.** Any `LIKE` query whose right-hand side is
built from user input via `+` without a sanitization call.

---

## Anti-Pattern 4: Marking the search method `cacheable=false`
to "force fresh"

**What the LLM generates.**

```apex
@AuraEnabled  // no cacheable=true
public static List<LookupResult> search(...) { ... }
```

**Correct pattern.** Use `cacheable=true`. The wire layer caches
identical queries, which is what you want — duplicate keystrokes
("acm" → "acme" → "acm") should return cached results, not
re-query.

**Detection hint.** Any `@AuraEnabled` Apex method named
`search*` that omits `cacheable=true` and returns a list of
records.

---

## Anti-Pattern 5: Forgetting to render the loading spinner

**What the LLM generates.** A lookup that shows the previous
results while a new search is in flight.

**Correct pattern.** Show `lightning-spinner` (size="x-small")
in the listbox while `isLoading` is true. Otherwise the user
typed "Acme" but still sees results for "Acm" and clicks the
wrong one.

**Detection hint.** Any lookup component without an `isLoading`
state or spinner element in the listbox template.

---

## Anti-Pattern 6: Keyboard navigation that doesn't preventDefault

**What the LLM generates.**

```js
case 'ArrowDown':
    this.activeIndex++;
    break;
```

**Correct pattern.**

```js
case 'ArrowDown':
    event.preventDefault();
    this.activeIndex = Math.min(this.activeIndex + 1, max);
    break;
```

Without `preventDefault()`, the page scrolls when the user
arrows through results.

**Detection hint.** Any `ArrowDown`/`ArrowUp` switch case that
does not call `event.preventDefault()`.

---

## Anti-Pattern 7: Showing all results on focus with no filter

**What the LLM generates.**

```js
handleFocus() {
    searchAccounts({ term: '' }).then(r => this.results = r);
}
```

**Correct pattern.** Show "Recently Viewed" via a separate
`getRecentlyViewed` Apex method, or do nothing on focus until
the user types ≥2 characters. An unfiltered query returns the
first 10 records by ordering, which is rarely useful.

**Detection hint.** Any `handleFocus` that calls the search
function with an empty term.
