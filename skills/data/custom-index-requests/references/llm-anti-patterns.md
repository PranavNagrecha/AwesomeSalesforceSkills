# LLM Anti-Patterns — Custom Index Requests

Common mistakes AI coding assistants make when advising on custom indexes, skinny tables, and index requests. These patterns help the consuming agent self-check its own output.

## Anti-pattern 1: Saying External ID Enforces Uniqueness

**What the LLM generates:** "Don't mark `Region__c` as External ID; it will reject duplicate values," or "External ID guarantees our integration keys are unique."

**Why it happens:** External ID and Unique often appear together in examples, and models merge them into one concept.

**Correct pattern:** They are separate `CustomField` booleans. Either one makes Salesforce index the field. Only `unique` enforces uniqueness; with External ID alone, duplicates can exist, and an upsert whose key matches several records fails with a 300 error.

**Detection hint:** Any sentence linking External ID to "unique index," "enforces uniqueness," or `DUPLICATE_VALUE`, without mentioning the separate `unique` flag.

---

## Anti-pattern 2: Believing `externalId: false` Creates a Non-Unique Index

**What the LLM generates:** "Deploy the field with `externalId: false` and `unique: false` to create a non-unique index, no Support case needed."

**Why it happens:** The boolean reads like a mode selector instead of an on/off switch.

**Correct pattern:** `false` is the default every unindexed field already has; it creates nothing. A self-service index needs `externalId` or `unique` set to **true** (on Auto Number, Email, Number, or Text); anything else is a Support case.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Partner_Key__c</fullName>
    <label>Partner Key</label>
    <type>Text</type>
    <length>20</length>
    <externalId>true</externalId>
</CustomField>
```

**Detection hint:** A field change described as "adding an index" whose metadata leaves both `externalId` and `unique` false.

---

## Anti-pattern 3: Generating SQL DDL

**What the LLM generates:** `CREATE INDEX idx_status ON Account (Status__c)`.

**Why it happens:** Relational habits.

**Correct pattern:** Customers have no SQL layer. Indexes come from field flags, a Support case, or a `CustomIndex` component deployed after Support has agreed the index (its special access rule says to contact Customer Support).

**Detection hint:** `CREATE INDEX`, `ALTER TABLE`, or any DDL in a Salesforce answer.

---

## Anti-pattern 4: Requesting an Index Without Threshold Arithmetic

**What the LLM generates:** "Open a Support case to index `Region__c`," with no counts.

**Why it happens:** "Slow query → index" is a reflex.

**Correct pattern:**

```text
Object rows N (include Recycle Bin rows).
Custom-index threshold = 10% x min(N, 1,000,000) + 5% x max(N - 1,000,000, 0)
  e.g. N = 5,000,000 -> 100,000 + 200,000 = 300,000 (LDV guide example)
Standard-index threshold = 30% x min(N, 1,000,000) + 15% x max(N - 1,000,000, 0)
  e.g. N = 2,000,000 -> 300,000 + 150,000 = 450,000 (LDV guide example)
Count the filter value with GROUP BY; if it is above the threshold, change the query.
```

**Detection hint:** An index recommendation with no row count, no value count, or a single flat percentage for every index type.

---

## Anti-pattern 5: Telling Teams Custom Indexes Never Reach Developer Sandboxes

**What the LLM generates:** "Custom indexes are only copied to Full sandboxes, so test in Full only."

**Why it happens:** The skinny-table rule (Full sandboxes only) is applied to custom indexes too.

**Correct pattern:** The LDV guide says custom indexes created by Customer Support in production are copied to all sandboxes created from that production org; skinny tables are the ones copied only to Full sandboxes.

**Detection hint:** A sandbox rule that treats custom indexes and skinny tables the same way.

---

## Anti-pattern 6: Promising a Fixed Speed-Up From a Skinny Table

**What the LLM generates:** "A skinny table will cut I/O by 95%," or a skinny table recommended for a query whose filter matches most of the object.

**Why it happens:** Models over-generalize from "fewer columns."

**Correct pattern:** A skinny table removes the join between the standard and custom field tables for read-only operations that use only its fields. It does not make a non-selective filter selective, and the LDV guide warns it can degrade performance in the wrong context. Describe the mechanism, not a percentage, and verify with timings.

**Detection hint:** A percentage improvement attached to a skinny-table recommendation, or a skinny table proposed for a write-heavy or non-selective workload.
