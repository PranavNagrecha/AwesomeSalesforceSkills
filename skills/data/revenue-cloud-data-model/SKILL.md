---
name: revenue-cloud-data-model
description: "Use this skill when querying, integrating with, or troubleshooting the native Salesforce Revenue Cloud (RLM) data model — including BillingSchedule, BillingScheduleGroup, Invoice, InvoiceLine, Payment, PaymentLineInvoice, and FinanceTransaction standard objects and their relationships. Triggers on: Revenue Cloud object relationships, BillingSchedule data model, native Revenue Cloud SOQL, FinanceTransaction object, Invoice object Revenue Cloud, PaymentLineInvoice relationship. NOT for the legacy Salesforce Billing managed package data model (blng__BillingSchedule__c, blng__Invoice__c — use billing-data-reconciliation skill for that), not for CPQ data model (SBQQ__* objects)."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
tags:
  - revenue-cloud
  - rlm
  - data-model
  - billing-schedule
  - invoice
  - payment
  - finance-transaction
  - billing-schedule-group
  - order-to-cash
inputs:
  - "Revenue Cloud (RLM) enabled Salesforce org"
  - "Activated Order with OrderItem records"
  - "BillingSchedule records created via Connect API"
outputs:
  - "Data model diagram: BillingSchedule → BillingScheduleGroup → Invoice → FinanceTransaction"
  - "SOQL queries for Revenue Cloud billing and payment objects"
  - "FinanceTransaction read-only ledger access pattern"
  - "Amendment billing reconciliation query across multiple BillingSchedule records"
triggers:
  - "BillingSchedule object SOQL Revenue Cloud"
  - "FinanceTransaction DML fails native Revenue Cloud"
  - "Invoice to Order relationship Revenue Cloud data model"
  - "BillingSchedule linked to OrderItem not Order"
  - "native Revenue Cloud vs blng managed package objects"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# Revenue Cloud Data Model

This skill activates when a practitioner needs to understand or query the native Salesforce Revenue Cloud (RLM) data model — the standard objects exposed for billing, invoicing, payment, and accounting. It does NOT cover the legacy Salesforce Billing managed package (blng__* namespace) or CPQ (SBQQ__*) objects — those are separate products with separate data models.

---

## Before Starting

Gather this context before working on anything in this domain:

- Native Revenue Cloud (RLM) uses **standard Salesforce objects** with standard API names: `BillingSchedule`, `Invoice`, `Payment`, `FinanceTransaction`. These are NOT the same as the managed-package objects: `blng__BillingSchedule__c`, `blng__Invoice__c`, `blng__Payment__c`.
- `BillingSchedule` is available from **API v55.0+**. Orgs on older API versions cannot access it.
- `FinanceTransaction` is a **read-only** accounting journal entry object — it cannot be created, updated, or deleted via API. It is system-generated when an Invoice is posted or a Payment is received.

---

## Core Concepts

### Object Hierarchy: Order to Revenue

The Revenue Cloud (RLM) data model follows this primary hierarchy:

```
Order
 └─ OrderItem
     └─ BillingSchedule (created via Connect API POST after order activation)
         └─ BillingScheduleGroup (aggregates multiple BillingSchedules for Invoice grouping)
             └─ Invoice
                 └─ InvoiceLine
                     └─ PaymentLineInvoice (junction between Invoice and Payment)
                 └─ FinanceTransaction (read-only accounting journal entry)
Payment
 └─ PaymentLineInvoice
```

### BillingSchedule Object

`BillingSchedule` (API v55.0+) represents the billing timeline for a single `OrderItem`. It stores:
- Billing start and end dates
- Billing frequency (Monthly, Quarterly, Annual)
- Amount per period
- Parent `OrderItem` ID

BillingSchedules are NOT auto-created on order activation — they must be explicitly created via Connect API POST. Each asset amendment order creates a NEW BillingSchedule record (it does not update the existing one).

### BillingScheduleGroup

`BillingScheduleGroup` aggregates multiple `BillingSchedule` records for invoice grouping purposes. The grouping logic determines which billing schedule lines appear on a single Invoice. This is the object that drives Invoice generation.

### Invoice and InvoiceLine

`Invoice` represents the billing document sent to the customer. Each Invoice can have multiple `InvoiceLine` records corresponding to individual billing schedule periods. Invoice posting creates a `FinanceTransaction` (accounting journal entry).

### Payment and PaymentLineInvoice

`Payment` records track customer payments received. `PaymentLineInvoice` is a junction object linking a Payment to one or more Invoices it covers (partial payment support).

### FinanceTransaction (Read-Only Ledger)

`FinanceTransaction` records are system-generated read-only accounting journal entries. They are created automatically when:
- An Invoice is posted (creates revenue recognition entries)
- A Payment is received (creates cash receipt entries)

They cannot be created, updated, or deleted via Apex DML or REST API. Any code attempting to DML a FinanceTransaction will throw a system exception.

---

## Common Patterns

### Pattern 1: Query All Billing Schedules for an Order

**When to use:** Audit or integration requiring all billing timeline records for a given order.

```sql
SELECT Id, OrderItemId, StartDate, EndDate, Status, BillingFrequency, Amount,
       BillingScheduleGroupId, CreatedDate
FROM BillingSchedule
WHERE OrderItem.OrderId = 'order_id_here'
ORDER BY StartDate ASC
```

**Why this query:** BillingSchedule has a lookup to OrderItem, not directly to Order. Use the relationship traversal `OrderItem.OrderId` to filter by Order.

