---
name: subscription-management-architecture
description: "Use when designing or evaluating Salesforce CPQ subscription lifecycle architecture: amendment flow, renewal automation, co-termination design, or billing integration at the contract level. Trigger keywords: amendment architecture, renewal automation, co-termination design, subscription ledger, large-scale amendment, billing schedule, swap pattern, SBQQ__Subscription__c. NOT for billing setup, standard Salesforce contracts without CPQ, or Revenue Cloud advanced order management."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Operational Excellence
triggers:
  - "how should we architect CPQ amendment and renewal flows for a large enterprise contract portfolio"
  - "our amendment quotes are creating duplicate subscription records instead of modifying existing ones"
  - "we need to change the price on an active subscription mid-contract — what is the correct pattern"
  - "co-termination start date edits are breaking proration on existing subscriptions"
  - "how do we configure renewal automation with SBQQ__RenewalForecast__c and SBQQ__RenewalQuoted__c"
  - "billing schedules are not generating after contract activation"
tags:
  - cpq
  - subscriptions
  - amendments
  - renewals
  - co-termination
  - billing-integration
  - sbqq
  - large-scale-amendment
  - ledger-model
inputs:
  - "CPQ package version installed in org"
  - "Approximate number of active SBQQ__Subscription__c records on contracts being amended"
  - "Whether the org uses bundle products with Preserve Bundle Structure enabled"
  - "Whether Combine Subscription Quantities is enabled in CPQ Settings"
  - "Whether Salesforce Billing is installed and blng__BillingSchedule__c records are expected"
  - "Renewal automation preference: auto-renew vs agent-initiated renewal"
  - "Co-termination strategy: earliest-end co-term vs fixed anchor date"
outputs:
  - "Amendment architecture decision: synchronous (Legacy) vs asynchronous (Large-Scale) service mode"
  - "Documented swap pattern for mid-contract price changes on existing subscriptions"
  - "Co-termination design with immutable Start Date guidance"
  - "Renewal automation configuration using SBQQ__RenewalForecast__c and SBQQ__RenewalQuoted__c"
  - "Billing integration checklist: Contract activation prerequisites for blng__BillingSchedule__c generation"
dependencies:
  - contract-and-renewal-management
  - cpq-pricing-rules
  - cpq-architecture-patterns
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# Subscription Management Architecture

This skill activates when designing or reviewing the architecture of a Salesforce CPQ subscription lifecycle: how amendments flow through the system, how renewals are automated, how co-termination is designed without breaking proration, and how billing integration is triggered at contract activation. It is the architect-level counterpart to the `contract-and-renewal-management` admin skill — it focuses on system design choices and failure modes rather than step-by-step configuration.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm CPQ package version (check Setup > Installed Packages). Large-Scale amendment behavior changed significantly in CPQ v228+. The async batch API (`SBQQ.ContractManipulationAPI`) and the separate Large-Scale Amendment service mode have different field semantics.
- Determine the approximate count of `SBQQ__Subscription__c` records on the contracts involved. Under ~200 lines: synchronous (Legacy) mode is safe. 200–1,000 lines: test in sandbox. Over 1,000 lines: design for async (Large-Scale) mode from the start.
- The most common wrong assumption: practitioners believe CPQ updates existing `SBQQ__Subscription__c` records when an amendment is processed. It does not. CPQ uses a **ledger model** — amendments create new delta subscription records. Existing records are never modified. This has cascading implications for reporting, billing integration, and custom triggers.
- Confirm whether Salesforce Billing is installed. If `blng__BillingSchedule__c` is expected, the Contract must reach "Activated" status before billing schedules generate. A Contract stuck in "Draft" silently blocks billing.
- Determine whether bundle products exist on contracts that will be amended. The interaction between **Preserve Bundle Structure** and **Combine Subscription Quantities** is a silent breaking combination that must be resolved before any bundle amendment is attempted.

---

## Core Concepts

### The CPQ Ledger Model: Amendments as Delta Records

Salesforce CPQ uses a ledger model for subscription state. When an amendment is processed, CPQ does **not** modify existing `SBQQ__Subscription__c` records. Instead, it creates new delta subscription records representing the change: a quantity increase creates a new record with the positive delta, a quantity decrease creates a record with the negative delta, and a product removal creates a zero-out record.

