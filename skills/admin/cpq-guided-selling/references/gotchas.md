# Gotchas — CPQ Guided Selling

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Missing Mirror Field on SBQQ__ProcessInput__c Produces Silent All-Product Return

**What happens:** The guided selling wizard launches, the rep enters answers, and the results list shows the complete product catalog instead of filtered results. There are no error messages. The wizard appears to be working correctly but filtering has no effect.

**When it occurs:** Whenever `SBQQ__SearchField__c` on a ProcessInput record references a custom field API name that does not exist as a field on the `SBQQ__ProcessInput__c` object. CPQ cannot store the answer at runtime because the target field is absent. The filter for that question is skipped entirely.

**How to avoid:** Before creating ProcessInput records, verify that every custom Product2 field used for filtering has a matching field — identical API name, compatible data type — on `SBQQ__ProcessInput__c`. Create the mirror fields in Setup before configuring the Quote Process. After setup, use a SOQL query to confirm the field exists: query `SBQQ__ProcessInput__c` schema and verify the API name appears.

---

## Gotcha 2: Products with Null Classification Field Values Are Excluded by Equals-Operator Filters

**What happens:** Reps complete the guided selling wizard but certain products that should appear in results are missing, even though those products are active and in the pricebook. The products have a null value on the filtered field.

**When it occurs:** When `SBQQ__Operator__c = 'equals'` on a ProcessInput and a Product2 record has a null (blank) value on the `SBQQ__SearchField__c` field. The SOQL filter `WHERE FieldName = 'AnswerValue'` will never match a null, so the product is excluded regardless of what the rep selects. This is not unique to CPQ — it is standard SQL/SOQL null behavior — but it surprises practitioners who expect products with no classification value to be treated as eligible for all searches.

**How to avoid:** Ensure all products intended to appear in guided selling results have non-null values on every classification field used in the wizard. If a product is genuinely cross-category (eligible for all answers), assign a sentinel picklist value such as "All" or "Any" and use `SBQQ__Operator__c = 'contains'` with that value, or set `SBQQ__Required__c = false` on the ProcessInput so a blank answer from the rep skips that filter entirely.

---

## Gotcha 3: SBQQ__GuidedProductSelection__c = false Deactivates the Wizard Without Any Warning

**What happens:** After cloning or editing a `SBQQ__QuoteProcess__c` record, the "Add Products" button on CPQ quotes stops launching the guided selling wizard and instead opens the standard product selector. No error is displayed. Reps may not immediately notice the wizard is missing.

**When it occurs:** When `SBQQ__GuidedProductSelection__c` is set to `false` on the Quote Process — which happens silently if a record is cloned from a template that had this field unchecked, or if the field is accidentally toggled during an edit. CPQ treats this as an instruction to use the Quote Process in standard (non-wizard) product search mode.

**How to avoid:** After creating or cloning a Quote Process intended for guided selling, verify `SBQQ__GuidedProductSelection__c = true` before testing. Add this to the review checklist for any CPQ deployment. If the standard product selector unexpectedly appears, this field is the first thing to check.

---

## Gotcha 4: Auto Select Product Triggers a Pricebook Entry Error When the Matched Product Is Not in the Quote's Pricebook

**What happens:** The guided selling wizard completes with exactly one matching product. Auto Select fires and CPQ attempts to add the product to the quote automatically. Instead of a smooth add, the rep sees an error about a missing pricebook entry or an invalid product price, and the product is not added.

**When it occurs:** When `SBQQ__AutoSelectProduct__c = true` on the Quote Process, the one matching product exists in the product catalog, but it has no active `PricebookEntry` in the pricebook assigned to the quote. CPQ's auto-add path does not pre-check pricebook coverage before attempting to create the quote line — it discovers the missing entry at line creation time and fails.

**How to avoid:** Before enabling Auto Select Product, verify that all products that could be the sole guided selling result are present in every pricebook that may be used with this Quote Process. Run a SOQL check: `SELECT Product2Id FROM PricebookEntry WHERE Pricebook2Id = '<target pricebook>' AND IsActive = true` and cross-reference against products that qualify under single-answer guided selling scenarios. If full pricebook coverage cannot be guaranteed, leave Auto Select disabled and let reps confirm the result manually.
