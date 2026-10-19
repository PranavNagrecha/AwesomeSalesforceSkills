---
name: data-migration-planning
description: "Use when planning, reviewing, or troubleshooting a Salesforce data migration — covering tool selection (Data Loader, Bulk API 2.0, MuleSoft, Informatica, Jitterbit), migration sequencing for parent-child objects, external ID strategy for upsert idempotency, validation rule bypass, trigger and flow suppression, rollback planning, and post-migration reconciliation. NOT for Data Loader step-by-step mechanics — use admin/data-import-and-management. NOT for schema or data model design — use data/data-model-design-patterns."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Security
  - Performance
triggers:
  - "how do I migrate Account and Contact records from our legacy CRM to Salesforce without losing relationships"
  - "my data migration is creating duplicate records every time I re-run the load job"
  - "validation rules are rejecting records during migration even though I am loading as a system admin"
  - "what order do I load parent and child objects when migrating Opportunities and their line items"
  - "how do I roll back migrated records if something goes wrong mid-load"
  - "owner assignment is failing during migration because some users are inactive"
  - "keep the original created dates from the legacy system when loading records"
  - "reference parent accounts by legacy ID in the contact load file instead of Salesforce IDs"
tags:
  - data-migration
  - etl
  - bulk-api
  - data-loader
  - external-id
  - upsert
  - migration-sequencing
  - validation-bypass
  - rollback
inputs:
  - "Source system type (legacy CRM, ERP, spreadsheets) and approximate record volumes per object"
  - "Object list with relationship types (lookup vs master-detail) and cardinality"
  - "Available tooling (Data Loader, Bulk API 2.0, MuleSoft, Informatica, Jitterbit, or custom)"
  - "Existing validation rules, triggers, and flows that may fire during load"
  - "User list for owner assignments and their active/inactive status"
  - "Rollback tolerance (hard cutover vs parallel run vs incremental)"
outputs:
  - "Completed migration plan document using the data-migration-planning-template.md"
  - "Object migration sequence with parent-before-child ordering and dependency map"
  - "External ID field mapping between source system keys and Salesforce fields"
  - "Validation rule bypass approach (migration user + custom permission or temporary deactivation)"
  - "Rollback strategy with batch ID tracking and targeted delete approach"
  - "Post-migration validation checklist (record counts, field-level spot checks, relationship integrity)"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-10-19
---

# Data Migration Planning

This skill activates when a practitioner needs to plan or review a Salesforce data migration: choosing the loading tool, sequencing objects by dependency, keying records by external ID, keeping automation and sharing from slowing or blocking the load, and having a rollback and reconciliation plan before the first row is written.

---

## Before Starting

Gather this context before working on anything in this domain:

| Context | What to confirm |
|---|---|
| Object inventory and volumes | Objects, rows per object, lookup versus master-detail relationships |
| Source keys | The natural identifier per object; it becomes an External ID field |
| Automation | Validation rules, triggers, flows, and workflow rules on each target object |
| Owners and audit fields | Whether owners are active users, and whether original CreatedDate and CreatedBy must be kept |
| Sharing model | Whether the load can run with Public Read/Write defaults and deferred sharing calculation |
| Volume limits | Bulk API 2.0: 150,000,000 records per rolling 24 hours, internal batches of 10,000; Data Loader supports files up to 150,000,000 records with Bulk API 2.0 |

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "What is the source key for each object, and is it unique and stable?" | Upserts and relationship columns in load files match on indexed fields such as External IDs; a key matched more than once fails the row (Gotcha 2) | One External ID field per object, set Unique when the key must be unique |
| "Which validation rules, triggers, and flows will fire, and which must be skipped for the migration user only?" | The LDV guide recommends disabling triggers, workflow rules, and validations during loads; doing it org-wide exposes other users (Gotcha 1) | A bypass scoped to the migration user through a custom permission or user-level hierarchy setting |
| "Must original created dates, creators, and owners be kept?" | Audit fields can only be set on create, with the Set Audit Fields upon Record Creation permission (Gotcha 3) | The permission enabled for the migration user before the first insert |
| "Are any owners inactive users?" | Records owned by inactive users need a decision before load (Gotcha 4) | An owner map, with placeholders or the inactive-owner permission tested in a sandbox |
| "Which relationship columns reference parents, and through which parent field?" | Bulk API relationship headers allow only one level and only indexed parent fields (Gotcha 5) | Load files whose parent references resolve |
| "Can sharing recalculation wait until the data is in?" | Ownership and sharing changes during the load add computation and lock contention (Gotcha 6) | Defer sharing calculation, or Public Read/Write defaults during the initial load |
| "How will a bad batch be removed, and does deletion need to be permanent?" | Deleted records stay in the Recycle Bin for 15 days unless hard deleted (Gotcha 7) | A batch ID field and a reverse-order delete runbook |

A planned migration adds keys, sequence, scoped bypasses, and a tested rollback; "just loading the files" produces duplicates on re-run, orphaned children, and automation side effects that are hard to undo.

---

## Core Concepts

### Tool selection

| Tool | Use when | Notes |
|---|---|---|
| Data Loader | An operator runs object-by-object loads and wants success and error CSVs | Can use SOAP API, Bulk API, or Bulk API 2.0; with Bulk API 2.0 batch sizes are handled automatically |
| Bulk API 2.0 (direct) | Large or scripted loads | CSV only; 150 MB per job; results via `successfulResults`, `failedResults`, `unprocessedrecords` (see `data/bulk-api-patterns`) |
| ETL platform (MuleSoft, Informatica, Jitterbit) | Heavy transformation, or the pipeline continues as an integration after cutover | Adds a mapping and retry layer |

