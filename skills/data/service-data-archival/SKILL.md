---
name: service-data-archival
description: "Use this skill when Service Cloud orgs are consuming excessive data or file storage due to Case-related records, or when compliance requirements demand structured retention and deletion of case history. Trigger keywords: EmailMessage bloat, Email-to-Case storage, ContentDocument archival, case attachment cleanup, compliance retention policy, service storage optimization. NOT for generic data archival across non-Service objects — use data-archival-strategies instead. NOT for CPQ, Sales Cloud, or FSL record archival. NOT for purging custom object data unrelated to Cases."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "Our Email-to-Case volume is filling up data storage and storage costs are spiking — how do we archive or purge old EmailMessage records safely?"
  - "We need to comply with a data retention policy that requires deleting Case records older than seven years, but we're unsure of the right deletion order to avoid orphaning attachments"
  - "After archiving old Cases, our ContentDocument file storage didn't shrink — what did we miss?"
tags:
  - data-archival
  - email-message
  - content-document
  - case-management
  - storage
  - compliance
inputs:
  - Case data volume targets (record count and storage GB by object type)
  - Retention policies per record type (e.g., Cases closed > 7 years, EmailMessage > 2 years)
  - Compliance requirements and legal-hold lists (record IDs exempt from deletion)
  - Current storage thresholds from Setup > Storage Usage
outputs:
  - Archival strategy document scoped to Case-related objects
  - Deletion sequence script (SOQL + Bulk API ordering for Case, EmailMessage, ContentDocumentLink, ContentDocument)
  - Compliance checklist covering legal-hold exemptions and export-before-delete confirmation
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Service Data Archival

This skill activates when a Service Cloud org needs to reduce storage consumption or meet data retention obligations by archiving or deleting Case-related records — specifically EmailMessage, ContentDocument, and ContentDocumentLink records that accumulate from Email-to-Case workflows. It guides practitioners through the three dependent deletion sequences required to avoid orphaned records, storage leaks, and compliance violations.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm current data storage GB used and file storage GB used separately from Setup > Company Information > Storage Usage. EmailMessage records count against **data storage**; ContentDocument/ContentVersion records count against **file storage**. These are two separate storage pools with separate limits, and they require separate archival pipelines.
- Confirm whether any Cases or related records are under legal hold. Legal-hold records **cannot be bulk-deleted even via the API** — the platform enforces a hard block. Attempting to delete them in bulk without a hold exemption list will cause partial job failures that are difficult to recover from.
- Understand the cascade behavior gap: deleting a Case does **not** automatically delete its EmailMessage children or ContentDocumentLink junction records. Storage does not reclaim until all three object layers are explicitly deleted in the correct dependency order.

---

## Core Concepts

### EmailMessage as the Primary Data Storage Driver

In Service Cloud orgs that use Email-to-Case, `EmailMessage` records are typically the largest data storage consumer — often larger than the Case records themselves. Each inbound and outbound email thread creates one or more `EmailMessage` records stored as sObjects against data storage quota. Unlike file attachments, email bodies are stored as long text fields on the `EmailMessage` object, not as ContentDocument blobs. This means they consume data storage (the record-based quota), not file storage. Practitioners who look only at file storage GB when diagnosing storage overruns will miss the EmailMessage problem entirely.

`EmailMessage` records have a parent `CaseId` lookup. When a Case is deleted, the related `EmailMessage` records are **not automatically deleted** in all configurations — behavior depends on whether the delete operation cascades through child relationships. Do not assume cascade deletion will reclaim EmailMessage storage. Explicitly query and delete EmailMessage records by CaseId before or after Case deletion, and confirm row counts before and after.

### ContentDocument and ContentVersion — The Separate File Pipeline

File attachments on Cases (uploaded via the Chatter Files component or email attachments processed by Email-to-Case) are stored as `ContentDocument` (the file container) and `ContentVersion` (the versioned blob). The linkage between a Case and its files is managed by `ContentDocumentLink`, a junction object that associates a `LinkedEntityId` (the Case Id) with a `ContentDocumentId`.

Critically, a `ContentDocument` can be linked to **multiple entities** simultaneously. Deleting a `ContentDocumentLink` removes the association but does **not** delete the underlying `ContentDocument` or reclaim file storage. The `ContentDocument` is only deleted — and file storage is only reclaimed — when the `ContentDocument` record itself is deleted and no other `ContentDocumentLink` references remain. Any archival process that only deletes Cases and their `ContentDocumentLink` records will leave `ContentDocument` records as orphans: unlinked files that still consume file storage indefinitely.

