# LLM Anti-Patterns — CPQ Product Catalog Setup

Common mistakes AI coding assistants make when generating or advising on Salesforce CPQ product catalog configuration. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating CPQ Product Options as Standard Junction Objects

**What the LLM generates:** Advice to create a "many-to-many junction object" between Product2 and a bundle product, or suggestions to query `Product2` and `PricebookEntry` to find bundle components.

**Why it happens:** LLMs trained on general Salesforce content default to standard Product2/Pricebook2 patterns. They do not distinguish between standard products and CPQ's managed-package extension objects (`SBQQ__ProductOption__c`, `SBQQ__Feature__c`).

**Correct pattern:**

```
Product Options in Salesforce CPQ are stored in SBQQ__ProductOption__c records.
Each record links a child product (SBQQ__OptionalSKU__c) to a parent bundle product
(SBQQ__ConfiguredSKU__c). Feature groupings use SBQQ__Feature__c records.
Do not use standard PricebookEntry or a custom junction object.
```

**Detection hint:** Watch for mentions of `PricebookEntry`, custom junction objects, or Apex code inserting product relationships via `OpportunityLineItem` in the context of bundle configuration.

---

## Anti-Pattern 2: Recommending Validation Rules to Enforce Required Bundle Components

**What the LLM generates:** A Validation Product Rule with a condition like "If Required Option is not selected, block save" to ensure a mandatory component is always included.

**Why it happens:** LLMs over-index on Product Rules as the universal CPQ enforcement mechanism. They are unaware that `SBQQ__Required__c = true` on the Product Option record enforces mandatory inclusion at the UI layer without needing a rule.

**Correct pattern:**

```
Set SBQQ__Required__c = true on the SBQQ__ProductOption__c record.
Required options are locked in the CPQ configurator UI — reps cannot deselect them.
Reserve Validation rules for complex cross-option logic that cannot be expressed
as a single Required flag (e.g., "if Option A quantity > Option B quantity, block save").
```

**Detection hint:** Any suggestion to create a Validation rule with logic equivalent to "X option must be present" when X is a product option that could simply be marked Required.

---

## Anti-Pattern 3: Assuming Filter Rules Enforce Constraints at the API Level

**What the LLM generates:** Instructions to set up Filter rules and state that they "prevent" incompatible options from being added to a quote.

**Why it happens:** LLMs conflate the CPQ configurator UI with the full quote data lifecycle. Filter rules are a UI-layer mechanism. They do not fire when quotes are built programmatically via the SBQQ API, Salesforce Flow, or direct DML.

**Correct pattern:**

```
Filter rules control option visibility in the CPQ configurator UI only.
For constraints that must hold in all contexts (including API-built quotes),
add a Validation Product Rule with equivalent conditions.
Document both rules together so future maintainers understand their complementary roles.
```

**Detection hint:** Phrases like "Filter rules will prevent..." or "the rule ensures the option cannot be added" — Filter rules hide, they do not block.

---

## Anti-Pattern 4: Generating Configuration Attribute Setup Without Specifying Bundle Scope

**What the LLM generates:** Instructions to create a Configuration Attribute without specifying which bundle product it is scoped to, or advice to create one Configuration Attribute to "control all bundles" in the catalog.

**Why it happens:** LLMs generalize Configuration Attributes as an org-wide setting rather than recognizing they are scoped to a specific parent bundle product (`SBQQ__ConfiguredSKU__c` on the `SBQQ__ConfigurationAttribute__c` record).

**Correct pattern:**

```
Each SBQQ__ConfigurationAttribute__c record must be linked to a specific
parent bundle via SBQQ__ConfiguredSKU__c. Attributes do not propagate to
nested sub-bundles automatically. Create separate attribute records for
each bundle level that needs header-driven behavior.
```

**Detection hint:** Advice to "create a global configuration attribute" or attribute setup that omits specifying the parent bundle product.

---

## Anti-Pattern 5: Ignoring Product Rule Sequence Numbers or Assigning Duplicates

**What the LLM generates:** Product Rule setup instructions that do not mention sequence numbers, or suggest setting all rules to sequence 1 and letting Salesforce "process them in creation order."

**Why it happens:** LLMs often omit administrative fields they consider secondary. They do not understand that CPQ rule evaluation order is governed exclusively by `SBQQ__Sequence__c` and that duplicate sequence numbers produce undefined evaluation behavior.

**Correct pattern:**

```
Every SBQQ__ProductRule__c must have a unique SBQQ__Sequence__c value.
Use spaced numbering (10, 20, 30) to allow future insertion without full renumbering.
Document the intended evaluation order and the reason for each rule's position in the sequence.
For Selection rules that chain (rule A's action triggers rule B's conditions),
sequence them explicitly and validate with the SBQQ__EvalEvent__c field set to "Always"
if single-pass evaluation is insufficient.
```

**Detection hint:** Any Product Rule setup that does not explicitly set `SBQQ__Sequence__c`, or that sets all rules to the same sequence value.

---

## Anti-Pattern 6: Recommending 3–4 Level Bundle Nesting Without Performance Warning

**What the LLM generates:** Multi-level bundle setup instructions that recommend 3 or 4 nesting levels without flagging the configurator load time impact.

**Why it happens:** LLMs describe what CPQ can do (supports up to 4 levels) without the experiential context that deep nesting causes significant performance degradation in real org environments with large catalogs.

**Correct pattern:**

```
Salesforce CPQ supports bundle nesting up to 4 levels, but each nesting level
multiplies SOQL queries at configurator open. In practice, limit nesting to
2 levels. If 3 levels are required, test configurator load time with
representative data volume before go-live. Never design 4-level nesting
without explicit performance validation.
Consider replacing deep nesting with a flat bundle + Configuration Attribute
+ Filter rules to achieve the same business outcome.
```

**Detection hint:** Bundle design recommendations with 3+ nesting levels that make no mention of performance impact or testing requirements.
