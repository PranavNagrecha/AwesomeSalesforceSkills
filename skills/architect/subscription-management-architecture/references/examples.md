# Examples — Subscription Management Architecture

## Example 1: Mid-Contract Price Renegotiation Using the Swap Pattern

**Context:** An enterprise customer on a 36-month contract negotiates a 15% unit price reduction at month 18 due to expanded volume commitments. The product `Professional Services Hours` is on the active contract at $200/hr for 500 hours. The new negotiated rate is $170/hr starting on the amendment effective date.

**Problem:** An architect attempts to edit the unit price directly on the existing subscription line in the amendment quote. CPQ either rejects the edit or silently reverts it on quote calculation, because existing subscription lines are locked to their contracted price. The $200 price persists and the amendment activates with the wrong price.

**Solution:**

```text
Amendment Quote Setup:
1. Initiate amendment from the active Contract record.
2. On the amendment quote, locate the "Professional Services Hours" line.
3. Set Quantity = 0 on that line.
   → CPQ will create a SBQQ__Subscription__c delta record: Qty = -500, 
     prorated for the remaining 18 months.
4. Add a new "Professional Services Hours" line.
   → Set Quantity = 500.
   → Apply the new unit price ($170) via a Price Rule or manual override 
     (override requires "Allow Price Override" on the product).
5. Calculate quote.
   → Co-termination applies: new line end date = original contract end date.
   → Proration: new line is priced for the remaining 18 months only.
6. Approve and activate.
   → Three SBQQ__Subscription__c records exist for this product on the contract:
       Record 1 (original):    Qty=500, Price=$200, Start=Month 0
       Record 2 (zero-out):    Qty=-500, Price=$200, Start=Month 18 (prorated)
       Record 3 (replacement): Qty=500,  Price=$170, Start=Month 18 (prorated)
   → Effective state (sum of records): Qty=500 at $170 from Month 18 onward.
```

**Why it works:** CPQ's ledger model allows delta records to represent changes without modifying existing records. The zero-out record cancels the remaining value of the original subscription, and the replacement record begins the new pricing. Downstream billing correctly generates a credit memo for the zeroed-out record and a new invoice for the replacement.

---

## Example 2: Async Amendment on a 3,000-Line Enterprise Contract

**Context:** A telecommunications customer has a master contract with 3,000 active `SBQQ__Subscription__c` records representing individual service line items. A quarterly amendment adds 150 new lines and removes 75 existing lines. The standard Amend button times out after 30 seconds with an Apex CPU limit error.

**Problem:** The synchronous amendment path executes within a single Apex transaction. At 3,000 lines, CPQ's subscription processing exceeds the 10,000 ms CPU time governor limit before the amendment quote is created. Every attempt via the UI button fails.

**Solution:**

```apex
// Scheduled Apex or developer console execution
// Initiate async amendment
public static void initiateAsyncAmendment(Id contractId) {
    SBQQ.ContractManipulationAPI.AmendmentContext ctx = 
        new SBQQ.ContractManipulationAPI.AmendmentContext();
    ctx.contractId = contractId;
    ctx.amendmentStartDate = Date.today();
    
    // This queues SBQQ.AmendmentBatchJob asynchronously
    SBQQ.ContractManipulationAPI.amend(ctx);
}

// Monitor for completion — call from a scheduled job or platform event
public static Boolean isAmendmentComplete(Id contractId) {
    List<AsyncApexJob> jobs = [
        SELECT Id, Status, NumberOfErrors, ExtendedStatus
        FROM AsyncApexJob
        WHERE ApexClass.Name = 'AmendmentBatchJob'
        AND Status NOT IN ('Completed', 'Failed', 'Aborted')
        ORDER BY CreatedDate DESC
        LIMIT 1
    ];
    if (jobs.isEmpty()) return true; // No pending job
    return false; // Still running
}
```

After calling `initiateAsyncAmendment()`:
1. Monitor `AsyncApexJob` for `SBQQ.AmendmentBatchJob` status.
2. Do NOT activate the Contract or trigger billing until `Status = 'Completed'`.
3. Once complete, the amendment Quote appears on the Contract's related list.
4. Review, approve, and activate through the standard CPQ approval flow.

**Why it works:** Large-Scale mode processes subscription records in configurable batch chunks (default 200 per batch), each within its own transaction. Governor limits reset per chunk, allowing 3,000+ lines to be processed without hitting CPU or SOQL limits. The tradeoff is that the process is no longer synchronous — user notification and billing triggers must be deferred until job completion.

---

## Example 3: Renewal Forecast Without Premature Price Lock

**Context:** A SaaS company's Sales Operations team needs renewal opportunities visible in the forecast 90 days before contract expiration so AEs can plan. However, renewals are always negotiated, and auto-generating a renewal quote at list price creates incorrect price anchors that AEs then have to manually correct before customer-facing negotiations.

**Problem:** When `SBQQ__RenewalForecast__c = true` AND `SBQQ__RenewalQuoted__c = true` on the contract, CPQ creates both the Renewal Opportunity and a Renewal Quote at current list price on contract activation. AEs start negotiations with a quote that shows the wrong price, which the customer perceives as an opening bid rather than a system artifact.

**Solution:**

```text
CPQ Contract Configuration:
- SBQQ__RenewalForecast__c = true   → creates Renewal Opportunity on activation
- SBQQ__RenewalQuoted__c = false    → does NOT auto-generate Renewal Quote

Workflow:
1. Contract activates → Renewal Opportunity created with forecast amount.
2. AE works the renewal opportunity; no Quote exists yet.
3. When ready to quote (typically 60 days out), AE clicks "Renew" from 
   the Contract or Renewal Opportunity.
4. CPQ generates the Renewal Quote at that point, using current price book.
5. AE negotiates and adjusts pricing on the Renewal Quote.
6. If contracted renewal pricing is required, SBQQ__ContractedPrice__c 
   records for the account-product combination must exist before step 4.
```

**Why it works:** Separating Renewal Forecast from Renewal Quoted gives the forecast pipeline visibility that Sales Operations needs while preventing premature price commitment. The Renewal Quote is generated only when the AE is ready to engage the customer, and at that point the AE has full control to negotiate pricing before any customer communication.

---

## Anti-Pattern: Reading a Single Subscription Record as Current State

**What practitioners do:** Write a report, trigger, or integration that queries the most recent `SBQQ__Subscription__c` record for a product on a contract to get the "current" quantity and price.

```soql
-- Wrong: assumes latest record = current state
SELECT SBQQ__Quantity__c, SBQQ__NetPrice__c
FROM SBQQ__Subscription__c
WHERE SBQQ__Contract__c = :contractId
  AND SBQQ__Product__c = :productId
ORDER BY CreatedDate DESC
LIMIT 1
```

**What goes wrong:** After the first amendment, CPQ has created additional delta records for the same product-contract combination. The most recently created record may be a delta (e.g., +200 qty from an upsell), not the full current quantity. The query returns the delta value, not the effective total.

**Correct approach:**

```soql
-- Correct: aggregate all delta records to derive current state
SELECT SBQQ__Product__c, SUM(SBQQ__Quantity__c) totalQty
FROM SBQQ__Subscription__c
WHERE SBQQ__Contract__c = :contractId
  AND SBQQ__Product__c = :productId
  AND SBQQ__SubscriptionEndDate__c >= TODAY
GROUP BY SBQQ__Product__c
```

This aggregation pattern accounts for original records, positive delta records (upsells), negative delta records (downsells), and zero-out records from swaps. Only active records (end date in the future) should be included to exclude expired co-termed lines.
