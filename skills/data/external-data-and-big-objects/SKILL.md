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
  - "Async SOQL job returns 404 or the async-queries endpoint is gone (retired Summer '23)"
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
  - "Big Object read plan: standard SOQL vs Batch Apex vs Bulk API query, with index-prefix filters"
  - "Decision matrix entry: Big Object vs External Object vs standard object"
  - "Apex insert pattern using Database.insertImmediate"
  - "Review checklist confirming index coverage and a supported (non-Async-SOQL) read path"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# External Data and Big Objects

This skill activates when a practitioner needs to store, retrieve, or decide the placement of extremely large or historical datasets in a Salesforce org. It covers the two main platform mechanisms for high-volume data: **Big Objects** (on-platform storage tier) and **External Objects** (virtual, real-time access via Salesforce Connect). Use this skill to design composite indexes, pick a working read path, choose between the two mechanisms, and avoid the platform-specific failure modes that trip up every team the first time.

**Read this before anything else in the Big Object space:** Async SOQL was **retired in Summer '23**. It appears throughout pre-2023 documentation, blog posts, and model training data as the canonical way to query a Big Object, and it does not exist. Replacements are standard SOQL, Batch Apex, and Bulk API query.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Volume and query patterns**: Big Objects are only queryable via composite index fields. If you do not know which fields will be filtered, you cannot design the index — and an unusable index means an unqueryable Big Object.
- **Async SOQL no longer exists — check this first.** Salesforce retired Async SOQL with the **Summer '23** release. `POST /services/data/vXX.0/async-queries/` and the `AsyncQueryJob` API are gone. Any design, runbook, or code review comment that routes Big Object reads through Async SOQL is describing a feature that has not existed since 2023, and a team that archives into a Big Object on that basis discovers at read time that there is no read path. Per Salesforce Help: "You must use the Bulk API or batch Apex to query or report on custom Big Objects."
- **Standard SOQL is the query mechanism for Big Objects**, not a fallback for small data. It works, and it is what Batch Apex and the Bulk API run underneath. What constrains it is the composite index: filters must follow the index left to right with no gaps. See Core Concepts.
- **Storage vs API limits**: External Objects count against SOQL query limits on every read because each query results in a live callout to the external system. Big Objects do not make callouts but consume Salesforce data storage. This distinction drives the core decision.

---

## Core Concepts

### Big Objects

Big Objects are a dedicated Salesforce storage tier designed for datasets in the hundreds of millions to billions of records. They are defined as custom metadata objects with the suffix `__b` and are inserted via `Database.insertImmediate()` (synchronous, fire-and-forget) or the Bulk API v1/v2.

Big Objects require a **composite index**: a mandatory, ordered list of fields that defines both the uniqueness constraint and the queryable access path. Per the SOQL and SOSL Reference, verbatim: "A SOQL query can only filter on the fields defined in the big object's index, in the order that they are defined, without gaps." Filter a later index field while omitting an earlier one and the query is invalid.

Operator support is asymmetric across the index and this is easy to get wrong:

- Every index field **before** the last one you filter on accepts **`=` only**.
- The **final** index field in your filter chain also accepts `<`, `>`, `<=`, `>=`, and `IN`.
- `!=`, `LIKE`, `NOT IN`, `EXCLUDES`, and `INCLUDES` are **not supported anywhere** in a big object query.

So for index `(UserId__c, EventTime__c, EventType__c)`, `WHERE UserId__c = :u AND EventTime__c >= :start` is valid — a range on the last filtered field. `WHERE EventTime__c >= :start` alone is not, because it skips the leading field. This is why the index has to be designed from the query patterns, not from the data shape.

**Platform limitations of Big Objects:**
- No triggers (before/after insert/update/delete are not supported)
- No standard reports or list views
- No roll-up summary fields pointing at Big Object records
- No SOSL (Salesforce Object Search Language) support
- Restricted SOQL: filters must be a gapless left-to-right prefix of the composite index (see above)

### Querying Big Objects (Async SOQL Was Retired in Summer '23)

**Async SOQL is gone.** Salesforce retired it with Summer '23. There is no `/services/data/vXX.0/async-queries/` endpoint and no `AsyncQueryJob` resource. If you are reading a design that submits a background query job and polls for a `targetObject` to be populated, that design cannot be built. Per Salesforce Help (article 000394892): "You must use the Bulk API or batch Apex to query or report on custom Big Objects."

The three supported read paths, in order of when to reach for each:

| Path | Use when | Notes |
|---|---|---|
| **Standard SOQL** (Apex, REST, Developer Console) | Bounded result sets — a specific user's history, one day's rows | Subject to the normal Apex query-row limit (50,000 rows per transaction). Filters must be a gapless index prefix. |
| **Batch Apex** over a `Database.QueryLocator` on the big object | Result sets larger than a single transaction can hold — the general answer for production volume | This is what replaced Async SOQL's job semantics. Salesforce's guidance for very large result sets is to chain additional batch jobs. Aggregate in `execute()`, write the summary in `finish()`. |
| **Bulk API query** | Extracting rows out of the platform entirely | Async, job-based, results downloaded as CSV. |

