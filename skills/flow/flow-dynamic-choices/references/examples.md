# Examples — Flow Dynamic Choices

## Example 1: Active Account picker

**Context:** Case creation flow

**Problem:** Hard-coded account names

**Solution:**

Record Choice Set: Account WHERE IsActive__c=true LIMIT 50 ORDER BY Name

**Why it works:** Always current


---

## Example 2: Country → State dependent

**Context:** Address capture

**Problem:** All states shown regardless of country

**Solution:**

Two Record Choice Sets; State_Choice filtered by {!SelectedCountry}

**Why it works:** Reactive filter on selection