The active subscription state is derived by summing all subscription records for a given product on a contract, not by reading a single mutable record. This means:

- Any custom Apex, Flow, or reporting that reads a single `SBQQ__Subscription__c` record and treats it as the current state will be wrong after the first amendment.
- Integration systems (ERP, billing, entitlement) must be designed to aggregate subscription records by `SBQQ__Contract__c` + `SBQQ__Product__c` + `SBQQ__StartDate__c` grouping, not to react to individual record changes.
- Triggers on `SBQQ__Subscription__c` that perform calculations on insert will fire for every delta record, including the new ones created by each amendment. Design triggers to handle delta quantities, not assume net quantities.

### Price Change Swap Pattern

Changing the price of an existing active subscription mid-contract is not directly supported by CPQ's amendment mechanism, because existing subscription lines are locked to their contracted price. The only supported architecture for a mid-contract price change is the **swap pattern**:

1. In the amendment quote, set the quantity of the existing product line to zero (or reduce to zero) — this creates a negative delta subscription record zeroing out the original.
2. Add a new product line for the same product at the new price — this creates a new subscription record at the updated price with the new start date.
3. Co-termination applies to both records, ensuring the new line ends on the same date as the rest of the contract.

The swap pattern has a billing implication: if Salesforce Billing is active, the zero-out and the new line each generate billing schedule actions. The architecture must account for credit memos against the original line and new invoices against the replacement line.

### Preserve Bundle Structure vs Combine Subscription Quantities

CPQ has two overlapping settings that control how bundle product subscriptions are managed during amendments:

- **Preserve Bundle Structure** (`SBQQ__PreserveBundleStructure__c` in CPQ Settings): when enabled, amendment quotes keep bundle parent-child relationships intact. This is required for bundles where child products have individually priced subscriptions.
- **Combine Subscription Quantities** (`SBQQ__CombineSubscriptionQuantities__c` in CPQ Settings): when enabled, subscription records for the same product on the same contract are collapsed into a single record rather than maintained as separate delta records.

**Critical conflict:** when both settings are active simultaneously, Preserve Bundle Structure is silently ignored. Bundle child subscriptions are collapsed into single records, destroying the parent-child relationship in the subscription data. This produces incorrect renewal quotes (child products reprice independently of bundle logic) and breaks any entitlement or billing system that relies on bundle membership. The correct design is to choose one model: either preserve bundles OR combine quantities, not both.

### Legacy vs Large-Scale Amendment Service Modes

CPQ provides two service modes for amendment and renewal processing:

**Legacy mode (synchronous):**
- Triggered via the Amend/Renew button on the Contract record or via `SBQQ.ContractManipulationAPI` without the async flag.
- Executes within a single synchronous transaction.
- Reliable up to approximately 200 `SBQQ__Subscription__c` records.
- Field behavior: `SBQQ__SubscriptionStartDate__c` on the amendment quote is set to the amendment effective date.

**Large-Scale mode (asynchronous batch):**
- Triggered via `SBQQ.ContractManipulationAPI.amend()` with the async parameter, or via the dedicated batch job framework documented in KA-000384875.
- Executes as an `AsyncApexJob` (`SBQQ.AmendmentBatchJob` class).
- Required for contracts with 1,000+ subscription lines.
- Field behavior differs: `SBQQ__AmendmentStartDate__c` on the Contract drives the effective date rather than the quote field. Edits to this field post-activation produce incorrect proration if subscriptions have already been processed.
- Monitoring: poll `AsyncApexJob` for `Status IN ('Completed', 'Failed')` before presenting the amendment quote to the user.

The service mode must be decided at architecture time. Retrofitting synchronous contracts to async processing mid-deployment requires testing every downstream integration and trigger.

### Co-termination Design and Start Date Immutability

Co-termination forces all subscription lines on a contract to share the same end date — the earliest-ending subscription on the contract. The **co-termination start date** (`SBQQ__CoTerminationDate__c` on the Contract) is the anchor for all proration calculations during amendments.

**Immutability rule:** Once `SBQQ__CoTerminationDate__c` (or `SBQQ__SubscriptionStartDate__c` on individual subscriptions) is set on an active contract, editing it post-sale corrupts all proration calculations for subsequent amendments. The proration formula (remaining days / total days × price) is calculated against the original start date. If the start date is changed after subscriptions are generated, CPQ recalculates proration against the new date but does not reprocess historical billing — resulting in over-charging or under-charging.

