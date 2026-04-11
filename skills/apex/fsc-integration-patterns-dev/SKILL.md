---
name: fsc-integration-patterns-dev
description: "Use this skill when designing or implementing FSC-specific integration: core banking data sync, custodian feeds (Schwab/Fidelity), market data pipelines, or payment processing wired to FSC Financial objects. Triggers: syncing FinancialAccount or FinancialHolding records from a core banking system, integrating a custodian data feed into FSC Wealth Management, market data prices updating CurrentValue on FinancialHolding, payment transactions flowing into FSC from an external ledger. NOT for generic Salesforce integration, non-FSC object sync, or MuleSoft platform configuration unrelated to FSC financial objects."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Security
triggers:
  - "how do I sync FinancialAccount records from our core banking system into Salesforce FSC?"
  - "custodian feed from Schwab or Fidelity is causing row-lock errors on FinancialHolding bulk loads"
  - "market data price updates are failing when I call an external service from a trigger on FinancialHolding"
  - "need to reconcile daily holding positions from a custodian into FSC Wealth Management"
  - "FSC Integrations API remote call-in pattern for real-time custodian updates"
tags:
  - fsc
  - core-banking
  - custodian-integration
  - financial-holding
  - financial-account
  - bulk-api
  - platform-events
  - cdc
  - mulesoft
  - wealth-management
inputs:
  - "FSC org type: managed-package (FinServ__ namespace) or Core FSC (no namespace)"
  - "Integration pattern required: batch reconciliation, real-time event-driven, or market data feed"
  - "Target FSC objects: FinancialAccount, FinancialHolding, or both"
  - "Wealth Management Custom Settings: whether Rollup-by-Lookup is currently enabled"
  - "Custodian or core banking system identity (e.g. Schwab, Fidelity, FIS, Jack Henry)"
outputs:
  - "Integration pattern recommendation with rationale (Bulk API batch / Remote Call-In / CDC / Platform Events)"
  - "Apex batch or scheduled class for market data or reconciliation loads"
  - "Pre-load and post-load checklist covering RBL disable, DPE recalculation, and idempotency"
  - "Review checklist for row-lock prevention and governor limit compliance"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# FSC Integration Patterns — Developer Guidance

Use this skill when building or reviewing Apex-backed integrations that move financial data into or out of FSC Financial Services Cloud objects. It covers daily batch reconciliation from core banking systems, real-time custodian feed handling via the FSC Integrations API, market data price pipelines, and payment transaction flows. It does not cover generic Salesforce REST/SOAP integration or MuleSoft platform setup unrelated to FSC financial objects.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Namespace**: Determine whether the org uses the managed-package FSC (`FinServ__` namespace) or Core FSC (no namespace). Object API names differ — `FinServ__FinancialAccount__c` vs `FinancialAccount`. All integration queries, upserts, and field references must use the correct prefix.
- **Rollup-by-Lookup (RBL) status**: In Wealth Management Custom Settings, check whether RBL is enabled for the integration user. This is the single most common source of row-lock failures on bulk FinancialHolding loads. It must be disabled for the integration user before any batch operation against FinancialHolding or FinancialAccount.
- **Pattern required**: Confirm whether the integration is (a) daily batch reconciliation, (b) real-time event-driven custodian updates, or (c) market data price feeds. Each requires a different Apex pattern and different governor limit budget.
- **Volume expectations**: Establish record counts per load. Anything above ~5,000 FinancialHolding rows per run requires Bulk API 2.0 job semantics rather than synchronous DML.

---

## Core Concepts

### FSC Integrations API and Remote Call-In

The FSC Integrations API supports a Remote Call-In pattern for real-time custodian updates. External systems POST enriched financial data payloads to a Salesforce REST endpoint; Apex handler classes parse, validate, and upsert to FSC objects in the same transaction. This pattern is appropriate when custodian systems can emit near-real-time webhooks and latency of seconds is acceptable. It is not appropriate for daily position reconciliation at scale — batch Bulk API is the right tool there.

Change Data Capture (CDC) works in the reverse direction: FSC object changes flow outward to downstream systems. CDC on `FinancialAccount` is appropriate for replicating Salesforce-side changes (advisor notes, risk profile updates) back to a core banking system. Platform Events suit cross-application process orchestration — for example, notifying a downstream risk system when a new account is opened.

