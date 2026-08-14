---
name: rebate-management-setup
description: "Rebate Management setup: rebate types, payout calculations, accruals, partner rebates, program setup, compliance reporting. NOT for Sales Agreements or channel revenue management — use integration/manufacturing-cloud-setup. NOT for CPQ discounts on quotes — use admin/cpq-pricing-rules."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Security
tags:
  - rebate-management
  - channel-incentives
  - payouts
  - accruals
  - partner-rebates
  - revenue-cloud
  - compliance
triggers:
  - "how do i set up salesforce rebate management"
  - "partner rebate program volume tier configuration"
  - "rebate accrual and payout scheduling"
  - "rebate vs cpq discount which one to use"
  - "transactional rebate benefit calculation"
  - "channel rebate reporting and compliance"
inputs:
  - Rebate Management license and edition
  - Program structure (volume tier, growth, co-op, SPIF, MDF)
  - Data sources for benefit-calculating transactions (orders, invoices, POS feeds)
  - Payout cadence and finance controls (approval, GL posting)
outputs:
  - Rebate program + benefit calculation setup plan
  - Accrual and payout schedule configuration
  - Partner visibility (Experience Cloud page wiring)
  - Compliance and audit reporting scaffold
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
status: stub
---

# Rebate Management Setup

Activate when configuring Salesforce Rebate Management for channel incentive programs: volume rebates, growth rebates, market-development funds (MDF), SPIFs, and partner co-op programs. Rebate Management is a distinct feature from CPQ discounting — it calculates after-the-fact incentives based on transactions, not at quote time.

## Before Starting

- **Confirm Rebate Management license and edition.** It is a paid add-on: "Rebate Management is available in Lightning Experience. Available in: Enterprise, Unlimited, and Developer Editions." The object model ships as **standard** objects (`RebateProgram`, `ProgramRebateType`, `TransactionJournal`, …) that appear only when the feature is provisioned — none of them are custom objects and none carry a `__c` suffix.
- **Identify the source of transactions.** Rebates calculate against `TransactionJournal` records — sourced from Orders, Invoices, a POS feed, or a data warehouse extract. This source drives the ingestion pipeline.
- **Know the finance control requirements.** Most rebate programs require accounting sign-off before payout. Approval routing and GL integration must be designed before program go-live.

## Core Concepts

### Program → Rebate Type → Benefit → Payout

`RebateProgram` (API 51.0+) is the top-level container — "The rebate program your organization runs with a single account, all accounts, or specific list of accounts." `ProgramRebateType` is what is measured: "Provide the rebate types that are part of this program. For example, volume rebate, revenue rebate, or rebate on every transaction." `ProgramRebateTypeBenefit` "Defines the benefit matrix for the rebate type. For example, 5% or $200." `RebateProgramMemberPayout` is "The payout calculated for a member for the period," and `RebateProgramPayoutPeriod` is "The period of the payout calculation."

Eligibility and scope hang off the rebate type: `ProgramRebateTypEligibility` (note the truncated API name) holds "the rules and criteria to determine rebate type eligibility and terms for calculating payouts," `ProgramRebateTypeFilter` is "The definition that filters the transaction journals eligible for a rebate type," and `ProgramRebateTypeProduct` is "a junction between a program rebate type and a product."

### Accrual accounting

Between the period start and close, Rebate Management posts **accruals** — estimates of the liability as transactions come in. On period close, accruals reconcile to actual payouts. Accrual frequency (daily, weekly, monthly) is a finance decision.

### Transaction ingestion

`TransactionJournal` records are the fuel — "The transactions that need to be processed for a rebate program." They come from CG Cloud orders, Revenue Cloud invoices, Data Cloud feeds, CSV loads (`ReceivedDocument` "Allows partners to upload .CSV document"), or custom integrations. Schema matters — amount, participant, product, and date are what the calculation aggregates. Results land in `RebateMemberProductAggregate`, which "Stores the post calculation summary of journal transactions by member, period, and rebate type," with `RebateMemberAggregateItem` as the junction back to each contributing `TransactionJournal`.

