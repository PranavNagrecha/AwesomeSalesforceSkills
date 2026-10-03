# LLM Anti-Patterns — CPQ Guided Selling

Common mistakes AI coding assistants make when generating or advising on CPQ Guided Selling.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Omitting Mirror Custom Fields on SBQQ__ProcessInput__c

**What the LLM generates:** Instructions to create `SBQQ__ProcessInput__c` records with `SBQQ__SearchField__c` set to a custom Product2 field API name (e.g., `Product_Category__c`), without mentioning that an identically named field must also exist on `SBQQ__ProcessInput__c`.

**Why it happens:** LLMs trained on general CPQ documentation see the `SBQQ__SearchField__c` field and assume it is merely a pointer to the Product2 field. The runtime answer-storage mechanism — where CPQ writes the rep's answer to a same-name field on `SBQQ__ProcessInput__c` — is a non-obvious implementation detail not prominently documented. LLMs omit it because it looks redundant at first glance.

**Correct pattern:**
```
For every custom Product2 classification field used in guided selling:
1. Create the field on Product2 (e.g., Product_Category__c, Picklist)
2. Create a field with IDENTICAL API name on SBQQ__ProcessInput__c (e.g., Product_Category__c, Picklist)
3. Set SBQQ__SearchField__c on the ProcessInput record to the API name
Without step 2, guided selling silently returns all products regardless of rep answers.
```

**Detection hint:** Look for any ProcessInput setup instruction that references a custom `__c` field in `SBQQ__SearchField__c` without a corresponding step to create that same field on `SBQQ__ProcessInput__c`. Flag it.

UNVERIFIED (2026-10-03): the mirror-field mechanism and the `SBQQ__SearchField__c` API name are documented only on help.salesforce.com; confirm the field name in Object Manager.

---

## Anti-Pattern 2: Recommending OmniStudio Flows for Guided Product Selection on CPQ Quotes

**What the LLM generates:** Advice to build an OmniScript or FlexCard-based product selection flow to capture rep answers, filter a product list, and add results to a CPQ quote — often framed as "more flexible" than native CPQ Guided Selling.

**Why it happens:** LLMs conflate "Salesforce guided selling" (a generic UX concept) with CPQ's specific `SBQQ__QuoteProcess__c` mechanism. When prompted about a "product wizard," LLMs with OmniStudio training data may reach for OmniScript as the default solution for any wizard-style flow.

**Correct pattern:**
```
For any product selection that feeds a CPQ-managed quote (SBQQ__Quote__c):
- Use SBQQ__QuoteProcess__c + SBQQ__ProcessInput__c (native CPQ Guided Selling)
- OmniStudio product selection is for non-CPQ order management contexts only
- Products added outside the CPQ configurator bypass price rules, product rules,
  bundle configuration, and the CPQ price waterfall
```

**Detection hint:** Any response that suggests OmniScript, FlexCard, or a custom LWC product picker for a question explicitly about CPQ quoting should be flagged for review.

---

## Anti-Pattern 3: Treating SBQQ__SearchField__c as a Formula or Lookup Expression

**What the LLM generates:** Instructions to set `SBQQ__SearchField__c` to a formula-style expression, a related field path (e.g., `Product2.Family`), or a display label instead of the raw API name (e.g., `Product Family` instead of `Family`).

**Why it happens:** LLMs familiar with formula fields, SOQL relationship traversal, and Salesforce field expressions assume that `SBQQ__SearchField__c` accepts Salesforce's standard field reference syntax. In reality, CPQ uses this field as a direct string API name for a dynamic SOQL WHERE clause against Product2.

**Correct pattern:**
```
SBQQ__SearchField__c must be set to the exact API name of a flat field on Product2:
- Correct: Family
- Correct: Product_Category__c
- Wrong: Product2.Family (relationship path — not supported)
- Wrong: Product Family (display label — not the API name)
- Wrong: SBQQ__ProductCode__c (use the underlying API name, not a related field)
```

**Detection hint:** Any `SBQQ__SearchField__c` value containing a dot (`.`), a space, or a label-style name should be flagged.

UNVERIFIED (2026-10-03): the field API name is help-only. The plugin guide does confirm that answers reach plugins keyed by Product2 API name.

---

## Anti-Pattern 4: Setting SBQQ__GuidedProductSelection__c to False on the Quote Process

**What the LLM generates:** A `SBQQ__QuoteProcess__c` record with `SBQQ__GuidedProductSelection__c` omitted (defaulting to false) or explicitly set to false, often because the LLM is generating a generic "Quote Process" template without recognizing that this field is the activation flag for wizard mode.

**Why it happens:** LLMs generating boilerplate record creation steps often omit boolean flags that are not mentioned in the question. The field name `GuidedProductSelection` is not obviously an activation toggle — it reads more like a feature description than a required true/false configuration field.

