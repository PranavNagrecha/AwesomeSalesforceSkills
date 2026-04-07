# Examples — Financial Account Setup

## Example 1: Setting Up a Brokerage Account with Holdings and Financial Account Roles

**Context:** A wealth management firm is configuring FSC for their advisory practice. A client (Person Account: Margaret Chen) holds a joint brokerage account with her spouse (Person Account: David Chen). Both are in the same household. The account holds three equity positions. The firm uses the managed-package FSC deployment (FinServ__ namespace).

**Problem:** Without explicit `FinancialAccountRole` records, the account will not appear in either client's household balance rollup. The `FinServ__PrimaryOwner__c` lookup field on `FinancialAccount` is not sufficient on its own — the FSC rollup engine reads from `FinancialAccountRole`, not from the lookup field directly.

**Solution:**

Step 1 — Create the FinancialAccount record:

```
Object: FinServ__FinancialAccount__c
Fields:
  Name: "Chen Joint Brokerage"
  FinServ__FinancialAccountType__c: "Joint Brokerage"
  RecordType: Brokerage Account (record type linked to brokerage page layout)
  FinServ__Balance__c: 142500.00
  FinServ__PrimaryOwner__c: [Margaret Chen Person Account Id]
  FinServ__FinancialAccountNumber__c: "BRK-2024-00147"
```

Step 2 — Create the Primary Owner FinancialAccountRole record:

```
Object: FinServ__FinancialAccountRole__c
Fields:
  FinServ__FinancialAccount__c: [Chen Joint Brokerage Id]
  FinServ__RelatedAccount__c: [Margaret Chen Person Account Id]
  FinServ__Role__c: Primary Owner
  FinServ__Active__c: true
```

Step 3 — Create the Joint Owner FinancialAccountRole record:

```
Object: FinServ__FinancialAccountRole__c
Fields:
  FinServ__FinancialAccount__c: [Chen Joint Brokerage Id]
  FinServ__RelatedAccount__c: [David Chen Person Account Id]
  FinServ__Role__c: Joint Owner
  FinServ__Active__c: true
```

Step 4 — Load FinancialHolding records:

```
Object: FinServ__FinancialHolding__c
Record 1:
  FinServ__FinancialAccount__c: [Chen Joint Brokerage Id]
  FinServ__Symbol__c: "AAPL"
  FinServ__Quantity__c: 50
  FinServ__Price__c: 185.40
  FinServ__MarketValue__c: 9270.00
  FinServ__HoldingType__c: Stock

Record 2:
  FinServ__FinancialAccount__c: [Chen Joint Brokerage Id]
  FinServ__Symbol__c: "VTSAX"
  FinServ__Quantity__c: 200
  FinServ__Price__c: 118.00
  FinServ__MarketValue__c: 23600.00
  FinServ__HoldingType__c: Mutual Fund
```

Step 5 — After record creation, trigger or allow the FSC rollup batch to run. Navigate to the Chen household record and verify `FinServ__TotalBalance__c` has increased to reflect the brokerage account balance.

**Why it works:** The `FinancialAccountRole` record with `Role = Primary Owner` is what the FSC rollup engine follows to identify the household. Margaret Chen's `FinServ__PrimaryGroup__c` (household) is the target for rollup. David Chen is in the same household, so he also sees the aggregated balance through the household record. The holdings give the brokerage account its position-level detail for the Account Summary Lightning component.

---

## Example 2: Household Balance Rollup Configuration for Joint Account Owners in Different Households

**Context:** A client, Robert Nakamura, holds a joint brokerage account with his business partner, Priya Patel. They are not related and belong to different FSC households. The account balance must appear in both households' rollup figures for their respective advisor views.

**Problem:** FSC's managed-package rollup engine only rolls the account balance up to the Primary Owner's household. If Priya Patel is set as Joint Owner and belongs to a different household, her household record will show a rollup balance that does not include the joint account. Her advisor will undercount Priya's total assets under management.

**Solution — Custom Rollup via Flow:**

Step 1 — Create both FinancialAccountRole records as usual (Robert = Primary Owner, Priya = Joint Owner).

Step 2 — After the native FSC rollup runs, implement a Record-Triggered Flow or a scheduled Apex job that:
  - Queries all `FinancialAccountRole` records where `Role = Joint Owner` and the Joint Owner's `PrimaryGroup__c` differs from the Primary Owner's `PrimaryGroup__c`
  - Reads the `FinancialAccount.Balance` value
  - Writes the balance (or increments a custom `Custom_Joint_TotalBalance__c` field) to the Joint Owner's household record

Step 3 — Add a custom field to the Household object: `Custom_JointAccountBalance__c` (Currency, to distinguish from the native FSC rollup field which is owned by the managed package and should not be overwritten).

Step 4 — Surface this custom field on the Household page layout alongside the native FSC rollup fields, clearly labeled "Joint Account Balance (External Households)".

Example Flow logic (pseudocode):

```
Trigger: After Insert/Update on FinancialAccountRole
  Filter: Role = "Joint Owner" AND RelatedAccount.PrimaryGroup != FinancialAccount.PrimaryOwner.PrimaryGroup
  Get: FinancialAccount.Balance
  Get: RelatedAccount.PrimaryGroup (the Joint Owner's household)
  Update: Household.Custom_JointAccountBalance__c += FinancialAccount.Balance
```

**Why it works:** The standard FSC rollup is intentionally scoped to the Primary Owner's household to avoid double-counting in the same household. A separate custom field on the Joint Owner's household captures cross-household exposure without interfering with the managed package's native rollup fields. This design survives FSC package upgrades because it does not modify managed package fields or objects.

---

## Anti-Pattern: Using FinServ__PrimaryOwner__c Lookup as a Substitute for FinancialAccountRole

**What practitioners do:** Some developers skip creating `FinancialAccountRole` records and instead rely solely on the `FinServ__PrimaryOwner__c` lookup field on `FinancialAccount` to associate the account with a person.

**What goes wrong:** The `FinServ__PrimaryOwner__c` field is a display convenience — it populates the "Primary Owner" on the account record page. However, the FSC rollup engine reads from `FinancialAccountRole` records, not from this field. An account with only the lookup field populated will not appear in household balance rollups. Additionally, joint owners, beneficiaries, and other relationship types cannot be expressed with a single lookup field — they require `FinancialAccountRole` records.

**Correct approach:** Always create at least one `FinancialAccountRole` record with `Role = Primary Owner` for every `FinancialAccount`. The `FinServ__PrimaryOwner__c` lookup may be populated for convenience, but the role record is mandatory for rollup and relationship model correctness.
