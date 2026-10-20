---
name: system-field-behavior-and-audit
description: "Use when practitioners need to understand system-managed fields (CreatedDate, LastModifiedDate, SystemModstamp, CreatedById, LastModifiedById, IsDeleted) — their update behavior, indexing, and queryability. Triggers: 'difference between SystemModstamp and LastModifiedDate', 'how to query deleted records', 'set CreatedDate during data migration', 'why does LastModifiedDate not match SystemModstamp', 'Create Audit Fields permission'. NOT for a field's value-change history — use data/field-history-tracking. NOT for Shield Field Audit Trail — use security/field-audit-trail."
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
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# System Field Behavior and Audit

Use this skill when a practitioner needs to understand how Salesforce automatically manages system fields on every record — when each field updates, which fields are indexed, how to query deleted records, and how to override audit fields during data migration.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Use case**: Is this about delta sync / incremental queries, data migration with date preservation, soft-delete recovery, or general audit understanding?
- **Common wrong assumption**: Practitioners assume LastModifiedDate and SystemModstamp always have the same value. The Object Reference defines LastModifiedDate as "when a user last modified this record" and SystemModstamp as when "a user or automated process" did (object_reference 264 L2563, L2566). UNVERIFIED (2026-10-20): which specific processes (workflow field update, approval stamp, roll-up recalculation) advance SystemModstamp but not LastModifiedDate — the guide names none of them. The guide also warns SystemModstamp "doesn't capture every field change": if object A retrieves values from object B, B's change is reflected on B's SystemModstamp but not A's (object_reference 264 L2581-2583).
- **Platform constraints**: Create Audit Fields is self-service in Setup (User Interface > "Set Audit Fields upon Record Creation"), plus the user permission of the same name on a profile or permission set (object_reference 264 L2600-2602). It lets you set CreatedDate, CreatedById, LastModifiedDate and LastModifiedById when you create a record, on the listed objects only (Account, ArticleVersion, Attachment, CampaignMember, Case, CaseComment, Contact, ContentVersion, Contract, Event, Idea, IdeaComment, Lead, Opportunity, Question, Task, Vote and custom objects, L2592-2594). SystemModstamp is the one audit field you cannot set (L2594). Restrictions: CreatedDate cannot be greater than LastModifiedDate and no date may be later than the current time (L3132-3133). Insert-only is the safe reading; the guide documents the create path, not an update path — UNVERIFIED (2026-10-20): the exact error on an update attempt.

---

## Questions to Ask Before Configuring

Each question traces to a gotcha in `references/gotchas.md`.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which object is the sync keyed on, and does it only mirror values from another object?" | A value one object retrieves from another moves only the source's SystemModstamp (gotcha 1) | A per-object watermark list, with mirrored values re-read from their source |
| "Who runs the migration insert, and which permission set carries 'Set Audit Fields upon Record Creation'?" | The Setup setting and the user permission are separate steps (gotcha 2) | A named migration user and a dated permission-set assignment |
| "Is the target object on the audit-fields object list, and is it custom or standard?" | The setting covers listed objects and custom objects only, and custom objects also need Modify All Data (gotcha 2) | A confirmed object list and the profile or permission set that holds Modify All Data |
| "Do you need only Recycle Bin rows, or archived activities too?" | `ALL ROWS` returns deleted records and archived activities (gotcha 3) | An explicit `IsDeleted = true` filter in the query |
| "How old are the deleted rows you want back?" | Items are scheduled for hard deletion after 15 days at an unguaranteed time, or at once on empty or hard delete (gotcha 4) | A recovery deadline and a scheduled backup query |
| "How large is the object, and which field does the filter hit?" | The default index list names SystemModstamp; the LastModifiedDate claim is UNVERIFIED (gotcha 5) | A measured query plan instead of an assumption |
| "Were audit dates already loaded wrong?" | The guide documents audit fields on create only, so a fix may need a re-insert or a custom field (gotcha 6) | A remediation choice agreed before any delete |

A proper configuration adds a named user, a dated permission, a per-object watermark and a recovery deadline, where "just doing it" gives dates that silently reset to the load time.

---

## Core Concepts

### SystemModstamp vs. LastModifiedDate

Both fields record when a record was last changed, but they track different scopes of change:

- **LastModifiedDate** is the "date and time when a user last modified this record" (object_reference 264 L2563). It reflects the last *intentional* edit.
- **SystemModstamp** is the "date and time when a user or automated process (such as a trigger) last modified this record"; "trigger" here means Salesforce code that implements standard functionality, not an Apex trigger (object_reference 264 L2566-2567, L2577). It is not a complete change log: a change to object B's field is reflected on B's SystemModstamp but not on object A that retrieves the value (L2581-2583). UNVERIFIED (2026-10-20): "SystemModstamp is always >= LastModifiedDate" and the list of workflow field updates / roll-up recalculations / approval stamps as advancing it — the guide states neither.

SystemModstamp is on the platform's default index list, with CreatedDate, Name and the record Id (salesforce_large_data_volumes_bp 264 L309, L404). L404 prints the bullet as "Systemmodstamp (LastModifiedDate)", so the guide does not say LastModifiedDate is unindexed — UNVERIFIED (2026-10-20): that a LastModifiedDate filter forces a full scan. The recommendation to filter on SystemModstamp for delta sync stands on the definition above (it covers automated changes) and on its place in the index list.

### Create Audit Fields

The "Set Audit Fields upon Record Creation" setting (Setup > User Interface, enabled together with "Update Records with Inactive Owners") plus the user permission of the same name lets API clients set the four audit fields when they create a record (object_reference 264 L2599-2603):

- `CreatedDate`
- `CreatedById`
- `LastModifiedDate`
- `LastModifiedById`

