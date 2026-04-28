---
name: revenue-recognition-requirements
description: "Use this skill to configure and troubleshoot Salesforce Billing revenue recognition rules, schedules, and GL transaction generation in compliance with ASC 606. Triggers: 'revenue schedule not generated after order activation', 'blng__RevenueSchedule__c records missing', 'how to configure blng__RevenueRecognitionRule__c on a product', 'Finance Periods not set up before revenue schedule generation', 'revenue schedule did not update after contract amendment', 'performance obligation allocation for bundled products', 'distribution method for revenue spread', 'ASC 606 implementation in Salesforce Billing'. NOT for billing schedule setup (see billing-schedule-setup skill), NOT for standard Salesforce CPQ quoting, NOT for OpportunityLineItem native Revenue Schedules (standard platform feature unrelated to Salesforce Billing), NOT for Salesforce Revenue Cloud (Revenue Lifecycle Management)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Security
triggers:
  - "revenue schedule records are not generated after activating the order in Salesforce Billing"
  - "blng__RevenueSchedule__c records missing or show wrong amounts after order activation"
  - "how do I set up ASC 606 compliant revenue recognition rules in Salesforce Billing"
  - "Finance Periods must be configured before revenue schedules can be generated"
  - "revenue schedule did not update after amending the contract or order"
  - "how to configure performance obligation allocation across bundled products"
  - "which revenue distribution method should I use for a SaaS annual subscription"
tags:
  - revenue-recognition-requirements
  - salesforce-billing
  - blng-namespace
  - asc-606
  - revenue-schedule
  - revenue-recognition-rule
  - finance-periods
  - revenue-transaction
  - gl-events
  - performance-obligation
  - distribution-method
inputs:
  - "Salesforce org with Salesforce Billing managed package (blng__ namespace) installed on top of Salesforce CPQ"
  - "Activated or draft Order with OrderProducts sourced from a CPQ Quote"
  - "Product2 records requiring blng__RevenueRecognitionRule__c lookup configuration"
  - "Finance Periods configured in Salesforce Billing setup (hard prerequisite)"
  - "Determination of revenue recognition treatment: immediate, straight-line, event-based, or custom"
  - "Clarification of whether bundled products require separate performance obligation allocation"
  - "GL account mapping requirements for blng__RevenueTransaction__c records"
outputs:
  - "Configured blng__RevenueRecognitionRule__c records on Product2 with correct treatment and distribution method"
  - "blng__RevenueSchedule__c records auto-generated per OrderProduct at Order activation"
  - "blng__RevenueTransaction__c GL event records representing earned and deferred revenue movements"
  - "Finance Period configuration verified before schedule generation"
  - "Decision guidance on distribution method selection and amendment handling"
  - "Checklist confirming ASC 606 compliance requirements are met in configuration"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Revenue Recognition Requirements

This skill activates when a practitioner needs to configure Salesforce Billing revenue recognition rules, schedules, and GL transaction generation for ASC 606 compliance — from Finance Period setup through blng__RevenueTransaction__c posting and amendment handling.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the Salesforce Billing managed package (namespace prefix `blng__`) is installed. Revenue recognition objects live entirely within this managed package — they do not exist in standard Salesforce or CPQ alone.
- Confirm **Finance Periods are configured** in Salesforce Billing setup. Finance Periods are a hard prerequisite: the Billing engine cannot generate `blng__RevenueSchedule__c` records if no Finance Periods exist that overlap the Order's service date range.
- Identify the required recognition treatment for each product: Immediate Recognition, Straight-Line (rateable), Event-Based, or a custom distribution schedule.
- Know whether products are sold as bundles that require separate performance obligation allocation under ASC 606 rules — bundle components may need individual `blng__RevenueRecognitionRule__c` records.
- Confirm the GL account mapping requirements — `blng__RevenueTransaction__c` records feed downstream ERP integrations and must carry the correct GL account codes.

---

## Core Concepts

### Object Chain: Rule → Schedule → Transaction

Salesforce Billing implements ASC 606 through a three-level object chain. All three objects live in the `blng__` namespace:

