---
name: data-archival-strategies
description: "Use when planning how to archive aging Salesforce records to reduce storage costs, maintain query performance, and meet retention policies. Covers Big Object archival, external storage via Heroku or S3, field history truncation, recycle bin behavior, and soft-delete patterns. Triggers: storage limit reached, archive old records, Big Objects, field history too large, recycle bin overflow, data retention policy. NOT for finding out what is eating your storage right now — use data/data-storage-management. NOT for a scheduled job that just deletes aged records — use data/batch-data-cleanup-patterns."
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
  - "storage limit reached on my salesforce org"
  - "how do I archive old records in Salesforce"
  - "big objects for archival"
  - "field history is too large"
  - "recycle bin is affecting storage"
  - "data retention policy for salesforce records"
  - "move closed cases older than seven years into a big object and delete the originals"
  - "design the composite index for an archive big object so auditors can query it"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-10-19
---

# Data Archival Strategies

Use this skill when an org needs to move aging records off its main objects, for storage, query performance, or a retention policy, and has to choose where they go and how they come back. It does not cover migrating data to a new org (use `data/data-migration-planning`) or a delete-only retention job (use `data/batch-data-cleanup-patterns`).

---

## Before Starting

Gather this context before working on anything in this domain:

- The storage baseline from Setup > Storage Usage (data versus file storage, top objects). Storage allocations by edition and licence are covered in `data/data-storage-management`; read the org's own page rather than quoting a figure.
- The retention rule per object: how long records must stay queryable, who reads them, and whether a legal hold forbids deletion.
- Whether the org has Field Audit Trail (part of Shield) for field history retention beyond the standard window.
- The read questions auditors will ask of the archive ("all cases for this account in 2019"), because a big object can only be queried along its index.
- Whether archived records must stay visible in standard list views, detail pages, and reports; big objects support custom Lightning and Visualforce components instead of standard list views and detail pages.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "What exact questions will someone ask of the archive, and by which fields?" | A big object is queried along its index, and the index cannot be changed after deployment (Gotcha 7) | An index designed from retrieval questions, in the right field order |
| "Has anyone run the restore or audit query end to end before the source is deleted?" | The write path can work for months before anyone discovers the read path does not (Gotcha 2) | A tested read path, signed off before the first delete |
| "Is the goal storage, query speed, or both?" | Emptying the Recycle Bin helps queries but frees no storage, because Recycle Bin rows don't count against storage (Gotcha 3) | The right lever for the actual pain |
| "Do auditors need field-level change history for these records, and for how long?" | Deleting a record cascades to its field history; standard history is kept 18 months (24 via the API) unless Field Audit Trail is on (Gotcha 4) | A Field Audit Trail policy, or an export, in place before deletion |
| "What happens when an archive write half-fails?" | `insertImmediate` returns errors instead of throwing, and partial batch failures are expected (Gotcha 5) | A retry-the-whole-batch loop and a delete that only runs after a clean write |
| "Does the archive job do any other DML in the same transaction?" | Big object DML is treated as a callout, and callouts aren't allowed after DML in the same transaction (Gotcha 6) | An execute method that writes the big object first |
| "Is any source data encrypted with Shield Platform Encryption?" | Custom big objects don't support encryption; archived values are stored as clear text (Gotcha 8) | A decision on which fields may be archived at all |

A proper archival design adds a tested read path, an index built from real questions, and a delete step gated on verified writes; "export and delete" leaves the org with records nobody can retrieve and storage that did not move.

---

## Core Concepts

### What counts toward storage

| Data | Counts against data storage? | Source |
|---|---|---|
| Records in standard and custom objects | Yes | — |
| Records in the Recycle Bin | No; the bin has no item limit | LDV guide, Deleting Data |
| Field history tracking and Field Audit Trail data | No | Security guide, Field History Tracking |

Soft-deleted rows still affect query performance: they remain resident and have to be excluded from every query. Deleted items stay 15 days, then are scheduled for hard deletion with no guaranteed time.

### Big objects

