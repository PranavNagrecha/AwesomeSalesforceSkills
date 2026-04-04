# Gotchas — Custom Iterators and Iterables

Non-obvious Salesforce platform behaviors that cause real production problems when using custom `Iterator<T>` and `Iterable<T>` in Apex.

## Gotcha 1: Custom Iterable in start() Does NOT Bypass the 50,000 Query Rows Limit

**What happens:** When `Database.Batchable.start()` returns an `Iterable<SObject>` and the iterator fetches records via SOQL inside `hasNext()` or `next()`, every row returned by those SOQL calls accumulates against the standard 50,000-query-rows-returned-per-transaction governor limit in the `start()` execution context. The job throws `System.LimitException: Too many query rows: 50001` if enumeration crosses that threshold — even though the job is asynchronous.

**When it occurs:** Any time the custom iterable's lazy SOQL pagination returns more than 50,000 total rows across all page fetches during `start()` execution. This is most common when developers assume that async batch context removes this limit, because `Database.getQueryLocator()` is exempt from it (QueryLocator uses a server-side cursor, not per-transaction SOQL rows).

**How to avoid:** Use `Database.getQueryLocator()` for any single-SOQL data source that may exceed 50,000 rows. Reserve custom iterables for sources where the total count is controlled and known to stay within the limit (e.g., pre-computed ID sets, small cross-object aggregations). If the source is SOQL-queryable and large, QueryLocator is the correct choice.

---

## Gotcha 2: for-each Loop Requires Iterable<T>, Not Iterator<T>

**What happens:** Apex for-each syntax (`for (SObject o : source)`) requires `source` to implement `Iterable<T>`. A class that implements only `Iterator<T>` (with `hasNext()` and `next()`) cannot be used as the target of a for-each loop directly. Attempting to do so produces a compile error: `For loop variable must implement java.lang.Iterable`.

**When it occurs:** A developer writes a custom `Iterator<SObject>` class intending to use it in a for-each loop and finds the Batch `start()` method can return `Iterable<SObject>`, so they add `Iterable<SObject>` to the iterator class and implement `iterator()` by returning `this`. This works once but breaks on the second iteration because `iterator()` returns the already-advanced cursor rather than a fresh one.

**How to avoid:** Always separate the `Iterable<T>` wrapper (factory) from the `Iterator<T>` cursor (stateful). The `Iterable.iterator()` method must return `new MyIterator(...)`, not `this`. For simple cases, `List<T>` already implements `Iterable<T>` — use the built-in `List.iterator()` rather than rolling a custom class.

---

## Gotcha 3: OFFSET-Based Pagination Degrades Severely Past ~2,000 Records

**What happens:** SOQL `OFFSET` is implemented by scanning and discarding rows up to the offset value before returning results. A custom iterator that re-queries with increasing `OFFSET` values will spend progressively more CPU and DML time on each page. By page 10 at 200 records per page (offset 2,000), query time has measurably degraded. At offset 10,000, each query scan is expensive and risks CPU time limit violations.

**When it occurs:** Developers implement lazy pagination using `LIMIT n OFFSET :currentOffset` inside `hasNext()`. This looks correct and works for small datasets but silently degrades and eventually fails for large ones.

**How to avoid:** Use keyset pagination: track the last-seen `Id` (or a monotone indexed field) and use `WHERE Id > :lastSeenId ORDER BY Id LIMIT :pageSize`. This converts each page query from a full-table scan with skip to an index seek on the primary key, which remains O(1) regardless of how far through the set you are. Keyset pagination requires `ORDER BY Id` and that records are not deleted between pages (or that you handle gaps gracefully).

---

## Gotcha 4: Shared Mutable State When iterator() Returns this

**What happens:** If an `Iterable` class stores cursor position as instance variables and `iterator()` returns `this`, any two callers sharing the same `Iterable` instance see a shared cursor. The second caller starts mid-stream. In Batch Apex this is unlikely (the framework holds one instance), but in test code or when the same iterable is reused across multiple for-each loops, the second loop sees no elements because the cursor is at the end from the first traversal.

**When it occurs:** A developer writes `public Iterator<SObject> iterator() { return this; }` on their combined `Iterable + Iterator` class to reduce boilerplate.

**How to avoid:** `iterator()` must always return a freshly constructed cursor object. Treat the `Iterable` as a stateless factory and the `Iterator` as a stateful cursor.

---

## Gotcha 5: NoSuchElementException Is Not Caught by the Batch Framework

**What happens:** If `next()` is called when `hasNext()` would return `false` — because the caller forgot to check, or because a race in stateful logic advanced the index incorrectly — the platform throws `NoSuchElementException`. This exception is uncaught and fails the entire batch job, not just the current scope slice.

**When it occurs:** Iterator logic that calls `hasNext()` once but then calls `next()` multiple times before calling `hasNext()` again (e.g., inside a custom page-filling loop that over-fetches). Also occurs when an iterator is used outside of Batch — in a for loop with manual cursor management.

**How to avoid:** Always call `hasNext()` immediately before each call to `next()`. Do not cache the result of `hasNext()` across multiple `next()` calls. Implement a defensive guard at the top of `next()` that throws `NoSuchElementException` with a meaningful message when `hasNext()` would return `false`, so the failure location is clear in debug logs.
