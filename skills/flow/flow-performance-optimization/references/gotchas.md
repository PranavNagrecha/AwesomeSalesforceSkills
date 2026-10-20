# Gotchas — Flow Performance Optimization

## Gotcha 1: Tuning without measuring

Without a baseline, you can't distinguish real improvements from noise. Always benchmark before + after, and read the `Limits` counters inside the `Test.startTest()` / `Test.stopTest()` block: code after `stopTest` "is assigned the original limits that were in effect before startTest" (apexdev 264 L41866-41867).

---

## Gotcha 2: Sandbox perf ≠ production perf

Sandboxes run on shared infrastructure with different load characteristics. A tuning that looks good in sandbox may behave differently in prod. Re-measure after promotion. UNVERIFIED (2026-10-20): the sandbox-versus-production difference is not described in the corpus.

---

## Gotcha 3: Asynchronous paths run after commit, so consumers see a delay

Moving work to an asynchronous path is a performance win for user-perceived save time: it is post-commit logic (apexdev 264 L15682, L15692). Downstream systems that expect immediate data see a delay. UNVERIFIED (2026-10-20): the "1-5 min" latency figure the earlier heading carried is not in the corpus. Coordinate with consumers.

---

## Gotcha 4: Before-Save only updates the triggering record

`RecordBeforeSave` is for "more updates to that record before it's saved to the database" (api_meta 264 L75266-75268). Migrating an After-Save flow to Before-Save fails if the flow works on other records. Check element support before planning the move. UNVERIFIED (2026-10-20): that Before-Save rejects DML and callout elements by name is not in the corpus.

---

## Gotcha 5: Get-Related-Records subquery depth

"In a SOQL query with parent-child relationship subqueries, each parent-child relationship counts as an extra query. These types of queries have a limit of three times the number for top-level queries" (apexdev 264 L19816-19818). Querying related records through `relatedRecords` (api_meta 264 L73630) may count against it. UNVERIFIED (2026-10-20): the Contact → Opportunities → Products nesting example and whether Flow issues a subquery for a related-records lookup are not in the corpus.

---

## Gotcha 6: Loop over a filtered collection still walks the filter

Flow's Loop with a Filter expression evaluates the filter once per iteration. If the filter is expensive, pre-filter into a smaller collection. UNVERIFIED (2026-10-20): the per-iteration evaluation is not described in the corpus.

---

## Gotcha 7: Formula evaluation inside Assignments is not free

Complex formulas in Assignments are computed each time the Assignment runs. Pre-compute once outside the loop. UNVERIFIED (2026-10-20): the evaluation cost of an Assignment formula is not described in the corpus.

---

## Gotcha 8: Heap can grow faster than expected

Loading 10,000 records × 30 fields each can grow heap. The limit is 10 MB synchronous and 25 MB asynchronous (apexdev 264 L19780); the earlier text said 6 MB, which the Winter '27 table replaces. Reduce fields selected or process in chunks. UNVERIFIED (2026-10-20): the "5+ MB" size of that example and whether this table governs a flow's own heap are not in the corpus.
