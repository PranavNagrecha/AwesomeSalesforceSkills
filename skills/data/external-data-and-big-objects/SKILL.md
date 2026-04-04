---
name: external-data-and-big-objects
description: "Use this skill when storing large historical datasets in Salesforce using Big Objects, querying them with Async SOQL, or deciding between Big Objects and External Objects for high-volume or external data access patterns. Trigger keywords: big object, async SOQL, AsyncQueryJob, external object, Salesforce Connect, IoT data, audit history, event log archival, Database.insertImmediate, composite index. NOT for Salesforce Connect adapter configuration or OAuth setup (use salesforce-connect-external-objects), and NOT for standard data archival strategies (use data-archival-strategies)."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Scalability
  - Reliability
triggers:
  - "We need to store millions of audit log records in Salesforce without hitting data storage limits"
  - "How do I query a Big Object — regular SOQL returns no results or errors"
  - "Should I use a Big Object or an External Object to access high-volume historical data"
  - "Database.insertImmediate is failing silently and I cannot tell why"
  - "Async SOQL job is submitted but records never appear in the target object"
tags:
  - big-objects
  - async-soql
  - external-objects
  - large-data-volumes
  - archival
  - composite-index
inputs:
  - "Volume and growth rate of the dataset to be stored or accessed"
  - "Query patterns: which fields are filtered, sorted, or aggregated"
  - "Latency tolerance: real-time lookup vs batch/async acceptable"
  - "Whether data lives in Salesforce or in an external system"
  - "Existing Salesforce storage headroom and budget constraints"
outputs:
  - "Big Object metadata design with valid composite index definition"
  - "Async SOQL job template using AsyncQueryJob API"
  - "Decision matrix entry: Big Object vs External Object vs standard object"
  - "Apex insert pattern using Database.insertImmediate"
  - "Review checklist confirming index coverage and Async SOQL job configuration"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# External Data and Big Objects

This skill activates when a practitioner needs to store, retrieve, or decide the placement of extremely large or historical datasets in a Salesforce org. It covers the two main platform mechanisms for high-volume data: **Big Objects** (on-platform storage tier with Async SOQL) and **External Objects** (virtual, real-time access via Salesforce Connect). Use this skill to design composite indexes, author Async SOQL jobs, choose between the two mechanisms, and avoid the platform-specific failure modes that trip up every team the first time.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Volume and query patterns**: Big Objects are only queryable via composite index fields. If you do not know which fields will be filtered, you cannot design the index — and an unusable index means an unqueryable Big Object.
- **Common wrong assumption**: Practitioners assume they can write a standard SOQL query against a Big Object. Standard SOQL does not work on Big Objects; Async SOQL (via the `AsyncQueryJob` REST API) is the only scalable query mechanism.
- **Storage vs API limits**: External Objects count against SOQL query limits on every read because each query results in a live callout to the external system. Big Objects do not make callouts but consume Salesforce data storage. This distinction drives the core decision.

---

## Core Concepts

### Big Objects

Big Objects are a dedicated Salesforce storage tier designed for datasets in the hundreds of millions to billions of records. They are defined as custom metadata objects with the suffix `__b` and are inserted via `Database.insertImmediate()` (synchronous, fire-and-forget) or the Bulk API v1/v2.

Big Objects require a **composite index**: a mandatory, ordered list of fields that defines both the uniqueness constraint and the queryable access path. Every field used in a WHERE clause of an Async SOQL query must appear in the composite index in the same left-to-right order the query filters apply. Omitting a field from the index, or querying in a non-leading-column order, produces zero results with no error.

**Platform limitations of Big Objects:**
- No triggers (before/after insert/update/delete are not supported)
- No standard reports or list views
- No roll-up summary fields pointing at Big Object records
- No SOSL (Salesforce Object Search Language) support
- Standard SOQL returns results only for very small datasets; for production volumes always use Async SOQL

### Async SOQL

Async SOQL is a REST-based API (`/services/data/vXX.0/async-queries/`) that submits a query as a background job and writes results to a target object (standard, custom, or Big Object). It is the only reliable way to query Big Objects at production scale.

Key facts:
- Jobs are submitted via POST with a `query` body and a `targetObject` specifying where to write results.
- Job status is polled via GET on the returned job ID.
- Async SOQL supports aggregations (`COUNT`, `SUM`, `MIN`, `MAX`) but not all SOQL features (e.g., no subqueries across Big Objects).
- Result rows are written as records into the target object — not returned inline to the caller.
- Jobs run asynchronously; there is no push notification; the caller must poll.

### External Objects

External Objects (`__x` suffix) provide a virtual, real-time view of data stored outside Salesforce. They are powered by **Salesforce Connect**, which uses OData 2.0, OData 4.0, or custom Apex adapters to proxy read and write operations to the external system. Every SOQL query against an External Object translates into a live callout to the external data source at query time.