| Behaviour | Detail |
|---|---|
| Editions | Enterprise, Performance, Unlimited, and Developer (Developer up to 1 million records); up to 100 big objects per org |
| Writes | `Database.insertImmediate()`; reinserting the same index values overwrites (upsert-like) and is idempotent; DML on big objects is treated as a callout and doesn't count toward the DML statement limit |
| Deletes | `Database.deleteImmediate()` or SOAP `deleteByExample()`, with every index field specified; 50,000 records per call |
| Index | Required fields only; no LongTextArea or URL; text fields in the index total at most 100 characters; cannot be edited after deployment |
| APIs | SOQL, Bulk API and Bulk API 2.0, Chatter, and SOAP only; the REST API isn't supported |
| Not supported | Triggers, flows, processes, the mobile app, sharing rules (object and field permissions only), standard list views and detail pages, encryption for custom big objects |

UNVERIFIED (2026-10-19): the 100-big-objects-per-org cap, DML treated as a callout and not counted toward the DML statement limit, SOAP `deleteByExample()`, and the list-view, detail-page, and encryption entries come from Big Objects Implementation Guide pages that are not in the Summer '26 PDF corpus. The corpus confirms the editions and Developer 1M cap, idempotent writes, the API list with REST unsupported, the index rules, and the unsupported triggers, flows, processes, mobile app, and sharing rules (Object Reference L3530-3700); `insertImmediate` partial success without an exception (Apex Reference L208300-208303); and the 50,000-record `deleteImmediate` batch limit (Apex Reference L206805).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- objects/Case_Archive__b.object (Metadata API format). Index fields must be required. -->
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <deploymentStatus>Deployed</deploymentStatus>
    <fields>
        <fullName>Account__c</fullName>
        <label>Account</label>
        <referenceTo>Account</referenceTo>
        <relationshipName>Case_Archives</relationshipName>
        <required>true</required>
        <type>Lookup</type>
    </fields>
    <fields>
        <fullName>Closed_Date__c</fullName>
        <label>Closed Date</label>
        <required>true</required>
        <type>DateTime</type>
    </fields>
    <fields>
        <fullName>Case_Number__c</fullName>
        <label>Case Number</label>
        <length>30</length>
        <required>true</required>
        <type>Text</type>
    </fields>
    <fields>
        <fullName>Subject__c</fullName>
        <label>Subject</label>
        <length>255</length>
        <required>false</required>
        <type>Text</type>
    </fields>
    <indexes>
        <fullName>CaseArchiveIndex</fullName>
        <label>Case Archive Index</label>
        <fields>
            <name>Account__c</name>
            <sortDirection>ASC</sortDirection>
        </fields>
        <fields>
            <name>Closed_Date__c</name>
            <sortDirection>DESC</sortDirection>
        </fields>
        <fields>
            <name>Case_Number__c</name>
            <sortDirection>ASC</sortDirection>
        </fields>
    </indexes>
    <label>Case Archive</label>
    <pluralLabel>Case Archives</pluralLabel>