The LDV guide calls any operation over 2,000 records a candidate for Bulk API 2.0, and ranks operations by speed: insert, then update, then upsert. Where the source cleanly separates new and existing rows, an insert pass and an update pass are faster than one upsert; upsert stays the safe default for re-runnable loads.

### Sequencing

Load owners and queues first, then parents before children: Accounts, Contacts, Opportunities, Products and Price Book Entries, Opportunity Line Items, Cases, Case Comments. Self-references (Contact `ReportsTo`) can use a relationship column to a record already loaded, or a second update pass after all rows exist.

### External IDs and relationship columns

Mark each source key field External ID (Auto Number, Email, Number, or Text). That indexes it and makes it usable as the upsert key. A child file can then reference its parent by that key: `Account.Legacy_Id__c` for a standard lookup, `Parent_Object__r.Legacy_Id__c` for a custom one.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- excerpt: objects/Account/Account.object-meta.xml — External ID key plus a migration-user bypass
     on one validation rule. Merge into retrieved metadata; do not deploy this fragment as-is. -->
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <fields>
        <fullName>Legacy_Id__c</fullName>
        <label>Legacy ID</label>
        <type>Text</type>
        <length>40</length>
        <externalId>true</externalId>
        <unique>true</unique>
    </fields>
    <validationRules>
        <fullName>Billing_Country_Required</fullName>
        <active>true</active>
        <errorConditionFormula>AND(NOT($Permission.Bypass_Migration_Validation), ISBLANK(BillingCountry))</errorConditionFormula>
        <errorMessage>Billing Country is required.</errorMessage>
    </validationRules>
</CustomObject>
```

### Automation and sharing during the load

| Concern | Approach |
|---|---|
| Validation rules | Add `NOT($Permission.<Custom_Permission>)` to each rule that must not block migration rows; grant the permission through a permission set to the migration user only |
| Triggers | Check a hierarchy custom setting with `Migration_Control__c.getInstance().Skip_Automation__c` and set the value at the migration user's level, or check the custom permission with `FeatureManagement.checkPermission` |
| Flows | Add an entry condition or first Decision on the same custom permission |
| Sharing | Defer sharing calculation, or load with Public Read/Write defaults and tighten after |
| Locking | Group child rows by parent in the same batch |

### Rollback

Stamp every migrated row with `Migration_Batch_Id__c`. To roll back a batch, delete its rows child objects first, in reverse load order. Use Bulk API hard delete when the rows must not stay restorable in the Recycle Bin (the user needs the "Bulk API Hard Delete" permission).

---

## Recommended Workflow

1. Fill `templates/data-migration-planning-template.md`: objects, volumes, keys, dependency order, automation inventory, owner map, audit-field decision, and rollback runbook.
2. Write `migration_sequence.csv` (`object,depends_on,bypass_documented`) and put the load CSVs and target metadata (`objects/`) next to it.
3. Run `python3 skills/data/data-migration-planning/scripts/check_data_migration_planning.py --manifest-dir <migration folder>` and fix every ERROR (sequence order, unindexed or grandparent relationship columns); review WARN lines (missing key columns, rules without a bypass).
4. Deploy External ID fields, the bypass permission set, and the batch ID field to a full-copy sandbox; run each load with a sample of a few hundred rows, then the full volume.
5. Reconcile counts, sample field values, and orphan checks per object (`data/data-reconciliation-patterns`); rehearse the rollback once.
6. Repeat in production during the cutover window, following the runbook in `references/cutover-worked-example.md` (it also has a troubleshooting table); remove the bypass permission set and reset sharing settings immediately after.

---

## Review Checklist

- [ ] Sequence puts every parent before its children; self-references have a plan
- [ ] Every object has an External ID key; re-runnable loads use upsert
- [ ] Relationship columns use one level and an indexed parent field
- [ ] Bypasses are scoped to the migration user and removed after the load
- [ ] Audit-field and inactive-owner decisions were tested in a sandbox
- [ ] Sharing calculation is deferred or the load runs before restrictive sharing is configured
- [ ] Every row carries a batch ID; the reverse-order delete runbook was rehearsed
- [ ] Reconciliation targets (counts, samples, orphans) are written down per object
- [ ] The checker reports no ERROR lines

---

## Salesforce-Specific Gotchas

Full write-ups are in `references/gotchas.md`:

| # | Gotcha |
|---|---|
| 1 | Automation fires for the migration user unless the bypass is built in |
| 2 | External ID indexes and matches but does not make values unique |
| 3 | Original audit values can only be set on create, with a permission |
| 4 | Inactive owners need a decision before the load |
| 5 | Relationship columns allow one level and indexed parent fields only |
| 6 | Sharing and locking slow large loads unless planned |
| 7 | Rollback deletes leave rows restorable unless hard deleted |
| 8 | Master-detail children fail without a parent value |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Migration plan | Filled `templates/data-migration-planning-template.md` |
| Sequence file | `migration_sequence.csv` checked by the skill's checker |
| Key and bypass metadata | External ID fields, bypass custom permission, permission set, batch ID field |
| Rollback runbook | Reverse-order delete per batch, with hard-delete decision |
| Reconciliation report | Counts, samples, orphan checks per object |

---

## Related Skills

- `admin/data-import-and-management` — Data Loader and import wizard mechanics
- `data/data-model-design-patterns` — designing the model the migration fills, including key fields
- `data/bulk-api-patterns` — Bulk API 2.0 job calls, CSV rules, and result retrieval
- `data/bulk-api-and-large-data-loads` — load sizing and lock contention for large jobs
- `data/data-reconciliation-patterns` — proving source and target match after the load
- `architect/large-data-volume-architecture` — objects with tens of millions of rows
