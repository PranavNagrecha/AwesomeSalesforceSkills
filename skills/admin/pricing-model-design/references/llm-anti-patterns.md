# LLM Anti-Patterns — Pricing Model Design

Common mistakes AI coding assistants make when generating or advising on Salesforce CPQ pricing model design. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating Range and Slab Discount Schedule Types

**What the LLM generates:** Instructions to create a `SBQQ__DiscountSchedule__c` with tiers and a statement like "the CPQ engine applies the appropriate tier discount based on quantity." The output does not specify `SBQQ__Type__c` and does not explain the behavioral difference between Range and Slab.

**Why it happens:** LLMs describe "tiered discounts" generically — the distinction between flat-tier (Range) and incremental-bracket (Slab) requires CPQ-specific knowledge that is underrepresented in training data compared to the generic concept of "volume discounts." The LLM defaults to a vague description that applies to both.

**Correct pattern:**

```text
Always specify SBQQ__Type__c explicitly:
  - Range: entire quantity receives the discount rate for the tier
    the quantity falls into. Cliff effects at tier boundaries.
  - Slab: each unit priced at the rate for the bracket it occupies,
    like income tax brackets. No cliff effects.

Walk through a tier-boundary example before configuring:
  "If a customer orders 26 units instead of 25, does their
  price for all 26 units drop (Range) or only the 26th unit
  gets the higher discount (Slab)?"

Record the stakeholder's answer before setting SBQQ__Type__c.
```

**Detection hint:** Output describes creating Discount Schedule tiers without specifying `SBQQ__Type__c`, or uses phrasing like "the tier discount applies to the quantity" without clarifying whether it applies to the full quantity or only the incremental units.

---

## Anti-Pattern 2: Using a Discount Schedule to Implement Block Pricing

**What the LLM generates:** A solution for flat-fee capacity-tier pricing that sets a per-unit list price and then creates a Range Discount Schedule where the discount percentages are computed to produce the intended flat fee at the maximum quantity of each tier.

**Why it happens:** LLMs recognize "different prices at different quantities" as a volume discount scenario and default to Discount Schedules as the volume pricing mechanism. Block Pricing is a less prominent CPQ concept in training data. The LLM does not recognize that a flat absolute price for a range is fundamentally incompatible with a percentage-of-unit-price mechanism.

**Correct pattern:**

```text
When the requirement is a FLAT PRICE for a quantity range
(e.g., "1–10 seats = $500 total regardless of exact count"):
  - Set SBQQ__PricingMethod__c = 'Block' on Product2
  - Create SBQQ__BlockPrice__c records with:
      SBQQ__LowerBound__c, SBQQ__UpperBound__c, SBQQ__Price__c
  - Do NOT use a Discount Schedule for this requirement.
    A percentage discount cannot produce a constant absolute
    price across a range of quantities.
```

**Detection hint:** Output describes computing discount percentages from a list price to approximate a flat fee, or suggests creating a Discount Schedule for a requirement described as "flat price" or "fixed fee per tier."

---

## Anti-Pattern 3: Stating That CPQ Enforces Markup Limits on Cost Plus Markup Products

**What the LLM generates:** A statement like "CPQ's Cost Plus Markup pricing method ensures reps cannot set markups that violate margin thresholds" or "markup is validated against the default markup on the product."

**Why it happens:** LLMs apply a general assumption that systems enforce business rules at the point of input. CPQ does validate many fields but has no native mechanism to reject a markup value as out-of-range. The `SBQQ__DefaultMarkup__c` on Product2 is a *default* — it populates the quote line's markup initially but does not prevent a rep from changing it to any numeric value.

**Correct pattern:**

```text
CPQ accepts any numeric value for SBQQ__Markup__c — including
negative values and values above any business threshold.

To enforce markup limits, build one of:
  1. Validation Rule on SBQQ__QuoteLine__c:
     SBQQ__Markup__c < 0 || SBQQ__Markup__c > 500
     → Error: "Markup must be between 0% and 500%"

  2. CPQ Approval Rule:
     Condition: SBQQ__Markup__c > [ceiling]
     → Route to manager approval before quote can be submitted

SBQQ__DefaultMarkup__c on Product2 is a default only.
It does not constrain what a rep can set on the quote line.
```

**Detection hint:** Output claims that CPQ "enforces," "validates," or "restricts" markup values, or implies that `SBQQ__DefaultMarkup__c` acts as a ceiling or floor at quote time.

---

## Anti-Pattern 4: Recommending a Price Rule for Percent of Total Pricing

