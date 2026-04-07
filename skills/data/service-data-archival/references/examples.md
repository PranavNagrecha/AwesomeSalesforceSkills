# Examples — Service Data Archival

## Example 1: EmailMessage Bloat After Email-to-Case Implementation

**Scenario:** A Service Cloud org that enabled Email-to-Case three years ago is now consuming 85% of its data storage limit. The team is surprised because they have only ~200,000 Case records, which they estimated at roughly 400 MB. Setup > Storage Usage shows 18 GB consumed — nearly 17 GB unaccounted for by Cases alone.

**Problem:** The team is auditing Case and Attachment record counts but not querying EmailMessage. Each Case averages 8 email threads. With 200,000 Cases, that is approximately 1.6 million EmailMessage records. EmailMessage body text is stored in a long text area field (`TextBody`, `HtmlBody`) and counts against data storage — not file storage. A single EmailMessage with a verbose HTML body can consume 30–50 KB. At scale, EmailMessage records are commonly the largest data storage consumer in Service Cloud orgs, yet they are invisible to the file storage dashboard.

**Solution:**

```soql
-- Step 1: Quantify EmailMessage storage by age bucket
SELECT CALENDAR_YEAR(CreatedDate) yr, COUNT(Id) cnt
FROM EmailMessage
GROUP BY CALENDAR_YEAR(CreatedDate)
ORDER BY CALENDAR_YEAR(CreatedDate) ASC

-- Step 2: Identify EmailMessage records eligible for purge (closed Cases, > 2 years old, no legal hold)
SELECT em.Id, em.CaseId
FROM EmailMessage em
WHERE em.CreatedDate < LAST_N_YEARS:2
  AND em.Parent.IsClosed = true
  AND em.Parent.Legal_Hold__c = false

-- Step 3: Export to external store, then delete via Bulk API 2.0
-- (CSV of Ids submitted as Bulk API 2.0 delete job — no Apex required)
```

**Why it works:** EmailMessage records are queried and deleted independently of their parent Cases. This approach reclaims data storage without touching Case records, preserving the service history, SLA metrics, and case audit trail. Bulk API 2.0 handles large volumes without hitting synchronous DML governor limits (10,000 per transaction).

---

## Example 2: ContentDocument Orphaning After Case Archival

**Scenario:** A compliance team runs a scripted batch to delete Cases older than seven years. Post-deletion, they re-run Setup > Storage Usage and find file storage consumption is unchanged. They expected to reclaim 40 GB of file storage from archived case attachments.

**Problem:** The deletion script deleted Case records and their ContentDocumentLink junction records but did not delete the underlying ContentDocument records. ContentDocumentLink is a junction object — deleting it removes the association between the Case and the file, but the ContentDocument record and its ContentVersion blobs remain in file storage. The platform only reclaims file storage when the ContentDocument itself is deleted. Additionally, some ContentDocument records were linked to both Cases and related Contact records, meaning a query filtering solely on Case-linked ContentDocument Ids would have deleted shared files used elsewhere in the org.

**Solution:**

```soql
-- Step 1: Find ContentDocument Ids linked ONLY to the target Cases (no other links)
-- Run this BEFORE Case deletion to capture the target ContentDocument Ids
SELECT ContentDocumentId
FROM ContentDocumentLink
WHERE LinkedEntityId IN :targetCaseIds

-- Step 2: For each ContentDocumentId from Step 1, verify no other ContentDocumentLinks exist
SELECT ContentDocumentId, COUNT(Id) linkCount
FROM ContentDocumentLink
WHERE ContentDocumentId IN :targetContentDocIds
GROUP BY ContentDocumentId
HAVING COUNT(Id) = 1
-- Only ContentDocuments with exactly 1 link (the Case) are safe to delete

-- Step 3: Delete ContentDocumentLink records for target Cases first
-- (Bulk API 2.0 delete job on ContentDocumentLink Ids)

-- Step 4: Delete ContentDocument records identified in Step 2
-- (Bulk API 2.0 delete job on ContentDocument Ids)
```

**Why it works:** The two-step query approach identifies ContentDocument records that are exclusively linked to the target Cases. ContentDocuments with multiple links are excluded from deletion, preventing accidental destruction of files shared with other records. Deleting the ContentDocument record itself — not just the ContentDocumentLink — is what triggers file storage reclaim. The dependency order (link first, then document) ensures referential integrity during the deletion process.

---

## Anti-Pattern: Deleting Cases Without Pre-Processing Child Records

**What practitioners do:** Submit a Bulk API 2.0 delete job directly on a list of Case Ids, assuming Salesforce will handle cascading cleanup of all child records automatically.

**What goes wrong:** Case deletion in Salesforce does cascade-delete certain child relationships (Tasks, Events, CaseComments) but does not reliably cascade-delete EmailMessage records in all configurations, and does **not** delete ContentDocumentLink or ContentDocument records. After the Case delete job completes, the org has: (a) orphaned EmailMessage records with null or invalid CaseId references consuming data storage, and (b) orphaned ContentDocument records (files with no remaining links) consuming file storage. Storage consumption is unchanged or barely changed despite a large Case deletion batch.

**Correct approach:** Always pre-process in dependency order:
1. Query and export EmailMessage, ContentDocumentLink, and ContentDocument records for target Cases.
2. Delete ContentDocumentLink records (exclusively linked to target Cases).
3. Delete now-orphaned ContentDocument records.
4. Delete EmailMessage records by CaseId.
5. Delete Case records last.

Validate storage reclaim after each phase using Setup > Storage Usage and aggregate SOQL counts.
