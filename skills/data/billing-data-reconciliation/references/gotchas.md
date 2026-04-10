# Gotchas — Billing Data Reconciliation

Non-obvious Salesforce Billing platform behaviors that cause real production problems in this domain.

## Gotcha 1: Unallocated Partial Payments Do Not Auto-Close Invoices

**What happens:** A customer pays 60% of an invoice. A `blng__PaymentAllocation__c` record is created for the partial amount, and the invoice balance (`blng__Invoice__c.blng__Balance__c`) is correctly reduced to the remaining 40%. However, the invoice status remains `Posted` — not `Paid` — even though a payment has been recorded. Finance reports the invoice as outstanding in the AR aging report, triggering a follow-up with the customer who has already partially paid.

**When it occurs:** Any time a partial payment is received and allocated to an invoice where the remaining balance exceeds zero. This is standard Salesforce Billing behavior, not a bug. The platform requires full balance retirement (i.e., all `blng__PaymentAllocation__c` amounts summing to the invoice total) before the status transitions to `Paid`.

**How to avoid:** Train billing operations teams that partial allocation is correct behavior — the invoice *should* remain open until fully paid. The confusion arises when teams compare Salesforce Billing behavior to ERP systems that support tolerance-based auto-closure (e.g., closing an invoice if the remaining balance is within 1% of the payment). Salesforce Billing has no native tolerance rule. If a write-off is needed for the remaining balance, create a credit memo or adjustment per the org's write-off policy. Do not manually set `blng__Status__c = Paid` — this bypasses the allocation trail and corrupts AR reporting.

---

## Gotcha 2: Missing blng__RevenueRecognitionRule__c Produces Silent Revenue Entries — No Error on the Invoice

**What happens:** A Product2 record is missing its `blng__RevenueRecognitionRule__c` lookup when an Order is activated. The Billing engine generates `blng__BillingSchedule__c` records and, after the billing run, `blng__Invoice__c` records correctly. The invoice amounts are accurate. However, no `blng__RevenueSchedule__c` is created, and no `blng__RevenueTransaction__c` GL events are generated. The billing side of the ledger is intact; the revenue side is silent.

**When it occurs:** At Order activation when `Product2.blng__RevenueRecognitionRule__c` is null. The failure is captured in `blng__RevenueTransactionErrorLog__c` but is not surfaced as an error on the Order, the Invoice, or any notification to the billing operations team. It is invisible in the day-to-day billing workflow.

**How to avoid:** After each billing batch run, query `blng__RevenueTransactionErrorLog__c` filtered to the batch run date. Any records returned indicate products or orders where revenue schedule generation failed. Resolve the root cause (populate the missing rule on Product2, confirm Finance Periods exist) and re-trigger schedule generation before the accounting period closes. Include this query as a standard step in the post-billing-run checklist.

---

## Gotcha 3: Revenue Transaction Error Log Is the First-Look Diagnostic — Not an Optional Object

**What happens:** Billing reconciliation investigations start at the invoice or payment layer. Hours are spent comparing `blng__InvoiceLine__c` amounts to `OrderItem.TotalPrice` without finding a match. The actual root cause — a failed revenue schedule generation, a Finance Period gap, or a cancelled Order with an open schedule — is sitting in `blng__RevenueTransactionErrorLog__c` with an explicit error message identifying the affected Order and Product.

**When it occurs:** In orgs where the Revenue Transaction Error Log was never added to a monitoring report or dashboard. The object is created by the Billing package but is not included in the default Salesforce Billing app pages. Teams that do not proactively navigate to it or query it via SOQL are unaware it contains diagnostic data.

**How to avoid:** Make `blng__RevenueTransactionErrorLog__c` the mandatory first step in every billing reconciliation investigation. Create a Salesforce report on this object filtered to the current billing period and add it to the Billing Operations home page or dashboard. Set up a scheduled report delivery to the billing operations team after each billing batch run. Query syntax: `SELECT Id, blng__ErrorMessage__c, blng__Order__c, blng__OrderProduct__c, CreatedDate FROM blng__RevenueTransactionErrorLog__c WHERE CreatedDate = THIS_MONTH ORDER BY CreatedDate DESC`.

---

## Gotcha 4: blng__BillingSchedule__c Is Not Automatically Updated After Order Amendment

**What happens:** A contract amendment activates, changing `OrderItem.TotalPrice` for an existing order product. The `blng__BillingSchedule__c` record for that order product retains the pre-amendment `blng__BillingAmount__c`. When the next billing run executes, it reads the stale billing schedule and generates an invoice for the wrong amount. The invoice amount differs from the current order product price, and from the customer's expectation based on the amendment they signed.

**When it occurs:** Any Order amendment in Salesforce Billing where the amendment changes the price of an existing order product. The Billing engine creates a new delta billing schedule for the amendment OrderProduct, but does not revise the original billing schedule. The divergence is `OrderItem.TotalPrice` (correct, amended value) vs. `blng__BillingSchedule__c.blng__BillingAmount__c` (stale, pre-amendment value).

**How to avoid:** After activating any amendment order, query the billing schedules for all affected OrderProducts and compare `blng__BillingAmount__c` to `OrderItem.TotalPrice`. If they diverge, correct the billing schedule before the next billing run. This is a manual data integrity step — the platform does not do it automatically. If the incorrect invoice has already been generated, issue a credit memo via the Salesforce Billing credit memo process and generate a corrected invoice from the updated billing schedule.

---

## Gotcha 5: blng__PaymentAllocation__c Deletion Does Not Immediately Restore blng__UnallocatedAmount__c

**What happens:** A payment allocation record is deleted (e.g., to correct an allocation made against the wrong invoice). The expectation is that `blng__Payment__c.blng__UnallocatedAmount__c` will immediately increase by the deleted allocation amount, making those funds available for re-allocation to the correct invoice. In some Salesforce Billing package versions, the `blng__UnallocatedAmount__c` field is not recalculated synchronously. The funds appear to still be allocated even though the allocation record no longer exists, blocking the creation of a new correct allocation.

**When it occurs:** When deleting `blng__PaymentAllocation__c` records via the UI, Apex, or Data Loader in orgs running certain Salesforce Billing package versions. The recalculation may be deferred to a scheduled job or triggered asynchronously.

**How to avoid:** After deleting a `blng__PaymentAllocation__c` record, query `blng__Payment__c.blng__UnallocatedAmount__c` and wait for the value to reflect the freed funds before creating a replacement allocation. If the value does not update within a few minutes, check if a Billing batch job is queued to recalculate payment balances. In high-volume environments, perform allocation corrections during off-peak hours when the Billing batch scheduler is not actively processing to avoid race conditions between the allocation deletion and the recalculation job.