### Bulk API Batch Loads for Daily Reconciliation

Core banking and custodian systems typically produce end-of-day position files. The standard pattern uses MuleSoft BIAN-canonical integration templates (or an equivalent ETL) to transform these files into Bulk API 2.0 ingest jobs targeting `FinancialAccount` and `FinancialHolding`. Bulk API 2.0 processes records in parallel server-side batches of up to 10,000 rows, does not consume synchronous Apex CPU, and provides job-level success/failure results that are safe to inspect asynchronously.

Key constraint: `FinancialHolding` records share a parent `FinancialAccount`. Concurrent Bulk API batches that touch holdings with the same parent will contend for the parent row lock if any trigger or process fires a rollup recalculation during the load. This is why RBL must be disabled for the integration user and DPE-based post-load recalculation must be scheduled separately.

### Scheduled and Batch Apex for Market Data Feeds

Market data feeds update `CurrentValue` (and related price fields) on `FinancialHolding` records after each trading day. The correct Apex pattern is a `Schedulable` that enqueues a `Batchable` class. The batch queries holdings needing price updates, makes callouts to the market data vendor in `execute()` chunks, and updates the records. Synchronous callouts from DML-heavy triggers are prohibited by the Apex callout-after-DML restriction and will fail at runtime with a `System.CalloutException`. Post-load DPE aggregation should recalculate portfolio totals after the batch completes, not inline.

---

## Common Patterns

### Pattern A: Daily Custodian Reconciliation via Bulk API

**When to use:** End-of-day position file from Schwab, Fidelity, or similar; file volume 5,000–2,000,000 FinancialHolding rows per night.

**How it works:**
1. Disable RBL for the integration user in Wealth Management Custom Settings (via Named Credential–secured connected app with a dedicated integration profile).
2. ETL/MuleSoft transforms custodian position file into Bulk API 2.0 ingest job against `FinancialHolding`, using `ExternalId` or `AccountNumber` as the upsert key.
3. Monitor job via Bulk API job status endpoint; log failures to a custom object for reconciliation review.
4. After job completes, enqueue a Schedulable/Batchable to trigger DPE recalculation of household and account-level rollups.
5. Re-enable RBL (or leave it disabled if nightly runs are continuous).

**Why not synchronous Apex upsert:** Bulk loads of this volume exceed `DMLException` transaction limits, trigger callout-after-DML restrictions, and cause rollup row-lock contention if RBL is active.

### Pattern B: Real-Time Custodian Update via FSC Integrations API

**When to use:** Custodian or payment processor can emit near-real-time webhooks; fewer than a few hundred records per event; latency of 2–5 seconds is acceptable.

**How it works:**
1. External system authenticates to Salesforce via Connected App (OAuth 2.0 JWT Bearer).
2. POST payload to a custom REST endpoint backed by an `@RestResource` Apex class.
3. Handler class validates payload, applies idempotency check (query for existing record by external ID before insert), and upserts to `FinancialAccount` or `FinancialHolding`.
4. Platform Event is published on success to notify downstream processes.

**Why not inbound Bulk API for real-time:** Bulk API jobs are asynchronous with variable processing delay; they are not suitable for sub-second transactional confirmation.

### Pattern C: Market Data Price Feed via Scheduled Batch

**When to use:** Daily or intraday `CurrentValue` updates on FinancialHolding; external market data vendor provides REST price endpoint.

