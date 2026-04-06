# LLM Anti-Patterns — File And Document Integration

Common mistakes AI coding assistants make when generating or advising on File And Document Integration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Inserting ContentDocument Directly

**What the LLM generates:** Code that creates and inserts a `ContentDocument` record with fields like `Title` and `FileType`, then attempts to add versions to it.

**Why it happens:** LLMs generalize from standard parent-child patterns in Salesforce (Account -> Contact). They assume ContentDocument is the insertable parent and ContentVersion is a child you attach afterward. Training data may include outdated or incorrect StackOverflow answers that reference ContentDocument insertion.

**Correct pattern:**

```apex
// CORRECT: Insert ContentVersion — ContentDocument is auto-created
ContentVersion cv = new ContentVersion();
cv.Title = 'My Document';
cv.PathOnClient = 'MyDocument.pdf';
cv.VersionData = fileBlob;
insert cv;

// Query back the auto-created ContentDocumentId
Id docId = [SELECT ContentDocumentId FROM ContentVersion WHERE Id = :cv.Id].ContentDocumentId;
```

**Detection hint:** Look for `new ContentDocument(` or `insert` statements targeting ContentDocument. Any direct ContentDocument DML is wrong.

---

## Anti-Pattern 2: Using Base64 Encoding for Large File Uploads

**What the LLM generates:** Code that base64-encodes file data and sets it on `VersionData` regardless of file size, often with a comment like "supports files up to 2 GB."

**Why it happens:** LLMs conflate the platform's 2 GB file size limit with the REST API request body limit. They default to the simpler base64 pattern because it appears more frequently in training data (tutorials, small-file examples). The 37.5 MB request body limit and the 33% base64 inflation are rarely mentioned together in training sources.

**Correct pattern:**

```text
# For files over ~20 MB, use multipart form-data upload:
POST /services/data/v63.0/sobjects/ContentVersion/
Content-Type: multipart/form-data; boundary=boundary_string

--boundary_string
Content-Disposition: form-data; name="entity_content"
Content-Type: application/json

{"Title":"LargeReport","PathOnClient":"LargeReport.pdf"}
--boundary_string
Content-Disposition: form-data; name="VersionData"; filename="LargeReport.pdf"
Content-Type: application/pdf

<binary file data>
--boundary_string--
```

**Detection hint:** Look for `EncodingUtil.base64Encode` or `VersionData = base64String` in contexts where file size is not constrained to under 20 MB. If the code does not mention a size threshold, it is likely wrong for production use.

---

## Anti-Pattern 3: Assuming Salesforce Provides Built-In Virus Scanning

**What the LLM generates:** Advice that states "Salesforce automatically scans uploaded files for viruses" or omits virus scanning entirely from security recommendations. Sometimes generates code that checks a nonexistent `ScanResult` field on ContentVersion.

**Why it happens:** LLMs conflate Salesforce Shield event monitoring with file scanning, or hallucinate security features based on general enterprise platform expectations. Some training data references Salesforce's virus scanning for email attachments (which exists for Email-to-Case) and incorrectly generalizes it to CRM file uploads.

**Correct pattern:**

```text
Salesforce does NOT scan CRM-uploaded files for viruses.
Virus scanning must be implemented as a custom solution:
1. After-insert trigger on ContentVersion
2. Queueable Apex with Database.AllowsCallouts
3. HTTP callout to external scanning service (ClamAV, VirusTotal, etc.)
4. Named Credential for secure authentication
5. Custom field (Scan_Status__c) to track scan state
```

**Detection hint:** Look for claims about "automatic scanning," "built-in malware detection," references to `ScanResult` or `VirusStatus` fields on ContentVersion, or security guidance that omits virus scanning from file upload implementations.

---

## Anti-Pattern 4: Using the Legacy Attachment Object for New Implementations

**What the LLM generates:** Code that creates `Attachment` records with `ParentId` and `Body` fields to store files on records, often because the LLM was trained on pre-Lightning documentation.

**Why it happens:** The Attachment object appears frequently in older Salesforce training data, blog posts, and StackOverflow answers from 2015-2019. LLMs weight this volume of legacy content heavily. The `Attachment` API is simpler (one object, direct parent link), making it a pattern LLMs favor for its syntactic simplicity.

**Correct pattern:**

```apex
// CORRECT: Use ContentVersion + ContentDocumentLink
ContentVersion cv = new ContentVersion();
cv.Title = 'Invoice';
cv.PathOnClient = 'Invoice.pdf';
cv.VersionData = invoiceBlob;
cv.FirstPublishLocationId = parentRecordId; // Auto-links to record
insert cv;
```

**Detection hint:** Look for `new Attachment(`, `Attachment att = new Attachment`, or any DML targeting the Attachment sObject. In new code, this is always wrong — redirect to ContentVersion.

---

## Anti-Pattern 5: Querying VersionData in Bulk Without Heap Protection

**What the LLM generates:** SOQL queries like `SELECT Id, Title, VersionData FROM ContentVersion WHERE ...` that retrieve binary data for multiple records in a single query, often inside a for loop or batch execute method with default scope size.

**Why it happens:** LLMs treat VersionData like any other field and include it in multi-record queries for convenience. They do not account for the fact that each VersionData blob loads the full file binary into Apex heap memory. Training data rarely demonstrates the heap-limit failure mode because examples use small test files.

**Correct pattern:**

```apex
// CORRECT: Query metadata first, process binaries one at a time
List<ContentVersion> metadataOnly = [
    SELECT Id, Title, ContentDocumentId
    FROM ContentVersion
    WHERE ContentDocumentId IN :docIds
];

// Process VersionData individually in a Queueable chain or Batch with scope = 1
for (ContentVersion cv : metadataOnly) {
    // Enqueue individual processing for each file
    System.enqueueJob(new FileProcessor(cv.Id));
}
```

**Detection hint:** Look for `VersionData` in a SELECT clause that also includes a WHERE clause returning multiple records, or VersionData access inside a batch execute method where scope size is not explicitly set to 1.

---

## Anti-Pattern 6: Confusing Files Connect with Bidirectional File Sync

**What the LLM generates:** Architecture recommendations that describe Files Connect as a solution for syncing files between Salesforce and external storage in both directions, or code that attempts to write files to an external system via Files Connect APIs.

**Why it happens:** The name "Files Connect" implies a general-purpose connection between systems. LLMs infer bidirectional capability from the name and from training data that describes Files Connect alongside integration patterns without clearly stating its read-only limitation.

**Correct pattern:**

```text
Files Connect is READ-ONLY for external files:
- Users can browse, search, and preview external files in Salesforce
- Users CANNOT upload or write files to the external system via Files Connect

For outbound file push to external storage:
- Use custom Apex callouts to the external system API
- Use MuleSoft or another middleware for orchestrated file transfer
- Use Industries CLM External Document Management (EDM) for contract documents
```

**Detection hint:** Look for advice that describes Files Connect as a "sync" solution, mentions writing to external systems via Files Connect, or proposes Files Connect for requirements that include outbound file transfer.
