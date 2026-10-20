---
name: data-storage-management
description: "Salesforce storage management: monitoring data storage vs file storage usage, diagnosing storage alerts, optimizing large text fields, choosing between Attachment and ContentDocument (Files), and planning storage reclamation. NOT for archiving aging records to Big Objects or external storage (S3, Heroku) — use data/data-archival-strategies. NOT for Case and EmailMessage storage bloat in Service Cloud — use data/service-data-archival."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
triggers:
  - "our org is approaching the data storage limit and we need to free up space"
  - "Salesforce sent a storage alert email at 75 percent capacity"
  - "how do I check which objects are consuming the most storage in our org"
  - "should we use Attachments or Files for user uploaded documents"
  - "large text area fields are inflating our storage usage unexpectedly"
  - "how do I calculate how much storage each object is using in Salesforce"
  - "we're having issues with storage management"
tags:
  - storage-management
  - data-storage
  - file-storage
  - contentdocument
  - storage-optimization
  - large-data-volumes
inputs:
  - "Current org edition (Enterprise, Unlimited, Developer)"
  - "Number of active user licenses"
  - "Current storage usage breakdown from Setup > Storage Usage"
  - "List of high-volume objects or file upload patterns in the org"
outputs:
  - "Storage type breakdown (data vs file) with per-object analysis"
  - "Prioritized list of storage reclamation actions"
  - "Recommendation on Attachment vs ContentDocument for the use case"
  - "Large text area field optimization strategy"
  - "Storage monitoring and alerting plan"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Data Storage Management

This skill activates when an org is approaching storage limits, receiving storage alert emails, or when a practitioner needs to understand how Salesforce allocates and measures data storage vs file storage. It covers monitoring, diagnosis, reclamation, and field-level optimization. It does NOT cover offloading files to external systems such as S3 or Heroku — use the data-archival-strategies skill for those patterns.

---

## Before Starting

Gather this context before working on anything in this domain:

- Navigate to **Setup > Storage Usage** and note the current data storage usage (GB used / GB allocated) and file storage usage separately. Export or screenshot the per-object breakdown.
- Confirm the org edition. Enterprise orgs receive 10 GB base data storage + 20 MB per user license and 10 GB base file storage + 2 GB per user license. Unlimited orgs receive more generous per-user additions. UNVERIFIED (2026-10-20): the allocation figures are Salesforce Help only; a grep of all 14 corpus files for them returns nothing, and sfdx_dev 264 L3750-3751 only points to the Help article "Data and File Storage Allocations". Read the real numbers from Setup > Storage Usage.
- Check whether a large delete or data load ran recently. Storage is recalculated asynchronously, so the Storage Usage page may simply not have caught up (UNVERIFIED (2026-10-20): the asynchronous recalculation is Salesforce Help only; no corpus file states it). The Recycle Bin is not a contributor: "items in the Recycle Bin don't count against an org's storage usage" (salesforce_large_data_volumes_bp 264 L736-737), so do not budget for reclaiming anything by emptying it.
- Confirm whether Big Objects are in use. Big Objects have their own separate storage allocation and do NOT consume regular data storage quota. UNVERIFIED (2026-10-20): the separate Big Object allocation is Help-only; salesforce_large_data_volumes_bp 264 L94-95 and object_reference 264 L3605-3610 describe big objects as the home for archived and massive data but state no allocation.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Which pool is at the threshold, data or file, and what does Setup > Storage Usage show per object? | Gotcha 1 and Anti-pattern 2: the two pools are separate and the fix differs | The pool, the top five consumers, and the screenshot to diff against after cleanup |
| Did a large delete or load run in the last day or two? | Gotcha 1: Help says storage recalculates asynchronously, so the number may still be settling | Rules out a false alarm before anyone deletes more data |
| Is anyone proposing to empty the Recycle Bin or run a hard delete to "free space"? | Gotcha 1: bin records do not count against storage (ldv L736-737) and hard delete cannot be undone | Stops an irreversible step that frees nothing |
| Do tracked-history objects appear in the top consumers, and was that assumed to be the cause? | Gotcha 4: field history data does not count against data storage (secguide 262 L4555-4556) | Removes a wrong suspect and points the investigation at the real consumers |
| Which file pattern is in use: Attachment, ContentDocument, or Chatter files? | Pattern: Preventing Duplicate File Storage; Attachments duplicate binaries per parent | Migration candidates and an estimate of duplicate bytes |
| Does the user running the orphan query hold Query All Files? | The orphan subquery is unfiltered (object_reference 264 L77253-77254) | Whether the cleanup query can run at all, and as whom |
| Who owns the Limits API alert, and at what remaining percentage does it fire? | Workflow step 6: built-in alerts are a lagging safety net (the alert levels themselves are UNVERIFIED) | A named owner, a threshold, and a place the alert lands |

