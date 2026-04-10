---
name: billing-data-reconciliation
description: "Use this skill to investigate, diagnose, and resolve data mismatches across the Salesforce Billing reconciliation chain — from Quote Line through Order, Billing Schedule, Invoice, Invoice Line, and Payment to Payment Allocation. Triggers: 'invoice balance does not match payment received', 'blng__Invoice__c status stuck at Posted despite full payment', 'payment allocated but invoice still shows balance due', 'billing schedule amount differs from order product', 'revenue transaction error log records appearing', 'blng__PaymentAllocation__c not closing invoice', 'reconciling billing data for month-end close', 'invoice to payment mismatch in Salesforce Billing'. NOT for configuring revenue recognition rules or Finance Periods (see admin/revenue-recognition-requirements skill), NOT for setting up billing schedules or invoice runs (see admin/billing-schedule-setup skill), NOT for standard Salesforce Opportunity revenue schedules (unrelated to Salesforce Billing), NOT for CRM reporting or Opportunity close date reconciliation."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Security
triggers:
  - "invoice balance does not match the payment amount received and the invoice remains open in Salesforce Billing"
  - "blng__PaymentAllocation__c records exist but the invoice status has not changed to Paid"
  - "billing schedule amount differs from the order product net price after order activation"
  - "revenue transaction error log records are appearing and I need to identify which invoices are affected"
  - "month-end close requires reconciling all outstanding invoice and payment records in Salesforce Billing"
  - "partial payment was applied but the remaining invoice balance is not visible in the payment allocation"
  - "order item net price does not match the blng__BillingSchedule__c total after order amendment"
tags:
  - billing-data-reconciliation
  - salesforce-billing
  - blng-namespace
  - invoice-reconciliation
  - payment-allocation
  - billing-schedule
  - revenue-transaction-error-log
  - payment-matching
  - month-end-close
  - data-reconciliation
inputs:
  - "Salesforce org with Salesforce Billing managed package (blng__ namespace) installed"
  - "Activated Order with OrderItems sourced from a CPQ Quote or direct order entry"
  - "blng__Invoice__c and blng__InvoiceLine__c records in scope for the reconciliation period"
  - "blng__Payment__c and blng__PaymentAllocation__c records for the period"
  - "blng__BillingSchedule__c records linked to the OrderItems in scope"
  - "Access to the Revenue Transaction Error Log (blng__RevenueTransactionErrorLog__c) object"
  - "Identified date range or set of Order/Invoice Ids for the reconciliation"
outputs:
  - "Root-cause identification for invoice-to-payment discrepancies across the full reconciliation chain"
  - "SOQL queries to surface unallocated payments, open invoices, and orphaned billing schedule records"
  - "Reconciliation decision table mapping each discrepancy type to the correct remediation action"
  - "Step-by-step remediation plan for closing open blng__Invoice__c records after partial payment resolution"
  - "Checklist confirming data integrity across the reconciliation chain before month-end close"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# Billing Data Reconciliation

This skill activates when a practitioner needs to investigate and resolve data mismatches across the Salesforce Billing reconciliation chain — traversing SBQQ__QuoteLine__c → OrderItem → blng__BillingSchedule__c → blng__Invoice__c → blng__InvoiceLine__c → blng__Payment__c → blng__PaymentAllocation__c — and to diagnose failures surfaced in the Revenue Transaction Error Log.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the Salesforce Billing managed package (namespace prefix `blng__`) is installed. All billing reconciliation objects — invoices, payments, billing schedules, payment allocations — live inside this managed package and do not exist in standard Salesforce or CPQ alone.
- Identify the reconciliation scope: is this a single invoice dispute, a batch of invoices for month-end close, or a systemic discrepancy across an order amendment? The scope determines which SOQL path to start with.
- Establish the authoritative source of truth for expected amounts. The canonical amount chain starts at `SBQQ__QuoteLine__c.SBQQ__NetPrice__c`, flows to `OrderItem.TotalPrice`, and is reflected in `blng__BillingSchedule__c.blng__BillingAmount__c`. If these three do not agree, the discrepancy exists upstream of invoicing.
- Confirm whether partial payments are in play. Partial payments in Salesforce Billing require explicit `blng__PaymentAllocation__c` records to reduce invoice balances. An unallocated partial payment does not reduce the invoice balance — the platform does not automatically match payments to invoices.
- Check the Revenue Transaction Error Log (`blng__RevenueTransactionErrorLog__c`) first for any systemic errors before diving into individual record investigation.

---

## Core Concepts

### The Billing Reconciliation Chain

Salesforce Billing connects Quote-to-Cash through a six-level object chain. Every reconciliation investigation must trace discrepancies back through this chain to find the authoritative source of the mismatch:

