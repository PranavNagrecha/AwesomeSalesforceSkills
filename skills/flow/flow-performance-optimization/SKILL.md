---
name: flow-performance-optimization
description: "Tune Flow runtime performance: pick Before-Save over After-Save, consolidate Get Records, eliminate loop-DML, cache lookups, split with Scheduled Paths, and measure actual runtime. Covers benchmarking methodology, profiling tools, and the 80/20 wins. NOT for governor-limit math — use flow/flow-governor-limits-deep-dive. NOT for LDV strategy — use flow/flow-large-data-volume-patterns."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
tags:
  - flow
  - performance
  - optimization
  - benchmarking
  - profiling
  - before-save
  - tuning
triggers:
  - "flow performance optimization"
  - "flow slow at scale"
  - "optimize flow cpu time"
  - "flow benchmark tool"
  - "flow tuning techniques"
  - "before-save vs after-save performance"
  - "flow slow tuning cpu time hoist soql dml from loop"
inputs:
  - Target flow + its entry point
  - Current runtime measurement (or target SLA)
  - Bulk volume scenario
  - Other automations on the same object
outputs:
  - Performance bottleneck analysis
  - Prioritized tuning recommendations
  - Before/after benchmark comparison
  - Risk assessment for each optimization
dependencies: []
version: 1.0.2
author: Pranav Nagrecha
updated: 2026-10-20
---

# Flow Performance Optimization

## Core concept — the performance hierarchy

Flow performance is dominated by a small set of decisions, ranked by impact:

1. **Before-Save vs After-Save** (biggest lever — 10-50× swing for field derivation).
2. **Hoisting DML and SOQL out of loops** (10-200× swing depending on loop size).
3. **Consolidating multiple Get Records into one** (2-5× swing).
4. **Caching lookup data in session variables** (2-10× swing for repeated reads).
5. **Splitting synchronous work into asynchronous paths** (removes cost from user-facing save).
6. **Reducing CPU-heavy Decision/Assignment chains** (5-20% swing, rarely the biggest lever).

Optimize in this order. Tuning (6) when (1) is still suboptimal is wasted effort. UNVERIFIED (2026-10-20): the swing multipliers above (10-50×, 10-200×, 2-5×, 2-10×, 5-20%) and the ranking itself are practitioner estimates, not corpus figures; the corpus supplies the limits they trade against (100 SOQL queries, 150 DML statements, apexdev 264 L19747, L19757) and the save order (before-save flows run at L15643, after-save flows at L15673).

## Recommended Workflow

1. **Measure first.** Don't optimize without a baseline. Fire the flow inside `Test.startTest()` and read `Limits.getCpuTime()`, `Limits.getQueries()` and `Limits.getDMLStatements()` before `Test.stopTest()`: code between the two "is assigned a new set of governor limits" and code after `stopTest` returns to the original limits (apexdev 264 L41859-41864, L41866-41867), so a delta taken across `stopTest` measures nothing.
2. **Identify the dominant cost.** SOQL count? DML count? CPU time? Heap?
3. **Apply the highest-impact lever** for that dominant cost, per the hierarchy above.
4. **Re-measure.** If the cost is still dominant, iterate; if another cost now dominates, shift focus.
5. **Stop when the flow meets SLA with 30% headroom.** Premature micro-optimization has diminishing returns.

## Questions to Ask Before Configuring

