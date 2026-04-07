# LLM Anti-Patterns — Service Data Archival

Common mistakes AI coding assistants make when generating or advising on Service Data Archival. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending DELETE on Case Without Handling EmailMessage First

**What the LLM generates:** A Bulk API job or Apex batch that deletes Case records directly, with a comment like "Salesforce will cascade-delete related records automatically."

**Why it happens:** LLMs trained on general Salesforce documentation know that some parent-child relationships use cascade delete (e.g., Opportunity → OpportunityLineItem), and they overgeneralize this behavior to all child relationships. EmailMessage records with a CaseId lookup are not guaranteed to cascade-delete in all configurations, and ContentDocumentLink/ContentDocument records are never cascade-deleted by Case deletion.

**Correct pattern:**

```
Pre-process in dependency order:
1. Query ContentDocumentLink WHERE LinkedEntityId = Case Ids
2. Verify ContentDocument has no other links (COUNT(Id) = 1)
3. Delete ContentDocumentLink records
4. Delete orphaned ContentDocument records
5. Delete EmailMessage records WHERE CaseId IN :targetCaseIds
6. Delete Case records last

Never assume cascade deletion handles file and email storage cleanup.
```

**Detection hint:** Look for any code that deletes Case records without a preceding or concurrent EmailMessage deletion step and without a ContentDocumentLink/ContentDocument cleanup step.

---

## Anti-Pattern 2: Conflating ContentDocument with Attachment (Legacy Object)

**What the LLM generates:** SOQL queries targeting the legacy `Attachment` object (`SELECT Id FROM Attachment WHERE ParentId IN :caseIds`) for case file cleanup, or advice to delete `Attachment` records to reclaim file storage.

**Why it happens:** The `Attachment` object was the pre-Salesforce Files (pre-Spring '16) mechanism for storing files on records. Training data contains significant volume of content referencing `Attachment`. LLMs conflate the two, especially when the prompt mentions "attachments" in natural language. In modern orgs (post-Spring '16 with Salesforce Files enabled), files are stored as `ContentDocument`/`ContentVersion` and linked via `ContentDocumentLink`. The `Attachment` object may still exist with legacy data but is not the primary file storage mechanism.

**Correct pattern:**

```soql
-- Modern orgs: use ContentDocumentLink to find files linked to Cases
SELECT ContentDocumentId FROM ContentDocumentLink
WHERE LinkedEntityId IN :targetCaseIds

-- Legacy orgs (pre-Salesforce Files): check Attachment object
SELECT Id FROM Attachment WHERE ParentId IN :targetCaseIds

-- Always verify which mechanism is in use before scripting deletions
SELECT COUNT(Id) FROM Attachment WHERE ParentId IN :sampleCaseIds
SELECT COUNT(Id) FROM ContentDocumentLink WHERE LinkedEntityId IN :sampleCaseIds
```

**Detection hint:** Any SOQL query on the `Attachment` object in a modern Service Cloud archival context. Verify whether the org uses legacy Attachments or Salesforce Files before treating Attachment deletion as the storage solution.

---

## Anti-Pattern 3: Ignoring ContentDocumentLink Orphans After ContentDocument Deletion

**What the LLM generates:** A deletion sequence that deletes ContentDocument records directly (without first deleting ContentDocumentLink records) and assumes the ContentDocumentLink records will be cleaned up automatically.

**Why it happens:** LLMs reason that if the parent (ContentDocument) is deleted, the child junction record (ContentDocumentLink) will be gone too — similar to how deleting a Case removes CaseComments. But ContentDocumentLink is a junction object with its own lifecycle. In practice, deleting ContentDocument records may leave stale ContentDocumentLink rows (pointing to deleted ContentDocuments) that appear in SOQL queries, confuse downstream processes, and create noise in orphan scans.

**Correct pattern:**

```
Correct deletion order for ContentDocument cleanup:
1. Delete ContentDocumentLink records first
   (removes the association between the entity and the file)
2. Then delete ContentDocument records
   (removes the file itself and reclaims file storage)

Never delete ContentDocument before ContentDocumentLink.
```

**Detection hint:** Any code that deletes `ContentDocument` records in a step that precedes deletion of the associated `ContentDocumentLink` records, or code that deletes `ContentDocument` without any `ContentDocumentLink` handling step at all.