The substantive difference from Async SOQL is that **nothing writes results into a target object for you any more.** Async SOQL materialised aggregates as a side effect of the job; Batch Apex does not. If your design depended on that, you now own the write: accumulate in the batch class's instance state and insert the summary records yourself in `finish()`.

```apex
// Replacement for the retired "Async SOQL aggregate into a summary object" pattern.
// Stateful batch over a big object; the class does the aggregation and the write.
public class EventLogRollup implements Database.Batchable<SObject>, Database.Stateful {

    private Map<String, Integer> countsByType = new Map<String, Integer>();
    private final Id targetUserId;
    private final DateTime windowStart;

    public EventLogRollup(Id targetUserId, DateTime windowStart) {
        this.targetUserId = targetUserId;
        this.windowStart  = windowStart;
    }

    public Database.QueryLocator start(Database.BatchableContext bc) {
        // Gapless left-to-right prefix of index (UserId__c, EventTime__c, EventType__c):
        // leading field uses =, the last filtered field may use a range operator.
        return Database.getQueryLocator([
            SELECT UserId__c, EventTime__c, EventType__c
            FROM EventLog__b
            WHERE UserId__c = :targetUserId AND EventTime__c >= :windowStart
        ]);
    }

    public void execute(Database.BatchableContext bc, List<EventLog__b> scope) {
        for (EventLog__b row : scope) {
            Integer running = countsByType.get(row.EventType__c);
            countsByType.put(row.EventType__c, running == null ? 1 : running + 1);
        }
    }

    public void finish(Database.BatchableContext bc) {
        // Async SOQL used to do this write for you. It does not exist; you do it.
        List<EventRollup__c> summaries = new List<EventRollup__c>();
        for (String eventType : countsByType.keySet()) {
            summaries.add(new EventRollup__c(
                UserId__c    = targetUserId,
                EventType__c = eventType,
                EventCount__c = countsByType.get(eventType)
            ));
        }
        insert summaries;
    }
}
```

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
3. To query, run standard SOQL for bounded reads, or a stateful Batch Apex job over a `Database.QueryLocator` on the Big Object for anything larger than one transaction. (Async SOQL was the documented path here until Summer '23; it no longer exists.)
4. If the job produces aggregates, write the summary records yourself in `finish()` — nothing materialises results into a target object for you.

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
| Need batch analytics over historical data stored externally | Neither — use external analytics platform or Data Cloud | External Object callouts cannot handle bulk scans; Big Object query paths do not reach `__x` objects |
| Need to retain Salesforce event log data for compliance | Big Object, read via Batch Apex | On-platform, queryable, no callout limits |
| Data volume is moderate (< 1M records) and needs rollups | Standard custom object | Big Objects do not support roll-up summaries or triggers |
| Query requires non-indexed field filtering at scale | Reconsider composite index design or use external analytics | Big object SOQL cannot filter on non-indexed fields at all — not a performance issue, a hard restriction |

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
- [ ] Read path is standard SOQL, Batch Apex, or Bulk API query — NOT Async SOQL (retired Summer '23) — and any aggregate write into a summary object is implemented explicitly in `finish()`
- [ ] External Object SOQL query volume is within per-transaction callout limits (100 callouts / 10-second timeout per callout)
- [ ] Big Object storage growth projection has been reviewed against org data storage allocation
- [ ] No triggers, reports, or roll-up summary fields have been placed on a Big Object

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Composite index order is absolute** — filters must be a gapless left-to-right prefix of the index. For index `(A, B, C)`, `WHERE B = :val` is not a valid big object query because it skips A. Fields before the last one you filter on take `=` only; the last one may also take `<`, `>`, `<=`, `>=`, `IN`. `!=`, `LIKE`, `NOT IN`, `EXCLUDES`, and `INCLUDES` are unsupported outright.
2. **Async SOQL was retired in Summer '23** — `/services/data/vXX.0/async-queries/` and `AsyncQueryJob` do not exist. Most Big Object material written before mid-2023 (including a large amount of training data) presents it as *the* read path, so this is the single most likely wrong assumption in any Big Object design you inherit. Read via standard SOQL, Batch Apex, or Bulk API query, and write your own aggregate rows in `finish()`.
2. **`Database.insertImmediate` does not throw exceptions** — Unlike `Database.insert`, insert failures are returned as `Database.SaveResult` error objects. Unchecked, they silently fail and records are never written. Always inspect `result.isSuccess()` and log errors.
3. **External Objects count against SOQL limits at query time** — Every SOQL query against an External Object fires a live callout to the external system. In a single Apex transaction, this consumes from the 100-callout limit. Bulk processing logic that queries External Objects in a loop will hit limits immediately.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Big Object composite index design | Ordered list of index fields with rationale tied to the actual query patterns |
| Big Object read plan | Standard SOQL vs Batch Apex vs Bulk API query, with the index-prefix filter each read will use |
| Decision matrix entry | Completed row in the Big Object vs External Object vs standard object table |
| Apex insert snippet | `Database.insertImmediate()` call with error-checking pattern |

---

## Related Skills

- `data-archival-strategies` — Use alongside this skill when the broader archival strategy (move to Big Object vs delete vs external storage) is not yet decided
- `limits-and-scalability-planning` — Use when storage growth projections and SOQL limit budgets need formal documentation