This is used during data migration to preserve historical timestamps and ownership from a source system. Step 2 is a Setup checkbox, not a Support case — the earlier "must be enabled by Salesforce Support" statement was CONTRADICTED by L2600-2601 and is removed. For custom objects the org must also be API enabled and the user must have "Modify All Data" (L3125). Not every standard object has all four fields; check the Enterprise WSDL (L2604). UNVERIFIED (2026-10-20): whether an update that sets these fields is rejected or silently ignored — the guide documents only the create path.

### IsDeleted and Soft Deletes

When a record is moved to the Recycle Bin, Salesforce sets `IsDeleted = true` on the record rather than physically removing it. The record remains queryable through two mechanisms:

- **SOQL**: `SELECT Id, Name FROM Account WHERE IsDeleted = true ALL ROWS`
- **REST API**: The `/services/data/vXX.0/queryAll/` endpoint (vs. the standard `/query/` endpoint; api_rest 264 L17247)

Deleted records stay in the Recycle Bin for 15 days; after that they are "scheduled for hard deletion" and Salesforce does not guarantee the exact time (salesforce_large_data_volumes_bp 264 L738-740; apex dev guide 264 L8358). The earlier "configurable up to 15 days" wording is removed — no corpus line makes the window configurable. `ALL ROWS` queries "all records in an organization, including deleted records and archived activities" and cannot be combined with `FOR UPDATE` (apex dev guide 264 L10124-10130). The REST guide states the query behaviour afterwards: QueryAll returns soft-deleted records, and "after these records are permanently removed from the recycle bin, you can no longer query them" (api_rest 264 L17232-17233).

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

**Why not LastModifiedDate:** SystemModstamp is defined to include changes by "a user or automated process" while LastModifiedDate is defined as a user's modification (object_reference 264 L2563, L2566), so a sync keyed on LastModifiedDate can miss automated changes. UNVERIFIED (2026-10-20): the specific example of a workflow field update advancing only SystemModstamp.

### Data Migration with Audit Field Preservation

**When to use:** Migrating records from a legacy system or another Salesforce org where you need to preserve the original creation date and creator.

**How it works:**

1. Confirm Create Audit Fields is enabled (Setup > User Interface > Enable "Set Audit Fields upon Record Creation"; object_reference 264 L2599-2601).
2. In your Data Loader or Apex script, include `CreatedDate`, `CreatedById`, `LastModifiedDate`, and `LastModifiedById` columns in the insert payload.
3. The user performing the insert must have the "Set Audit Fields upon Record Creation" user permission assigned via permission set.
4. Insert the records. The platform accepts the provided timestamps instead of auto-generating them.

**Why not post-insert update:** The guide documents setting audit fields on create only (object_reference 264 L2603). UNVERIFIED (2026-10-20): that the platform rejects a later DML update of these fields — plan the values before the insert.

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
| Incremental ETL / delta sync queries | SystemModstamp | On the default index list (large_data_volumes_bp 264 L404); covers user and automated changes (object_reference 264 L2566) |
| Display "last edited" to end users | LastModifiedDate | Reflects intentional human/API edits only |
| Audit trail of who last changed a record | LastModifiedById | Paired with LastModifiedDate for human-edit attribution |
| Preserve historical dates during migration | CreatedDate (with Create Audit Fields) | Set on create; needs the Setup setting and the user permission (object_reference 264 L2600-2602) |
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

1. **SystemModstamp does not capture every change** — CONTRADICTED and reversed: the earlier text said a parent change advances the child's SystemModstamp through a cross-object formula. The Object Reference says the opposite case holds: when object A retrieves values from object B, B's change shows on B's SystemModstamp but not on A's (object_reference 264 L2581-2583). A delta sync keyed on A will not see that change.
2. **Create Audit Fields is documented for create only** — the guide gives the create path (object_reference 264 L2603). UNVERIFIED (2026-10-20): whether an update of CreatedDate or CreatedById fails silently or throws, and whether any supported way exists to change them after creation.
3. **ALL ROWS includes archived activities** — it returns "deleted records and archived activities" (apex dev guide 264 L10124); Bulk API queryAll likewise returns archived Task and Event records (api_asynch 264 L6670-6671). If you only want Recycle Bin items, add `IsDeleted = true` as an explicit filter.
4. **SystemModstamp is on the default index list** (large_data_volumes_bp 264 L404, printed as "Systemmodstamp (LastModifiedDate)"). UNVERIFIED (2026-10-20): that a `LastModifiedDate >` filter is a full table scan — the guide does not say LastModifiedDate is unindexed.
5. **Bulk API queryAll is an operation, not a URL** — Bulk API query supports `query` and `queryAll`; queryAll returns records deleted by merge or delete plus archived Task and Event records (api_asynch 264 L6670-6671). REST uses the `/queryAll` URI (api_rest 264 L17247).

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

- `data/field-history-tracking` — Use when you need to track individual field value changes over time, not just the last modification timestamp.
- `security/field-audit-trail` — Use when compliance requires retaining field change history beyond the 18-month default archive window (api_meta 264 L46331-46332; Shield Field Audit Trail).
- `data/data-migration-planning` — Use for end-to-end migration planning including Create Audit Fields as one component.
- `data/soql-query-optimization` — Use for broader SOQL performance guidance beyond system field indexing.

---

## Official Sources Used

- Object Reference: System Fields — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/system_fields.htm
- Help: Set Audit Fields upon Record Creation — https://help.salesforce.com/s/articleView?id=sf.enable_set_audit_fields.htm
- REST API Developer Guide: queryAll — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/dome_queryall.htm
- SOQL Reference: ALL ROWS — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_all_rows.htm
