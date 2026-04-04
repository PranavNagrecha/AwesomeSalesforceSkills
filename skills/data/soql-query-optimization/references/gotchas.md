# Gotchas — SOQL Query Optimization

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The 10% Selectivity Threshold Applies Per Field, Not to the Combined WHERE Clause

**What happens:** Practitioners assume that combining two WHERE clause filters with AND makes the query selective. In reality, the optimizer evaluates each filter independently against its own threshold before deciding whether to use an index for that filter. Two individually non-selective filters joined by AND do not automatically produce a selective query.

**When it occurs:** When a developer adds a second custom field filter to a slow query hoping it will narrow the result set sufficiently. For example, filtering on `Region__c = 'West'` (returns 18% of records) AND `Tier__c = 'Gold'` (returns 12% of records). Each is above the 10%/333,333 custom index threshold, so neither index is used — the query still scans the full table.

**How to avoid:** Always check selectivity for each filter field individually using a GROUP BY aggregate query. If either individual filter exceeds the threshold, restructure the query to introduce a more selective filter (such as RecordTypeId or a date range), or request a two-column composite index if the combined filter is selective together.

---

## Gotcha 2: Custom Indexes Do Not Help Queries with Leading LIKE Wildcards

**What happens:** A custom index exists on a field, but queries using `LIKE '%value%'` or `LIKE '%value'` still produce full-table scans. The index is completely bypassed.

**When it occurs:** Any `LIKE` pattern where the wildcard appears at the start of the search string (`LIKE '%term'` or `LIKE '%term%'`) prevents index usage. This is a fundamental database-level limitation — an index is structured as an ordered prefix tree; a leading wildcard means the optimizer cannot use the tree prefix to narrow the search.

**How to avoid:** There is no workaround within SOQL. Options:
- If full-text search is needed, switch to SOSL (`FIND :term IN ALL FIELDS RETURNING Object__c(Id, Name)`).
- If trailing wildcard is acceptable (`LIKE 'value%'`), Salesforce can use the index on that pattern.
- If the search term is known and fixed, use an exact equality filter (`= 'value'`) instead of LIKE.

---

## Gotcha 3: Adding ORDER BY to a Non-Selective Query Increases Cost, Not Reduces It

**What happens:** Developers add `ORDER BY CreatedDate DESC` to a slow query, expecting it to help by using the CreatedDate index. Instead, the query becomes even more expensive. The cost in Query Plan increases.

**When it occurs:** When ORDER BY is applied to a query that already lacks a selective WHERE clause filter. ORDER BY is evaluated after the initial data access phase. If the optimizer is already scanning the full table to satisfy WHERE, it then has to sort those millions of records — adding I/O and memory pressure on top of the scan.

**How to avoid:** Always make the query selective (cost < 1.0 in Query Plan) before adding ORDER BY. If you need both filtering and sorting, consider a two-column composite custom index on (filter_field, sort_field), which allows the optimizer to use the index for both operations in a single pass.

---

## Gotcha 4: Soft-Deleted Records Inflate Selectivity Calculations

**What happens:** A query that appears selective based on active record counts is actually non-selective because soft-deleted records (records in the recycle bin) count toward the total record count used in selectivity threshold calculations. An index that would be selective on 1M live records may not be used if there are an additional 500K soft-deleted records inflating the total to 1.5M.

**When it occurs:** Orgs with aggressive delete workflows, data migration projects that deleted large batches of records, or objects where records are soft-deleted and not permanently purged for 15 days.

**How to avoid:** When calculating selectivity, use `SELECT COUNT() FROM Object__c WHERE IsDeleted = false ALL ROWS` to get the live count, and `SELECT COUNT() FROM Object__c ALL ROWS` to see the true total including soft-deleted records. Use the full total (including deleted) as the denominator when evaluating selectivity.

---

## Gotcha 5: Custom Indexes Are Not Propagated to Most Sandbox Types

**What happens:** A custom index is requested via Salesforce Support and confirmed active in production. Performance testing in a Developer or Partial sandbox shows the same query is still slow, leading teams to doubt whether the index is working.

**When it occurs:** Custom indexes created by Salesforce Support in production are automatically copied only to Full sandboxes. Developer sandboxes, Developer Pro sandboxes, and Partial sandboxes do not receive custom indexes from production.

**How to avoid:** Use Query Plan in production (read-only diagnostic, no records touched) rather than sandbox for index validation. If sandbox testing is required, request that Salesforce Support manually create the same index in the specific sandbox, or use a Full sandbox for performance testing.
