# Gotchas — Products and Pricebooks

Non-obvious platform behaviors that cause real production problems in the Salesforce product catalog and pricing configuration.

---

## Gotcha 1: Standard Pricebook Cannot Be Deleted — Only Deactivated

The Standard Pricebook (the one automatically created with every Salesforce org) cannot be deleted through the UI or the API. Attempting deletion via the API returns an error. It can only be deactivated (`IsActive = false`), which prevents it from being selected on new Opportunities and Quotes but does not remove it from the org or invalidate existing line items referencing it.

**Why it matters:** Teams that want to "clean up" the Standard Pricebook or replace it with a company-branded equivalent cannot delete it. The org will always have the Standard Pricebook as a permanent object. Design workflows around its existence — do not build on the assumption it can be removed.

**Detection:** Any plan or migration script that includes a step to delete the Standard Pricebook will fail at that step.

---

## Gotcha 2: Custom Pricebook Cannot Be Deleted While Referenced by Open Opportunities or Quotes

A custom Pricebook cannot be deleted while any Opportunity or Quote in an open status (i.e., not Closed Won or Closed Lost) has `Pricebook2Id` pointing to it. The UI will display an error, and the API will return a deletion failure.

**Why it matters:** Before running a data cleanup that removes old custom Pricebooks, you must either close all referencing Opportunities/Quotes or reassign them to a different Pricebook. In large orgs, this can require a bulk data update.

**Safe approach:**
1. Query `SELECT Id, Name FROM Opportunity WHERE Pricebook2Id = '<pricebook_id>' AND IsClosed = false` to find all blocking records.
2. Either close them, move them to a different Pricebook, or mark them as lost before attempting the deletion.
3. Deactivate the Pricebook first as an intermediate step — deactivation has no such blocking constraint.

---

## Gotcha 3: Standard Pricebook Entry Must Exist Before Any Custom Pricebook Entry

The platform enforces a hard dependency: a Product2 must have an active PricebookEntry in the Standard Pricebook before a PricebookEntry for that product can be created in any custom Pricebook. This applies regardless of whether the Standard Pricebook is ever used for selling.

**Why it matters:** When building a catalog that uses only custom Pricebooks, it is tempting to skip the Standard Pricebook entirely. Any attempt to create a custom Pricebook entry via the API or UI without the Standard Pricebook entry will fail with a validation error.

**Common scenario:** A migration script creates custom Pricebook entries first for efficiency (because they are sorted by Pricebook name alphabetically, and the custom Pricebook name comes first). The script fails on every record. The fix is to always insert Standard Pricebook entries before any custom Pricebook entries in the data load sequence.

---

## Gotcha 4: Multi-Currency Does Not Auto-Create PricebookEntries — Each Currency Requires an Explicit Entry

Enabling a new currency in Setup > Manage Currencies does NOT automatically create PricebookEntry records for that currency. Exchange rate conversion is a reporting feature — it does not provision new entries. A product is only available on an Opportunity in a given currency if a PricebookEntry exists for that product, Pricebook, and currency combination.

**Why it matters:** An org enables EUR after going live in USD. All existing products immediately become unavailable for EUR Opportunities — the picker shows no products. This surprises admins who assume the platform's currency conversion handles it.

**Detection:** Create a test Opportunity in the new currency. Try to add a product. If the picker is empty, the PricebookEntry for that currency is missing.

**Fix:** Bulk-create missing PricebookEntries via Data Loader or a script. Query the existing USD entries as a template; set `CurrencyIsoCode` to the new currency and define the `UnitPrice` in that currency.

---

## Gotcha 5: Deactivating a Product Does Not Remove It from Existing Opportunity Line Items

Setting `Product2.IsActive = false` hides the product from the "Add Products" picker on new Opportunities and Quotes. It does NOT remove or alter existing OpportunityLineItem or QuoteLineItem records that already reference the product. Historical data is fully preserved.

**Why it matters:** A common misconception is that deactivating a product will cause issues with existing Opportunities. It does not. The OpportunityLineItem record stores `PricebookEntryId`, which in turn references the Product2 — deactivating Product2 does not break that reference chain.

**Corollary:** You cannot deactivate a product to "retroactively remove it" from in-flight Opportunities. If the goal is to remove a product from open Opportunities, those OpportunityLineItem records must be explicitly deleted or updated.

---

## Gotcha 6: Hardcoding the Standard Pricebook ID in Apex Tests Is a Common Source of Org-Specific Failures

The Standard Pricebook has a different ID in every org and every sandbox. Apex test code that hardcodes the Standard Pricebook ID (typically retrieved once from a production query and then pasted into the test class) will fail when deployed to any other org, including sandboxes refreshed from production.

**Correct pattern:** Always use `Test.getStandardPricebookId()` inside test methods to retrieve the Standard Pricebook ID at runtime. This method is available in API version 16.0 and later.

```apex
// WRONG — hardcoded ID breaks across orgs
Id pricebookId = '01s000000000ABC';

// CORRECT — runtime retrieval works in any org
Id pricebookId = Test.getStandardPricebookId();
```

**Why it matters:** This is the #1 cause of "works in dev sandbox, fails in UAT sandbox" for any Apex that creates Opportunity products or PricebookEntry records in test methods.

---

## Gotcha 7: Product Schedules Affect Collaborative Forecasting Rollups If the Forecast Object Is Set to Product Schedules

When Revenue or Quantity Schedules are enabled and Collaborative Forecasting is configured to use "Product Schedules" as its forecast object, the forecast rolls up from individual schedule installments — NOT from the OpportunityLineItem total. This means:

- An Opportunity with a $120,000 product split into 12 monthly revenue installments will show $10,000/month in the forecast, not $120,000 in the close date month.
- If schedules are enabled but the forecast type is still set to "Opportunity," schedule data is completely invisible to forecasts.

**Why it matters:** Finance teams often expect both views simultaneously. The forecast type must be set deliberately. Changing the forecast object after forecast data exists requires a full forecast history rebuild.
