# Gotchas — Flow Performance Optimization

## Gotcha 1: Tuning without measuring

Without a baseline, you can't distinguish real improvements from noise. Always benchmark before + after.

---

## Gotcha 2: Sandbox perf ≠ production perf

Sandboxes run on shared infrastructure with different load characteristics. A tuning that looks good in sandbox may behave differently in prod. Re-measure after promotion.

---

## Gotcha 3: Scheduled Path introduces 1-5min latency

Moving work async is a performance win for user-perceived save time, but downstream systems that expect immediate data see delay. Coordinate with consumers.

---

## Gotcha 4: Before-Save doesn't allow DML or callouts

Migrating an After-Save to Before-Save to save the DML cost fails if the flow has DML elements. Check element support before planning the move.

---

## Gotcha 5: Get-Related-Records subquery depth

Querying related records via child relationships has a subquery count limit. Deep nesting (Contact → Opportunities → Products) may hit the subquery limit.

---

## Gotcha 6: Loop over a filtered collection still walks the filter

Flow's Loop with a Filter expression evaluates the filter once per iteration. If the filter is expensive, pre-filter into a smaller collection.

---

## Gotcha 7: Formula evaluation inside Assignments is not free

Complex formulas in Assignments are computed each time the Assignment runs. Pre-compute once outside the loop.

---

## Gotcha 8: Heap can grow faster than expected

Loading 10,000 records × 30 fields each can spike heap to 5+ MB. Synchronous limit is 6 MB. Reduce fields selected or process in chunks.
