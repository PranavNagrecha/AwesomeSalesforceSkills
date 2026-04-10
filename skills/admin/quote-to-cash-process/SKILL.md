---
name: quote-to-cash-process
description: "Use when designing, mapping, or troubleshooting the end-to-end quote-to-cash process in orgs running Salesforce CPQ (managed package) or Revenue Cloud — covering the full object chain from SBQQ__Quote__c through Contract to blng__Invoice__c, approval routing via Advanced Approvals (sbaa__), billing schedule generation, and order activation. Trigger keywords: CPQ quote, SBQQ, revenue cloud billing, Advanced Approvals, subscription, blng invoice, contract pivot. NOT for standard Sales Cloud quote-to-cash or implementation of individual CPQ pricing rules, discount schedules, or guided selling configuration — use the quote-to-cash-requirements skill for standard objects."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Security
triggers:
  - "Our CPQ quotes are approved but invoices are never being generated — how does the billing chain get triggered?"
  - "We need multi-step conditional approval routing in CPQ where different approvers are required based on discount tier and deal size"
  - "How does a Contract connect an approved CPQ quote to subscriptions and billing schedules in Revenue Cloud?"
  - "What objects do we need to query to report on CPQ quote lines through to invoice in a Revenue Cloud org?"
  - "We activated an order in CPQ but no billing schedule was created — what did we miss?"
  - "How do the SBQQ and blng managed package objects relate across the full quote-to-cash lifecycle?"
tags:
  - cpq
  - revenue-cloud
  - sbqq
  - billing
  - advanced-approvals
  - sbaa
  - contract
  - subscription
  - invoice
  - quote-to-cash
inputs:
  - "Confirmation that Salesforce CPQ (SBQQ__) and/or Revenue Cloud Billing (blng__) managed packages are installed"
  - "Current CPQ quote configuration: products, pricing methods, and discount thresholds requiring approval"
  - "Approval routing requirements: number of tiers, approver sources (user, queue, role hierarchy), conditional branching logic"
  - "Billing model: one-time, recurring, usage-based, or hybrid — determines billing schedule shape"
  - "Order activation and subscription creation requirements"
  - "Contract amendment and co-termination requirements if applicable"
outputs:
  - "CPQ Q2C object chain map showing every record type and relationship from SBQQ__Quote__c to blng__Invoice__c"
  - "Advanced Approvals design: approval rules, approval conditions, approver objects, and chain configuration"
  - "Contract pivot design: fields required on Contract to connect approved quote to downstream billing"
  - "Billing schedule and invoice generation requirements document"
  - "Status transition table for quote, order, contract, subscription, and invoice lifecycle"
  - "Gap list identifying requirements that cannot be met without custom Apex or additional packages"
dependencies:
  - cpq-data-model
  - cpq-architecture-patterns
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# Quote-to-Cash Process (CPQ + Revenue Cloud)

Use this skill when mapping, designing, or troubleshooting the end-to-end quote-to-cash process in orgs running Salesforce CPQ or Revenue Cloud. It covers the complete object chain from SBQQ__Quote__c through Contract to blng__Invoice__c, the Advanced Approvals managed package, and the billing triggers that fire on order activation.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm **both managed packages** are installed: Salesforce CPQ (namespace `SBQQ`) and, if billing is in scope, Revenue Cloud Billing (namespace `blng`). Query `PackageLicense` or check Setup > Installed Packages.
- Identify the **billing model** in use: one-time charges, recurring subscriptions (monthly/annual), usage-based billing, or a hybrid mix. This determines how blng__BillingSchedule__c records are shaped.
- Confirm whether the org uses **Advanced Approvals** (namespace `sbaa`) or standard Salesforce Approval Processes for CPQ quotes. They are mutually exclusive in practice — Advanced Approvals is a separate managed package installed alongside CPQ and provides multi-step conditional routing that standard Approval Processes cannot replicate for CPQ.
- Determine whether **contract amendments** (mid-term changes) or **renewals** are in scope — both require careful handling of the Contract record and existing Subscription records before new quotes are generated.
- Check the org's **Order Management** configuration: `SBQQ__OrderingPreference__c` on the Quote and the `SBQQ__Contracted__c` field on the Order drive whether order activation creates Subscriptions and triggers billing.

---

## Core Concepts

### 1. The CPQ Q2C Object Chain

The canonical object chain in a CPQ + Revenue Cloud org is:

