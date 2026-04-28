---
name: flow-get-records-optimization
description: "Optimize Get Records elements in Flow: filter sharpness, field selection, sort-and-limit placement, caching via formula resources, and avoiding repeated queries in loops. Trigger keywords: get records, flow soql, flow query limit, flow performance, record lookup. Does NOT cover Apex SOQL, Data Cloud queries, or external object lookups."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# Flow Get Records Optimization

## Performance Symptoms

- A Flow hits the 100-SOQL governor limit or times out.
- Get Records inside a Loop.
- Screen Flow with multiple lookups feeling sluggish.
- Large-collection filter returning tens of thousands of records when
  only a few are needed.

## Out of Scope

- One-record, one-lookup flows. Leave them alone.
- Platform event triggers where SOQL is not the bottleneck.

## The Rules

1. **Never Get Records inside a Loop.** Move the Get Records above the
   loop; filter by a collection of IDs built from the loop source.
2. **Always set a limit.** For single-record lookups, limit 1. For
   collections, set an explicit upper bound; don't rely on the 50k
   default.
3. **Specify fields.** Leaving "All fields" on a Get Records on a big
   object costs heap and view-state. Pick only the fields the flow
   reads.
4. **Index-backed filters.** The first filter on the query should be
   an indexed field (ID, owner, external ID, standard indexed field).
   Add custom indexes where needed.
5. **Sort + limit for "top N".** Use Sort + Limit inside the Get
   Records, not "Get all, then a Decision to pick the top."
6. **Reuse collections across the flow.** A single Get Records at the
   start feeding multiple downstream elements beats repeated queries.

## Recommended Workflow

1. List every Get Records in the flow.
2. For each: note filter fields, field selection, sort/limit,
   whether it lives in a loop.
3. Fix loops first: pull the query above the loop, filter by the
   collection.
4. Add or tighten filters; make the first filter field indexed.
5. Trim the field list to what downstream elements reference.
6. Add explicit limits. Single: 1. Collection: meaningful upper bound.
7. Re-run the flow debug log; confirm SOQL count < 10 per transaction
   as a sane target.

## Official Sources Used

- Get Records —
  https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_data_get.htm
- Flow Limits —
  https://help.salesforce.com/s/articleView?id=sf.flow_considerations_limits.htm
- Query & Search Optimization —
  https://developer.salesforce.com/docs/atlas.en-us.salesforce_large_data_volumes_bp.meta/salesforce_large_data_volumes_bp/ldv_deployments_techniques_speeding_up_soql_search.htm
