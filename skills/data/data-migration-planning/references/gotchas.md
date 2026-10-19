# Gotchas — Data Migration Planning

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Automation Fires for the Migration User Unless the Bypass Is Built In

**What happens:** Migration rows are rejected by validation rules, or triggers and flows send emails, create child records, and call external systems for every loaded row.

**When it occurs:** Every load. The LDV guide's advice for load throughput is to "Disable Apex triggers, workflow rules, and validations during loads" and process records with batch Apex afterwards; it also notes that workflow actions increase Bulk API processing time. Don't assume a profile exempts anyone: load one row that breaks each active rule in a sandbox as the migration user and confirm it fails until the bypass is in place.

**How to avoid:** Scope the bypass to the migration user. In validation rules, add `NOT($Permission.<Custom_Permission>)`. In Apex, check the same permission with `FeatureManagement.checkPermission`, or read a hierarchy custom setting with `getInstance()`, which returns the value merged for the current user, so the flag can be set at the migration user's level instead of org-wide. Name an owner for removing the permission set (or resetting the setting) after cutover, and test a normal user's save afterwards.

---

## Gotcha 2: External ID Indexes and Matches but Does Not Make Values Unique

**What happens:** Re-run loads update the wrong record, or upserts fail on some rows because two Salesforce records share the source key.

**When it occurs:** External ID and Unique are separate field flags. Upsert documentation: "If the external ID is matched multiple times, then a 300 error is reported, and the record isn't created or updated." Keys that were unique in the source can collide after merges, test loads, or manual entry.

**How to avoid:** Mark the key field both External ID and Unique when the source key must stay unique, and decide its case sensitivity (`caseSensitive` on the field) deliberately. Profile duplicates in the source before the first load.

---

## Gotcha 3: Original Audit Values Can Only Be Set on Create, With a Permission

**What happens:** Migrated records show the load date as CreatedDate and the migration user as creator, and history-based reports break.

**When it occurs:** The Object Reference describes the steps: enable "Set Audit Fields upon Record Creation" and "Update Records with Inactive Owners" in User Interface settings, grant Set Audit Fields upon Record Creation to the loading user, then create records through the API with the audit fields set. The values can be set on Account, Case, Contact, Lead, Opportunity, Task, Event, custom objects, and others listed there; `SystemModstamp` can never be set. Audit dateTime fields accept dates from 1970-01-01 onwards.

**How to avoid:** Decide before the first insert and set the values in the insert itself. The documented path is "create a record and set its audit fields," so don't plan on a later update pass to fix them.

---

## Gotcha 4: Inactive Owners Need a Decision Before the Load

**What happens:** Rows whose owner is a departed salesperson fail or end up owned by the wrong user, and the team finds out from the error file.

**When it occurs:** Source data references users who are inactive in Salesforce. The Object Reference pairs "Update Records with Inactive Owners" with the audit-field setup; whether your load can assign an inactive owner on insert is something to test in a sandbox with your settings, not to assume.

**How to avoid:** Export `SELECT Id, IsActive FROM User`, map every source owner, and choose per owner: an active placeholder owner (with a post-cutover reassignment list), or the inactive-owner permission after a sandbox test proves it works for your objects.

---

## Gotcha 5: Relationship Columns Allow One Level and Indexed Parent Fields Only

**What happens:** A child file references `Account.Parent.Legacy_Id__c`, or a parent field that isn't an External ID, and every row fails to resolve.

**When it occurs:** Bulk API relationship headers use `RelationshipName.IndexedFieldName`. The guide's rules: child-to-parent only; no child-to-parent-grandparent chains; and "You can only use indexed fields on the parent object. A custom field is indexed if its External ID field is selected." Standard fields qualify when their `idLookup` property is true. Custom relationships use the `__r` name (`Mother_Of_Child__r.External_ID__c`).

**How to avoid:** Give every parent object an External ID key, reference it one level up only, and resolve grandparents through the intermediate object's own key.

---

## Gotcha 6: Sharing and Locking Slow Large Loads Unless Planned

**What happens:** Loads crawl or fail with lock errors as each ownership change triggers sharing recalculation and many children update the same parent at once.

**When it occurs:** The LDV guide's loading practices: use Public Read/Write defaults during the initial load to avoid sharing calculation, load users into roles before records, add sharing rules one at a time afterwards, use the defer sharing calculation permission, and group child records by parent in the same batch to minimize locking conflicts. It also notes that errors in a Bulk API 2.0 batch trigger single-row processing for that batch, which hurts performance, so dirty data slows everything.

**How to avoid:** Put the sharing sequence in the cutover plan, sort child files by parent key, and clean data before loading.

---

## Gotcha 7: Rollback Deletes Leave Rows Restorable Unless Hard Deleted

**What happens:** A rolled-back batch is deleted, but the rows can still be restored for 15 days and still have to be excluded from queries; or the team believes the deletes freed storage while the bin was holding it (it isn't: Recycle Bin items don't count against storage).

**When it occurs:** The LDV guide: deleted items stay in the Recycle Bin for 15 days and still affect database performance; Bulk API and Bulk API 2.0 hard delete bypasses the bin and is recommended for large deletes. The hard-delete permission is off by default. Deleting a master record also deletes its detail records.

**How to avoid:** Delete rollback batches child-first in reverse load order, using hard delete when the rows must not remain restorable, and rehearse the runbook in a sandbox.

---

## Gotcha 8: Master-Detail Children Fail Without a Parent Value, and Take Their Owner From It

**What happens:** Detail rows with a blank parent column fail; an `OwnerId` column on a detail object has no effect.

**When it occurs:** The Object Reference: the master-detail field is required on the detail record's page layout; the detail object has no Owner field of its own and takes the master record's owner; records can't be reparented unless "Allow reparenting" is enabled on the relationship. A plan to "load children now and attach parents later" works for a lookup but not for a master-detail.

**How to avoid:** Count blank-parent rows during source profiling, route them to a catch-all parent or hold them out, load parents first, and drop owner columns from master-detail child files.
