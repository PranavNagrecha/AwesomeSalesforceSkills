---
name: data-migration-planning
description: "Use when planning, reviewing, or troubleshooting a Salesforce data migration — covering tool selection (Data Loader, Bulk API 2.0, MuleSoft, Informatica, Jitterbit), migration sequencing for parent-child objects, external ID strategy for upsert idempotency, validation rule bypass, trigger and flow suppression, rollback planning, and post-migration reconciliation. NOT for Data Loader step-by-step mechanics (use data-import-and-management). NOT for schema or data model design (use data-model-design-patterns). NOT for ongoing ETL pipeline architecture."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Data Migration Planning

This skill activates when a practitioner needs to plan or review a Salesforce data migration — choosing the right loading tool, sequencing objects in the correct dependency order, establishing external ID-based upsert idempotency, bypassing automation during load, and building a rollback safety net. It covers the full migration planning lifecycle from pre-migration analysis through post-migration reconciliation.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Object inventory and volumes**: Which objects are being migrated? How many records per object? Are there lookup or master-detail relationships between them?
- **Source system key**: What is the natural identifier in the source system? This becomes the external ID in Salesforce.
- **Automation landscape**: Which validation rules, triggers, workflow rules, and flows exist on each target object? All of them will fire during migration unless you suppress them.
- **User and queue inventory**: Who are the record owners? Are those Salesforce users active and licensed? Assigning ownership to an inactive or unlicensed user causes insert failures.
- **Most common wrong assumption**: Practitioners assume that loading as a System Administrator bypasses validation rules. It does not. Validation rules fire for all users including admins unless a bypass mechanism is explicitly in place.
- **Key limits in play**: Bulk API 2.0 supports up to 150 million rows per 24-hour period and processes up to 10,000 records per batch. Data Loader supports up to 5 million records per operation (configurable). External ID fields are limited to 25 per object, all indexed by default.

---

## Core Concepts

### Tool Selection: Data Loader vs Bulk API 2.0 vs Third-Party ETL

Choosing the right tool is the first decision in any migration plan. The tools are not interchangeable — each has different throughput characteristics, error-handling behavior, and feature support.

**Data Loader** is a Salesforce-provided desktop client that can use either the SOAP API or the Bulk API under the hood. It supports insert, update, upsert, delete, and hard delete operations. Configured with Bulk API mode, it handles up to 5 million records per operation (the limit is configurable in settings). Data Loader is best for straightforward single-object loads where an operator can monitor progress interactively. It produces a success file and an error file after each run, which are essential for reconciliation.

**Bulk API 2.0** is the REST-based bulk interface. It supports CSV input, parallel batch processing, and up to 150 million rows per 24-hour window across all jobs. Each job processes records in batches of up to 10,000 records. Bulk API 2.0 is the right choice for large-volume, unattended, or automated migrations — it is also the backend used by Data Loader in Bulk API mode. Upsert via Bulk API 2.0 requires an External ID field specified as the `externalIdFieldName`.

**Third-party ETL tools** (MuleSoft, Informatica, Jitterbit, Talend) add a transformation layer between source and target. Use them when:
- Source data requires significant field mapping, normalization, or cleansing before loading
- The migration is part of an ongoing integration that will continue post-cutover
- The source system does not export clean CSVs and requires API-to-API extraction

For a pure lift-and-shift with minimal transformation, Bulk API 2.0 (via Data Loader or direct API calls) is lower overhead than a full ETL platform.

### Migration Sequencing: Parents Before Children

Salesforce enforces referential integrity at insert time. A master-detail child record cannot be inserted without a valid parent record ID — the insert fails immediately with a field error. Lookup relationship inserts that reference a missing parent record fail with a "Record ID not found" error rather than silently storing a broken reference.

The rule is absolute: **migrate parents before children**. For a typical CRM migration:

