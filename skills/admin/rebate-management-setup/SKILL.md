---
name: rebate-management-setup
description: "Rebate Management setup: rebate types, payout calculations, accruals, partner rebates, program setup, compliance reporting. NOT for CPQ discounts on quotes (use revenue-cloud-cpq-setup). NOT for channel loyalty programs (use partner-loyalty-programs)."
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
---

# Rebate Management Setup

Activate when configuring Salesforce Rebate Management for channel incentive programs: volume rebates, growth rebates, market-development funds (MDF), SPIFs, and partner co-op programs. Rebate Management is a distinct feature from CPQ discounting — it calculates after-the-fact incentives based on transactions, not at quote time.

## Before Starting

- **Confirm Rebate Management license.** It is a paid add-on; the object model (`Rebate_Program__c`, `Benefit__c`, `Rebate_Payout__c`, `Transaction__c`) only appears when provisioned.
- **Identify the source of transactions.** Rebates calculate against transactions — could be Orders, Invoices, a POS feed, or a data warehouse extract. This source drives the ingestion pipeline.
- **Know the finance control requirements.** Most rebate programs require accounting sign-off before payout. Approval routing and GL integration must be designed before program go-live.

## Core Concepts

### Program → Measure → Benefit → Payout

`Rebate_Program__c` is the top-level container (e.g., "2026 Channel Volume Rebate"). `Rebate_Measure__c` defines what is measured (units, revenue, growth %). `Benefit__c` defines what the participant earns at each threshold. `Rebate_Payout__c` is an actual payout instance after the period closes.

### Accrual accounting

Between the period start and close, Rebate Management posts **accruals** — estimates of the liability as transactions come in. On period close, accruals reconcile to actual payouts. Accrual frequency (daily, weekly, monthly) is a finance decision.

### Transaction ingestion

`Transaction__c` records are the fuel. They come from: CG Cloud orders, Revenue Cloud invoices, Data Cloud feeds, CSV loads, or custom integrations. Schema matters — amount, participant, product family, and date are mandatory for rebate calculation.

## Common Patterns

### Pattern: Volume-tier rebate with quarterly payout

`Rebate_Program__c` with `Benefit__c` records defining tier thresholds (1-1000 units → 2%, 1001-5000 → 3%, 5000+ → 5%). Transactions accumulate through the quarter. At period close, Rebate Calculation runs, Payouts are generated, Approval routes to finance, then GL posts.

### Pattern: Growth rebate vs prior period

Benefit tied to % growth vs the same participant's prior quarter. Requires reference data on prior period baseline. Flow or a scheduled Apex sets the baseline at period start.

### Pattern: MDF with manual claim approval

Participant submits an MDF claim (via portal LWC). Claim is a `Rebate_Payout__c` with a manual route rather than auto-calculation. Approval + receipt review before payout.

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
2. Map transaction source systems; build the `Transaction__c` ingestion job (daily recommended).
3. Design programs: volume, growth, MDF — one `Rebate_Program__c` per program for auditability.
4. Configure `Benefit__c` thresholds; validate with sample transactions through a scratch-org dry run.
5. Set accrual cadence and validate with finance; set up GL posting integration.
6. Build partner visibility: Experience Cloud page showing year-to-date accrued rebate, tier progress.
7. Run a full period-close dry run: accruals → calculation → approval → payout → GL post.

## Review Checklist

- [ ] Rebate Management license provisioned and objects visible
- [ ] Transaction ingestion validated end-to-end
- [ ] Program + Measure + Benefit structure matches contract
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

- `admin/revenue-cloud-cpq-setup` — quote-time discount sibling
- `admin/experience-cloud-site-setup` — partner portal host
- `integration/integration-pattern-selection` — transaction ingestion