Because each read is a callout, External Objects consume Salesforce SOQL query limits and are subject to callout timeouts (default 10 seconds). They are best suited for small, latency-sensitive lookups of current external data — not for bulk historical data access.

---

## Common Patterns

### Pattern 1: High-Volume Event Log Archival with Big Objects

**When to use:** You are generating large numbers of platform events, integration logs, or IoT sensor readings and need to retain them for compliance or analytics beyond standard data retention windows.

**How it works:**
1. Define a Big Object (e.g., `EventLog__b`) with a composite index on `(UserId__c, EventTime__c, EventType__c)`.
2. In the platform event subscriber or integration handler, call `Database.insertImmediate()` synchronously after event processing.
3. To query, submit an Async SOQL job targeting a scratch custom object or a summary Big Object for aggregated results.
4. Poll the job until status is `Completed`, then read result records from the target object.

**Why not standard objects:** Standard objects cannot hold billions of records without exceeding storage limits and degrading org query performance across unrelated workloads.

```apex
// Inserting a Big Object record
EventLog__b log = new EventLog__b(
    UserId__c      = UserInfo.getUserId(),
    EventTime__c   = DateTime.now(),
    EventType__c   = 'LOGIN',
    Payload__c     = JSON.serialize(eventData)
);
Database.SaveResult result = Database.insertImmediate(log);
if (!result.isSuccess()) {
    // Log errors — insertImmediate does not throw exceptions
    for (Database.Error err : result.getErrors()) {
        System.debug('Big Object insert error: ' + err.getMessage());
    }
}
```

### Pattern 2: Real-Time External Data Lookup with External Objects

**When to use:** You need current data from an external ERP or data warehouse displayed on a Salesforce record page, and the volume of records displayed at once is small (under a few hundred rows per query).

**How it works:**
1. Configure a Salesforce Connect named credential and external data source pointing to the external OData endpoint.
2. Define the External Object with fields mapped to OData entity properties.
3. Create a lookup relationship from a standard or custom object to the External Object.
4. Use standard SOQL in Apex or standard list views to query the External Object — Salesforce handles the callout transparently.

**Why not Big Objects:** Big Objects are on-platform; if the data lives externally and must stay external (regulatory, ownership, or cost reasons), External Objects avoid the need to copy and sync data into Salesforce.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Data lives in Salesforce and volume is > 10M records | Big Object | Own storage tier; does not degrade standard org queries |
| Need real-time single-record lookup of external ERP data | External Object | No data copy required; Salesforce Connect handles callout |
| Need batch analytics over historical data stored externally | Neither — use external analytics platform or Data Cloud | Async SOQL cannot query External Objects; External Object callouts cannot handle bulk scans |
| Need to retain Salesforce event log data for compliance | Big Object with Async SOQL aggregation | On-platform, queryable, no callout limits |
| Data volume is moderate (< 1M records) and needs rollups | Standard custom object | Big Objects do not support roll-up summaries or triggers |
| Query requires non-indexed field filtering at scale | Reconsider composite index design or use external analytics | Async SOQL cannot filter on non-indexed fields efficiently |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All fields used in WHERE clauses appear in the composite index in the correct left-to-right order
- [ ] `Database.insertImmediate()` return values are checked; errors are logged (method does not throw)
- [ ] Async SOQL job targets a valid writable object and the API version supports the query syntax used
- [ ] External Object SOQL query volume is within per-transaction callout limits (100 callouts / 10-second timeout per callout)
- [ ] Big Object storage growth projection has been reviewed against org data storage allocation
- [ ] No triggers, reports, or roll-up summary fields have been placed on a Big Object

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Composite index order is absolute** — Async SOQL silently returns zero results if you filter on a non-leading index column or skip a column in the filter chain. For index `(A, B, C)`, a query `WHERE B = :val` returns nothing. Always filter left-to-right continuously from the first index column.
2. **`Database.insertImmediate` does not throw exceptions** — Unlike `Database.insert`, insert failures are returned as `Database.SaveResult` error objects. Unchecked, they silently fail and records are never written. Always inspect `result.isSuccess()` and log errors.
3. **External Objects count against SOQL limits at query time** — Every SOQL query against an External Object fires a live callout to the external system. In a single Apex transaction, this consumes from the 100-callout limit. Bulk processing logic that queries External Objects in a loop will hit limits immediately.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Big Object composite index design | Ordered list of index fields with rationale tied to the actual query patterns |
| Async SOQL job body | JSON request payload for `POST /async-queries/` with target object and polling guidance |
| Decision matrix entry | Completed row in the Big Object vs External Object vs standard object table |
| Apex insert snippet | `Database.insertImmediate()` call with error-checking pattern |

---

## Related Skills

- `data-archival-strategies` — Use alongside this skill when the broader archival strategy (move to Big Object vs delete vs external storage) is not yet decided
- `limits-and-scalability-planning` — Use when storage growth projections and SOQL limit budgets need formal documentation
