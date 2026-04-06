# Examples — Quotes and Quote Templates

## Example 1: Syncing a Quote and Keeping Opportunity Products in Sync

**Context:** A sales rep has three quote drafts on an opportunity — one for the standard configuration, one for a discounted bundle, and one for a reduced scope. The customer selects the discounted bundle. The rep must make the opportunity reflect those exact products and pricing for forecasting.

**Problem:** If the rep manually updates opportunity products instead of using quote sync, the opportunity and quote will diverge. The quote PDF will not match the opportunity revenue, causing forecast inaccuracies.

**Solution:**

1. Navigate to the selected quote record (the discounted bundle quote).
2. Click **Start Sync** on the quote. Salesforce sets `Opportunity.SyncedQuoteId` to this quote's ID.
3. All further line item edits should be made on the quote record's line items, NOT directly on the opportunity products.
4. When the quote is finalized, generate the PDF and email it to the customer from the quote record.
5. If the rep needs to revise, they edit the quote lines — changes flow to opportunity products automatically.

```text
Opportunity.SyncedQuoteId = [ID of the selected quote]

QuoteLineItem edits  ->  OpportunityLineItem updates (bidirectional while synced)
OpportunityLineItem edits  ->  QuoteLineItem updates (bidirectional while synced)
```

**Why it works:** The platform's bidirectional sync keeps the opportunity's Total Amount field (used for forecasting) in lock-step with the quote that represents the agreed deal. Stopping sync on other draft quotes ensures they remain historical records without polluting the opportunity.

---

## Example 2: Populating Opportunity and Account Fields on a Quote PDF

**Context:** The legal team requires that the quote PDF include the Account's billing address, the opportunity close date, and a custom contract term field (`Opportunity.Contract_Term_Months__c`). None of these exist natively on the Quote object.

**Problem:** The quote template field picker only surfaces `Quote` and `QuoteLineItem` fields. Attempting to add Opportunity or Account fields directly to the template is not possible.

**Solution:**

Step 1 — Create mirror fields on the Quote object:
- `Quote.Billing_Street_Mirror__c` (Text)
- `Quote.Billing_City_Mirror__c` (Text)
- `Quote.Close_Date_Mirror__c` (Date)
- `Quote.Contract_Term_Months__c` (Number)

Step 2 — Create a Record-Triggered Flow (After Save, on Quote insert and update) that retrieves the related Opportunity and Account and populates the mirror fields:

```text
Flow: Quote_Populate_Mirror_Fields
Trigger: Quote — After Save (Create and Update)
Get Records: Opportunity WHERE Id = {!$Record.OpportunityId}
Get Records: Account WHERE Id = {!Opportunity.AccountId}

Assignment:
  Quote.Billing_Street_Mirror__c  = {!Account.BillingStreet}
  Quote.Billing_City_Mirror__c    = {!Account.BillingCity}
  Quote.Close_Date_Mirror__c      = {!Opportunity.CloseDate}
  Quote.Contract_Term_Months__c   = {!Opportunity.Contract_Term_Months__c}

Update Records: Quote (current record)
```

Step 3 — In Setup > Quote Templates, add the mirror fields to the Header section using the Insert Field picker.

**Why it works:** The template renders quote fields at PDF generation time. By keeping mirror fields updated via Flow, the PDF always reflects current opportunity and account data without any template-side SOQL.

---

## Example 3: Discount Approval Process on Quotes

**Context:** Sales leadership wants any quote with a header discount exceeding 15% to require VP of Sales approval before the quote can be sent to the customer.

**Problem:** Without an approval gate, reps can set any discount value and email the quote immediately.

**Solution:**

1. In Setup > Approval Processes, create a new Approval Process on the **Quote** object.
2. Entry criteria: `Quote.Discount > 15`
3. Record editability: Lock the record on submission.
4. Approver: Named user (VP of Sales) or dynamic (lookup to a VP field on the quote).
5. Approval action: Unlock record, set `Quote.Status` to "Approved".
6. Rejection action: Unlock record, reset `Quote.Discount` to 15 (field update), send email notification to the submitter.
7. Add a validation rule to prevent emailing the quote before approval:

```text
[Validation Rule on Quote]
Rule Name: Require_Approval_Before_Email
Error Condition:
  AND(
    Quote.Discount > 15,
    Quote.Status != 'Approved'
  )
Error Message: "This quote requires VP approval before it can be emailed to the customer."
```

**Why it works:** The Approval Process creates the control point; the validation rule enforces it at the UI layer so reps cannot bypass approval by directly clicking Email Quote.

---

## Anti-Pattern: Editing Opportunity Products While a Quote Is Synced

**What practitioners do:** A rep syncs a quote, then goes back to the opportunity and edits the opportunity products directly — changing quantities or removing a line item — because it feels faster than navigating to the quote.

**What goes wrong:** The edit on the opportunity product immediately flows back to the synced quote's line items, which modifies the quote. If the quote PDF was already generated and sent to the customer, the saved PDF and the live quote are now out of sync.

**Correct approach:** Once a quote is synced, direct all line item edits through the quote's line items tab. Never edit opportunity products directly while a sync is active. If you need to make emergency changes to the opportunity, stop sync first, make the change, then re-evaluate whether to re-sync.
