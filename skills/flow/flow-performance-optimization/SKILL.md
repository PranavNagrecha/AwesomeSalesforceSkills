---
name: flow-performance-optimization
description: "Tune Flow runtime performance: pick Before-Save over After-Save, consolidate Get Records, eliminate loop-DML, cache lookups, split with Scheduled Paths, and measure actual runtime. Covers benchmarking methodology, profiling tools, and the 80/20 wins. NOT for governor-limit math (use flow-governor-limits-deep-dive). NOT for LDV strategy (use flow-large-data-volume-patterns)."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Flow Performance Optimization

## When to use this skill

Activate when:

- A specific flow is reported as slow or causing UI lag.
- You're pre-validating a flow before deploying to a high-volume org.
- A record save that used to take 1 second now takes 5 seconds; you need to attribute which flow is responsible.
- You're choosing between two flow designs and want the cheaper one at scale.

Do NOT use this skill for:
- Governor-limit budgeting math (use `skills/flow/flow-governor-limits-deep-dive`).
- Large-data-volume strategy (use `skills/flow/flow-large-data-volume-patterns`).
- General flow architecture decisions (use `standards/decision-trees/flow-pattern-selector.md`).

## Core concept — the performance hierarchy

Flow performance is dominated by a small set of decisions, ranked by impact:

1. **Before-Save vs After-Save** (biggest lever — 10-50× swing for field derivation).
2. **Hoisting DML and SOQL out of loops** (10-200× swing depending on loop size).
3. **Consolidating multiple Get Records into one** (2-5× swing).
4. **Caching lookup data in session variables** (2-10× swing for repeated reads).
5. **Splitting synchronous work into Scheduled Paths** (removes cost from user-facing save).
6. **Reducing CPU-heavy Decision/Assignment chains** (5-20% swing, rarely the biggest lever).

Optimize in this order. Tuning (6) when (1) is still suboptimal is wasted effort.

## Recommended Workflow

1. **Measure first.** Don't optimize without a baseline. Use Test.startTest/stopTest in Apex to capture `Limits.getCpuTime()` before and after the flow fires.
2. **Identify the dominant cost.** SOQL count? DML count? CPU time? Heap?
3. **Apply the highest-impact lever** for that dominant cost, per the hierarchy above.
4. **Re-measure.** If the cost is still dominant, iterate; if another cost now dominates, shift focus.
5. **Stop when the flow meets SLA with 30% headroom.** Premature micro-optimization has diminishing returns.

## Key patterns

### Pattern 1 — Before-Save over After-Save for field derivation

Before-Save field assignments cost zero extra DML. The same assignment in After-Save causes the record to be written twice (once for the user's save, once for the flow's update).

Migration:
- After-Save Flow that sets `Region__c` on Account → change entry to Before-Save.
- Verify no DML elements remain (Before-Save doesn't support them).
- Expected win: 90% reduction in flow cost.

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

Impact: 200 iterations = 200 DML statements → 1 DML statement. Often the single biggest win in a bulk-sensitive flow.

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

Flow Get Records supports querying related records in one go via the child relationship picker. Use it.

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

Flow doesn't have a Map primitive, but you can simulate with a Collection and filter-by-equality inside the loop. Better: push the lookup to an Apex invocable that returns a bulked result.

### Pattern 5 — Scheduled Path for non-critical work

Flow fires on save. It does 4 things: (a) derive a field, (b) create a Task, (c) send an email, (d) call a vendor API.

- (a) stays inline (Before-Save).
- (b, c) stay inline (After-Save, cheap).
- (d) moves to Scheduled Path +0 (async; callout allowed; won't block the save).

User-perceived save time drops from 2s to 0.5s.

### Pattern 6 — Reduce wasteful sObject loading

A Get Records element that selects `SELECT *` equivalent returns all fields. Flow's default is to fetch every field. Tune by explicitly listing the fields needed — both for heap and CPU savings.

## Benchmarking methodology

```apex
@IsTest
static void benchmarkFlow() {
    List<Account> accounts = createBulkFixture(200);

    Long start = Limits.getCpuTime();
    Integer startSoql = Limits.getQueries();
    Integer startDml = Limits.getDMLStatements();

    Test.startTest();
    insert accounts;
    Test.stopTest();

    System.debug('CPU: ' + (Limits.getCpuTime() - start) + 'ms');
    System.debug('SOQL: ' + (Limits.getQueries() - startSoql));
    System.debug('DML: ' + (Limits.getDMLStatements() - startDml));
}
```

Run before and after each optimization; commit measurements alongside the code change.

## Bulk safety

Performance optimization and bulk safety are the same discipline. Every pattern in this skill is about scaling gracefully; every skipped optimization is a future limit exception.

## Error handling

Optimization sometimes changes error surface:
- Moving work to a Scheduled Path means errors no longer roll back the user's save — they become log records instead.
- Consolidating Get Records into one means a single null-result affects downstream logic; handle with Decision elements.

Test both success and fault paths after every optimization.

## Well-Architected mapping

- **Performance** — the whole skill is about performance. Each pattern addresses one of the six highest-impact levers.
- **Reliability** — a performant flow survives load spikes. An un-tuned flow works in test, breaks on the first busy day.

## Gotchas

See `references/gotchas.md`.

## Testing

Every optimization should ship with a benchmark delta in the PR description:

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
