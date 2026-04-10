# Gotchas — Subscription Management Architecture

Non-obvious Salesforce CPQ platform behaviors that cause real production problems in subscription lifecycle architecture.

## Gotcha 1: Ledger Model — Amendments Never Modify Existing Subscription Records

**What happens:** After an amendment is processed, the original `SBQQ__Subscription__c` record for an amended product still exists with its original quantity and price. A new delta subscription record is created representing the change. Any query, trigger, or integration that reads the original record (or "most recent" record) as the current state returns stale data.

**When it occurs:** Every amendment creates this condition for every changed product. After a contract has gone through two or three amendments, there may be five or more subscription records for a single product, spread across original and delta records. The problem is invisible to practitioners using the CPQ UI because the UI displays the calculated sum — the raw data model does not.

**How to avoid:** Design all integrations, reports, and Apex code that consume subscription data to aggregate `SBQQ__Subscription__c` records by `SBQQ__Contract__c` + `SBQQ__Product__c`, summing `SBQQ__Quantity__c` and applying weighted average or effective-date logic for price. Never treat the most recent subscription record as the source of truth for current state. Audit this assumption in every custom trigger, Process Builder, and integration mapping that touches `SBQQ__Subscription__c`.

---

## Gotcha 2: Co-termination Start Date Is Write-Once — Post-Activation Edits Break Proration

**What happens:** If `SBQQ__SubscriptionStartDate__c` on a `SBQQ__Subscription__c` record, or `SBQQ__CoTerminationDate__c` on a Contract, is edited after the contract is activated and subscriptions are generated, CPQ uses the new date for all subsequent proration calculations. However, CPQ does not retroactively adjust any proration that has already been invoiced. The result is a silent divergence between the billing ledger and the CPQ subscription ledger.

**When it occurs:** This most commonly happens when an admin edits a contract start date to correct a data entry error, or when a Flow/Apex trigger updates these fields as part of a data migration. It can also occur when a subscription is manually cloned or imported with a different start date than the original.

**How to avoid:** Treat `SBQQ__SubscriptionStartDate__c` and `SBQQ__CoTerminationDate__c` as write-once fields. Audit all Flows, Apex triggers, and validation rules that can write to these fields and add guards preventing writes after `Contract.Status = 'Activated'`. For data migrations involving date corrections, the correct path is to void the contract, regenerate it with the correct dates, and reprocess billing — not to edit the dates on active records.

---

## Gotcha 3: Preserve Bundle Structure + Combine Subscription Quantities Are Mutually Exclusive but Have No Warning

**What happens:** CPQ's "Preserve Bundle Structure" setting is designed to maintain the parent-child relationships between bundle products in subscription records, ensuring bundle children are not priced or renewed independently. "Combine Subscription Quantities" collapses multiple subscription records for the same product into a single record. When both are enabled, CPQ executes Combine Subscription Quantities first, collapsing bundle children before Preserve Bundle Structure has a chance to act. The bundle hierarchy is destroyed silently — no error or warning is shown.

**When it occurs:** This occurs when a CPQ administrator enables Combine Subscription Quantities for reporting simplicity without realizing that bundle products are on the same contracts. It is particularly common in post-merger CPQ consolidations where one org used bundles and the other did not.

**How to avoid:** Before enabling either setting, run a query to determine whether the org has both bundle products (`SBQQ__BundleRoot__c != null`) and multiple subscription records for the same product on the same contract. If bundles are present and subscriptions need consolidation, the options are: (1) keep Preserve Bundle Structure only, accepting multiple delta records per product, or (2) remove bundle configuration in favor of standalone products if consolidation is a hard requirement. Never enable both settings simultaneously.

---

## Gotcha 4: Large-Scale Async Mode Uses a Different Date Field Than Legacy Mode

**What happens:** In Legacy (synchronous) amendment mode, the amendment effective date is taken from `SBQQ__SubscriptionStartDate__c` on the amendment Quote. In Large-Scale (asynchronous) mode, the effective date is taken from `SBQQ__AmendmentStartDate__c` on the Contract. If the architecture is designed for one mode and the org later switches modes (because subscription line count grows past the threshold), all amendment effective dates begin coming from a different field. Proration calculations are based on the wrong date.

**When it occurs:** This most often occurs when a deployment starts with fewer than 200 subscription lines (Legacy mode) and grows to 1,000+ over time, triggering a switch to Large-Scale mode. Architects who did not document which date field drives amendments are caught off-guard when proration suddenly changes.

**How to avoid:** Document the chosen amendment service mode at architecture time, including the date field that drives effective date. If Large-Scale mode is adopted, implement automation to set `SBQQ__AmendmentStartDate__c` on the Contract correctly before initiating the async amendment. Add a validation rule or trigger guard preventing edits to `SBQQ__AmendmentStartDate__c` after an amendment job is in progress.

---

## Gotcha 5: Billing Schedules Fire Against Pre-Amendment Data if Contract Is Activated Before Async Job Completes

**What happens:** In Large-Scale async amendment mode, the `SBQQ.AmendmentBatchJob` runs asynchronously. If any automation (a triggered Flow, a platform event handler, or a scheduled Apex job) sets Contract Status to "Activated" before the batch job finishes, Salesforce Billing's trigger on `Status = 'Activated'` fires and generates `blng__BillingSchedule__c` records against the subscription data that exists at that moment — which is the pre-amendment data. The result is billing schedules that do not reflect the amendment: old quantities, old prices, missing new products, or present removed products.

**When it occurs:** This is most common when a CPQ deployment adds Large-Scale amendment support to an org that already has billing automation. The existing billing Flow or trigger was designed for Legacy mode, where the amendment completes synchronously before activation. The same automation now races with the async batch job.

**How to avoid:** Implement a check gate before any automation that sets `Contract.Status = 'Activated'`: query `AsyncApexJob` for pending `SBQQ.AmendmentBatchJob` records for the contract in question. If a job is in progress, defer activation until the job completes. Use a Platform Event or Scheduled Apex poll to trigger activation only after confirming `AsyncApexJob.Status = 'Completed'`. Test this sequencing explicitly in sandbox with production-scale subscription volumes.

---

## Gotcha 6: Renewal Quotes Reprice at List — Not Contracted Prices — by Default

**What happens:** Unlike amendment quotes (where existing subscription lines are locked to contracted price), renewal quotes reprice all lines at the current price book price. This means a customer who has been on a negotiated discount for three years will see list price on their auto-generated renewal quote. If the renewal quote is sent to the customer without review, they see an unexpected price increase.

**When it occurs:** Any time `SBQQ__RenewalQuoted__c = true` is enabled and the account does not have `SBQQ__ContractedPrice__c` records covering the renewed products.

**How to avoid:** Before enabling auto-renewal quote generation, create `SBQQ__ContractedPrice__c` records for the account-product combinations that should carry forward their negotiated prices. Alternatively, use the deferred renewal quote pattern (`SBQQ__RenewalQuoted__c = false`) so that a human reviews the renewal quote before it is presented to the customer. Never rely on auto-generated renewal quotes reaching the customer without a pricing review step.
