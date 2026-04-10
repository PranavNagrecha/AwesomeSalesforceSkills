# LLM Anti-Patterns — Billing Data Reconciliation

Common mistakes AI coding assistants make when generating or advising on Salesforce Billing data reconciliation.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Suggesting Direct Status Update on blng__Invoice__c to Close Open Invoices

**What the LLM generates:** Advice to close an open invoice by setting `blng__Invoice__c.blng__Status__c = 'Paid'` directly via Apex, Data Loader, or the UI when a payment has been received.

**Why it happens:** LLMs trained on general CRM patterns know that "updating a status field" is a common way to mark records as complete. They apply this pattern to Salesforce Billing without knowing that invoice status is derived from the payment allocation balance, not directly editable in a reconciliation-valid way.

**Correct pattern:**

```apex
// WRONG — direct status update bypasses allocation trail
blng__Invoice__c inv = [SELECT Id FROM blng__Invoice__c WHERE Id = :invoiceId];
inv.blng__Status__c = 'Paid';
update inv;

// CORRECT — create the allocation record; status transitions automatically
blng__PaymentAllocation__c alloc = new blng__PaymentAllocation__c(
    blng__Invoice__c = invoiceId,
    blng__Payment__c = paymentId,
    blng__Amount__c  = invoiceBalance
);
insert alloc;
// Invoice status transitions to 'Paid' after blng__Balance__c reaches zero
```

**Detection hint:** Look for `blng__Status__c` being set directly on `blng__Invoice__c` in any DML statement. If the code updates invoice status without a corresponding `blng__PaymentAllocation__c` insert, flag it.

---

## Anti-Pattern 2: Treating blng__Payment__c as Automatically Linked to blng__Invoice__c

**What the LLM generates:** A description or code that assumes recording a `blng__Payment__c` against a customer account automatically reduces the balance of any open invoices for that account. For example: "Once the payment is created, the invoice will be marked as paid."

**Why it happens:** Many ERP systems and AR platforms perform automatic payment-to-invoice matching by account and amount. LLMs trained on general finance system documentation assume this is the default behavior. Salesforce Billing's explicit allocation model — which requires a separate `blng__PaymentAllocation__c` record — is a non-obvious departure from this norm.

**Correct pattern:**

```
Payment received → blng__Payment__c record created (blng__UnallocatedAmount__c = full amount)
        ↓
Explicit allocation step required
        ↓
blng__PaymentAllocation__c record created (blng__Invoice__c, blng__Payment__c, blng__Amount__c)
        ↓
Invoice blng__Balance__c reduced by allocation amount
        ↓
If blng__Balance__c = 0 → invoice status transitions to Paid
```

**Detection hint:** Any response that says a payment "closes" or "pays" an invoice without mentioning `blng__PaymentAllocation__c` is missing the explicit allocation step.

---

## Anti-Pattern 3: Advising Direct Edit of blng__InvoiceLine__c to Correct Billing Amounts

**What the LLM generates:** Instructions to correct an invoice amount discrepancy by directly editing `blng__InvoiceLine__c.blng__ChargeAmount__c` (or the parent `blng__Invoice__c.blng__TotalAmount__c`) via Data Loader or Apex.

**Why it happens:** LLMs default to "find the wrong field value, update it" as a generic data correction pattern. They do not know that invoice line records in Salesforce Billing are system-generated from billing schedule data and that direct edits create a divergence that is overwritten by the next billing run.

**Correct pattern:**

```
WRONG approach:
  blng__InvoiceLine__c.blng__ChargeAmount__c = amended_amount  // edited directly

CORRECT approach:
  1. Identify the blng__BillingSchedule__c record for the affected OrderProduct
  2. Correct blng__BillingSchedule__c.blng__BillingAmount__c to the amended amount
  3. Issue a credit memo against the incorrect invoice via Salesforce Billing credit memo process
  4. Regenerate a corrected invoice from the updated billing schedule
```

**Detection hint:** Any DML update targeting `blng__InvoiceLine__c.blng__ChargeAmount__c` or `blng__Invoice__c.blng__TotalAmount__c` outside of a system-managed billing process should be flagged.

