---
name: billing-schedule-setup
description: "Use this skill to configure Salesforce Billing billing schedules, invoice plans, billing policies, and billing treatments on activated Orders. Triggers: 'billing schedule not generating invoices', 'blng__BillingSchedule__c records missing after order activation', 'how to set up in-advance vs in-arrears billing', 'configure milestone billing in Salesforce Billing', 'invoice run not picking up order products', 'evergreen billing setup', 'billing treatment configuration'. NOT for CPQ quoting, not for standard revenue schedules (OpportunityLineItem revenue schedule splits), not for Salesforce Revenue Cloud (Revenue Lifecycle Management), not for native Salesforce subscription billing without the Salesforce Billing managed package."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Operational Excellence
triggers:
  - "billing schedule not created after activating the order in Salesforce Billing"
  - "invoice run batch job is not picking up order products or generates empty invoices"
  - "how do I configure in-advance versus in-arrears billing schedules for subscription products"
  - "milestone billing invoice requires manual trigger not firing automatically"
  - "blng__BillingSchedule__c records are missing or show wrong amounts on OrderProduct"
  - "how to set up Legal Entity, Billing Policy, and Billing Treatment in the right sequence"
  - "evergreen billing schedule keeps stopping instead of rolling forward each period"
tags:
  - billing-schedule-setup
  - salesforce-billing
  - blng-namespace
  - invoice-run
  - billing-policy
  - billing-treatment
  - in-advance
  - in-arrears
  - milestone-billing
  - evergreen-billing
inputs:
  - "Salesforce org with Salesforce Billing managed package (blng__ namespace) installed on top of Salesforce CPQ"
  - "Activated or draft Order with OrderProducts sourced from a CPQ Quote"
  - "Product2 records with blng__BillingRule__c and blng__RevenueRecognitionRule__c lookups populated"
  - "Confirmed whether Data Pipelines is enabled in the org (hard dependency)"
  - "Billing schedule type requirement: In-Advance, In-Arrears, Evergreen, Milestone, or Dynamic Invoice Plan"
  - "Legal Entity name and Tax Policy to associate with Billing Policy"
outputs:
  - "Configured Legal Entity, Billing Policy, Billing Treatment, and Tax Policy records in the correct dependency order"
  - "blng__BillingSchedule__c records auto-generated per OrderProduct upon Order activation"
  - "Invoice Run configuration that batches billing schedule items into blng__Invoice__c records"
  - "Guidance on schedule type selection with documented tradeoffs"
  - "Checklist confirming Data Pipelines dependency, governor limit awareness, and batch size alignment"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# Billing Schedule Setup

This skill activates when a practitioner needs to configure Salesforce Billing (blng__ namespace) billing schedules, invoice plans, billing policies, or billing treatments — from initial Legal Entity setup through Invoice Run execution. It covers In-Advance, In-Arrears, Evergreen, Milestone, and Dynamic Invoice Plan schedule types.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the Salesforce Billing managed package (namespace prefix `blng__`) is installed. Salesforce Billing is a separate managed package layered on top of Salesforce CPQ — it is not part of core Salesforce or CPQ alone.
- Confirm **Data Pipelines is enabled** in the org (Setup > Data Pipelines). This is a hard platform dependency: without it, the Billing package cannot create billing schedule records even if all configuration is correct.
- Identify the required schedule type (In-Advance, In-Arrears, Evergreen, Milestone, or Dynamic Invoice Plan) — this determines configuration path and invoice run behavior.
- Confirm the OrderProducts are CPQ-sourced (via Quote > Order flow), not manually created — manually created Orders bypass CPQ fields required by Billing.
- Know the billing period (Monthly, Quarterly, Annually, Custom) and billing day-of-month required by the business.

---

## Core Concepts

### Billing Lifecycle: Order Activation Creates blng__BillingSchedule__c

The Salesforce Billing lifecycle begins when an Order is activated. At activation, the Billing package creates one `blng__BillingSchedule__c` record per OrderProduct that has a valid Billing Rule reference. Each `blng__BillingSchedule__c` holds the projected charge dates and amounts for that product's billing period. These records are auto-generated — do not create them manually.

The configuration chain that must be in place before Order activation:

```
Legal Entity → Billing Policy → Billing Treatment → Tax Policy → (Invoice Plan if Dynamic)
```

Each link in this chain is a lookup on the previous object. Missing any one link prevents billing schedule generation or invoice creation.

### Schedule Types and Their Behavior

Salesforce Billing supports five schedule types, each controlled by the `blng__BillingType__c` field on `blng__BillingRule__c`:

| Type | Invoice Timing | Manual Trigger Required | Notes |
|---|---|---|---|
| In-Advance | Invoice issued before service period | No | Default for most subscription SaaS |
| In-Arrears | Invoice issued after service period ends | No | Calculates from actual usage period end date |
| Evergreen | Rolls forward each period indefinitely | No | No end date; must explicitly cancel |
| Milestone | Invoice issued at milestone completion | Yes | Admin or Apex must trigger invoice run per milestone |
| Dynamic Invoice Plan | Custom date-driven schedule | No | Requires separate Invoice Plan record |

The most commonly misconfigured: **Milestone billing** — practitioners expect it to fire automatically but it requires a manual Invoice Run scoped to the milestone date.

### Invoice Run: Batch Processing and Governor Limits

Invoice Runs (`blng__InvoiceRun__c`) are the mechanism that aggregates `blng__BillingSchedule__c` items into `blng__Invoice__c` records. Invoice Runs execute as batch jobs, processing approximately **300 billing schedule lines per batch chunk** to stay within Salesforce governor limits. For orgs with thousands of order products, this means a single Invoice Run may spawn many batch iterations.

Key Invoice Run fields:
- `blng__InvoiceDate__c` — the date that appears on the invoice header
- `blng__TargetDate__c` — the cutoff date; only schedule items on or before this date are processed
- `blng__Status__c` — Posted, Canceled, Draft; only Draft runs can be modified

### blng__BillingSchedule__c vs blng__RevenueSchedule__c vs OpportunityLineItem Revenue Schedules

These are three entirely different constructs:

- `blng__BillingSchedule__c` — Salesforce Billing managed package object; one per OrderProduct; controls invoice generation
- `blng__RevenueSchedule__c` — Salesforce Billing managed package object; controls revenue recognition timing (separate from billing timing)
- OpportunityLineItem Revenue Schedule — standard Salesforce feature for splitting opportunity revenue; has no integration with the Billing package

Do not conflate these. Enabling "Revenue Schedules" in standard Salesforce Setup is unrelated to and does not replace `blng__RevenueSchedule__c`.

---

## Common Patterns

### Pattern 1: Standard Subscription Billing (In-Advance, Monthly)

**When to use:** A subscription product should invoice at the start of each monthly period.

**How it works:**
1. Create a `blng__BillingRule__c` with `blng__BillingType__c = In-Advance`, `blng__BillingDayOfMonth__c = 1` (or contract start day), `blng__InitialBillingDate__c` logic set to Order Start Date.
2. Create a `blng__RevenueRecognitionRule__c` if revenue recognition is required.
3. On the Product2 record, set the `blng__BillingRule__c` lookup to the new rule.
4. Ensure a Billing Policy exists with a Legal Entity and Tax Policy attached.
5. Ensure the Billing Policy is set on the Account record (`blng__BillingPolicy__c` lookup on Account).
6. Activate the Order — `blng__BillingSchedule__c` records are created automatically.
7. Run an Invoice Run with `blng__TargetDate__c` set to today or the desired billing date.

**Why not the alternative:** Manually creating `blng__BillingSchedule__c` records bypasses Billing Rule logic and produces orphaned records that Invoice Runs cannot reliably pick up.

### Pattern 2: Milestone Billing for Professional Services

**When to use:** A services engagement invoices at project milestone completion (e.g., 30% at kickoff, 40% at delivery, 30% at acceptance).

**How it works:**
1. Set `blng__BillingType__c = Milestone` on the `blng__BillingRule__c`.
2. Define milestone amounts on the `blng__BillingSchedule__c` child records (created at Order activation).
3. When a milestone is achieved, update the milestone record's status to indicate completion.
4. Manually trigger an Invoice Run scoped to the milestone date — the run will only process lines where the milestone status is complete and the date is on or before `blng__TargetDate__c`.

