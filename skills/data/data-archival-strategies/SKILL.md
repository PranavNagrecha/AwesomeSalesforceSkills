---
name: data-archival-strategies
description: "Use when planning how to archive aging Salesforce records to reduce storage costs, maintain query performance, and meet retention policies. Covers Big Object archival, external storage via Heroku or S3, field history truncation, recycle bin behavior, and soft-delete patterns. Triggers: storage limit reached, archive old records, Big Objects, field history too large, recycle bin overflow, data retention policy. NOT for migrating data to a new org (use data-migration-planning) or cleaning up duplicate records (use duplicate-management)."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
tags:
  - archival
  - big-objects
  - storage
  - large-data-volumes
  - data-retention
inputs:
  - Object(s) to be archived with approximate record volumes
  - Data retention policy (how long to keep data accessible vs archived)
  - Storage type breakdown (data storage vs file storage)
  - Compliance or audit requirements
outputs:
  - Archival strategy recommendation (Big Object vs external)
  - Archival implementation plan with sequencing
  - Storage reclamation estimate
  - Recycle bin and soft-delete guidance
triggers:
  - storage limit reached on my salesforce org
  - how do I archive old records in Salesforce
  - big objects for archival
  - field history is too large
  - recycle bin is affecting storage
  - data retention policy for salesforce records
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Data Archival Strategies

Use this skill when an org is approaching storage limits, experiencing query performance degradation from large object row counts, or needs to implement a formal data retention and archival policy. This skill does NOT cover migrating data to a new org (use `data-migration-planning`) or cleaning up duplicate records.

---

## Before Starting

Gather this context before working on anything in this domain:

- What is the current storage usage breakdown? Run Setup > Storage Usage to see data storage vs file storage split.
- What is the org edition? Storage limits differ: Essentials and Professional each get 1 GB base; Enterprise and Unlimited get 10 GB base plus 20 MB per user license for data storage.
- Does the org use Salesforce Shield? Shield provides Field Audit Trail with configurable retention beyond the default 18 months; without Shield, field history is capped at 18 months rolling.
- Are there compliance or legal hold requirements that prevent hard deletion of records?
- What is the query access pattern for the data to be archived — does it need to remain queryable from within Salesforce, or is it purely for audit/retention?

---

## Core Concepts

### Salesforce Storage Model

Salesforce separates storage into two buckets:

- **Data storage** — counts standard and custom object records. Roughly 2 KB per record on average. Every record in an object counts, including soft-deleted records in the recycle bin (see Recycle Bin section).
- **File storage** — counts Attachments, Files (ContentVersion), and documents. File storage limits scale differently: Enterprise gets 1 GB base plus 2 GB per user license.

Storage alerts fire at 85% and 100% of your allocation. Exceeding data storage blocks new record inserts org-wide — a critical reliability risk.

### Big Objects

Salesforce Big Objects (`__b` suffix) are a separate, horizontally scalable database that stores and manages massive amounts of data — consistently across 1 million, 100 million, or 1 billion records. They are available in Enterprise, Performance, Unlimited, and Developer Editions (Developer Edition is capped at 1 million records).

Key behavioral constraints:

- **Immutable after write** — standard DML (`insert`, `update`, `delete`) does not apply. Use `Database.insertImmediate()` for writes. Updates are achieved by reinserting with the same index values (upsert semantics). Deletion uses `Database.deleteImmediate()` or SOAP `deleteByExample()`.
- **Index-only queries** — SOQL on Big Objects must use fields that are part of the defined composite index, in order, without gaps. Arbitrary filter queries are not supported.
- **No triggers, flows, or processes** — automations do not fire on Big Object writes. Use asynchronous Apex (Queueable or Batch) for any post-write processing.
- **No aggregate functions in SOQL** — `COUNT()` and similar aggregates are not supported. Use Batch Apex to iterate and count manually.
- **No standard UI** — Big Objects do not appear in standard list views, reports, or dashboards. To surface Big Object data in reports, extract a representative subset into a custom object via Bulk API query, then report on the custom object.
- **Idempotent writes** — reinserting a record with identical index values results in a single record, making retry-on-failure safe.
- **No encryption support for custom Big Objects** — data archived to a custom Big Object from an encrypted standard/custom object is stored as clear text. The standard `FieldHistoryArchive` Big Object does respect Shield Platform Encryption.
- **Mixed DML restriction in Apex tests** — tests cannot mix DML on sObjects and Big Objects in the same transaction. Use a mocking framework or manually roll back test data.

