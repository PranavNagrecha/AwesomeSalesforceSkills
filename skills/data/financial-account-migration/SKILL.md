---
name: financial-account-migration
description: "Use this skill when bulk-migrating financial account data into Salesforce FSC — including FinancialAccount, FinancialHolding, FinancialAccountRole, FinancialAccountTransaction, and balance history records. Trigger keywords: ETL load FSC, migrate holdings, bulk insert financial accounts, data migration rollup lock, FinancialAccountBalance import. NOT for financial account configuration or FSC data model reference."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
triggers:
  - "How do I bulk load FinancialHolding records without causing row-lock errors in FSC?"
  - "What is the correct insert order for migrating financial accounts, holdings, and transactions into FSC?"
  - "My FSC data migration is failing with record lock timeouts — how do I disable rollup triggers before loading?"
  - "How do I migrate balance history for financial accounts in Core FSC vs the managed package?"
  - "FinancialSecurity records must pre-exist before loading FinancialHolding — how do I set that up?"
tags:
  - fsc
  - data-migration
  - financial-accounts
  - holdings
  - transactions
  - bulk-load
inputs:
  - "Source system export files (CSV or equivalent) for accounts, holdings, transactions, and balances"
  - "FSC package type: managed package (FinServ__) or Core FSC (API v61.0+ standard objects)"
  - "Target org credentials and Salesforce CLI / Data Loader access"
  - "Wealth Application Config custom setting access (for RBL disablement)"
outputs:
  - "Validated, sequenced bulk load plan covering all six object layers"
  - "Pre-load and post-load configuration steps for Rollup-by-Lookup management"
  - "Balance history migration approach tailored to managed package vs Core FSC"
  - "Post-load recalculation commands (RollupRecalculationBatchable or DPE)"
dependencies:
  - admin/financial-account-setup
  - admin/fsc-data-model
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# Financial Account Migration