**Why not the alternative:** Using In-Advance for milestone billing creates invoices on fixed calendar dates regardless of project status, violating contract terms and creating disputes.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| SaaS subscription, invoice before each period | In-Advance billing schedule | Matches standard subscription contract terms; invoices auto-generate |
| Usage-based billing, invoice after metering | In-Arrears billing schedule | Arrears calculates from actual period end; supports usage data import |
| Month-to-month with no defined end date | Evergreen billing schedule | No termination date required; rolls forward indefinitely until canceled |
| Professional services with milestone gates | Milestone billing with manual Invoice Run | Prevents premature invoicing; admin controls when each invoice fires |
| Complex custom schedule (variable amounts by date) | Dynamic Invoice Plan | Supports arbitrary date/amount combinations outside period-based logic |
| Need to invoice multiple order products on one invoice | Single Invoice Run with shared Invoice Date | Invoice Run aggregates multiple schedule items into one blng__Invoice__c per Account |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify prerequisites** — Confirm Salesforce Billing (blng__) is installed, Data Pipelines is enabled, and the org has at least one CPQ-sourced Order in Draft status. Check that the Account has a `blng__BillingPolicy__c` value set.
2. **Build the configuration chain** — In order: create or confirm Legal Entity (`blng__LegalEntity__c`), then Billing Policy (`blng__BillingPolicy__c`) linked to the Legal Entity and Tax Policy, then Billing Treatment (`blng__BillingTreatment__c`) linked to the Billing Policy. Do not skip steps or reorder.
3. **Configure Billing Rules on Products** — Set `blng__BillingRule__c` on each Product2 record. Select the schedule type (In-Advance, In-Arrears, Evergreen, Milestone). Set billing period and day-of-month fields to match contract terms.
4. **Activate the Order** — Change Order Status to Activated. Confirm that `blng__BillingSchedule__c` records are created — one per OrderProduct. If records are missing, check Data Pipelines status and Billing Rule linkage.
5. **Create and submit an Invoice Run** — Create a `blng__InvoiceRun__c` with `blng__InvoiceDate__c` and `blng__TargetDate__c` set correctly. Set Status to Posted to execute. Monitor the batch job in Setup > Apex Jobs for completion.
6. **Validate invoices** — Confirm `blng__Invoice__c` records are created with correct amounts, invoice dates, and line items. Confirm `blng__BillingSchedule__c` records show the expected next billing date.
7. **For Milestone billing only** — After each milestone completes, manually trigger a scoped Invoice Run. Confirm that only the completed milestone lines are invoiced; future milestones must remain uninvoiced.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Data Pipelines is enabled in Setup (hard dependency confirmed)
- [ ] Legal Entity, Billing Policy, Billing Treatment, and Tax Policy are all created and linked in the correct order
- [ ] Every Product2 in scope has a `blng__BillingRule__c` lookup populated with the correct schedule type
- [ ] The Account record has `blng__BillingPolicy__c` set to the correct Billing Policy
- [ ] `blng__BillingSchedule__c` records were auto-generated upon Order activation (no manual records)
- [ ] Invoice Run `blng__TargetDate__c` is set to capture all intended billing schedule items
- [ ] Invoice Run batch completed without errors (check Setup > Apex Jobs)
- [ ] `blng__Invoice__c` records show correct amounts, line counts, and invoice dates
- [ ] Milestone billing: only completed milestones have been invoiced; future milestones are still pending

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Data Pipelines is a silent hard dependency** — If Data Pipelines is not enabled, the Billing package installs successfully and the UI shows no errors, but `blng__BillingSchedule__c` records are never created when Orders activate. The failure is silent — no error is thrown, no record is created. Always verify Data Pipelines is enabled before debugging any "missing billing schedule" issue.
2. **Billing Policy must be on the Account, not the Order** — Many practitioners set the Billing Policy lookup on the Order directly, expecting it to drive invoice generation. The billing engine reads `blng__BillingPolicy__c` from the Account record, not the Order. Setting it only on the Order has no effect.
3. **Invoice Run Target Date is a hard cutoff, not a range** — An Invoice Run processes all billing schedule items where the next billing date is on or before `blng__TargetDate__c`. If `blng__TargetDate__c` is set to yesterday, items scheduled for today are excluded. Practitioners expecting to invoice "through today" must set target date to today, not yesterday.
4. **In-Arrears calculates from period end, not run date** — In-Arrears billing schedule amounts are finalized based on the actual service period end date stored on the schedule item, not the date the Invoice Run executes. Running the Invoice Run early does not change the invoice amount or date — the run simply skips items whose period has not yet ended.
5. **Manually created blng__BillingSchedule__c records are not invoice-run-eligible** — The Invoice Run engine has internal validation that marks billing schedule items as engine-created. Records created via Data Loader, Flow, or Apex that bypass the Order activation trigger are treated as invalid by the Invoice Run and silently skipped.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `blng__LegalEntity__c` record | Top of the configuration chain; required before Billing Policy can be created |
| `blng__BillingPolicy__c` record | Links Legal Entity and Tax Policy; set on Account to drive billing behavior |
| `blng__BillingTreatment__c` record | Child of Billing Policy; defines how the policy applies to specific billing scenarios |
| `blng__BillingRule__c` record | Set on Product2; defines schedule type, billing period, and day-of-month |
| `blng__BillingSchedule__c` records | Auto-generated per OrderProduct at Order activation; source of truth for invoice timing |
| `blng__InvoiceRun__c` record | Triggers batch processing of billing schedule items into invoices |
| `blng__Invoice__c` records | Aggregated invoice documents sent to customers |

---

## Related Skills

- `admin/products-and-pricebooks` — Configure Product2 records and price book entries before Billing Rules can be applied
- `admin/batch-job-scheduling-and-monitoring` — Monitor Invoice Run batch jobs in Setup > Apex Jobs and diagnose batch failures
