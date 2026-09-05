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
Opportunity.SyncedQuoteId = [ID of the selected quote]   // writable: Create, Filter, Nillable, Update
                                                          // BUT read-only inside an Apex trigger
Quote.IsSyncing            = true                         // read-only: Defaulted on create, Filter

QuoteLineItem edits  ->  OpportunityLineItem updates (bidirectional while synced)
OpportunityLineItem edits  ->  QuoteLineItem updates (bidirectional while synced)

Exception: if the synced OpportunityLineItem has a quantity or revenue schedule,
writes to Quantity / TotalPrice / GrandTotal are IGNORED without an error.
Check QuoteLineItem.HasQuantitySchedule and .HasRevenueSchedule first.
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

Step 4 — Verify the mirror actually populated, for every quote, not just the one you tested:

```sql
SELECT Id, QuoteNumber, Status, OpportunityId,
       Billing_Street_Mirror__c, Billing_City_Mirror__c,
       Close_Date_Mirror__c, Contract_Term_Months__c
FROM Quote
WHERE CreatedDate = LAST_N_DAYS:30
  AND (Contract_Term_Months__c = NULL OR Close_Date_Mirror__c = NULL)
ORDER BY CreatedDate DESC
```

Rows here are quotes whose PDF would render blanks. The usual cause is a flow configured for Create only, or for Update only — `scripts/check_quotes_and_quote_templates.py` does not catch that, so this query is the check.

**Why it works:** The template renders quote fields at PDF generation time. By keeping mirror fields updated via Flow, the PDF always reflects current opportunity and account data without any template-side SOQL. Do not try to shortcut this with a Quote formula field that references `GrandTotal` — that field "is not directly referenceable or usable in custom formula fields on the Quote object" (`object_reference.txt` L239630–239637).

---

## Example 3: Discount Approval Process on Quotes

**Context:** Sales leadership wants any quote with a header discount exceeding 15% to require VP of Sales approval before the quote can be sent to the customer.

**Problem:** Without an approval gate, reps can set any discount value and email the quote immediately.

**Solution:**

1. In Setup > Approval Processes, create a new Approval Process on the **Quote** object.
2. Entry criteria: `Quote.Discount > 15`
3. Record editability: Lock the record on submission.
4. Approver: Named user (VP of Sales) or dynamic (lookup to a VP field on the quote).
5. Approval action: Unlock record, set `Quote.Status` to "Approved" — a status whose `allowEmail` is `true`.
6. Rejection action: Unlock record, set `Quote.Status` to "Rejected" (`allowEmail` false), notify the submitter, and reset the discount **on the line items**.
7. Gate the send with `allowEmail` on the status value, not with a validation rule.

Step 7 is where most implementations go wrong. `StandardValue.allowEmail` "indicates whether this value lets users email a quote PDF (true), or not (false). This field is only relevant for the Status field in quotes." (`api_meta.txt` L47538–47541). It is deployable, per status, and needs no formula:

```xml
<!-- excerpt: two standardValue entries from the QuoteStatus StandardValueSet -->
<StandardValueSet xmlns="http://soap.sforce.com/2006/04/metadata">
<standardValue>
    <fullName>In Review</fullName>
    <default>false</default>
    <isActive>true</isActive>
    <label>In Review</label>
    <allowEmail>false</allowEmail>
</standardValue>
<standardValue>
    <fullName>Approved</fullName>
    <default>false</default>
    <isActive>true</isActive>
    <label>Approved</label>
    <allowEmail>true</allowEmail>
</standardValue>
</StandardValueSet>
```

Step 6 is the other trap. `Quote.Discount` has properties `Filter, Nillable, Sort` — no `Create`, no `Update` — because it is derived from the line items' subtotals (`object_reference.txt` L239578–239592). A field update against it cannot be built. Reset the lines instead; the header roll-up follows:

```text
Flow: Quote_Reset_Line_Discounts_On_Reject
Trigger: Invoked from the approval process rejection action (or Quote after-save
         when Status changes to Rejected)

Get Records: QuoteLineItem WHERE QuoteId = {!$Record.Id}
             AND Discount > 15
Loop over the collection:
  Assignment: currentLine.Discount = 15          // percent, 0-100, writable
Update Records: the looped collection

Do NOT: Update Records -> Quote -> Discount = 15
        Quote.Discount is read-only. There is no field update to build.
```

**Why it works:** the approval process creates the control point, `allowEmail` removes the Email Quote action for every pre-approval status without depending on a save-time rule that the action may not pass through, and the reset writes to the only discount field the platform will accept — `QuoteLineItem.Discount` (`Create, Filter, Nillable, Sort, Update`, "Editable number from 0 to 100" — `object_reference.txt` L240758–240767).

---

## Anti-Pattern: Editing Opportunity Products While a Quote Is Synced

**What practitioners do:** A rep syncs a quote, then goes back to the opportunity and edits the opportunity products directly — changing quantities or removing a line item — because it feels faster than navigating to the quote.

**What goes wrong:** The edit on the opportunity product immediately flows back to the synced quote's line items, which modifies the quote. If the quote PDF was already generated and sent to the customer, the saved PDF and the live quote are now out of sync.

**Correct approach:** Once a quote is synced, direct all line item edits through the quote's line items tab. Never edit opportunity products directly while a sync is active. If you need to make emergency changes to the opportunity, stop sync first, make the change, then re-evaluate whether to re-sync.