```
SBQQ__Quote__c
  -> SBQQ__QuoteLine__c (line items with pricing, discounts, product configuration)
     -> [Approval via sbaa__ApprovalRequest__c if Advanced Approvals is installed]
  -> SBQQ__Quote__c.SBQQ__Status__c = "Approved"
     -> Contract (standard object — required pivot)
        -> SBQQ__Subscription__c (one per recurring quote line)
        -> Order (standard object)
           -> OrderItem
           -> blng__BillingSchedule__c (one per billable order item)
              -> blng__BillingScheduleItem__c
              -> blng__Invoice__c
                 -> blng__InvoiceLine__c
```

Every stage in this chain is triggered by a status transition or field value change — nothing is purely manual. The most common misconfiguration is assuming that setting a Quote to Approved automatically creates a Contract. It does not. Contract creation is a deliberate step, driven by the **Create Contract** button or a custom automation that calls `SBQQ.ServiceRouter` or sets `SBQQ__Quote__c.SBQQ__Contracted__c = true`.

### 2. The Contract as the Required Pivot

The Contract record is the mandatory bridge between the approved CPQ quote and all downstream billing and subscription records. It is not optional.

When a Quote is contracted (via the Quote's "Create Contract" action or automation):
- A Contract record is created and linked to the Account.
- `SBQQ__Subscription__c` records are created for each recurring Quote Line — linked to the Contract via `SBQQ__Contract__c`.
- The Contract's `SBQQ__RenewalForecast__c` and `SBQQ__RenewalQuoted__c` flags control whether renewal quotes are auto-generated.

If the Contract record is skipped or bypassed (e.g., an Order is created directly from the Quote without contracting), Subscription records are never created and blng billing schedules cannot be generated for recurring products. This is the single most common architectural failure in CPQ implementations.

### 3. Advanced Approvals (sbaa__ Namespace)

Advanced Approvals is a **separate managed package** (namespace `sbaa`) installed alongside Salesforce CPQ. It is not part of the core CPQ package. Its key objects are:

- `sbaa__ApprovalChain__c` — the named approval chain (e.g., "CPQ Discount Approval")
- `sbaa__ApprovalRule__c` — a rule that adds an approver to the chain when conditions are met (e.g., Discount > 20%)
- `sbaa__ApprovalCondition__c` — field-level conditions that qualify a rule
- `sbaa__Approver__c` — the approver definition (user, queue, or group)
- `sbaa__ApprovalRequest__c` — the runtime approval record created when a quote enters approval

Standard Salesforce Approval Processes fire on the `SBQQ__Quote__c` object but cannot support conditional multi-step branching based on Quote Line attributes. Advanced Approvals evaluates rules against both Quote-level and Quote Line-level fields, making it the correct tool for CPQ discount approval scenarios with multiple tiers or product-specific overrides.

**Critical distinction:** `sbaa__ApprovalRequest__c` is the runtime record — not the same as a standard `ProcessInstanceWorkitem`. SOQL queries on `ProcessInstanceWorkitem` will return empty for Advanced Approvals-managed quotes.

### 4. Order Activation and Billing Trigger

In a CPQ + Revenue Cloud org, billing schedules are generated by **activating an Order**, not by creating it. The trigger sequence is:

1. Quote is contracted → Contract + Subscriptions created.
2. Order is created from the Contract (or from the Quote, if ordering before contracting).
3. Order `Status` is set to `Activated`.
4. CPQ's order management code fires and sets `SBQQ__Contracted__c = true` on the Order.
5. `blng__BillingSchedule__c` records are created for each OrderItem with a billing-enabled product.
6. Billing runs (scheduled job or on-demand) processes billing schedules and generates `blng__Invoice__c` records.

If the Order is never activated, billing schedules are never created. If `blng__BillingSchedule__c` records exist but `blng__Invoice__c` records do not, the billing run has not executed or the billing rule on the product is misconfigured.

---

## Common Patterns

### Pattern: Advanced Approvals Chain for Tiered Discount Routing

**When to use:** CPQ org requires manager approval above 15% line-level discount and VP approval above 30%, with different approvers per product family.

**How it works:**
1. Create one `sbaa__ApprovalChain__c` named "CPQ Quote Approval" and link it to the `SBQQ__Quote__c` object.
2. Create `sbaa__ApprovalRule__c` records — one per approval tier. Each rule references the chain and contains an `sbaa__ApprovalCondition__c` that evaluates a Quote or Quote Line field (e.g., `SBQQ__Discount__c > 15`).
3. Define `sbaa__Approver__c` records pointing to a User, Queue, or field-based dynamic user (e.g., `Owner.Manager`).
4. On Quote submission, the package evaluates all rules and builds the runtime `sbaa__ApprovalRequest__c` chain in order.
5. Quote `SBQQ__Status__c` changes to `"Approved"` only after all required `sbaa__ApprovalRequest__c` records in the chain reach `sbaa__Status__c = "Approved"`.

**Why not standard Approval Processes:** Standard processes cannot evaluate Quote Line fields as entry criteria and cannot dynamically add or remove approver steps based on combinations of quote-level and line-level attributes.

### Pattern: Automated Contract Creation on Quote Approval

**When to use:** Business requires no manual intervention between quote approval and contract + subscription creation.

**How it works:**
1. Create a Record-Triggered Flow on `SBQQ__Quote__c`, fired on Update, entry criteria: `SBQQ__Status__c changed to "Approved"` and `SBQQ__Contracted__c = false`.
2. In the Flow, call the CPQ `SBQQ.ServiceRouter` via an Apex action or use the `QuoteDocumentService` API to contract the quote. Alternatively, set `SBQQ__Quote__c.SBQQ__Contracted__c = true` — CPQ's trigger handler fires on this field change and creates the Contract + Subscriptions.
3. After the contract is created, a second flow (or continuation of the first) creates the Order from the Contract using the "Create Order" action on the Contract, then activates it.

**Why not a Process Builder:** Process Builder is legacy. More importantly, the CPQ package's `SBQQ__Contracted__c` field change must be handled carefully to avoid recursion — Flow with re-entry condition `Once per record version` is safer.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single-level discount approval in CPQ | Advanced Approvals with a single-rule chain | Standard Approval Processes cannot evaluate Quote Line fields; Advanced Approvals is the package-supported approach |
| Multi-tier conditional approval by line attributes | Advanced Approvals with multiple `sbaa__ApprovalRule__c` records per chain | Rules are evaluated dynamically at submission — chain is built at runtime, not design time |
| Need to query approval status of a CPQ quote | Query `sbaa__ApprovalRequest__c` where `sbaa__TargetId__c = quoteId` | `ProcessInstanceWorkitem` returns empty for Advanced Approvals-managed records |
| Recurring products need billing schedules | Contract the Quote before or alongside Order creation | Billing schedules are created by the Order activation path — Contract + Subscriptions must exist |
| Order created but no billing schedules generated | Check Order `Status = Activated` and `SBQQ__Contracted__c = true` on Order | Both flags are required for the blng billing schedule trigger to fire |
| Amendment to an active subscription mid-term | Use the "Amend" button on the Contract to generate an Amendment Quote | Amending directly on the Subscription or Order will corrupt the billing chain |
| Renewal quote generation | Configure `SBQQ__RenewalForecast__c` and `SBQQ__RenewalTerm__c` on Contract | CPQ auto-generates a Renewal Opportunity and Quote based on these fields + Subscription records |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm CPQ and billing package installation** — Verify `SBQQ` and `blng` namespaces in Setup > Installed Packages. Confirm whether Advanced Approvals (`sbaa`) is also installed. If any package is missing, no downstream object exists and the workflow cannot proceed.
2. **Map the approval requirements to Advanced Approvals objects** — Document each discount tier, the approver source (user, queue, role hierarchy field), and the Quote or Quote Line field used as the condition. Translate each tier into an `sbaa__ApprovalRule__c` + `sbaa__ApprovalCondition__c` pair within a named `sbaa__ApprovalChain__c`.
3. **Design the Contract pivot** — Document exactly which fields on the Quote drive the Contract creation, which Subscription fields are populated from Quote Lines, and whether Contract start/end dates come from the Quote or are entered manually. The Contract is mandatory — document this explicitly with stakeholders.
4. **Map the Order activation and billing trigger sequence** — Confirm that activating an Order sets `SBQQ__Contracted__c = true` (check CPQ Order Management settings). Identify which products have `blng__BillingRule__c` assigned (required for billing schedule creation). Confirm the billing run schedule.
5. **Build and test the approval chain in sandbox** — Create test quotes at each discount tier and submit for approval. Verify `sbaa__ApprovalRequest__c` records are created in the correct sequence and that Quote `SBQQ__Status__c` transitions correctly on final approval.
6. **Test the Contract-to-Invoice chain end-to-end** — In sandbox: approve a quote → contract it → create and activate an Order → confirm `blng__BillingSchedule__c` records exist → run the billing job → confirm `blng__Invoice__c` records are generated with correct amounts and dates.
7. **Validate amendment and renewal paths** — Use the Contract's Amend and Renew actions on at least one test record. Confirm that the new quote's Subscription references are correct and that billing schedules on the original order are not duplicated.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] CPQ (SBQQ), Billing (blng), and Advanced Approvals (sbaa) package installation confirmed
- [ ] Every `sbaa__ApprovalRule__c` has at least one `sbaa__ApprovalCondition__c` and a linked `sbaa__Approver__c`
- [ ] Contract creation is automated or explicitly documented as a required manual step — no implicit assumption that Quote approval triggers Contract creation
- [ ] `SBQQ__Contracted__c` on the Order is set to `true` before billing schedules are expected
- [ ] Each recurring product has a `blng__BillingRule__c` assigned — products without billing rules generate no billing schedule
- [ ] Billing run schedule is configured and enabled in Setup > Billing Runs
- [ ] Amendment and renewal paths tested in sandbox — existing Subscriptions not duplicated
- [ ] No standard `Quote` or `QuoteLineItem` SOQL used in Apex or reports — CPQ orgs use `SBQQ__Quote__c` and `SBQQ__QuoteLine__c`

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Contract is required — skipping it breaks billing permanently** — If an Order is created directly from an approved Quote without first creating a Contract, `SBQQ__Subscription__c` records are never generated. Without Subscriptions linked to a Contract, `blng__BillingSchedule__c` records cannot be created for recurring products. This cannot be retroactively fixed without recreating the Contract and re-linking records.
2. **Advanced Approvals is a separate installed package — not bundled with CPQ** — `sbaa__ApprovalChain__c` and related objects do not exist in a CPQ-only org. SOQL on these objects will throw `sObject type 'sbaa__ApprovalChain__c' is not supported` if the package is not installed. Always confirm installation before referencing `sbaa__` objects in code or validation rules.
3. **Standard Quote/QuoteLineItem APIs return empty results in CPQ orgs** — CPQ quotes live on `SBQQ__Quote__c`, not the standard `Quote` object. Apex code or reports querying `SELECT Id FROM Quote` will return zero rows for CPQ-managed quotes. Metadata APIs that reference the standard `Quote` object also cannot read CPQ quote data.
4. **Order activation is the billing trigger — not Order creation** — Creating an Order record does not generate billing schedules. The Order's `Status` must be set to `Activated` and the CPQ field `SBQQ__Contracted__c` must be `true` on the Order for the blng billing trigger to fire. Both conditions must be true simultaneously.
5. **`sbaa__ApprovalRequest__c` status is not reflected in `ProcessInstance`** — Tools that check approval status by querying `ProcessInstance` or `ProcessInstanceWorkitem` (including standard approval-related merge fields) return no records for Advanced Approvals-managed quotes. Approval status must be read from `sbaa__ApprovalRequest__c.sbaa__Status__c`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| CPQ Q2C object chain map | End-to-end diagram mapping SBQQ__Quote__c → SBQQ__QuoteLine__c → Contract → SBQQ__Subscription__c → Order → blng__BillingSchedule__c → blng__Invoice__c with field-level triggers at each transition |
| Advanced Approvals design document | Named chains, rules per tier, conditions per rule, approver sources, and expected runtime sbaa__ApprovalRequest__c chain sequence |
| Contract pivot specification | Fields populated on Contract from Quote, Subscription creation mapping from Quote Lines, start/end date sources |
| Billing configuration checklist | Products with blng__BillingRule__c, billing run schedule, billing schedule type (evergreen vs. fixed term), invoice generation triggers |
| Status transition table | Quote, Order, Contract, Subscription, and Invoice status values and the events that drive each transition |