```
SBQQ__QuoteLine__c           (CPQ Quote Line — the contract price source)
        ↓
OrderItem                    (Order Product — activated, drives billing)
        ↓
blng__BillingSchedule__c     (Billing Schedule — defines when to bill and for how much)
        ↓
blng__Invoice__c             (Invoice — the billed record sent to the customer)
        ↓
blng__InvoiceLine__c         (Invoice Line — per-product line detail on the invoice)
        ↓
blng__Payment__c             (Payment — the customer payment received)
        ↓
blng__PaymentAllocation__c   (Payment Allocation — the explicit link between payment and invoice)
```

A discrepancy at any layer must be traced to the layer above to determine whether the error originated in configuration, in the billing run, in payment entry, or in the allocation step. Do not start remediation at the invoice layer if the billing schedule amount is already wrong — fixing the invoice without fixing the billing schedule produces recurring mismatches.

### Invoice-to-Payment Matching via blng__PaymentAllocation__c

Payment matching in Salesforce Billing is explicit, not automatic. When a `blng__Payment__c` record is received, the platform does not automatically identify which invoice it belongs to and reduce that invoice's balance. The practitioner or the billing operations team must create `blng__PaymentAllocation__c` records linking the payment to one or more invoices.

Key fields on `blng__PaymentAllocation__c`:
- `blng__Invoice__c` — lookup to the invoice being paid
- `blng__Payment__c` — lookup to the payment being applied
- `blng__Amount__c` — the amount of the payment allocated to this invoice

The invoice balance is reduced by the sum of all `blng__PaymentAllocation__c.blng__Amount__c` records linked to it, not by the payment amount alone. An invoice with a `blng__Payment__c` linked directly (without an allocation record) will not show a reduced balance.

### Partial Payments Do Not Auto-Close Invoices

A common production failure: a customer pays 60% of an invoice. The `blng__Payment__c` record is created for the partial amount. A `blng__PaymentAllocation__c` is created linking the payment to the invoice for the partial amount. The invoice balance is reduced — but the invoice status does not change to `Paid` because the remaining 40% is still outstanding.

The invoice remains in `Posted` or `Outstanding` status until the balance reaches zero. This is by design: Salesforce Billing requires full invoice balance retirement for the status to change to `Paid`. Practitioners who expect a partial payment to automatically close an invoice (as some ERP systems do with tolerance rules) will find the invoice perpetually open, distorting month-end AR aging reports.

### Revenue Transaction Error Log

The `blng__RevenueTransactionErrorLog__c` object is the first-look diagnostic for reconciliation failures. It captures errors generated during revenue recognition processing — most commonly:
- Missing `blng__RevenueRecognitionRule__c` on a Product2 when the order activated
- Finance Period gaps that prevented revenue schedule generation
- Revenue schedule generation failures for amended or cancelled orders

Before investigating individual invoice or payment records, run a query against `blng__RevenueTransactionErrorLog__c` filtered to the date range of the discrepancy. Error records here identify which Orders and Products have failed to generate revenue entries, which can cascade into invoice-amount mismatches if the revenue and billing paths diverge.

### Billing Schedule vs Invoice Line Amount Divergence

`blng__BillingSchedule__c` records are created when an order is activated. Each record represents a future billing event with an expected amount. When the billing run executes, it reads the billing schedule and creates `blng__InvoiceLine__c` records. If the billing schedule amount was correct at creation but a contract amendment subsequently changed the order product price, the billing schedule may not have been updated — and the invoice line will reflect the stale billing schedule amount, not the amended order product price.

The divergence pattern is:
1. `OrderItem.TotalPrice` reflects the amended value (correct)
2. `blng__BillingSchedule__c.blng__BillingAmount__c` reflects the pre-amendment value (stale)
3. `blng__InvoiceLine__c.blng__ChargeAmount__c` reflects the stale billing schedule amount (incorrect)

This is not a payment allocation problem — it is a billing schedule data integrity problem that must be corrected upstream before re-running the billing batch.

---

## Common Patterns

### Pattern 1: Open Invoice With Full Payment Received — Allocation Missing

**When to use:** The customer has paid the full invoice amount. The `blng__Payment__c` record exists and the amount matches the invoice total. But the invoice status is still `Posted` and the balance shows as outstanding.

**How it works:**
1. Query `blng__PaymentAllocation__c` where `blng__Invoice__c = '<invoice_id>'`. If no records are returned, no allocation exists.
2. Query `blng__Payment__c` for the customer account to confirm the payment record exists with the correct amount and a `blng__Status__c` of `Posted`.
3. Create a `blng__PaymentAllocation__c` record:
   - `blng__Invoice__c` = the open invoice Id
   - `blng__Payment__c` = the customer payment Id
   - `blng__Amount__c` = the invoice balance amount