## Common Patterns

### Pattern: Volume-tier rebate with quarterly payout

`RebateProgram` with a volume `ProgramRebateType`, and `ProgramRebateTypeBenefit` rows defining tier thresholds (1–1000 units → 2%, 1001–5000 → 3%, 5000+ → 5%). `TransactionJournal` records accumulate through the quarter. At period close, calculation runs against the `RebateProgramPayoutPeriod`, `RebateProgramMemberPayout` rows are generated, approval routes to finance, then GL posts via `RebatePayment`, which "Tracks if the payment has been generated for this member for back end processing."

### Pattern: Growth rebate vs prior period

Benefit tied to % growth vs the same participant's prior quarter. Requires reference data on prior period baseline. Flow or a scheduled Apex sets the baseline at period start.

### Pattern: MDF with manual claim approval

Participant submits an MDF claim (via portal LWC). The manual, off-calculation amount is a `RebatePayoutAdjustment` — "Rebate amount adjustment that needs to be given manually" — rather than a calculated `RebateProgramMemberPayout`. Approval + receipt review before payout. (`RebateClaim` and `RebateClaimAdjustment` are the ship-and-debit claim objects, a different program shape.)

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Quote-time discount | CPQ discount schedules | Applied before deal signs |
| After-sale volume rebate | Rebate Management | Calculates against delivered transactions |
| MDF / co-op claims | Rebate Management with manual payout | Shipped claim workflow |
| Loyalty point rewards | Loyalty Management | Distinct product |
| Simple referral SPIF | Rebate Management flat benefit | Overkill for ad-hoc, use Rebate anyway for audit |

## Recommended Workflow

1. Provision the license; confirm Rebate Management objects are visible in Object Manager.
2. Map transaction source systems; build the `TransactionJournal` ingestion job (daily recommended).
3. Design programs: volume, growth, MDF — one `RebateProgram` per program for auditability, with a `ProgramRebateType` per measure.
4. Configure `ProgramRebateTypeBenefit` thresholds and `ProgramRebateTypEligibility` criteria; validate with sample journals through a scratch-org dry run.
5. Set accrual cadence and validate with finance; set up GL posting integration.
6. Build partner visibility: Experience Cloud page showing year-to-date accrued rebate, tier progress.
7. Run a full period-close dry run: accruals → calculation → approval → payout → GL post.

## Review Checklist

- [ ] Rebate Management license provisioned and objects visible
- [ ] Transaction ingestion validated end-to-end
- [ ] `RebateProgram` → `ProgramRebateType` → `ProgramRebateTypeBenefit` structure matches contract
- [ ] Accrual cadence signed off by finance
- [ ] Approval routing in place before first payout
- [ ] Partner portal shows accurate year-to-date figures
- [ ] Audit report: traceable from payout back to source transactions

## Salesforce-Specific Gotchas

1. **Rebate recalculation is not retroactive unless forced.** Fixing a Benefit threshold after accruals have posted requires a manual recalc job; partners may see shifting balances.
2. **Transaction date drives period assignment.** Out-of-order backfills can hit closed periods — either reopen for recalc or post as a next-period adjustment.
3. **Experience Cloud rebate widgets depend on the Benefit Accrual snapshot.** If the snapshot job fails, partner portals show stale numbers with no obvious error.

## Output Artifacts

| Artifact | Description |
|---|---|
| Rebate program catalog | Active programs, benefit structures, participants |
| Transaction ingestion spec | Source, schema, schedule, error handling |
| Accrual and payout runbook | Period open/close procedure |
| Partner visibility page | LWC / Experience Cloud layout showing YTD rebate |

## Related Skills

- `admin/cpq-pricing-rules` — quote-time discount sibling
- `admin/experience-cloud-site-setup` — partner portal host
- `admin/integration-pattern-selection` — transaction ingestion