### Field History and Field History Truncation

Salesforce tracks field history on standard and custom objects when Field History Tracking is enabled. History records are stored in a separate History object (e.g., `AccountHistory`, `OpportunityFieldHistory`) and are subject to an 18-month rolling retention window by default.

- History records are stored separately from the parent object. They count against data storage on their own.
- After 18 months, Salesforce automatically truncates field history records. There is no API to manually trigger truncation sooner.
- With Salesforce Shield's **Field Audit Trail**, history can be retained for up to 10 years and is archived into the `FieldHistoryArchive` Big Object. Without Shield, you cannot extend the 18-month window.
- When archiving parent records, their associated history records are NOT automatically archived — the History object retains those rows until automatic truncation.

### Recycle Bin and Soft Delete

When a record is deleted in Salesforce, it enters the Recycle Bin (soft delete):

- Soft-deleted records remain in the Recycle Bin for 15 days and can be restored during that period.
- After 15 days, records are scheduled for hard deletion.
- Soft-deleted records affect query performance — they participate in selectivity calculations even though they are excluded from standard queries. Keeping the Recycle Bin full degrades performance on large tables.
- To hard-delete immediately: use Setup > Empty Recycle Bin, the Apex `Database.emptyRecycleBin()` method, or Bulk API 2.0 hard delete operation.
- The Bulk API 2.0 hard delete bypasses the Recycle Bin entirely — deleted records are gone immediately and do not affect storage or selectivity.

---

## Common Patterns

### Mode 1: Design an Archival Strategy from Scratch

**When to use:** Org is growing rapidly, storage is projected to exceed limits within 6–12 months, or a data retention policy requires records older than N years to be moved off the main object.

**How it works:**

1. Run Setup > Storage Usage to establish the current data storage and file storage baseline.
2. Identify the top 3–5 objects by record count. Use SOQL aggregate queries: `SELECT COUNT(Id) FROM Opportunity`.
3. For each candidate object, determine: (a) is the data still needed for real-time queries or reports? (b) what is the legal retention requirement?
4. Choose an archival destination:
   - **Big Object** if the data must remain queryable from within Salesforce (compliance, audit dashboards) and the query pattern fits the indexed fields.
   - **External storage** (Heroku PostgreSQL, Amazon S3 via middleware, Data Cloud) if data is rarely accessed and cost-optimized storage is the priority.
   - **Soft-delete pattern** (IsArchived__c flag) if the data must remain in the same object for reporting but should be excluded from standard views.
5. Design the archival job: use Batch Apex to read source records in pages of up to 2,000, write to the destination, then hard-delete source records via `Database.deleteImmediate()` or Bulk API hard delete.
6. Schedule the archival job to run nightly or weekly depending on growth rate.

**Why not archive manually:** Manual export-and-delete via Data Loader creates recycle bin pollution that degrades query performance until the 15-day window expires. Batch Apex with hard delete reclaims storage immediately.

### Mode 2: Audit Current Storage and Recommend Action

**When to use:** Storage alert has fired or query performance has degraded on a large object.

**How it works:**

1. Check Setup > Storage Usage. Identify whether the pressure is data storage or file storage.
2. For data storage pressure: run `SELECT COUNT(Id) FROM RecycleBin` equivalent — check Setup > Recycle Bin for volume. Empty the recycle bin first; this is the fastest win.
3. Identify the top objects by count. Look for History objects (`AccountHistory`, `CaseHistory`) as hidden storage consumers.
4. Check if field history tracking is enabled on high-volume objects for fields that change frequently (e.g., Stage, Status). Disabling tracking on low-value fields stops future accumulation.
5. Recommend archival approach based on access pattern (see Decision Guidance table below).

### Mode 3: Troubleshoot Storage Alert or Query Performance Degradation

