---
name: revenue-lifecycle-management
description: "Use this skill when implementing or troubleshooting Salesforce Revenue Lifecycle Management (RLM) — the native Revenue Cloud product covering order-to-cash lifecycle, Dynamic Revenue Orchestrator (DRO) fulfillment plan design, asset amendments, billing schedule creation via Connect API, and invoice management. Triggers on: Dynamic Revenue Orchestrator, RLM order decomposition, DRO fulfillment swimlanes, native Revenue Cloud billing schedule, asset lifecycle management Salesforce. NOT for CPQ quoting or pricing rules (use cpq-* skills), not for the legacy Salesforce Billing managed package with blng__* objects (different product entirely), not for standard Order objects without Revenue Cloud features."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
tags:
  - revenue-cloud
  - rlm
  - dynamic-revenue-orchestrator
  - dro
  - order-to-cash
  - billing-schedule
  - asset-lifecycle
  - invoice-management
  - fulfillment
inputs:
  - "Revenue Cloud (RLM) enabled org"
  - "Order and OrderItem records (native Salesforce objects, not CPQ)"
  - "Dynamic Revenue Orchestrator fulfillment plan definition"
  - "Connect API credentials for billing schedule creation"
outputs:
  - "DRO fulfillment plan with swimlane configuration"
  - "Billing schedule created via Connect API POST"
  - "Asset amendment order design"
  - "Invoice management workflow"
triggers:
  - "Dynamic Revenue Orchestrator DRO fulfillment plan setup"
  - "RLM billing schedule not created automatically"
  - "native Revenue Cloud vs Salesforce Billing difference"
  - "DRO stalled swimlane troubleshooting"
  - "asset amendment creates new BillingSchedule"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# Revenue Lifecycle Management

This skill activates when a practitioner needs to implement the native Salesforce Revenue Lifecycle Management (RLM) product — the Revenue Cloud order-to-cash engine distinct from the CPQ managed package. It covers Dynamic Revenue Orchestrator (DRO) for order decomposition, asset amendments, billing schedule creation, and invoice management. It does NOT cover CPQ quoting, pricing rules, or the legacy blng__* Salesforce Billing managed package objects.

---

## Before Starting

Gather this context before working on anything in this domain:

- Revenue Lifecycle Management (RLM) is a native Revenue Cloud product, completely distinct from CPQ + Salesforce Billing (managed package). RLM uses standard Salesforce objects (Order, OrderItem, BillingSchedule, Invoice). CPQ uses custom managed objects (blng__*, SBQQ__*). These are different products with different object models.
- Billing schedules in RLM are created via Connect API POST after order activation — they do NOT auto-update when an asset amendment order is activated. Each amendment produces a net-new BillingSchedule record requiring manual reconciliation.
- Dynamic Revenue Orchestrator (DRO) decomposes a commercial order into technical fulfillment orders routed across swimlanes (billing, provisioning, shipping) using auto-tasks, callouts, manual tasks, milestones, and pauses.

---

## Core Concepts

### Revenue Lifecycle Management vs. CPQ + Salesforce Billing

| Dimension | RLM (Native Revenue Cloud) | CPQ + Salesforce Billing |
|---|---|---|
| Object model | Standard API objects (Order, BillingSchedule, Invoice) | Managed package objects (SBQQ__*, blng__*) |
| Quoting | Product Catalog + Pricing engine | CPQ Quote, Quote Line, Price Rules |
| Fulfillment | Dynamic Revenue Orchestrator | Salesforce Billing DRE (different engine) |
| Billing schedules | Created via Connect API POST | blng__BillingSchedule__c, auto-created |
| Amendments | Asset Lifecycle Management | SBQQ__Amendment pattern |

These are not interchangeable. Code, SOQL, flows, and automation built for one product does NOT work for the other.

### Dynamic Revenue Orchestrator (DRO)

