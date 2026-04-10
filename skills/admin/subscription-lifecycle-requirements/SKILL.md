---
name: subscription-lifecycle-requirements
description: "Use when documenting, reviewing, or gathering requirements for Salesforce CPQ subscription lifecycle behavior: how amendments, renewals, upgrades, downgrades, and cancellations must work for a specific business. Trigger keywords: subscription requirements, amendment requirements, renewal requirements, proration requirements, co-termination, subscription ledger, upgrade downgrade policy. NOT for CPQ setup or configuration, not for Apex amendment API implementation, and not for Revenue Cloud advanced order management."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Scalability
triggers:
  - "what are the business rules we need to capture before configuring CPQ amendments and renewals"
  - "the customer wants to upgrade a subscription mid-term but I am not sure how CPQ will handle the pricing"
  - "we need to document what happens to existing subscription lines when a contract is amended"
  - "our renewals team needs a requirements checklist for how subscriptions behave at term end"
  - "product owner is asking how proration is calculated when a customer adds a product mid-contract"
tags:
  - cpq
  - subscriptions
  - amendments
  - renewals
  - proration
  - co-termination
  - sbqq
  - requirements
inputs:
  - "Business description of how customers buy, change, and renew subscriptions (upgrade/downgrade policies, cancellation rules)"
  - "Whether the org uses co-termination (all lines end on the same date) or allows staggered subscription end dates"
  - "Renewal model: auto-renew, manual renew, or hybrid"
  - "Amendment pricing expectation: are existing subscription lines expected to reprice when list prices change?"
  - "Proration method preference: daily proration, monthly proration, or no proration"
outputs:
  - "Documented subscription lifecycle requirements aligned to CPQ platform behavior"
  - "Decision table mapping business scenarios to CPQ amendment and renewal capabilities"
  - "Gap list identifying business requirements that require custom Apex or workarounds"
  - "Review checklist for validating requirements completeness before CPQ configuration begins"
dependencies:
  - contract-and-renewal-management
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# Subscription Lifecycle Requirements

This skill activates when a practitioner needs to gather, document, or review business requirements for Salesforce CPQ subscription lifecycle behavior — specifically how the platform handles amendments (mid-term changes), renewals, upgrades, downgrades, cancellations, and proration. It surfaces the platform's non-negotiable constraints so requirements can be written to match what CPQ actually does rather than what stakeholders assume.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm that the org is using Salesforce CPQ (the SBQQ managed package). The subscription lifecycle model described here is specific to CPQ — standard Salesforce Contracts and Opportunities do not have equivalent behavior.
- The most common wrong assumption: stakeholders often assume that amending a contract edits the existing subscription records. CPQ never modifies existing `SBQQ__Subscription__c` records. Amendments create new additive delta records (the ledger model). Requirements that describe "updating" or "editing" an active subscription are not implementable as written.
- Relevant platform constraints: co-termination end dates on existing contracts are immutable once the contract is activated. Requirements that ask to change the end date of an active subscription line without an amendment are not achievable in standard CPQ.
- Amendment pricing for existing subscription lines is locked to the original contracted price. Requirements that expect list-price changes to flow into existing lines on an amendment quote will require a custom zero-out swap workaround or a custom pricing override.

---

## Core Concepts

### The CPQ Subscription Ledger Model

Salesforce CPQ uses an additive ledger model for subscription changes, not an in-place edit model. When a customer amends a contract — to add quantity, remove a product, or upgrade a product — CPQ creates new `SBQQ__Subscription__c` records representing the delta change. The original subscription records are never modified. The full picture of a customer's entitlement is reconstructed by reading all subscription records across all amendments for a contract, not by looking at the latest version of a single record.

This model has direct requirements implications:

- Reports that show "current subscriptions" must account for all delta records and sum quantities correctly.
- Integrations that consume subscription data must read the full ledger, not just the most recently created records.
- Any business rule that assumes a subscription record represents a single point-in-time snapshot is incorrect.

The `SBQQ__Contract__c` lookup on each `SBQQ__Subscription__c` record links the delta back to the master contract. The `SBQQ__AmendedSubscription__c` lookup (on amendment-derived subscriptions) points back to the original subscription being modified.

