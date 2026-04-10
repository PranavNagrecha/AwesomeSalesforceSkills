# Examples — Billing Data Reconciliation

## Example 1: Invoice Remains Open After Full Payment Received — Missing Payment Allocation

**Context:** A SaaS customer pays the full amount of an annual invoice ($12,000). The accounts receivable team records the payment in Salesforce Billing as a `blng__Payment__c` with `blng__Status__c = Posted` and `blng__Amount__c = 12000`. Two days later, the invoice still shows `blng__Status__c = Posted` and `blng__Balance__c = 12000`. Finance escalates because the AR aging report shows the invoice as fully overdue despite the confirmed payment.

**Problem:** No `blng__PaymentAllocation__c` record was created. The payment exists in the system but is not linked to the invoice. Salesforce Billing does not auto-match payments to invoices — the link must be explicit. Without the allocation record, the invoice balance does not change.

**Solution:**

```soql
-- Step 1: Find the open invoice and the unallocated payment
SELECT Id, Name, blng__TotalAmount__c, blng__Balance__c, blng__Status__c
FROM blng__Invoice__c
WHERE blng__Account__c = '001xxxxxxxxxxxxxxx'
  AND blng__Status__c = 'Posted'
  AND blng__Balance__c > 0

SELECT Id, Name, blng__Amount__c, blng__UnallocatedAmount__c, blng__Status__c
FROM blng__Payment__c
WHERE blng__Account__c = '001xxxxxxxxxxxxxxx'
  AND blng__Status__c = 'Posted'
  AND blng__UnallocatedAmount__c > 0
```

```soql
-- Step 2: Confirm no allocation exists for the invoice
SELECT Id, blng__Amount__c, blng__Payment__c
FROM blng__PaymentAllocation__c
WHERE blng__Invoice__c = 'a1Bxxxxxxxxxxxxxxx'
-- If no records returned, allocation is missing.
```

```apex
// Step 3: Create the allocation record
blng__PaymentAllocation__c alloc = new blng__PaymentAllocation__c(
    blng__Invoice__c   = 'a1Bxxxxxxxxxxxxxxx',   // Invoice Id
    blng__Payment__c   = 'a2Cxxxxxxxxxxxxxxx',   // Payment Id
    blng__Amount__c    = 12000.00                 // Full invoice balance
);
insert alloc;

// Step 4: Verify invoice status transition
blng__Invoice__c inv = [
    SELECT blng__Balance__c, blng__Status__c
    FROM blng__Invoice__c
    WHERE Id = 'a1Bxxxxxxxxxxxxxxx'
];
System.debug('Balance: ' + inv.blng__Balance__c);    // Expected: 0
System.debug('Status: '  + inv.blng__Status__c);     // Expected: Paid
```

**Why it matters:** Payment allocation is the only mechanism that reduces an invoice balance in Salesforce Billing. A payment without an allocation is invisible to the invoice. This is the most common cause of "invoice open despite payment received" in Salesforce Billing orgs, and it is trivially fixed once the root cause is identified. Skipping the allocation step and instead manually setting `blng__Status__c = Paid` on the invoice will corrupt the AR balance because the payment will remain unallocated (with `blng__UnallocatedAmount__c = 12000`) while the invoice shows as paid — double-counting the cash.

---

## Example 2: Revenue Transaction Error Log Reveals Silent Revenue Failure Causing Billing Reconciliation Gap

**Context:** During month-end close, the Finance team notices that 15 invoices from the previous billing run show correct amounts in `blng__Invoice__c` but the corresponding revenue entries in `blng__RevenueTransaction__c` are missing. The total gap is $180,000 in earned revenue that should have been posted to the GL. The billing operations team starts investigating individual invoice records and finds no obvious problem.

**Problem:** The root cause is upstream: the 15 affected Product2 records were missing `blng__RevenueRecognitionRule__c` lookups at the time the orders were activated. The Billing engine generated invoices correctly (billing and revenue recognition are separate processes) but silently skipped revenue schedule generation. The Revenue Transaction Error Log captured these failures, but no one checked it.

