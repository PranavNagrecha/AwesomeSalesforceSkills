# Examples — CPQ Guided Selling

## Example 1: Custom Classification Fields Causing Silent All-Product Return

**Context:** A manufacturing company configured CPQ Guided Selling with two custom fields on Product2: `Product_Line__c` (Picklist) and `Market_Segment__c` (Picklist). The admin created the Quote Process and ProcessInput records, set `SBQQ__SearchField__c` correctly on each ProcessInput, and activated the wizard. Reps reported that no matter what answers they selected, the product results list always showed every product in the catalog.

**Problem:** The admin created the classification fields on `Product2` but did not create the mirror fields on `SBQQ__ProcessInput__c`. Because CPQ stores the rep's runtime answer on the ProcessInput object using a field whose API name matches `SBQQ__SearchField__c`, and that field did not exist on `SBQQ__ProcessInput__c`, CPQ had nowhere to write the answer. The SOQL filter for each question was silently skipped, returning all products.

**Solution:**

Step 1: In Setup, navigate to Object Manager > Process Input (`SBQQ__ProcessInput__c`) > Fields & Relationships.

Step 2: Create a Picklist field named "Product Line" with API name `Product_Line__c`. Match the picklist values exactly to those on the Product2 field.

Step 3: Create a Picklist field named "Market Segment" with API name `Market_Segment__c` with matching values.

Step 4: Return to a test CPQ quote, click Add Products, and run the wizard. Each answer now writes to the corresponding ProcessInput field and the SOQL filter applies correctly.

Verification: Select a value that matches only 2 of your 50 catalog products. Confirm the results list shows exactly those 2 products.

**Why it works:** CPQ's guided selling filter engine reads the rep's answer from the ProcessInput field whose API name matches `SBQQ__SearchField__c`, then uses it as the filter value in a dynamic SOQL query against Product2. Without the mirror field, the read returns null and no WHERE clause is generated for that question — every product passes the filter unconditionally.

---

## Example 2: Multi-Value Product Eligibility with Enhanced Search

**Context:** A technology services company sells consulting packages that are eligible across multiple industry verticals. The Product2 catalog has an `Industry_Vertical__c` Picklist field with values: Healthcare, Financial Services, Manufacturing, Public Sector. Some packages (e.g., "Digital Transformation Consulting") are valid for Healthcare and Financial Services but not Manufacturing or Public Sector. With Standard search, a rep selecting "Healthcare" would see that product, but a rep selecting "Financial Services" also needed to find it. The admin initially tried using a "contains" operator with comma-separated values on the Product2 field but found matching unreliable.

**Problem:** Standard search with a single `equals` operator only matches one answer value per question. Storing multi-value strings in a text field and using "contains" is fragile — a product tagged "Healthcare,Financial Services" could incorrectly match a search for "Services" if another industry happened to include that substring.

**Solution:**

Step 1: On the `SBQQ__QuoteProcess__c` record, change `SBQQ__SearchType__c` from `Standard` to `Enhanced`.

Step 2: Ensure the `Industry_Vertical__c` field exists on both Product2 and `SBQQ__ProcessInput__c` with identical picklist values.

Step 3: For products that apply to multiple verticals, use a multi-select picklist on Product2 for `Industry_Vertical__c` so multiple values can be stored per product. Set eligible values (e.g., Healthcare and Financial Services) on the Digital Transformation Consulting product.

Step 4: When the rep opens the wizard in Enhanced mode, the Industry Vertical question renders as a multi-select input. The rep can check "Healthcare" and "Financial Services" simultaneously. CPQ returns products that match either selected value.

Step 5: Test by selecting only "Manufacturing" — confirm the consulting package does not appear. Select "Healthcare" alone — confirm it appears. Select "Financial Services" alone — confirm it still appears.

**Why it works (as reported):** Enhanced search is described here as changing the filter from a single-value match to an OR-match across the rep's selected values.

UNVERIFIED (2026-10-03): this multi-select behavior, and the `SBQQ__SearchType__c` field, are help-only claims carried from earlier versions of this skill. The CPQ Plugins Developer Guide uses "Enhanced" for a different thing: the product search plugin mode in which `isSuggestCustom` returns false and CPQ appends the WHERE fragment returned by `getAdditionalSuggestFilters`. Test multi-select behavior in a sandbox before promising it to the business, and if it is not available, express multi-value eligibility in the plugin's appended filter (for example `AND Product2.Industry_Vertical__c INCLUDES ('Healthcare')`). CPQ runs the returned fragment itself, so bind variables are not available there: build it only from values checked against the picklist's allowed values, and escape them with `String.escapeSingleQuotes`.

---

## Anti-Pattern: Conflating CPQ Guided Selling with OmniStudio Product Selection Flows

**What practitioners do:** When a business requests "a guided product selection experience," practitioners unfamiliar with CPQ vs. OmniStudio boundaries sometimes build an OmniScript or FlexCard-based flow to capture rep answers and filter products, then attempt to add those products to a CPQ quote from OmniStudio.

**What goes wrong:** OmniStudio product selection flows operate outside the CPQ quote calculation engine. Products injected into a CPQ quote via OmniScript do not pass through CPQ's configurator, price waterfall, or product rule evaluation. Quote line items end up with missing pricing data, skipped bundle configuration, and no CPQ-managed document. The experience appears to work in the UI but produces structurally incomplete CPQ quotes that fail downstream in approval, contracting, and revenue recognition.

**Correct approach:** For CPQ-managed quotes, always use the native CPQ Guided Selling mechanism — `SBQQ__QuoteProcess__c` and `SBQQ__ProcessInput__c` records. OmniStudio product selection is a legitimate tool for non-CPQ quoting contexts (e.g., OmniStudio-native order management), not for adding products to SBQQ-managed quotes.

---

## Example 3: Diagnosing an Unfiltered Wizard in Two Queries

**Context:** After a release, reps report that the "Deployment Model" question returns the whole catalog.

**Problem:** The release renamed the Product2 picklist field to `Deployment_Model_v2__c`, but the Process Input mirror field was not renamed, and the question still points at the old name.

**Solution:** Compare the field on both objects with `FieldDefinition` (no Tooling API needed):

```sql
SELECT EntityDefinition.QualifiedApiName, QualifiedApiName, DataType
FROM FieldDefinition
WHERE EntityDefinition.QualifiedApiName IN ('Product2', 'SBQQ__ProcessInput__c')
  AND QualifiedApiName LIKE 'Deployment_Model%'
```

If the two objects return different API names, the mirror is broken. Then confirm products carry values, because null values never match an equals filter:

```sql
SELECT Deployment_Model_v2__c, COUNT(Id)
FROM Product2
WHERE IsActive = true
GROUP BY Deployment_Model_v2__c
```

**Why it works:** The first query proves whether the same API name exists on both objects, which is the first thing to check for unfiltered results (`gotchas.md` gotcha 2). The second shows how many active products have no value and therefore never appear for that question (gotcha 8). Redeploy the mirror field from `metadata-examples.md` with the new name, and update the question to point at it.

