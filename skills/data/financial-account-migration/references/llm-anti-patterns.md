# LLM Anti-Patterns — Financial Account Migration

Common mistakes AI coding assistants make when generating or advising on Financial Account Migration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Not Disabling RBL Before Bulk Load

**What the LLM generates:** A Data Loader / Bulk API runbook that loads FinancialHolding and FinancialAccountTransaction records directly, with no mention of Rollup-by-Lookup or the Wealth Application Config custom setting.

**Why it happens:** LLMs are trained on generic Salesforce bulk data loading patterns where standard triggers and validation rules are the only concern. The FSC-specific RBL Apex trigger behavior is not prominent in generic training data. The LLM correctly describes Bulk API mechanics but silently omits the FSC-specific pre-load configuration step.

**Correct pattern:**

```apex
// REQUIRED before any FinancialHolding or FinancialAccountTransaction bulk load
FinServ__WealthAppConfig__c config = FinServ__WealthAppConfig__c.getInstance();
if (config == null) { config = new FinServ__WealthAppConfig__c(); }
config.FinServ__EnableRollupSummary__c = false;
upsert config;
// ... run ETL jobs ...
// Re-enable and recalculate post-load
config.FinServ__EnableRollupSummary__c = true;
update config;
Database.executeBatch(new FinServ.RollupRecalculationBatchable(), 200);
```

**Detection hint:** If a generated migration plan for FinancialHolding or FinancialAccountTransaction does not mention `FinServ__WealthAppConfig__c`, `EnableRollupSummary`, or `RollupRecalculationBatchable`, it is missing the RBL safety pattern.

---

## Anti-Pattern 2: Treating FinancialAccountTransaction as Always a Custom Object

**What the LLM generates:** Instructions to load transaction data into `FinServ__FinancialAccountTransaction__c` regardless of whether the target org is managed-package or Core FSC.

**Why it happens:** The FSC managed package was historically the dominant deployment model and is well-represented in training data. The Core FSC standard object (`FinancialAccountTransaction`, no namespace, API v61.0+) is newer and less common in public documentation indexed before the training cutoff.

**Correct pattern:**

```
Managed-package FSC org  → target: FinServ__FinancialAccountTransaction__c
Core FSC org (v61.0+)    → target: FinancialAccountTransaction (standard object, no namespace)
```

Verify before building CSV mappings:
```bash
sf sobject describe --sobject FinancialAccountTransaction --target-org <alias>
```

**Detection hint:** If a response unconditionally uses `FinServ__FinancialAccountTransaction__c` without confirming the deployment model, flag it. Conversely, if it uses `FinancialAccountTransaction` without confirming Core FSC availability, also flag it.

---

## Anti-Pattern 3: Using Single Balance Field Strategy for Core FSC Orgs

**What the LLM generates:** A migration plan that writes a single balance value to a FinancialAccount field and considers balance migration complete, without loading any `FinancialAccountBalance` child records.

**Why it happens:** The managed-package FSC pattern (single `FinServ__Balance__c` field) is heavily documented online. Core FSC's `FinancialAccountBalance` child object is a newer addition and is sparsely represented in training data. The LLM defaults to the pattern it has seen most frequently.

**Correct pattern:**

```
Core FSC orgs require child FinancialAccountBalance records for balance history.
Load format: one row per account per snapshot date, sorted ascending by BalanceDate.
Objects: FinancialAccount (parent) → FinancialAccountBalance (child, FinancialAccountId FK)
```

**Detection hint:** If the response does not mention `FinancialAccountBalance` for a Core FSC migration, or if it claims balance is stored entirely on the FinancialAccount record in Core FSC, it is applying the managed-package strategy incorrectly.

---

## Anti-Pattern 4: Missing FinancialSecurity in the Insert Order

**What the LLM generates:** A six-step migration sequence that goes: Account → FinancialAccount → FinancialAccountRole → FinancialHolding → FinancialAccountTransaction, omitting FinancialSecurity.

**Why it happens:** FinancialSecurity is conceptually an instrument master / reference table, not a transactional record, and is often treated as pre-existing setup data rather than a migration artifact. LLMs frequently omit it when generating insert-order guidance because it does not appear in narrative descriptions of the "main" financial account migration flow.

**Correct pattern:**

```
Correct insert order:
1. Account / PersonAccount
2. FinancialSecurity          ← REQUIRED before FinancialHolding
3. FinancialAccount
4. FinancialAccountRole
5. FinancialHolding
6. FinancialAccountTransaction
```

**Detection hint:** Any generated insert-order list that shows FinancialHolding without FinancialSecurity appearing earlier in the sequence is missing this prerequisite.

---

## Anti-Pattern 5: Not Running RollupRecalculationBatchable After Load

**What the LLM generates:** A migration plan that re-enables `FinServ__EnableRollupSummary__c` after the load but does not invoke `RollupRecalculationBatchable`, or that omits the post-load step entirely.

**Why it happens:** LLMs understand that disabling and re-enabling a setting is a symmetric operation and often frame it as sufficient. The distinction between "re-enabling the trigger guard" and "recomputing all existing data that was loaded while the guard was off" is subtle and frequently omitted.

**Correct pattern:**

```apex
// After all ETL jobs complete and RBL is re-enabled:
Database.executeBatch(new FinServ.RollupRecalculationBatchable(), 200);
// Core FSC equivalent: trigger the configured DPE recalculation job
```

**Detection hint:** If a generated plan re-enables `EnableRollupSummary` but does not include a `RollupRecalculationBatchable` invocation or equivalent DPE step, the post-load recalculation is missing. FinancialAccount and household rollup totals will remain zero or stale.

---

## Anti-Pattern 6: Loading All Objects in a Single Parallel Job

**What the LLM generates:** A Data Loader configuration or script that loads all six object types simultaneously or in an unordered batch to maximize throughput.

**Why it happens:** LLMs optimizing for speed naturally suggest parallelism. The foreign-key dependency chain in FSC financial data is not always explicit in generic migration guidance.

**Correct pattern:**

```
Each object layer is a SEQUENTIAL job with validation between steps.
Do not parallelize across layers. Parallelizing within a single layer (e.g., 
splitting a 1M-row FinancialHolding file into parallel chunks) is acceptable 
provided parent FinancialAccount records are all committed first.
```

**Detection hint:** Any suggestion to run Account + FinancialAccount + FinancialHolding loads simultaneously is applying the wrong parallelism model and will produce foreign-key failures.
