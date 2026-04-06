# Examples — Quote-to-Cash Requirements

## Example 1: Two-Tier Discount Approval Process on the Quote Object

**Context:** A manufacturing company sells custom equipment. Sales reps can give up to 10% discount independently. Discounts between 10% and 25% require Regional Manager approval. Discounts above 25% require VP of Sales approval.

**Problem:** A single-step approval process cannot route to two different approver tiers. Building two separate approval processes on Quote causes unpredictable behavior because Salesforce only processes one active approval at a time per record.

**Solution:**

Configure one Approval Process on the Quote object with two steps:

```
Approval Process: Quote Discount Approval
Entry Criteria: Quote.Discount >= 10

Step 1: Regional Manager Review
  Step entry criteria: Quote.Discount < 25
  Approver: User.Manager (relative to opportunity owner)
  On approve: Go to Next Step
  On reject: Reject approval, set Quote.Status = "Denied"

Step 2: VP of Sales Review
  Step entry criteria: (none — catches all remaining)
  Approver: Named user or "VP Sales" Queue
  On approve: Final Approval (set Quote.Status = "Approved")
  On reject: Final Rejection (set Quote.Status = "Denied", send email to rep)
```

Quotes with discount < 10% skip the process entirely. Quotes between 10-24% go through Step 1 only (VP step is skipped because step-entry criteria are not met). Quotes at 25%+ go through both steps.

**Why it works:** A single process with step-entry criteria is the correct pattern for multi-tier approvals. Step-entry criteria let Salesforce skip steps that do not apply, so each tier fires only for the relevant discount range. Using separate processes would mean only the first process fires — the second is never evaluated.

---

## Example 2: Flow-Driven Order Creation on Quote Acceptance

**Context:** An org wants an Order and OrderItems automatically created whenever a Quote is set to "Accepted" status — triggered by the final approval action or a rep manually updating the field.

**Problem:** The Approval Process Final Approval action cannot create records. Teams without this knowledge try to create the Order via a Final Approval "Field Update" and then another process — resulting in race conditions and orphaned records.

**Solution:**

Record-Triggered Flow on Quote object:

```
Trigger: Record is updated
Entry condition: Quote.Status = "Accepted" AND ISCHANGED(Status) = true

Action 1: Create Record — Order
  AccountId = Opportunity.AccountId (from Quote)
  Pricebook2Id = Quote.Pricebook2Id
  QuoteId = Quote.Id
  EffectiveDate = TODAY()
  Status = "Draft"
  (Store created record ID in variable: varOrderId)

Action 2: Get Records — QuoteLineItem
  Filter: QuoteId = Quote.Id
  (Store in collection: colQLI)

Action 3: Loop — colQLI
  For each QuoteLineItem, Create Record — OrderItem:
    OrderId = varOrderId
    Product2Id = currentItem.Product2Id
    PricebookEntryId = currentItem.PricebookEntryId
    Quantity = currentItem.Quantity
    UnitPrice = currentItem.UnitPrice
```

**Why it works:** Record-Triggered Flows can perform DML in the same transaction and support loops over related record collections. This eliminates the need for Apex and keeps the logic declarative and maintainable by admins.

---

## Anti-Pattern: Building Two Separate Approval Processes for Two Discount Tiers

**What practitioners do:** Create "Approval Process A" with entry criteria `Discount >= 10` routed to Regional Manager, and "Approval Process B" with entry criteria `Discount >= 25` routed to VP Sales — expecting both to fire for high discounts.

**What goes wrong:** Salesforce evaluates active approval processes in order and only the first matching process is triggered. "Approval Process B" never fires because Process A matches first. High-discount quotes receive only Regional Manager approval with no escalation to VP.

**Correct approach:** Use a single Approval Process with two sequential steps. Step 1 has step-entry criteria `Discount < 25` (fires only for mid-range discounts). Step 2 has no step-entry criteria (always fires after Step 1 approves, catching the escalation case). Both tiers receive their appropriate approval events within the same approval run.