---

## Related Skills

- `admin/quote-to-cash-requirements` — Standard Sales Cloud Q2C using the standard Quote object — use when CPQ is NOT installed.
- `cpq-data-model` — Detailed field-level reference for SBQQ__ and blng__ objects.
- `cpq-architecture-patterns` — Pricing rules, discount schedules, product configuration, and bundle architecture.
- `cpq-api-and-automation` — CPQ JavaScript API, SBQQ.ServiceRouter, and automation patterns for quote calculation.

---

## Official Sources Used

- Salesforce CPQ Developer Guide — Quote and Order Capture: https://developer.salesforce.com/docs/atlas.en-us.cpq_dev_guide.meta/cpq_dev_guide/cpq_dev_guide.htm
- Revenue Cloud Help — Advanced Approvals: https://help.salesforce.com/s/articleView?id=sf.cpq_advanced_approvals.htm
- Revenue Cloud Help — Contract a Quote: https://help.salesforce.com/s/articleView?id=sf.cpq_contracting_quotes.htm
- Revenue Cloud Help — Billing Schedules: https://help.salesforce.com/s/articleView?id=sf.blng_billing_schedules.htm
- Revenue Cloud Help — Generate Invoices: https://help.salesforce.com/s/articleView?id=sf.blng_invoice_generation.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Object Reference — Contract: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_contract.htm
- Object Reference — Order: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_order.htm
