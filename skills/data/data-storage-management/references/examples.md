# Examples — Data Storage Management

## Example 1: Diagnosing a 90% Data Storage Alert

**Context:** An Enterprise org with 200 users (10 GB base + 200 × 20 MB = 14 GB allocated) has received a 90% storage alert. The admin opens Setup > Storage Usage and sees the top consumers are: Task (3.1 GB), ContentDocument (0.8 GB in data storage for metadata records), and a custom object `Support_Log__c` (2.2 GB).

**Problem:** The admin does not know which pool (data vs file) is at 90%, which objects are safe to clean, or whether the Recycle Bin is inflating the number.

**Solution:**

```text
Step 1 — Confirm which pool is at 90%:
  Setup > Storage Usage > Data Storage section shows 12.6 GB / 14 GB = 90%.
  File Storage section shows 4.1 GB / 410 GB = 1%. Problem is data storage only.

Step 2 — Check Recycle Bin:
  Setup > Storage Usage > Recycle Bin shows 0.9 GB held.
  Action: Empty the Recycle Bin via Setup > Recycle Bin > Empty.
  Result: Data storage drops to 11.7 GB / 14 GB = 83.6%.

Step 3 — Assess Task records:
  SELECT COUNT() FROM Task WHERE CreatedDate < LAST_N_YEARS:3
  Result: 2.4 million records older than 3 years.
  Business confirms: tasks older than 2 years have no retention requirement.
  Action: Batch delete using Bulk API hardDelete. Estimated reclamation: ~4.8 GB.

Step 4 — Assess Support_Log__c:
  SELECT COUNT() FROM Support_Log__c WHERE CreatedDate < LAST_N_YEARS:2
  Result: 890,000 old records. Business needs these for compliance (7-year retention).
  Action: Evaluate Big Object migration — logs are append-only with known query patterns.
  Big Objects do not consume regular data storage.
```

**Why it works:** Separating the two storage pools prevents wasted effort (file storage was not the problem). Checking the Recycle Bin first is low-risk and immediate. Assessing retention requirements before deleting prevents compliance violations.

---

## Example 2: Eliminating Duplicate File Storage via ContentDocumentLink

**Context:** A manufacturing org uploads the same 3 product specification PDF files to every Quote record (currently ~50,000 Quotes). Each PDF averages 2 MB. The files are stored as Attachments on each Quote record.

**Problem:** File storage shows 300 GB consumed by Attachments on Quote. The same 3 PDFs (6 MB total) are stored 50,000 times (3 × 2 MB × 50,000 = 300 GB). Every time a spec is updated, staff manually re-upload to all Quotes.

**Solution:**

```apex
// Step 1 — Create ContentVersion for each unique PDF (done once)
ContentVersion cv = new ContentVersion();
cv.Title = 'Product Spec - Model A';
cv.PathOnClient = 'ProductSpecModelA.pdf';
cv.VersionData = Blob.valueOf('...binary content...');
cv.IsMajorVersion = true;
insert cv;

// Retrieve the ContentDocumentId created by the ContentVersion insert
ContentVersion inserted = [SELECT ContentDocumentId FROM ContentVersion WHERE Id = :cv.Id];
Id contentDocId = inserted.ContentDocumentId;

// Step 2 — Link to all Quote records via ContentDocumentLink (no binary duplication)
List<ContentDocumentLink> links = new List<ContentDocumentLink>();
for (Quote q : [SELECT Id FROM Quote]) {
    ContentDocumentLink link = new ContentDocumentLink();
    link.ContentDocumentId = contentDocId;
    link.LinkedEntityId = q.Id;
    link.ShareType = 'V'; // Viewer access
    link.Visibility = 'AllUsers';
    links.add(link);
}
insert links;

// Step 3 — Delete original Attachments after confirming links are correct
// DELETE FROM Attachment WHERE ParentId IN (SELECT Id FROM Quote) AND Name = 'ProductSpecModelA.pdf'
// Run via Bulk API hardDelete after validation
```

**Why it works:** ContentDocument stores the binary once. ContentDocumentLink is a lightweight data record (~2 KB) that creates the association. 50,000 links × ~2 KB = ~100 MB data storage, versus the original 300 GB file storage. When the spec PDF is updated, only one ContentVersion upload is needed — all links automatically point to the latest version.

---

## Anti-Pattern: Using Long Text Area Fields to Store Binary Content

**What practitioners do:** Store base64-encoded file content (PDFs, images, CSVs) directly in a Long Text Area or Rich Text Area field because it avoids building a file upload UI.

**What goes wrong:** Long Text Area fields have a maximum of 131,072 characters. A 100 KB binary file base64-encodes to ~133 KB — already over the field limit. Even at smaller sizes, each record with populated fields can exceed the 2 KB average record size by 10–100x, rapidly inflating data storage. Rich Text Area fields store embedded images in file storage, but the field metadata record still consumes data storage for the reference overhead. Neither approach benefits from ContentDocument deduplication, versioning, or preview generation.

**Correct approach:** Use ContentVersion + ContentDocumentLink for all binary file storage. Use the Long Text Area field only for genuine text content (notes, descriptions, structured text data). If a binary payload must be stored on-record for integration reasons, evaluate whether the integration can be refactored to reference a ContentDocumentId instead of carrying the payload inline.
