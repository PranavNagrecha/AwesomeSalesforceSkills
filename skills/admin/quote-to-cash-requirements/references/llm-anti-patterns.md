# LLM Anti-Patterns — Quote-to-Cash Requirements

Common mistakes AI coding assistants make when generating or advising on quote-to-cash processes using standard Salesforce objects.

## Anti-Pattern 1: Creating Two Approval Processes for Multi-Tier Discount Routing

**What the LLM generates:** Advice to create "Approval Process 1" for discounts 10-25% (routed to manager) and "Approval Process 2" for discounts >25% (routed to director), expecting both to run sequentially on a high-discount quote.

**Why it happens:** LLMs conflate Salesforce Approval Processes with general workflow rules. Workflow rules and some other automation tools can have multiple active configurations that all fire — the LLM incorrectly projects this behavior onto Approval Processes.

**Correct pattern:**
```
One Approval Process on Quote object with two steps:
  Step 1: step-entry criteria "Discount < 25", approver = Manager
  Step 2: no step-entry criteria (fires after Step 1), approver = Director
```
One process, two steps. Step-entry criteria control which steps apply to which discount range.

**Detection hint:** Any advice mentioning "create a second approval process" or "two active approval processes on Quote" is wrong.

---

## Anti-Pattern 2: Creating Order Records via Approval Process Final Actions

**What the LLM generates:** A Final Approval action configuration that "creates an Order record" when the Quote is approved — often described as an Approval Process action type of "Create Record."

**Why it happens:** LLMs trained on general workflow documentation may not know that Salesforce Approval Process Final Actions only support field updates, email alerts, tasks, and outbound messages. There is no "Create Record" action type in Approval Processes.

**Correct pattern:**
```
Approval Process Final Action: Field Update -> Quote.Status = "Accepted"

Separate Record-Triggered Flow on Quote:
  Trigger: Record Updated
  Condition: Status = "Accepted" AND ISCHANGED(Status)
  Action: Create Order + loop to create OrderItems
```
The Approval Process handles governance. The Flow handles downstream record creation triggered by the resulting status change.

**Detection hint:** Any response claiming an Approval Process can "create records" or has a "Create Order" action type is fabricated.

---

## Anti-Pattern 3: Recommending CPQ Features for Standard Quote Requirements

**What the LLM generates:** Advice to use "CPQ Discount Schedules," "CPQ Pricing Rules," or "Salesforce CPQ approval chains" when the question is about standard Salesforce Quotes without CPQ installed.

**Why it happens:** LLMs frequently blur the boundary between standard Sales Cloud Quotes and Salesforce CPQ. Both use "Quote" terminology but are entirely different products with different objects, features, and licensing.

**Correct pattern:**
```
Standard Salesforce Quotes (Sales Cloud):
  Objects: Quote, QuoteLineItem, QuoteDocument
  Approval: native Approval Processes
  PDF: Quote Templates (max 100 line items)
  Orders: manual or Flow-driven from Quote

Salesforce CPQ (Revenue Cloud):
  Objects: SBQQ__Quote__c, SBQQ__QuoteLine__c (custom)
  Approval: separate CPQ approval waterfall engine
  Pricing: Discount Schedules, Price Rules, Product Rules
```

**Detection hint:** If the response mentions SBQQ__, Discount Schedules, Pricing Rules, or Guided Selling for a standard Salesforce org, it has crossed into CPQ territory without basis.

---

## Anti-Pattern 4: Ignoring the 100-Line-Item PDF Limit

**What the LLM generates:** Quote Template configuration guidance with no mention of the 100-line-item PDF rendering limit, or assertions that "all line items will appear in the PDF."

**Why it happens:** Platform limits are underrepresented in LLM training data. The LLM knows Quote Templates generate PDFs but does not know the specific hard limit that causes silent truncation.

**Correct pattern:**
```
Quote Template hard limits:
  - Maximum 30 pages per generated PDF
  - Maximum 100 line items rendered in the template

If the deal requires > 100 line items:
  - Split into multiple Quotes (if business process allows)
  - Add a validation rule warning when QuoteLineItemCount > 90
  - Evaluate CPQ/Revenue Cloud for large-catalog requirements
```

**Detection hint:** Any Quote Template guidance that does not mention the 100-line-item limit when discussing high-volume product catalogs is incomplete.

---

## Anti-Pattern 5: Claiming Quote Currency Can Be Edited After Creation

**What the LLM generates:** Instructions to "edit the currency field on the Quote record" if the deal currency needs to change, or suggestions to use a Flow to update Quote.CurrencyIsoCode after creation.

**Why it happens:** LLMs know that Currency fields exist on Salesforce records and are generally editable. They do not know that Quote currency is an immutable system-level constraint — the field is locked post-creation by the platform, not by field-level security or validation rules.

**Correct pattern:**
```
Quote.CurrencyIsoCode is set at creation and cannot be changed.
If the currency is wrong:
  1. Delete the Quote (or archive it with a custom status)
  2. Create a new Quote with the correct currency
  3. Re-add line items from PricebookEntry records in the correct currency

Prevention: Make CurrencyIsoCode visible and required on the Quote creation quick action.
```

**Detection hint:** Any advice to "update" or "change" the currency on an existing Quote, or to use automation to modify CurrencyIsoCode post-creation, reflects a platform misunderstanding.

---

## Anti-Pattern 6: Conflating Quote Sync with a Merge Operation

**What the LLM generates:** Guidance that syncing a second Quote "adds" or "merges" its line items with existing Opportunity Products, or that "the Opportunity will have all line items from both Quotes."

**Why it happens:** The word "sync" implies incremental update. LLMs apply the common meaning without knowing that Salesforce Quote sync is destructive — it replaces, not merges.

**Correct pattern:**
```
Syncing Quote B to an Opportunity that already has Quote A synced:
  - ALL existing Opportunity Products are deleted
  - Quote B line items are inserted as new Opportunity Products
  - Quote A line items are no longer reflected on the Opportunity

This is a REPLACE operation, not a merge.
```

**Detection hint:** Any description of Quote sync that uses the words "merge," "add to," or "combine" with existing Opportunity Products is incorrect.