```
blng__RevenueRecognitionRule__c  (configured on Product2)
        ↓  (triggers at Order activation)
blng__RevenueSchedule__c          (one per OrderProduct; holds the recognition schedule)
        ↓  (generated as Finance Periods close or revenue events fire)
blng__RevenueTransaction__c       (individual GL events: earned revenue and deferred revenue movements)
```

**blng__RevenueRecognitionRule__c** is the configuration object. It is set as a lookup on the Product2 record and defines the recognition treatment (how revenue is spread) and the distribution method (what period boundaries drive the spread). It does not hold amounts — amounts are computed at schedule generation time.

**blng__RevenueSchedule__c** is the computed schedule. One record is created per OrderProduct when the Order is activated. It holds the total contract value to be recognized and the breakdown of that value across Finance Periods. Unlike billing schedules, revenue schedules use Finance Periods — not calendar months — as their period boundary.

**blng__RevenueTransaction__c** represents individual GL events. Each transaction record marks a movement of revenue from deferred to earned status, or a reversal. These are the records that feed ERP and GL integrations. They are generated when a Finance Period closes or when a revenue event triggers recognition.

### Finance Periods: Hard Prerequisite for Schedule Generation

Finance Periods (`blng__FinancePeriod__c`) define the accounting calendar used by the revenue recognition engine. They must be created and activated in Salesforce Billing setup before any `blng__RevenueSchedule__c` records can be generated.

The revenue engine calculates how revenue is distributed across Finance Periods. If no Finance Periods exist that overlap an Order's service dates, the engine cannot allocate revenue and the schedule record is not created — with no error surfaced to the end user. This is a silent failure.

Finance Periods do not auto-generate. An admin must explicitly create them for all periods that will have active revenue schedules, including future periods for multi-year subscriptions.

### Revenue Distribution Methods

The `blng__DistributionMethod__c` field on `blng__RevenueRecognitionRule__c` controls how contract revenue is spread across Finance Periods. Salesforce Billing supports:

| Distribution Method | Behavior |
|---|---|
| Daily Proration | Revenue allocated proportionally to the number of days in each Finance Period that overlap the service date range |
| Equal Distribution | Revenue divided equally across all Finance Periods in the service range, regardless of period length |
| Percent Distribution | Admin defines a custom percentage per period on the rule |
| Single Period | Full amount recognized in one Finance Period (immediate recognition) |

For SaaS annual subscriptions, Daily Proration is the most common choice because it correctly handles partial-month periods at subscription start and end.

### Revenue Recognition Treatments

The `blng__RecognitionTreatment__c` field on `blng__RevenueRecognitionRule__c` defines the trigger for recognition:

| Treatment | Behavior |
|---|---|
| Immediate | Revenue is recognized at Order activation. Used for one-time products delivered at point of sale. |
| Rateable | Revenue is spread ratably over the service period. The most common treatment for subscription SaaS products (ASC 606 §606-10-25-27 performance obligation satisfied over time). |
| Event-Based | Revenue is recognized when a specified event occurs (e.g., delivery confirmation, milestone completion). Requires an event record to trigger the recognition. |
| Custom | Admin-defined schedule; rarely used. |

### Contract Amendments Do Not Auto-Update Revenue Schedules

When a contract is amended (Order amendment or replacement order in CPQ Billing), the **existing `blng__RevenueSchedule__c` record is not automatically updated**. The revenue engine does not re-compute previously generated schedules. The practitioner must:

1. Cancel or close the existing revenue schedule manually.
2. Ensure the amendment order generates a new `blng__RevenueSchedule__c` for the amended terms.
3. Reconcile any periods already recognized under the old schedule.

This is a critical difference from billing schedules, which handle amendments through a separate amendment order product. Revenue schedules require explicit manual intervention to align with amended contract values.

### Performance Obligation Allocation for Bundles

Under ASC 606, bundled products that contain multiple distinct performance obligations must have revenue allocated to each obligation based on standalone selling price (SSP). In Salesforce Billing:

- Each bundle component Product2 that is a distinct performance obligation should have its own `blng__RevenueRecognitionRule__c`.
- The `blng__StandaloneSellingPrice__c` field on the bundle component drives the allocation ratio.
- If SSP fields are not populated, the Billing engine defaults to allocating revenue based on the list price ratio, which may not comply with ASC 606 SSP requirements.