---

## Anti-Pattern 4: Missing Legal-Hold Checks Before Bulk Delete

**What the LLM generates:** A Bulk API 2.0 delete job definition or an Apex batch that does not include a legal-hold filter in its SOQL query. The code works correctly for records without holds but throws non-retriable errors for any batch containing a held record.

**Why it happens:** LLMs generate "happy path" deletion scripts by default. Legal hold is a compliance concept that appears infrequently in technical training data relative to basic CRUD operations. The LLM is not aware that a single held record in a Bulk API batch causes the entire batch to fail, not just the held record itself.

**Correct pattern:**

```soql
-- Always filter legal hold at the SOQL level, not in post-processing

-- For EmailMessage deletion (join to parent Case for hold status):
SELECT Id FROM EmailMessage
WHERE CreatedDate < LAST_N_YEARS:2
  AND Parent.IsClosed = true
  AND Parent.Legal_Hold__c = false

-- For Case deletion:
SELECT Id FROM Case
WHERE ClosedDate < LAST_N_YEARS:7
  AND Legal_Hold__c = false
  AND IsClosed = true
```

**Detection hint:** Any SOQL query in a deletion pipeline that does not include a `Legal_Hold__c = false` filter or equivalent legal-hold exclusion clause. Also flag any post-query filtering approach (filtering the result list in Python/Apex after querying) instead of embedding the exclusion in the WHERE clause.

---

## Anti-Pattern 5: Using Synchronous DML for Large-Volume EmailMessage Deletion

**What the LLM generates:** An Apex batch class that calls `delete emailMessages;` in the `execute()` method with a batch size of 200, looping over millions of EmailMessage records.

**Why it happens:** Apex batch is the most common large-data pattern in Salesforce training data, and `delete` in Apex is the most common DML operation. LLMs default to Apex batch for any "process many records" task. For pure deletion at scale, however, Apex batch is significantly slower and more fragile than Bulk API 2.0 (which runs outside Apex governor limits) and consumes Apex async capacity that may be needed by other processes.

**Correct pattern:**

```
For EmailMessage/ContentDocument deletion at scale (> 10,000 records):

Use Bulk API 2.0 hard-delete job:
- POST /services/data/vXX.0/jobs/ingest
  { "operation": "hardDelete", "object": "EmailMessage", "contentType": "CSV" }
- Upload CSV of Ids to delete
- PATCH job to "UploadComplete"
- Poll job status until "JobComplete"

Benefits:
- No Apex governor limits
- Parallel batch processing
- Bypasses Recycle Bin (immediate storage reclaim)
- No deployed Apex class required

Use Apex batch only when per-record conditional logic
is required that cannot be expressed in a SOQL WHERE clause.
```

**Detection hint:** Any Apex `delete` DML statement in a batch `execute()` method targeting EmailMessage, ContentDocument, or ContentDocumentLink at scale. Flag it and recommend Bulk API 2.0 unless per-record conditional logic is genuinely required.

---

## Anti-Pattern 6: Not Validating Storage Reclaim After Deletion

**What the LLM generates:** A deletion script with no post-deletion validation step. The script deletes records and reports "Done" without confirming that storage was actually reclaimed.

**Why it happens:** LLMs focus on the operational task (delete the records) and do not model the Salesforce platform's Recycle Bin delay or the ContentDocument orphan scenario. In practice, storage may not reclaim immediately (due to Recycle Bin) or at all (due to orphaned ContentDocuments or skipped pipeline steps).

**Correct pattern:**

```
Post-deletion validation checklist:
1. Run: SELECT COUNT(Id) FROM EmailMessage WHERE CaseId IN :deletedCaseIds
   → should return 0
2. Run: SELECT COUNT(Id) FROM ContentDocumentLink WHERE LinkedEntityId IN :deletedCaseIds
   → should return 0
3. Run: SELECT COUNT(Id) FROM ContentDocument WHERE Id IN :targetContentDocIds
   → should return 0
4. Empty Recycle Bin for deleted object types OR wait 15 days
5. Re-check Setup > Storage Usage data GB and file GB
6. Compare to pre-deletion baseline; document the delta
```

**Detection hint:** Any archival or deletion script that lacks a post-deletion SOQL validation step and a comparison to pre-deletion storage baselines.
