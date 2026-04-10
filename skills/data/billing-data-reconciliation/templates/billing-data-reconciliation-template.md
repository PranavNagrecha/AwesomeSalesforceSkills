# Billing Data Reconciliation — Work Template

Use this template when investigating or resolving data mismatches in the Salesforce Billing reconciliation chain.

---

## Scope

**Skill:** `billing-data-reconciliation`

**Request summary:** (describe the reconciliation issue or task — e.g., "Invoice INV-00123 shows balance due despite full payment received", "Month-end close — reconcile all outstanding invoices for Account XYZ")

**Date range in scope:**

**Accounts in scope (if account-specific):**

**Order Ids in scope (if known):**

---

## Step 1: Revenue Transaction Error Log Check

Run this query before investigating any individual records:

```soql
SELECT Id, blng__ErrorMessage__c, blng__Order__c, blng__OrderProduct__c, CreatedDate
FROM blng__RevenueTransactionErrorLog__c
WHERE CreatedDate >= :startDate AND CreatedDate <= :endDate
ORDER BY CreatedDate DESC
```

**Error log findings:**
- [ ] No errors found — proceed to amount chain audit
- [ ] Errors found — document below and resolve before proceeding

| Error Record Id | Error Message | Affected Order | Affected OrderProduct |
|---|---|---|---|
| | | | |

**Root cause of errors (if any):**

**Resolution taken:**

---

## Step 2: Amount Chain Audit

For each Order in scope, complete the chain below. All amounts should agree. Document any divergence.

| Order Id | SBQQ__QuoteLine__c NetPrice | OrderItem TotalPrice | blng__BillingSchedule__c BillingAmount | blng__InvoiceLine__c ChargeAmount | Divergence Layer |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |
| | | | | | |

**Notes on divergences found:**

---

## Step 3: Invoice and Payment Allocation Audit

For each invoice in scope:

```soql
SELECT Id, Name, blng__TotalAmount__c, blng__Balance__c, blng__Status__c, blng__Account__c
FROM blng__Invoice__c
WHERE Id IN (:invoiceIds)
```

```soql
SELECT Id, blng__Invoice__c, blng__Payment__c, blng__Amount__c
FROM blng__PaymentAllocation__c
WHERE blng__Invoice__c IN (:invoiceIds)
```

**Allocation audit findings:**

| Invoice Id | Invoice Total | Sum of Allocations | Balance | Status | Missing Allocation? |
|---|---|---|---|---|---|
| | | | | | Yes / No |
| | | | | | Yes / No |

---

## Step 4: Unallocated Payment Check

```soql
SELECT Id, Name, blng__Amount__c, blng__UnallocatedAmount__c, blng__Status__c, blng__Account__c
FROM blng__Payment__c
WHERE blng__Account__c IN (:accountIds)
  AND blng__Status__c = 'Posted'
  AND blng__UnallocatedAmount__c > 0
```

**Unallocated payments found:**

| Payment Id | Payment Amount | Unallocated Amount | Account |
|---|---|---|---|
| | | | |

---

## Step 5: Remediation Plan

Document the specific actions to take, in order:

| # | Action | Object | Record Id | Amount | Responsible |
|---|---|---|---|---|---|
| 1 | Create PaymentAllocation | blng__PaymentAllocation__c | | | |
| 2 | Correct BillingSchedule amount | blng__BillingSchedule__c | | | |
| 3 | Issue credit memo | blng__CreditMemo__c | | | |

**Remediation notes:**

---

## Step 6: Post-Remediation Verification

Run these checks after remediation is complete:

- [ ] All targeted invoices with zero balance show `blng__Status__c = 'Paid'`
- [ ] All `blng__Payment__c` records that should be fully allocated show `blng__UnallocatedAmount__c = 0`
- [ ] No new `blng__RevenueTransactionErrorLog__c` records created during remediation
- [ ] Amount chain re-audited for all corrected records — all layers agree
- [ ] Finance sign-off obtained for month-end close (if applicable)

**Verification notes:**

---

## Decisions and Deviations

Record any decisions made that deviate from the standard workflow in SKILL.md, and the reason:

| Decision | Reason | Approved By |
|---|---|---|
| | | |

---

## References

- Skill: `data/billing-data-reconciliation`
- Gotchas: `skills/data/billing-data-reconciliation/references/gotchas.md`
- Examples: `skills/data/billing-data-reconciliation/references/examples.md`
- Official: https://help.salesforce.com/s/articleView?id=sf.blng_invoice_based_revenue_recognition_reporting.htm&type=5
- Official: https://developer.salesforce.com/docs/revenue/revenue-cloud/guide/blng-invoice-data-model.html
