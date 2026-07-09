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

## Gotcha 5: A Long `FIND` Search Query Silently Drops Operators Or Returns Nothing

**What happens:** A search built from long free-text or concatenated user input starts returning far more rows than the `AND`-joined terms should allow — or comes back empty even though matches clearly exist.

**When it occurs:** The search query string crosses a length cliff. Past 4,000 characters the logical operators are removed, so an `AND`-joined search no longer requires every term and the result set broadens unexpectedly. Past 10,000 characters no result rows are returned at all. Both cliffs are easy to hit when the term is assembled from user input, pasted text, or a long list of OR-joined values.

**How to avoid:** Cap and validate the length of assembled search text before running the query, keeping it well under 4,000 characters. Treat a search string that approaches that mark as a signal to redesign the query — for example, narrow the scope, split the work, or feed the terms through a different pattern — rather than passing raw long text straight into `FIND`.

---

## Gotcha 6: A `LIKE` Wildcard Escape Should Be Bound, Not Inlined

**What happens:** A SOQL `LIKE` query meant to match a literal underscore (so `name_a` matches but `namea` does not) matches too many records — the underscore keeps behaving as a wildcard even though it was escaped.

**When it occurs:** The escape (`\_` or `\%`, the two escape sequences that exist only inside `LIKE`) is written straight into the query string literal in Apex, where the Apex string parser processes the backslash before the SOQL engine sees it.

**How to avoid:** Bind the pattern as a `String` variable (`WHERE Name LIKE :searchTerm`) instead of concatenating it into the query text, so the platform handles the underscore/percent escaping rather than the Apex parser consuming it.

---

## Gotcha 7: Some Object Types Are Invisible Unless Named In `RETURNING`

**What happens:** A broad `FIND ... IN ALL FIELDS` search never surfaces files, Chatter feed items, or `Solution` records, even though matching records clearly exist and the search text is widened repeatedly.

**When it occurs:** A fixed set of object types — external objects, articles, documents, feed comments, feed items, files, products, and solutions — is excluded from SOSL results unless each is named explicitly in a `RETURNING` clause. A search that omits `RETURNING` (or omits those specific objects) silently skips them, so the missing records look like a relevance problem when they are really a scope problem.

**How to avoid:** When any of those types must appear, list them by object name in `RETURNING` (for example `RETURNING FeedItem(Id, Body), Solution(Id, SolutionName)`). Don't try to reach them by broadening the `FIND` text — only naming the object type makes it eligible.