Treat subscription start dates and co-termination anchors as **write-once fields**. Any architecture that allows post-activation edits to these fields (via Flow, Apex trigger, or direct field edit) must be rejected.

### Renewal Automation Configuration

Renewal automation is controlled by two fields on the Contract object:

- `SBQQ__RenewalForecast__c` (checkbox): when true, CPQ creates a Renewal Opportunity automatically when the contract is activated.
- `SBQQ__RenewalQuoted__c` (checkbox): when true, CPQ creates a Renewal Quote linked to the Renewal Opportunity.

Both fields must be true for the full auto-renewal flow. Setting only `SBQQ__RenewalForecast__c` creates the Opportunity but not the Quote — this is the correct pattern when renewal negotiations require human review before pricing.

Renewal quotes reprice at **current** price book prices by default, not contracted prices. To lock renewal pricing to a specific price, create `SBQQ__ContractedPrice__c` records linking the Account, Product, and price before the renewal quote is generated.

### Billing Integration at Contract Level

Salesforce Billing generates `blng__BillingSchedule__c` records when a Contract is activated. The integration point is the Contract Status field: the billing engine listens for `Status = 'Activated'` to trigger schedule generation.

Architecture requirements:
- The Contract must have `SBQQ__Contracted__c = true` on the parent Opportunity AND the Contract Status must be moved to "Activated" explicitly.
- Any custom Apex or automation that sets Contract Status to "Activated" before CPQ has finished processing subscriptions will generate billing schedules against incomplete subscription data.
- The correct sequence: CPQ processes the quote → Contract is created → `SBQQ__Subscription__c` records are fully written → Contract Status is set to "Activated" → Billing engine generates `blng__BillingSchedule__c` records.
- For async Large-Scale amendments, billing schedule generation must be deferred until `AsyncApexJob` completes.

---

## Common Patterns

### Pattern: Mid-Contract Price Change (Swap Pattern)

**When to use:** A customer negotiates a new unit price for a product already on an active contract. The price must change starting from a specific date, not at renewal.

**How it works:**
1. Initiate an amendment from the active Contract record.
2. On the amendment quote, locate the existing subscription line for the product.
3. Set the quantity on that line to 0 — this generates a negative delta `SBQQ__Subscription__c` record zeroing out the original.
4. Add a new product line for the same product, entering the new agreed unit price as an override or via a Price Rule.
5. Calculate the quote. CPQ applies co-termination to the new line, prorating it from the amendment effective date to the co-termination date.
6. Approve and activate. Two new `SBQQ__Subscription__c` records are created: one zero-quantity close-out and one new-price record.

**Why not direct price edit:** CPQ locks existing subscription line prices on amendment quotes. Attempting to override the price directly on an existing line will be rejected or silently reverted. The swap pattern is the only path that CPQ's pricing engine honors.

### Pattern: Large-Scale Async Amendment

**When to use:** The contract has 1,000+ active `SBQQ__Subscription__c` records and synchronous amendment generation times out or hits CPU limits.

**How it works:**
```apex
// Trigger async amendment via ContractManipulationAPI
Id contractId = '800xx000001234AAA';
SBQQ.ContractManipulationAPI.AmendmentContext ctx = 
    new SBQQ.ContractManipulationAPI.AmendmentContext();
ctx.contractId = contractId;
// Setting amendmentStartDate explicitly; defaults to today if omitted
ctx.amendmentStartDate = Date.today();
SBQQ.ContractManipulationAPI.amend(ctx);
```
After calling `amend()`, poll for job completion:
```apex
List<AsyncApexJob> jobs = [
    SELECT Id, Status, NumberOfErrors
    FROM AsyncApexJob
    WHERE ApexClass.Name = 'AmendmentBatchJob'
    AND Status NOT IN ('Completed', 'Failed')
    ORDER BY CreatedDate DESC
    LIMIT 1
];
```
Once `Status = 'Completed'`, the amendment quote is available on the Contract's related list.

**Why not the Amend button:** For 1,000+ lines, the synchronous path exhausts Apex CPU time limits (10,000 ms for synchronous). The async path distributes processing across batch chunks and does not block the user session.

### Pattern: Renewal Forecast with Deferred Quote Generation

