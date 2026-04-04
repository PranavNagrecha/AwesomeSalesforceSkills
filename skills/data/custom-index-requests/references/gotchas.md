# Gotchas — Custom Index Requests

## 1. External ID Creates a UNIQUE Index, Not a Generic Index

**What happens:** A developer wants to index `LeadSource__c` on the Lead object for a filter query. They mark `LeadSource__c` as External ID in the field definition, expecting this to create an index. Salesforce creates the index but also enforces uniqueness — any attempt to insert two Leads with the same `LeadSource__c` value now fails with a unique constraint violation.

**Why:** External ID in Salesforce means two things simultaneously: (1) this field is indexed, and (2) this field is unique. They cannot be separated via the External ID flag.

**How to avoid:** Use External ID only for fields that are genuinely unique integration keys. For non-unique filter fields, open a Salesforce Support case requesting a non-unique custom index. Do not use External ID as a hack to get an index.

---

## 2. Custom Indexes Are Not Copied to Partial or Developer Sandboxes

**What happens:** Salesforce Support creates a custom index on `Account.CustomerType__c` in production. A developer refreshes their Developer sandbox and runs the slow query — it still uses a TableScan. They report "the index isn't working" when actually it was never copied to the Developer sandbox.

**Why:** Only Full sandbox refreshes copy custom indexes and skinny tables from production. Partial and Developer sandboxes do not include database-level customizations.

**How to avoid:** All performance testing that requires custom indexes must be done in a Full sandbox or production (with caution). Do not rely on Developer or Partial sandboxes for index validation.

---

## 3. Index Selectivity Changes as Data Grows

**What happens:** A custom index on `Status__c` is created when the org has 200,000 records and `Status = 'Active'` = 8% (16,000 records). Over 2 years, the org grows to 5 million records and `Status = 'Active'` = 12% (600,000 records). The query optimizer stops using the index and queries degrade to TableScan.

**Why:** Salesforce's query optimizer dynamically recalculates selectivity at query time. If the field's value distribution changes so that the filter now matches more than 10% of records, the optimizer abandons the index.

**How to avoid:** Monitor Query Plan output on high-volume objects quarterly. When a query starts slowing down again after a previously successful period, re-run the Query Plan to check if selectivity has changed. The fix may require additional WHERE clause conditions.

---

## 4. Two-Column Index Column Order Must Match Query Pattern

**What happens:** Salesforce Support creates a two-column index on `(OwnerId, Status__c)` based on a request. A developer then changes the primary query to `WHERE Status__c = 'Open' AND OwnerId = :userId` (Status first, OwnerId second). The index is not used because the leading column is OwnerId, not Status.

**Why:** A two-column index is most effective when the query's first filter condition matches the leading column of the index. If the query filters on the second column first, the index cannot be used for that filter pattern.

**How to avoid:** Specify the exact column order in the Support case based on the actual query pattern. If the query is `WHERE A = :x ORDER BY B`, request the index as `(A, B)`. If the query pattern later changes, open a new Support case to request the reordered index.
