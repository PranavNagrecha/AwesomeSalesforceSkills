# Examples — Flow Large Data Volume Patterns

## Example 1: Production failure from one wide `Get Records`

**Context:** A record-triggered after-save Flow on `Account` loads “all” open `Case` rows for that account to compute a rollup-style field on the account. In the sandbox, test accounts have fewer than twenty cases.

**Problem:** After go-live, several accounts accumulate tens of thousands of historical cases. The flow interview returns `Too many query rows: 50001` (or similar query-rows messaging) during a bulk account update, even though the flow only has a small number of elements.

**Solution:**

1. Replace unbounded “all cases” retrieval with a **selective** query: only statuses or date ranges the business truly needs, and only fields used later.
2. If the business rule is “count” or “sum,” move aggregation to a roll-up summary field, report, or Apex/Async that can chunk work.
3. Where product behavior allows, use **explicit row caps** and **sort** so the flow retrieves a deterministic slice (for example latest 500 by `LastModifiedDate`) instead of the entire history.

**Why it works:** The failure mode is total **rows returned** in the transaction, not element count. Narrowing the query reduces returned rows below the platform ceiling and keeps behavior stable as data grows.

---

## Example 2: Several “small” queries that add up

**Context:** An autolaunched Flow performs five separate `Get Records` elements against different custom objects, each filtered and returning up to 10,000 rows for reconciliation logic.

**Problem:** No single query exceeds the limit, but the **sum** of rows returned in the same interview approaches or exceeds the transaction query-rows limit under peak loads.

**Solution:**

1. Build a row-budget table for the interview: list each `Get Records`, realistic max rows, running total.
2. Merge queries where possible (single query with sub-selects is not available in Flow the same way as SOQL in Apex, so prefer **fewer** retrievals, tighter filters, or moving merge logic to Apex with one query).
3. Drop unused fields from each retrieval to reduce heap and cost per row.

**Why it works:** Governor behavior is cumulative across the transaction. LDV design must account for **aggregate** row retrieval, not each element in isolation.

---

## Anti-Pattern: Treating scheduled Flow as a batch ETL over millions of rows

**What practitioners do:** They schedule a Flow that queries every `OrderLine__c` for the month with `Get Records` set to return all matches, then loop to callout or update each row.

**What goes wrong:** Even if the scheduled path runs once per night, the interview still executes under Flow and transaction limits. Large result sets hit query-row and heap ceilings, time out, or fail partially without an idempotent chunking strategy.

**Correct approach:** Use Flow to **kick off** bounded work (for example a Platform Event or invocable Apex that processes chunks), or move the bulk processing to Batch Apex or an external integration designed for volume.