1. Users and queues (record owners — must exist before any record with an OwnerId is inserted)
2. Accounts (top-level parent of most B2B objects)
3. Contacts (lookup to Account)
4. Opportunities (lookup to Account)
5. Products / Price Book Entries (must exist before Opportunity Line Items)
6. Opportunity Line Items (master-detail to Opportunity; requires both Opportunity and Price Book Entry to exist)
7. Cases (lookup to Account and Contact)
8. Case Comments (master-detail to Case)

Determine the dependency graph before writing the migration sequence. If Object A has a lookup to Object B, Object B must be loaded first. If there are circular references (rare, but possible with self-referencing lookup fields like `Reports_To__c` on Contact), load the parent batch first with the self-reference blank, then update the self-reference field in a second pass.

### External ID Strategy for Upsert Idempotency

An External ID field stores the source system's natural key on each Salesforce record. During migration, this enables **upsert** operations: Salesforce checks whether a record with that external ID already exists. If it does, Salesforce updates it; if it does not, Salesforce inserts it.

Without an external ID upsert strategy, re-running a load job after a partial failure creates duplicate records. With it, a failed-and-retried load job is safe to re-run at any time.

External ID fields must be explicitly marked as External ID (and optionally Unique) in the object's field setup. They are indexed by default — no Support case required. Each object supports up to 25 external ID fields. For text-based external IDs, note that **lookups on Text External ID fields are case-sensitive** — "ABC-123" and "abc-123" are treated as different values.

When a child record references a parent by external ID (rather than by Salesforce record ID), Bulk API 2.0 supports relationship references in the form `ParentObject__r.ExternalId__c`. This means you can load child records without first resolving parent Salesforce IDs, as long as the parent records have already been loaded with their external IDs populated.

### Validation Rule and Automation Bypass During Migration

Validation rules, triggers, workflow rules, Process Builder flows, and Flow automations all fire during data loads. A validation rule that requires a field value under normal business conditions may legitimately prevent migration records from loading if those records do not yet satisfy the rule (e.g., a required related record hasn't been created yet, or source data doesn't conform to current business rules).

There are two main bypass approaches:

**Approach 1: Migration user + custom permission bypass (preferred for production)**
1. Create a dedicated migration user profile or permission set.
2. Create a Custom Permission named `Bypass_Validation_Rules` (or similar).
3. On each validation rule that should be bypassed, add a formula condition: `NOT($Permission.Bypass_Validation_Rules)`. This makes the rule not fire when the running user has the custom permission.
4. Assign the custom permission to the migration user before running the load. Remove it afterward.

This approach is auditable, reversible, and does not require deactivating rules in production.

**Approach 2: Temporarily deactivate validation rules**
- Simpler to implement for one-time migrations.
- High risk in production — other users or automations may insert bad data while rules are off.
- Must be documented with a precise deactivation/reactivation window.
- Always re-enable rules immediately after the migration completes. Never leave rules deactivated.

The same bypass patterns apply to triggers and flows. A common approach is a **Custom Setting flag** (e.g., a Hierarchy Custom Setting with a `Migration_In_Progress__c` checkbox). Triggers and flows check this flag at the start of their logic: if `Migration_In_Progress__c` is true, they skip processing. Set the flag before the load; clear it immediately after.

### Rollback Planning

Every migration plan must include a rollback strategy before the first record is loaded. Options:

**Batch ID tracking**: Before each load job, generate a unique batch identifier (e.g., `MGRN-2026-04-04-001`). Store this value in a dedicated `Migration_Batch_Id__c` field on each migrated record (a custom text field). If a load batch needs to be reversed, query all records with that batch ID and delete them. This enables surgical rollback of a single batch without touching records from other batches.

**Soft delete / migration flag**: Add an `Is_Migrated__c` checkbox field. Set it to `true` on every loaded record. If rollback is needed, query `WHERE Is_Migrated__c = true` and delete. Combine with batch ID for more precision.

**Staging objects**: For high-risk migrations, load data into a parallel set of staging custom objects first. Validate the staging data, then copy from staging to production objects. Rollback means deleting the staging records, not touching live data.

