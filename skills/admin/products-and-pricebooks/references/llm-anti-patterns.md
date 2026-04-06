# LLM Anti-Patterns — Products and Pricebooks

Common mistakes AI coding assistants make when generating or advising on Salesforce Products, Pricebooks, and PricebookEntry configuration. These patterns help the consuming agent self-check its own output.

---

## Anti-Pattern 1: Creating Custom Pricebook Entries Before Standard Pricebook Entries

**What the LLM generates:** Migration scripts or setup instructions that create PricebookEntry records directly in a custom Pricebook (e.g., "Partner Pricebook") without first ensuring a corresponding Standard Pricebook entry exists for each product.

**Why it happens:** LLMs treat the Standard Pricebook as one of many optional Pricebooks rather than as a platform-required anchor. The dependency constraint is not visible from the data model diagram alone — it is a runtime platform rule.

**Correct pattern:**

```text
Required creation order for PricebookEntry records:
  1. Create Product2 (IsActive = true).
  2. Create PricebookEntry in the STANDARD Pricebook for that product.
     - This step is MANDATORY even if the Standard Pricebook is never used for selling.
  3. Only after step 2: create PricebookEntry records in custom Pricebooks.

API error if step 2 is skipped:
  "INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST: You cannot create a custom pricebook
   entry for a product that doesn't have a standard pricebook entry."
```

**Detection hint:** Any data load script or instruction set that creates custom Pricebook entries without a prior step explicitly creating Standard Pricebook entries for the same products.

---

## Anti-Pattern 2: Advising That the Standard Pricebook Can Be Deleted

**What the LLM generates:** Cleanup instructions such as "delete the Standard Pricebook if you don't use it and replace it with your own default Pricebook" or API scripts that call `delete` on the Standard Pricebook record.

**Why it happens:** LLMs generalize from the pattern that custom Pricebooks can be deleted (when not referenced), and incorrectly extend that to the Standard Pricebook. The platform's permanent nature of the Standard Pricebook is an edge-case constraint not always present in training data.

**Correct pattern:**

```text
The Standard Pricebook:
  - CANNOT be deleted through the UI or API.
  - CAN be deactivated (IsActive = false) to hide it from pickers.
  - Will always exist in the org — design catalog workflows to account for its presence.
  - Deactivation does not remove existing line items referencing it.
```

**Detection hint:** Any instruction to delete, remove, or replace the Standard Pricebook, or any script that includes `Database.delete` or `DELETE` SOQL targeting the Standard Pricebook.

---

## Anti-Pattern 3: Assuming Multi-Currency Exchange Rates Auto-Populate PricebookEntries

**What the LLM generates:** Setup guidance like "once you enable EUR in Manage Currencies and set the exchange rate, Salesforce will automatically create EUR prices for your products based on the USD price" or "the platform's currency conversion will handle EUR pricing automatically."

**Why it happens:** Salesforce's multi-currency conversion (static or advanced, via DatedExchangeRates) is a reporting-time feature. LLMs conflate currency conversion for display/reporting with the creation of pricing records, which are distinct platform features.

**Correct pattern:**

```text
Currency exchange rate conversion:
  - Applies at REPORT and DISPLAY time only.
  - Does NOT create new PricebookEntry records.
  - Does NOT make products available for selection on Opportunities in new currencies.

To make products available in a new currency:
  - Create one PricebookEntry per product per Pricebook per currency with an explicit UnitPrice.
  - Use Data Loader for bulk entry creation across large catalogs.
  - A product is ONLY available on an Opportunity in currency X if a PricebookEntry
    exists for that product, Pricebook, and currency X.
```

**Detection hint:** Any claim that enabling a currency or setting an exchange rate makes products available in that currency without an explicit PricebookEntry creation step.

---

## Anti-Pattern 4: Hardcoding the Standard Pricebook ID in Apex Test Code

**What the LLM generates:** Apex test setup code that hardcodes the Standard Pricebook ID retrieved from a production query, such as `Id stdPBId = '01sXXXXXXXXXXXXX';` — and then uses that hardcoded ID to create test PricebookEntry and OpportunityLineItem records.

**Why it happens:** The Standard Pricebook ID is a real, queryable record ID. LLMs generate what looks like valid Apex but use a literal ID string without flagging that this ID is org-specific and will fail in any other org or sandbox.

**Correct pattern:**

```apex
// WRONG — hardcoded ID is org-specific and will fail in any other org/sandbox
Id stdPBId = '01s000000000ABCAAA';

// CORRECT — runtime retrieval works in all orgs
Id stdPBId = Test.getStandardPricebookId();

// Usage:
Pricebook2 stdPB = new Pricebook2(Id = Test.getStandardPricebookId(), IsActive = true);
update stdPB; // ensure it's active in the test context

PricebookEntry pbe = new PricebookEntry(
    Pricebook2Id = Test.getStandardPricebookId(),
    Product2Id = myProduct.Id,
    UnitPrice = 100.00,
    IsActive = true
);
insert pbe;
```

**Detection hint:** Any Apex test class containing a literal string starting with `01s` used as a Pricebook ID.

---

## Anti-Pattern 5: Claiming Deactivating a Product Removes It from Open Opportunities

**What the LLM generates:** Advice like "if you deactivate a product, it will be removed from any open opportunities that currently have it as a line item" or "deactivating cleans up all references to the product."

**Why it happens:** LLMs conflate the "hidden from picker" effect of deactivation with a broader removal of all references. The platform's decision to preserve existing OpportunityLineItem records on deactivation is intentional and not always obvious from the term "deactivate."

**Correct pattern:**

```text
Product2.IsActive = false (deactivation) effects:
  - Product HIDDEN from "Add Products" picker on new Opportunities and Quotes.
  - Existing OpportunityLineItem records: UNCHANGED (product still shows on those records).
  - Existing QuoteLineItem records: UNCHANGED.
  - PricebookEntry records: NOT deleted (they remain but the product is hidden).
  - Historical reporting: UNAFFECTED.

To remove a product from open Opportunities after deactivation:
  - Manually delete or update the specific OpportunityLineItem records.
  - Deactivation alone does NOT do this.
```

**Detection hint:** Any statement that deactivating a product will "clean up," "remove," or "hide" existing line items on open or historical Opportunity records.

---

## Anti-Pattern 6: Mixing Products from Different Pricebooks on a Single Opportunity

**What the LLM generates:** Instructions to add some products from the "Standard Pricebook" and other products from a "Partner Pricebook" to the same Opportunity, or code that sets different `Pricebook2Id` values on different OpportunityLineItems for the same Opportunity.

**Why it happens:** LLMs model PricebookEntry as a simple price lookup and miss the platform constraint that an Opportunity's `Pricebook2Id` field applies uniformly — all products on that Opportunity must come from the same Pricebook.

**Correct pattern:**

```text
Opportunity.Pricebook2Id is set ONCE per Opportunity.
ALL products added to that Opportunity must have PricebookEntry records in that same Pricebook.
You CANNOT mix products from different Pricebooks on a single Opportunity.

If a rep needs to use multiple pricing tiers on one deal:
  Option 1: Consolidate all needed products into a single Pricebook.
  Option 2: Use a manual discount approach within one Pricebook.
  Option 3: Evaluate CPQ for multi-tier pricing on a single quote.
```

**Detection hint:** Any code or instruction that assigns different Pricebook IDs to different OpportunityLineItem records on the same Opportunity, or that suggests "mixing" Pricebooks is possible on a single Opportunity.
