---
name: field-audit-trail
description: "Salesforce Shield Field Audit Trail: configuration, retention policies, querying archived field data, compliance requirements. NOT for field history tracking (use field-history-tracking) — use data/field-history-tracking."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "how do I retain field change history for more than 18 months in Salesforce"
  - "we need to prove which fields changed for a FINRA or HIPAA audit"
  - "how do I query FieldHistoryArchive in SOQL for archived field data"
  - "set up Shield Field Audit Trail to meet data retention requirements"
  - "field history tracking only keeps 18 months — how do I keep it longer"
tags:
  - field-audit-trail
  - shield
  - compliance
  - data-retention
  - archival
inputs:
  - "List of objects and fields that require long-term audit trail coverage"
  - "Compliance framework driving retention requirements (FINRA, HIPAA, GDPR, SOX, etc.)"
  - "Shield license confirmation (Field Audit Trail requires Salesforce Shield)"
  - "Required retention period for archived data (how long it must be kept before you delete it; the guides document no maximum)"
outputs:
  - "Field Audit Trail retention policy configuration decisions per object"
  - "SOQL query patterns for FieldHistoryArchive"
  - "Compliance evidence matrix mapping regulations to tracked fields"
  - "Review checklist for FAT activation and validation"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-11-19
---

# Field Audit Trail

This skill activates when a practitioner needs to configure Salesforce Shield Field Audit Trail (FAT) for long-term field-change retention, query archived field history via `FieldHistoryArchive`, or map compliance regulations (FINRA, HIPAA, GDPR, SOX) to FAT retention policies. It does NOT cover standard Field History Tracking — use the `field-history-tracking` skill for that.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Shield license:** Field Audit Trail is a Salesforce Shield feature. Confirm the org has Shield or the standalone Field Audit Trail add-on activated. Without it, the `FieldHistoryArchive` object does not exist and FAT policies cannot be defined.
- **Existing field history tracking:** Know which objects already have Field History Tracking enabled and how many fields are tracked per object. Without Field Audit Trail the cap is 20 tracked fields per object; with it, up to 200 (security guide 262 L4835-4838).
- **Retention requirement:** Identify the governing compliance framework and required retention period. Salesforce retains archived field history "until you delete it" (security guide 262 salesforce_security_impl_guide.txt L4836-4837); the guides document no 10-year maximum. When FAT is on, the default policy archives data after 18 months in production and after one month in sandboxes (262 L4881-4883). `archiveRetentionYears` is only a reminder for manual deletion; data is not automatically deleted (api_meta.txt L46348-46351).
- **Object eligibility:** FAT supports most standard objects (Account, Contact, Lead, Opportunity, Case, etc.) and custom objects. Not every object type is eligible — confirm the target objects against the supported-objects list in the security guide (262 L4840-4876). The guides document policy definition through Metadata API (`HistoryRetentionPolicy`, 262 L4833-4835) and enablement through your Salesforce representative (262 L4830); they document no Setup > Field Audit Trail page. UNVERIFIED (2026-11-19): whether a Setup UI exists for policies — not in the guides.

---

## Core Concepts

### What Field Audit Trail Is

Field Audit Trail is a Salesforce Shield feature that extends field-change history retention far beyond the standard 18-month limit of Field History Tracking. With FAT enabled and a retention policy set, field change data is archived into the `FieldHistoryArchive` sObject, where Salesforce keeps it until you delete it (security guide 262 L4836-4837). There is no documented maximum retention period; `archiveAfterMonths` controls only when data moves out of the History related list (1-18 months, api_meta.txt L46342-46346).

FAT captures: who changed a field, when, from what value, to what value — the same data as standard field history. The key difference is the storage backend and retention duration. Data older than the standard window migrates asynchronously to `FieldHistoryArchive`.

FAT is enabled by contacting your Salesforce representative, and retention policies are defined with Metadata API (`HistoryRetentionPolicy`, then deploy; security guide 262 L4830-4835). Querying archived data requires SOQL against `FieldHistoryArchive`.

### How FAT Differs from Standard Field History Tracking