**Solution:**

```soql
-- Step 1: Check Revenue Transaction Error Log for the period
SELECT Id, blng__ErrorMessage__c, blng__Order__c, blng__OrderProduct__c, CreatedDate
FROM blng__RevenueTransactionErrorLog__c
WHERE CreatedDate = LAST_N_DAYS:30
ORDER BY CreatedDate DESC
```

```soql
-- Step 2: Find OrderProducts without a RevenueRecognitionRule for the affected orders
SELECT Id, Product2Id, Product2.Name, Product2.blng__RevenueRecognitionRule__c,
       OrderId, TotalPrice
FROM OrderItem
WHERE OrderId IN (
    SELECT blng__Order__c
    FROM blng__RevenueTransactionErrorLog__c
    WHERE CreatedDate = LAST_N_DAYS:30
)
AND Product2.blng__RevenueRecognitionRule__c = null
```

```soql
-- Step 3: Verify blng__RevenueSchedule__c is absent for the affected OrderProducts
SELECT Id, blng__OrderProduct__c, blng__TotalAmount__c
FROM blng__RevenueSchedule__c
WHERE blng__OrderProduct__c IN (
    SELECT Id FROM OrderItem WHERE OrderId IN ('801xxxxxxxxxxxxxxx','801yyyyyyyyyyyyyyy')
)
-- If no records returned for affected OrderProducts, revenue schedule generation failed.
```

**Remediation approach:**
1. Configure `blng__RevenueRecognitionRule__c` on each affected Product2 with the correct treatment and distribution method (coordinate with Finance).
2. Re-trigger revenue schedule generation for the affected OrderProducts using the Salesforce Billing "Generate Revenue Schedule" action or equivalent Batch Apex process.
3. Confirm `blng__RevenueSchedule__c` records are created and `blng__RevenueTransaction__c` GL entries are generated for each Finance Period.
4. File a manual journal entry in the ERP to reverse the period-close entries that were made without the GL data, and replace them with entries derived from the newly generated transaction records.

**Why it matters:** The Revenue Transaction Error Log is a diagnostic object that many Salesforce Billing implementations never monitor. Without proactive querying of this object at billing run time, silent revenue recognition failures accumulate undetected. By the time Finance discovers the gap at close, it may span multiple billing periods and require complex ERP corrections. A simple post-billing-run query against `blng__RevenueTransactionErrorLog__c` would surface these failures within minutes of the billing batch completing.

---

## Anti-Pattern: Editing blng__InvoiceLine__c to Correct Billing Amount After Amendment

**What practitioners do:** A contract amendment reduces an annual subscription from $24,000 to $18,000. The billing batch has already run and generated a `blng__Invoice__c` for $24,000 (reflecting the pre-amendment billing schedule). The practitioner edits `blng__InvoiceLine__c.blng__ChargeAmount__c` directly from $24,000 to $18,000 to match the amended price, then manually adjusts the invoice total.

**What goes wrong:** The `blng__BillingSchedule__c` record still shows `blng__BillingAmount__c = 24000`. When the next billing run executes, it reads the uncorrected billing schedule and generates a new invoice for $24,000 — the same wrong amount. Worse, the GL now shows a $24,000 invoice (from the first billing run) with a manual edit applied, and a second $24,000 invoice from the next run, with no systematic link to the amended order product. Finance cannot reconcile the AR balance to the amended contract value.

**Correct approach:** Trace the discrepancy to `blng__BillingSchedule__c`. Correct the billing schedule amount to reflect the amended order product price before the next billing run. If the incorrect invoice has already been sent to the customer, issue a credit memo against the original invoice using the Salesforce Billing credit memo process, and generate a corrected invoice from the updated billing schedule. Never edit invoice or invoice line records directly.