### Proration Calculation

CPQ calculates proration for mid-term amendments using the formula:

**Prorated amount = (Effective Term / Product Term) × Unit Price**

Where:
- **Effective Term** is the number of months (or days, depending on the proration method) the line will be active under the amendment, from the amendment effective date to the co-termination end date.
- **Product Term** is the original subscription term in the same unit (months or days).
- **Unit Price** is the contracted unit price (not the current list price).

If a 12-month subscription at $1,200/year is amended at month 6, the prorated amount for the remaining 6 months is (6/12) × $1,200 = $600. Requirements must specify the proration method (monthly vs. daily) because the two produce different decimal values and the business must agree which is correct for billing.

Proration does not apply to one-time or usage products. Only subscription products (where `SBQQ__SubscriptionType__c` is set to "Renewable" or "Evergreen") are subject to proration.

### Amendment Pricing Lock for Existing Lines

When CPQ generates an amendment quote from an active contract, existing subscription lines on the amendment quote carry the original contracted price. The price is locked — it comes from the `SBQQ__Subscription__c.SBQQ__RegularPrice__c` (or the relevant pricing field), not from the current price book entry. This is the platform's intended behavior: existing contractual commitments are honored even if the product's list price has changed since the contract was signed.

If a business requirement states that a mid-term price increase must apply to existing subscribers, CPQ cannot fulfill this in standard configuration. The only supported workaround is the "zero-out swap": remove the existing subscription line at $0 on the amendment quote, then add a new line at the new price. This generates two delta subscription records — a $0 cancellation record and a new record at the new price. The workaround requires custom Apex or a custom button to automate, and the resulting subscription ledger is more complex to report on.

### Co-Termination Behavior

CPQ applies co-termination by default during amendment: all subscription lines on the contract are forced to share the same end date, which is the earliest end date among all active subscription lines. This means that if a contract has products with staggered start dates (purchased in different months), adding a new product mid-term will prorate it to end on the co-termination date, not on its own natural 12-month anniversary.

Co-termination can be disabled at the CPQ package level (Settings > Subscriptions tab > Disable Co-Termination). When disabled, each line retains its own end date and new lines receive a full term from the amendment effective date. Most B2B SaaS businesses prefer co-termination on for billing simplicity; services businesses with project-based subscriptions often need it off.

End dates on existing subscription records are immutable after contract activation, even when co-termination is disabled. A requirement to "extend the end date" of an existing active contract must be implemented as an amendment that adds a new renewal line, not as a direct edit.

### Renewal Process

CPQ generates a renewal quote from an activated contract. The renewal quote reprices all lines at the **current** price book rates — the opposite of amendment behavior, where existing lines are locked. If the business requires renewal at contracted prices, a `SBQQ__ContractedPrice__c` record must be created for each account/product combination to override the renewal pricing.

Auto-renewal is configured via CPQ Settings (Subscriptions & Renewals tab: "Auto Renew" setting). When enabled, CPQ creates a Renewal Opportunity and Renewal Quote automatically when the contract is activated. When disabled, renewals are initiated manually by clicking the Renew button on the contract. The `SBQQ__RenewedContract__c` lookup on the Renewal Opportunity links the renewal back to the original contract. This link is required for contract history chaining and must not be bypassed by cloning quotes.

### Upgrade and Downgrade Patterns

An upgrade (adding quantity, moving to a higher-tier product) is handled as an amendment: the delta quantity creates a new additive subscription record prorated to the co-termination date. CPQ does not have a native "replace product" action — a product swap requires removing the old line (setting quantity to 0 or deleting the line on the amendment quote, which generates a $0 delta record) and adding the new product as a net-new line.

A downgrade (reducing quantity) follows the same amendment path. CPQ generates a negative delta subscription record representing the reduction. If the business requires a credit for the unused portion, this is typically handled in the billing system by reading the negative delta record, not by CPQ itself.