Ask these before tuning anything. Each one maps to a gotcha in `references/gotchas.md`.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "What is the current measurement, and where was it taken?" | Without a baseline you cannot tell a gain from noise, and limits restart inside `Test.startTest` (apexdev 264 L41859-41864; gotcha 1) | CPU, SOQL and DML counts read before `stopTest`, from a 200-record fixture |
| "Was that measurement taken in a sandbox?" | A sandbox figure may not hold in production (gotcha 2; UNVERIFIED in the corpus) | A re-measurement after promotion |
| "Does anything downstream need the data immediately?" | Work moved to an asynchronous path runs after commit (apexdev 264 L15682, L15692), so consumers see a delay (gotcha 3) | The consumers named and told |
| "Does the flow contain DML, callouts or cross-object updates?" | Before-save only updates the triggering record (api_meta 264 L75266-75268; gotcha 4) | The element list checked before a migration is planned |
| "How deep are the related-record lookups?" | Parent-child subqueries each count as an extra query against three times the top-level limit (apexdev 264 L19816-19818; gotcha 5) | The relationship depth and the count against that limit |
| "How many records and fields does the flow hold at once?" | Heap is 10 MB synchronous and 25 MB asynchronous (apexdev 264 L19780; gotcha 8) | Record count times fields, against the right limit |
| "What is the SLA, and how much headroom is wanted?" | Tuning stops when the target is met (Recommended Workflow step 5) | A number to stop at |

A proper configuration adds a baseline, one lever chosen on evidence, and a re-measurement, none of which "just tuning the flow" provides.

## Key patterns

### Pattern 1 — Before-Save over After-Save for field derivation

Before-Save field assignments need no Update Records element: a `RecordBeforeSave` flow makes "more updates to that record before it's saved to the database" (api_meta 264 L75266-75268). The same assignment in After-Save is an Update Records DML, and "When a process or flow executes a DML operation, the affected record goes through the save procedure" (apexdev 264 L15671) — the record is saved a second time.

