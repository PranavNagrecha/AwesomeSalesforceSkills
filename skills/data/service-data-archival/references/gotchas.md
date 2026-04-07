# Gotchas — Service Data Archival

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: EmailMessage Deletion Does Not Cascade to ContentDocumentLink

**What happens:** When an EmailMessage record is deleted, the ContentDocumentLink records that link file attachments (processed by Email-to-Case from the original email) to that EmailMessage are **not automatically deleted**. The ContentDocumentLink records remain in the org pointing to a now-deleted parent entity. The ContentDocument and ContentVersion records also remain, continuing to consume file storage. These orphaned ContentDocumentLink records are invisible to most storage audits because they are not browsable through the UI.

**When it occurs:** Any time EmailMessage records are deleted as part of a storage cleanup without first querying and explicitly deleting their associated ContentDocumentLink and ContentDocument records. This is especially common when teams focus the archival effort on data storage (EmailMessage) without realizing email attachment blobs count against file storage as ContentDocument records.

**How to avoid:** Before deleting EmailMessage records, query `ContentDocumentLink WHERE LinkedEntityId IN :targetEmailMessageIds` to collect ContentDocument Ids. Verify each ContentDocument has no other links (`HAVING COUNT(Id) = 1`), then delete the ContentDocumentLink and ContentDocument records before or alongside the EmailMessage deletion. Run the checker script post-deletion to confirm no orphaned links remain.

---

## Gotcha 2: Archived Cases Still Consume Storage When Attachments Are Not Separately Archived

**What happens:** When the Salesforce Archive feature (Legacy Salesforce Archive) is used to move Case records to the archive tier, only the Case sObject data moves. ContentDocument and ContentVersion records linked to those Cases **remain in the active file storage pool** unless the archive configuration explicitly includes file objects. The file storage dashboard shows no reduction after archiving, and practitioners incorrectly conclude the archive job failed or is still processing.

**When it occurs:** Any Salesforce Archive implementation that archives Case records but does not configure file archival separately. This is the default behavior — file object archival must be explicitly enabled and mapped in the Archive retention policy configuration. Orgs consuming large file storage GB from case attachments see zero reclaim from Case archival alone.

**How to avoid:** When using Salesforce Archive, review the retention policy configuration to confirm ContentDocument and ContentVersion are included in the archive scope. If the Archive feature does not cover file storage in your edition, supplement it with a separate ContentDocument deletion pipeline post-archive. Do not treat Case archival and file storage archival as a single operation without verifying the archive policy covers both storage pools.

---

## Gotcha 3: Legal-Hold Records Fail Entire Bulk API Batches

**What happens:** The Salesforce platform enforces a hard block on deletion of records flagged as under legal hold (via the built-in Legal Hold feature or a custom enforcement field). If even one legal-hold record is included in a Bulk API 2.0 delete job batch, the **entire batch** containing that record fails with a non-retriable error. The other records in that batch are also not deleted. For large archival jobs with thousands of batches, a small number of legal-hold records scattered through the job can cause widespread batch failures that are tedious to diagnose and resubmit.

**When it occurs:** Legal-hold exclusion is applied in post-processing (filtering results after the SOQL query) rather than at the SOQL WHERE clause level. If the exclusion list is not applied before the Bulk API job CSV is generated, legal-hold records slip into batches. This is particularly likely when the legal-hold field is on the Case parent record but the deletion target is EmailMessage or ContentDocument — the exclusion list must be joined across objects, not just applied on the directly deleted object.

**How to avoid:** Always apply legal-hold exclusion in the SOQL query itself, not in application code post-query. For EmailMessage deletion, join back to the parent Case to filter: `WHERE Parent.Legal_Hold__c = false`. For ContentDocument deletion, join back to Case via ContentDocumentLink to verify none of the linked entities are under hold. Maintain a persistent legal-hold exclusion list and refresh it before every archival run.

---

## Gotcha 4: ContentDocument Shared Across Multiple Objects Gets Deleted Prematurely

**What happens:** A ContentDocument can be linked to multiple entities simultaneously — for example, a case attachment that was also shared to a related Account or forwarded to a Contact record. A deletion script that queries ContentDocument Ids by filtering on `ContentDocumentLink WHERE LinkedEntityId IN :targetCaseIds` will collect ContentDocument Ids that have other active links. Deleting those ContentDocument records destroys files that are still referenced by non-Case entities, causing data loss invisible to the deletion script operator.

**When it occurs:** Any archival pipeline that collects ContentDocument Ids via a single ContentDocumentLink filter pass without checking for additional links. This is the most common ContentDocument archival bug.

**How to avoid:** After collecting target ContentDocument Ids from Case-linked ContentDocumentLink records, run a second query: `SELECT ContentDocumentId, COUNT(Id) linkCount FROM ContentDocumentLink WHERE ContentDocumentId IN :targetIds GROUP BY ContentDocumentId HAVING COUNT(Id) = 1`. Only ContentDocuments with exactly one link (the Case being archived) are safe to delete. ContentDocuments with two or more links must be excluded or handled in a separate review step.

---

## Gotcha 5: Recycle Bin Delays True Storage Reclaim by Up to 15 Days

**What happens:** Deleted records in Salesforce go to the Recycle Bin and **continue to count against storage** until permanently purged. The Recycle Bin retains records for 15 days before automatic permanent deletion. This means that an archival run that deletes 10 GB of EmailMessage records will not show a storage reclaim in Setup > Storage Usage until those records are purged from the Recycle Bin — either by waiting 15 days or by explicitly calling `Database.emptyRecycleBin()` (Apex) or the REST API equivalent.

**When it occurs:** Any time storage reduction is expected immediately after a bulk delete. Teams who run the archival job and immediately check storage are surprised to see no change, leading them to conclude the deletion failed and re-run the job, creating duplicate delete attempts.

**How to avoid:** After a bulk delete job completes, explicitly empty the Recycle Bin for the deleted record types using the Bulk API hard-delete operation (which bypasses the Recycle Bin entirely and permanently deletes records immediately) or by calling `Database.emptyRecycleBin()` in a subsequent Apex job. Alternatively, document the 15-day delay in the archival runbook so stakeholders do not misinterpret the storage dashboard. Note: hard-delete requires the "Bulk API Hard Delete" permission, which should be tightly controlled.
