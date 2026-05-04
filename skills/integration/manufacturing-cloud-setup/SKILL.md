---
name: manufacturing-cloud-setup
description: "Use this skill when configuring Salesforce Manufacturing Cloud — including Sales Agreement setup, Account-Based Forecasting (ABF) recalc jobs, run-rate management, Rebate Management programs, channel inventory tracking via Channel Revenue Management, and Group Membership / OrderItem-to-SalesAgreement reconciliation. Triggers on: Manufacturing Cloud setup, Sales Agreement Salesforce, account-based forecast recalculation, run rate manufacturing, rebate program setup, channel revenue management. NOT for general Sales Cloud opportunity-to-order flow (use standard Opportunity / Order), NOT for Field Service install-base management (use FSL skills), NOT for Automotive Cloud dealer modeling (use automotive-cloud-setup)."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
tags:
  - manufacturing-cloud
  - sales-agreement
  - account-based-forecasting
  - run-rate
  - rebate-management
  - channel-revenue-management
  - actual-orders
  - data-processing-engine
  - industry-cloud
  - planning
inputs:
  - "Manufacturing Cloud license enabled on the org"
  - "Sales Agreement structure: term, schedule frequency, planned quantity / revenue source"
  - "Order data feed (Order, OrderItem) for actuals capture"
  - "Rebate program design (volume tiers, payout cadence, eligible accounts)"
outputs:
  - "Sales Agreement records with planned quantity / revenue schedules"
  - "Activated Account-Based Forecasting recalc + Account Product Forecast records"
  - "Rebate program records with member assignments and DPE-driven payout"
  - "Channel Revenue Management sell-in / sell-through reconciliation"
triggers:
  - "configuring Salesforce Manufacturing Cloud Sales Agreements from scratch"
  - "Account-Based Forecasting recalculation never running or stale"
  - "Sales Agreement actuals not matching OrderItem data"
  - "rebate management program setup with volume tiers"
  - "channel revenue management sell-in vs sell-through"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-03
---

# Manufacturing Cloud Setup

This skill activates when a practitioner is configuring Manufacturing Cloud — the industry cloud that adds long-horizon Sales Agreements, account-based forecasting, run-rate planning, and rebate / channel-revenue management to Sales Cloud. It covers Sales Agreement structure, Account-Based Forecasting (ABF) recalc activation, run-rate vs. planned-quantity reconciliation, and Rebate / CRM module setup. It does NOT cover generic Sales Cloud opportunity-to-order flow, Field Service install-base, or Automotive Cloud dealer modeling.

---

## Before Starting

Gather this context before working in this domain:

- Confirm the org has the Manufacturing Cloud license — `SalesAgreement`, `SalesAgreementProduct`, `AccountProductForecast`, `RebateProgram`, and the Channel Revenue Management object family are gated behind that license.
- Identify whether actuals come from `Order` / `OrderItem` (the standard pattern) or from an external ERP feed (custom integration). The Sales Agreement actuals reconciliation strategy depends on this.
- Decide the Sales Agreement schedule frequency (Monthly / Quarterly / Yearly) and term length up front. Changing these after the agreement is activated is destructive.
- Map which DPE definitions need activation: ABF recalc, Sales Agreement actuals refresh, Rebate payout calculation. None of these run automatically.

---

## Core Concepts

### Sales Agreement: Long-Horizon Planned Demand

A `SalesAgreement` is a multi-period commitment between an account (a distributor, dealer, or wholesaler) and the manufacturer to purchase planned quantities of products over a fixed term — often 12–36 months. Unlike an Opportunity (point-in-time sale), a Sales Agreement breaks planned quantity / revenue into a schedule of periods (`SalesAgreementProductSchedule`).

Each `SalesAgreementProduct` represents one product within the agreement. Its planned quantity for each schedule period is the "planned" half of the planned-vs.-actual reporting.

The actual half comes from `Order` / `OrderItem` data: when an actual order is placed against the agreement, the `OrderItem.SalesAgreementId` lookup associates the actual with the agreement, and a recalc job aggregates the actuals into the corresponding schedule periods.

### Account-Based Forecasting (ABF)

ABF aggregates Sales Agreement schedules + open Opportunities + open Orders + actuals into a single per-account, per-product forecast: `AccountProductForecast`. Each forecast row holds planned quantity, planned revenue, actual quantity, and actual revenue per period.

