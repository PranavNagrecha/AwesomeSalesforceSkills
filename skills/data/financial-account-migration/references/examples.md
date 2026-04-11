# Examples — Financial Account Migration

## Example 1: Bulk Migrating FinancialHolding Records — Disabling RBL and Running Post-Load Recalculation

**Context:** A wealth management firm is migrating 500,000 FinancialHolding records from a legacy portfolio system into a managed-package FSC org. Initial test loads consistently fail after 300–400 rows with `UNABLE_TO_LOCK_ROW` errors on FinancialAccount records.

**Problem:** The FSC Rollup-by-Lookup Apex triggers (`FinancialHoldingTrigger`, `FinServAssetsLiabilitiesTrigger`) fire synchronously on every inserted FinancialHolding row. Because multiple holdings share the same parent FinancialAccount, concurrent Data Loader threads compete for a row lock on the parent, causing the DML to fail. Retrying without fixing the root cause produces the same error.

**Solution:**

Step 1 — Disable RBL for the ETL user before the load:

```apex
// Run as System Administrator in Anonymous Apex before the ETL job starts
FinServ__WealthAppConfig__c config = FinServ__WealthAppConfig__c.getInstance();
if (config == null) {
    config = new FinServ__WealthAppConfig__c();
}
config.FinServ__EnableRollupSummary__c = false;
upsert config;
System.debug('RBL disabled: ' + config.FinServ__EnableRollupSummary__c);
```

Step 2 — Run the FinancialHolding bulk load using Bulk API 2.0 (Data Loader or Salesforce CLI):

```bash
# Using Salesforce CLI with a pre-built CSV
sf data bulk upsert \
  --sobject FinServ__FinancialHolding__c \
  --file financial_holdings.csv \
  --external-id External_ID__c \
  --wait 30
```

Step 3 — After all jobs complete, re-enable RBL and run the recalculation batch:

```apex
// Re-enable RBL
FinServ__WealthAppConfig__c config = FinServ__WealthAppConfig__c.getInstance();
config.FinServ__EnableRollupSummary__c = true;
update config;

// Run full recalculation — batch size of 200 is safe for most orgs
Database.executeBatch(new FinServ.RollupRecalculationBatchable(), 200);
System.debug('RollupRecalculationBatchable enqueued');
```

**Why it works:** Disabling the custom setting causes the RBL trigger guards to short-circuit the aggregation logic for the ETL user's DML, eliminating lock contention entirely. The post-load batch recalculates all rollup values from committed data in a single, controlled pass, producing a consistent final state.

---

## Example 2: Migrating Balance History in Core FSC Using FinancialAccountBalance Records

**Context:** A Core FSC org (API v61.0+, Spring '25) is receiving migrated financial accounts. The source system stores 24 months of month-end balance snapshots per account. The team wants this history to populate FSC's balance trend charts.

**Problem:** A developer familiar with the FSC managed package writes the most recent balance value directly to a FinancialAccount field during the account load. In Core FSC, balance history is stored as child `FinancialAccountBalance` records. No child records are created, so all account trend charts remain empty even though the account record shows a current balance value.

**Solution:**

Step 1 — Load FinancialAccount records (no balance field required at this stage):

```bash
# financial_accounts.csv columns: ExternalId__c, Name, AccountId, FinancialAccountType, CurrencyIsoCode
sf data bulk upsert \
  --sobject FinancialAccount \
  --file financial_accounts.csv \
  --external-id ExternalId__c \
  --wait 30
```

Step 2 — Prepare the FinancialAccountBalance CSV with one row per historical snapshot:

```
ExternalBalanceId__c,FinancialAccountId,Balance,BalanceDate,CurrencyIsoCode
BAL-001-2024-01,0016g00000XXXXX,125000.00,2024-01-31,USD
BAL-001-2024-02,0016g00000XXXXX,127500.00,2024-02-28,USD
BAL-001-2024-03,0016g00000XXXXX,131200.00,2024-03-31,USD
```

Step 3 — Load FinancialAccountBalance records in ascending date order:

```bash
# Sort the CSV by BalanceDate ascending before loading
sort -t',' -k4 financial_account_balances.csv -o financial_account_balances_sorted.csv

sf data bulk upsert \
  --sobject FinancialAccountBalance \
  --file financial_account_balances_sorted.csv \
  --external-id ExternalBalanceId__c \
  --wait 60
```

Step 4 — Verify trend chart population via SOQL:

```soql
SELECT FinancialAccountId, Balance, BalanceDate
FROM FinancialAccountBalance
WHERE FinancialAccountId = '0016g00000XXXXX'
ORDER BY BalanceDate ASC
LIMIT 30
```

**Why it works:** Core FSC uses `FinancialAccountBalance` as the canonical, append-only time-series store for balance data. Each child record represents a point-in-time snapshot. The most recent record's `Balance` value is what appears as the current balance in the advisor UI; earlier records feed the trend visualization. Loading in ascending date order ensures the most recent snapshot is the last one written, which is the value the UI surfaces as current.

---

## Anti-Pattern: Applying the Managed-Package Balance Strategy to a Core FSC Org

**What practitioners do:** They copy a managed-package migration runbook and write the current balance value to a top-level FinancialAccount field, then consider the balance migration complete.

**What goes wrong:** In Core FSC orgs, the `FinancialAccountBalance` child object is the authoritative store. No child records exist, so balance trend charts in the advisor console show empty or flat lines. Analytics based on balance history (e.g., AUM growth reports) return zero or incorrect figures. The error is silent — no load failure occurs, and the account record may show a balance value, making the gap easy to miss during initial QA.

**Correct approach:** Always determine the deployment model first. For Core FSC orgs, load `FinancialAccountBalance` child records — one per historical snapshot — after loading the parent FinancialAccount. For managed-package orgs, the single-field approach is correct.