A proper configuration adds a monitored threshold, a retention rule per high-volume object and a cleanup runbook that names the irreversible steps, instead of reacting to the next alert email.

---

## Core Concepts

### Data Storage vs File Storage

Salesforce measures two distinct pools of storage:

**Data storage** counts every standard and custom object record. The platform allocates roughly 2 KB per record on average, though records with many Long Text Area fields can consume significantly more. Every record in every object — including junction objects, feed items, and task/event records — contributes to the data storage total. UNVERIFIED (2026-10-20): the 2 KB average and the list of contributing objects are Help-only (grep "2 KB" across the corpus finds no storage figure). **Field history tracking data is the exception, and an earlier version of this skill had it backwards:** "Field history tracking data doesn't count against your data storage limits" (secguide 262 L4555-4556; repeated at secguide 262 L4634-4635 and, with Field Audit Trail, L4755-4756).

**File storage** counts the binary content of files: ContentDocument (Salesforce Files), legacy Attachment records, Documents in the Documents tab, and Chatter post attachments. Each ContentVersion (a version of a File) contributes its full byte size to file storage. Thumbnail previews and renditions generated by Salesforce also consume file storage. UNVERIFIED (2026-10-20): which record types count toward file storage, and that renditions count, are Help-only; no corpus file says either (grep "rendition" finds only the Connect API preview samples, apexdev 264 L24584-24613).

For Enterprise edition:
- Data storage: **10 GB base + 20 MB per user license**
- File storage: **10 GB base + 2 GB per user license**

These allocations are org-wide shared pools. There is no per-user or per-object quota. (UNVERIFIED (2026-10-20): same Help-only source as the figures above.)

### Monitoring Storage Usage

The canonical monitoring path is **Setup > Storage Usage**. This page shows:
- Total data storage used vs allocated, broken down by object type
- Total file storage used vs allocated, broken down by ContentDocument, Attachment, Document, etc.

For programmatic monitoring, use the **Limits API** (`GET /services/data/vXX.0/limits/`, api_rest 264 L7917) which returns `DataStorageMB` and `FileStorageMB` (api_rest 264 L8191, L8193; the API user needs the Manage Users permission) with `Max` and `Remaining` values (api_rest 264 L2163-2174). This is the recommended approach for automated alerting pipelines.

Salesforce sends automated email alerts to system administrators at **75%, 90%, and 100%** of storage capacity for both data and file storage pools independently. UNVERIFIED (2026-10-20): the alert thresholds are Help-only; the only corpus hit for "75%" is Apex test coverage.

### ContentDocument (Files) vs Attachments

The legacy `Attachment` sObject is tied one-to-one to a parent record. If the same file needs to be associated with multiple records, it must be duplicated — each copy consuming full file storage. Attachments cannot be shared. The one-parent shape is grounded: Attachment "represents a file that a User has uploaded and attached to a parent object" (object_reference 264 L43853); "cannot be shared" is UNVERIFIED (2026-10-20) (Help-only).

`ContentDocument` (Salesforce Files) with `ContentDocumentLink` is the modern replacement. A single ContentDocument can be linked to multiple records via ContentDocumentLink records without duplicating the binary content. This is a critical distinction for orgs that attach the same reference documents (contracts, product specs) to many records.

