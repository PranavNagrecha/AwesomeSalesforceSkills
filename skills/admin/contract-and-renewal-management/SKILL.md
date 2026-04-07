---
name: contract-and-renewal-management
description: "Use when configuring or troubleshooting Salesforce CPQ contract creation, subscription management, amendment quotes, or renewal quotes. Trigger keywords: contract, amendment, renewal, subscription, co-termination, SBQQ__Subscription__c. NOT for standard Salesforce contracts without CPQ, nor for Revenue Cloud advanced order management."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Performance
triggers:
  - "how do I create a contract from a CPQ opportunity"
  - "amendment quote is not picking up updated list prices for existing subscription lines"
  - "renewal quote is not being generated automatically after contract activation"
  - "co-termination is extending lines beyond the expected end date"
  - "large-scale amendment is timing out or failing with more than 1000 subscription lines"
tags:
  - cpq
  - contracts
  - amendments
  - renewals
  - subscriptions
  - sbqq
inputs:
  - "CPQ package version installed in org"
  - "Opportunity with SBQQ__Quoted__c = true and at least one Quote Line with SBQQ__SubscriptionPricing__c set"
  - "CPQ Settings: Contract, Renewal, and Amendment preference values"
  - "Whether the org uses auto-renewal or agent-initiated renewal"
  - "Approximate number of subscription lines on contracts being amended"
outputs:
  - "Activated Contract with child SBQQ__Subscription__c records"
  - "Amendment Quote with preserved original subscription pricing on existing lines"
  - "Renewal Quote linked via SBQQ__RenewedContract__c with configurable term"
  - "Decision guidance on async vs synchronous amendment processing"
dependencies:
  - cpq-pricing-rules
  - cpq-product-catalog-setup
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# Contract and Renewal Management

This skill covers the full Salesforce CPQ contract lifecycle: creating contracts from won opportunities, managing subscription records, generating amendment quotes to modify active contracts, and generating renewal quotes when contracts approach expiration. It activates when a practitioner needs to configure, debug, or extend CPQ contract or renewal behavior.

---

## Before Starting

Gather this context before working on anything in this domain:

- Verify that the Salesforce CPQ package is installed and that at least one Quote Line on the originating Opportunity has `SBQQ__SubscriptionPricing__c` populated (Fixed Price or Percent Of Total). Without this field, the contract creation process will not generate `SBQQ__Subscription__c` child records.
- Confirm whether the org relies on automatic renewal (CPQ Setting: Auto Renew) or manually initiated renewal. This determines whether a Renewal Opportunity and Renewal Quote are created automatically on contract activation.
- The most common wrong assumption is that editing a product's list price after a contract is activated will update the prices on an amendment quote for existing subscription lines. It will not — existing lines are locked to the original contracted price.
- Relevant platform limits: synchronous amendment processing is reliable up to approximately 200 subscription lines. Above 1,000 lines, async processing via `SBQQ.ContractManipulationAPI` or the batch job framework is required. Between 200 and 1,000 lines, behavior depends on org governor limits and should be tested.

---

## Core Concepts

### Contract Creation Requirements

A CPQ contract is created by setting `SBQQ__Contracted__c = true` on an Opportunity that is in a Closed Won stage and has a primary CPQ Quote with at least one subscribed Quote Line. The system reads the primary Quote (`SBQQ__PrimaryQuote__c`) and creates child `SBQQ__Subscription__c` records under the resulting standard Contract object. Each subscription record captures the product, quantity, pricing, subscription start date, and subscription end date from the Quote Line.

If no Quote Lines have `SBQQ__SubscriptionPricing__c` set, no subscription records are created and the contract lifecycle features (amendment, renewal) will not function.

### Amendment Quotes and Subscription Line Locking

An amendment quote is created from an active contract and allows quantity changes, product additions, and product removals. The critical behavior: **existing subscription lines on an amendment quote carry the original contracted price**. Updated list prices in the price book are applied only to net-new lines added during the amendment. This is intentional — it protects customers from unexpected price increases mid-contract.

Co-termination is applied automatically during amendment: all subscription lines are forced to share the same end date as the earliest-ending subscription on the contract. Term precedence is: Quote Line level > Quote Group level > Quote header level.