**Correct pattern:**
```
Any SBQQ__QuoteProcess__c record intended for Guided Selling MUST have:
SBQQ__GuidedProductSelection__c = true

Without this:
- The Quote Process exists but the wizard does not launch
- "Add Products" falls back to the standard CPQ product selector
- No error or warning is shown to the rep or admin
```

**Detection hint:** Any instruction to create a `SBQQ__QuoteProcess__c` record for guided selling that does not explicitly set `SBQQ__GuidedProductSelection__c = true` is incomplete.

UNVERIFIED (2026-10-03): the activation field's API name is help-only; confirm it in Object Manager before scripting record creation.

---

## Anti-Pattern 5: Reaching for Plugin Code Before Configuration Is Exhausted

**What the LLM generates:** An `SBQQ.ProductSearchPlugin` class for a requirement that is plain classification filtering ("filter by product line and region").

**Why it happens:** "ProductSearchPlugin" is the most visible extension point in CPQ developer material, so the model treats it as the default answer for any filtering requirement.

**Correct pattern:**

```
1. Questions mapped to Product2 fields (no code). Use for most cases.
2. Plugin in Enhanced mode (isSuggestCustom = false): CPQ keeps its query,
   getAdditionalSuggestFilters appends a WHERE fragment for a rule the rep does not control.
3. Plugin in Custom mode (isSuggestCustom = true): suggest() builds and runs the whole
   query and returns List<PricebookEntry>. Only for external data, ranking, or logic
   the appended fragment cannot express.
The CPQ package has no new feature development; keep custom code small.
```

**Detection hint:** Plugin code proposed for a requirement that only lists classification fields and equals filters.

---

## Anti-Pattern 6: Inventing the Plugin Signature

**What the LLM generates:** `global List<Id> search(SBQQ.ProductSearchContext ctx)` presented as the guided selling contract.

**Why it happens:** The model composes a plausible "context object" API. An earlier version of this skill did the same.

**Correct pattern:** The guided selling methods are `isInputHidden(SObject quote, String fieldName)`, `getInputDefaultValue(SObject quote, String fieldName)`, `isSuggestCustom(SObject quote, Map<String,Object> fieldValuesMap)`, `suggest(SObject quote, Map<String,Object> fieldValuesMap)` returning `List<PricebookEntry>`, and `getAdditionalSuggestFilters(SObject quote, Map<String,Object> fieldValuesMap)` returning a WHERE fragment. The product search interface uses `isFilterHidden`, `getFilterDefaultValue`, `isSearchCustom`, `search`, and `getAdditionalSearchFilters` with the same parameter shapes.

**Detection hint:** `ProductSearchContext`, a `List<Id>` return type, or a `suggest` method that never runs because `isSuggestCustom` returns false.

---

## Anti-Pattern 7: Copying the Guide's String-Built SOQL

**What the LLM generates:** A `suggest` or `search` implementation that concatenates `quote.get('SBQQ__Pricebook__c')` and rep answers into a query string, because the guide's sample does.

**Why it happens:** The sample is the most authoritative code the model has seen for this interface.

**Correct pattern:** In `suggest` and `search`, use bind variables (`Database.queryWithBinds` with `AccessLevel.USER_MODE` when the field list comes from a field set). In `getAdditionalSuggestFilters`, CPQ runs the fragment, so return static text or values checked against an allowed list and escaped with `String.escapeSingleQuotes`.

**Detection hint:** `Database.query(` on a string containing a rep answer or a quote field value.

---

## Anti-Pattern 8: Assuming the Plugin Sees Every Quote Field

**What the LLM generates:** Plugin logic that reads a custom quote field from the `quote` parameter and branches on it, or parses a date field as a `Date`.

**Why it happens:** The parameter is typed `SObject`, so the model assumes it is fully populated.

**Correct pattern:** Plugins "can use only a subset of CPQ quote fields by default"; query the quote by `Id` for anything else. Date fields arrive as `yyyy-mm-dd` strings. The `suggest` and `search` maps contain only keys for non-null values.

**Detection hint:** `quote.get('Custom_Field__c')` with no SOQL fallback, or a cast of a date field to `Date`.

---

## Anti-Pattern 9: Using the Configuration Initializer for Custom Option Fields

**What the LLM generates:** A product configuration initializer that sets a custom field on a product option or a configuration attribute from the guided selling answers.

**Why it happens:** The initializer is described as "setting field values", and the model generalizes to all fields.

**Correct pattern:** The initializer "works only for standard product option fields and not for configuration attributes or custom product option fields". Use it for selection and quantity; use product rules or configuration rules for the rest.

**Detection hint:** An initializer design that writes custom option fields or configuration attributes.