</CustomObject>
```

### Field history

Without Field Audit Trail, field history is kept up to 18 months (24 months via the API), and up to 20 fields per object can be tracked. With Field Audit Trail, a `HistoryRetentionPolicy` deployed through Metadata API copies history into the `FieldHistoryArchive` big object and keeps it until you delete it; up to 200 fields per object can be tracked. By default the archive happens after 18 months in production and one month in sandboxes. Deleting a production record cascades to its history rows but not to the copy in `FieldHistoryArchive`. Field history can be deleted manually at any time.

---

## Common Patterns

### Pattern 1: Big object archive with a gated delete

1. Design the index from the audit questions; deploy the big object and a permission set (access is restricted by default).
2. Batch over the source with a selective `start` query (oldest closed records first).
3. In `execute`, build big object rows with trimmed index values, call `Database.insertImmediate()` before any sObject DML, and check every `SaveResult`; on any failure, retry the whole batch rather than picking out failures.
4. Delete source rows only for a fully written batch, then call `Database.emptyRecycleBin()` (10,000 records per call; it counts as a DML statement) if query performance on the source matters.
5. Before the first production delete, run the read path: a SOQL query on the index prefix and a Bulk API 2.0 query job for volume.

### Pattern 2: Soft archive on the same object

Add `Is_Archived__c` and filter it out of list views and queues when records must stay in standard reports. Storage does not change; only clutter and query scope do. Ask Support for a custom index if the flag must drive queries.

### Pattern 3: External archive

Move rarely read data to an external store when cost matters more than in-org access. Decide first how users will reach it (Salesforce Connect external object, a link, or an integration) and how lookups from active records will behave.

---

## Decision Guidance

| Situation | Recommended approach | Reason |
|---|---|---|
| Must stay queryable in Salesforce along known keys | Big object with an index built from the questions | Consistent performance at very large volume; stays on platform |
| Must stay in standard list views and reports | Soft archive flag on the source object | Big objects use custom components, not standard list views or detail pages |
| Rarely read, cost is the driver | External store | No Salesforce data storage used |
| Queries slow after a mass delete | Empty the Recycle Bin, or use Bulk API hard delete next time | Soft-deleted rows still affect queries |
| Storage alert after a mass delete | Do not count on emptying the Recycle Bin | Recycle Bin rows don't count against storage |
| Field changes must be kept beyond 18 months | Field Audit Trail retention policy | Standard history is kept up to 18 months (24 via the API) |
| Source fields are Shield-encrypted | Keep them out of custom big objects, or accept clear text | Custom big objects don't support encryption |

---

## Recommended Workflow

1. Fill `templates/data-archival-strategies-template.md` with the storage baseline, candidate objects, retention rules, and the read questions for each object.
2. Pick the destination per object with Decision Guidance; for big objects, write the `.object` file (or `objects/<Name>__b/` source folder) and a permission set.
3. Run `python3 skills/data/data-archival-strategies/scripts/check_data_archival_strategies.py --manifest-dir force-app/main/default` and fix every ERROR (index rules, required index fields, text length) before deploying; review WARN lines on field history tracking.
4. Build the archive batch from `references/examples.md`, and write Apex tests that mock the big object writes with the Stub API (tests write real big object data with no rollback).
5. In a full-copy sandbox, run the job on a sample, then run the read path (SOQL on the index prefix and a Bulk API 2.0 query job, as in `references/read-path-worked-example.md`) and have the data owner sign off.
6. Enable the production schedule with deletion gated on verified writes; re-check Storage Usage and source query plans after the next run.

---

## Review Checklist

- [ ] Every archived object has documented read questions, and the big object index matches them in field order
- [ ] The read path was executed against archived data before any source delete
- [ ] Index fields are required, contain no LongTextArea or URL, and text fields total 100 characters or less
- [ ] The archive job writes the big object before any sObject DML and retries failed batches whole
- [ ] Source deletion runs only after a fully successful write
- [ ] Field history needs were settled (Field Audit Trail policy or export) before deletion
- [ ] No Shield-encrypted field is written to a custom big object without sign-off
- [ ] Storage savings are measured against live records, not Recycle Bin contents

---

## Salesforce-Specific Gotchas

Full write-ups are in `references/gotchas.md`:

| # | Gotcha |
|---|---|
| 1 | Big object rows cannot be changed with standard DML |
| 2 | The read path is the part nobody tests until it is too late |
| 3 | Emptying the Recycle Bin helps queries, not storage |
| 4 | Deleting a record deletes its field history too |
| 5 | `insertImmediate` reports failures instead of throwing |
| 6 | Big object writes are callouts, so order matters in a transaction |
| 7 | A big object index is permanent and tightly constrained |
| 8 | Custom big objects store encrypted source data as clear text |
| 9 | Whitespace and nulls behave unexpectedly in big object writes |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Archival strategy | Destination per object with the read questions it must answer |
| Big object definition | `.object` file with fields and index, plus a permission set |
| Archive batch | Apex job with gated delete and retry |
| Read-path proof | The SOQL and Bulk API 2.0 queries run against archived data, with results |
| Filled template | `templates/data-archival-strategies-template.md` |

---

## Related Skills

- `data/data-storage-management` — finding what consumes storage and the allocation figures
- `data/batch-data-cleanup-patterns` — delete-only retention jobs
- `data/data-migration-planning` — moving data to a new org or loading from outside systems
- `data/data-quality-and-governance` — retention policy and data lifecycle governance
- `architect/limits-and-scalability-planning` — forecasting storage growth before limits are hit
- `architect/large-data-volume-architecture` — object-level volume strategy beyond archival