4. Confirm the invoice balance drops to zero and the status transitions to `Paid`.

**Why not the alternative:** Simply updating `blng__Invoice__c.blng__Status__c` to `Paid` directly corrupts the AR balance — the system expects allocation records to drive the status transition, and a manual status update bypasses the payment trail.

### Pattern 2: Partial Payment — Invoice Remains Open After Allocation

**When to use:** A partial payment has been allocated but the invoice remains in `Posted` status. Finance wants to know whether to write off the remaining balance or await a second payment.

**How it works:**
1. Query `blng__PaymentAllocation__c` to confirm the partial allocation exists and the `blng__Amount__c` is less than the invoice total.
2. Confirm `blng__Invoice__c.blng__Balance__c` reflects the remaining amount after the partial allocation.
3. If a second payment is expected: record a new `blng__Payment__c` for the remaining amount when received, then create a second `blng__PaymentAllocation__c` for the balance.
4. If the remaining balance is to be written off: create a Credit Memo or adjustment record per the org's write-off process (finance policy-dependent; Salesforce Billing does not auto-write-off partial balances).

**Why not the alternative:** Do not delete the partial `blng__PaymentAllocation__c` and replace it with a full-amount allocation record — this overstates the payment applied and creates an audit discrepancy in the payment register.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Invoice open, payment received, no allocation | Create blng__PaymentAllocation__c linking payment to invoice | Allocation is required; payment alone does not close the invoice |
| Invoice open, partial payment allocated, remainder outstanding | Leave invoice open; await second payment or initiate write-off process | Platform requires full balance retirement; partial allocation is correct behavior |
| Billing schedule amount wrong after amendment | Correct the blng__BillingSchedule__c upstream; do not edit invoice lines directly | Invoice lines are derived from billing schedules; fixing downstream leaves the schedule stale |
| Revenue Transaction Error Log shows errors for a period | Identify affected Orders/Products; correct the root cause (missing rule, Finance Period gap) before re-running billing | Error log errors cascade into invoice mismatches if ignored |
| Invoice line amount differs from order product price | Trace OrderItem → blng__BillingSchedule__c → blng__InvoiceLine__c; find where the divergence starts | Amendment may have updated OrderItem but not the billing schedule |
| Multiple payments against one invoice | Create one blng__PaymentAllocation__c per payment; sum of allocations should equal invoice total | Platform sums all allocation records to determine invoice balance |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Check the Revenue Transaction Error Log first** — Query `blng__RevenueTransactionErrorLog__c` for the date range of the discrepancy. Any errors here indicate systemic reconciliation failures (missing rules, Finance Period gaps) that affect multiple records. Address these before investigating individual invoices, or the individual fixes will be invalidated when the underlying issue recurs.

2. **Establish the authoritative amount chain** — For each Order in scope, trace `SBQQ__QuoteLine__c.SBQQ__NetPrice__c` → `OrderItem.TotalPrice` → `blng__BillingSchedule__c.blng__BillingAmount__c` → `blng__InvoiceLine__c.blng__ChargeAmount__c`. Record the value at each layer and identify where the first divergence appears. This is the root cause layer.

3. **Audit payment allocation records** — For each invoice in scope, query `blng__PaymentAllocation__c WHERE blng__Invoice__c = :invoiceId`. Sum `blng__Amount__c` across all allocation records and compare to `blng__Invoice__c.blng__TotalAmount__c`. If the sum is less than the invoice total and a payment record exists for the shortfall amount, a missing allocation is the cause of the open invoice.

4. **Verify blng__Payment__c status** — Confirm each `blng__Payment__c` in scope has a `blng__Status__c` of `Posted` and that `blng__UnallocatedAmount__c` is zero if full allocation is expected. A payment with a positive `blng__UnallocatedAmount__c` has funds available that have not been applied to any invoice.

5. **Remediate at the correct layer** — Create or correct `blng__PaymentAllocation__c` records for payment matching issues. Correct `blng__BillingSchedule__c` records for billing amount discrepancies. Do not edit `blng__Invoice__c` or `blng__InvoiceLine__c` records directly — they are system-generated and must be regenerated from corrected upstream data.

6. **Confirm invoice status transitions** — After remediation, confirm that invoices with zero balance have transitioned to `Paid` status. Invoices with partial balances should remain in `Posted` status — this is correct behavior, not an error.

