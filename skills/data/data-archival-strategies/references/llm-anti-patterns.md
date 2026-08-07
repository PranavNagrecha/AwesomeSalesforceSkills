# LLM Anti-Patterns — Data Archival Strategies

Common mistakes AI coding assistants make when generating or advising on Salesforce data archival strategies.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Big Objects as a General-Purpose Archive Without Noting Query Limitations

**What the LLM generates:** "Archive old records to a Big Object and query them as needed" without explaining that Big Objects can only be queried using SOQL with exact match filters on composite index fields, and do not support wildcards, LIKE, OR, aggregate functions, or ORDER BY on non-index fields.

**Why it happens:** LLMs treat Big Objects as a "large table" equivalent from relational databases. The severe query constraints unique to Big Objects are underrepresented in training data.

**Correct pattern:**

```text
Big Object query constraints:
- SOQL only, with filters on composite index fields
- First index field: = (equals) only
- Subsequent fields: =, <, >, <=, >=, IN
- Last index field can use range operators
- No LIKE, no wildcards, no OR clauses
- No GROUP BY, no aggregate functions (COUNT, SUM, etc.)
- No ORDER BY on non-index fields (results are always ordered by index)
- No subqueries or relationship queries

Design the composite index to match your most common query pattern.
If ad-hoc querying is needed, Big Objects are the wrong archival target.
```

**Detection hint:** Flag Big Object recommendations that do not mention composite index query constraints or that suggest LIKE, OR, or aggregate queries on Big Objects.

---

## Anti-Pattern 2: Forgetting That Big Object Inserts Are Fire-and-Forget

**What the LLM generates:** Apex code using `Database.insertImmediate()` for Big Objects without error handling, treating it like standard DML with full error reporting.

**Why it happens:** Standard DML operations return `SaveResult` objects with success/failure information per record. `Database.insertImmediate()` for Big Objects is asynchronous and does not return per-record errors — failures are silent unless you check debug logs.

**Correct pattern:**

```text
Big Object insert behavior:
- Use Database.insertImmediate(records) — NOT standard insert
- Returns void, not SaveResult[]
- Failures are silent — no exception, no per-record error
- Check debug logs for UNABLE_TO_INSERT errors
- Duplicates (same composite index values) silently overwrite existing records

Error handling strategy:
1. Validate data before insertion (all index fields non-null)
2. Log the batch ID and record count for reconciliation
3. Query the Big Object after insertion to verify record count
4. Verify archived data completeness with Batch Apex over the Big Object
   (Async SOQL was retired in Summer '23 — do not use async-queries)
```

**Detection hint:** Flag `Database.insertImmediate()` calls without subsequent verification or logging. Look for missing error handling after Big Object DML.

---

## Anti-Pattern 3: Overlooking Recycle Bin Impact on Storage Reclamation

**What the LLM generates:** "Delete 5 million old records to free up storage" without mentioning that deleted records go to the Recycle Bin and continue consuming storage for 15 days before being hard-deleted automatically.

**Why it happens:** Most training data discusses delete as an immediate storage reclamation. The Recycle Bin's 15-day retention and its storage impact are operational details not commonly covered in development-focused content.

**Correct pattern:**

```text
Storage reclamation after record deletion:

1. Soft delete (standard delete): records move to Recycle Bin
   - Storage is NOT freed for 15 days (or until Recycle Bin is emptied)
   - Recycle Bin limit: 25 x data storage (MB) or 25,000 records,
     whichever is greater

2. Hard delete (Bulk API with hardDelete operation):
   - Bypasses Recycle Bin — storage freed immediately
   - Requires "Bulk API Hard Delete" permission enabled on the profile
   - Cannot be undone — no recovery possible

3. Empty Recycle Bin programmatically:
   Database.emptyRecycleBin(recordIds) — permanently deletes records

For large archival deletions, use Bulk API hardDelete to avoid
Recycle Bin overflow and delayed storage reclamation.
```

**Detection hint:** Flag deletion-based archival recommendations that do not mention Recycle Bin behavior. Look for "delete to free storage" without `hardDelete` or `emptyRecycleBin` references.

---

## Anti-Pattern 4: Recommending External Storage Without Addressing Reporting and Lookup Requirements

**What the LLM generates:** "Archive records to Amazon S3 or Heroku Postgres to reduce Salesforce storage" without evaluating whether users need to view archived data in Salesforce reports, relate archived records to active records, or search archived data from within the Salesforce UI.

**Why it happens:** External storage is technically straightforward and well-documented outside Salesforce. LLMs recommend it without assessing the Salesforce-specific implications: broken report history, orphaned lookup references, and user experience disruption when records "disappear."

**Correct pattern:**