### Pattern 2: Trace Invoice to Finance Transactions

**When to use:** Accounting integration requiring the journal entries generated by an invoice.

```sql
SELECT Id, InvoiceId, TransactionType, Amount, AccountingPeriodId, CreatedDate
FROM FinanceTransaction
WHERE InvoiceId = 'invoice_id_here'
```

**Why not DML FinanceTransaction:** These are read-only system records. Accounting integrations must read them, not write to them. Write accounting data to your external ERP, not back into FinanceTransaction.

### Pattern 3: Reconcile Billing Schedules Across Asset Amendments

**When to use:** An asset has been amended multiple times, each creating a new BillingSchedule. Aggregate all schedules for total billed amount.

```sql
SELECT OrderItem.Product2Id,
       SUM(Amount) totalBilled,
       COUNT(Id) scheduleCount
FROM BillingSchedule
WHERE OrderItem.Order.AccountId = 'account_id'
  AND Status = 'Active'
GROUP BY OrderItem.Product2Id
```

**Why needed:** Each amendment creates a new BillingSchedule rather than updating the existing one. Without aggregation, the billing picture appears fragmented.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Query billing schedules | SELECT from BillingSchedule (standard API name) | RLM uses standard objects, not blng__* |
| Create billing schedule via code | Connect API POST, not DML | BillingSchedules require Connect API — direct DML may not work for all fields |
| Read accounting journal entries | SELECT from FinanceTransaction | Read-only — no DML allowed |
| Legacy Salesforce Billing data model | billing-data-reconciliation skill | Separate product, different object names |
| Invoice grouping logic | Examine BillingScheduleGroup configuration | Controls which billing lines appear on a single Invoice |

---

## Recommended Workflow

1. Confirm the org uses native Revenue Cloud (RLM), not CPQ + Salesforce Billing — verify by checking for standard `BillingSchedule` object (not `blng__BillingSchedule__c`) in the object list.
2. Verify API version is v55.0+ in org settings — `BillingSchedule` is not accessible in earlier API versions.
3. Map the object hierarchy: Order → OrderItem → BillingSchedule → BillingScheduleGroup → Invoice → InvoiceLine → FinanceTransaction.
4. For queries: use standard Salesforce SOQL with the standard API object names.
5. For billing integration: read BillingSchedule and Invoice records via REST or SOQL; publish to ERP via outbound callout or Platform Events.
6. For FinanceTransaction: read only. Never attempt DML. Reconcile FinanceTransaction data with ERP on read.
7. For amendment reconciliation: aggregate BillingSchedule by Product2Id and AccountId to get total billed amount across lifecycle.

---

## Review Checklist

- [ ] Org confirmed as native Revenue Cloud (RLM) — not Salesforce Billing managed package
- [ ] API version set to v55.0+ for BillingSchedule access
- [ ] SOQL uses standard API names (BillingSchedule, not blng__BillingSchedule__c)
- [ ] FinanceTransaction access is read-only — no DML attempted
- [ ] Amendment billing aggregation accounts for multiple BillingSchedule records per asset
- [ ] PaymentLineInvoice junction queried for partial payment scenarios
- [ ] No blng__* or SBQQ__* objects referenced in RLM queries or code

---

## Salesforce-Specific Gotchas

1. **Standard Object Names vs. Managed Package Names** — The most common error is writing SOQL against `blng__BillingSchedule__c` in an RLM org (or the reverse). `BillingSchedule` (standard) and `blng__BillingSchedule__c` (managed package) are completely different objects. SOQL that targets the wrong object returns zero results or a "no such column" error.

2. **FinanceTransaction Cannot Be DML'd** — Any Apex or API attempt to insert, update, or delete a FinanceTransaction throws a system exception. These are system-generated read-only ledger records. Accounting integrations must export FinanceTransaction data to ERP — they cannot write back.

3. **BillingSchedule Requires API v55.0+** — If code targets an older API version (e.g., v51.0), the BillingSchedule object is not accessible. This causes describe calls to return null and SOQL to fail with "object not found" errors. Always verify API version compatibility.

4. **Amendment Creates New BillingSchedule, Not Update** — When an asset amendment order is activated, a new BillingSchedule record is created for the amendment period. The original BillingSchedule is NOT updated. Queries that look only at the latest BillingSchedule for an OrderItem will miss historical billing periods from earlier lifecycles.

5. **BillingScheduleGroup Controls Invoice Grouping** — Invoice generation is driven by BillingScheduleGroup, not directly by BillingSchedule. If multiple billing schedules should appear on a single invoice, they must be assigned to the same BillingScheduleGroup. Misconfiguration results in separate invoices per billing schedule line.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Revenue Cloud data model diagram | Visual: Order → OrderItem → BillingSchedule → BillingScheduleGroup → Invoice → FinanceTransaction |
| SOQL query library | Queries for BillingSchedule, Invoice, FinanceTransaction, PaymentLineInvoice with correct API names |
| Amendment reconciliation query | Aggregation of BillingSchedule records across asset lifecycle for correct total billing view |
| ERP integration data map | Field mapping from Revenue Cloud standard objects to common ERP schemas |

---

## Related Skills

- revenue-lifecycle-management — for DRO fulfillment and order-to-cash workflow using these objects
- revenue-cloud-architecture — for architectural design of the full order-to-cash domain
- billing-data-reconciliation — for legacy Salesforce Billing managed package (blng__*) data model
