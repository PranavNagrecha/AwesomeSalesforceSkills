# Examples — Historical Order Migration

## Example 1: Full Legacy CPQ Load for SaaS Company Migrating from Legacy Billing System

**Context:** A SaaS company is migrating to Salesforce CPQ from a legacy subscription billing platform. They have 3,200 active contracts with 8,900 subscription lines representing the current book of business. Each contract renews annually. They need the renewal quotes to generate automatically in CPQ at the correct renewal date with the correct products and pricing.

**Problem:** The team attempts to load Subscription records via standard Bulk API 2.0 with a batch size of 200 (the default). All 8,900 records insert without errors. Three months later, when the first batch of contracts reaches renewal date, CPQ generates renewal quotes with blank product lines. Investigating the subscriptions reveals that CPQ's renewal-preparation trigger logic (which sets internal renewal fields on the SBQQ__Subscription__c record) did not fire because the bulk load bypassed the per-record trigger execution path.

**Solution:**

```text
Load configuration:
- Tool: Salesforce Data Loader 57+
- Batch size: 1 (mandatory for all CPQ Legacy Data Upload objects)
- Object order:
  1. SBQQ__Quote__c  (Status=Approved, Primary=true)
  2. SBQQ__QuoteLine__c
  3. Contract         (SBQQ__Quote__c field populated)
  4. SBQQ__Subscription__c
  5. SBQQ__Asset__c

Pre-load steps:
- CPQ Package Settings > Pricing and Calculation > Disable Background Pricing = true
- CPQ Package Settings > Quote > Disable Quote Line Related Rules = true

Sample CSV header for SBQQ__Subscription__c:
External_Id__c, SBQQ__Contract__c (external ID ref), SBQQ__Product__c (external ID ref),
SBQQ__StartDate__c, SBQQ__EndDate__c, SBQQ__Quantity__c, SBQQ__RegularPrice__c,
SBQQ__NetPrice__c, SBQQ__CustomerPrice__c, SBQQ__SubscriptionType__c

Post-load validation SOQL:
SELECT SBQQ__Contract__c, COUNT(Id) subCount
FROM SBQQ__Subscription__c
WHERE SBQQ__Contract__c IN (SELECT Id FROM Contract WHERE SBQQ__RenewalForecast__c = true)
GROUP BY SBQQ__Contract__c
```

**Why it works:** A batch size of 1 ensures that CPQ's package trigger fires independently for each Subscription record, executing the renewal-preparation logic that sets the internal fields CPQ reads when generating renewal quote lines. The constraint is documented in the CPQ Legacy Data Upload help article and is enforced by package design, not by a configurable setting.

---

## Example 2: Asset Root Id Corruption During Amendment-Enabled Migration

**Context:** A team is migrating historical CPQ contracts that include both original assets and assets that were revised (amended) mid-term. In the source system, each revised asset has a pointer to both the original root asset and the immediately preceding asset version.

**Problem:** The migration team populates both `SBQQ__RootId__c` and `SBQQ__RevisedAsset__c` on SBQQ__Asset__c records to preserve the full amendment chain. The records insert without errors. When the first amendment quote is created after migration, CPQ follows both the root chain and the revised-asset chain simultaneously, producing duplicate amendment quote lines — one from the root traversal and one from the revised-asset traversal.

**Solution:**

```text
Rule: For any SBQQ__Asset__c that has SBQQ__RevisedAsset__c populated,
      SBQQ__RootId__c must be null (not populated).

Correct asset record structure:

Original (root) asset:
  SBQQ__RootId__c: null (CPQ sets this to its own Id post-insert)
  SBQQ__RevisedAsset__c: null

Revised (amended) asset:
  SBQQ__RootId__c: null  ← MUST be null if RevisedAsset is set
  SBQQ__RevisedAsset__c: <Id of the asset this revision replaces>

Pre-load validation query to detect violations:
SELECT Id, SBQQ__RootId__c, SBQQ__RevisedAsset__c
FROM SBQQ__Asset__c
WHERE SBQQ__RootId__c != null
  AND SBQQ__RevisedAsset__c != null
```

**Why it works:** CPQ's amendment logic uses `SBQQ__RevisedAsset__c` to traverse the amendment chain (newest revision first) and `SBQQ__RootId__c` to find the originating asset. When both are populated, CPQ treats the record as simultaneously a member of two overlapping chains, causing duplicate quote line generation. Populating only `SBQQ__RevisedAsset__c` and leaving `SBQQ__RootId__c` null is the correct pattern documented in the CPQ Legacy Data Upload guidance.

---

## Anti-Pattern: Inserting SBQQ__Quote__c with Status = Draft for Historical Load

**What practitioners do:** Practitioners treating the historical CPQ Quote as just a data record (rather than a functional CPQ object) insert it with `SBQQ__Status__c` = `Draft` and `SBQQ__Primary__c` = `false` because those are the default values and the record "isn't really being used."

**What goes wrong:** CPQ's contract-to-quote linkage and renewal engine only recognize Quotes with `Status = Approved` and `Primary = true` as the authoritative quote for a contract. When renewal opportunity generation fires on an expiring contract, CPQ looks for the linked approved primary quote to determine what products to include in the renewal. A Draft quote is invisible to this lookup. The renewal quote generates with blank or incorrect lines, and the root cause is difficult to diagnose because the Contract and Subscription records look correct.

**Correct approach:** Always insert historical SBQQ__Quote__c records with `SBQQ__Status__c` = `Approved` and `SBQQ__Primary__c` = `true`. These are not status flags for human workflow — they are technical markers that CPQ's renewal engine uses to discover the correct configuration for a contract.