| Dimension | Field History Tracking | Field Audit Trail |
|---|---|---|
| License | Included in all editions | Requires Salesforce Shield |
| Retention | Up to 18 months (24 months via the API) without FAT (262 L4553-4554) | Archived data kept until you delete it (262 L4836-4837) |
| Max fields per object | 20 | 200 (262 L4835-4838) |
| Storage location | Standard History sObjects (e.g., `AccountHistory`) | `FieldHistoryArchive` sObject |
| Query mechanism | Standard SOQL on History sObjects | SOQL on `FieldHistoryArchive` |
| Reports | Yes — History sObjects are reportable | No — `FieldHistoryArchive` is not available in Reports |
| Setup | Field History Tracking checkbox per object | `HistoryRetentionPolicy` per object, deployed through Metadata API (262 L4833-4835) |
| Async archival | N/A | Yes — data migrates to archive asynchronously |

Both can be active simultaneously. Standard history records remain in `XxxHistory` objects for their normal window; older records move to `FieldHistoryArchive`.

### Retention Policies

A FAT retention policy (`HistoryRetentionPolicy`, defined on the object and deployed with Metadata API; security guide 262 L4833-4835) controls when history leaves the object's History related list and goes to the archive, not how long it is kept:

- `archiveAfterMonths` (required): months to keep field history in Salesforce before archiving; minimum 1, maximum 18, default 18 (api_meta.txt L46342-46346).
- `archiveRetentionYears`: "the number of years until you manually delete data from the archive. Use this field as a reminder"; by default field history is not automatically deleted when FAT is enabled (api_meta.txt L46348-46351).
- `gracePeriodDays`: 0-10 days, default 1, applies only to the first archival (api_meta.txt L46354-46361).

Archived data stays in `FieldHistoryArchive` until you delete it; you can delete data that falls outside your policy window (262 L4836-4838). No maximum retention is documented. To satisfy a multi-year rule such as 6 or 7 years, record the period in `archiveRetentionYears`, leave the archive alone for that long, and put a manual deletion step in your runbook.

Retention policies are per object. If no custom policy is set, the default applies: archive after 18 months in production, after one month in sandboxes (262 L4881-4883). Set an explicit policy so the intent is on record.

### FieldHistoryArchive Object and Querying

`FieldHistoryArchive` is a read-only platform sObject available only to orgs with Shield. It stores archived field change records for all FAT-enabled objects in a unified table, distinguished by the `FieldHistoryType` field, which holds the name of the object that contains the field history (object_reference.txt L138499-138503, API 68.0).

Key fields on `FieldHistoryArchive`:

| Field | Description |
|---|---|
| `FieldHistoryType` | Name of the object that contains the field history, e.g. `"Account"` (restricted picklist of supported objects) |
| `Field` | Name of the field that was changed (the field ID if the field or object was deleted) |
| `ParentId` | Id of the record that was changed |
| `OldValue` | Value before the change |
| `NewValue` | Value after the change |
| `CreatedDate` | Timestamp of the change |

Query example — retrieving archived history for a specific Account:

```soql
SELECT ParentId, FieldHistoryType, Field, OldValue, NewValue, CreatedDate
FROM FieldHistoryArchive
WHERE FieldHistoryType = 'Account'
  AND ParentId = '001XXXXXXXXXXXX'
ORDER BY CreatedDate DESC
LIMIT 200
```

Query example — retrieving archived history for a specific field across all records:

```soql
SELECT ParentId, OldValue, NewValue, CreatedDate
FROM FieldHistoryArchive
WHERE FieldHistoryType = 'Contact'
  AND Field = 'ContactAnnualRevenue__c'
  AND CreatedDate >= 2022-01-01T00:00:00Z
ORDER BY CreatedDate ASC
```

**SOQL limitations on FieldHistoryArchive:** Not all fields are indexed for filtering. Filtering on `ParentId` and `CreatedDate` is efficient; filtering on `OldValue` or `NewValue` with a `WHERE` clause is an unindexed scan and will time out on large archives. Always anchor queries with `ParentId` or a bounded `CreatedDate` range.

---

## Common Patterns

### Pattern: Enabling FAT on High-Sensitivity Fields for Regulatory Compliance