This skill covers bulk migration execution for FSC financial data — the correct object insert sequence, how to suppress Rollup-by-Lookup (RBL) triggers during load to prevent row-lock errors, and how to handle balance history differently depending on whether the org runs the managed package or Core FSC (API v61.0+). It does not cover FSC configuration, object model reference, or non-financial data migration.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the org uses the **FSC managed package** (`FinServ__` namespace) or **Core FSC** standard objects (available from API v61.0 / Spring '25). The balance history migration approach differs fundamentally between the two.
- Check whether **"Enable Rollup Summary"** is active in Wealth Application Config. If it is, Apex RBL triggers will fire on every DML row and will cause record-lock timeouts at bulk-load volumes.
- Verify that **FinancialSecurity** records (instrument master data — stocks, funds, etc.) already exist in the target org before any FinancialHolding insert. FinancialHolding has a required lookup to FinancialSecurity; missing records cause immediate load failures.

---

## Core Concepts

### 1. Six-Layer Insert Order

FSC financial data has strict parent-child and lookup dependencies. The correct order is:

1. **Account / PersonAccount** — the client record. Every FinancialAccount requires an Account parent.
2. **FinancialSecurity** — instrument master. Must pre-exist before FinancialHolding can reference it. If your source system includes positions, load securities first even if they appear to be a child concept.
3. **FinancialAccount** — the account (brokerage, checking, insurance policy, etc.). References Account.
4. **FinancialAccountRole** — the Primary Owner and any additional roles. References both FinancialAccount and Contact/Account. Load at least the Primary Owner role before loading FinancialHolding or FinancialAccountTransaction.
5. **FinancialHolding** — individual positions held within a FinancialAccount. References both FinancialAccount and FinancialSecurity.
6. **FinancialAccountTransaction** — transaction history entries. References FinancialAccount (and optionally FinancialHolding). Load last.

Inverting any step creates foreign-key lookup failures that can only be resolved by deleting and re-inserting downstream records.

### 2. Rollup-by-Lookup (RBL) and Bulk Load

FSC's Rollup-by-Lookup feature aggregates holding values and transaction totals up to the FinancialAccount and then to the household. The aggregation is implemented as Apex triggers (`FinServAssetsLiabilitiesTrigger`, `FinancialHoldingTrigger`, and related classes). During bulk ETL, these triggers fire row-by-row inside the DML transaction and compete for the same FinancialAccount record, causing `UNABLE_TO_LOCK_ROW` errors at virtually any load volume above a few hundred rows per batch.

**Mitigation — pre-load:** Disable RBL for the ETL integration user via the **Wealth Application Config** custom setting (`FinServ__WealthAppConfig__c`). Set `FinServ__EnableRollupSummary__c = false` for the dedicated ETL user's profile or use the OmniStudio / Apex custom setting API to set it programmatically before the load job runs.

**Mitigation — post-load:** After all records are committed, run `FinServ.RollupRecalculationBatchable` (managed package) or the equivalent Data Processing Engine (DPE) job (Core FSC) to rebuild all rollup values from scratch. This produces a clean, consistent state without incremental trigger races.

### 3. Balance History: Managed Package vs Core FSC

The two FSC deployment models store balance history differently:

| Aspect | Managed Package (FinServ__ namespace) | Core FSC (API v61.0+) |
|---|---|---|
| Balance storage | Single overwritable field `FinServ__Balance__c` on FinancialAccount | Child `FinancialAccountBalance` object; one record per snapshot date |
| History available? | No native snapshot history; balance is the current value only | Yes — each `FinancialAccountBalance` record captures a point-in-time balance |
| Migration approach | Load the most recent balance into `FinServ__Balance__c` during FinancialAccount insert | Load FinancialAccount first, then insert one `FinancialAccountBalance` row per historical snapshot |
| Post-load recalc | Run `RollupRecalculationBatchable` | Run DPE recalculation job; `FinancialAccountBalance` records are not recalculated by rollups |

If you apply the managed-package single-field strategy to a Core FSC org you will discard all historical balance data and the org's balance trend charts will be permanently empty.

### 4. FinancialAccountTransaction — Standard vs Custom

`FinancialAccountTransaction` is a **standard object in Core FSC** (API v61.0+). In the FSC managed package it is the custom object `FinServ__FinancialAccountTransaction__c`. Both exist natively in their respective deployment models; neither is a practitioner-created custom object. Do not attempt to create a replacement custom object — use the platform-provided object for your deployment model.

---

## Common Patterns

### Pattern A: RBL-Safe Bulk Load (Managed Package)

**When to use:** Any bulk insert of FinancialHolding or FinancialAccountTransaction in a managed-package FSC org.

**How it works:**
1. Before the ETL job: query `FinServ__WealthAppConfig__c` and set `FinServ__EnableRollupSummary__c = false` for the ETL user via Apex or the Tooling API.
2. Run Data Loader / Bulk API 2.0 jobs in dependency order (see Six-Layer Insert Order).
3. After all jobs complete: re-enable the setting, then invoke `Database.executeBatch(new FinServ.RollupRecalculationBatchable(), 200)` via Anonymous Apex or a scheduled job.
4. Validate: query aggregate holding balances and compare to source system totals.

**Why not the alternative:** Loading with RBL enabled causes `UNABLE_TO_LOCK_ROW` errors after the first few hundred rows of FinancialHolding in most orgs. Disabling it at the org level (not just the user level) also risks disrupting live advisor users; the per-user setting is the safe scope.

### Pattern B: Core FSC Balance History Snapshot Load

**When to use:** Migrating historical balance data into a Core FSC (v61.0+) org where balance history must be preserved.

**How it works:**
1. Load FinancialAccount records first (no balance field needed at this stage).
2. For each historical balance snapshot in the source system, create one `FinancialAccountBalance` record with `FinancialAccountId`, `Balance`, `BalanceDate`, and `CurrencyIsoCode`.
3. Load snapshots in ascending date order to avoid any UI anomalies in trend charts.
4. The most recent snapshot value is the current balance visible in the UI; no separate field update is needed.

**Why not the alternative:** Writing a single balance value to the FinancialAccount record (the managed-package approach) is not wrong in Core FSC but discards all historical data. Balance history drives advisory analytics; losing it is typically unacceptable in a migration.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Managed-package org, bulk load of holdings/transactions | Disable RBL → load → run RollupRecalculationBatchable | RBL triggers cause row-lock at scale; batch recalc is reliable |
| Core FSC org, balance history must be preserved | Load FinancialAccount then FinancialAccountBalance child rows | Core FSC has native snapshot history; managed-package strategy discards it |
| Core FSC org, balance history not required | Load FinancialAccount with current balance only; skip FinancialAccountBalance | Simpler load; acceptable only when history is confirmed out of scope |
| FinancialHolding insert failing with lookup errors | Load FinancialSecurity first, then re-run FinancialHolding | FinancialHolding.FinancialSecurityId is required; missing parent = immediate failure |
| Transaction load to managed-package org | Target `FinServ__FinancialAccountTransaction__c` custom object | Managed package does not use the Core FSC standard object |
| Transaction load to Core FSC org | Target standard `FinancialAccountTransaction` object (API v61.0+) | Core FSC provides this as a standard object; do not create a custom replacement |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm deployment model and RBL status** — Determine whether the org uses the FSC managed package (`FinServ__` namespace) or Core FSC standard objects (API v61.0+). Query `FinServ__WealthAppConfig__c` to check whether `FinServ__EnableRollupSummary__c` is true. Document the current value so it can be restored after load.
2. **Pre-load: disable RBL for the ETL user** — Set `FinServ__EnableRollupSummary__c = false` on the Wealth Application Config custom setting for the ETL integration user before any bulk DML begins. For Core FSC orgs, confirm the equivalent DPE recalculation job is identified and ready to run post-load.
3. **Load objects in strict dependency order** — Execute bulk loads in this sequence: Account/PersonAccount → FinancialSecurity → FinancialAccount → FinancialAccountRole (Primary Owner first) → FinancialHolding → FinancialAccountTransaction. Use Bulk API 2.0 with `UPSERT` on an external ID field where possible to support re-runnable loads.
4. **Handle balance history per deployment model** — For managed-package orgs, write the current balance to `FinServ__Balance__c` during the FinancialAccount load. For Core FSC orgs, load `FinancialAccountBalance` child records after FinancialAccount, one row per historical snapshot in ascending date order.
5. **Post-load: run rollup recalculation** — Re-enable RBL for the ETL user, then run `FinServ.RollupRecalculationBatchable` (managed package) or the configured DPE job (Core FSC) to rebuild all aggregated balances. Do not skip this step; FinancialAccount and household totals will be zero or stale until recalculation completes.
6. **Validate and reconcile** — Query total record counts per object and compare to source. Spot-check holding balances and transaction counts for a sample of accounts. Verify that household-level rollups reflect correct totals after the recalculation batch completes.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] RBL was disabled for the ETL user before any FinancialHolding or FinancialAccountTransaction DML
- [ ] FinancialSecurity records were loaded before FinancialHolding
- [ ] FinancialAccountRole (Primary Owner) was loaded before FinancialHolding
- [ ] Balance history strategy matches the deployment model (snapshot rows for Core FSC, single field for managed package)
- [ ] `RollupRecalculationBatchable` or DPE recalculation job ran to completion post-load
- [ ] Record counts reconcile between source and target for all six object layers
- [ ] Household-level balance rollups are non-zero and match expected totals

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **RBL triggers fire on every single DML row** — The FSC Rollup-by-Lookup implementation uses synchronous Apex triggers, not platform roll-up summary fields. At bulk volumes, multiple load threads updating holdings under the same FinancialAccount compete for a row lock on that parent record, producing `UNABLE_TO_LOCK_ROW` exceptions. Disabling the setting does not remove the trigger; it adds a guard condition checked at runtime.
2. **FinancialSecurity is a silent prerequisite** — The FinancialHolding object has a required lookup (`FinancialSecurityId`) that is easy to overlook in data mapping. If FinancialSecurity records do not already exist in the target org, every FinancialHolding row will fail with a foreign-key error. Source systems often call these "instruments" or "securities" in a separate catalog table.
3. **Core FSC balance history is a child object, not a field** — Practitioners familiar with the managed package assume they can write `Balance__c` on FinancialAccount and be done. In Core FSC orgs, the `FinancialAccountBalance` child object is the canonical store for balance data. Writing only to a top-level field (if one exists) does not populate history and advisor analytics will show empty trend charts.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Sequenced bulk load plan | Six-step ordered job list with object names, external ID fields, and batch size recommendations |
| RBL pre/post configuration steps | Anonymous Apex or CLI commands to disable and re-enable the Wealth Application Config setting |
| Balance history load file | CSV template for `FinancialAccountBalance` records (Core FSC) or FinancialAccount balance field mapping (managed package) |
| Post-load recalculation command | Anonymous Apex snippet invoking `RollupRecalculationBatchable` or DPE job reference |

---

## Related Skills

- `admin/financial-account-setup` — configure FSC financial account types, roles, and household rollup behavior (use before migration to confirm target configuration is correct)
- `admin/fsc-data-model` — FSC object model reference; use to identify correct API names and relationship fields before building data mapping