**When to use:** The org needs a renewal pipeline visible in forecasting before the renewal quote is negotiated, but the renewal price should not be locked automatically.

**How it works:**
1. Set `SBQQ__RenewalForecast__c = true` on the Contract (or set in CPQ Settings as the default).
2. Leave `SBQQ__RenewalQuoted__c = false`.
3. On contract activation, CPQ creates a Renewal Opportunity with the renewal amount as a forecast, but no Quote is generated.
4. When the account team is ready to negotiate, they manually initiate the Renew action from the Contract or the Renewal Opportunity, which generates the Renewal Quote at that time.

**Why not auto-quote:** Auto-generating renewal quotes immediately locks pricing at current list price. For enterprise accounts with negotiated renewals, this creates incorrect price anchors that must be manually corrected. The deferred pattern keeps the renewal pipeline visible without committing to a price prematurely.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Contract has fewer than ~200 subscription lines | Synchronous (Legacy) amendment via Amend button or `SBQQ.ContractManipulationAPI` (sync) | No async overhead; transaction completes immediately |
| Contract has 1,000+ subscription lines | Async Large-Scale amendment via `SBQQ.ContractManipulationAPI.amend()` with async context | Synchronous path will hit CPU time limits |
| Contract has 200–1,000 subscription lines | Test in sandbox with production data volume before choosing mode | Governor limit behavior is sensitive to trigger complexity |
| Mid-contract price change needed | Swap pattern: zero out existing line, add new line at new price | Existing subscription lines are locked to contracted price; direct edit is not supported |
| Bundle products on contract need amendment | Verify Preserve Bundle Structure enabled; disable Combine Subscription Quantities | Both settings active simultaneously silently destroys bundle parent-child relationships |
| Renewal pipeline needed but price not yet negotiated | Set RenewalForecast=true, RenewalQuoted=false | Creates Renewal Opportunity for forecasting without locking a price |
| Full renewal automation needed | Set both RenewalForecast=true and RenewalQuoted=true | Generates Opportunity and Quote automatically on contract activation |
| Billing schedules not generating after amendment | Ensure Contract Status is set to Activated AFTER async amendment job completes | Billing engine triggers on Status=Activated; premature activation generates incomplete schedules |
| Co-termination anchor needs to change | Reject the change; redesign the contract term structure instead | Post-sale edits to co-termination start date corrupt all proration calculations |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Establish subscription scale and service mode** — Count active `SBQQ__Subscription__c` records on the contracts in scope. Decide at this step whether the architecture will use Legacy synchronous or Large-Scale async mode. This decision affects field behavior, monitoring requirements, and billing integration sequencing.

2. **Audit CPQ Settings for conflicting configurations** — In Setup > Installed Packages > Salesforce CPQ > Configure, review: Preserve Bundle Structure, Combine Subscription Quantities, Co-Termination behavior, Default Renewal Term, and Auto Renew. If both Preserve Bundle Structure and Combine Subscription Quantities are enabled, resolve the conflict before proceeding with any bundle amendment design.

3. **Design amendment flow with ledger model in mind** — Document all downstream consumers of `SBQQ__Subscription__c` data (triggers, integrations, reports). For each consumer, verify it aggregates by contract+product grouping rather than reading a single record as current state. Update any consumer that treats a single subscription record as the source of truth.

4. **Design co-termination anchors as write-once** — Identify any Flows, Apex triggers, or processes that can write to `SBQQ__SubscriptionStartDate__c` or `SBQQ__CoTerminationDate__c` after contract activation. Remove or gate these. Document the co-termination anchor date in the contract template so it is set correctly at origination and never changed.

5. **Configure renewal automation** — Set `SBQQ__RenewalForecast__c` and `SBQQ__RenewalQuoted__c` on the Contract (or in CPQ Settings defaults) based on the renewal negotiation model. If contracted renewal pricing is required, ensure `SBQQ__ContractedPrice__c` records are created for the relevant account-product combinations before the renewal quote is generated.

6. **Sequence billing integration correctly** — If Salesforce Billing is installed, confirm the activation sequence: (a) CPQ processes quote → (b) subscriptions are fully written → (c) Contract Status set to Activated → (d) billing schedules generate. For async amendments, add a job completion check before activating the Contract.

