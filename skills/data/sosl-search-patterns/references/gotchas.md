# Gotchas - Sosl Search Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Dynamic Search Text Becomes An Injection Surface

**What happens:** User input is concatenated into dynamic SOSL text.

**When it occurs:** Teams use `Search.query` for convenience without a safety boundary.

**How to avoid:** Prefer static SOSL with bind variables or tightly controlled query construction.

---

## Gotcha 2: Result Shape Surprises Consumers

**What happens:** The caller expects one flat result set and instead receives grouped lists by object.

**When it occurs:** The design copies SOQL assumptions into SOSL consumers.

**How to avoid:** Model the grouped response shape up front.

---

## Gotcha 3: Search UX Overpromises Precision

**What happens:** Stakeholders expect exact report-like behavior from a search experience.

**When it occurs:** Search and filtering requirements were never separated.

**How to avoid:** Be clear about when the flow is discovery and when it transitions to structured retrieval.

---

## Gotcha 4: `USING ListView` Silently Ignores Records Past The View's First 2,000

**What happens:** A `RETURNING Object(... USING ListView=<Name>)` search returns no hits for a record that clearly matches the `FIND` text.

**When it occurs:** The matching record sits beyond position 2,000 in the list view. Only the first 2,000 records of the list view are searched, according to the sort order the user has set for the view, so the eligible set is decided by the view's sort before the text is ever matched. A second surprise: only one list view can be specified, and the clause is unavailable to callers pinned below API version 41.

**How to avoid:** Treat the list view as a scope boundary, not a relevance ranker — if the target records can fall past the 2,000 mark, tighten the view's filter or sort so the wanted records lead, or drop the clause and scope with an explicit query instead. Confirm the calling context is API v41 or later (SOAP API, REST API, and Apex all support the clause).

---

## Gotcha 5: A `LIKE` Wildcard Escape Should Be Bound, Not Inlined

**What happens:** A SOQL `LIKE` query meant to match a literal underscore (so `name_a` matches but `namea` does not) matches too many records — the underscore keeps behaving as a wildcard even though it was escaped.

**When it occurs:** The escape (`\_` or `\%`, the two escape sequences that exist only inside `LIKE`) is written straight into the query string literal in Apex, where the Apex string parser processes the backslash before the SOQL engine sees it.

**How to avoid:** Bind the pattern as a `String` variable (`WHERE Name LIKE :searchTerm`) instead of concatenating it into the query text, so the platform handles the underscore/percent escaping rather than the Apex parser consuming it.