Amendments also generate co-terming proration. If a line originally ran 12 months and the amendment starts at month 6, the amended quantity is prorated to the remaining 6 months.

### Renewal Quotes

A renewal quote is generated from an active contract, linked via the `SBQQ__RenewedContract__c` lookup on the resulting Opportunity. The term of the renewal quote defaults to `SBQQ__DefaultRenewalTerm__c` on the Contract. If this field is blank, CPQ falls back to the term defined in CPQ Settings.

Renewal quotes reprice all lines at **current** price book prices unless contracted prices exist for the account. This is the opposite behavior from amendments, where existing lines are locked.

### Large-Scale Amendment Processing

When a contract has more than approximately 1,000 subscription lines, synchronous amendment generation times out. CPQ provides an asynchronous path: instead of clicking the Amend button on the contract record, an administrator or developer calls the `SBQQ.ContractManipulationAPI.amend()` method, which queues a batch job. The resulting amendment quote is linked to the contract once the job completes. Monitoring is done via `AsyncApexJob` or via the CPQ amendment status field on the contract.

---

## Common Patterns

### Pattern: Standard Amendment from Active Contract

**When to use:** Changing quantity or adding/removing products on a contract with fewer than ~200 subscription lines.

**How it works:**
1. Navigate to the active Contract record.
2. Click the **Amend** button (CPQ quick action).
3. CPQ creates a draft Amendment Quote. Existing subscription lines appear locked (grayed out for price edits).
4. Add new products or adjust quantities. New products price from the current price book.
5. Calculate the quote. CPQ applies co-termination and proration.
6. Approve and activate the amendment quote. CPQ updates the existing Contract and `SBQQ__Subscription__c` records.

**Why not direct Contract edits:** Editing the Contract or Subscription records directly bypasses CPQ pricing logic, proration calculation, and the approval workflow. This results in mismatched subscription records and broken renewal quotes downstream.

### Pattern: Renewal Quote Generation

**When to use:** Contract is approaching expiration and the account intends to continue service.

**How it works:**
1. Confirm `SBQQ__DefaultRenewalTerm__c` is set on the Contract (months).
2. Click the **Renew** button on the active Contract (or enable Auto Renew in CPQ Settings to trigger this automatically on activation).
3. CPQ creates a Renewal Opportunity and a Renewal Quote, linked via `SBQQ__RenewedContract__c`.
4. All lines are repriced at current price book prices (not contracted prices unless a `SBQQ__ContractedPrice__c` record exists for the account/product).
5. Negotiate and approve the renewal quote as a standard CPQ quote.

**Why not clone the original quote:** Cloning does not set up the `SBQQ__RenewedContract__c` relationship, so the renewed contract lifecycle tracking breaks. Revenue reporting and contract history will be incorrect.

### Pattern: Async Large-Scale Amendment

**When to use:** Contract has 1,000+ subscription lines and synchronous Amend fails or times out.

