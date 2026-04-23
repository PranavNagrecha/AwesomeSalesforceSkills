# Gotchas — Get Records

## 1. "Automatically Store All Fields" Is A Trap

Flow retrieves every field even if you only use 2. Heap and view-state
costs matter on larger objects.

## 2. No Limit = 50,000 Default

Flow will gladly try to fetch up to the 50k SOQL row limit. Always set
a lower explicit cap.

## 3. Loops Don't Get Free SOQL

Every Get Records call inside a loop is a separate SOQL. 200 iterations
= 200 queries, not one.

## 4. LIKE With Leading Wildcard Skips Indexes

`Name LIKE '%foo%'` does a full scan. `Name LIKE 'foo%'` can use
index. If you need contains, use SOSL or a pre-computed external field.

## 5. Cross-Object Filter Performance

Filtering a child on parent field via `Account.Industry` may not use
the expected index. Often cheaper to query the parent first and carry
the IDs forward.

## 6. Collection Variable Not Shared Across Async Paused Waits

After a Pause, the paused interview is stored and resumed later. The
collection is serialised; large collections inflate storage and slow
resume. Trim before pause.

## 7. Sort On Non-Indexed Field With Large Result

Sort happens after filter. If the filter returns 50k rows and you sort
on an unindexed Text field, Flow materialises and sorts all 50k — even
with limit 10.

## 8. Record-Triggered Flow Doesn't Auto-Query Related

`{!$Record.Account}` on a Case flow looks automatic but is in-memory
only for fields loaded at trigger time. Deeper related lookups need an
explicit Get Records.
