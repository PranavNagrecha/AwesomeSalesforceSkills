# LLM Anti-Patterns — High Volume Sales Data Architecture

Common mistakes AI coding assistants make when generating or advising on High Volume Sales Data Architecture.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending SOQL Without Considering Selectivity

**What the LLM generates:** Queries like `SELECT Id, Name FROM Opportunity WHERE Custom_Status__c = 'Active'` on a table with 5 million records, without checking whether `Custom_Status__c` is indexed or whether the filter returns fewer than 10% of rows.

**Why it happens:** LLMs generate syntactically correct SOQL based on the field name and filter value without awareness of table size, index existence, or the selectivity threshold. Training data rarely includes selectivity commentary.

**Correct pattern:**

```
-- Before writing the query, verify:
-- 1. Is Custom_Status__c indexed? (Standard fields have default indexes; custom fields do not unless requested)
-- 2. Does the filter return < 10% of total records (standard index) or < 5% (custom index)?
-- 3. If not selective, add a conjunction with an indexed field:
SELECT Id, Name FROM Opportunity
WHERE Custom_Status__c = 'Active'
AND CloseDate >= LAST_N_DAYS:90
```

**Detection hint:** Look for SOQL on Opportunity, Account, or OpportunityLineItem with a single WHERE clause on a custom field and no mention of index verification or selectivity.

---

## Anti-Pattern 2: Suggesting Record Archival via Recycle Bin or Soft Delete

**What the LLM generates:** Advice like "delete old Opportunities and they will remain in the Recycle Bin for 15 days" or "add an Is_Archived__c checkbox and filter it out in queries."

**Why it happens:** LLMs conflate logical archival with physical removal. Soft-delete patterns are common in general database advice. The LLM does not account for Salesforce's storage model where soft-deleted and checkbox-filtered records still consume storage and degrade query performance.

**Correct pattern:**

```
-- For true archival:
-- 1. Insert into Big Object (Archived_Opportunity__b) via Database.insertImmediate()
-- 2. Hard-delete originals after verification
-- 3. Use summary custom object for UI lookups if needed
-- Soft delete / checkbox filtering does NOT reduce query load or storage
```

**Detection hint:** Presence of `Is_Archived__c`, `Archived__c` checkbox fields, or mention of "recycle bin" in archival recommendations.

---

## Anti-Pattern 3: Ignoring the 10K Ownership Threshold for Skew

**What the LLM generates:** Recommendations to assign all imported or API-created records to a single integration user, or to use a dedicated "data admin" user as default owner for batch-loaded Accounts.

**Why it happens:** Centralizing ownership is a common pattern in non-Salesforce databases and simplifies permission logic. LLMs default to this because it is architecturally clean. They do not model the Salesforce sharing recalculation cost that makes single-owner concentration problematic above 10K records.

**Correct pattern:**

```
-- Instead of assigning all records to one integration user:
-- 1. Assign to territory-aligned queues during import
-- 2. Use after-insert automation to reassign to the correct owner
-- 3. Monitor ownership distribution: no single owner should exceed 10K records
-- on Account or Opportunity
```

**Detection hint:** Recommendations containing "assign all to integration user", "default owner for batch", or "single service account owner" without a skew warning.

---

## Anti-Pattern 4: Assuming Big Objects Support Synchronous SOQL

**What the LLM generates:** Code that queries a Big Object with standard SOQL in a Lightning controller or trigger, expecting inline results:
```apex
List<Archived_Opportunity__b> results = [SELECT Name__c FROM Archived_Opportunity__b WHERE Account__c = :accountId];
```

**Why it happens:** LLMs treat Big Objects like standard custom objects because the SOQL syntax looks identical. Training data rarely distinguishes between standard SOQL and Async SOQL execution contexts. The LLM does not know that Big Object queries in Apex are limited to the composite index fields and that large-scale reads require Async SOQL.

**Correct pattern:**

```
-- Big Objects support limited standard SOQL only on indexed fields (composite key).
-- For analytical queries, use Async SOQL which writes results to a target object:
-- System.enqueueJob() with an Async SOQL request, results land in a custom object.
-- For UI access, query a pre-populated summary custom object, not the Big Object directly.
```

**Detection hint:** Standard SOQL brackets `[SELECT ... FROM ...__b]` used in synchronous Apex contexts like Aura/LWC controllers or triggers.

---

## Anti-Pattern 5: Recommending Report-Level Fixes for Index-Level Problems

**What the LLM generates:** Advice to "restructure the report" or "use a different report type" or "add a cross-filter" when the real issue is a missing index on the Opportunity table. The LLM suggests report-design changes because it does not model the database layer.

**Why it happens:** LLMs see the symptom (slow report) and suggest UI-layer fixes. Salesforce report performance is predominantly an index and selectivity problem at high volumes, not a report-design problem. Changing the report type cannot compensate for a full table scan.

**Correct pattern:**

```
-- When a report is slow on a table with >200K records:
-- 1. Check filter fields for index coverage using Query Plan tool
-- 2. Calculate selectivity: filter result count / total record count
-- 3. If not selective, request a custom index via Salesforce Support
-- 4. If object is wide (200+ fields), request a skinny table
-- Only after index/skinny table are in place, optimize the report layout
```

**Detection hint:** Recommendations focused on "change report type", "use summary instead of tabular", "add cross-filter" without mentioning indexes, selectivity, or Salesforce Support case for custom index.

---

## Anti-Pattern 6: Conflating Salesforce Storage Limits with Query Performance

**What the LLM generates:** Statements like "you are under the storage limit so performance should be fine" or "upgrade to additional storage to fix slow queries."

**Why it happens:** LLMs associate storage quota with system health. In Salesforce, storage limits and query performance are independent concerns. An org can be at 20% storage utilization and still have non-selective queries timing out on a 3M-row Opportunity table.

**Correct pattern:**

```
-- Storage and performance are separate concerns:
-- Storage: governed by org edition limits (data storage, file storage)
-- Performance: governed by index coverage, selectivity, skew, and sharing model
-- Buying more storage does not improve query speed
-- Archival improves both but the primary driver should be query performance, not storage
```

**Detection hint:** Mentions of "storage limit", "buy more storage", or "storage utilization" in the context of query performance advice.