**How it works:**
1. Use Apex or a scheduled job to call `SBQQ.ContractManipulationAPI.amend(contractId)`.
2. This queues an `AsyncApexJob`. The amendment quote is created asynchronously.
3. Monitor `AsyncApexJob` for the `SBQQ.AmendmentBatchJob` class.
4. Once complete, the amendment quote appears on the Contract's related list.
5. Proceed with standard amendment review and approval.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Fewer than ~200 subscription lines, simple quantity change | Synchronous Amend button | Sufficient for governor limits; no setup overhead |
| 1,000+ subscription lines | Async `SBQQ.ContractManipulationAPI.amend()` | Synchronous processing will hit CPU and SOQL limits |
| List price changed and amendment should reflect new price for existing lines | Do NOT attempt — this is not supported | Existing lines are locked to contracted price; only new lines get current pricing |
| Contract approaching end, auto-renewal enabled | Auto-Renew CPQ Setting | System creates Renewal Opportunity automatically on contract activation |
| Renewal with negotiated pricing different from list | Manual Renew + edit Renewal Quote | Auto-Renew prices at list; negotiate after quote generation |
| Customer wants to remove a product mid-contract | Amendment — set quantity to 0 or remove the line | Direct deletion of `SBQQ__Subscription__c` breaks renewal logic |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm CPQ contract prerequisites** — Verify `SBQQ__Contracted__c = true` is set (or will be set) on the Opportunity, and that the primary Quote has at least one line with `SBQQ__SubscriptionPricing__c` populated. Without this, no subscription records are created.
2. **Verify CPQ Settings for renewal and amendment** — Check Setup > Installed Packages > Salesforce CPQ > Configure > Subscriptions & Renewals tab. Confirm the Default Renewal Term, Co-Termination behavior, and Amendment Pricing settings match org requirements.
3. **Determine amendment scale** — Count active `SBQQ__Subscription__c` records on the contract. Under ~200: use the Amend button. Over 1,000: plan for the async API path. Between 200 and 1,000: test in a sandbox first.
4. **Execute the amendment or renewal** — Follow the appropriate pattern (Standard Amendment, Renewal Quote Generation, or Async Large-Scale Amendment from Core Concepts). Never directly edit Contract or Subscription records.
5. **Validate co-termination and proration** — After amendment quote generation, confirm all subscription end dates align to the co-termination date and that prorated amounts are mathematically correct (line quantity × daily rate × remaining days).
6. **Approve and activate** — Route the quote through the approval process. On activation, CPQ updates the Contract and Subscription records. Confirm the Contract Status moves to "Activated" and Subscription records reflect the change.
7. **Verify renewal setup** — After any contract update, confirm `SBQQ__RenewalQuoted__c` and `SBQQ__DefaultRenewalTerm__c` are accurate on the Contract so the next renewal cycle is set up correctly.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `SBQQ__Contracted__c = true` set on Opportunity AND at least one Quote Line has `SBQQ__SubscriptionPricing__c` populated
- [ ] CPQ Settings for Renewal Term, Co-Termination, and Amendment Pricing reviewed and confirmed
- [ ] Amendment quote does not show updated list prices on locked existing subscription lines (expected behavior — verify no custom workaround is breaking this)
- [ ] Co-termination end dates on all amendment lines are consistent and match the earliest subscription end date
- [ ] For large-scale amendments (1000+ lines), async processing is used and `AsyncApexJob` status is monitored
- [ ] Renewal Opportunity and Quote are linked via `SBQQ__RenewedContract__c` (not a cloned quote)
- [ ] `SBQQ__DefaultRenewalTerm__c` is set correctly on the Contract

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **List price changes do not flow into amendment quotes for existing lines** — Once a subscription is created from a contract, the subscription's price is locked. An amendment quote will show the original contracted price for existing lines, even if the price book entry was updated after contract activation. Only net-new lines added in the amendment get current pricing. Practitioners who update price books expecting renewal-price parity on amendments will be surprised.

2. **Co-termination can shorten line terms unexpectedly** — When a contract has lines with staggered start dates, co-termination forces all lines to end on the same date as the earliest-ending line. This means some lines may receive significantly shorter prorated terms than expected. The customer may perceive this as an incorrect charge. Always preview the co-termination date before activating an amendment on a contract with mixed-term lines.

3. **`SBQQ__RenewedContract__c` must be set for contract history tracking** — Manually cloning a quote and relabeling it a "renewal" skips the `SBQQ__RenewedContract__c` linkage. CPQ uses this lookup to chain contract history, calculate contracted price inheritance, and drive revenue recognition rollups. Skipping it silently breaks downstream contract reporting.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Activated Contract with SBQQ__Subscription__c records | Standard Contract record with child Subscription records representing each subscribed product line |
| Amendment Quote | Draft CPQ Quote with locked existing lines and editable new lines; co-termination applied automatically |
| Renewal Opportunity and Quote | Opportunity linked to the expiring Contract via SBQQ__RenewedContract__c; Quote repriced at current price book rates |
| Async Amendment Job Status | AsyncApexJob record for SBQQ.AmendmentBatchJob — monitor for large-scale amendment completion |

---

## Related Skills

- `cpq-pricing-rules` — Use when contracted prices, price rules, or discount schedules need to be configured to govern amendment and renewal pricing behavior
- `cpq-product-catalog-setup` — Use when subscription-type products are not generating subscriptions during contract creation (usually a product configuration issue upstream of contracts)
- `cpq-approval-workflows` — Use when amendment or renewal quotes need approval routing before activation
