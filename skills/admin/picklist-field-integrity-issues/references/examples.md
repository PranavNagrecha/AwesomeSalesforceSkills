# Examples — Picklist Field Integrity Issues

## Example 1: Data Loader Import Creates Orphaned Picklist Values

**Context:** A sales ops team uses Data Loader weekly to bulk-update Account records with regional classifications. The `Region__c` field is an unrestricted picklist with values like "North America", "EMEA", "APAC".

**Problem:** A CSV column contains "N. America" and "NA" — typos and abbreviations that don't match the defined picklist values. Because `Region__c` is unrestricted, Salesforce silently accepts every value. After six months, the org has 14 distinct Region values instead of 4, breaking reports and dashboards that filter on Region.

**Solution:**

```sql
-- Step 1: Audit actual values in the field
SELECT Region__c, COUNT(Id) cnt
FROM Account
GROUP BY Region__c
ORDER BY COUNT(Id) DESC

-- Step 2: Build a mapping of invalid → valid values
-- "N. America" → "North America"
-- "NA" → "North America"
-- "Emea" → "EMEA"

-- Step 3: Clean via Data Loader update with the corrected values
-- Step 4: Toggle the field to Restricted in Setup
-- Step 5: Test that Data Loader now rejects unknown values
```

**Why it works:** The GROUP BY audit surfaces every distinct value stored in data, regardless of what the picklist definition says. Cleaning before restricting ensures no existing records are left with orphaned values. Restricting the field prevents future pollution at the API layer.

---

## Example 2: Record Type Picklist Mapping Drift After Global Value Set Update

**Context:** An org uses a Global Value Set `CaseOrigin` shared across Case and a custom object. The admin adds a new value "Chat" to the GVS. Users on the "Support" record type report they cannot see "Chat" when creating Cases.

**Problem:** Adding a value to a Global Value Set makes it available on the field definition, but it is NOT automatically added to any record type's picklist mapping. The "Support" record type still shows only the previously mapped values. The admin assumed "global" meant "available everywhere."

**Solution:**

```text
1. Navigate to Setup > Object Manager > Case > Record Types > Support
2. Click Edit next to the Case Origin picklist
3. Move "Chat" from Available to Selected
4. Save
5. Repeat for every record type that should display the new value
6. Document the record type mapping update in the change log
```

**Why it works:** Record type picklist mappings are a separate configuration layer from the field's value set. Each record type independently controls which values are visible to users. This two-step process (add to GVS + map to record types) must be in every admin's deployment checklist.

---

## Anti-Pattern: Relying on Dependent Picklist Configuration as Data Validation

**What practitioners do:** Configure a dependent picklist relationship between `Country__c` (controlling) and `State__c` (dependent) and assume the platform will reject invalid combinations from all channels.

**What goes wrong:** An integration team uses REST API to create records. The API does not enforce dependent picklist filtering — any State value is accepted regardless of the Country value. Over time, the data contains impossible combinations like Country="Japan", State="Texas".

**Correct approach:** Deploy a validation rule that explicitly checks the controlling-dependent relationship:

```text
AND(
  ISPICKVAL(Country__c, "United States"),
  NOT(
    OR(
      ISPICKVAL(State__c, "California"),
      ISPICKVAL(State__c, "Texas"),
      ISPICKVAL(State__c, "New York")
      /* ... all valid US states */
    )
  )
)
```

For large value sets, use an Apex before-trigger with a Custom Metadata map of valid combinations instead of an enormous validation rule formula.
