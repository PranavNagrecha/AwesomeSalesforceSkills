# Examples — FSC Data Model

## Example 1: Mapping a Client's Investment Portfolio Using FinancialHolding and FinancialAccountRole

**Context:** A wealth management firm is implementing FSC on a managed-package org. An advisor needs to display a client's complete investment portfolio — all brokerage accounts, the securities held within them, and the client's ownership role — on the client's Person Account record.

**Problem:** The developer queries `FinServ__FinancialAccount__c` filtering only on `FinServ__PrimaryOwner__c`. Accounts where the client is a joint owner are silently excluded. Additionally, the developer attempts to retrieve holding values using a standard ROLLUP summary on the Account, which returns null because FSC holdings are not aggregated through standard master-detail relationships.

**Solution:**

```soql
// Step 1: Get all financial accounts where the client is primary OR joint owner
SELECT Id, Name, FinServ__FinancialAccountType__c, FinServ__Balance__c,
       FinServ__Status__c, FinServ__PrimaryOwner__r.Name, FinServ__JointOwner__r.Name
FROM FinServ__FinancialAccount__c
WHERE FinServ__PrimaryOwner__c = :clientContactId
   OR FinServ__JointOwner__c = :clientContactId

// Step 2: For each account, retrieve financial holdings
SELECT Id, Name, FinServ__FinancialAccount__c,
       FinServ__Shares__c, FinServ__Price__c, FinServ__MarketValue__c,
       FinServ__SecurityType__c
FROM FinServ__FinancialHolding__c
WHERE FinServ__FinancialAccount__c IN :accountIds
ORDER BY FinServ__MarketValue__c DESC NULLS LAST
```

```apex
// Equivalent Apex map for portfolio aggregation
Map<Id, List<FinServ__FinancialHolding__c>> holdingsByAccount =
    new Map<Id, List<FinServ__FinancialHolding__c>>();

for (FinServ__FinancialHolding__c h : [
    SELECT Id, FinServ__FinancialAccount__c, FinServ__MarketValue__c,
           FinServ__SecurityType__c, Name
    FROM FinServ__FinancialHolding__c
    WHERE FinServ__FinancialAccount__c IN :accountIds
]) {
    if (!holdingsByAccount.containsKey(h.FinServ__FinancialAccount__c)) {
        holdingsByAccount.put(h.FinServ__FinancialAccount__c,
            new List<FinServ__FinancialHolding__c>());
    }
    holdingsByAccount.get(h.FinServ__FinancialAccount__c).add(h);
}
```

**Why it works:** The `OR FinServ__JointOwner__c` clause captures joint accounts. Holdings are queried separately per account — the FSC data model does not expose a direct Contact-to-Holding relationship, so the traversal is Contact → FinancialAccount → FinancialHolding.

---

## Example 2: Querying Household Financial Data via ACR and Understanding the Rollup Model

**Context:** A financial advisor dashboard needs to display total household net worth, list all household members, and show each member's individual financial accounts. The org is managed-package FSC with Person Accounts enabled.

**Problem:** The developer writes a SOQL aggregate query to SUM balances across all financial accounts related to the household at query time. This works in a developer sandbox with 5 accounts but times out or produces inconsistent results in production with households having 50+ accounts across family members. Additionally, the household Account's `FinServ__TotalAssets__c` field appears stale — balances were updated via a data load but the household total did not change.

**Solution:**

```soql
// Step 1: Read pre-computed rollup fields from the household Account
// These are maintained by the FSC async rollup engine, not by SOQL aggregation
SELECT Id, Name,
       FinServ__TotalAssets__c,
       FinServ__TotalLiabilities__c,
       FinServ__NetWorth__c,
       FinServ__TotalAnnualIncome__c
FROM Account
WHERE Id = :householdAccountId
AND RecordType.DeveloperName = 'HouseHold'

// Step 2: Retrieve all active household members via AccountContactRelation
SELECT ContactId, Contact.Name, Contact.Email, Roles, IsActive
FROM AccountContactRelation
WHERE AccountId = :householdAccountId
AND IsActive = TRUE

// Step 3: For a given household member, retrieve their financial accounts
SELECT Id, Name, FinServ__FinancialAccountType__c, FinServ__Balance__c
FROM FinServ__FinancialAccount__c
WHERE FinServ__PrimaryOwner__c IN :memberContactIds
   OR FinServ__JointOwner__c IN :memberContactIds
```

```apex
// After a bulk data load, trigger the FSC rollup recalculation
// (done via FSC Admin Settings or via the FSC batch Apex API, not SOQL)
// The rollup batch class in managed-package FSC:
Database.executeBatch(new FinServ.RollupBatch(), 200);
// Note: The exact batch class name and invocation method varies by FSC package version.
// Always confirm via Setup > Apex Classes > search "RollupBatch" in your org.
```

**Why it works:** The household `FinServ__TotalAssets__c` field is written by the FSC async rollup engine after the rollup batch runs. After a data load that bypassed triggers (e.g., Data Loader with "Bulk API" mode), the rollup batch must be explicitly triggered from FSC Admin Settings or via the FSC-provided batch Apex class. Reading the pre-computed field is performant and consistent; real-time SOQL aggregation is neither.

---

## Anti-Pattern: Creating a Native Roll-Up Summary Field to Aggregate FSC Balances

**What practitioners do:** In Setup, they create a Roll-Up Summary field on the Account object with a SUM of `FinServ__FinancialAccount__c.FinServ__Balance__c`, expecting it to aggregate all client balances to the household Account.

**What goes wrong:** `FinServ__FinancialAccount__c` is not in a master-detail relationship with Account for the purpose of native ROLLUP summary fields. The FSC model uses lookup relationships and the FSC rollup engine — not master-detail. The field either cannot be created (Salesforce blocks ROLLUP on lookup) or returns zero/null. The practitioner then mistakenly concludes the financial account data is missing.

**Correct approach:** Use the pre-computed rollup fields (`FinServ__TotalAssets__c`, `FinServ__NetWorth__c`, etc.) on the household Account, which are populated by the FSC async rollup engine. Configure rollup settings in FSC Admin Settings and ensure the rollup batch is scheduled. Never replicate FSC rollup logic using native Salesforce ROLLUP summary fields.