The forecast is **recomputed by a DPE batch job**, not in real time. Without activating the recalc job, `AccountProductForecast` records grow stale and reports show last-recalc data — which leads to a common production bug: "the forecast doesn't match what I know is in the agreement."

### Run-Rate Management

Run-rate is the trailing-period average of actuals, used to detect when a customer is consuming below or above their committed schedule. Manufacturing Cloud computes run-rate as part of the ABF recalc and surfaces variance (planned − actual) on `AccountProductForecast`. Use this for early-warning alerts on under-consuming agreements.

### Rebate Management

`RebateProgram` defines the rebate structure: tiers (volume-based or revenue-based), payout cadence, eligible products, eligible accounts. `RebateProgramPayoutPeriod` defines a payout window. `ProgramRebatePayout` is the calculated payout per member-account per period.

Rebate payout calculation is **another DPE batch job** that must be activated. It pulls actuals from `Order` / `OrderItem`, applies tier logic, and writes `ProgramRebatePayout` rows.

### Channel Revenue Management (CRM module)

For OEMs that sell into a distribution channel (sell-in), then track ultimate consumer sales by the channel partner (sell-through), the Channel Revenue Management module provides:

- `ChannelProgram` / `ChannelProgramMember` for partner enrollment.
- `ChannelInventory` for partner stock levels.
- Integration with Rebate Management for sell-through-based rebates.

This is distinct from the base Sales Agreement / ABF flow — only configure if the OEM has a true two-step distribution model.

---

## Common Patterns

### Pattern 1: First-Time Sales Agreement Setup with ABF Activation

**When to use:** Net-new Manufacturing Cloud rollout.

**How it works:**

1. Define the Sales Agreement term and schedule frequency on the agreement record (e.g., 24 months, monthly schedule).
2. Add `SalesAgreementProduct` rows for each product in scope. Set planned quantity and planned revenue per period.
3. Activate the agreement (this creates the `SalesAgreementProductSchedule` rows).
4. In Setup → Data Processing Engine, locate the **Account-Based Forecasting recalculation** definition. Activate it and schedule it (typically nightly).
5. Run the recalc once manually after activation to backfill `AccountProductForecast`.
6. Wire `OrderItem.SalesAgreementId` population in your Order ingest path so actuals associate correctly.

**Why activate ABF explicitly:** ABF recalc is opt-in. Without activation, `AccountProductForecast` is empty and the executive dashboards show "no forecast data."

### Pattern 2: Actual-vs-Planned Reconciliation

**When to use:** "The Sales Agreement says we should be at 50K units this quarter but actuals show 30K — is the data wrong?"

**How it works:**

1. Verify the `OrderItem.SalesAgreementId` field is populated on the relevant orders. This is the linkage to the agreement.
2. Check the last successful run timestamp of the ABF recalc DPE job. If it's stale, the forecast data is stale by definition.
3. Confirm the schedule period alignment — Order date must fall within the schedule period for the actual to land in that period.
4. Re-run the recalc and re-check `AccountProductForecast`.

### Pattern 3: Rebate Program with Volume Tiers

**When to use:** OEM offers volume-based rebates to channel partners.

**How it works:**

1. Create a `RebateProgram` with payout cadence (typically quarterly).
2. Define rebate tiers: e.g., 0–10K units = 0%, 10K–50K units = 2%, 50K+ units = 4%.
3. Enroll member accounts via `RebateProgramMember`.
4. Activate the **Rebate Payout Calculation DPE definition** and schedule it to run after each payout period closes.
5. Verify `ProgramRebatePayout` rows are created with the correct tier applied.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Multi-period commitment to purchase | `SalesAgreement` + `SalesAgreementProduct` schedule | Purpose-built for multi-period planned demand; do not use Opportunity |
| Per-account forecast view spanning agreement + opps + orders | Activate ABF recalc DPE | `AccountProductForecast` is the only object that aggregates all four sources |
| Volume / revenue rebates to channel partners | `RebateProgram` + Rebate Payout DPE | Built-in tier engine; do not build custom rebate logic |
| OEM sells into distributors, distributors sell to consumers | Channel Revenue Management module | `ChannelInventory` + sell-through rebates require CRM module |
| One-shot point-in-time sale | Standard Opportunity / Order | Sales Agreement overhead not justified for single transactions |
| Forecast recalc cadence | Nightly DPE schedule for most orgs | Real-time recalc is not supported; near-real-time requires custom triggers (rare) |