DRO is the fulfillment engine in RLM. When a commercial order is activated, DRO creates a **fulfillment plan** that decomposes the order into technical fulfillment orders. Each fulfillment order is routed across configurable **swimlanes** (e.g., billing, provisioning, shipping).

Swimlane steps can include:
- **Auto-tasks** — automated Apex or integration callouts
- **Manual tasks** — human review steps
- **Callouts** — external system notifications
- **Milestones** — synchronization points across swimlanes
- **Pauses** — wait states pending external completion signals

DRO enables parallel processing of fulfillment activities that can proceed independently while maintaining synchronization at milestones.

### Billing Schedule Creation

Unlike legacy Salesforce Billing, RLM does NOT automatically create billing schedules on order activation. After an order is activated, billing schedules must be explicitly created via a **Connect API POST** call. The request specifies the OrderItem, start date, billing period, and amount.

Critically: when an asset amendment order is activated, it does NOT auto-update existing BillingSchedule records. Instead, a net-new BillingSchedule record is created for the amended asset. Reconciling billing schedules across the full asset lifecycle requires explicit aggregation logic.

### Asset Lifecycle Management

Assets in RLM represent contracted products post-order. The asset lifecycle follows: Order Activated → Asset Created → Asset Amendment → Renewal. Each asset amendment generates a new Order and new fulfillment plan through DRO.

### Invoice Management

Invoices in RLM are standard Invoice objects (not blng__Invoice__c). Invoice generation is triggered from BillingSchedule milestones. Invoice posting creates FinanceTransaction records (read-only accounting journal entries). Payments are tracked via the Payment standard object.

---

## Common Patterns

### Pattern 1: Configure a DRO Fulfillment Plan with Parallel Swimlanes

**When to use:** A commercial order requires parallel execution of billing setup, provisioning, and shipping steps.

**How it works:**

1. In Revenue Cloud Setup > Dynamic Revenue Orchestrator, create a Fulfillment Plan.
2. Add Swimlanes: "Billing", "Provisioning", "Shipping".
3. Within each swimlane, define steps:
   - Billing: Auto-task (Create Billing Schedule via Connect API), then Milestone "Ready to Invoice"
   - Provisioning: Callout to provisioning system, Manual Task (provisioning confirmation), Milestone "Provisioned"
   - Shipping: Auto-task (generate shipping label), Callout to fulfillment partner
4. Define cross-swimlane synchronization: shipping starts after "Provisioned" milestone.
5. Assign the Fulfillment Plan to the product catalog entries that trigger this plan.

**Why not use a single sequential flow:** Parallel swimlanes cut fulfillment cycle time significantly when billing, provisioning, and shipping can proceed concurrently.

### Pattern 2: Create a Billing Schedule via Connect API

**When to use:** An order has been activated and requires billing schedule creation.

**How it works:**

```python
# POST to Connect API BillingSchedule resource
import requests

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

payload = {
    "orderItemId": "801...",  # OrderItem ID
    "billingStartDate": "2026-05-01",
    "billingFrequency": "Monthly",
    "numberOfBillingPeriods": 12,
    "amount": 1200.00
}

resp = requests.post(
    f"{instance_url}/services/data/v63.0/commerce/billing/schedules",
    headers=headers,
    json=payload
)
billing_schedule = resp.json()
```

**Why not use standard Salesforce Billing objects:** RLM uses standard API objects, not blng__* managed-package objects. blng__BillingSchedule__c is for the legacy Salesforce Billing product — using it in an RLM org will not link to native Revenue Cloud billing flows.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| CPQ quoting, pricing rules, discount schedules | Use cpq-* skills | Completely separate product, different objects |
| Order decomposition into fulfillment steps | Dynamic Revenue Orchestrator (DRO) | Native RLM fulfillment engine |
| Create billing schedule after order activation | Connect API POST | RLM does not auto-create billing schedules |
| Asset amendment billing reconciliation | Aggregate BillingSchedule records by Asset | Amendment creates new BillingSchedule, not update |
| Invoice generation | Configure BillingSchedule milestone triggers | Invoice generation flows from BillingSchedule milestones |
| Legacy Salesforce Billing (blng__*) | Use billing-schedule-setup skill | Separate product, separate workflow |