Cancellation of a single product mid-term is a product removal on an amendment. Full contract cancellation is handled outside CPQ (Contract Status field on the Contract object), and the business must define what happens to in-flight subscription records upon cancellation — CPQ does not automatically zero out subscription records when a contract is cancelled.

---

## Common Patterns

### Pattern: Requirements Gathering for Mid-Term Amendment Policy

**When to use:** A new CPQ implementation or an existing implementation being extended must define the business rules for mid-term subscription changes.

**How it works:**
1. Document each amendment scenario the business needs (add quantity, remove product, upgrade product, downgrade quantity, price change, full cancellation).
2. For each scenario, explicitly map it to a CPQ-native capability or flag it as requiring a custom workaround.
3. Capture the proration method (monthly/daily) and verify the billing system can consume the prorated amounts CPQ generates.
4. Capture the co-termination preference and document the impact on line end dates with examples using real product terms.
5. Document whether amendment pricing lock is acceptable or whether a zero-out swap workaround is required.

**Why not start directly in CPQ configuration:** Configuring CPQ without documented requirements for proration and pricing lock leads to mid-project rework when the business discovers that existing lines cannot be repriced without a workaround.

### Pattern: Renewal Requirements Documentation

**When to use:** Defining business rules for contract renewal, including pricing behavior at renewal, auto-renewal vs. manual renewal, and how contracted prices are preserved.

**How it works:**
1. Confirm whether renewals should reprice at list or at contracted rates. If contracted rates, plan for `SBQQ__ContractedPrice__c` records.
2. Document the renewal term: is it always 12 months, or does it match the original contract term?
3. Define the lead time: how many days before expiration should a renewal quote be generated and sent to the customer?
4. Determine the auto-renew vs. manual-renew requirement per customer segment or contract type.
5. Document what happens if a renewal quote is not activated before the contract end date — does the subscription lapse, roll month-to-month, or continue on the previous contract?

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Business wants existing lines to reprice when list price changes mid-contract | Document as a custom workaround requirement (zero-out swap); not standard CPQ | Amendment pricing lock is a platform constraint — existing lines cannot reprice without removing and re-adding them |
| Business wants all subscription lines to end on the same date | Enable co-termination in CPQ Settings | CPQ natively aligns all lines to the earliest end date during amendment |
| Business wants each product to have its own renewal date | Disable co-termination in CPQ Settings and document per-line end date reporting requirements | Each line retains its own end date; reporting complexity increases |
| Business wants renewal at the same price as original contract | Create SBQQ__ContractedPrice__c records per account/product | Renewal reprices at list by default; contracted prices override this |
| Business wants to extend an active contract end date | Document as an amendment (add renewal line) not a direct edit | End dates on existing subscription records are immutable |
| Business needs to cancel a single product mid-term | Document as a product removal amendment | CPQ creates a $0 delta record; billing system must process the credit |
| Business requires credit memo for cancellation | Flag as billing system integration requirement, not CPQ native | CPQ does not generate credit memos; it creates negative delta subscription records |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner gathering and documenting subscription lifecycle requirements:

1. **Inventory all subscription change scenarios** — Work with the business to list every way a customer's subscription can change during its term: add quantity, remove quantity, add product, remove product, upgrade tier, downgrade tier, price adjustment, full cancellation. Confirm whether each scenario must happen mid-term or only at renewal.
2. **Map each scenario to CPQ behavior** — For each scenario, document whether it is natively supported (amendment via ledger model), requires a workaround (zero-out swap for price changes), or is out of scope for CPQ (e.g., credit memo generation). Flag scenarios that conflict with platform constraints.
3. **Document proration requirements** — Confirm the proration method (monthly or daily), which products are subject to proration (subscription products only, not one-time or usage), and whether the billing system can consume the prorated amounts CPQ calculates.
4. **Define co-termination policy** — Confirm whether co-termination should be enabled or disabled. Document examples using real contract timelines showing how staggered start dates affect line end dates and prorated charges.
5. **Document renewal pricing rules** — Specify whether renewal should reprice at current list or at contracted rates. If contracted rates, document which products require `SBQQ__ContractedPrice__c` records and how they are maintained when list prices change.
6. **Validate requirements against CPQ constraints** — Review the final requirements against the platform constraints in this skill (amendment pricing lock, immutable end dates, ledger model). Revise requirements that are not achievable in standard CPQ to either accept the platform behavior or explicitly scope a custom development workaround.
7. **Produce the requirements artifact** — Use the template in `templates/subscription-lifecycle-requirements-template.md` to produce a structured requirements document. Include a gap list of scenarios requiring custom development and a decision table for the main CPQ configuration choices.

