# Examples — FSC Relationship Groups

## Example 1: Creating a Household Group with Two Spouses and Verifying Wealth Rollup

**Context:** A wealth management org is onboarding a married couple. Both spouses are existing Person Accounts. The advisor wants a Household Relationship Group so the FSC advisor dashboard aggregates both spouses' financial accounts into a single household net worth view.

**Problem:** Without explicit field-setting on the ACR records, the household appears to contain both members but the rollup fields (`FinServ__TotalAssets__c`) remain at zero. The most common cause is `FinServ__IncludeInGroup__c` defaulting to `false` when ACR records are inserted programmatically.

**Solution:**

```apex
// Retrieve PersonContactId for each spouse — ACR requires Contact Id, not Account Id
Account spouse1 = [SELECT Id, PersonContactId FROM Account WHERE Name = 'Alice Chen' AND IsPersonAccount = true LIMIT 1];
Account spouse2 = [SELECT Id, PersonContactId FROM Account WHERE Name = 'Bob Chen' AND IsPersonAccount = true LIMIT 1];

// Retrieve the Household Account (already created with Household record type)
Account household = [SELECT Id FROM Account WHERE Name = 'Chen Household' AND RecordType.Name = 'Household' LIMIT 1];

// Create ACR for Alice — primary member, primary group
AccountContactRelation acrAlice = new AccountContactRelation(
    AccountId = household.Id,
    ContactId = spouse1.PersonContactId,
    FinServ__PrimaryGroup__c = true,   // This household is Alice's primary group
    FinServ__Primary__c = true,         // Alice is the primary member of this household
    FinServ__IncludeInGroup__c = true   // Include Alice's financial accounts in rollups
);

// Create ACR for Bob — also primary group, not primary member
AccountContactRelation acrBob = new AccountContactRelation(
    AccountId = household.Id,
    ContactId = spouse2.PersonContactId,
    FinServ__PrimaryGroup__c = true,   // This household is Bob's primary group
    FinServ__Primary__c = false,        // Bob is not the primary member (Alice is)
    FinServ__IncludeInGroup__c = true   // Include Bob's financial accounts in rollups
);

insert new List<AccountContactRelation>{ acrAlice, acrBob };
```

**Why it works:** Setting `FinServ__PrimaryGroup__c = true` on both ACRs tells the FSC rollup engine that the Chen Household is the authoritative financial unit for both spouses. Setting `FinServ__IncludeInGroup__c = true` on both ACRs ensures their financial accounts are pulled into the household's aggregated wealth view. `FinServ__Primary__c = true` on Alice's ACR designates her as the primary household contact for display and advisor assignment purposes.

---

## Example 2: Adding a Client to a Trust Group Without Breaking Their Household Rollup

**Context:** Alice Chen (from Example 1) is also a trustee of the "Chen Family Trust" managed by the firm. The Trust needs to be an FSC Relationship Group so trust documents and trust-level financial accounts are visible in the advisor's group panel. However, Alice's wealth rollup must remain anchored to the Chen Household, not the Trust.

**Problem:** If a practitioner sets `FinServ__PrimaryGroup__c = true` on Alice's Trust ACR, Alice's household ACR is no longer the sole primary group. The FSC rollup engine behavior becomes indeterminate — some assets may aggregate to the Trust, others to the Household, and the household net worth display breaks. This is a common mistake when advisors add clients to trust groups without understanding the primary group constraint.

**Solution:**

```apex
// Retrieve the Trust Account (created with Trust record type)
Account trust = [SELECT Id FROM Account WHERE Name = 'Chen Family Trust' AND RecordType.Name = 'Trust' LIMIT 1];

// Create ACR for Alice as trustee — NOT primary group, IS primary member of the Trust
AccountContactRelation acrAliceTrust = new AccountContactRelation(
    AccountId = trust.Id,
    ContactId = spouse1.PersonContactId,  // Alice's PersonContactId
    FinServ__PrimaryGroup__c = false,  // Chen Household remains Alice's primary group
    FinServ__Primary__c = true,         // Alice is the primary contact (trustee) for this Trust
    FinServ__IncludeInGroup__c = true   // Trust can display Alice's accounts in relationship view
                                         // NOTE: assets will NOT roll up to Trust totals — PrimaryGroup is false
);

insert acrAliceTrust;
```

