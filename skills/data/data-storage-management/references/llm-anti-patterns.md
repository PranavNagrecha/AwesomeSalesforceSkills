# LLM Anti-Patterns — Data Storage Management

Common mistakes AI coding assistants make when generating or advising on Data Storage Management in Salesforce. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Claiming Deleted Records Immediately Free Storage

**What the LLM generates:** "To free up storage, simply delete the old records using a SOQL delete loop or Data Loader. Your storage will drop right away."

**Why it happens:** The LLM models storage reclamation after typical database behavior where DELETE immediately frees space. Salesforce's Recycle Bin mechanism is a platform-specific behavior not reflected in general database training data.

**Correct pattern:**

```text
Deleting records sends them to the Recycle Bin for 15 days (standard delete) or
30 days (Bulk API hard delete). Records in the Recycle Bin still count against
data storage.

To immediately free storage after deletion:
1. Use Bulk API with hardDelete=true operation to bypass the Recycle Bin, OR
2. After standard delete, empty the Recycle Bin via:
   - Setup > Recycle Bin > Empty Recycle Bin
   - Database.emptyRecycleBin(List<Id>) in Apex
   - DELETE /services/data/vXX.0/sobjects/... does NOT bypass the bin
```

**Detection hint:** Look for phrasing like "delete to free storage" or "storage drops after deletion" without any mention of the Recycle Bin.

---

## Anti-Pattern 2: Confusing Data Storage Limits with File Storage Limits

**What the LLM generates:** "Your org has 10 GB of storage for everything — records, files, and attachments all share the same pool."

**Why it happens:** LLMs conflate the two storage pools because Salesforce's overall "storage" concept is mentioned generically in training data without always distinguishing the pools.

**Correct pattern:**

```text
Salesforce maintains two completely separate storage pools:

1. DATA STORAGE: records (standard + custom objects), ~2 KB per record
   Enterprise: 10 GB base + 20 MB per user license

2. FILE STORAGE: binary content of files
   ContentDocument (Files), Attachments, Documents, Chatter attachments
   Enterprise: 10 GB base + 2 GB per user license

An org can be at 95% data storage and 5% file storage simultaneously.
Monitoring and remediation must target the correct pool.
```

**Detection hint:** Any advice that does not distinguish data storage from file storage, or advice that treats the limits as a single combined number.

---

## Anti-Pattern 3: Recommending Attachments for New File Upload Features

**What the LLM generates:** "Use the Attachment sObject for storing user-uploaded files. Just set ParentId to the record Id and insert the Attachment."

**Why it happens:** The Attachment sObject has existed in Salesforce for years and appears extensively in training data. ContentDocument/ContentVersion patterns are more complex and less prevalent in older documentation that LLMs may weight heavily.

**Correct pattern:**

```apex
// Correct: Use ContentVersion + ContentDocumentLink
ContentVersion cv = new ContentVersion(
    Title = 'My File',
    PathOnClient = 'myfile.pdf',
    VersionData = fileBlob,
    IsMajorVersion = true
);
insert cv;

Id contentDocId = [SELECT ContentDocumentId FROM ContentVersion WHERE Id = :cv.Id].ContentDocumentId;

ContentDocumentLink link = new ContentDocumentLink(
    ContentDocumentId = contentDocId,
    LinkedEntityId = targetRecordId,
    ShareType = 'V',
    Visibility = 'AllUsers'
);
insert link;
// Benefit: file can be linked to multiple records without duplicating binary content
```

**Detection hint:** Any code that inserts an `Attachment` sObject for new development. The Attachment object is deprecated for new development in modern Salesforce.

---

## Anti-Pattern 4: Assuming Big Objects Consume Standard Data Storage

**What the LLM generates:** "If you move old records to Big Objects, you won't save any storage because they still use the same storage pool."

**Why it happens:** The LLM generalizes Salesforce's shared storage model without knowing the Big Object exception. Big Objects are a specialized feature less covered in mainstream training data.

**Correct pattern:**

```text
Big Objects have their own SEPARATE storage allocation, completely independent
of standard data storage. Migrating records from a standard custom object to
a Big Object:
- REDUCES standard data storage usage (removes records from the standard pool)
- DOES NOT reduce the Big Object allocation (they have separate, larger limits)

This makes Big Objects a valid storage reclamation strategy for append-only
data (audit logs, event history) with known query patterns.

Constraint: Big Objects require a defined composite index and support limited
SOQL (no aggregates without indexing, no relationship queries).
```

**Detection hint:** Any statement claiming Big Objects "count toward" the same storage limit as standard objects.

---

## Anti-Pattern 5: Suggesting Base64-Encoding Files Into Text Fields

**What the LLM generates:** "You can store the file content as a base64-encoded string in a Long Text Area field to avoid the complexity of ContentVersion."

**Why it happens:** Base64 encoding a file into a string field is a common workaround pattern in non-Salesforce systems where binary storage is not natively supported. LLMs trained on general programming content apply this pattern to Salesforce without understanding the platform's dedicated file storage model.

**Correct pattern:**

```text
Do NOT store binary content in Long Text Area or Rich Text Area fields.

Problems with the anti-pattern:
- Long Text Area max = 131,072 characters. A 100 KB PDF base64-encodes to ~133 KB
  — already over the limit.
- Even smaller files inflate the record size far beyond the 2 KB average, rapidly
  consuming data storage.
- No deduplication, versioning, preview generation, or sharing controls.
- Files are inaccessible via standard file download UIs.

Correct approach: ContentVersion for binary storage, Long Text Area only for
genuine text content (notes, unstructured descriptions, JSON metadata up to
the field limit).
```

**Detection hint:** Any code that calls `EncodingUtil.base64Encode()` and stores the result in a field of type `LongTextArea` or `TextArea`.

---

## Anti-Pattern 6: Ignoring ContentVersion Renditions in Storage Projections

**What the LLM generates:** "To calculate file storage needs, multiply average file size by expected number of uploads. For example: 10,000 files × 500 KB average = 5 GB."

**Why it happens:** The LLM uses a straightforward multiplication model that doesn't account for Salesforce's automatic rendition generation behavior, which is a platform-specific background process not commonly documented in general storage planning guides.

**Correct pattern:**

```text
Salesforce automatically generates preview renditions (thumbnails, PDF previews)
for each ContentVersion upload. Renditions are stored as additional ContentVersion
records and count toward file storage.

Storage projection formula:
  Effective file storage = raw upload size × rendition multiplier

Conservative estimate: multiply raw upload size by 1.5x to 2x to account for
renditions. Higher for image-heavy workloads (each image generates multiple
thumbnail sizes).

To audit actual rendition overhead:
SELECT IsLatest, COUNT(Id), SUM(ContentSize)
FROM ContentVersion
GROUP BY IsLatest

IsLatest = false records include renditions and older versions.
```

**Detection hint:** Storage projections that use simple (file count × average size) without any mention of rendition overhead.