---

## Review Checklist

Run through these before marking requirements documentation complete:

- [ ] Every amendment scenario (add, remove, upgrade, downgrade, cancel, price change) is documented and mapped to CPQ-native behavior or flagged as a workaround
- [ ] Proration method (monthly vs. daily) is explicitly decided and documented with a worked example
- [ ] Co-termination behavior is explicitly decided (enabled or disabled) with an example showing how staggered lines are affected
- [ ] Amendment pricing lock is acknowledged — requirements do not assume existing lines will reprice on an amendment quote without a zero-out swap workaround
- [ ] Subscription ledger model is understood — requirements do not assume `SBQQ__Subscription__c` records are edited in place
- [ ] Renewal pricing rules are documented (list price reprice vs. contracted price), with a plan for `SBQQ__ContractedPrice__c` if contracted pricing is required
- [ ] Cancellation and credit requirements are explicitly scoped (CPQ creates delta records; credit memos require billing system integration)
- [ ] End date mutability constraint is acknowledged — extending an active subscription requires an amendment, not a direct edit

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Amendments never modify existing SBQQ__Subscription__c records** — The ledger model means every change creates a new delta subscription record. Integrations, reports, and business rules written to read the "current" subscription record will be wrong if they only read the most recently created record. Total entitlement must be summed across all subscription records for the contract.

2. **End dates on existing contract subscription records are immutable** — Once a contract is activated, the end date on each `SBQQ__Subscription__c` record cannot be changed directly. Co-termination can force new amendment lines to align to an existing end date, but it cannot retroactively change the end date of an already-existing subscription record. Requirements asking to "extend" or "shorten" an existing subscription must be implemented as an amendment.

3. **Amendment pricing is locked to contracted price, not current list price** — Existing lines on an amendment quote will never reflect a list price update made after the original contract was signed. This surprises stakeholders who update a price book entry and expect the change to propagate to open contracts. Only net-new lines added in an amendment are priced from the current price book.

4. **Co-termination can create unexpectedly short prorated terms for new lines** — If the contract's co-termination date is 2 months away and a new product is added in an amendment, CPQ will prorate that product to 2 months, not 12. The customer is billed for 2 months. If the co-termination date is not communicated to the customer before the amendment, the prorated charge will be a surprise.

5. **Renewal quotes reprice at list — the opposite of amendments** — The pricing behavior at renewal is the inverse of amendment behavior: renewals use current list prices, amendments lock to contracted prices. A business that expects renewal at contracted rates must implement `SBQQ__ContractedPrice__c` records for the account. Failing to do this means all renewals will reprice at list, often causing billing disputes.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Subscription Lifecycle Requirements Document | Structured document listing all subscription change scenarios, their CPQ mapping, and gap items requiring custom development |
| Proration Decision Record | Agreed proration method (monthly/daily), worked examples, and billing system consumption approach |
| Co-Termination Policy Decision | Enabled/disabled decision with timeline examples showing line end date impact |
| Renewal Pricing Policy | List reprice vs. contracted price decision, with a plan for ContractedPrice__c record maintenance |
| CPQ Configuration Gap List | Explicit list of business requirements that cannot be met by standard CPQ and require Apex customization or workarounds |

---

## Related Skills

- `contract-and-renewal-management` — Use for the hands-on CPQ configuration and troubleshooting of contracts, amendments, and renewals after requirements are finalized
- `cpq-pricing-rules` — Use when discount schedules, block pricing, or contracted price records need to be configured to match the pricing requirements documented in this skill
- `subscription-management-architecture` — Use when designing the overall architecture of a multi-contract subscription model, including how renewal chains, ledger reads, and billing integrations are structured