Prefer ContentDocument for all new file upload patterns. Migrate Attachments to ContentDocument when reclaiming file storage — but plan the migration carefully since it touches sharing, Apex triggers, and API integrations that reference the Attachment sObject.

### Large Text Area Fields and Data Storage

Long Text Area and Rich Text Area fields count toward data storage based on their actual content length, not the field's maximum size. An empty Long Text Area field on a record does not consume the maximum 131,072 characters of storage. However, records with dense Rich Text Area content (heavy formatting markup) can push individual record sizes well above the 2 KB average. UNVERIFIED (2026-10-20): length-based accounting and the 131,072-character Long Text Area maximum are Help-only — the only corpus hit for 131072 is the Bulk API "maximum number of characters in a field" (cheatsheet 264 L403), which is a Bulk API limit, not the field-type maximum.

Rich Text Area fields that store embedded images move those image bytes into file storage, not data storage — the field stores a reference. This is a non-obvious split that can cause confusion when diagnosing storage usage. UNVERIFIED (2026-10-20): Help-only; no corpus file describes where inline rich-text images are stored.

### Recycle Bin and Storage Reclamation

Two claims circulate about this and both are wrong. Check them against the Large Data Volumes guide before acting on a storage incident.

- **Standard delete puts records in the Recycle Bin for 15 days**, during which they can be restored (salesforce_large_data_volumes_bp 264 L738). Records in the Recycle Bin **do not count against the org's storage usage** ("items in the Recycle Bin don't count against an org's storage usage", salesforce_large_data_volumes_bp 264 L736-737), and there is no cap on how many deleted records the bin holds (L737). So emptying the bin is not a storage-reclamation lever; it is a *recoverability* decision, and an irreversible one.
- **Bulk API hard delete does not go to the Recycle Bin at all.** That is the definition of the operation: "the deleted records aren't stored in the Recycle Bin. Instead, they become immediately eligible for deletion" (api_asynch 264 L1630-1632), so there is no bin copy to restore. There is no 30-day (or any) window in which a hard delete can be undone. Anyone told otherwise will authorise a hard-delete job believing it is reversible. The "Bulk API Hard Delete" permission is disabled by default and an administrator must enable it (api_asynch 264 L1633-1634).

Why storage still looks unchanged after a mass delete: **storage is recalculated asynchronously.** Salesforce Help states that after adding or removing a large number of records or files, "the change in your org's storage usage isn't reflected immediately." (UNVERIFIED (2026-10-20): Help-only quote, no corpus file holds it.) Wait and re-check Setup > Storage Usage rather than reaching for the Recycle Bin.

Programmatic reclamation: `Database.emptyRecycleBin(List<Id>)` in Apex permanently removes records from the bin (you can "manually empty the Recycle Bin by using the UI, the API, or Apex", salesforce_large_data_volumes_bp 264 L738-739; example call at apexdev 264 L17676). A plain REST `DELETE /services/data/vXX.0/sobjects/{SObjectType}/{id}` is an ordinary delete — the record goes to the bin like any other (an earlier version of this skill said it permanently deletes with `?allOrNone=false`; `allOrNone` belongs to Composite and sObject Collections requests, api_rest 264 L5900-5901, not to the single-record DELETE). For bulk reclamation, use the Bulk API with the hardDelete operation (api_asynch 264 L1630-1632).

---

## Common Patterns

### Pattern: Storage Usage Triage After Alert

**When to use:** Org has received a 75%, 90%, or 100% storage alert email and the administrator needs to identify what is consuming storage and what can be safely reclaimed.