---

## Common Patterns

### Pattern 1: SaaS Annual Subscription — Monthly Revenue Spread

**When to use:** A SaaS product is sold as a 12-month subscription. Revenue must be recognized ratably month by month, not at invoice date.

**How it works:**
1. Create a `blng__RevenueRecognitionRule__c` with `blng__RecognitionTreatment__c = Rateable` and `blng__DistributionMethod__c = Daily Proration`.
2. Set the rule as the `blng__RevenueRecognitionRule__c` lookup on the Product2 record.
3. Confirm Finance Periods exist for all 12 months of the subscription service period.
4. Activate the Order — one `blng__RevenueSchedule__c` is created per OrderProduct, pre-calculated across each Finance Period.
5. As each Finance Period closes, `blng__RevenueTransaction__c` GL event records are generated for the earned portion.

**Why not the alternative:** Using Immediate recognition for a 12-month subscription recognizes the full contract value at activation. This violates ASC 606 §606-10-25-27 (performance obligation satisfied over time) and misstates deferred revenue on the balance sheet.

### Pattern 2: Amendment Requires Manual Revenue Schedule Reconciliation

**When to use:** A customer upgrades a subscription mid-term (e.g., adds seats at month 6 of a 12-month contract). The existing revenue schedule must be reconciled against the amended terms.

**How it works:**
1. The CPQ amendment order creates a new OrderProduct representing the uplift.
2. At activation of the amendment order, a new `blng__RevenueSchedule__c` is created for the uplift delta only.
3. The original `blng__RevenueSchedule__c` is NOT modified — it continues to recognize revenue based on the original contract value.
4. Finance team must confirm whether the two schedules produce the correct cumulative GL entries. In some cases, the original schedule must be manually closed and a net-new schedule created for the full amended value.