**What the LLM generates:** A solution for "support product priced as 18% of software lines" that creates a `SBQQ__PriceRule__c` with a `SBQQ__LookupQuery__c` that sums the net prices of other lines, then sets the support product's `SBQQ__SpecialPrice__c` via a Price Action.

**Why it happens:** LLMs recognize that CPQ Price Rules can perform calculations across quote lines and pattern-match on the requirement as "conditional pricing logic" → "Price Rule." The native `SBQQ__PricingMethod__c = 'Percent of Total'` mechanism is less visible in general CPQ content than Price Rules.

**Correct pattern:**

```text
For a product priced as a percentage of other quote lines:
  - Set SBQQ__PricingMethod__c = 'Percent of Total' on Product2
  - Set SBQQ__PercentOfTotalBase__c:
      'Regular'  → all lines with standard Product Type
      'All'      → all quote lines including other Percent of Total
      [Category] → lines in a specific product category
  - Set SBQQ__DefaultPercentage__c on Product2 for the default rate
  - No Price Rule required for the standard case.

Only use a Price Rule for this requirement when the percentage
itself must vary based on quote conditions (e.g., different rates
by product family or contract term) — and document why the native
Pricing Method cannot handle the variation.
```

**Detection hint:** Output describes a Price Rule, Lookup Query, or Price Action in the context of a support/maintenance product that should be priced as a fixed percentage of other quote lines, without mentioning `SBQQ__PricingMethod__c = 'Percent of Total'`.

---

## Anti-Pattern 5: Treating Block Pricing and Discount Schedules as Interchangeable Mechanisms

**What the LLM generates:** A recommendation to use a Discount Schedule "for Block Pricing" or to use Block Pricing "instead of a Discount Schedule" without recognizing that the two mechanisms operate on fundamentally different pricing models.

**Why it happens:** Both mechanisms produce a price that varies by quantity, and both are associated with volume pricing in CPQ. LLMs conflate the two because the surface-level requirement ("price changes at quantity thresholds") sounds identical even though the underlying math is completely different.

**Correct pattern:**

```text
DISCOUNT SCHEDULE (SBQQ__DiscountSchedule__c):
  - Applies a percentage discount to the product's unit price
  - Total = quantity × list_price × (1 - discount_percent)
  - Price per unit scales smoothly (or in brackets for Slab)
  - Use when: the product has a unit price and tiers discount that price

BLOCK PRICING (SBQQ__PricingMethod__c = 'Block'):
  - Replaces per-unit math with a fixed absolute price for the range
  - Total = the SBQQ__Price__c value on the matching BlockPrice record
  - Price per unit is NOT multiplied by quantity
  - Use when: the product has a flat total price per capacity tier

They are NOT interchangeable:
  - A Discount Schedule cannot produce a constant flat price across
    a range of quantities
  - Block Pricing does not apply percentage discounts to a unit price
```

**Detection hint:** Output uses "Block Pricing" and "Discount Schedule" interchangeably, or suggests using a Discount Schedule to produce a flat total price for a quantity range.

---

## Anti-Pattern 6: Not Checking for Block Price Range Gaps or Overlaps Before Quoting

**What the LLM generates:** Instructions to create Block Price records for each tier without a verification step for contiguous, non-overlapping ranges. The output assumes that if records are created in order they will be correct.

**Why it happens:** LLMs model data creation as an ordered sequence and assume the records created will be correct as long as the input values are from the right columns. CPQ does not validate Block Price record bounds against other records for the same product at save time — the gap/overlap is silent.

**Correct pattern:**

```text
After creating all SBQQ__BlockPrice__c records for a product:

1. Export all records for the product filtered by Pricebook:
   SELECT SBQQ__LowerBound__c, SBQQ__UpperBound__c, SBQQ__Price__c
   FROM SBQQ__BlockPrice__c
   WHERE SBQQ__Product__c = :productId
   ORDER BY SBQQ__LowerBound__c

2. Verify contiguity: each record's LowerBound equals the
   previous record's UpperBound + 1 (no gaps).

3. Verify no overlaps: sort by LowerBound; ensure no record's
   LowerBound is within the range of a previous record.

4. Verify coverage: the first record's LowerBound is 1 (or the
   minimum expected quantity) and the last record's UpperBound
   covers the maximum expected quantity.

Gaps cause CPQ to fall back to list price for quantities in
the gap. Overlaps cause undefined tier matching behavior.
```

**Detection hint:** Output creates Block Price records without a subsequent verification step for range contiguity, or states that CPQ validates record bounds at save time.