**When to use:** The org must demonstrate to auditors (FINRA, HIPAA, SOX, GDPR) which users changed specific sensitive fields and when, over a multi-year period.

**How it works:**

1. Confirm Shield license is active.
2. Have Field Audit Trail enabled through your Salesforce representative (262 L4830); the guides do not document a Setup page for it.
3. Select the target object (e.g., Account, Contact).
4. Enable tracking for the required fields (up to 200 per object).
5. Define a `HistoryRetentionPolicy` for the object and deploy it with Metadata API: `archiveAfterMonths` (1-18) and `archiveRetentionYears` (e.g., 7 as the deletion reminder for a 7-year requirement; data is not deleted automatically).
6. Deploy the policy. Existing history already in the standard History sObject will migrate to `FieldHistoryArchive` asynchronously over the next several days.
7. Validate by querying `FieldHistoryArchive` after migration completes.

**Why not Field History Tracking alone:** Standard Field History Tracking caps at 18 months. For FINRA's 7-year requirement or HIPAA's 6-year PHI access log requirement, standard tracking is insufficient and creates compliance gaps.

### Pattern: Querying FieldHistoryArchive for Audit Evidence

**When to use:** Compliance team or legal counsel requires a point-in-time record of changes to a specific record or field set, pulled programmatically for an audit response.

**How it works:**

Use a bounded SOQL query filtered first on `FieldHistoryType` (the object) and `ParentId` (or a `CreatedDate` range), then process results in Apex or an external tool:

```apex
List<FieldHistoryArchive> archived = [
    SELECT ParentId, FieldHistoryType, Field, OldValue, NewValue,
           CreatedDate
    FROM FieldHistoryArchive
    WHERE FieldHistoryType = 'Opportunity'
      AND ParentId IN :opportunityIds
      AND CreatedDate >= :startDate
      AND CreatedDate <= :endDate
    ORDER BY CreatedDate ASC
    LIMIT 50000
];
```

Export to CSV or a Big Object for offline audit delivery. Because `FieldHistoryArchive` is not reportable, the only way to extract data for auditors is via SOQL (Apex, Data Loader, or Workbench).

**Why not use Reports:** `FieldHistoryArchive` is intentionally excluded from the Report Builder. Attempting to create a report against it will fail.

### Pattern: Combining Standard History and FieldHistoryArchive in a Single View

**When to use:** The org needs a complete timeline of changes — including recent changes (in the standard History sObject) and older changes (in `FieldHistoryArchive`) — for audit or analytics purposes.

**How it works:**

Query both `AccountHistory` (or the relevant History sObject) and `FieldHistoryArchive` separately, then merge and sort the results in Apex or the calling application:

```apex
// Recent history (standard)
List<AccountHistory> recent = [
    SELECT Field, OldValue, NewValue, CreatedById, CreatedDate
    FROM AccountHistory
    WHERE AccountId = :recordId
    ORDER BY CreatedDate DESC
];

// Archived history (FAT)
List<FieldHistoryArchive> archived = [
    SELECT FieldHistoryType, Field, OldValue, NewValue, CreatedDate
    FROM FieldHistoryArchive
    WHERE FieldHistoryType = 'Account'
      AND ParentId = :recordId
    ORDER BY CreatedDate DESC
];
```

Merge both result sets by `CreatedDate` in the calling layer. Deduplicate records that appear in both (overlap can occur during the migration window).

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Retention needed for 18 months or less | Standard Field History Tracking | No Shield required; fully reportable |
| Retention needed beyond 18 months | Shield Field Audit Trail with explicit `HistoryRetentionPolicy` | Archived data is kept until you delete it; no maximum is documented |
| Need to query archived field changes programmatically | SOQL against `FieldHistoryArchive` | Only supported query mechanism for archived data |
| Need to build a report showing historical field changes | Query `XxxHistory` sObjects (not FAT) or export via SOQL | `FieldHistoryArchive` is not in Report Builder |
| More than 20 fields need long-term tracking on one object | Shield FAT — up to 200 fields per object | Standard FHT hard-caps at 20 fields |
| Need to track a field not yet in Field History Tracking | Enable Field History Tracking AND FAT for that field | Both must be enabled for the field to be captured |
| Compliance regulation requires 7-year retention (FINRA) | FAT policy with `archiveRetentionYears` 7 and a manual-deletion runbook | `archiveRetentionYears` is a reminder only; nothing is deleted automatically |
| PHI access log retention under HIPAA | FAT policy with `archiveRetentionYears` of at least 6; do not delete archive data before then | HIPAA requires 6-year retention for access logs |

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

