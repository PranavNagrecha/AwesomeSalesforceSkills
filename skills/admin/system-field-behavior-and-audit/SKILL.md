---
name: system-field-behavior-and-audit
description: "Use when practitioners need to understand system-managed fields (CreatedDate, LastModifiedDate, SystemModstamp, CreatedById, LastModifiedById, IsDeleted) — their update behavior, indexing, and queryability. Triggers: 'difference between SystemModstamp and LastModifiedDate', 'how to query deleted records', 'set CreatedDate during data migration', 'why does LastModifiedDate not match SystemModstamp', 'Create Audit Fields permission'. NOT for field-level change tracking (use field-history-tracking skill), Shield Field Audit Trail for compliance retention (use field-audit-trail skill), or custom audit logging with Apex triggers."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Performance
triggers:
  - "what is the difference between SystemModstamp and LastModifiedDate"
  - "how do I query records that were deleted from the recycle bin"
  - "I need to preserve the original CreatedDate when migrating data into Salesforce"
  - "why does SystemModstamp keep changing but LastModifiedDate does not"
  - "how do I enable Create Audit Fields for data migration"
  - "which date field should I use for incremental delta sync queries"
  - "IsDeleted field and queryAll to find soft-deleted records"
tags:
  - system-fields
  - audit-fields
  - SystemModstamp
  - LastModifiedDate
  - CreatedDate
  - IsDeleted
  - data-migration
  - delta-sync
inputs:
  - "Which system fields are being referenced or queried"
  - "Whether the use case is delta sync, data migration, audit reporting, or soft-delete recovery"
  - "Org edition and whether Create Audit Fields permission is enabled"
outputs:
  - "Field selection guidance for the practitioner's use case"
  - "SOQL query patterns for delta sync or soft-delete recovery"
  - "Create Audit Fields enablement checklist for data migration"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# System Field Behavior and Audit

Use this skill when a practitioner needs to understand how Salesforce automatically manages system fields on every record — when each field updates, which fields are indexed, how to query deleted records, and how to override audit fields during data migration.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Use case**: Is this about delta sync / incremental queries, data migration with date preservation, soft-delete recovery, or general audit understanding?
- **Common wrong assumption**: Practitioners assume LastModifiedDate and SystemModstamp always have the same value. They diverge whenever an automated system process (workflow field update, formula recalculation, approval process) modifies a record without a direct user or API save.
- **Platform constraints**: Create Audit Fields is an org-level permission that must be enabled by Salesforce Support. It allows overriding CreatedDate, CreatedById, LastModifiedDate, and LastModifiedById only on insert, not on update.

---

## Core Concepts

### SystemModstamp vs. LastModifiedDate

Both fields record when a record was last changed, but they track different scopes of change:

- **LastModifiedDate** updates only when a user or API call explicitly modifies the record (DML update, inline edit, API PATCH/POST). It reflects the last *intentional* edit.
- **SystemModstamp** updates on every change, including automated system processes — workflow field updates, formula recalculations, roll-up summary recalculations, and approval process field stamps. SystemModstamp is always >= LastModifiedDate.

SystemModstamp is indexed by the platform. LastModifiedDate is not indexed. For any SOQL query that filters by modification date (delta sync, incremental ETL, change data capture fallback), always use SystemModstamp for correctness and performance.

### Create Audit Fields

The "Create Audit Fields" org permission (also called "Set Audit Fields upon Record Creation") allows API clients to set the four audit ownership fields on insert:

- `CreatedDate`
- `CreatedById`
- `LastModifiedDate`
- `LastModifiedById`

This is used exclusively during data migration to preserve historical timestamps and ownership from a source system. The permission must be enabled by Salesforce Support (Setup > Contact Support, or via case). It applies org-wide once enabled and works only on insert operations — you cannot retroactively change these fields on existing records via update.

### IsDeleted and Soft Deletes

When a record is moved to the Recycle Bin, Salesforce sets `IsDeleted = true` on the record rather than physically removing it. The record remains queryable through two mechanisms:

- **SOQL**: `SELECT Id, Name FROM Account WHERE IsDeleted = true ALL ROWS`
- **REST API**: The `/services/data/vXX.0/queryAll/` endpoint (vs. the standard `/query/` endpoint)

Records in the Recycle Bin are retained for 15 days (configurable up to 15 days). After permanent deletion, records are no longer queryable by any means. The `ALL ROWS` keyword also returns archived records on objects that support archiving.

---

## Common Patterns

### Delta Sync with SystemModstamp

**When to use:** An integration or ETL process needs to pull only records modified since the last sync.

**How it works:**

```sql
SELECT Id, Name, AccountNumber, SystemModstamp
FROM Account
WHERE SystemModstamp > 2025-01-15T00:00:00Z
ORDER BY SystemModstamp ASC
```

Store the highest SystemModstamp value returned as the watermark for the next sync. Use `ORDER BY SystemModstamp ASC` so if the sync is interrupted, you can resume from the last processed record.

**Why not LastModifiedDate:** A workflow field update that fires after record save will update SystemModstamp but not LastModifiedDate. Using LastModifiedDate misses those changes, causing data drift between systems.

### Data Migration with Audit Field Preservation

**When to use:** Migrating records from a legacy system or another Salesforce org where you need to preserve the original creation date and creator.

**How it works:**