---

## Recommended Workflow

1. Confirm Manufacturing Cloud license; verify standard objects appear in Object Manager.
2. Decide schedule frequency and term length per typical agreement before configuring (changes after activation are destructive).
3. Build the first Sales Agreement end-to-end (with `SalesAgreementProduct` rows and activation).
4. Activate the **Account-Based Forecasting recalculation** DPE definition; run once manually to backfill.
5. Wire `OrderItem.SalesAgreementId` population in the order ingest path.
6. For rebates: configure `RebateProgram` with tier structure, enroll members, activate the Rebate Payout DPE.
7. For channel-revenue-management: enable `ChannelProgram` only if the OEM has a true two-step distribution model.
8. Test end-to-end: agreement activation → order placement → ABF recalc → forecast accuracy → rebate payout.

---

## Review Checklist

- [ ] Sales Agreement schedule frequency / term decided before activation
- [ ] `SalesAgreementProductSchedule` rows present after activation (verifies activation succeeded)
- [ ] `OrderItem.SalesAgreementId` populated by Order ingest path
- [ ] ABF recalc DPE definition activated AND scheduled
- [ ] First ABF recalc run manually executed; `AccountProductForecast` populated
- [ ] Rebate Payout DPE definition activated (if rebates in scope)
- [ ] Channel Revenue Management module enabled ONLY if two-step distribution applies
- [ ] Run-rate variance dashboard built off `AccountProductForecast` (not custom rollup)

---

## Salesforce-Specific Gotchas

1. **ABF Recalc Is Not Automatic** — A net-new Manufacturing Cloud org has no DPE jobs running. `AccountProductForecast` will be empty until the Account-Based Forecasting recalc DPE definition is activated and scheduled. This is the single most common go-live failure mode.

2. **Schedule Frequency Cannot Be Changed Post-Activation Without Pain** — Changing a Sales Agreement from Monthly to Quarterly schedule after activation requires deactivating, deleting `SalesAgreementProductSchedule` rows, and reactivating. Plan the cadence carefully up front.

3. **`OrderItem.SalesAgreementId` Is Not Auto-Populated** — Even when an order is placed against an account that has an active Sales Agreement, the `SalesAgreementId` lookup is not automatically set. The Order ingest path (Apex, Flow, or external integration) must explicitly populate it, or actuals never reconcile to plan.

4. **Rebate Tier Boundaries Are Cumulative, Not Marginal** — Manufacturing Cloud's standard rebate calculation applies the highest qualifying tier to the entire volume, not marginal tiers. If a member buys 60K units in a 0–10K=0%, 10–50K=2%, 50K+=4% structure, they receive 4% on all 60K. Modeling marginal tiers requires custom logic.

5. **Channel Revenue Management Is Not Required for Simple Rebates** — Many practitioners enable CRM unnecessarily. Base Manufacturing Cloud Rebate Management handles direct-customer rebates fine. Only enable CRM when there's a true sell-in / sell-through distribution model with partner inventory tracking.

6. **`SalesAgreement` Permissions Are Granular** — End-user roles need specific permissions on `SalesAgreement`, `SalesAgreementProduct`, AND `SalesAgreementProductSchedule`. Granting only the parent does not cascade — the schedule rows stay invisible.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Sales Agreement design document | Schedule frequency, term, product mix, planned quantity source |
| ABF activation runbook | DPE definition activation steps, schedule cadence, manual-run verification |
| Rebate program blueprint | Tier structure, payout cadence, member enrollment, DPE activation |
| Order-to-agreement integration spec | OrderItem.SalesAgreementId population pattern in the ingest path |
| Forecast variance dashboard | Reports built off AccountProductForecast for run-rate alerts |

---

## Related Skills

- automotive-cloud-setup — for sibling industry-cloud setup patterns and shared Industries object behaviors (FinancialAccount, AccountAccountRelation)
- industries-cloud-selection — for the architect-level decision of whether Manufacturing Cloud is the right vertical fit
- loyalty-management-setup — for the related DPE-driven Industries pattern (DPE jobs are also opt-in there)