**How it works:**
1. Open Setup > Storage Usage. Note the top 5 objects by data storage consumption.
2. For each high-volume object, check whether records in it have a defined retention need. Common candidates for cleanup: Task/Event records older than 2 years, ContentVersion records from deleted parent records (orphaned files), EmailMessage records.
3. Rule out asynchronous recalculation before diagnosing further — if a large delete or load ran recently, the page may not have caught up. Do not reach for the Recycle Bin: bin records do not count against storage, so emptying it frees nothing and destroys the 15-day restore window.
4. Query orphaned ContentDocuments: `SELECT Id FROM ContentDocument WHERE Id NOT IN (SELECT ContentDocumentId FROM ContentDocumentLink)`. The subquery has no filter on `ContentDocumentId`, `LinkedEntityId` or `Id`, so from API 59.0 it needs the Query All Files permission, which itself requires View All Data (object_reference 264 L77253-77254). Files this finds have no linked records and can be deleted after review.
5. For large Attachment volumes, evaluate migration to ContentDocument to enable deduplication via ContentDocumentLink.

**Why not skip the triage:** Deleting records from the wrong object or time range can break business processes. Triage first, delete second.

### Pattern: Preventing Duplicate File Storage via ContentDocumentLink

**When to use:** Multiple records need access to the same file (e.g., a standard contract template linked to every Opportunity).

**How it works:**
- Create the ContentDocument once (via ContentVersion insert).
- Create one `ContentDocumentLink` record for each parent record that needs access.
- Each ContentDocumentLink costs ~2 KB of data storage (it is a record), but the file binary is stored only once in file storage.

