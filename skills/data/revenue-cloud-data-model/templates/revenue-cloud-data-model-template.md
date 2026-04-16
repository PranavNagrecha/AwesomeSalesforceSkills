# Revenue Cloud Data Model — Work Template

## Scope

**Skill:** `revenue-cloud-data-model`

**Request summary:** (fill in: SOQL query, ERP integration, billing reconciliation, or data model question)

## Product Confirmation

- **Product:** [ ] Native RLM (standard objects: BillingSchedule, Invoice, Payment, FinanceTransaction)
  [ ] Salesforce Billing managed package (blng__* objects — use billing-data-reconciliation skill instead)
- **API version:** [ ] v55.0+ (required for BillingSchedule)

## Object Hierarchy Context

```
Order → OrderItem → BillingSchedule → BillingScheduleGroup → Invoice → InvoiceLine
                                                          └→ FinanceTransaction (read-only)
Payment → PaymentLineInvoice → Invoice
```

## Query Requirements

- **Target object(s):** (BillingSchedule / Invoice / Payment / FinanceTransaction)
- **Relationship traversal needed?** (e.g., OrderItem.OrderId for BillingSchedule)
- **Amendment reconciliation needed?** [ ] Yes — aggregate all BillingSchedule records per asset

## FinanceTransaction Access

- **Access type:** [ ] Read-only SELECT  [ ] DML — NOT allowed, DML will fail
- **Purpose:** [ ] ERP export  [ ] Accounting reconciliation

## Checklist

- [ ] Product confirmed as native RLM (not Salesforce Billing managed package)
- [ ] API version set to v55.0+ for BillingSchedule access
- [ ] Standard API object names used (BillingSchedule, not blng__BillingSchedule__c)
- [ ] FinanceTransaction accessed read-only — no DML
- [ ] Amendment history accounted for — not LIMIT 1 on BillingSchedule
- [ ] BillingSchedule filtered via OrderItemId (not OrderId directly)

## Notes

(Record ERP field mapping, amendment aggregation strategy, reconciliation approach)