**Why not the alternative:** Attempting to edit `blng__RevenueSchedule__c` records directly corrupts the recognition timeline and produces double-counting in GL entries. The object is system-managed — treat it as read-only after generation.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| SaaS subscription, recognize ratably | Rateable treatment + Daily Proration distribution | Compliant with ASC 606 over-time recognition; handles partial months correctly |
| One-time product delivered at sale | Immediate treatment + Single Period distribution | Full amount earned at point of sale; no deferred revenue balance required |
| Professional services, milestone-based | Event-Based treatment | Ties recognition to delivery event, not calendar; supports ASC 606 point-in-time obligation |
| Bundle with distinct performance obligations | Separate blng__RevenueRecognitionRule__c per component with SSP allocation | ASC 606 requires SSP-based allocation across distinct obligations |
| Mid-term amendment (upgrade/downgrade) | Generate new schedule for delta; manually close and reconcile original if needed | Revenue engine does not auto-update existing schedules; manual reconciliation required |
| Finance Periods missing for service dates | Create Finance Periods first; then re-trigger schedule generation | Silent failure: schedules do not generate without Finance Periods covering the date range |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify Finance Period prerequisites** — Navigate to Salesforce Billing setup and confirm that Finance Periods (`blng__FinancePeriod__c`) exist and are Active for all calendar periods that overlap the Order's service date range. Create missing Finance Periods before proceeding. Without this step, revenue schedule generation silently fails.
2. **Configure blng__RevenueRecognitionRule__c on Product2** — Create or confirm the Revenue Recognition Rule with the correct `blng__RecognitionTreatment__c` (Rateable, Immediate, Event-Based) and `blng__DistributionMethod__c` (Daily Proration, Equal Distribution, Single Period). Assign the rule to the `blng__RevenueRecognitionRule__c` lookup on each in-scope Product2 record.
3. **For bundles, configure SSP allocation** — For each bundle component Product2 that is a distinct ASC 606 performance obligation, set `blng__StandaloneSellingPrice__c`. Confirm the allocation ratios sum correctly across all components.
4. **Activate the Order** — Change Order Status to Activated. Confirm that `blng__RevenueSchedule__c` records are created — one per OrderProduct with a Revenue Recognition Rule. If records are missing, verify Finance Period coverage and the Product2 rule lookup.
5. **Validate revenue schedule line distribution** — Open each `blng__RevenueSchedule__c` record and review the child line records. Confirm amounts are distributed correctly across Finance Periods with expected proration logic.
6. **Confirm blng__RevenueTransaction__c GL event generation** — After Finance Periods close (or event-based triggers fire), confirm that `blng__RevenueTransaction__c` records are created with the correct GL account codes, amounts, and period references. These feed downstream ERP integrations.
7. **For amendments: reconcile manually** — If an Order amendment changes contract value, confirm the amendment order generates a new `blng__RevenueSchedule__c` for the delta. Coordinate with Finance on whether the original schedule requires manual closure and replacement. Document the reconciliation in the Finance Period notes.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Finance Periods exist and are Active for all service date periods covered by the Order
- [ ] Every in-scope Product2 has `blng__RevenueRecognitionRule__c` lookup populated with the correct rule
- [ ] Recognition treatment (Rateable/Immediate/Event-Based) matches the ASC 606 performance obligation type for each product
- [ ] Distribution method matches contract and Finance reporting requirements (Daily Proration for partial-month accuracy)
- [ ] For bundles: `blng__StandaloneSellingPrice__c` is set on each distinct performance obligation component
- [ ] `blng__RevenueSchedule__c` records were auto-generated at Order activation (not manually created)
- [ ] Revenue schedule line amounts sum to the correct total contract value
- [ ] `blng__RevenueTransaction__c` GL events carry correct GL account codes for the downstream ERP integration
- [ ] For amendments: original revenue schedule has been reviewed; manual reconciliation was performed if contract value changed

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Finance Periods are a silent hard prerequisite** — If Finance Periods do not exist for the Order's service date range, `blng__RevenueSchedule__c` records are not generated when the Order activates. No error is thrown, no warning appears — the system simply skips schedule creation. Always verify Finance Periods before activating Orders or debugging "missing revenue schedule" issues.
2. **Revenue schedules do not auto-update on contract amendment** — Unlike CRM contract fields that update when an amendment record is saved, `blng__RevenueSchedule__c` records are immutable after generation. An amendment order generates a new delta schedule; it does not revise the original. Finance teams that expect the original schedule to reflect the amended contract value will find a persistent discrepancy until the original is manually reconciled.
3. **blng__RevenueSchedule__c and OpportunityLineItem Revenue Schedules are completely different objects** — Standard Salesforce allows "Revenue Schedules" to be enabled in Setup > Products > Schedule Settings, which populates the `Revenue Schedules` related list on OpportunityLineItems. This is a standard CRM feature for splitting opportunity revenue across periods for forecasting. It has no relationship to `blng__RevenueSchedule__c`, does not interact with the Salesforce Billing engine, and does not generate GL transactions. Enabling or populating standard Revenue Schedules has zero effect on Salesforce Billing recognition behavior.
4. **SSP defaults to list price ratio if unset** — For bundle products, if `blng__StandaloneSellingPrice__c` is not populated on bundle components, the engine allocates revenue using list price ratios. List price ratios may not equal the SSP ratios required by ASC 606, creating an audit finding. This mismatch is not flagged by the platform.
5. **blng__RevenueTransaction__c records are system-created; manual edits corrupt GL integrity** — Revenue Transaction records are created by the Billing engine as Finance Periods close. Direct edits via data loader or Apex bypass the engine's internal consistency checks and can produce GL balances that do not reconcile to the revenue schedule totals. Treat these records as read-only.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `blng__RevenueRecognitionRule__c` record | Configuration record defining treatment and distribution method; set on Product2 |
| `blng__RevenueSchedule__c` records | Auto-generated at Order activation; one per OrderProduct; holds recognition timeline |
| `blng__RevenueTransaction__c` records | GL event records generated as Finance Periods close; feed ERP integrations |
| Finance Period records (`blng__FinancePeriod__c`) | Accounting calendar prerequisite; must exist before schedules can generate |

---

## Related Skills

- `admin/billing-schedule-setup` — Configure billing schedules and invoice runs (separate from revenue recognition; both may apply to the same product)
- `admin/cpq-order-management` — Understand how CPQ Quote-to-Order flow creates OrderProducts that drive both billing and revenue schedule generation