Hard delete (permanent deletion, bypassing the recycle bin) requires the `Bulk API Hard Delete` permission or the `hardDelete` operation in the Bulk API. Use hard delete only during testing in sandboxes or when recycle bin pollution would cause issues (e.g., SOQL queries accidentally matching soft-deleted records).

---

## Common Patterns

### Pattern: Parent-Child Migration with External ID Cross-Reference

**When to use:** Migrating related objects (e.g., Account + Contact + Case) where children reference parents by source system ID.

**How it works:**
1. Add an External ID field to each object (e.g., `Legacy_Id__c` as Text, External ID, Unique).
2. Load Accounts first, populating `Legacy_Id__c` with the source system account ID.
3. In the Contact CSV, reference the parent Account by external ID using the column header `Account.Legacy_Id__c` (Bulk API 2.0 relationship notation).
4. Load Contacts via upsert with `Legacy_Id__c` as the external ID field for Contact matching. Bulk API 2.0 resolves the Account reference automatically using the Account's external ID.
5. Load Cases similarly, referencing Account by `Account.Legacy_Id__c` and Contact by `Contact.Legacy_Id__c`.

**Why not use Salesforce record IDs directly:** Source system exports do not contain Salesforce IDs. Resolving Salesforce IDs requires a pre-load query step per object — adding complexity and a failure point. External ID cross-references eliminate this step.

### Pattern: Validation Rule Bypass via Custom Permission

**When to use:** Migrating into a production org where validation rules must stay active for other users during the migration window.

**How it works:**
1. Create a Custom Permission: Setup > Custom Permissions > New. Name: `Bypass_Migration_Validation`.
2. Edit each validation rule that blocks migration. Wrap the existing formula: `NOT($Permission.Bypass_Migration_Validation) AND (<original formula>)`.
3. Create a Permission Set that includes the Custom Permission. Assign it to the migration user.
4. Run the migration. Remove the Permission Set assignment from the migration user when done.
5. Test that the validation rules are still enforced for normal users by running a test insert without the custom permission.

**Why not deactivate rules:** Deactivating rules opens a window where any user — not just the migration job — can save records that violate business rules. In a shared production environment, this is high-risk.

### Pattern: Migration Custom Setting Trigger Bypass

**When to use:** Triggers and flows on migration target objects perform expensive operations (sending emails, creating child records, calling external APIs) that should not fire during migration.

**How it works:**
1. Create a Hierarchy Custom Setting: `Migration_Control__c` with a `Skip_Automation__c` checkbox field.
2. In each trigger, add at the top: `if (Migration_Control__c.getInstance().Skip_Automation__c) return;`
3. In each Flow, add a Decision element at the start that checks `{!$CustomMetadata.Migration_Control__c.Skip_Automation__c}`. If true, route to an End element.
4. Before the migration load, set `Skip_Automation__c = true` via a quick data update or Setup UI.
5. Clear the flag immediately after the migration completes. Verify automation resumes by testing a manual record save.

**Why not comment out trigger code:** Commenting out trigger code requires a deployment, a code review, and another deployment to restore. The Custom Setting flag requires no deployment and can be toggled in seconds.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single object, < 1M records, interactive monitoring needed | Data Loader (Bulk API mode) | Simple, produces success/error CSV files, low setup overhead |
| Multi-object, > 1M records, unattended/automated | Bulk API 2.0 direct or via custom script | Higher throughput, parallel processing, 150M rows/24h limit |
| Source data requires transformation or cleansing before load | MuleSoft / Informatica / Jitterbit | ETL layer handles mapping, normalization, and error retry natively |
| Child object references parent by source system ID | External ID cross-reference via `Parent__r.External_Id__c` | Eliminates pre-load ID resolution step |
| Migration must be re-runnable safely | Upsert with External ID | Prevents duplicate creation on retry |
| Validation rules must stay active for other users during load | Custom Permission bypass on validation rule formula | Surgical bypass for migration user only; no org-wide impact |
| Validation rules are safe to disable temporarily (sandbox/non-prod) | Temporarily deactivate rules | Simpler, but must document window and re-enable immediately |
| Rollback must be targeted to a specific load batch | Migration_Batch_Id__c field + batch ID per load run | Enables surgical delete of one batch without touching others |
| Triggers/flows must not fire during load | Custom Setting `Skip_Automation__c` flag | No deployment required; toggleable in seconds |
| Parent records have circular self-references (e.g., Contact.Reports_To) | Two-pass load: insert without self-ref, then update self-ref | Avoids forward-reference failures at insert time |
| Owner user is inactive in Salesforce | Re-assign to an active placeholder user; update after activation | Inactive user assignments fail at insert time |