**Why it works:** Setting `FinServ__PrimaryGroup__c = false` preserves the Chen Household as Alice's primary group, keeping household wealth aggregation intact. Alice still appears in the Trust group's relationship view, and the Trust's own financial accounts (those owned directly by the Trust Account) aggregate independently. The `FinServ__IncludeInGroup__c = true` flag allows Alice's accounts to be *visible* in the Trust panel without triggering rollup aggregation.

---

## Example 3: Professional Group for Business Partners

**Context:** Two existing FSC clients, David Park and Sarah Kim, co-own a registered investment partnership. The firm wants a Professional Group to track the partnership's business financial accounts separately from each partner's personal household.

**Problem:** Creating a Household group for the business conflates personal and business wealth. The FSC Household record type surfaces household-specific components (household goals, household financial planning) that are inappropriate for a business entity.

**Solution:**

```apex
// Professional Group Account (created with Professional Group record type)
Account bizGroup = [SELECT Id FROM Account WHERE Name = 'Park-Kim Investment Partners' AND RecordType.Name = 'Professional Group' LIMIT 1];

Account david = [SELECT Id, PersonContactId FROM Account WHERE Name = 'David Park' AND IsPersonAccount = true LIMIT 1];
Account sarah = [SELECT Id, PersonContactId FROM Account WHERE Name = 'Sarah Kim' AND IsPersonAccount = true LIMIT 1];

// Both partners are already in personal Household groups; this is a secondary group
AccountContactRelation acrDavid = new AccountContactRelation(
    AccountId = bizGroup.Id,
    ContactId = david.PersonContactId,
    FinServ__PrimaryGroup__c = false,  // Each partner's Household remains their primary group
    FinServ__Primary__c = true,         // David is the managing partner (primary contact)
    FinServ__IncludeInGroup__c = false  // Personal accounts do not roll up to the business group
);

AccountContactRelation acrSarah = new AccountContactRelation(
    AccountId = bizGroup.Id,
    ContactId = sarah.PersonContactId,
    FinServ__PrimaryGroup__c = false,
    FinServ__Primary__c = false,
    FinServ__IncludeInGroup__c = false
);

insert new List<AccountContactRelation>{ acrDavid, acrSarah };
// Business financial accounts are linked directly to bizGroup Account via PrimaryOwner or FinancialAccount.AccountId
```

**Why it works:** Using the Professional Group record type activates the correct FSC page layout and components for a business entity. Setting `FinServ__PrimaryGroup__c = false` for both partners preserves their personal household wealth aggregation. Business financial accounts are linked directly to the Professional Group Account, not via member rollups, so business assets aggregate at the group level independently.

---

## Anti-Pattern: Setting FinServ__PrimaryGroup__c = true on Multiple Groups for the Same Member

**What practitioners do:** When adding a client to a second FSC group (e.g., a Trust or a joint household with a new spouse), a practitioner sets `FinServ__PrimaryGroup__c = true` on both the new ACR and the existing ACR without updating the original.

**What goes wrong:** The platform accepts both ACR records without throwing a validation error. The FSC rollup engine encounters ambiguous primary group designations for that member. Depending on the FSC version and trigger execution order, assets may double-count across both groups, aggregate only to one group arbitrarily, or produce inconsistent rollup totals that change after the next batch job run. This is extremely difficult to diagnose because no error appears in debug logs — the rollup engine simply processes both records.

**Correct approach:** Before setting `FinServ__PrimaryGroup__c = true` on a new group's ACR, explicitly set `FinServ__PrimaryGroup__c = false` on all existing ACR records for that Person Account. Make the primary group change a deliberate two-step update: clear the old designation first, then set the new one. A custom validation rule enforcing uniqueness of `FinServ__PrimaryGroup__c = true` per Contact (or PersonContactId) across ACR records is strongly recommended for production orgs.
