---
name: flow-get-records-optimization
description: "Optimize Get Records in Flow — filters, field selection, sort/limit, caching, avoiding queries in loops. Triggers: get records, flow SOQL, flow query limit. NOT for Apex SOQL tuning — use flow/flow-governor-limits-deep-dive. NOT for loop bulkification failures — use flow/flow-bulkification."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
triggers:
  - get records optimization
  - flow soql limit
  - flow query in loop
  - flow performance
tags:
  - flow
  - get-records
  - soql
  - performance
  - governor-limits
inputs:
  - Existing Get Records elements with slow or limit-hitting behaviour
  - Proposed Flow design using record lookups
outputs:
  - Refactored Get Records with tight filters, specific fields, limit
  - Extraction to collection reuse / sub-flow input where possible
dependencies:
  - flow/flow-governor-limits-deep-dive
  - flow/flow-performance-optimization
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# Flow Get Records Optimization

## Performance Symptoms

- A Flow hits the per-transaction SOQL governor limit (100 synchronous, 200
  asynchronous) or times out.
- Get Records inside a Loop.
- Screen Flow with multiple lookups feeling sluggish.
- Large-collection filter returning tens of thousands of records when
  only a few are needed.

## Out of Scope

- One-record, one-lookup flows. Leave them alone.
- Platform event triggers where SOQL is not the bottleneck.

## The Budget You Are Spending

Per **transaction**, not per element and not per interview:

| Governor | Synchronous | Asynchronous |
|---|---|---|
| SOQL queries | 100 | 200 |
| SOQL query rows | 50,000 | 50,000 |
| CPU time | 10,000 ms | 60,000 ms |
| Heap | 6 MB | 12 MB |

Record-triggered and schedule-triggered flows run one interview per record, and
the platform batches those interviews — up to 200 — into a single transaction
sharing one budget. **The number that matters is `per-interview cost × batch
size`**, so one Get Records in the per-record path is 200 queries at a full
batch. Almost every "my flow works in testing and fails in production" report in
this domain is that multiplication.

**Which column applies is not a detail.** A record-triggered flow runs inside the
triggering transaction and gets the synchronous column — 200 queries against 100,
which fails. A **schedule-triggered** flow runs under the asynchronous column from
runtime version 61.0 onward, per the *Improve Scheduled Flow Performance with
Updated Limits* release update — so the same 200 queries fit against 200, exactly,
with nothing left over for the Apex triggers and other flows sharing the
transaction. Establish the flow type and its runtime version before you do the
arithmetic; a scheduled flow costed against 100 gets rewritten in Apex for no
reason. Note also that DML statements are 150 in **both** columns, so the DML side
of the multiplication is often what actually breaches.

## The Rules

1. **Never Get Records inside a Loop.** Collect Ids in an Assignment, run one
   Get Records with an `In` filter after the loop, match in a second loop. Flow
   has no map, so the match is O(n×m) CPU and zero extra queries — the right
   trade given SOQL is budgeted at 100 (200 asynchronous) and CPU at 10,000 ms
   (60,000 asynchronous). Queries are the scarcer resource in both columns.
2. **Make the filter selective, and check rather than guess.** Selectivity is
   measured in absolute rows: a standard index is selective below 30% of the
   first million targeted records and 15% beyond, capping at 1,000,000; a custom
   index below 10% / 5%, capping at 333,333. A filter matching 500,000 rows
   cannot be made selective by indexing it. Verify in Developer Console → Query
   Plan; a Cost above 1 means a full table scan.
3. **Know which fields are actually indexed.** The standard-indexed set is `Id`,
   `Name`, `OwnerId`, `CreatedById`, `LastModifiedById`, lookup and master-detail
   relationship fields, `CreatedDate`, and `SystemModstamp`. Custom fields marked
   Unique or External Id get a custom index. Nothing else is indexed by default —
   "standard field" and "standard index" are different things.
4. **Specify fields on large collections, not on every lookup.** Heap is 6 MB
   synchronous and a screen flow re-serializes variables between screens, so a
   named field list is a real saving on a wide object. It is also brittle: a field
   added downstream and forgotten in the query returns null rather than erroring.
   Accept automatic storage on single-record lookups.
5. **Push sort and limit into the query for "top N",** and remember the limit
   bounds what is returned, not what the optimizer must consider. A limit does
   not rescue a non-selective filter.
6. **Cache what cannot change; re-query what can.** The running user's manager
   and a Custom Metadata row are safe to hold across screens. Record ownership
   and status are not — and a paused interview makes staleness a matter of days.

## Recommended Workflow

1. **Compute `per-interview cost × batch size` first — against the right column.**
   Record-triggered flows are costed against 100 SOQL, schedule-triggered flows on
   runtime version 61.0+ against 200. If that number is comfortably under the
   limit, the flow is not the consumer — inventory the object's other automation
   and read the debug log's cumulative limits section.
2. **Fix loops.** Any Get Records reachable from inside a Loop is the first and
   usually only real problem.
3. **Test each filter for selectivity** in the Query Plan tool, not by
   inspection. Lead with something genuinely narrow and let the rest reduce the
   small result.
4. **Replace `Contains` filters** with `StartsWith`, SOSL, or a pre-computed
   normalized field. A leading wildcard cannot use an index.
5. **Trim field lists on large collections**, and trim collections before any
   Pause element.
6. **Handle not-found with a Decision**, with `assignNullValuesIfNoRecordsFound`
   set to `true`. Zero rows is a successful query and will never take a fault
   path.
7. **Re-measure.** Confirm the SOQL count against the same multiplication you
   started with, in a debug log from a realistic batch.

## Official Sources Used

- Get Records Element — https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_data_get.htm&type=5
- Per-Transaction Apex Governor Limits — the synchronous/asynchronous columns this skill costs against — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Improve Scheduled Flow Performance with Updated Limits (Summer '24 release update; schedule-triggered flows move to asynchronous limits at runtime version 61.0) — https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow_release_update_improve_scheduled_flow_performance_with_updated_limitsxml.htm&release=250&type=5
- Maximizing the Performance of Force.com SOQL, Reports, and List Views — selectivity thresholds and the standard-indexed field list — https://developer.salesforce.com/blogs/engineering/2013/07/maximizing-the-performance-of-force-com-soql-reports-and-list-views
- Developer Console Query Plan Tool FAQ — https://help.salesforce.com/s/articleView?id=000386864&type=1
- Best Practices for Deployments with Large Data Volumes — https://developer.salesforce.com/docs/atlas.en-us.salesforce_large_data_volumes_bp.meta/salesforce_large_data_volumes_bp/

The full annotated list is in `references/well-architected.md`.
