# Gotchas — Attachment to Files Migration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Files Storage Costs More Than Attachment Storage

**What happens:** A migration of 50 GB of Attachments completes successfully. The next monthly bill includes a Files storage overage. The team assumed Files storage would be the same allocation as Attachment storage.

**Why:** Attachments and Files use the same "File Storage" allocation in modern editions, but Files storage is consumed differently. ContentVersion preserves every version (Attachment had no version history). On insert, the original counts as version 1; future updates accumulate. Bulk migration creates one version per file initially, but if the source Attachment was edited multiple times (rare), the migration may unexpectedly preserve only the latest.

**Mitigation:** Project total Files storage at 1.0× to 1.2× of source Attachment storage for a one-time migration. Confirm the org's File Storage allocation BEFORE starting; if the migration would exceed it, plan a selective predicate (Pattern 4 in SKILL.md) or a storage-tier upgrade.

## Gotcha 2: `Attachment.Body` Loaded Eagerly on Every Query

**What happens:** A SOQL `SELECT Id, Name, Body FROM Attachment LIMIT 100` materializes 100 binary blobs into Apex heap. Average size 800 KB → 80 MB needed in heap. Apex limit is 6 MB sync, 12 MB async. Transaction fails with `System.LimitException: Apex heap size too large`.

**Why:** SOQL on `Body` does not stream — every row's blob is loaded synchronously. There is no LIMIT-on-bytes clause.

**Mitigation:** Set Batch Apex `scope=10` (or `scope=1` for files >5 MB). Inside `execute`, copy `a.Body` to `cv.VersionData` immediately and let the local Attachment reference go out of scope so GC can release the body. NEVER hold a list of `Attachment` records in `Database.Stateful` member variables.

## Gotcha 3: Inactive Owners Cause Silent Visibility Gaps

**What happens:** Migration completes. Audit report shows 100% success. Users report "I can't see my old attachments." Investigation: those Attachments belonged to users who left the company; ownership of the migrated `ContentDocument` is now an inactive user, and current users don't have visibility through the parent record's sharing.

**Why:** `ContentVersion.OwnerId` accepts inactive users at insert time. The migration faithfully preserves the original owner. But Files visibility depends on the owner being part of the sharing audience for the parent — an inactive owner with no role/group membership is effectively invisible.

**Mitigation:** Decide a fallback BEFORE migrating: (a) reassign ownership to a designated migration user (loses audit but preserves access), (b) preserve original owner and accept the visibility consequence (correct for compliance/audit but loses access), (c) reassign to the parent record's current owner. Document the chosen policy in the migration log per row.

## Gotcha 4: `MIXED_DML_OPERATION` When Trigger Fires on Attachment Insert with User Context

**What happens:** A user record is being updated in the same transaction as an Attachment insert (e.g., a user-creation flow that uploads a profile picture as an Attachment). The Attachment-after-insert trigger tries to insert a `ContentVersion`. Transaction fails with `MIXED_DML_OPERATION: DML operation on setup object is not allowed after you have updated a non-setup object`.

**Why:** `ContentVersion` and `User` are setup-vs-non-setup boundary objects in Salesforce DML rules. Mixing them in a single transaction is forbidden.

**Mitigation:** The cutover trigger MUST defer to a Queueable (or `@future`). Direct inline insert from the trigger fails for any flow that touches User in the same transaction. The Queueable approach in Pattern 3 of SKILL.md handles this correctly.

## Gotcha 5: `ContentDocumentLink.Visibility='AllUsers'` Rejected on Private-OWD Parents

**What happens:** Migration runs against an org where the parent object's OWD is Private. Every `ContentDocumentLink` insert fails with `FIELD_INTEGRITY_EXCEPTION: A file shared with all users cannot be linked to a private record`.

**Why:** Salesforce enforces that `Visibility='AllUsers'` cannot be set on links to records whose audience is constrained by Private OWD. The platform rejects this at the validation layer.

