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
4. Use Async SOQL to bulk-verify archived data completeness
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