Before deleting any `ContentDocument`, confirm it has no other `ContentDocumentLink` associations (e.g., linked to Accounts, Contacts, or Knowledge articles) to avoid destroying shared files.

### The Three Deletion Sequences and Dependency Order

Compliance-safe archival of Case data requires coordinating three deletion sequences in strict dependency order:

1. **Export and archive** — Before any deletion, export Case data, EmailMessage records, and ContentDocument/ContentVersion blobs to an external store (Big Objects, external database, or file export). This is the irreversible step. Do not skip this for records that fall within retention windows.
2. **ContentDocumentLink deletion** — Remove junction records linking Cases to ContentDocuments. This unlinks files from Cases without yet deleting the files.
3. **ContentDocument/ContentVersion deletion** — Delete ContentDocument records that are now fully unlinked (no remaining ContentDocumentLink references). This reclaims file storage.
4. **EmailMessage deletion** — Delete EmailMessage records by CaseId. This reclaims data storage.
5. **Case deletion** — Delete the Case records. Note: in some configurations, Case deletion may cascade-delete EmailMessage children. If it does, the EmailMessage step above can be skipped, but verify this in a sandbox first. Never assume cascade behavior.

Legal-hold exemptions must be filtered out at each sequence step via an exclusion list of record IDs or a custom `Legal_Hold__c` field checked in SOQL WHERE clauses.

### Salesforce Archive Feature

Salesforce offers a **Legacy Salesforce Archive** feature (available in some editions) that can move records to archive storage with reduced cost. This feature does not replace the deletion sequences above — archived records still occupy storage until they are purged from the archive tier. Retention policies can be configured through the Archive feature to automate record movement, but the feature requires explicit enablement and configuration; it is not on by default. Evaluate the Archive feature as a complement to bulk deletion, not a substitute.

---

## Common Patterns

### Pattern: Phased Compliance Archival with Export-Before-Delete

**When to use:** Org has a formal data retention policy (e.g., Cases closed more than 7 years ago must be deleted; Cases closed within 7 years must be retained). Legal team requires an audit trail of what was deleted and when.

**How it works:**
1. Query Cases meeting the retention threshold: `SELECT Id FROM Case WHERE IsClosed = true AND ClosedDate < LAST_N_YEARS:7 AND Legal_Hold__c = false`.
2. For each Case batch, query and export EmailMessage records, ContentDocumentLink records, and ContentDocument/ContentVersion records to an external store.
3. Delete ContentDocumentLink records for the target Cases (only where ContentDocument has no other links).
4. Delete now-orphaned ContentDocument records.
5. Delete EmailMessage records by CaseId.
6. Delete Case records.
7. Run a post-deletion storage report (Setup > Storage Usage) and compare to the pre-deletion baseline.

**Why not the alternative:** Deleting Cases directly without the preparatory steps leaves ContentDocument orphans consuming file storage silently, and may leave EmailMessage records depending on cascade behavior. There is no bulk undo — once deleted, records are gone from the recycle bin after 15 days.

### Pattern: EmailMessage-Only Purge for Storage Relief

**When to use:** Data storage is near the limit due to Email-to-Case volume but there is no compliance requirement to delete Cases. The org wants to reduce storage cost without touching Case records.

**How it works:**
1. Query EmailMessage records older than the retention threshold: `SELECT Id, CaseId FROM EmailMessage WHERE CreatedDate < LAST_N_YEARS:2 AND Incoming = true`.
2. Filter out records associated with open Cases or Cases under legal hold.
3. Export the EmailMessage bodies to an external store or Big Object if archival is required.
4. Delete EmailMessage records via Bulk API 2.0 in batches of up to 10,000 records per job.