---

## Anti-Pattern 4: Skipping the Revenue Transaction Error Log in Reconciliation Advice

**What the LLM generates:** A billing reconciliation investigation workflow that starts with `blng__Invoice__c`, `blng__InvoiceLine__c`, or `blng__Payment__c` queries, without first checking `blng__RevenueTransactionErrorLog__c`.

**Why it happens:** The Revenue Transaction Error Log is a Billing-package-specific diagnostic object that LLMs frequently overlook. It is not a standard Salesforce object and does not appear in generic Salesforce troubleshooting guidance. LLMs default to the objects they know well (Invoice, Payment) rather than the error log that would immediately identify the root cause.

**Correct pattern:**

```soql
-- ALWAYS start reconciliation with the error log for the affected period
SELECT Id, blng__ErrorMessage__c, blng__Order__c, blng__OrderProduct__c, CreatedDate
FROM blng__RevenueTransactionErrorLog__c
WHERE CreatedDate = THIS_MONTH
ORDER BY CreatedDate DESC

-- If error records exist, address root causes before investigating individual invoices.
-- Error records often explain dozens of individual discrepancies with a single root cause.
```

**Detection hint:** Any reconciliation investigation workflow that does not include a `blng__RevenueTransactionErrorLog__c` query as the first step is incomplete for Salesforce Billing orgs.

---

## Anti-Pattern 5: Assuming blng__BillingSchedule__c Auto-Updates After Order Amendment

**What the LLM generates:** An amendment workflow that activates an amendment order and then proceeds directly to the next billing run, assuming the billing schedule amounts will reflect the amended order product prices.

**Why it happens:** LLMs that know Salesforce CPQ and Order Management correctly understand that amendment orders update OrderItem records. They incorrectly extend this to assume that downstream billing schedules are also updated. The billing engine creates a new delta billing schedule for the amendment OrderProduct, but the original billing schedule for the pre-amendment OrderProduct remains unchanged.

**Correct pattern:**

```soql
-- After activating any amendment order, verify billing schedule amounts
SELECT Id, blng__OrderProduct__c, blng__BillingAmount__c,
       blng__OrderProduct__r.TotalPrice
FROM blng__BillingSchedule__c
WHERE blng__OrderProduct__c IN (
    SELECT Id FROM OrderItem WHERE OrderId = :amendmentOrderId
)
-- Compare blng__BillingAmount__c to blng__OrderProduct__r.TotalPrice
-- If they differ, correct the billing schedule before the next billing run.
```

**Detection hint:** Any amendment workflow that activates the amendment order and immediately proceeds to billing without verifying `blng__BillingSchedule__c.blng__BillingAmount__c` against `OrderItem.TotalPrice` is missing the billing schedule verification step.

---

## Anti-Pattern 6: Confusing blng__RevenueSchedule__c with blng__BillingSchedule__c

**What the LLM generates:** SOQL queries or remediation advice that conflates `blng__BillingSchedule__c` (controls when invoices are generated and for how much) with `blng__RevenueSchedule__c` (controls how revenue is recognized across Finance Periods). The LLM may suggest querying or correcting `blng__RevenueSchedule__c` when investigating an invoice amount discrepancy — which is the wrong object for that problem.

**Why it happens:** Both objects use the `blng__` namespace, both have "Schedule" in the name, and both relate to OrderProducts. LLMs that do not have deep Salesforce Billing training conflate them because they look structurally similar in SOQL.

**Correct pattern:**

```
blng__BillingSchedule__c  →  Controls billing events → drives blng__Invoice__c generation
blng__RevenueSchedule__c  →  Controls revenue recognition → drives blng__RevenueTransaction__c GL events

Invoice amount discrepancy? → Investigate blng__BillingSchedule__c
Revenue GL entry missing?   → Investigate blng__RevenueSchedule__c and blng__RevenueTransactionErrorLog__c
```

**Detection hint:** If the LLM references `blng__RevenueSchedule__c` in the context of an invoice balance or payment allocation problem, it has conflated the two schedule objects. Check that the correct schedule object is referenced for the problem domain.
