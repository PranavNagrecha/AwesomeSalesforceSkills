# Examples — NPSP Data Model

## Example 1: Querying GAU Allocations Linked to a Set of Opportunities

**Context:** A nonprofit's finance team needs a report showing how each closed-won Opportunity's revenue is split across General Accounting Units (GAUs) — for example, 60% to Program A and 40% to Admin. The developer needs to write SOQL to retrieve this data.

**Problem:** Developers unfamiliar with NPSP attempt to traverse from Opportunity to allocations using a relationship subquery (e.g., `SELECT (SELECT ... FROM Allocations__r) FROM Opportunity`). This fails because `npsp__Allocation__c` is linked to Opportunity via a lookup, not a master-detail relationship. There is no standard child relationship name to traverse from Opportunity to its allocations.

**Solution:**

```soql
-- Query allocations directly, filtering by parent Opportunity IDs
SELECT
    Id,
    npsp__Amount__c,
    npsp__Percent__c,
    npsp__General_Accounting_Unit__c,
    npsp__General_Accounting_Unit__r.Name,
    npsp__Opportunity__c,
    npsp__Opportunity__r.Name,
    npsp__Opportunity__r.Amount,
    npsp__Opportunity__r.CloseDate
FROM npsp__Allocation__c
WHERE npsp__Opportunity__c IN (
    SELECT Id FROM Opportunity
    WHERE StageName = 'Closed Won'
    AND CloseDate = THIS_FISCAL_YEAR
)
ORDER BY npsp__Opportunity__c, npsp__Percent__c DESC
```

**Why it works:** `npsp__Allocation__c` is the correct object name (uses the `npsp__` namespace, not `npe01__`). The relationship from allocation to Opportunity is a lookup, so you always query the allocation side and filter by the parent Opportunity ID. The cross-object field traversal `npsp__Opportunity__r.Name` works because the lookup relationship supports it.

---

## Example 2: Querying Recurring Donations and Their Open Installment Opportunities

**Context:** A data migration team needs to export all open recurring donations and their future-dated installment Opportunities before switching the org to a new donation processing system.

**Problem:** The team tries to find installment Opportunities using a naming convention (e.g., Opportunity Name contains "Recurring") or by date range. This misses Opportunities and includes non-installment records. Some developers also use the wrong object API name — `npsp__Recurring_Donation__c` — which does not exist.

**Solution:**

```soql
-- Step 1: Get all open recurring donations
SELECT
    Id,
    Name,
    npe03__Amount__c,
    npe03__Installment_Period__c,
    npe03__Date_Established__c,
    npe03__Open_Ended_Status__c,
    npe03__Contact__c,
    npe03__Contact__r.Name,
    npe03__Organization__c,
    npe03__Organization__r.Name
FROM npe03__Recurring_Donation__c
WHERE npe03__Open_Ended_Status__c = 'Open'
ORDER BY npe03__Date_Established__c DESC

-- Step 2: For each recurring donation, get its unpaid installment Opportunities
SELECT
    Id,
    Name,
    Amount,
    StageName,
    CloseDate,
    npe03__Recurring_Donation__c,
    npe03__Recurring_Donation__r.npe03__Amount__c
FROM Opportunity
WHERE npe03__Recurring_Donation__c IN :rdIds
  AND IsClosed = FALSE
ORDER BY npe03__Recurring_Donation__c, CloseDate ASC
```

**Why it works:** `npe03__Recurring_Donation__c` is the correct object API name (uses the `npe03__` namespace). The lookup field on Opportunity (`npe03__Recurring_Donation__c`) is a custom field added by NPSP — it is the authoritative way to identify installment Opportunities. Filtering by `IsClosed = FALSE` isolates open installments without relying on naming conventions.

---

## Example 3: Safely Deleting an Opportunity With GAU Allocations

**Context:** A data cleanup process needs to delete a batch of duplicate or erroneous Opportunity records in an NPSP org.

**Problem:** A developer issues a bulk delete of Opportunities without first checking for related `npsp__Allocation__c` records. Because the relationship is a lookup (not master-detail), Salesforce does not cascade-delete the allocations. After the Opportunity delete, orphaned allocation records remain in the org with their `npsp__Opportunity__c` lookup field pointing to a deleted record ID. These orphans inflate GAU totals in reports.

**Solution:**

```apex
// Safe Opportunity deletion pattern — handle allocations first
List<Id> oppIdsToDelete = new List<Id>{ /* IDs here */ };

// Step 1: Query orphan-risk allocations
List<npsp__Allocation__c> allocs = [
    SELECT Id
    FROM npsp__Allocation__c
    WHERE npsp__Opportunity__c IN :oppIdsToDelete
];

// Step 2: Delete allocations first
if (!allocs.isEmpty()) {
    delete allocs;
}

// Step 3: Delete Opportunities
List<Opportunity> oppsToDelete = [
    SELECT Id FROM Opportunity WHERE Id IN :oppIdsToDelete
];
delete oppsToDelete;
```

**Why it works:** Explicitly querying and deleting `npsp__Allocation__c` records before the Opportunity ensures no orphaned allocations remain. This pattern must be applied in any bulk delete script, Data Loader operation (requires manual pre-step), or migration script that touches NPSP Opportunities.

---

## Anti-Pattern: Using npsp__ Prefix for All NPSP Objects

**What practitioners do:** Prefix every NPSP object reference with `npsp__` because "that's the NPSP namespace."

**What goes wrong:** `npsp__OppPayment__c` does not exist. The correct object is `npe01__OppPayment__c`. SOQL queries against `npsp__OppPayment__c` fail silently with zero results. Apex referencing this type fails at compile time only if the code is written in the org; if generated externally and deployed, it causes a deploy error.

**Correct approach:** Use the five-prefix reference table in SKILL.md to look up the exact namespace for each object. Payments = `npe01__`, Recurring Donations = `npe03__`, Relationships = `npe4__`, Affiliations = `npe5__`, GAUs and Allocations = `npsp__`.