**Mitigation:** Detect parent OWD before assigning visibility:

```apex
Map<String, EntityDefinition> parentDefs = new Map<String, EntityDefinition>();
for (EntityDefinition ed : [SELECT QualifiedApiName, InternalSharingModel FROM EntityDefinition WHERE QualifiedApiName IN :parentTypes]) {
    parentDefs.put(ed.QualifiedApiName, ed);
}
// For private-OWD parents, downgrade Visibility to 'InternalUsers'
```

Or simpler: default everything to `Visibility='InternalUsers'` and only escalate to `AllUsers` for parents you've verified have public-read OWD.

## Gotcha 6: `CreatedDate` Defaults to "Now" — Audit Trail Lost

**What happens:** Compliance team reviews migrated files. Every `ContentVersion` has `CreatedDate` matching the migration day. The original 5-year history of when files were uploaded is gone. An audit fails because document age cannot be proven.

**Why:** `CreatedDate` is a system field. Default Salesforce behavior on insert is to set it to `System.now()`. Preserving the source `CreatedDate` requires (a) the user has the "Set Audit Fields upon Record Creation" permission enabled at the org level, AND (b) the migration code explicitly sets `cv.CreatedDate = a.CreatedDate; cv.CreatedById = a.CreatedById;`.

**Mitigation:** Decide BEFORE the migration whether audit history must be preserved. If yes: enable the audit-field permission, write the explicit assignments, and verify on a sandbox slice. If no: document the decision in the migration plan so future audits don't surprise you.

## Gotcha 7: `Source_Attachment_Id__c` Not Carried to ContentDocumentLink

**What happens:** Reconciliation queries on `ContentVersion.Source_Attachment_Id__c` return correct counts, but downstream queries that group by `LinkedEntity` on `ContentDocumentLink` need to know which link came from which Attachment. There's no place to store that on the link row.

**Why:** `ContentDocumentLink` does not allow custom fields (it is a junction-style sObject managed internally).

**Mitigation:** Maintain the mapping in `Migration_Log__c` (one row per source Attachment with `Source_Attachment_Id__c`, `ContentDocument_Id__c`, and `Linked_Entity_Id__c`). Reconciliation queries join through the log, not through `ContentDocumentLink` directly.

## Gotcha 8: Queueable Re-Queries Must Re-Read Body

**What happens:** A trigger captures `Trigger.new` Attachment records and passes them to a Queueable. The Queueable reads `a.Body` and inserts ContentVersion. At runtime, `a.Body` is null and the file is empty.

**Why:** `Trigger.new` records do NOT contain `Body` unless `Body` was in the SOQL that loaded them — and triggers don't issue SOQL for `Trigger.new`. Body is a "not loaded" field. Once you cross an async boundary (Queueable, @future), the in-memory reference loses access to fields that were never loaded.

**Mitigation:** In the Queueable, re-query the Attachments by ID with explicit `SELECT Body, ParentId, ...`. Pattern 3 of SKILL.md's example shows this. Never trust `Trigger.new` to carry blob fields across async.

## Gotcha 9: Cleanup Batch Cascade Deletes Attachment-on-EmailMessage Linkage

**What happens:** Cleanup deletes original `Attachment` records. Subsequent users opening old Email records (`EmailMessage`) see the email but the inline attachment links are broken — the Email referenced the Attachment by ID, and that ID is gone.

**Why:** `EmailMessage` records may store an `Attachment` reference in their inline content (rendered HTML with `cid:` references) or via `EmailMessageRelation`. Deleting the source Attachment severs that link without updating the Email body.

**Mitigation:** For Attachments whose `ParentId.Type = 'EmailMessage'`, KEEP the Attachment alongside the Files copy, or update the Email rendering to point at the new ContentDocument URL. Default cleanup logic should EXCLUDE EmailMessage parents until a separate decision is made for that subset.
