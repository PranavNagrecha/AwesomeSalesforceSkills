# Examples — Revenue Recognition Requirements

## Example 1: SaaS Annual Subscription — Monthly Revenue Spread via Daily Proration

**Context:** A SaaS company sells a $12,000 annual subscription starting February 15. The subscription runs February 15 through February 14 of the following year. Finance requires revenue to be recognized ratably, aligned to monthly Finance Periods, with correct proration for partial months at the start and end.

**Problem:** Without configuring `blng__RevenueRecognitionRule__c` correctly, the Billing engine either does not generate a revenue schedule (if no rule is attached to the product) or generates one with equal monthly amounts that ignores partial months. The February Finance Period would then show a full month of revenue when only 14 days are earned — overstating revenue and understating deferred revenue on the balance sheet.

**Solution:**

1. Create a Revenue Recognition Rule:
   - `blng__RecognitionTreatment__c = Rateable`
   - `blng__DistributionMethod__c = Daily Proration`
2. Assign the rule to the Product2 record's `blng__RevenueRecognitionRule__c` lookup.
3. Verify Finance Periods exist from February through the following February (13 Finance Periods to cover the full service range).
4. Activate the Order on or after February 15. The engine creates one `blng__RevenueSchedule__c` for the OrderProduct.

Expected revenue schedule output (approximate):
```
Finance Period: Feb (Feb 1–Feb 28) → 14 days / 28 days × ($12,000 / 365 × 28) ≈ $460.27
Finance Period: Mar → $1,020.55  (full month, 31 days)
Finance Period: Apr → $986.30    (full month, 30 days)
...
Finance Period: Feb (following year, Feb 1–Feb 14) → $459.73
Total: $12,000.00
```

**Why it works:** Daily Proration divides the total contract value by the number of service days in the subscription, then allocates the result to each Finance Period based on the days of that period that fall within the service range. This handles partial months at start and end correctly without any manual calculation.

---

## Example 2: Contract Amendment Does Not Auto-Update Revenue Schedule

**Context:** A customer purchases a 12-month SaaS subscription for 10 seats at $1,000/seat/year ($10,000 total). At month 6, they add 5 more seats ($5,000 prorated for the remaining 6 months = $2,500 added contract value). The CPQ amendment order is activated.

**Problem:** Many practitioners expect the original `blng__RevenueSchedule__c` to update from $10,000 to $12,500 automatically when the amendment order is activated. It does not. The original schedule continues spreading $10,000 across its original 12-month Finance Period range unchanged. The amendment order generates a separate new `blng__RevenueSchedule__c` for the $2,500 uplift only. If Finance reconciles against a single revenue schedule, they will see $10,000 rather than the expected cumulative $12,500.

**Solution:**

After amendment order activation:
1. Confirm the original `blng__RevenueSchedule__c` is unchanged (still totaling $10,000).
2. Confirm a new `blng__RevenueSchedule__c` was auto-generated for the amendment OrderProduct ($2,500 spread across the remaining 6 Finance Periods).
3. For GL reporting, ensure the ERP integration or revenue report queries BOTH schedules to produce the correct cumulative recognized and deferred revenue balances.
4. If Finance requires a single consolidated schedule (common for audit trail purposes), manually close the original schedule and create a new unified schedule for $12,500 via Finance team processes — this is outside Salesforce Billing automation and must be a documented manual step.

```
Do NOT:
  Update blng__RevenueSchedule__c.blng__TotalAmount__c via Data Loader
  → This corrupts the schedule's internal line distribution and produces GL imbalances.

Do:
  Report on both schedules via SOQL:
  SELECT Id, blng__Order__c, blng__TotalAmount__c, blng__RecognizedAmount__c
  FROM blng__RevenueSchedule__c
  WHERE blng__Order__r.blng__OriginalOrder__c = :originalOrderId
```

**Why it works:** Treating each schedule independently preserves audit integrity. The ERP integration sums both schedules' `blng__RevenueTransaction__c` records to arrive at the correct net recognized revenue per period.

---

## Anti-Pattern: Enabling Standard Salesforce Revenue Schedules to Drive Billing Recognition

**What practitioners do:** When asked to "set up revenue recognition" in a Salesforce Billing org, a practitioner navigates to Setup > Products > Schedule Settings and enables "Revenue Schedules." They then populate Revenue Schedule fields on OpportunityLineItems or Products to define quantity and revenue splits.

**What goes wrong:** The standard Salesforce Revenue Schedules feature (OpportunityLineItem-level) is entirely separate from `blng__RevenueSchedule__c`. Enabling it has no effect on Salesforce Billing behavior. No `blng__RevenueSchedule__c` records are created by this action. No `blng__RevenueTransaction__c` GL events are generated. The Finance team continues to see no recognized revenue in the Billing GL report despite what appears to be a configured schedule.

**Correct approach:** Ignore the standard Revenue Schedules feature when working in a Salesforce Billing org for ASC 606 purposes. Instead:
1. Create `blng__RevenueRecognitionRule__c` records with the appropriate treatment and distribution method.
2. Assign them to Product2 via the `blng__RevenueRecognitionRule__c` lookup field.
3. Verify Finance Periods are configured.
4. Activate the Order to trigger `blng__RevenueSchedule__c` generation.
