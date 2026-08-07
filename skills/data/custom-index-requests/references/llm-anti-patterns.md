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

---

## Anti-Pattern: `externalId: false` "Creates a Non-Unique Index"

**What the LLM generates:** Metadata API guidance of the form "deploy the `CustomField` with `externalId: false` to create a non-unique custom index — no Support case required," sometimes framed as the lightweight alternative to marking a field Unique.

**Why it happens:** The surrounding model is right and only the polarity is wrong, which is what makes it survive review. There *is* a self-service path to a custom index, it *does* go through the `CustomField` metadata type, it *does* avoid a Support case, and unique-vs-non-unique *is* a real distinction in Salesforce indexing. The `externalId` boolean then reads like a mode selector — `true` for the unique flavour, `false` for the non-unique one — rather than an on/off switch. `false` is simply the default value that every unindexed field in the org already carries.

**Correct version:** Salesforce creates a custom index automatically when a field is marked **External ID** (`externalId: true`) or **Unique** (`unique: true`) — per Salesforce Help 000383981, no Support case is needed for either. `externalId: false` is the default and produces **no index whatsoever**. Everything else — indexes on standard fields, null-inclusive indexes, two-column indexes, skinny tables — requires a Support case.

**Why it is dangerous:** the deployment succeeds. `externalId: false` is valid metadata, so there is no error, no warning, and no failed deploy to investigate. The team believes an index exists, the query stays a full table scan, and the subsequent debugging looks for a *selectivity* problem (is the filter under 10%?) rather than an *existence* problem, because the index is assumed to be there. Confirming with the Query Plan tool shows `TableScan` with no explanation.

**Detection hint:** `grep -rn 'externalId>false\|externalId: false' --include='*.field-meta.xml' .` in any context where the surrounding text claims an index is being created. Positively: an index-creation change must set `externalId` or `unique` to **true**, or it must be a Support case — there is no third path.

---

## Anti-Pattern: Quoting One Selectivity Percentage, or Swapping the Two Caps

**What the LLM generates:** "A filter is selective if it matches fewer than 10% of records," stated flatly for all index types; or a threshold table pairing a cap with the wrong index type — "333,333 records for standard indexes, 100,000 for custom indexes."

**Why it happens:** The rule has four numbers per index type (a first-million percentage, a beyond-a-million percentage, and an absolute ceiling) and the numbers across the two index types are close enough to swap cleanly. 100,000 in particular is a real intermediate value — it is 10% of the first million, one line of the custom-index calculation — so it looks like a threshold in its own right and gets promoted to one. The flat "10%" version is the custom-index first-million figure with the decay and the ceiling both dropped.

**Correct version:**

```text
Standard index: < 30% of the first million targeted records
                < 15% of records beyond the first million
                ceiling 1,000,000 targeted records

Custom index:   < 10% of the first million targeted records
                <  5% of records beyond the first million
                ceiling   333,333 targeted records
```

The standard index always has the *looser* thresholds and the *higher* ceiling. Any statement in which the standard index is more restrictive than the custom index is inverted.

**Detection hint:** `grep -rniE '333,?333.*standard|standard.*333,?333|100,?000 for custom'` — the 333,333 ceiling belongs to custom indexes only. Also flag any single-percentage selectivity claim: a correct citation of this rule names two percentages and a cap, because the threshold decays past one million records.