Run through these before marking FAT configuration work complete:

- [ ] Shield license confirmed as active in the org
- [ ] Target objects and fields identified against compliance requirements
- [ ] FAT enabled (through your Salesforce representative) and a `HistoryRetentionPolicy` deployed for all required objects
- [ ] Field selection per object does not exceed 200 tracked fields
- [ ] Explicit retention policies set — not relying on defaults
- [ ] `archiveRetentionYears` matches or exceeds the compliance minimum, and the manual deletion step is scheduled no earlier than that
- [ ] Standard Field History Tracking also enabled on same fields (required for FAT to capture data)
- [ ] `FieldHistoryArchive` queried in a sandbox to validate data is arriving
- [ ] Async migration window accounted for — existing history may take days to appear in archive
- [ ] Audit team briefed: reporting via `FieldHistoryArchive` requires SOQL, not Report Builder

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Field History Tracking is still required alongside FAT** — Enabling FAT does not automatically capture field changes. Field History Tracking must also be enabled on the same object and fields. FAT extends retention of the data that Field History Tracking captures; it is not a standalone capture mechanism. Missing this step means FAT policies are active but no data flows into the archive.

2. **Standard field history is still capped at 20 fields even with Shield** — Standard Field History Tracking remains limited to 20 fields per object even when FAT is licensed. With Field Audit Trail you can track up to 200 fields per object; without it, only up to 20 (262 L4835-4838). UNVERIFIED (2026-11-19): the guide gives only the 200-field and 20-field per-object figures; how the two limits interact per field is not documented. Plan field selection to stay under 200 per object.

3. **`FieldHistoryArchive` is not available in Reports or List Views** — Compliance teams that expect to build Salesforce Reports against archived data will be blocked. The only supported query mechanism is SOQL (Apex, Data Loader, Workbench, or external ETL). Plan for a SOQL-based audit extraction workflow.

4. **Archival is asynchronous — timing is not guaranteed** — When FAT is enabled or when existing records fall outside the standard retention window, migration to `FieldHistoryArchive` happens asynchronously in the background. There is no user-visible indicator of when migration completes. Do not perform compliance audits immediately after enabling FAT; allow several days for the backfill.

5. **Non-indexed field filters on `FieldHistoryArchive` cause query timeouts** — Filtering `FieldHistoryArchive` on `OldValue`, `NewValue`, or `FieldHistoryType` alone (without bounding on `ParentId` or `CreatedDate`) will trigger full-table scans on potentially billions of rows. Always include `ParentId` or a tight `CreatedDate` range as the primary filter. Salesforce may enforce query governor limits or time out the query with no result.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| FAT retention policy decisions | Per-object table mapping compliance regulation to required retention months and FAT policy settings |
| FieldHistoryArchive SOQL query set | Parameterized queries for audit extraction by record, field, date range |
| Compliance evidence matrix | Mapping of regulations (FINRA, HIPAA, GDPR, SOX) to specific tracked objects and fields |
| FAT activation checklist | Step-by-step enablement verification record |

---

## Related Skills

- `field-history-tracking` — Standard Salesforce Field History Tracking (18-month limit, 20 fields, included with all licenses). Use this skill instead when FAT is not licensed or short-term retention is sufficient.
- `data-archival-strategies` — Covers broader Salesforce data archival patterns including Big Objects, external archival, and storage management. Useful when FAT is part of a larger archival strategy.
- `data-quality-and-governance` — Covers data governance frameworks, validation rules, and audit trail design at the org level. Useful when designing the governance layer that FAT supports.
- `event-monitoring` — The other Shield feature; captures user activity and API events. Complement to FAT when the requirement includes user behavior audit (not just field changes).
- `security-health-check` — Use to assess the overall security posture of the org, including whether Shield features are configured appropriately.
