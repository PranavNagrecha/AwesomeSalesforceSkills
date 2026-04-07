# Examples — Household Model Configuration

## Example 1: Household Rollup Totals Not Updating After Adding a Financial Account

**Context:** An FSC org (managed-package, `FinServ__` namespace) has an existing Household Account with two Person Account members. A new brokerage financial account was added to one member, but the Household Account's `FinServ__TotalAssets__c` field remains unchanged. The admin confirms the ACR records exist.

**Problem:** The ACR records for both members were created via Data Loader during a migration. The `FinServ__IncludeInGroup__c` field was not included in the import CSV, so it defaulted to `false` for both members. The FSC rollup trigger evaluates `FinServ__IncludeInGroup__c` before aggregating — members with `false` are excluded from all rollup calculations.

**Solution:**

```apex
// Query ACR records for the household where IncludeInGroup is false
List<AccountContactRelation> acrList = [
    SELECT Id, FinServ__IncludeInGroup__c, FinServ__PrimaryGroup__c, FinServ__Primary__c
    FROM AccountContactRelation
    WHERE AccountId = :householdAccountId
    AND FinServ__IncludeInGroup__c = false
];

// Set IncludeInGroup to true for all active members
for (AccountContactRelation acr : acrList) {
    acr.FinServ__IncludeInGroup__c = true;
}
update acrList;

// After update, trigger will recalculate household rollups
// For bulk corrections, run the batch job:
// FinServ.RollupBatchJob rollupJob = new FinServ.RollupBatchJob();
// Database.executeBatch(rollupJob);
```

**Why it works:** The FSC rollup trigger re-fires when ACR records are updated. Setting `FinServ__IncludeInGroup__c = true` causes the trigger to include that member's financial accounts in the next rollup calculation. For large orgs, the batch job is more reliable than relying on the update trigger for bulk corrections.

---

## Example 2: Setting Up a New Household with a Joint Account Holder

**Context:** A wealth management FSC org needs to onboard a married couple. Each spouse has individual financial accounts, plus a joint investment account. The primary household is "Smith Family Household." Both spouses should appear as household members; the joint financial account should roll up to the household.

**Problem:** If both spouses are added to the household ACR with `FinServ__PrimaryGroup__c = true`, FSC may behave inconsistently — the platform expects exactly one primary group per individual. Additionally, if the joint financial account's `AccountContactRelation` is not set up for both spouses, only one spouse's view will show the joint account.

**Solution:**

```apex
// Step 1: Create the Household Account
Account household = new Account(
    Name = 'Smith Family Household',
    RecordTypeId = householdRecordTypeId // Household record type Id
);
insert household;

// Step 2: Create ACR for Spouse 1 (primary member)
// Use PersonContactId — NOT the Account.Id of the Person Account
AccountContactRelation acr1 = new AccountContactRelation(
    AccountId = household.Id,
    ContactId = spouse1PersonAccount.PersonContactId,
    FinServ__PrimaryGroup__c = true,   // This is Spouse 1's primary household
    FinServ__Primary__c = true,        // Spouse 1 is the primary member of this household
    FinServ__IncludeInGroup__c = true
);

// Step 3: Create ACR for Spouse 2 (secondary member)
AccountContactRelation acr2 = new AccountContactRelation(
    AccountId = household.Id,
    ContactId = spouse2PersonAccount.PersonContactId,
    FinServ__PrimaryGroup__c = true,   // This is also Spouse 2's primary household
    FinServ__Primary__c = false,       // Only one primary member per household
    FinServ__IncludeInGroup__c = true
);

insert new List<AccountContactRelation>{ acr1, acr2 };
```

**Why it works:** Both spouses have `FinServ__PrimaryGroup__c = true` on their respective ACR records for this household because the Smith Family Household is each individual's primary group. This is correct — the field marks which household is primary *for that person*, not whether the household itself is "primary." Only `FinServ__Primary__c` must be unique per household (one primary member per household). Using `PersonContactId` (not `Account.Id`) ensures the ACR correctly references the underlying Contact for the Person Account.

---

## Example 3: Existing Org Missing Insurance Policy Rollups

**Context:** An FSC org was provisioned in 2021 and recently had Insurance Cloud enabled. Insurance Policy records are being created, but the Household Account shows no insurance policy aggregations. The admin can see the Insurance Policy records in Salesforce and confirms they are related to household members.

**Problem:** The `Rollups__c` picklist on the Account object does not include an `InsurancePolicy` value. This picklist was seeded during FSC provisioning with the values available at that time. Insurance Policy rollup support was added in a later FSC release, so existing orgs do not receive the new picklist value automatically.

**Solution:**

```
Setup > Object Manager > Account > Fields & Relationships
  > Rollups__c (Picklist field)
  > Manage Values
  > New
    Value: InsurancePolicy
    (Add to all active picklists / default picklist as appropriate)
Save
```

After saving, run the batch rollup job to recalculate all household rollup totals:

```apex
// In Developer Console > Execute Anonymous
FinServ.RollupBatchJob rollupJob = new FinServ.RollupBatchJob();
Database.executeBatch(rollupJob);
```

**Why it works:** The FSC rollup engine checks the `Rollups__c` picklist to determine which object types to aggregate. Adding the missing picklist value registers InsurancePolicy records as eligible for rollup aggregation. Running the batch job then triggers a full recalculation across all households.

---

## Anti-Pattern: Treating FSC Households Like NPSP Households

**What practitioners do:** Advisors or admins familiar with NPSP attempt to configure FSC households by modifying `Contact.AccountId` directly or by relying on NPSP's Household Naming batch to manage FSC household display names. Some mistakenly install NPSP triggers in an FSC org to get "household rollup" behavior.

**What goes wrong:** NPSP's rollup engine (`NPSP_Rollup`) fires on Contact-Account lookup field changes, not on ACR records. FSC rollups fire on ACR changes. The two systems do not share a trigger context. Running both creates duplicate rollup calculations, trigger conflicts, and corrupted `TotalAssets` values. Because both systems can update the same rollup fields, the final value depends on trigger execution order — which is non-deterministic in mixed environments.

**Correct approach:** Choose one household model for the org. FSC orgs use the ACR-based model with `Rollups__c` picklist and the `FinServ.RollupBatchJob`. NPSP orgs use the direct Contact-Account model with NPSP Rollups. These are mutually exclusive. If the org needs to transition from one to the other, engage Salesforce Professional Services or the ISV for a supported migration path.
