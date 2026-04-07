# LLM Anti-Patterns — CPQ Pricing Rules

Common mistakes AI coding assistants make when generating or advising on Salesforce CPQ pricing configuration. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Price Rules for Volume Tiers Instead of Discount Schedules

**What the LLM generates:** Advice to create multiple Price Rule records — one per quantity tier — with Price Conditions like "SBQQ__Quantity__c >= 11 AND SBQQ__Quantity__c <= 25" to replicate volume discounts.

**Why it happens:** LLMs pattern-match on "conditional pricing" → "conditional rules" without recognizing that CPQ has a first-class volume tier mechanism (Discount Schedules) that is purpose-built for this use case and does not require rule logic.

**Correct pattern:**

```text
Use SBQQ__DiscountSchedule__c with SBQQ__DiscountTier__c records.
Attach the Discount Schedule to Product2.SBQQ__DiscountSchedule__c.
The CPQ engine reads the tier automatically during the discount schedule
phase of the price waterfall — no Price Rule required.
```

**Detection hint:** Output mentions "Price Rule" or "Price Condition" in the context of quantity-based tier discounts, without mentioning Discount Schedule or DiscountTier.

---

## Anti-Pattern 2: Assigning the Same Evaluation Order to Multiple Price Rules

**What the LLM generates:** A configuration plan where multiple Price Rules are assigned the same `SBQQ__EvaluationOrder__c` value (e.g., all rules set to Evaluation Order 1) with a note like "they will run in the order they appear in the list."

**Why it happens:** LLMs apply a generic "list order" mental model without knowing that CPQ's calculation engine does not use record insertion order or list view order as a tiebreaker. The CPQ engine's behavior for same-order rules is undefined.

**Correct pattern:**

```text
Assign unique SBQQ__EvaluationOrder__c values to every active Price Rule.
Use spacing (10, 20, 30) to allow future insertions without renumbering.
Maintain a pricing design document listing each rule's evaluation order.
```

**Detection hint:** Output shows two or more Price Rules with identical `SBQQ__EvaluationOrder__c` values, or states that list order determines execution sequence.

---

## Anti-Pattern 3: Suggesting Price Actions Target SBQQ__ListPrice__c for Final Price Overrides

**What the LLM generates:** A Price Action configuration that sets the target field to `SBQQ__ListPrice__c`, stating this will "set the final price for the quote line."

**Why it happens:** LLMs conflate "list price" with "final price." In standard Salesforce, modifying the unit price is sufficient. In CPQ's price waterfall, `SBQQ__ListPrice__c` is an early-stage field that later stages can overwrite. Setting it via a Price Action does not guarantee the final net price reflects that value.

**Correct pattern:**

```text
To set a final price that overrides all waterfall steps, target
SBQQ__SpecialPrice__c in the Price Action.
SBQQ__SpecialPrice__c sits at the bottom of the CPQ price waterfall
and drives the final net price on the quote line.
Use SBQQ__ListPrice__c only if the intent is to modify the base
price before other waterfall phases recalculate from it.
```

**Detection hint:** Price Action target field is `SBQQ__ListPrice__c` or `SBQQ__RegularPrice__c` in a context where the business requirement is a final net price override.

---

## Anti-Pattern 4: Applying CPQ Pricing Logic to Standard Opportunity Products

**What the LLM generates:** Instructions to configure CPQ Price Rules or Discount Schedules and then stating that these will apply to "Opportunity Line Items" or "products on the opportunity."

**Why it happens:** LLMs conflate the CPQ quote object with standard Salesforce opportunity products. CPQ Price Rules, Discount Schedules, and Contracted Prices only execute during CPQ Quote (`SBQQ__Quote__c`) calculation. They have no effect on `OpportunityLineItem` records or standard pricebook lookups.

**Correct pattern:**

```text
CPQ pricing logic (Price Rules, Discount Schedules, Block Pricing,
Contracted Prices) applies only to SBQQ__QuoteLine__c records during
CPQ quote calculation.
Standard OpportunityLineItem records are not subject to CPQ pricing
logic. If pricing must be CPQ-driven, quotes must be used and synced
to the opportunity via CPQ's opportunity sync feature.
```

**Detection hint:** Output mentions "Opportunity Line Items" or "OpportunityLineItem" as the target of CPQ Price Rule or Discount Schedule configuration.

---

## Anti-Pattern 5: Assuming Contracted Prices Cascade to Bundle Components

**What the LLM generates:** A statement like "when you create a Contracted Price for the bundle parent product, all components will automatically receive the contracted rate."

**Why it happens:** LLMs apply a parent-child inheritance assumption. CPQ bundles do have parent-child relationships, but the CPQ calculation engine evaluates Contracted Prices at the individual product level, not at the bundle level. There is no cascading mechanism.

**Correct pattern:**

```text
Create SBQQ__ContractedPrice__c records for each product that needs
a contracted rate — including each bundle component individually.
A Contracted Price on the bundle parent does not apply to
SBQQ__ProductOption__c component lines.
If bundle-level contracted rates are required at scale, use a Flow
or Apex trigger on contract activation to generate component
Contracted Price records automatically.
```

**Detection hint:** Output describes a single `SBQQ__ContractedPrice__c` record on a bundle parent and states it covers all components, or does not mention the need for per-component contracted price records.

---

## Anti-Pattern 6: Confusing CPQ Product Rules with CPQ Price Rules

**What the LLM generates:** Instructions that mix `SBQQ__ProductRule__c` (used in the configurator for selection/validation/filtering of product options) with `SBQQ__PriceRule__c` (used in the calculation engine for pricing). The LLM may suggest editing Product Rules to change discounts, or suggest Price Rules to hide options in the configurator.

**Why it happens:** Both objects are called "rules" in CPQ and the LLM conflates them. They are distinct objects with completely different purposes and execution contexts.

**Correct pattern:**

```text
SBQQ__ProductRule__c — fires in the CPQ product configurator during
  bundle configuration. Used to validate, alert, auto-select, or
  filter product options. Has no effect on pricing.

SBQQ__PriceRule__c — fires during CPQ quote calculation. Used to
  set price fields on the quote or quote line. Has no effect on
  which products appear in the configurator.
```

**Detection hint:** Output uses "Product Rule" and "Price Rule" interchangeably, or suggests configuring a Price Rule to control which products are visible in the configurator.
