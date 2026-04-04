# LLM Anti-Patterns — Custom Index Requests

## 1. Recommending External ID as a Generic Index Solution

**What the LLM generates wrong:** "To improve query performance on `Status__c`, mark it as an External ID field to create an index."

**Why it happens:** External ID creates an index, and the LLM correctly identifies that indexes improve query performance. It misses the uniqueness implication.

**Correct pattern:** External ID enforces uniqueness and creates an indexed field intended for integration cross-reference keys. For non-unique filter fields, request a non-unique custom index via Salesforce Support. Using External ID on non-unique fields causes `DUPLICATE_VALUE` errors on insert/update.

**Detection hint:** Any recommendation to mark a non-integration-key field as External ID for performance reasons.

---

## 2. Claiming `CREATE INDEX` SQL Syntax Works in Salesforce

**What the LLM generates wrong:** "Run `CREATE INDEX idx_status ON Account (Status__c)` to add an index."

**Why it happens:** Standard SQL has `CREATE INDEX` statements. The LLM applies relational database patterns to Salesforce.

**Correct pattern:** Salesforce does not expose a SQL layer to customers. Indexes are managed by the Salesforce platform, not by customer SQL queries. Custom index requests go through (1) Metadata API for custom field External ID flags, or (2) Salesforce Support cases for non-unique indexes on any field.

**Detection hint:** Any `CREATE INDEX`, `ALTER TABLE`, or SQL DDL syntax in a Salesforce context.

---

## 3. Suggesting Index Requests Before Validating Selectivity

**What the LLM generates wrong:** "Open a Support case to request a custom index on `Region__c` to speed up the query."

**Why it happens:** The LLM pattern-matches "slow query" → "request index" without checking selectivity.

**Correct pattern:** Before requesting any custom index, validate that the filter field is selective — it must match fewer than 10% of records. Run the Query Plan tool to confirm TableScan and estimate selectivity. An index on a non-selective field will not be used by the query optimizer, and the Support case will have been filed for no benefit.

**Detection hint:** Any custom index recommendation that does not include a selectivity check or Query Plan analysis step.

---

## 4. Not Mentioning the Developer Sandbox Limitation for Index Testing

**What the LLM generates wrong:** "After Salesforce creates the custom index, test it in your Developer sandbox."

**Why it happens:** Developer sandboxes are the standard testing environment mentioned in most Salesforce guidance. The LLM applies this without knowing the index copy limitation.

**Correct pattern:** Custom indexes and skinny tables are only copied to Full sandbox refreshes — not to Partial or Developer sandboxes. Index performance testing must be done in a Full sandbox or in production (with caution). A Developer sandbox will always show a TableScan for the indexed field.

**Detection hint:** Any instruction to test index performance in a Developer or Partial sandbox.

---

## 5. Claiming Custom Field Indexes Are Automatically Created for All Custom Fields

**What the LLM generates wrong:** "All custom fields on Salesforce objects are automatically indexed."

**Why it happens:** Some database platforms auto-index all columns. The LLM applies this assumption to Salesforce.

**Correct pattern:** Only specific field types are automatically indexed: External ID fields, Unique fields, and lookup relationship fields. Standard custom fields (text, number, picklist, etc.) are NOT indexed by default. Unindexed fields on high-volume objects result in TableScans when used as WHERE clause filters.

**Detection hint:** Any claim that custom fields are "automatically indexed" or "indexed by default" in Salesforce.