```text
External archival readiness checklist:
1. Reporting: will users need to report on archived data?
   - If yes: consider Big Objects (limited reporting) or keep a summary
     record in Salesforce with a link to the archived detail.
2. Lookup integrity: do active records reference the archived records?
   - If yes: broken lookups will display "Data Not Available" — consider
     soft-archiving (custom status field) instead of deletion.
3. Search: do users need to find archived records from Salesforce?
   - If yes: use Salesforce Connect with External Objects for virtual access.
4. Compliance: do regulations require data to remain in Salesforce?
   - If yes: use Big Objects or Shield Field Audit Trail instead.

External storage is best for: pure cold storage, data lake feeds, or
data that was never frequently accessed in Salesforce.
```

**Detection hint:** Flag external archival recommendations that do not assess reporting, lookup integrity, or user search requirements.

---

## Anti-Pattern 5: Confusing Field Audit Trail with Field History Tracking for Archival

**What the LLM generates:** "Enable Field History Tracking to retain an audit trail of field changes for compliance" without distinguishing between standard Field History Tracking (18-month retention, 20 fields per object) and Shield Field Audit Trail (up to 10 years, configurable retention policy, FieldHistoryArchive object).

**Why it happens:** Both features track field changes, and their names are similar. LLMs conflate the two, often recommending the free feature (Field History Tracking) when the compliance requirement demands the paid Shield feature (Field Audit Trail).

**Correct pattern:**

```text
Field History Tracking vs Shield Field Audit Trail:

Field History Tracking (included with all editions):
- Up to 20 fields per object
- 18-month retention (data automatically deleted after 18 months)
- Queried via AccountHistory, OpportunityHistory, etc.
- No configurable retention policy

Shield Field Audit Trail (requires Shield license):
- Up to 60 fields per object
- Up to 10-year retention with configurable policies
- Data stored in FieldHistoryArchive object
- Supports compliance requirements (FINRA, HIPAA, SOX)

For compliance archival, Field History Tracking is NOT sufficient.
Field Audit Trail (Shield) is required for long-term retention.
```

**Detection hint:** Flag compliance-driven archival recommendations that reference "Field History Tracking" without mentioning its 18-month limit. Check whether Shield Field Audit Trail is evaluated.

---

## Anti-Pattern: Quoting a "1 GB Base" Storage Allocation, or Counting the Recycle Bin

**What the LLM generates:** A storage-capacity paragraph of the shape "Essentials and Professional get 1 GB base; Enterprise and Unlimited get 10 GB base plus 20 MB per user licence," or "Enterprise gets 1 GB base plus 2 GB per user licence for file storage." Usually paired with "deleted records keep consuming storage in the Recycle Bin, so empty it to reclaim space."

**Why it happens:** Every number in those sentences is a real Salesforce figure attached to the wrong dimension. **1 GB** is the *file* storage allocation for Essentials and Starter — it gets promoted into a data-storage base and spread across editions that do not have it. **20 MB** is the per-user data-storage increment, correct for Enterprise but not for Performance/Unlimited (120 MB). The Recycle Bin claim is a plausible inference from how most databases behave, reinforced by the genuine observation that Setup > Storage Usage often does not move right after a mass delete.

**Correct version:**

```text
Data storage base: 10 GB for Contact Manager, Group, Essentials, Professional,
                   Enterprise, Performance, Unlimited, Starter.
Per-user data:     20 MB/licence  (Enterprise, Professional, Contact Manager, Group)
                   120 MB/licence (Performance, Unlimited)
                   none           (Essentials, Starter)
File storage:      10 GB/org (Contact Manager, Group, Professional, Enterprise,
                   Performance, Unlimited); 1 GB (Essentials, Starter);
                   20 MB (Developer, Personal). Per-user file increments depend
                   on the USER LICENCE type - read the table, do not quote one number.

Recycle Bin: records in it do NOT count against storage, and the bin has no
             record-count cap. 15 days is the RESTORE window.
Why storage looks unchanged after a big delete: both pools are recalculated
             ASYNCHRONOUSLY. Wait and re-check.
```

**Why it matters for archival specifically:** the whole business case for an archival project is a storage number. Sizing against a fabricated 1 GB base under-states headroom by an order of magnitude and can justify a project the org did not need; budgeting reclaimed storage against "emptying the Recycle Bin" books a saving that will never appear, and the operation destroying the 15-day restore window is irreversible.

**Detection hint:** `grep -niE '1 ?GB base|2 ?GB per user' <files>` — neither shape is a real data-storage figure. And flag any storage allocation quoted without naming both the edition *and* whether the number is per-org or per-user-licence; a correct citation of this table cannot be a bare number.
