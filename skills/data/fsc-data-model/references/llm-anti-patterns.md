# LLM Anti-Patterns — FSC Data Model

Common mistakes AI coding assistants make when generating or advising on the FSC data model.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using FinServ__-Namespaced Objects in a Core FSC Org

**What the LLM generates:**
```soql
SELECT Id, Name, FinServ__Balance__c
FROM FinServ__FinancialAccount__c
WHERE FinServ__PrimaryOwner__c = :contactId
```

**Why it happens:** The majority of FSC documentation, Stack Exchange answers, Trailhead content, and blog posts predate Core FSC (Winter '23) and use managed-package examples. LLMs trained on this corpus default to `FinServ__` prefix without checking whether the org is Core FSC.

**Correct pattern:**
```soql
-- Core FSC org (no namespace):
SELECT Id, Name, Balance
FROM FinancialAccount
WHERE Id IN (
    SELECT FinancialAccountId
    FROM FinancialAccountParty
    WHERE RelatedPersonId = :contactId
)

-- Managed-package FSC org (FinServ__ namespace):
SELECT Id, Name, FinServ__Balance__c
FROM FinServ__FinancialAccount__c
WHERE FinServ__PrimaryOwner__c = :contactId
```

**Detection hint:** Any SOQL or Apex referencing `FinServ__FinancialAccount__c` without first confirming the org has the managed package installed is suspect. Check for `FinServ__` prefix usage without a prior "confirmed managed-package" assertion.

---

## Anti-Pattern 2: Assuming Native Roll-Up Summary Fields Aggregate FSC Financial Data

**What the LLM generates:**
```
Create a Roll-Up Summary field on Account:
- Related Object: Financial Account (FinServ__FinancialAccount__c)
- Aggregate: SUM of FinServ__Balance__c
- Filter: FinServ__Status__c = 'Active'
This will automatically update the household total assets.
```

**Why it happens:** LLMs are trained on standard Salesforce patterns where master-detail relationships and ROLLUP summary fields are the canonical aggregation pattern. The FSC async rollup engine is a product-specific behavior that deviates from this norm, and LLMs over-generalize the native ROLLUP approach.

**Correct pattern:**
```
FSC maintains pre-computed rollup fields on the household Account using its own async rollup engine.
Read FinServ__TotalAssets__c, FinServ__TotalLiabilities__c, FinServ__NetWorth__c directly.
Configure rollup settings in FSC Admin Settings > Rollup Configuration.
Schedule the FSC rollup batch to keep totals current.
Do NOT create native ROLLUP summary fields — FinServ__FinancialAccount__c is not in a
master-detail relationship with Account for ROLLUP purposes.
```

**Detection hint:** Any recommendation to create a Roll-Up Summary field targeting `FinServ__FinancialAccount__c` or `FinancialAccount` is wrong. Look for "Roll-Up Summary" + "Financial Account" in the same instruction.

---

## Anti-Pattern 3: Conflating FSC Household with NPSP Household

**What the LLM generates:**
```apex
// Get household members using NPSP household object
List<npe01__OOHousehold__c> households = [
    SELECT Id, Name FROM npe01__OOHousehold__c WHERE Id = :householdId
];
// Or: uses npo02__ rollup fields on the household account
```

**Why it happens:** Both FSC and NPSP use the term "household" prominently, and both involve Salesforce Account and Contact objects. LLMs conflate the two because the terminology overlaps and both are Salesforce financial/relationship products.

**Correct pattern:**
```soql
-- FSC household = Business Account with HouseHold RecordType
SELECT Id, Name, FinServ__TotalAssets__c, FinServ__NetWorth__c
FROM Account
WHERE Id = :householdAccountId
AND RecordType.DeveloperName = 'HouseHold'

-- FSC household membership = AccountContactRelation (standard junction object)
SELECT ContactId, Contact.Name, Roles
FROM AccountContactRelation
WHERE AccountId = :householdAccountId
AND IsActive = TRUE
-- No npe01__ or npo02__ objects involved.
```

**Detection hint:** Any FSC household query or code referencing `npe01__`, `npo02__`, or `npe04__` namespace prefixes is applying NPSP concepts to an FSC implementation. The two models do not overlap.

---

## Anti-Pattern 4: Missing the OR JointOwner Clause When Querying Managed-Package Financial Accounts

**What the LLM generates:**
```soql
SELECT Id, Name, FinServ__Balance__c
FROM FinServ__FinancialAccount__c
WHERE FinServ__PrimaryOwner__c = :contactId
```

**Why it happens:** The `PrimaryOwner__c` field is the most prominent ownership field in FSC documentation and examples. LLMs do not spontaneously include the `JointOwner__c` clause because it requires knowing the managed-package two-lookup ownership model rather than the Core FSC junction pattern.

**Correct pattern:**
```soql
-- Managed-package: include both ownership lookups
SELECT Id, Name, FinServ__Balance__c, FinServ__FinancialAccountType__c
FROM FinServ__FinancialAccount__c
WHERE FinServ__PrimaryOwner__c = :contactId
   OR FinServ__JointOwner__c = :contactId

-- Core FSC: query through FinancialAccountParty junction (handles unlimited owners)
SELECT FinancialAccountId, FinancialAccount.Name, Role
FROM FinancialAccountParty
WHERE RelatedPersonId = :contactId
```

**Detection hint:** A SOQL query on `FinServ__FinancialAccount__c` that filters only on `FinServ__PrimaryOwner__c` without a corresponding `OR FinServ__JointOwner__c` clause will silently exclude joint accounts.

---

## Anti-Pattern 5: Treating FinancialAccountRole as Unlimited-Owner Capable in Managed-Package

**What the LLM generates:**
```apex
// Adding multiple owners to a managed-package financial account
List<FinServ__FinancialAccountRole__c> roles = new List<FinServ__FinancialAccountRole__c>();
for (Contact c : owners) {
    roles.add(new FinServ__FinancialAccountRole__c(
        FinServ__FinancialAccount__c = account.Id,
        FinServ__RelatedContact__c = c.Id,
        FinServ__Role__c = 'Owner'
    ));
}
insert roles;
// Assumes this supports 3, 4, or more owners per account
```

**Why it happens:** LLMs see `FinServ__FinancialAccountRole__c` in the managed-package schema and extrapolate that it functions like Core FSC's `FinancialAccountParty` junction (which does support unlimited owners). The managed-package ownership model is actually enforced through direct lookup fields on the financial account record, not through this junction.

**Correct pattern:**
```
Managed-package FSC enforces ownership through two lookup fields on FinServ__FinancialAccount__c:
  - FinServ__PrimaryOwner__c (required, one Contact)
  - FinServ__JointOwner__c (optional, one Contact)

FinServ__FinancialAccountRole__c exists for other relationship types (e.g., beneficiary,
power of attorney) but does not replace the primary/joint ownership limitation.

For unlimited multi-owner accounts, Core FSC with FinancialAccountParty is required.
If on managed-package with a third-owner requirement, build a custom junction object
and document that it falls outside the FSC rollup engine's scope.
```

**Detection hint:** Code that inserts multiple `FinServ__FinancialAccountRole__c` records with `Role__c = 'Owner'` or equivalent on a managed-package org, expecting all of them to count as financial account owners in rollups and advisor views, is incorrect.
