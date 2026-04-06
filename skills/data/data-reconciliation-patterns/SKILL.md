---
name: data-reconciliation-patterns
description: "Patterns for reconciling Salesforce data with external systems: count-level, field-level, and record-level reconciliation, external ID upsert patterns, Change Data Capture for delta detection, and soft-delete tombstone strategies. Use when validating ongoing data sync or diagnosing discrepancies between Salesforce and external data sources. NOT for one-time data migration planning (use data-migration-planning). NOT for initial CDC topic configuration (use change-data-capture skill). NOT for deduplication within Salesforce (use large-scale-deduplication)."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "Salesforce record count does not match the source system after a data sync"
  - "How do I detect which records changed in Salesforce since my last integration run"
  - "External system and Salesforce are out of sync and I need to find the discrepancies"
  - "Upsert is creating duplicates instead of updating existing records"
  - "My delta load is missing hard-deleted records from Salesforce"
tags:
  - data-reconciliation
  - external-id
  - CDC
  - delta-load
  - bulk-api
  - data-quality
  - sync
inputs:
  - "Source system record counts or exported dataset for comparison"
  - "External ID field API name used as the upsert key"
  - "Date/time of last successful sync for delta load filtering"
  - "List of Salesforce objects involved in the integration"
outputs:
  - "SOQL queries for count-level and field-level reconciliation"
  - "Apex pattern for hash-based field comparison"
  - "Bulk API 2.0 upsert configuration using external ID"
  - "CDC replay strategy for gap recovery"
  - "Soft-delete tombstone pattern for detecting hard deletes"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Data Reconciliation Patterns

This skill activates when a Salesforce integration has produced a data discrepancy — record counts differ, field values drift, or records exist in one system but not the other. It provides a layered reconciliation strategy (count, field, record) plus the upsert and delta-detection primitives needed to close those gaps reliably.

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify the external ID field used as the join key between Salesforce and the source system. If none exists, one must be created before upsert-based reconciliation is possible.
- Confirm whether the integration uses Bulk API 2.0, REST API, or a middleware platform — the reconciliation approach differs for each.
- Establish a baseline: what is the expected record count in Salesforce, and what was the timestamp of the last successful sync? These two values anchor every reconciliation check.

---

## Core Concepts

The three levels of reconciliation form a diagnostic ladder. Start at count level, then drill down only when counts diverge.

### Count-Level Reconciliation

Count-level reconciliation compares the number of records in Salesforce against the source system. In Salesforce, use `SELECT COUNT() FROM Object__c WHERE <filter>` — the aggregate returns a single integer with no row limit. Cross-reference this against the equivalent count query on the source side. A mismatch means records were not created, were deleted, or were filtered differently.

Count-level reconciliation is cheap and fast. Run it after every bulk load job before treating a sync as complete. Note that `COUNT()` respects sharing rules if run as a non-admin user — always run reconciliation queries in a system context (via a dedicated integration user with View All Data or via the Tooling API for metadata counts).

### Field-Level Reconciliation

Field-level reconciliation compares the values of specific fields across matched records. Because Salesforce has no native checksum API, all hashing is client-side. The typical pattern is: export a projection of key fields from both systems, compute an MD5 or SHA-256 hash per row, then compare hashes to identify diverged records.

In Apex, `Crypto.generateDigest('SHA-256', Blob.valueOf(inputString))` produces a hash suitable for comparison. Feed it a concatenated string of the fields you care about, normalized to lowercase and trimmed. Field-level reconciliation is expensive at scale — scope it to the delta since the last clean reconciliation rather than running full-table scans.

### Record-Level Reconciliation

Record-level reconciliation uses a shared key — typically a Salesforce External ID field joined to the source system's primary key — to produce a full outer join and surface records that exist in one system but not the other. In Salesforce, External ID fields are created as custom fields with the `External ID` checkbox checked. Up to 25 External ID fields are allowed per object. Text-type External ID fields are case-sensitive by default; if the source system sends mixed-case keys, either normalize to uppercase/lowercase before loading or use a case-insensitive lookup strategy.

