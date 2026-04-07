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

---

## Anti-Pattern 5: Using Custom Apex (ProductSearchPlugin) for Scenarios That Standard Search Can Handle

**What the LLM generates:** An Apex class implementing `SBQQ.ProductSearchPlugin` for a requirement that is straightforwardly a standard classification filter — for example, filtering products by industry and service tier using equals operators on two custom fields.

**Why it happens:** LLMs default to code solutions when the question involves product filtering logic. "ProductSearchPlugin" appears in CPQ developer documentation and looks like the primary extension point. LLMs overfit on it as the solution for any non-trivial filtering requirement.

**Correct pattern:**
```
Decision order for CPQ Guided Selling search type:
1. Standard — one answer per question, equality/contains filtering. Use for most cases.
2. Enhanced — multi-select per question (OR matching). Use when a product spans multiple values.
3. Custom (Apex ProductSearchPlugin) — ONLY when:
   - Logic cannot be expressed with Standard or Enhanced operators
   - An external data source must be called during product search
   - Scoring or ranking beyond simple inclusion/exclusion is required

Custom search adds: Apex development, test coverage requirements, managed package
upgrade risk, and governor limit exposure. Do not recommend it when Standard or
Enhanced can express the requirement.
```

**Detection hint:** Any response recommending Apex and `SBQQ.ProductSearchPlugin` for a requirement that only describes classification-based filtering (e.g., "filter by product line and region") without external system lookups or scoring should be questioned.