**Why not use Attachments:** Every Attachment is an independent binary copy tied to one parent. 1,000 Opportunities each with the same 500 KB contract template = 500 MB of file storage. The same pattern using ContentDocumentLink = 500 KB of file storage + ~2 KB × 1,000 = ~2 MB data storage. The saving is roughly 250x.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New file upload feature for user documents | ContentDocument (Files) | Reusable across records via ContentDocumentLink, supports versioning, previews, sharing |
| Existing Attachment volume causing file storage alert | Audit for duplicates, migrate to ContentDocument | ContentDocumentLink eliminates binary duplication |
| Data storage alert, top object is Task/Event | Archive or delete old activity records | Activities accumulate rapidly; 2+ year old records rarely queried |
| Data storage alert, top object is custom log/audit table | Evaluate Big Object migration for append-only history | Big Objects do not consume regular data storage (UNVERIFIED (2026-10-20), Help-only; see Before Starting) |
| Need to check storage programmatically in a CI pipeline | Query Limits API (`/services/data/vXX.0/limits/`) | Returns DataStorageMB and FileStorageMB with Max/Remaining |
| Records deleted but storage not freed | Wait and re-check Setup > Storage Usage | Storage is recalculated asynchronously; Recycle Bin records do not count against storage, so emptying it will not move the number |
| Rich Text Area fields suspected of high storage usage | Audit for embedded base64 images in field content | Dense markup and inline images inflate the record; prefer ContentDocument links (where inline images are stored is UNVERIFIED (2026-10-20), see Core Concepts) |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Gather current state** — Open Setup > Storage Usage and record the current data storage used/allocated and file storage used/allocated. Note the top 5 objects by consumption in each pool. Confirm org edition and license count to understand the total allocation formula.
2. **Rule out asynchronous recalculation** — If a large delete or load ran recently, the Storage Usage page may simply not have caught up; Salesforce recalculates storage asynchronously. Re-check before diagnosing further. Do NOT empty the Recycle Bin as a reclamation step: bin records do not count against storage, so it frees nothing, and it destroys the 15-day restore window for everything in there.
3. **Identify orphaned ContentDocuments** — Run `SELECT Id, Title, ContentSize FROM ContentDocument WHERE Id NOT IN (SELECT ContentDocumentId FROM ContentDocumentLink)` in the Developer Console or Workbench. Delete orphans in batches using Bulk API hardDelete.
4. **Assess high-volume objects** — For the top data storage consumers, determine: (a) whether a retention policy allows deletion of old records, (b) whether the object is a candidate for Big Object archival, and (c) whether Large Text Area fields with embedded content are inflating sizes beyond the 2 KB average.
5. **Evaluate Attachment-to-ContentDocument migration** — If Attachments appear in the top file storage consumers, query for duplicate content (same ParentId pattern or same file name across many records). Plan migration using ContentVersion + ContentDocumentLink to eliminate binary duplication.
6. **Set up monitoring** — Implement an automated check using the Limits API. Alert when `DataStorageMB.Remaining / DataStorageMB.Max` drops below 25%. Salesforce's built-in alerts (75%, 90%, 100%) are a safety net, not a proactive monitoring strategy.
7. **Validate and document** — After reclamation actions, refresh Setup > Storage Usage to confirm the reduction. Document which objects were cleaned, how many records deleted, and the storage reclaimed. Update retention policies if none existed.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Setup > Storage Usage reviewed and per-object breakdown captured
- [ ] Asynchronous recalculation ruled out after any recent large delete or load
- [ ] Orphaned ContentDocuments queried and deleted (or confirmed none exist)
- [ ] Attachment vs ContentDocument decision documented for any new file feature
- [ ] Limits API monitoring confirmed or set up (alert threshold ≤25% remaining)
- [ ] Big Object suitability assessed for any high-volume append-only objects
- [ ] No Rich Text Area fields storing embedded base64 images directly in field content

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Recycle Bin records do NOT count toward storage, and hard delete is not recoverable** — Two widely-repeated beliefs, both wrong. Records in the Recycle Bin don't count against the org's storage usage and the bin has no record-count cap (salesforce_large_data_volumes_bp 264 L736-737); the 15-day figure is a *restore* window, not a storage-accounting window. And Bulk API hard delete bypasses the bin entirely — immediate, permanent, no undo, no 30-day grace. Storage that hasn't dropped after a mass delete is almost always asynchronous recalculation, which resolves on its own (UNVERIFIED (2026-10-20): Help-only, no corpus line).
2. **Big Objects do NOT consume regular data storage** — Practitioners planning to migrate log or audit records to Big Objects to "free up" storage will succeed — Big Objects have their own separate, larger allocation and are entirely independent of the standard data storage pool. UNVERIFIED (2026-10-20): Help-only, see Before Starting.
3. **ContentVersion renditions consume file storage** — When a ContentDocument is uploaded, Salesforce auto-generates preview thumbnails and PDF renditions. These renditions are stored as additional ContentVersion records and count toward file storage. An org with millions of small uploaded files can see file storage inflated 2–3x by renditions alone. UNVERIFIED (2026-10-20): renditions as counted ContentVersion records and the 2–3x figure are Help/field experience only; no corpus file states either.
4. **Field History Tracking records do NOT count toward data storage** — Every tracked field change creates a history record, and high-volume objects can accumulate millions of them, but "field history tracking data doesn't count against your data storage limits" (secguide 262 L4555-4556, L4634-4635). Retention without Field Audit Trail is up to 18 months in the UI and up to 24 months via the API (secguide 262 L4553-4554). Do not list history objects as a storage-reclamation target; see data/field-history-tracking.
5. **Chatter attachments count toward file storage, not data storage** — Files attached directly to Chatter posts (FeedAttachment) are stored as ContentDocument records and count against file storage. They are not counted in data storage. Orgs with heavy Chatter usage should monitor file storage, not just data storage. UNVERIFIED (2026-10-20): which pool Chatter files count against is Help-only; no corpus line assigns FeedAttachment or Chatter files to a storage pool.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Storage usage summary | Per-object data storage breakdown from Setup > Storage Usage, captured at point-in-time |
| Reclamation action plan | Prioritized list of delete/archive/migrate actions with estimated storage freed per action |
| Orphaned ContentDocument query | SOQL query and results identifying files with no ContentDocumentLink records |
| Limits API monitoring snippet | Apex or script to poll DataStorageMB and FileStorageMB and alert below threshold |
| Attachment migration plan | Assessment of Attachment volume, duplicate patterns, and ContentDocument migration approach |

---

## Related Skills

- data/data-archival-strategies — use when records need to be removed from the active org but retained for compliance; covers Big Objects, external archival, and MuleSoft/Heroku offload patterns
- data/batch-data-cleanup-patterns — use when planning large-scale record deletion or data quality cleanup that will reclaim storage
- architect/limits-and-scalability-planning — use when designing new data models and need to project storage growth over time before it becomes a problem