**How it works:**
1. `Schedulable` class fires at market close (or configured interval).
2. Enqueues `Batchable` with scope of 50–100 holdings per chunk (tuned to callout limits).
3. Each `execute()` chunk calls market data endpoint, maps prices to holdings, performs DML update.
4. `finish()` method publishes Platform Event to trigger downstream DPE recalculation.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Daily end-of-day position file, 10k–2M rows | Bulk API 2.0 ingest job (via MuleSoft or ETL) | Scale, parallelism, no Apex CPU cost |
| Real-time custodian webhook, <500 records | FSC Integrations API (Remote Call-In, `@RestResource`) | Low latency, transactional confirmation |
| FSC changes replicate to core banking | Change Data Capture on FinancialAccount | Native Salesforce event emission, no polling |
| Cross-app process notification (new account opened) | Platform Events | Decoupled, durable, retry-safe |
| Daily market data price updates | Scheduled Batch Apex with callouts | Avoids callout-after-DML, respects callout limits |
| Post-load rollup recalculation | Data Processing Engine (DPE) | Avoids RBL row-lock contention at scale |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm org namespace and pattern scope** — determine managed-package vs Core FSC, identify which FSC objects are targets, and confirm whether the integration is batch, real-time, or market-data-feed.
2. **Check Rollup-by-Lookup configuration** — before any bulk load design, verify RBL status for the integration user in Wealth Management Custom Settings. Document whether it needs to be disabled before the load and re-enabled (or replaced with DPE) after.
3. **Select the integration pattern** — use the Decision Guidance table to choose between Bulk API batch, Remote Call-In, CDC, Platform Events, or Scheduled Batch. Do not mix synchronous callouts with DML-heavy trigger paths.
4. **Implement Apex with idempotency** — for Remote Call-In patterns, query for existing records by external ID before upsert. For batch patterns, implement `Database.Stateful` if state must persist across chunks and use `Database.executeBatch` with appropriate scope size.
5. **Validate governor limit budget** — confirm callout count (max 100 per transaction), heap size, and CPU time are within limits for the chosen scope. For Bulk API jobs, confirm job concurrency limits (10 open jobs per org).
6. **Test with realistic data volume** — unit tests must cover both the happy path and the failure path (invalid payload, duplicate external ID, RBL still enabled). Integration tests should use a Bulk API sandbox load of at least 10,000 records to surface row-lock behavior.
7. **Wire post-load DPE recalculation** — after any batch load, schedule DPE to recompute household rollups. Verify rollup correctness against a known-good custodian snapshot before signing off.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Integration user profile has RBL disabled in Wealth Management Custom Settings before any bulk FinancialHolding load
- [ ] Bulk API 2.0 job is used for loads above ~5,000 records (not synchronous DML)
- [ ] No synchronous callouts inside triggers or transaction-heavy DML paths on FinancialHolding
- [ ] Idempotency check (external ID query before upsert) present in all Remote Call-In handlers
- [ ] DPE recalculation scheduled as a separate step after bulk loads complete
- [ ] Connected App uses Named Credential and OAuth 2.0 JWT Bearer (not username/password)
- [ ] Apex batch scope size tuned to keep callout count + DML rows within per-transaction limits

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **RBL row-lock on concurrent FinancialHolding writes** — When Rollup-by-Lookup is enabled, every write to a FinancialHolding record triggers a recalculation that acquires a row-lock on the parent FinancialAccount. Bulk API processes batches in parallel, so multiple batches touching holdings under the same account contend for the same parent lock, causing `UNABLE_TO_LOCK_ROW` errors. Fix: disable RBL for the integration user before the load; recalculate via DPE afterward.
2. **Callout-after-DML restriction on trigger paths** — Apex prohibits callouts after DML has been performed in the same transaction. Any trigger on FinancialHolding that attempts to call a market data or custodian endpoint after an upsert will throw `System.CalloutException: You have uncommitted work pending`. Fix: move callouts to a Queueable or Schedulable/Batchable class that runs in a fresh transaction.
3. **Namespace mismatch between managed-package and Core FSC** — Queries, field references, and SOQL written for one FSC deployment type fail silently or throw `System.QueryException` in another. Managed-package orgs use `FinServ__FinancialAccount__c`; Core FSC orgs use `FinancialAccount`. Always confirm namespace at the start of any integration work and parameterize object/field references.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Integration pattern recommendation | Pattern selection (Bulk API / Remote Call-In / CDC / Platform Events / Scheduled Batch) with rationale |
| RBL pre/post-load checklist | Steps to disable RBL, run load, schedule DPE recalculation |
| Apex batch or scheduled class | Batchable + Schedulable implementation for market data or reconciliation loads |
| Remote Call-In handler | `@RestResource` Apex class with idempotency check and error handling |

---

## Related Skills

- `admin/financial-account-setup` — configure FinancialAccount and FinancialHolding data model, roles, and household rollup settings before wiring integration
- `integration/event-driven-architecture-patterns` — general Platform Events and CDC patterns when FSC-specific guidance is not required
- `apex/fsl-integration-patterns` — FSL-specific integration patterns for field service; separate domain from FSC financial integrations