---

## Mode 1: Plan a Migration

Use this mode when starting a new migration project.

1. **Inventory objects and volumes**: List every object to be migrated, its approximate record count, and its relationships to other objects.
2. **Build the dependency graph**: Identify all parent-child relationships. Determine the correct load sequence — parents always before children.
3. **Design external IDs**: For each object, identify the source system natural key. Create an External ID field in the target Salesforce org. Add a `Migration_Batch_Id__c` field for rollback targeting.
4. **Audit automation**: List all active validation rules, triggers, workflow rules, and flows on each target object. Decide which require bypass during migration.
5. **Select bypass approach**: Use Custom Permission bypass for production. Use temporary deactivation only for sandboxes or one-time non-production loads.
6. **Select tool**: Apply the Decision Guidance table. For large volumes (> 1M records) choose Bulk API 2.0. For complex transformation, choose an ETL tool.
7. **Define rollback strategy**: Implement `Migration_Batch_Id__c`. Document the delete procedure for each object in reverse order of the migration sequence.
8. **Define post-migration validation**: Plan record count reconciliation (source total vs Salesforce total per object), field-level spot checks (sample 1–5% of records), and relationship integrity checks (no orphan child records).
9. **Fill the migration plan template**: Complete `data-migration-planning-template.md` and review with all stakeholders before starting any loads.

---

## Mode 2: Review a Migration Plan

Use this mode when auditing an existing migration plan before cutover approval.

1. Confirm the object sequence has no parent-child ordering violations — every parent object must appear before its children.
2. Confirm every object has an external ID field identified and that upsert (not insert) is the load operation.
3. Confirm the automation bypass approach is documented and tested in the sandbox. Confirm the bypass will be removed after migration.
4. Confirm the rollback procedure is documented with specific delete steps per object in reverse sequence.
5. Confirm the migration user has the correct permissions and the Custom Permission (or equivalent) assigned.
6. Confirm owner assignments: every record owner must be an active, licensed Salesforce user at load time.
7. Confirm the post-migration validation plan is specific — record count targets, spot-check sampling size, and relationship integrity query are defined.
8. Run `scripts/check_migration_plan.py` against the plan document or CSV configuration to catch structural issues automatically.

---

## Mode 3: Troubleshoot Migration Issues

Use this mode when a migration load has failed or produced unexpected results.

- **Duplicate records created**: The load operation used insert instead of upsert, or the external ID field was not populated in the source CSV. Verify the external ID column is present and populated for every row. Switch to upsert.
- **Validation rule rejections**: The migration user does not have the bypass custom permission, or the validation rule formula was not updated to include the bypass condition. Check rule formula and permission set assignment.
- **Owner assignment failures**: One or more assigned users are inactive or do not have a Salesforce license. Query `SELECT Id, Name, IsActive FROM User WHERE IsActive = false` and cross-reference against the owner IDs in the load file. Reassign to an active placeholder user.
- **Child records failing with "Record ID not found"**: The parent records were either not loaded yet or the parent external ID in the child CSV does not match the value loaded in the parent. Check for case-sensitivity differences in the external ID values (text external IDs are case-sensitive).
- **Triggers or flows firing unexpectedly**: The Custom Setting bypass flag was not set, or the trigger/flow does not check the flag. Verify the flag value and that the trigger/flow code path checks it before processing.
- **Master-detail child insert fails with field required error**: The parent Salesforce record ID (or external ID cross-reference) is missing or wrong in the child CSV. Confirm the parent was loaded and that the cross-reference column name matches the Bulk API 2.0 notation exactly.
- **Load is much slower than expected**: The load is using SOAP API mode instead of Bulk API mode in Data Loader. Switch to Bulk API mode. Alternatively, the batch size is set too small — increase toward 10,000 records per batch.

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

