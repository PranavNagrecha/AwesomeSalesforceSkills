# LLM Anti-Patterns — Picklist Field Integrity Issues

Common mistakes AI coding assistants make when generating or advising on picklist field integrity.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Claiming Dependent Picklists Are Enforced by the API

**What the LLM generates:** "Since you have a dependent picklist configured, the API will reject any record where the dependent value doesn't match the controlling field. No additional validation is needed."

**Why it happens:** LLMs conflate UI behavior with platform-wide enforcement. Training data includes Salesforce Setup documentation that describes how dependent picklists work in the UI, and the model generalizes this to all data entry channels.

**Correct pattern:**

```text
Dependent picklist filtering is enforced ONLY in the Lightning and Classic UI.
API, Data Loader, Bulk API, Apex DML, and Flows in system context do NOT enforce
the controlling-dependent mapping. To enforce at the data layer, add a validation
rule or Apex before-trigger that explicitly checks the combination.
```

**Detection hint:** Look for advice saying dependent picklists "enforce" or "prevent" invalid combinations without mentioning the UI-only limitation or recommending a validation rule.

---

## Anti-Pattern 2: Suggesting Restriction Toggle Alone Fixes Historical Data

**What the LLM generates:** "To fix the data quality issue, go to Setup and check 'Restrict picklist to the values defined in the value set.' This will clean up the invalid values."

**Why it happens:** LLMs compress multi-step remediation into a single action. The toggle is the most visible step, so it dominates the output. The model does not distinguish between prospective enforcement and retroactive cleanup.

**Correct pattern:**

```text
Toggling to restricted prevents FUTURE invalid writes only. Existing records with
invalid values are NOT cleaned. You must:
1. Audit existing values (GROUP BY query)
2. Clean invalid records (Data Loader or Apex batch)
3. THEN toggle to restricted
4. Test that future invalid API writes are rejected
```

**Detection hint:** Look for single-step remediation that mentions only the restriction toggle without a preceding data audit and cleanup step.

---

## Anti-Pattern 3: Assuming Global Value Set Changes Auto-Propagate to Record Types

**What the LLM generates:** "Add the new value to the Global Value Set and it will automatically be available to all users across all record types."

**Why it happens:** The phrase "Global Value Set" implies global availability. LLMs infer that "global" means "everywhere" without accounting for the record type picklist mapping layer.

**Correct pattern:**

```text
Adding a value to a Global Value Set makes it available on the FIELD definition.
It does NOT automatically appear in any record type's picklist mapping. After
adding a GVS value, you must also:
1. Go to Setup > Object Manager > [Object] > Record Types > [Each Record Type]
2. Edit the picklist and add the new value
3. Repeat for every record type that should offer the new value
```

**Detection hint:** Look for GVS advice that does not mention record type mapping as a follow-up step.

---

## Anti-Pattern 4: Hardcoding Picklist Values in Apex Validation

**What the LLM generates:**

```apex
Set<String> validValues = new Set<String>{'Open', 'Closed', 'Pending', 'Escalated'};
if (!validValues.contains(record.Status__c)) {
    record.addError('Invalid status value');
}
```

**Why it happens:** LLMs generate inline hardcoded sets because they are simple and self-contained. The model does not consider that picklist values change over time and require code redeployment.

**Correct pattern:**

```apex
Schema.DescribeFieldResult dfr = Account.Status__c.getDescribe();
Set<String> validValues = new Set<String>();
for (Schema.PicklistEntry pe : dfr.getPicklistValues()) {
    if (pe.isActive()) {
        validValues.add(pe.getValue());
    }
}
if (!validValues.contains(record.Status__c)) {
    record.addError('Invalid status: ' + record.Status__c);
}
```

**Detection hint:** Look for `new Set<String>{'value1', 'value2'}` patterns in Apex picklist validation code.

---

## Anti-Pattern 5: Using getPicklistValues() Without Record Type Context

**What the LLM generates:**

```apex
Schema.DescribeFieldResult dfr = Case.Priority.getDescribe();
List<Schema.PicklistEntry> entries = dfr.getPicklistValues();
// Use entries to populate a UI component
```

**Why it happens:** LLMs default to the simpler `getPicklistValues()` method which returns the master list. They don't account for record type filtering, which requires the UI API `getPicklistValues` wire adapter or `getPicklistValuesByRecordType`.

**Correct pattern:**

```text
Schema.DescribeFieldResult.getPicklistValues() returns the MASTER picklist
definition — all values regardless of record type. For record-type-aware
values, use the UI API:
  GET /ui-api/object-info/{objectApiName}/picklist-values/{recordTypeId}

In LWC, use the getPicklistValuesByRecordType wire adapter which respects
both record type mapping AND controlling field dependencies.
```

**Detection hint:** Look for `getPicklistValues()` used to populate UI components without any record type ID parameter or UI API reference.

---

## Anti-Pattern 6: Recommending SOQL NOT IN for Picklist Audit

**What the LLM generates:** "To find invalid values, query: `SELECT Id FROM Account WHERE Status__c NOT IN ('Active', 'Inactive', 'Pending')`"

**Why it happens:** LLMs generate brute-force exclusion queries because they don't know the full value set. This breaks when new valid values are added.

**Correct pattern:**

```sql
-- Use GROUP BY to discover all distinct values, then compare against the
-- defined set externally. This approach is additive and doesn't require
-- the query author to know all valid values.
SELECT Status__c, COUNT(Id) FROM Account GROUP BY Status__c ORDER BY COUNT(Id) DESC
```

**Detection hint:** Look for WHERE clauses that enumerate all valid values with `NOT IN` for audit purposes.