1. Confirm Create Audit Fields permission is enabled (Setup > User Interface > Enable "Set Audit Fields upon Record Creation", or contact Support).
2. In your Data Loader or Apex script, include `CreatedDate`, `CreatedById`, `LastModifiedDate`, and `LastModifiedById` columns in the insert payload.
3. The user performing the insert must have the "Set Audit Fields upon Record Creation" user permission assigned via permission set.
4. Insert the records. The platform accepts the provided timestamps instead of auto-generating them.

**Why not post-insert update:** You cannot update audit fields after insert — the platform rejects DML updates to these fields even with the permission enabled.

### Soft-Delete Recovery Query

**When to use:** A user accidentally deleted records and you need to identify what was lost before the Recycle Bin expires.

**How it works:**

```sql
SELECT Id, Name, CreatedDate, LastModifiedDate, LastModifiedById
FROM Contact
WHERE IsDeleted = true
  AND LastModifiedDate = LAST_N_DAYS:7
ALL ROWS
```

Use this to generate a list of recently deleted records for review. Admins can then undelete from the Recycle Bin via Setup or the `Database.undelete()` Apex method.

---

## Decision Guidance

| Situation | Recommended Field | Reason |
|---|---|---|
| Incremental ETL / delta sync queries | SystemModstamp | Indexed; captures all changes including automated processes |
| Display "last edited" to end users | LastModifiedDate | Reflects intentional human/API edits only |
| Audit trail of who last changed a record | LastModifiedById | Paired with LastModifiedDate for human-edit attribution |
| Preserve historical dates during migration | CreatedDate (with Create Audit Fields) | Only works on insert; requires org permission from Support |
| Find recently deleted records | IsDeleted + ALL ROWS | 15-day Recycle Bin window; permanent deletes are unrecoverable |
| Replication / data synchronization | SystemModstamp + IsDeleted (ALL ROWS) | Covers modifications, automated changes, and soft deletes |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on system field questions:

1. **Identify the use case** — Determine whether the practitioner needs delta sync, data migration, soft-delete recovery, or general field understanding.
2. **Check field semantics** — Confirm which system field applies. Use SystemModstamp for any query where completeness matters; use LastModifiedDate only for human-attribution display.
3. **Verify org permissions** — If data migration with audit field override is needed, confirm Create Audit Fields is enabled at the org level and the user has the corresponding user permission.
4. **Write or review the SOQL** — Ensure delta sync queries filter on SystemModstamp (not LastModifiedDate). Ensure soft-delete queries include `ALL ROWS`. Verify ORDER BY for resumable processing.
5. **Test in a sandbox** — Trigger a workflow field update on a record, then compare SystemModstamp vs. LastModifiedDate to confirm they diverge as expected. Test Create Audit Fields with a sample insert.
6. **Document the watermark strategy** — For delta sync, document where the high-watermark is stored, how failures are handled, and the expected sync frequency.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Delta sync queries use SystemModstamp, not LastModifiedDate
- [ ] Soft-delete recovery queries use ALL ROWS (SOQL) or queryAll (REST)
- [ ] Create Audit Fields permission is confirmed enabled before migration insert
- [ ] The migrating user has the "Set Audit Fields upon Record Creation" user permission
- [ ] Audit field values are included only in insert operations, not updates
- [ ] Watermark / checkpoint strategy is documented for incremental sync
- [ ] Recycle Bin retention window (15 days) is accounted for in recovery plans

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **SystemModstamp updates silently on formula recalculations** — If a formula field references a parent record's field and that parent changes, the child's SystemModstamp may update without any direct change to the child record. This inflates delta sync volumes.
2. **Create Audit Fields works on insert only** — Attempting to update CreatedDate or CreatedById on an existing record via DML silently fails or throws an error depending on context. There is no supported way to change these fields after record creation.
3. **ALL ROWS includes archived records** — On objects with archiving enabled, `ALL ROWS` returns both soft-deleted and archived records. If you only want Recycle Bin items, add `IsDeleted = true` as an explicit filter.
4. **LastModifiedDate is not indexed** — Filtering SOQL queries by `LastModifiedDate >` will result in a full table scan on large objects. SystemModstamp is the indexed alternative.
5. **Bulk API queryAll behaves differently** — The Bulk API uses the `queryAll` operation to include deleted/archived records. The syntax differs from REST API's `/queryAll/` endpoint — consult the Bulk API documentation for the correct job configuration.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Field selection recommendation | Which system field to use for the practitioner's specific use case with rationale |
| Delta sync SOQL template | Ready-to-use query with SystemModstamp filter and ORDER BY for resumable sync |
| Create Audit Fields enablement checklist | Steps to enable the permission, assign to users, and validate with test insert |
| Soft-delete recovery query | ALL ROWS query template for identifying and recovering deleted records |

---

## Related Skills

- `field-history-tracking` — Use when you need to track individual field value changes over time, not just the last modification timestamp.
- `field-audit-trail` — Use when compliance requires retaining field change history beyond 18 months (Shield Field Audit Trail).
- `data-migration-planning` — Use for end-to-end migration planning including Create Audit Fields as one component.
- `soql-query-optimization` — Use for broader SOQL performance guidance beyond system field indexing.

---

## Official Sources Used

- Object Reference: System Fields — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/system_fields.htm
- Help: Set Audit Fields upon Record Creation — https://help.salesforce.com/s/articleView?id=sf.enable_set_audit_fields.htm
- REST API Developer Guide: queryAll — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/dome_queryall.htm
- SOQL Reference: ALL ROWS — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_all_rows.htm