---

## Common Patterns

### External ID Upsert via Bulk API 2.0

**When to use:** Creating or updating records in bulk where the source system has a stable primary key that maps to a Salesforce External ID field.

**How it works:** Bulk API 2.0 upsert jobs specify `externalIdFieldName` in the job creation payload. The platform performs a lookup against that field for each incoming row; if a match is found the record is updated, otherwise it is inserted. The job returns per-row success/failure results in `successfulResults` and `failedResults` endpoints.

**Critical constraint:** The External ID field must be unique (unique checkbox on the field definition) to avoid `MULTIPLE_CHOICES` errors. If a non-unique external ID field is used in an upsert and two records match, the upsert fails with `MULTIPLE_CHOICES` for that row. Validate uniqueness in your source data before submitting to the bulk job.

**Why not REST single-record upsert:** For large datasets, REST PATCH by external ID (e.g., `PATCH /services/data/vXX.0/sobjects/Account/External_Id__c/ABC123`) works but is serial and subject to API call limits. Use Bulk API 2.0 for anything over a few hundred records.

### CDC-Driven Delta Load

**When to use:** You need near-real-time detection of changes (inserts, updates, deletes, undeletes) on Salesforce records to sync to an external system.

**How it works:** Change Data Capture publishes platform events to the Pub/Sub API channel `/data/<ObjectName>ChangeEvent` whenever a CDC-enabled record changes. Each event carries a `changeType` header (`CREATE`, `UPDATE`, `DELETE`, `UNDELETE`) and a `replayId`. Subscribers store the last-processed `replayId` and use it on reconnect to replay missed events.

**Gap recovery:** If a subscriber goes offline, it can replay up to 72 hours (3 days) of events using the stored `replayId`. Beyond the retention window, a full reconciliation run (count + record-level) is required to identify the gap. Not all objects support CDC; consult the Salesforce CDC Developer Guide for the supported object list.

### Soft-Delete Tombstone for Hard Delete Detection

**When to use:** Your integration uses `LastModifiedDate` or `SystemModstamp` delta loads and needs to detect records deleted in Salesforce.

**How it works:** Standard SOQL `WHERE LastModifiedDate > :lastRunDate` does not return hard-deleted records. Salesforce exposes deleted records through the `isDeleted = true` filter in queries against the recycle bin (`queryAll()` REST endpoint or `ALL ROWS` SOQL in certain contexts). A tombstone pattern maintains a separate deletion log table in the external system, updated by either a CDC `DELETE` event or a periodic `queryAll` sweep.

**Why this matters:** Without tombstone tracking, records deleted in Salesforce silently diverge from the external system. Count-level checks will catch the discrepancy, but only a tombstone or CDC delete event can tell you *which* records were removed.

### Delta Load via SystemModstamp

**When to use:** CDC is not available for the object, and you need periodic delta detection without full-table comparison.