Run through these before marking migration planning complete:

- [ ] Object migration sequence is documented with explicit parent-before-child ordering
- [ ] Every target object has an External ID field; all load operations use upsert (not insert)
- [ ] `Migration_Batch_Id__c` field exists on each migrated object; batch IDs are assigned per load run
- [ ] Automation bypass approach is documented, tested in sandbox, and includes a reversal step
- [ ] Rollback procedure is documented in reverse sequence with specific delete steps
- [ ] All record owner users are confirmed active and licensed before load begins
- [ ] Post-migration validation plan includes record count targets, field-level spot checks, and relationship integrity queries
- [ ] Migration plan template is completed and reviewed with stakeholders

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **System Administrator does not bypass validation rules** — Validation rules fire for all users, including admins and integration users. Running the migration as a System Administrator profile does not suppress validation rules. You must explicitly build a bypass into the rule formula or temporarily deactivate the rules.

2. **Text External ID lookups are case-sensitive** — When Bulk API 2.0 resolves a relationship cross-reference using a text External ID field, the match is case-sensitive. "ABC-001" and "abc-001" are treated as different values. If source system IDs have inconsistent casing, normalize them before loading or use a Number-type External ID field where applicable.

3. **External ID fields on formula fields do not support upsert matching** — Only stored fields (Text, Number, Email, Auto Number) can be designated External ID fields. Formula fields cannot be External IDs, even if they compute a unique value. If your natural key is computed, you must materialize it into a stored field.

4. **Inactive or unlicensed owner assignment causes silent batch failures in Bulk API** — In Bulk API 2.0, rows with an invalid OwnerId (inactive user, unlicensed user, or non-existent user) fail silently — the batch may show partial success. The failed row appears in the error results file with "invalid cross reference id." Always validate owner user lists against `SELECT Id, IsActive FROM User` before load.

5. **Lookup fields referencing un-migrated parents fail but do not block the batch** — If a lookup field references a record ID that does not yet exist in Salesforce (because the parent was not loaded first), the row fails with a reference error. The remaining rows in the batch still process. This means partial loads can create data where some child records have broken references and others do not — making reconciliation harder. Always load parents first.

6. **Hard delete requires explicit permission; soft-deleted records count against storage** — By default, deleted records go to the recycle bin and still consume storage. In large migrations, populating and then soft-deleting thousands of test records can exhaust storage limits. Use Bulk API `hardDelete` or Data Loader's Hard Delete option during sandbox testing. Hard delete requires the `Bulk API Hard Delete` user permission.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `data-migration-planning-template.md` | Fill-in-the-blank migration plan template covering object sequence, external ID mapping, bypass approach, rollback strategy, and validation checklist |
| `check_migration_plan.py` | stdlib Python checker that validates a migration plan CSV or config for external ID presence, parent-before-child ordering, and bypass documentation |

---

## Related Skills

- `data-import-and-management` — use for step-by-step Data Loader mechanics, field mapping, and import wizard operations; this skill covers planning and architecture, not tool operation
- `data-model-design-patterns` — use when designing the Salesforce data model that the migration will populate; covers relationship types, field types, and external ID field setup
- `large-data-volumes` — use when the migration involves objects with tens of millions of records and performance or index strategy is the primary concern