**When to use:** Org has received a storage alert or users report slow list views and reports on large objects.

**How it works:**

1. Empty the Recycle Bin immediately (Setup or `Database.emptyRecycleBin()`). Soft-deleted records degrade selectivity for query optimization.
2. Identify if the alert is driven by file storage (Attachments, ContentVersion). If so, the archival strategy is different — files require external storage or Content Delivery Networks.
3. For query performance: check if the slow query has selective filters on indexed fields. On objects with millions of records, non-selective filters cause full table scans.
4. For data storage: run a batch archival job targeting the oldest records by `CreatedDate` that are beyond the retention window.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Data must remain queryable from Salesforce with known filter patterns | Big Object with composite index | Consistent performance at billions of records; stays on-platform |
| Data is rarely accessed, cost is primary concern | External storage (S3 / Heroku / Data Cloud) | Lower cost per GB; no on-platform storage consumed |
| Records must stay on the parent object for reports but hidden from users | Soft-delete pattern (IsArchived__c boolean) | Keeps records in-org, excludes from views, supports historical queries |
| Storage alert fired and recycle bin is full | Empty recycle bin immediately | Fastest storage reclamation, no archival job required |
| Field history is consuming excessive storage | Disable tracking on low-value fields; evaluate Shield for extended retention | Field history growth is unbounded on high-churn fields |
| Compliance requires 7+ year history retention | Salesforce Shield Field Audit Trail + FieldHistoryArchive Big Object | Only supported path to extend beyond 18-month default |
| Large file/attachment storage pressure | Archive files to external storage; use Salesforce Files Connect or custom middleware | File storage limits are separate from data storage |

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

Run through these before marking archival work complete:

- [ ] Storage baseline documented (data storage GB used / limit, file storage GB used / limit)
- [ ] Archival candidate objects identified with current record counts and growth rates
- [ ] Recycle bin emptied before measuring baseline (avoids inflated numbers)
- [ ] Field history tracking reviewed — disabled on fields where history is not required
- [ ] Archival destination chosen and validated (Big Object index designed, or external endpoint confirmed)
- [ ] Batch Apex archival job tested in sandbox on a representative data volume
- [ ] Hard delete used (not soft delete) to reclaim storage immediately after archival
- [ ] Post-archival storage usage confirmed to be below alert threshold
- [ ] Query performance on the source object validated after records are removed

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Big Object records cannot be updated or deleted via standard DML** — `update` and `delete` DML statements throw an exception on Big Object records. Updates require reinserting with the same index values (upsert semantics). Deletion uses `Database.deleteImmediate()` which requires all index fields to be specified. Treating a Big Object like a standard object in Apex will cause runtime errors.
2. **Async SOQL is not transactional and runs slowly** — Async SOQL jobs run asynchronously and materialize results into a standard or Big Object. They are not real-time and cannot be chained with synchronous processes. Do not use Async SOQL where immediate consistency is required.
3. **Recycle bin affects query optimizer selectivity** — Even though soft-deleted records are excluded from normal SOQL results, they still participate in selectivity calculations used by the query optimizer. A full Recycle Bin on a large object can cause full table scans and slow reports, even if the table appears smaller to users. Empty the Recycle Bin regularly.
4. **Field history on archived records is not archived automatically** — When you archive (or delete) parent records, the associated History object rows (`AccountHistory`, `CaseHistory`, etc.) are NOT deleted automatically. They remain in the History object and continue to count against data storage until the 18-month automatic truncation window expires.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Archival strategy recommendation | Decision between Big Object, external storage, or soft-delete pattern with rationale |
| Archival implementation plan | Sequenced Batch Apex job design, index definition, and schedule |
| Storage reclamation estimate | Projected GB recovered based on record counts and average record size |
| Recycle bin and soft-delete guidance | Steps to empty recycle bin and implement IsArchived__c pattern |

---

## Related Skills

- `data-migration-planning` — Use when moving data to a new org or bulk-loading from external systems, not for in-org archival
- `limits-and-scalability-planning` — Use to forecast storage growth and plan capacity before hitting limits
- `data-quality-and-governance` — Use to define retention policies and data lifecycle governance that feed into archival decisions