---

## Recommended Workflow

1. Confirm the org is enabled for Revenue Cloud (RLM) — check Setup > Revenue Cloud — and distinguish from CPQ/Salesforce Billing.
2. Design the product catalog (Product Catalog and Pricing in Revenue Cloud Setup) before configuring DRO.
3. Create DRO Fulfillment Plan: define swimlanes and steps (auto-tasks, callouts, manual tasks, milestones, pauses).
4. Assign the Fulfillment Plan to relevant product catalog entries.
5. After order activation, create billing schedules via Connect API POST for each OrderItem that requires billing.
6. For asset amendments: activate the amendment order, then create net-new BillingSchedule records for amended assets via Connect API. Do not expect auto-update of existing schedules.
7. Configure Invoice generation from BillingSchedule milestone triggers.
8. Monitor DRO fulfillment plan execution via the Revenue Cloud Fulfillment Dashboard.

---

## Review Checklist

- [ ] Org confirmed as Revenue Cloud (RLM), not CPQ + Salesforce Billing
- [ ] DRO Fulfillment Plan defined with appropriate swimlanes and step types
- [ ] Billing schedules created via Connect API POST after order activation
- [ ] Amendment workflow documented: amendment creates new BillingSchedule, not update
- [ ] FinanceTransaction records (read-only) reviewed for accounting journal validation
- [ ] No blng__* or SBQQ__* objects used in RLM code or flows
- [ ] Invoice generation configured from BillingSchedule milestones

---

## Salesforce-Specific Gotchas

1. **RLM and CPQ + Salesforce Billing Are Completely Different Products** — The most damaging LLM error is conflating these two product lines. blng__BillingSchedule__c is not the same as the standard BillingSchedule object. Code, flows, and SOQL from one product does not work in the other. Always confirm which product is in use before writing any code.

2. **Billing Schedules Are Not Auto-Created on Order Activation** — Unlike legacy Salesforce Billing, RLM does not automatically create BillingSchedule records when an order activates. This is an explicit Connect API call that must be coded or configured. Missing this step leaves orders with no billing schedule.

3. **Amendment Orders Create New BillingSchedule Records** — Activating an asset amendment order does NOT update the existing BillingSchedule — it creates a net-new one. Billing reconciliation across amendments requires aggregating all BillingSchedule records for a given asset.

4. **FinanceTransaction Is Read-Only** — FinanceTransaction records are system-generated accounting journal entries created when an Invoice is posted or a Payment is received. They cannot be created, updated, or deleted via API. Attempting to DML FinanceTransaction records causes errors.

5. **DRO Swimlane Step Errors Do Not Auto-Retry** — If a DRO auto-task or callout step fails (e.g., an Apex auto-task throws an exception), the DRO plan stalls at that step. There is no automatic retry. Operators must review the DRO dashboard, resolve the root cause, and manually resume the fulfillment plan.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| DRO Fulfillment Plan design | Swimlane configuration with step types and milestone synchronization |
| Billing schedule creation script | Connect API POST implementation for post-activation billing setup |
| Amendment billing reconciliation query | SOQL/query pattern to aggregate BillingSchedule records across asset lifecycle |
| RLM vs. CPQ disambiguation guide | Checklist to confirm which product is in use before beginning implementation |

---

## Related Skills

- revenue-cloud-data-model — for native Revenue Cloud object relationships (BillingSchedule, Invoice, FinanceTransaction)
- revenue-cloud-architecture — for order-to-cash architecture design across Revenue Cloud domains
- billing-schedule-setup — for legacy Salesforce Billing managed package (blng__*) billing schedules