7. **Validate with a sandbox amendment cycle** — Run a full amendment-to-billing cycle in sandbox: initiate amendment, confirm delta subscription records are created (not existing records modified), validate co-termination dates, verify billing schedules generate after activation. Run `check_subscription_arch.py` against the metadata to catch configuration anti-patterns.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Amendment service mode (Legacy vs Large-Scale) documented and validated against subscription line count
- [ ] All downstream consumers of `SBQQ__Subscription__c` verified to aggregate delta records, not read single records as current state
- [ ] Preserve Bundle Structure and Combine Subscription Quantities confirmed not both enabled simultaneously
- [ ] Co-termination start dates and subscription start dates confirmed write-once; no automation modifies them post-activation
- [ ] `SBQQ__RenewalForecast__c` and `SBQQ__RenewalQuoted__c` set consistently with renewal negotiation model
- [ ] If Salesforce Billing installed: Contract activation sequence confirmed to fire after CPQ subscription write completes
- [ ] For Large-Scale async amendments: `AsyncApexJob` monitoring in place before any billing or downstream system action

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Ledger model misunderstanding breaks reporting and integrations** — The most damaging misconception in CPQ subscription architecture is treating `SBQQ__Subscription__c` records as mutable state. After the first amendment, a product's "current" quantity and price are spread across multiple subscription records (original + delta). Any report, trigger, or integration that reads the most-recent subscription record as the current state will return incorrect data. The only correct pattern is to aggregate all subscription records for a given contract-product combination.

2. **Co-termination Start Date edits corrupt proration silently** — If `SBQQ__SubscriptionStartDate__c` or `SBQQ__CoTerminationDate__c` is edited on an active subscription or contract after activation, CPQ recalculates proration in subsequent amendments using the new date but does not reprocess the proration that was already applied. This produces a silent discrepancy: the billing system and the CPQ subscription ledger diverge. The discrepancy is only discovered during a billing reconciliation, often quarters after the fact.

3. **Preserve Bundle Structure + Combine Subscription Quantities silently break bundle amendments** — These two CPQ settings have no conflict warning in the UI. When both are enabled, CPQ processes Combine Subscription Quantities first, collapsing bundle child subscriptions into single records. Preserve Bundle Structure then has no effect because the bundle hierarchy has already been destroyed. Renewal quotes generated from these contracts will reprice bundle children independently rather than as part of a bundle, producing incorrect renewal pricing without any error message.

4. **Large-Scale async amendment uses different date fields than Legacy mode** — In Legacy mode, the amendment effective date is read from `SBQQ__SubscriptionStartDate__c` on the Quote. In Large-Scale mode, it is read from `SBQQ__AmendmentStartDate__c` on the Contract. If an architect designs date logic for one mode and the deployment switches modes later (e.g., contract volume grows past the threshold), all amendment dates will come from the wrong field and proration will be calculated incorrectly.

5. **Billing schedules generate against incomplete data if Contract is activated before async job completes** — In Large-Scale amendment mode, the amendment quote and subscription records are created asynchronously. If a downstream automation (Flow, Apex trigger) moves Contract Status to "Activated" immediately after calling the async amendment API, the billing engine may fire before subscriptions are fully written. The resulting `blng__BillingSchedule__c` records will be based on pre-amendment subscription data. This is not easily reversible.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Amendment architecture decision record | Documents chosen service mode (Legacy vs Large-Scale), scale threshold, and async monitoring approach |
| Subscription ledger aggregation pattern | Code or report definition that correctly aggregates SBQQ__Subscription__c delta records by contract+product |
| Swap pattern implementation | Amendment configuration or script for mid-contract price changes using zero-out + new-line pattern |
| Co-termination design document | Write-once field inventory and automation gate preventing post-activation start date edits |
| Renewal automation configuration | SBQQ__RenewalForecast__c and SBQQ__RenewalQuoted__c settings with rationale |
| Billing integration sequencing checklist | Ordered list of prerequisites for blng__BillingSchedule__c generation |

---

## Related Skills

- `contract-and-renewal-management` — Admin-level procedural guidance for executing amendment and renewal tasks within this architecture
- `cpq-pricing-rules` — Use when swap pattern requires Price Rules to enforce the new contracted price on replacement subscription lines
- `cpq-architecture-patterns` — Broader CPQ solution architecture decisions that scope the subscription management design
- `cpq-product-catalog-setup` — Use when bundle product configuration upstream is causing Preserve Bundle Structure conflicts
