# Gotchas — SOQL Query Optimization

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: AND Across Two Non-Selective Filters Can Still Be Selective

**What happens:** Practitioners either assume any AND makes a query selective, or (the opposite error) assume that two filters that each miss the threshold always force a table scan. Neither is the rule. For AND, the LDV guide says the overall condition is selective when each filter targets less than twice its own threshold, or when the intersection of the filters is under the threshold.

**When it occurs:** A 1M-row object with custom indexes on `Region__c` (180,000 matches, 18%) and `Tier__c` (120,000 matches, 12%). Each misses the 100,000 custom threshold, but each is under twice the threshold (200,000), so the combined condition can be selective. Conversely, if one filter returns more than 20% of the object's rows, the optimizer stops using the indexes for that AND.

**How to avoid:** Run a `GROUP BY ROLLUP` count for each filter and for the intersection, do the arithmetic for both tests, and confirm with the query plan (`relativeCost` under 1.0). Do not request a new index until the arithmetic says the existing ones cannot be used.

---

## Gotcha 2: Non-Deterministic Formula Filters Never Use an Index

**What happens:** A report or query filters on a formula field and scans the table no matter how few rows match. A Support request for an index on that field is declined.

**When it occurs:** The formula references a field through a lookup, uses TODAY or NOW, references a multi-select picklist, a currency field in a multicurrency org, a long text area, or calls TEXT() on a picklist. The LDV guide also treats formulas over some standard fields (for example Opportunity Amount and IsClosed, Case IsClosed) as non-deterministic.

**How to avoid:** Filter on the source field directly, use cross-object notation on an indexed parent field (`Parent__r.Indexed_Field__c`), or store the value in a regular field that automation keeps current and index that field.

---

## Gotcha 3: ORDER BY Plus LIMIT Can Rescue a Last-N-Days Query; LIMIT Alone Does Not Fix a Scan

**What happens:** Two opposite mistakes. Developers add `LIMIT 200` to a query whose filter cannot use an index and expect the timeout to go away; the optimizer still has to find the matching rows. Others are told "ORDER BY always makes it worse" and miss the documented case where it helps.

**When it occurs:** The LDV guide's sort-optimization case study: `WHERE CreatedDate = LAST_N_DAYS:3` on an object too large for the CreatedDate threshold performed poorly; adding `ORDER BY CreatedDate LIMIT 99999` made the optimizer use the ORDER BY index without the threshold check. The guide's note: for Last_N_Days data, an ORDER BY on an indexed field with a limit under 100,000 records uses the ORDER BY index.

**How to avoid:** Use ORDER BY on an indexed field with a LIMIT under 100,000 only when returning at most that many rows is acceptable. For any other filter, make the filter selective first. The LDV guide lists adding a LIMIT (starting at 100,000) as the last step after tuning the filters, not the first.

---

## Gotcha 4: Recycle Bin Rows Still Sit in the Table the Query Scans

**What happens:** A filter looks selective against the live row count and is not. The LDV guide says soft-deleted data "still affects database performance because the data is still resident, and deleted records have to be excluded from any queries." The Apex guide's selectivity examples state that the record count includes soft-deleted rows still in the Recycle Bin.

**When it occurs:** After large delete jobs, data migrations that deleted and reloaded, or objects with heavy churn. Deleted items stay for 15 days before they are scheduled for hard deletion.

**How to avoid:** Count with `ALL ROWS` in Apex (or the `queryAll` REST resource) and use that total in the threshold arithmetic. For deletes of one million records or more, the LDV guide recommends the Bulk API hard delete option so rows bypass the Recycle Bin. One of its case studies fixed a slow report partly by keeping the Recycle Bin empty.

---

## Gotcha 5: Custom Indexes Reach Every Sandbox; Skinny Tables Reach Only Full Sandboxes

**What happens:** Teams test a skinny-table-dependent report in a Developer or Partial sandbox, see it run slowly, and conclude the skinny table is not working. The opposite mistake is assuming a Support-created custom index is missing from a Developer sandbox and filing a second request.

**When it occurs:** The LDV guide says custom indexes that Customer Support creates in production are copied to all sandboxes created from that production org. Skinny tables are copied to Full sandboxes only; other sandbox types need a Support request to activate them.

**How to avoid:** Test skinny-table queries in a Full sandbox. For custom indexes, a sandbox created after the index exists has it; check the plan there (`leadingOperationType` of `Index`) before raising a case.

---

## Gotcha 6: Trigger Context Is Where a Non-Selective Query Hurts Most

**What happens:** A query that is acceptable in Execute Anonymous, a batch job, or a controller fails when the same selector is reused from a trigger. The Apex guide states that SOQL queries must be selective "particularly for queries inside triggers." The failure seen in debug logs is reported as `System.QueryException: Non-selective query against large object type (more than 200000 rows)`. UNVERIFIED (2026-10-19): the exception text and the 200,000-row figure come from a Salesforce Help article that could not be fetched; neither appears in the Apex Developer Guide or LDV guide used here.

**When it occurs:** When working code is moved rather than written: a selector proven in batch is called from a new trigger handler, or an object grows past the size where its trigger query stops being selective.

**How to avoid:** Before any SOQL moves into or under a trigger, capture its plan against production row counts and require `relativeCost` under 1.0. If the filter cannot be made selective, move the work to an asynchronous path.

---

## Gotcha 7: Optimizer Statistics Are Refreshed Nightly

**What happens:** Right after a large load, delete, or mass update, a plan shows a table scan (or an index) that does not match the data now in the object. The LDV guide says the statistics-gathering process runs nightly, and that after large API changes the database must gather statistics before the application can access the data efficiently.

**When it occurs:** Cut-over weekends, archive purges, and mass ownership changes.

**How to avoid:** Re-run the plan the day after a bulk change before deciding the query needs an index. Schedule performance sign-off for after the first nightly statistics run.

---

## Gotcha 8: Negative Operators and Empty-Value Comparisons Defeat Custom Indexes

**What happens:** A query filters with `Status__c != 'Closed'` or `Name != ''` and scans the table even though the field is indexed.

**When it occurs:** The Apex guide lists the cases where a custom index typically isn't used: the value exceeds the threshold; the operator is negative (`!=`, NOT CONTAINS, NOT STARTS WITH); CONTAINS is used and more than 333,333 rows would be scanned; or the filter compares with an empty value. Its worked example `SELECT Id FROM Account WHERE Name != ''` is non-selective because it returns most rows.

**How to avoid:** Rewrite negative filters as a positive `IN` list of the values you want. The LDV guide also recommends `IN` over long OR lists and replacing nulls with a value such as `NA` when nulls must be filtered.