Migration:
- After-Save Flow that sets `Region__c` on Account → change entry to Before-Save.
- Verify no DML elements remain (Before-Save doesn't support them).
- Expected win: UNVERIFIED (2026-10-20): the "90% reduction" is not in the corpus. The documented difference is scope: `RecordBeforeSave` makes "more updates to that record before it's saved to the database" (api_meta 264 L75266-75268) and runs before the save (apexdev 264 L15643).

### Pattern 2 — Hoist DML out of a loop

```
BEFORE:
[Loop over Cases]
  └── [Update Case.Priority = 'High']   ← 1 DML per iteration

AFTER:
[Assignment: collect Cases with new Priority into a collection]
[Loop over Cases]
  └── [Assignment: priorityCollection.add({!Case with Priority='High'})]
[Update Records (collection)]            ← 1 DML total
```

Impact: 200 iterations = 200 DML statements → 1 DML statement; the synchronous limit is 150 DML statements per transaction (apexdev 264 L19757), so the loop version fails at the 151st iteration. Often the single biggest win in a bulk-sensitive flow.

### Pattern 3 — Consolidate Get Records

```
BEFORE:
[Get Records: Contacts where AccountId = X]
[Get Records: Opportunities where AccountId = X]
[Get Records: Cases where AccountId = X]
=> 3 SOQL

AFTER (if single relation direction is acceptable):
[Get Records: Account where Id = X, with nested children Contacts, Opportunities, Cases]
=> 1 SOQL with traversal via Get-Related-Records sub-query
```

Flow Get Records can look up related records: `FlowRecordLookup` has `relatedObject` and `relatedRecords` (`FlowRelatedRecordLookup`, with `relationshipField`) (api_meta 264 L73627-73644). UNVERIFIED (2026-10-20): that this runs as one SOQL query, and the query counts in the BEFORE/AFTER sketch, are not in the corpus. If it does run as a parent-child subquery, "each parent-child relationship counts as an extra query" against a limit of three times the top-level limit (apexdev 264 L19816-19818).

### Pattern 4 — Cache repeated lookups

```
BEFORE:
[Loop over Orders]
  └── [Get Records: Shipping Rate where PostalCode = {!Order.ShipZip}]    ← SOQL per iteration

AFTER:
[Outside loop: Get Records: all Shipping Rates for the zips in the batch]
[Assignment: build Map<String, ShippingRate> by PostalCode]
[Loop over Orders]
  └── [Assignment: rate = map[Order.ShipZip]]
```

Flow doesn't have a Map primitive — `FlowVariable.dataType` lists Apex, Boolean, Currency, Date, DateTime, Number, Multipicklist, Picklist, String, sObject and Time, and no map type (api_meta 264 L75596-75621) — but you can simulate with a Collection and filter-by-equality inside the loop. Better: push the lookup to an Apex invocable that returns a bulked result (see `flow/flow-invocable-from-apex`).

### Pattern 5 — Asynchronous path for non-critical work

Flow fires on save. It does 4 things: (a) derive a field, (b) create a Task, (c) send an email, (d) call a vendor API.

- (a) stays inline (Before-Save).
- (b, c) stay inline (After-Save, cheap).
- (d) moves to an asynchronous path (async; won't block the save). The metadata value is `pathType` `AsyncAfterCommit`: "The scheduled path runs asynchronously after a save" (api_meta 264 L74148-74151); asynchronous paths in record-triggered flows are post-commit logic (apexdev 264 L15682, L15692). A scheduled path with a time offset (`offsetNumber`, `offsetUnit`, api_meta 264 L74126-74146) is a different setting. UNVERIFIED (2026-10-20): that a callout is allowed on the path, and which limits the path runs under, are not in the corpus.

Illustrative numbers, not measurements: user-perceived save time drops from 2s to 0.5s.

### Pattern 6 — Reduce wasteful sObject loading

`FlowRecordLookup.queriedFields` "specifies which fields from the selected record are saved to the specified record variable" (api_meta 264 L73623-73625), so the field list is a setting you control. UNVERIFIED (2026-10-20): that Flow's default fetches every field, and that listing fields saves heap and CPU, are not in the corpus. The heap limit itself is 10 MB synchronous and 25 MB asynchronous (apexdev 264 L19780).

## Benchmarking methodology

```apex
@IsTest
static void benchmarkFlow() {
    List<Account> accounts = createBulkFixture(200);

    Test.startTest();                       // new set of governor limits starts here
    insert accounts;                        // the flow fires inside this block
    // Read the counters BEFORE stopTest: after it the original limits are restored.
    System.debug('CPU: ' + Limits.getCpuTime() + 'ms');
    System.debug('SOQL: ' + Limits.getQueries());
    System.debug('DML: ' + Limits.getDMLStatements());
    Test.stopTest();
}
```

Run before and after each optimization; commit measurements alongside the code change.

## Bulk safety

Performance optimization and bulk safety are the same discipline. Every pattern in this skill is about scaling gracefully; every skipped optimization is a future limit exception.

## Error handling

Optimization sometimes changes error surface:
- Moving work to an asynchronous path means it runs after the changes are committed (apexdev 264 L15682, L15692), so its errors no longer roll back the user's save. UNVERIFIED (2026-10-20): that they surface as log records is not in the corpus.
- Consolidating Get Records into one means a single null-result affects downstream logic; handle with Decision elements.

Test both success and fault paths after every optimization.

## Well-Architected mapping

- **Performance** — the whole skill is about performance. Each pattern addresses one of the six highest-impact levers.
- **Reliability** — a performant flow survives load spikes. An un-tuned flow works in test, breaks on the first busy day.

## Gotchas

See `references/gotchas.md`.

## Testing

Every optimization should ship with a benchmark delta in the PR description (illustrative figures):

```
Before: 200-record insert = 3200ms CPU, 15 SOQL, 8 DML
After:  200-record insert = 1100ms CPU, 4 SOQL, 2 DML
Reduction: 66% CPU, 73% SOQL, 75% DML
```

## Official Sources Used

- Salesforce Developer — Flow Performance Optimization: https://developer.salesforce.com/blogs/2022/07/flow-performance-optimization
- Salesforce Help — Flow Limits and Considerations: https://help.salesforce.com/s/articleView?id=sf.flow_considerations_limit.htm
- Salesforce Help — Before-Save vs After-Save Flows: https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger.htm
- Salesforce Architects — Performance Engineering: https://architect.salesforce.com/