7. **Document and validate before month-end close** — Run a final SOQL check across all in-scope accounts: confirm no `blng__Invoice__c` records exist with `blng__Balance__c > 0` and an associated `blng__Payment__c` that covers the balance but lacks a `blng__PaymentAllocation__c`. Produce a reconciliation summary for Finance sign-off.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Revenue Transaction Error Log queried for the reconciliation period; all errors have been investigated and root causes documented
- [ ] Amount chain verified: SBQQ__QuoteLine__c → OrderItem → blng__BillingSchedule__c → blng__InvoiceLine__c amounts agree for all in-scope orders
- [ ] blng__PaymentAllocation__c records exist for every blng__Payment__c that should reduce an invoice balance
- [ ] Sum of blng__PaymentAllocation__c.blng__Amount__c equals blng__Invoice__c.blng__TotalAmount__c for all invoices expected to be fully paid
- [ ] No blng__Payment__c records with blng__UnallocatedAmount__c > 0 exist for the reconciliation period unless unallocated funds are intentional
- [ ] All fully paid invoices show blng__Status__c = 'Paid'
- [ ] Invoices with partial payments show the correct remaining blng__Balance__c and remain in 'Posted' status (expected behavior)
- [ ] No invoice or invoice line records were directly edited; all corrections went through upstream billing schedule or payment allocation objects

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Unallocated partial payments do not auto-close invoices** — When a customer pays a partial amount and a `blng__PaymentAllocation__c` is created for that partial amount, the invoice balance is reduced but the status remains `Posted`. Salesforce Billing requires the full balance to reach zero before the status transitions to `Paid`. Orgs that expect tolerance-based auto-closure (as some ERP systems provide) will find invoices perpetually open in AR aging until every cent is allocated.
2. **Missing blng__RevenueRecognitionRule__c produces silent revenue entries** — If a Product2 has no Revenue Recognition Rule at the time an Order is activated, the Billing engine skips revenue schedule generation without throwing an error. The invoice is still generated correctly, but the revenue side of the ledger shows no entries. This creates a billing-revenue reconciliation mismatch that only surfaces at period close when the GL shows invoiced amounts with no corresponding earned revenue entries. The Revenue Transaction Error Log captures this failure.
3. **Revenue Transaction Error Log is the first-look diagnostic** — Many practitioners skip the `blng__RevenueTransactionErrorLog__c` object and go directly to invoice or payment records. This wastes time: the error log often identifies a systemic root cause (missing rule, Finance Period gap, cancelled order with open schedule) that explains dozens of individual discrepancies at once.
4. **Direct edits to blng__InvoiceLine__c corrupt the billing audit trail** — Invoice line records are system-generated from billing schedule data. Editing `blng__ChargeAmount__c` directly via Data Loader or Apex updates the invoice line but does not update the billing schedule, creating a permanent divergence between the two. If the billing batch is re-run or the invoice is regenerated, the edit is overwritten. All amount corrections must go through `blng__BillingSchedule__c`.
5. **blng__PaymentAllocation__c deletion does not restore payment availability automatically** — If a payment allocation is deleted, the `blng__Payment__c.blng__UnallocatedAmount__c` must be recalculated. In some Billing package versions, the unallocated amount does not immediately reflect the freed funds. Confirm `blng__UnallocatedAmount__c` after any allocation deletion before creating a replacement allocation.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| SOQL reconciliation queries | Queries traversing the billing chain to surface mismatches at each layer |
| Payment allocation gap report | List of blng__Invoice__c records with balance > 0 and unallocated blng__Payment__c records available |
| Amount chain audit | Table comparing expected vs. actual amounts at each layer of the reconciliation chain |
| Remediation plan | Ordered list of blng__PaymentAllocation__c records to create or billing schedules to correct |

---

## Related Skills

- `admin/billing-schedule-setup` — Configure billing schedules and invoice runs; use when the discrepancy originates at the billing schedule layer
- `admin/revenue-recognition-requirements` — Configure revenue recognition rules and Finance Periods; use when Revenue Transaction Error Log errors indicate missing recognition configuration
- `apex/billing-integration-apex` — Custom Apex for payment gateway and billing lifecycle automation; use when payment allocation errors trace to a custom gateway implementation
- `data/bulk-api-patterns` — Use when the reconciliation remediation requires bulk creation or update of PaymentAllocation records at scale

## Official Sources Used

- Invoice-Based Revenue Recognition Reporting — https://help.salesforce.com/s/articleView?id=sf.blng_invoice_based_revenue_recognition_reporting.htm&type=5
- Understanding Revenue Recognition Process — https://help.salesforce.com/s/articleView?id=sf.blng_understanding_the_revenue_recognition_process.htm&type=5
- Billing Invoice Data Model — Revenue Cloud Data Model Gallery — https://developer.salesforce.com/docs/revenue/revenue-cloud/guide/blng-invoice-data-model.html