**How it works:** Filter SOQL with `WHERE SystemModstamp > :lastRunTimestamp`. `SystemModstamp` is updated on every DML write plus system events like formula recalculations. This can produce false positives — records appear "changed" even when no user-visible fields were modified. Filter on `LastModifiedDate` if you only care about explicit DML changes, but be aware `LastModifiedDate` does not update on system-driven recalculations.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need to verify bulk load job completeness | Count-level SOQL reconciliation post-job | Fast, cheap, catches missing rows immediately |
| Records exist in source but appear as duplicates in Salesforce | Verify External ID field has Unique constraint; check for case sensitivity mismatch | Non-unique external IDs cause MULTIPLE_CHOICES on upsert |
| Need real-time detection of Salesforce changes | CDC via Pub/Sub API with replayId gap recovery | Lowest latency; handles insert/update/delete/undelete |
| Periodic batch sync; CDC not available for object | SystemModstamp or LastModifiedDate delta + periodic full reconciliation | Covers most changes; supplement with tombstone for deletes |
| Field values drifted between systems | Field-level hash comparison on key field projection | Pinpoints diverged records without full data export |
| Hard deletes not surfaced by delta load | Tombstone pattern via CDC DELETE events or queryAll sweep | Standard SOQL misses hard deletes entirely |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Confirm the integration's upsert key: identify the External ID field, verify it has the Unique and External ID checkboxes set on the field definition, and validate that the source system sends a consistent key format (case, length, special characters).
2. Run a count-level reconciliation after each bulk load: execute `SELECT COUNT() FROM Object__c WHERE <scope filter>` and compare to the source row count. A count mismatch is the entry point for deeper investigation.
3. If counts match but functional issues remain, run a field-level hash reconciliation on the fields most likely to drift (status fields, date fields, currency fields) using Apex `Crypto.generateDigest` or a client-side hash on a field projection export.
4. For record-level gap detection, use a full outer join on the External ID field — identify records in source not in Salesforce (missing inserts) and records in Salesforce not in source (orphans or unexpected inserts).
5. Set up CDC event subscription with `replayId` persistence for objects that support it. Test gap recovery by simulating a subscriber outage and confirming replay from stored `replayId`.
6. Implement a tombstone strategy for hard deletes: either consume CDC `DELETE` events or run a periodic `queryAll` sweep and mark removed records in the external system.
7. Before closing a reconciliation run, verify that the Bulk API 2.0 job's `failedResults` endpoint returns zero rows — partial failures are silent unless explicitly checked.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] External ID field has both Unique and External ID checkboxes checked on the object definition
- [ ] Bulk API 2.0 job `failedResults` endpoint has been checked and returns zero failed rows
- [ ] Count-level reconciliation passes (Salesforce count equals source system count within expected tolerance)
- [ ] Hard delete handling is addressed via CDC DELETE events or a queryAll tombstone sweep
- [ ] CDC subscriber stores `replayId` persistently and gap recovery has been tested
- [ ] SystemModstamp false positives from formula recalculations are accounted for in the delta load filter

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **SystemModstamp fires on formula recalculation** — When a formula field recalculates (e.g., due to a referenced lookup changing), `SystemModstamp` updates on the parent record even though no user-visible DML occurred. This causes delta loads to pull records that appear unchanged in the downstream system, wasting processing cycles and potentially triggering false update notifications. Use `LastModifiedDate` if you only want explicit DML changes.

2. **External ID Text fields are case-sensitive** — A Text-type External ID field treats `ABC123` and `abc123` as different values. If the source system sends mixed-case keys, upserts will create duplicate records instead of updating. Either enforce normalization at the source (always uppercase/lowercase) or use a case-insensitive custom field approach with a formula-derived normalized field.

3. **MULTIPLE_CHOICES on non-unique external IDs** — If an External ID field is not marked Unique and two Salesforce records share the same external ID value, a Bulk API 2.0 upsert targeting that field will fail with `MULTIPLE_CHOICES` for those rows. The error does not prevent other rows from processing but silently skips the affected rows unless `failedResults` is explicitly checked.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Count reconciliation SOQL query | A parameterized `SELECT COUNT()` query scoped to the relevant object and date filter, ready to run post-bulk-load |
| Field-level hash comparison script | Apex or Python pattern that normalizes and hashes key field projections from both systems for comparison |
| Bulk API 2.0 upsert job spec | JSON job creation payload with `externalIdFieldName` set and `failedResults` check logic |
| CDC replay configuration | Pub/Sub API subscriber config with `replayId` persistence and 3-day window gap recovery procedure |
| Tombstone query | `queryAll` SOQL for deleted record detection, parameterized by object and last-run timestamp |

---

## Related Skills

- data-migration-planning — use for one-time initial data migration; this skill handles ongoing sync verification after go-live
- external-id-strategy — use to decide which field to use as the upsert key and how to design the External ID schema across objects
- bulk-api-patterns — use for Bulk API 2.0 job lifecycle, error handling, and throughput optimization