**Why not the alternative:** Deleting Cases to eliminate EmailMessage storage is disproportionate — it removes the case history, service metrics, and SLA records. An EmailMessage-only purge reduces storage without losing the Case audit trail.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Storage overrun is primarily data storage (EmailMessage bloat) | EmailMessage-only purge via Bulk API 2.0 | Targeted; preserves Case history; fastest storage reclaim |
| Storage overrun is primarily file storage (ContentDocument) | ContentDocument orphan cleanup after verifying no other links | File storage reclaim requires ContentDocument deletion, not just ContentDocumentLink removal |
| Compliance-driven deletion of Cases and all child records | Phased export-then-delete in dependency order: export → ContentDocumentLink → ContentDocument → EmailMessage → Case | Avoids orphaned records; provides audit trail; satisfies legal hold requirements |
| Records under legal hold mixed into archival batch | Filter legal-hold records from all SOQL queries via exclusion list or custom field | Platform blocks deletion of legal-hold records; partial failures corrupt Bulk API jobs |
| Org uses Salesforce Archive feature | Configure retention policies in Archive setup; complement with deletion of purge-eligible archive records | Archive moves records to lower-cost tier; explicit purge still required to reclaim storage |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Audit current storage usage by object type** — Run Setup > Storage Usage and note data storage GB and file storage GB separately. Use SOQL aggregate queries (`SELECT COUNT(Id), SUM(BodyLength) FROM EmailMessage` and `SELECT COUNT(Id) FROM ContentDocument`) to quantify record counts by object. Identify the primary storage driver before prescribing a solution.
2. **Define retention policies per record type** — Work with the legal and compliance team to produce a retention matrix: minimum retention period per object (Case, EmailMessage, ContentDocument), legal-hold criteria, and export-before-delete requirements. Document which Cases are in-scope for archival.
3. **Export and archive ContentDocument/ContentVersion and EmailMessage records before deletion** — For all in-scope records, export blobs and metadata to an external store (e.g., S3, Big Objects, or a compliance archive). Confirm exports are complete and checksummed before proceeding to deletion. This step is irreversible once deletion completes.
4. **Execute deletion in dependency order using Bulk API 2.0** — Delete in this sequence: (a) ContentDocumentLink records for in-scope Cases where ContentDocument has no other links, (b) now-orphaned ContentDocument records, (c) EmailMessage records by CaseId, (d) Case records. Each step must exclude legal-hold records. Use Bulk API 2.0 for volumes above 200 records to avoid hitting DML governor limits.
5. **Validate with storage report and orphan scan** — After deletion, re-run Setup > Storage Usage and compare to the pre-deletion baseline to confirm storage reclaim. Run the `check_service_data_archival.py` script to scan for orphaned ContentDocumentLink records (links pointing to deleted Cases), orphaned ContentDocument records (no remaining links), and any remaining EmailMessage records for deleted Cases.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Data storage GB and file storage GB baseline documented before any deletion
- [ ] Retention policy matrix confirmed with legal/compliance team and documented
- [ ] Legal-hold record IDs identified and excluded from all SOQL queries
- [ ] Export-before-delete confirmed for all records within retention windows
- [ ] Deletion executed in dependency order: ContentDocumentLink → ContentDocument → EmailMessage → Case
- [ ] Post-deletion storage report run and delta confirmed
- [ ] Orphaned ContentDocumentLink and ContentDocument records scanned with checker script
- [ ] Recycle bin monitored for 15 days before treating deletion as final

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **EmailMessage deletion does not cascade to ContentDocumentLink** — Deleting an EmailMessage that had attachments does not delete the ContentDocumentLink records or ContentDocument records created when the attachment was processed. These remain as orphans and continue to consume file storage. Always run a ContentDocumentLink query after EmailMessage deletion to catch stranded links.
2. **Archived Cases still consume storage if attachments are not separately archived** — If you use the Salesforce Archive feature to move Cases off the active tier, the ContentDocument records linked to those Cases remain in the active file storage pool unless the Archive is explicitly configured to include file objects. Many implementations assume Archive = storage reclaim, but file storage is unaffected until ContentDocument records are explicitly deleted or moved.
3. **Legal-hold records cannot be bulk-deleted even via the API** — The platform enforces a hard deletion block on records flagged as under legal hold. Including even one legal-hold record in a Bulk API 2.0 delete job causes the entire batch containing that record to fail with a non-retriable error. Pre-filter legal-hold records at the SOQL level, not in post-processing, to prevent cascading batch failures across large jobs.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Archival strategy document | Scoped to Case/EmailMessage/ContentDocument objects; includes retention matrix, legal-hold list, and estimated storage reclaim |
| Deletion sequence script | SOQL queries and Bulk API 2.0 job definitions in dependency order; parameterized by retention date threshold |
| Compliance checklist | Pre-deletion export confirmations, legal-hold exclusions, post-deletion storage delta, orphan scan results |

---

## Related Skills

- `data-archival-strategies` — use for generic multi-object archival strategy across non-Service objects, Big Object design, and org-wide storage governance
- `data-storage-management` — use for diagnosing storage limits, understanding storage allocation, and storage alert response
- `case-history-migration` — use when migrating Case history across orgs, not for in-place archival or deletion
